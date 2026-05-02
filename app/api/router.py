from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.report import router as report_router
from app.api.v1.endpoints.node import router as node_router


api_router = APIRouter()

api_router.include_router(auth_router, prefix="/api/v1")
api_router.include_router(report_router, prefix="/api/v1")
api_router.include_router(node_router, prefix="/api/v1")


