from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from app.db.postgran import SessionType
from app.repository.report_repo import create_report, get_edge_status_snapshot
from app.schemas.report import EdgeStatusSnapshotSchema, ReportCreateResponseSchema, ReportCreateSchema
from app.services.auth import get_current_user


router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("", response_model=ReportCreateResponseSchema, status_code=201)
def submit_report(
    payload: ReportCreateSchema,
    db: SessionType,
    current_user: dict = Depends(get_current_user),
):
    report = create_report(payload, db, current_user)
    snapshot = get_edge_status_snapshot(report.edge_id, db)
    return {
        "message": "report submitted",
        "report_id": report.id,
        "edge_status": snapshot,
    }


@router.get("/edges/{edge_id}/status", response_model=EdgeStatusSnapshotSchema)
def read_edge_status(edge_id: uuid.UUID, db: SessionType):
    return get_edge_status_snapshot(edge_id, db)
