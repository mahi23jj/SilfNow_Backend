from fastapi import APIRouter, HTTPException
from typing import List

from app.db.postgran import SessionType
from app.schemas.route import PathRequest, RouteResponse
from app.services.path_ranking_service import compute_routes

router = APIRouter()


@router.post("/routes", response_model=List[RouteResponse])
def post_routes(req: PathRequest, session: SessionType):
    # validate nodes are UUIDs handled by Pydantic
    try:
        results = compute_routes(req, session)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # convert label strings to RouteResponse expects list of Label values already handled
    return results
