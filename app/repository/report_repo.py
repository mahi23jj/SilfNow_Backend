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
    get_status,
    haversine_distance_meters,
    location_score_from_distance,
    normalize_transport_types,
)


DUPLICATE_REPORT_WINDOW_MINUTES = 2


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

    session.exec(delete(EdgeStatus).where(EdgeStatus.edge_id == edge_id))

    if not reports["fresh"]:
        return reports

    for item in reports["statuses"]:
        session.add(
            EdgeStatus(
                edge_id=edge_id,
                transport_type=item["transport_type"],
                queue_level=QueueLevel(item["queue_level"]),
                vehicle_availability=VehicleAvailability(item["vehicle_availability"]),
                estimated_wait_time=item["estimated_wait_time"],
                confidence_score=item["confidence"],
                recent_reports_count=item["num_reports"],
            )
        )

    return reports


def get_edge_status_snapshot(edge_id, session: Session) -> dict:
    live_snapshot = get_status(edge_id, session)
    stored_statuses = session.exec(
        select(EdgeStatus)
        .where(EdgeStatus.edge_id == edge_id)
        .order_by(EdgeStatus.transport_type)
    ).all()

    if not live_snapshot["fresh"]:
        return {
            "edge_id": edge_id,
            "fresh": False,
            "last_updated": None,
            "num_reports": 0,
            "statuses": [],
            "message": "No recent data",
        }

    return {
        "edge_id": edge_id,
        "fresh": True,
        "last_updated": live_snapshot["last_updated"],
        "num_reports": live_snapshot["num_reports"],
        "statuses": [
            {
                "transport_type": status_row.transport_type,
                "queue_level": status_row.queue_level,
                "vehicle_availability": status_row.vehicle_availability,
                "estimated_wait_time": status_row.estimated_wait_time,
                "confidence_score": status_row.confidence_score,
                "recent_reports_count": status_row.recent_reports_count,
            }
            for status_row in stored_statuses
        ],
    }
