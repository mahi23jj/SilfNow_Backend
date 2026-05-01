from __future__ import annotations

from datetime import datetime
from typing import Optional
import uuid

from pydantic import BaseModel, Field, field_validator

from app.models.report_enums import QueueLevel, VehicleAvailability


class ReportCreateSchema(BaseModel):
    edge_id: uuid.UUID
    transport_types: list[str] = Field(..., min_length=1)
    queue_level: QueueLevel
    vehicle_availability: VehicleAvailability
    estimated_wait_time: Optional[int] = Field(default=None, ge=0)
    gps_lat: float
    gps_lng: float
    device_timestamp: Optional[datetime] = None
    image_url: Optional[str] = None
    additional_message: Optional[str] = None

    @field_validator("transport_types")
    @classmethod
    def normalize_transport_types(cls, value: list[str]) -> list[str]:
        cleaned: list[str] = []
        for item in value:
            normalized = item.strip().lower()
            if normalized and normalized not in cleaned:
                cleaned.append(normalized)
        if not cleaned:
            raise ValueError("At least one transport type is required")
        return cleaned


class EdgeStatusItemSchema(BaseModel):
    transport_type: str
    queue_level: QueueLevel
    vehicle_availability: VehicleAvailability
    estimated_wait_time: Optional[int] = None
    confidence_score: float
    recent_reports_count: int


class EdgeStatusSnapshotSchema(BaseModel):
    edge_id: uuid.UUID
    fresh: bool
    last_updated: Optional[datetime] = None
    num_reports: int = 0
    statuses: list[EdgeStatusItemSchema] = Field(default_factory=list)
    message: Optional[str] = None


class ReportCreateResponseSchema(BaseModel):
    message: str
    report_id: uuid.UUID
    edge_status: EdgeStatusSnapshotSchema
