"""Health check. Android expects GET /health -> { status: \"ok\" }."""
from fastapi import APIRouter

from app.schemas.recipe import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ok")
