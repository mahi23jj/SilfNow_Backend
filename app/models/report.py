import datetime
from typing import Optional
import uuid

from pydantic import Field
from sqlmodel import Relationship, SQLModel

from app.models.edge import Edge
from app.models.user import User


class Report(SQLModel, table=True):
    __tablename__ = "reports"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    user_id: uuid.UUID = Field(foreign_key="users.id")
    edge_id: uuid.UUID = Field(foreign_key="edges.id")

    transport_type: str
    queue_level: str
    vehicle_availability: str
    estimated_wait_time: int

    image_url: Optional[str] = None
    additional_message: Optional[str] = None

    gps_lat: Optional[float] = None
    gps_lng: Optional[float] = None
    is_verified_location: bool = False

    device_timestamp: Optional[datetime] = None # type: ignore
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # 🔗 relationships
    user: Optional[User] = Relationship(back_populates="reports")
    edge: Optional[Edge] = Relationship(back_populates="reports")
