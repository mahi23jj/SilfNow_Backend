from datetime import datetime
from typing import Optional, TYPE_CHECKING
import uuid

from sqlalchemy import Column, JSON
from sqlmodel import Field, Relationship, SQLModel

from app.models.report_enums import QueueLevel, VehicleAvailability

if TYPE_CHECKING:
    from app.models.edge import Edge
    from app.models.user import User


class Report(SQLModel, table=True):
    __tablename__ = "reports"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    edge_id: uuid.UUID = Field(foreign_key="edges.id", index=True)

    transport_types: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False),
    )
    queue_level: QueueLevel
    vehicle_availability: VehicleAvailability
    estimated_wait_time: Optional[int] = Field(default=None, ge=0)

    image_url: Optional[str] = None
    additional_message: Optional[str] = None

    gps_lat: Optional[float] = None
    gps_lng: Optional[float] = None
    location_distance_meters: Optional[float] = Field(default=None, ge=0)
    location_score: float = Field(default=0.0, ge=0, le=1)

    device_timestamp: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # 🔗 relationships
    user: Optional["User"] = Relationship(back_populates="reports")
    edge: Optional["Edge"] = Relationship(back_populates="reports")
