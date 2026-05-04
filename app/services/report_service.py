from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
import math
from typing import Any, Iterable

from sqlmodel import Session, delete, select

from app.models.edge_status import EdgeStatus
from app.models.report import Report


REPORT_WINDOW_MINUTES = 10
TIME_DECAY_HALF_LIFE_MINUTES = 10.0
PRIMARY_LOCATION_DISTANCE_METERS = 150.0
MAX_LOCATION_DISTANCE_METERS = 500.0


def haversine_distance_meters(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    earth_radius_m = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    return 2 * earth_radius_m * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def location_score_from_distance(distance_meters: float) -> float:
    if distance_meters <= PRIMARY_LOCATION_DISTANCE_METERS:
        return 1.0
    if distance_meters <= MAX_LOCATION_DISTANCE_METERS:
        return 0.35
    return 0.0


# def is_near(lat1: float, lng1: float, lat2: float, lng2: float) -> bool:
    # return haversine_distance_meters(lat1, lng1, lat2, lng2) <= MAX_LOCATION_DISTANCE_METERS


def time_decay(created_at: datetime) -> float:
    minutes = max((datetime.utcnow() - created_at).total_seconds() / 60, 0.0)
    return math.exp(-minutes / TIME_DECAY_HALF_LIFE_MINUTES)


def normalize_transport_types(transport_types: Iterable[str]) -> list[str]:
    normalized: list[str] = []
    for transport_type in transport_types:
        cleaned = transport_type.strip().lower()
        if cleaned and cleaned not in normalized:
            normalized.append(cleaned)
    return normalized


def compute_edge_status_per_transport(reports: list[Report]) -> list[dict[str, Any]]:
    grouped: dict[str, list[Report]] = defaultdict(list)

    for report in reports:
        for transport_type in normalize_transport_types(report.transport_types):
            grouped[transport_type].append(report)

    results: list[dict[str, Any]] = []

    for transport_type, transport_reports in grouped.items():
        queue_votes: dict[str, float] = defaultdict(float)
        availability_votes: dict[str, float] = defaultdict(float)
        weighted_wait_time_total = 0.0
        weighted_wait_time_count = 0.0
        total_weight = 0.0

        for report in transport_reports:
            location_weight = report.location_score or 0.0
            weight = location_weight * time_decay(report.created_at)
            if weight <= 0:
                continue

            total_weight += weight
            queue_votes[report.queue_level.value] += weight
            availability_votes[report.vehicle_availability.value] += weight

            if report.estimated_wait_time is not None:
                weighted_wait_time_total += report.estimated_wait_time * weight
                weighted_wait_time_count += weight

        if total_weight <= 0 or not queue_votes or not availability_votes:
            continue

        final_queue_level, final_queue_weight = max(queue_votes.items(), key=lambda item: item[1])
        final_vehicle_availability, final_availability_weight = max(
            availability_votes.items(), key=lambda item: item[1]
        )

        queue_confidence = final_queue_weight / total_weight
        availability_confidence = final_availability_weight / total_weight
        confidence = round((queue_confidence + availability_confidence) / 2, 2)

        average_wait_time = (
            round(weighted_wait_time_total / weighted_wait_time_count)
            if weighted_wait_time_count > 0
            else None
        )

        results.append(
            {
                "transport_type": transport_type,
                "queue_level": final_queue_level,
                "confidence": confidence,
                "num_reports": len(transport_reports),
                "estimated_wait_time": average_wait_time,
                "vehicle_availability": final_vehicle_availability,
            }
        )

    return sorted(results, key=lambda item: item["transport_type"])


def get_recent_reports(edge_id, session: Session) -> list[Report]:
    ten_minutes_ago = datetime.utcnow() - timedelta(minutes=REPORT_WINDOW_MINUTES)

    return session.exec(
        select(Report)
        .where(Report.edge_id == edge_id, Report.created_at >= ten_minutes_ago)
        .order_by(Report.created_at.desc())
    ).all()


def get_status(edge_id, session: Session) -> dict[str, Any]:
    reports = get_recent_reports(edge_id, session)

    if not reports:
        return {
            "statuses": [],
            "last_updated": None,
            "num_reports": 0,
            "fresh": False,
            "message": "No recent data",
        }

    return {
        "statuses": compute_edge_status_per_transport(reports),
        "last_updated": max(report.created_at for report in reports),
        "num_reports": len(reports),
        "fresh": True,
    }


def cleanup_old_reports(session: Session):
    cutoff = datetime.utcnow() - timedelta(hours=24)

    session.exec(delete(Report).where(Report.created_at < cutoff))
    session.exec(delete(EdgeStatus).where(EdgeStatus.updated_at < cutoff))
    session.commit()
