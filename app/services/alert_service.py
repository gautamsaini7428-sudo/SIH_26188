"""
Persistent Alert Management Service — SIH26188
Module 3: Real Security Alerts, Lifecycle & Supervisor Review
"""

import json
import logging
from datetime import datetime, timezone
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_

from app.models import Alert, Verification
from app.schemas import ValidationResult, BiometricResult
from app.services.audit_log import log_verification

logger = logging.getLogger(__name__)


def _determine_alert_severity_and_title(
    verdict: str,
    risk_score: int,
    tampering_score: int,
    face_match_score: Optional[int],
    doc_type: str,
    issues: List[str],
) -> Tuple[str, str]:
    """
    Authoritative severity determination derived directly from verification results:
    - CRITICAL: FAKE verdict, severe tampering (>70), critical face mismatch (<50), or risk >= 80
    - HIGH: REJECTED verdict, high risk (66-79), document category mismatch
    - MEDIUM: SUSPICIOUS verdict, moderate risk (31-65), borderline face match or moderate tampering
    - LOW: (Clean documents do not generate high/critical alerts)
    """
    has_watchlist = any("BLACKLIST" in i.upper() or "WATCHLIST" in i.upper() for i in issues)
    has_cat_mismatch = any("DOCUMENT TYPE MISMATCH" in i.upper() or "CATEGORY MISMATCH" in i.upper() for i in issues)

    if (
        verdict == "FAKE"
        or tampering_score >= 70
        or (face_match_score is not None and face_match_score < 50)
        or risk_score >= 80
        or has_watchlist
    ):
        severity = "CRITICAL"
        title = f"CRITICAL SECURITY ALERT — Fraudulent {doc_type} Flagged"
    elif (
        verdict == "REJECTED"
        or risk_score >= 66
        or has_cat_mismatch
    ):
        severity = "HIGH"
        title = f"HIGH RISK ALERT — {doc_type} Rejected by Intake Gate"
    elif verdict == "SUSPICIOUS" or risk_score >= 31:
        severity = "MEDIUM"
        title = f"SUSPICIOUS ACTIVITY — {doc_type} Under Manual Review"
    else:
        severity = "LOW"
        title = f"INFORMATIONAL — {doc_type} Verification Recorded"

    return severity, title


def _extract_alert_indicators(
    verdict: str,
    risk_score: int,
    tampering_score: int,
    face_match_score: Optional[int],
    doc_type: str,
    issues: List[str],
    reason: Optional[str],
) -> List[str]:
    """Compile human-readable forensic indicators for the supervisor."""
    indicators = []

    if any("DOCUMENT TYPE MISMATCH" in i.upper() for i in issues):
        for i in issues:
            if "DOCUMENT TYPE MISMATCH" in i.upper():
                indicators.append(i)
    elif any("CATEGORY MISMATCH" in i.upper() for i in issues):
        for i in issues:
            if "CATEGORY MISMATCH" in i.upper():
                indicators.append(i)

    if face_match_score is not None:
        if face_match_score < 50:
            indicators.append(f"Critical facial mismatch: {face_match_score}% (Rejection threshold: 50%)")
        elif face_match_score < 70:
            indicators.append(f"Borderline facial correlation: {face_match_score}%")

    if tampering_score >= 70:
        indicators.append(f"Severe digital forgery detected: {tampering_score}/100 tampering score")
    elif tampering_score >= 40:
        indicators.append(f"Moderate compression/splicing anomaly: {tampering_score}/100 tampering score")

    for issue in issues:
        if "BLACKLIST" in issue.upper() or "WATCHLIST" in issue.upper():
            indicators.append(f"Security Watchlist Hit: {issue}")
        elif "EXPIRED" in issue.upper():
            indicators.append(issue)
        elif "MRZ" in issue.upper() and "CHECKSUM" in issue.upper():
            indicators.append(issue)

    if risk_score >= 66:
        indicators.append(f"High composite risk score: {risk_score}/100")

    if not indicators and reason:
        indicators.append(reason)

    return indicators


async def create_alert_for_verification(
    db: AsyncSession,
    verification: Verification,
    validation_result: Optional[ValidationResult] = None,
    biometric_result: Optional[BiometricResult] = None,
) -> Optional[Alert]:
    """
    Automatically generate and persist an Alert for verifications exhibiting security concerns.
    Low-risk clean documents (GENUINE + risk <= 30) do not generate high/critical alerts.
    """
    verdict = verification.verdict or "GENUINE"
    risk_score = verification.risk_score or 0
    tampering_score = verification.tampering_score or 0
    face_score = verification.face_match_score
    doc_type = verification.document_type or "IDENTITY_DOCUMENT"

    issues = validation_result.issues if validation_result else []

    # Rule: Genuine documents with low risk (0-30) do not trigger security alerts
    if verdict == "GENUINE" and risk_score <= 30 and tampering_score < 40 and (face_score is None or face_score >= 70):
        return None

    severity, title = _determine_alert_severity_and_title(
        verdict=verdict,
        risk_score=risk_score,
        tampering_score=tampering_score,
        face_match_score=face_score,
        doc_type=doc_type,
        issues=issues,
    )

    indicators = _extract_alert_indicators(
        verdict=verdict,
        risk_score=risk_score,
        tampering_score=tampering_score,
        face_match_score=face_score,
        doc_type=doc_type,
        issues=issues,
        reason=verification.reason,
    )

    message = (
        f"{title}.\n"
        f"Verdict: {verdict} | Risk Score: {risk_score}/100 | "
        f"Officer: {verification.officer_email or 'Unassigned'} | "
        f"Checkpoint: {verification.checkpoint_location or 'Unknown'}.\n"
        + ("Indicators:\n- " + "\n- ".join(indicators) if indicators else "")
    )

    alert = Alert(
        verification_id=verification.id,
        severity=severity,
        status="UNREVIEWED",
        title=title,
        message=message,
        document_number=verification.extracted_id_number,
        person_name=verification.extracted_name,
        document_type=doc_type,
        officer_email=verification.officer_email,
        checkpoint=verification.checkpoint_location,
        risk_score=risk_score,
        verdict=verdict,
        face_score=face_score,
        tampering_score=tampering_score,
        details_json=json.dumps(indicators),
        created_at=datetime.utcnow(),
    )

    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return alert


