from typing import List
import uuid

from sqlmodel import Field, Relationship, SQLModel

from app.models.edge import Edge


class Node(SQLModel, table=True):
    __tablename__ = "nodes"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    name: str
    latitude: float
    longitude: float
    is_terminal: bool = True

    # 🔗 graph relationships
    outgoing_edges: List["Edge"] = Relationship(
        back_populates="from_node",
        sa_relationship_kwargs={"foreign_keys": "[Edge.from_node_id]"}
    )

    incoming_edges: List["Edge"] = Relationship(
        back_populates="to_node",
        sa_relationship_kwargs={"foreign_keys": "[Edge.to_node_id]"}
    )
