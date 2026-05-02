from __future__ import annotations

from typing import List
import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.db.postgran import SessionType
from app.services.node_service import create_node, create_edge
from app.schemas.node import (
    NodeCreateSchema,
    NodeReadSchema,
    EdgeCreateSchema,
    EdgeReadSchema,
)
from sqlmodel import select
from app.models.node import Node
from app.models.edge import Edge


router = APIRouter(prefix="/graph", tags=["Graph"])


@router.post("/nodes", response_model=NodeReadSchema, status_code=201)
def post_node(payload: NodeCreateSchema, db: SessionType):
    node = create_node(payload.dict(), db)
    return NodeReadSchema(
        id=node.id,
        name=node.name,
        latitude=node.latitude,
        longitude=node.longitude,
        is_terminal=node.is_terminal,
    )


@router.get("/nodes", response_model=List[NodeReadSchema])
def list_nodes(db: SessionType):
    with db as session:
        results = session.exec(select(Node)).all()
    return [NodeReadSchema(**r.dict()) for r in results]


@router.post("/edges", response_model=EdgeReadSchema, status_code=201)
def post_edge(payload: EdgeCreateSchema, db: SessionType):
    edge = create_edge(payload.dict(), db)
    return EdgeReadSchema(
        id=edge.id,
        from_node_id=edge.from_node_id,
        to_node_id=edge.to_node_id,
        transport_types=edge.transport_types,
        base_travel_time_min=edge.base_travel_time_min,
        base_travel_time_max=edge.base_travel_time_max,
        base_cost_min=edge.base_cost_min,
        base_cost_max=edge.base_cost_max,
    )


@router.get("/edges/{edge_id}", response_model=EdgeReadSchema)
def get_edge(edge_id: uuid.UUID, db: SessionType):
    with db as session:
        result = session.get(Edge, edge_id)
        if not result:
            raise HTTPException(status_code=404, detail="edge not found")
    return EdgeReadSchema(**result.dict())
