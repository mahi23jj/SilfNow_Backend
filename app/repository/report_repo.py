from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlmodel import Session, delete, select

from app.models.edge import Edge
from app.models.edge_status import EdgeStatus
from app.models.node import Node
from app.models.report import Report
from app.models.report_enums import QueueLevel, VehicleAvailability
from app.models.user import User
from app.schemas.report import ReportCreateSchema
from app.services.report_service import (
    get_recent_reports,
    get_status,
    haversine_distance_meters,
    location_score_from_distance,
    normalize_transport_types,
)


DUPLICATE_REPORT_WINDOW_MINUTES = 10


def _resolve_user_id(session: Session, current_user: dict) -> object:
    phone_number = current_user.get("phone_number")
    if not phone_number:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = session.exec(select(User).where(User.phone_number == phone_number)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user.id


def _find_duplicate_report(session: Session, user_id, data: ReportCreateSchema) -> Report | None:
    recent_cutoff = datetime.utcnow() - timedelta(minutes=DUPLICATE_REPORT_WINDOW_MINUTES)
    candidates = session.exec(
        select(Report).where(
            Report.user_id == user_id,
            Report.edge_id == data.edge_id,
            Report.created_at >= recent_cutoff,
        )
    ).all()

    normalized_transport_types = normalize_transport_types(data.transport_types)
    for candidate in candidates:
        if (
            normalize_transport_types(candidate.transport_types) == normalized_transport_types
            and candidate.queue_level == data.queue_level
            and candidate.vehicle_availability == data.vehicle_availability
            and candidate.estimated_wait_time == data.estimated_wait_time
        ):
            return candidate

    return None


def create_report(data: ReportCreateSchema, session: Session, current_user: dict) -> Report:
    edge = session.get(Edge, data.edge_id)
    if not edge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Edge not found")

    node = session.get(Node, edge.from_node_id)
    if not node:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Edge origin node not found")

    normalized_transport_types = normalize_transport_types(data.transport_types)
    allowed_transport_types = set(normalize_transport_types(edge.transport_types))
    invalid_transport_types = sorted(set(normalized_transport_types) - allowed_transport_types)
    if invalid_transport_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported transport types for this edge: {', '.join(invalid_transport_types)}",
        )

    user_id = _resolve_user_id(session, current_user)
    duplicate_report = _find_duplicate_report(session, user_id, data)
    if duplicate_report:
        return duplicate_report

    distance_meters = haversine_distance_meters(data.gps_lat, data.gps_lng, node.latitude, node.longitude)
    location_score = location_score_from_distance(distance_meters)
    if location_score <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Report location is too far from the edge origin to be accepted",
        )

    report = Report(
        user_id=user_id,
        edge_id=data.edge_id,
        transport_types=normalized_transport_types,
        queue_level=QueueLevel(data.queue_level.value),
        vehicle_availability=VehicleAvailability(data.vehicle_availability.value),
        estimated_wait_time=data.estimated_wait_time,
        image_url=data.image_url,
        additional_message=data.additional_message,
        gps_lat=data.gps_lat,
        gps_lng=data.gps_lng,
        location_distance_meters=distance_meters,
        location_score=location_score,
        device_timestamp=data.device_timestamp,
    )

    session.add(report)
    session.flush()
    rebuild_edge_status(edge.id, session)
    session.commit()
    session.refresh(report)
    return report


def rebuild_edge_status(edge_id, session: Session) -> dict:
    reports = get_status(edge_id, session)

    now = datetime.utcnow()

    if not reports["fresh"]:
        return reports

    for item in reports["statuses"]:
        existing = session.exec(
            select(EdgeStatus).where(
                EdgeStatus.edge_id == edge_id,
                EdgeStatus.transport_type == item["transport_type"]
            )
        ).first()

        if existing:
            # 🔄 UPDATE
            existing.queue_level = QueueLevel(item["queue_level"])
            existing.vehicle_availability = VehicleAvailability(item["vehicle_availability"])
            existing.estimated_wait_time = item["estimated_wait_time"]
            existing.confidence_score = item["confidence"]
            existing.recent_reports_count = item["num_reports"]
            existing.updated_at = now
            existing.stability = item["stability"]

        else:
            # ➕ INSERT
            session.add(
                EdgeStatus(
                    edge_id=edge_id,
                    transport_type=item["transport_type"],
                    queue_level=QueueLevel(item["queue_level"]),
                    vehicle_availability=VehicleAvailability(item["vehicle_availability"]),
                    estimated_wait_time=item["estimated_wait_time"],
                    confidence_score=item["confidence"],
                    recent_reports_count=item["num_reports"],
                    stability=item["stability"],
                    updated_at=now,
                )
            )
       
    session.commit()
    return reports




STALE_MINUTES = 10


def get_edge_status_snapshot(edge_id, session: Session) -> dict:
    rows = session.exec(
        select(EdgeStatus)
        .where(EdgeStatus.edge_id == edge_id)
    ).all()

    # 🟢 Case 1: no cache
    if not rows:
        return rebuild_edge_status(edge_id, session)

    last_updated = max(r.updated_at for r in rows)
    now = datetime.utcnow()

    is_stale = (now - last_updated) > timedelta(minutes=STALE_MINUTES)

    # 🟢 Case 2: fresh → return directly
    if not is_stale:
        return {
            "edge_id": edge_id,
            "fresh": True,
            "is_stale": False,
            "last_updated": last_updated,
            "statuses": [
                {
                    "transport_type": r.transport_type,
                    "queue_level": r.queue_level,
                    "vehicle_availability": r.vehicle_availability,
                    "estimated_wait_time": r.estimated_wait_time,
                    "confidence": r.confidence_score,
                    "num_reports": r.recent_reports_count,
                    "stability": r.stability,
                }
                for r in rows
            ],
        }

    # 🟢 Case 3: stale → check recent reports
    recent_reports = get_recent_reports(edge_id, session)

    if recent_reports:
        return rebuild_edge_status(edge_id, session)

    # 🟢 Case 4: stale + no new reports → degrade confidence
    degraded_statuses = []

    for r in rows:
        degraded_confidence = round(r.confidence_score * 0.5, 2)

        degraded_statuses.append(
            {
                "transport_type": r.transport_type,
                "queue_level": r.queue_level,
                "vehicle_availability": r.vehicle_availability,
                "estimated_wait_time": r.estimated_wait_time,
                "confidence": degraded_confidence,
                "num_reports": r.recent_reports_count,
                "stability": r.stability,
            }
        )

    return {
        "edge_id": edge_id,
        "fresh": False,
        "is_stale": True,
        "last_updated": last_updated,
        "message": "No recent reports, data may be outdated",
        "statuses": degraded_statuses,
    }