async def get_alerts(
    db: AsyncSession,
    status_filter: Optional[str] = None,
    severity_filter: Optional[str] = None,
    checkpoint_filter: Optional[str] = None,
    verification_id: Optional[int] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
) -> Tuple[List[Alert], int, Dict[str, int]]:
    """
    Retrieve paginated alerts with filtering and summary metrics.
    """
    query = select(Alert)

    # Apply filters
    if status_filter:
        query = query.where(Alert.status == status_filter.upper())
    if severity_filter:
        query = query.where(Alert.severity == severity_filter.upper())
    if checkpoint_filter:
        query = query.where(Alert.checkpoint.ilike(f"%{checkpoint_filter}%"))
    if verification_id:
        query = query.where(Alert.verification_id == verification_id)
    if date_from:
        try:
            df = datetime.fromisoformat(date_from)
            query = query.where(Alert.created_at >= df)
        except Exception:
            pass
    if date_to:
        try:
            dt = datetime.fromisoformat(date_to)
            query = query.where(Alert.created_at <= dt)
        except Exception:
            pass

    # Count total matching
    count_query = select(func.count()).select_from(query.subquery())
    total_res = await db.execute(count_query)
    total = total_res.scalar() or 0

    # Paginate and order by newest first
    offset = (page - 1) * limit
    ordered_query = query.order_by(desc(Alert.created_at)).offset(offset).limit(limit)
    res = await db.execute(ordered_query)
    items = list(res.scalars().all())

    # Summary metrics across all alerts in DB
    metrics_query = select(
        func.count().label("total"),
        func.count().filter(Alert.status == "UNREVIEWED").label("unreviewed"),
        func.count().filter(Alert.severity == "CRITICAL").label("critical"),
        func.count().filter(Alert.severity == "HIGH").label("high"),
        func.count().filter(Alert.severity == "MEDIUM").label("medium"),
        func.count().filter(Alert.status == "RESOLVED").label("resolved"),
        func.count().filter(Alert.status == "ESCALATED").label("escalated"),
    ).select_from(Alert)

    m_res = await db.execute(metrics_query)
    m_row = m_res.one_or_none()
    metrics = {
        "total": m_row.total if m_row else 0,
        "unreviewed": m_row.unreviewed if m_row else 0,
        "critical": m_row.critical if m_row else 0,
        "high": m_row.high if m_row else 0,
        "medium": m_row.medium if m_row else 0,
        "resolved": m_row.resolved if m_row else 0,
        "escalated": m_row.escalated if m_row else 0,
    }

    return items, total, metrics


async def get_alert_by_id(db: AsyncSession, alert_id: int) -> Optional[Alert]:
    """Retrieve a single alert by ID."""
    res = await db.execute(select(Alert).where(Alert.id == alert_id))
    return res.scalar_one_or_none()


async def review_alert(
    db: AsyncSession,
    alert_id: int,
    reviewer_email: str,
    new_status: str,
    notes: Optional[str] = None,
) -> Optional[Alert]:
    """
    Supervisor action: Review, resolve, or escalate an alert.
    Records reviewer, timestamp, and audit trail without altering the original AI verification record.
    """
    alert = await get_alert_by_id(db, alert_id)
    if not alert:
        return None

    valid_statuses = ("UNREVIEWED", "REVIEWED", "RESOLVED", "ESCALATED")
    status_upper = new_status.upper()
    if status_upper not in valid_statuses:
        status_upper = "REVIEWED"

    alert.status = status_upper
    alert.reviewed_by = reviewer_email
    alert.reviewed_at = datetime.utcnow()
    if notes:
        alert.review_notes = notes
    if status_upper == "RESOLVED":
        alert.resolved_at = datetime.utcnow()

    await db.commit()
    await db.refresh(alert)

    # Append supervisor review event to the immutable tamper-evident SHA-256 audit log
    try:
        log_verification({
            "document_id": f"CASE-26188-{alert.verification_id or alert.id:03d}",
            "verdict": "VERIFIED" if status_upper == "RESOLVED" else "SUSPECTED",
            "tampering_score": alert.tampering_score or 0,
            "face_match_score": alert.face_score or 0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
    except Exception as log_err:
        logger.warning(f"Failed to record audit log for alert review #{alert_id}: {log_err}")

    return alert
