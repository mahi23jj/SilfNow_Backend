from __future__ import annotations

from typing import Optional, List
import uuid

from pydantic import BaseModel, Field


class NodeCreateSchema(BaseModel):
    name: str
    latitude: float
    longitude: float
    is_terminal: Optional[bool] = True


class NodeReadSchema(BaseModel):
    id: uuid.UUID
    name: str
    latitude: float
    longitude: float
    is_terminal: bool


class EdgeCreateSchema(BaseModel):
    from_node_id: uuid.UUID
    to_node_id: uuid.UUID
    transport_types: List[str] = Field(..., min_length=1)
    base_travel_time_min: int
    base_travel_time_max: int
    base_cost_min: float
    base_cost_max: float


class EdgeReadSchema(BaseModel):
    id: uuid.UUID
    from_node_id: uuid.UUID
    to_node_id: uuid.UUID
    transport_types: List[str]
    base_travel_time_min: int
    base_travel_time_max: int
    base_cost_min: float
    base_cost_max: float
