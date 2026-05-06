from enum import Enum
from typing import List, Optional
import uuid

from pydantic import BaseModel


class Label(str, Enum):
    FASTEST = "FASTEST"
    CHEAPEST = "CHEAPEST"
    MOST_RELIABLE = "MOST_RELIABLE"
    BALANCED = "BALANCED"


class PathRequest(BaseModel):
    from_node_id: uuid.UUID
    to_node_id: uuid.UUID
    preference: Optional[str] = "balanced"  # fastest|cheapest|reliable|balanced


class EdgeExplanation(BaseModel):
    edge: str
    mode: str
    time: float
    cost: float
    risk: float
    confidence: float
    queue_level: Optional[str] = None
    vehicle_availability: Optional[str] = None
    num_reports: Optional[int] = None
    stability: Optional[str] = None
    note: Optional[str] = None


class RouteResponse(BaseModel):
    path: List[uuid.UUID]
    total_time: float
    total_cost: float
    total_risk: float
    labels: List[Label]
    explanation: List[EdgeExplanation]
