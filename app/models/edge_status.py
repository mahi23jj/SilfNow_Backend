from datetime import datetime
from typing import Optional, TYPE_CHECKING
import uuid

from sqlalchemy import Column, Enum as SAEnum, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

from app.models.report_enums import QueueLevel, VehicleAvailability

if TYPE_CHECKING:
    from app.models.edge import Edge

class EdgeStatus(SQLModel, table=True):
    __tablename__ = "edge_status"
    __table_args__ = (
        UniqueConstraint("edge_id", "transport_type", name="uq_edge_status_edge_transport"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    edge_id: uuid.UUID = Field(foreign_key="edges.id", index=True)

    transport_type: str = Field(index=True)

    queue_level: QueueLevel = Field(
        sa_column=Column(SAEnum(QueueLevel, name="queue_level_enum"), nullable=False)
    )

    vehicle_availability: VehicleAvailability = Field(
        sa_column=Column(
            SAEnum(VehicleAvailability, name="vehicle_availability_enum"),
            nullable=False,
        )
    )

    estimated_wait_time: Optional[int] = Field(default=None, ge=0)

    confidence_score: float = Field(default=0.0, ge=0, le=1)

    recent_reports_count: int = Field(default=0, ge=0)
    
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # 🔗 relationship
    edge: Optional["Edge"] = Relationship(back_populates="status")




