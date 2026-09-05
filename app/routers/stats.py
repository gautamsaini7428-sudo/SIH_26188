from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.database import get_db
from app.services.verification import get_verification_stats
from app.auth import get_current_user
from app.schemas import StatsResponse
from app.models import User

router = APIRouter(prefix="", tags=["stats"])


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    date_from: Optional[str] = Query(None, description="Start date (ISO format: YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (ISO format: YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StatsResponse:
    """
    Get verification statistics for dashboard.

    Requires officer or supervisor authentication (session cookie or Bearer token).

    Returns counts of Genuine, Suspicious, Fake, Rejected and counts by document_type.
    """
    stats = await get_verification_stats(db, date_from, date_to)

    return StatsResponse(
        genuine=stats.get("genuine", 0),
        suspicious=stats.get("suspicious", 0),
        fake=stats.get("fake", 0),
        rejected=stats.get("rejected", 0),
        total=stats.get("total", 0),
        high_risk=stats.get("high_risk", 0),
        avg_processing_time_ms=stats.get("avg_processing_time_ms", 0),
        by_document_type=stats.get("by_document_type", {}),
        by_checkpoint=stats.get("by_checkpoint", {}),
        daily_volume=stats.get("daily_volume", []),
        alerts_total=stats.get("alerts_total", 0),
        alerts_resolved=stats.get("alerts_resolved", 0),
        period_from=date_from and __import__("datetime").datetime.fromisoformat(date_from) or None,
        period_to=date_to and __import__("datetime").datetime.fromisoformat(date_to) or None,
    )