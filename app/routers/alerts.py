"""
Security Alerts API Router — SIH26188
Handles alert feeds, detail retrieval, and supervisor-only review & escalation.
"""

import json
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.database import get_db
from app.auth import get_current_user, get_current_supervisor
from app.models import User, Alert
from app.schemas import (
    AlertDTO,
    AlertListResponse,
    AlertReviewRequest,
    AlertStatsResponse,
)
from app.services.alert_service import (
    get_alerts,
    get_alert_by_id,
    review_alert,
)

router = APIRouter(prefix="", tags=["alerts"])


def _to_alert_dto(alert: Alert) -> AlertDTO:
    details: List[str] = []
    if alert.details_json:
        try:
            parsed = json.loads(alert.details_json)
            if isinstance(parsed, list):
                details = parsed
        except Exception:
            pass

    return AlertDTO(
        id=alert.id,
        verification_id=alert.verification_id,
        case_number=f"CASE-26188-{alert.verification_id or alert.id:03d}",
        severity=alert.severity,
        status=alert.status,
        title=alert.title,
        message=alert.message,
        document_number=alert.document_number,
        person_name=alert.person_name,
        document_type=alert.document_type,
        officer_email=alert.officer_email,
        checkpoint=alert.checkpoint,
        risk_score=alert.risk_score,
        verdict=alert.verdict,
        face_score=alert.face_score,
        tampering_score=alert.tampering_score,
        details=details,
        created_at=alert.created_at,
        reviewed_at=alert.reviewed_at,
        reviewed_by=alert.reviewed_by,
        review_notes=alert.review_notes,
        resolved_at=alert.resolved_at,
    )


@router.get("/alerts", response_model=AlertListResponse)
async def list_alerts(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (UNREVIEWED, REVIEWED, RESOLVED, ESCALATED)"),
    severity_filter: Optional[str] = Query(None, alias="severity", description="Filter by severity (CRITICAL, HIGH, MEDIUM, LOW)"),
    checkpoint_filter: Optional[str] = Query(None, alias="checkpoint", description="Filter by checkpoint name"),
    verification_id: Optional[int] = Query(None, description="Filter by verification record ID"),
    date_from: Optional[str] = Query(None, description="ISO start date"),
    date_to: Optional[str] = Query(None, description="ISO end date"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AlertListResponse:
    """
    Retrieve real persisted security alerts from database.
    Supports filtering by status, severity, checkpoint, date, and verification ID.
    """
    items, total, metrics = await get_alerts(
        db=db,
        status_filter=status_filter,
        severity_filter=severity_filter,
        checkpoint_filter=checkpoint_filter,
        verification_id=verification_id,
        date_from=date_from,
        date_to=date_to,
        page=page,
        limit=limit,
    )

    return AlertListResponse(
        items=[_to_alert_dto(a) for a in items],
        total=total,
        unreviewed_count=metrics["unreviewed"],
        critical_count=metrics["critical"],
        high_count=metrics["high"],
        resolved_count=metrics["resolved"],
    )


@router.get("/alerts/stats", response_model=AlertStatsResponse)
async def get_alert_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AlertStatsResponse:
    """Get aggregated alert metrics for dashboards."""
    _, total, metrics = await get_alerts(db=db, page=1, limit=1)
    return AlertStatsResponse(
        total=metrics["total"],
        unreviewed=metrics["unreviewed"],
        critical=metrics["critical"],
        high=metrics["high"],
        medium=metrics["medium"],
        resolved=metrics["resolved"],
        escalated=metrics["escalated"],
    )


@router.get("/alerts/{alert_id}", response_model=AlertDTO)
async def get_alert_detail(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AlertDTO:
    """Retrieve full detail for a single alert."""
    alert = await get_alert_by_id(db, alert_id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert #{alert_id} not found",
        )
    return _to_alert_dto(alert)


@router.patch("/alerts/{alert_id}/review", response_model=AlertDTO)
@router.post("/alerts/{alert_id}/review", response_model=AlertDTO)
async def perform_alert_review(
    alert_id: int,
    body: AlertReviewRequest,
    db: AsyncSession = Depends(get_db),
    current_supervisor: User = Depends(get_current_supervisor),
) -> AlertDTO:
    """
    Supervisor action: Review, resolve, or escalate an alert.
    Requires SUPERVISOR role. Officers receive 403 Forbidden.
    """
    updated_alert = await review_alert(
        db=db,
        alert_id=alert_id,
        reviewer_email=current_supervisor.email,
        new_status=body.status,
        notes=body.notes,
    )

    if not updated_alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert #{alert_id} not found",
        )

    return _to_alert_dto(updated_alert)


@router.post("/alerts/mark-all-read")
async def mark_all_alerts_read(
    db: AsyncSession = Depends(get_db),
    current_supervisor: User = Depends(get_current_supervisor),
):
    """Mark all unreviewed alerts as REVIEWED. Requires supervisor role."""
    await db.execute(
        update(Alert)
        .where(Alert.status == "UNREVIEWED")
        .values(status="REVIEWED", reviewed_by=current_supervisor.email, reviewed_at=__import__("datetime").datetime.utcnow())
    )
    await db.commit()
    return {"success": True, "message": "All alerts marked as reviewed"}
