from typing import List, Optional
import uuid

from sqlalchemy import Column, JSON
from sqlmodel import Field, Relationship, SQLModel

from app.models.edge_status import EdgeStatus
from app.models.node import Node
from app.models.report import Report
from app.models.user import User

class Edge(SQLModel, table=True):
    __tablename__ = "edges"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    from_node_id: uuid.UUID = Field(foreign_key="nodes.id", index=True)
    to_node_id: uuid.UUID = Field(foreign_key="nodes.id", index=True)

    transport_types: List[str] = Field(
        default_factory=lambda: ["taxi", "bus"],
        sa_column=Column(JSON, nullable=False),
    )

    base_travel_time_min: int
    base_travel_time_max: int

    base_cost_min: float
    base_cost_max: float

    # 🔗 relationships
    from_node: Optional[Node] = Relationship(
        back_populates="outgoing_edges",
        sa_relationship_kwargs={"foreign_keys": "[Edge.from_node_id]"}
    )

    to_node: Optional[Node] = Relationship(
        back_populates="incoming_edges",
        sa_relationship_kwargs={"foreign_keys": "[Edge.to_node_id]"}
    )

    status: List["EdgeStatus"] = Relationship(back_populates="edge")
    reports: List["Report"] = Relationship(back_populates="edge")
