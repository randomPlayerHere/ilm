from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from app.db.base import async_session_factory

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Returns 200 with database connectivity status."""
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "unavailable"
    return {"status": "ok", "db": db_status}
