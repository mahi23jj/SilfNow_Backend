from typing import Dict

import datetime
from typing import Optional
import uuid

from pydantic import Field
from sqlmodel import Relationship, SQLModel

from app.models.edge import Edge
from app.models.user import User

class EdgeStatus(SQLModel, table=True):
    __tablename__ = "edge_status"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    edge_id: uuid.UUID = Field(foreign_key="edges.id", index=True)

    transport_type: str

    data: dict = Field(default_factory=dict)

    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # 🔗 relationship
    edge: Optional[Edge] = Relationship(back_populates="status")
