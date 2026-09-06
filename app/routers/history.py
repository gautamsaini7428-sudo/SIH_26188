from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.database import get_db
from app.services.verification import get_verification_history
from app.auth import get_current_user
from app.schemas import (
    HistoryResponse,
    VerificationHistoryItem,
    VerifyResponse,
    ValidationResult,
    TamperingRegion,
    SecurityCheckItem,
)
from app.models import User, Verification
import json


router = APIRouter(prefix="", tags=["history"])


@router.get("/history", response_model=HistoryResponse)
async def get_history(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    verdict: Optional[str] = Query(None, description="Filter by verdict: GENUINE, SUSPICIOUS, FAKE, REJECTED"),
    document_type: Optional[str] = Query(None, description="Filter by document_type: PASSPORT, VISA, NATIONAL_ID, DRIVING_LICENSE, PERMIT"),
    checkpoint_location: Optional[str] = Query(None, description="Filter by checkpoint location name"),
    officer_email: Optional[str] = Query(None, description="Filter by screening officer email"),
    q: Optional[str] = Query(None, description="Search term by subject name, ID number, filename, case ID, or officer"),
    date_from: Optional[str] = Query(None, description="Start date (ISO format: YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (ISO format: YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> HistoryResponse:
    """
    Get paginated verification history with filters for date range, verdict, document_type, checkpoint_location, officer_email, and search term.
    """
    if verdict and verdict not in ("GENUINE", "SUSPICIOUS", "FAKE", "REJECTED"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verdict filter. Must be GENUINE, SUSPICIOUS, FAKE, or REJECTED",
        )

    items, total = await get_verification_history(
        db=db,
        page=page,
        limit=limit,
        verdict=verdict,
        document_type=document_type,
        checkpoint_location=checkpoint_location,
        officer_email=officer_email,
        search_query=q,
        date_from=date_from,
        date_to=date_to,
    )

    total_pages = (total + limit - 1) // limit

    return HistoryResponse(
        items=[
            VerificationHistoryItem(
                id=item.id,
                timestamp=item.timestamp,
                filename=item.filename,
                document_type=item.document_type,
                checkpoint_location=item.checkpoint_location,
                officer_email=item.officer_email,
                extracted_name=item.extracted_name,
                extracted_id_number=item.extracted_id_number,
                tampering_score=item.tampering_score,
                face_match_score=item.face_match_score,
                risk_score=item.risk_score,
                verdict=item.verdict,
                reason=item.reason,
                processing_time_ms=item.processing_time_ms,
            )
            for item in items
        ],
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
    )


@router.get("/verification/{verification_id}", response_model=VerifyResponse)
async def get_single_verification(
    verification_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> VerifyResponse:
    """Retrieve the full canonical verification result by ID for persistence and page reloads."""
    from sqlalchemy import select

    res = await db.execute(select(Verification).where(Verification.id == verification_id))
    record = res.scalar_one_or_none()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Verification record with ID {verification_id} not found.",
        )

    # 1. If full canonical response JSON is stored, return it directly
    if record.full_response_json:
        try:
            return VerifyResponse.model_validate_json(record.full_response_json)
        except Exception:
            pass

    # 2. Reconstruct canonical VerifyResponse from DB fields
    extracted_fields = {}
    if record.extracted_fields_json:
        try:
            extracted_fields = json.loads(record.extracted_fields_json)
        except Exception:
            pass
    if not extracted_fields:
        if record.extracted_name:
            extracted_fields["name"] = record.extracted_name
        if record.extracted_id_number:
            extracted_fields["id_number"] = record.extracted_id_number
        if record.extracted_dob:
            extracted_fields["dob"] = record.extracted_dob
        if record.extracted_address:
            extracted_fields["address"] = record.extracted_address

    tampering_regions = []
    if record.tampering_regions:
        try:
            regions_raw = json.loads(record.tampering_regions)
            tampering_regions = [TamperingRegion(x=r["x"], y=r["y"], w=r["w"], h=r["h"]) for r in regions_raw]
        except Exception:
            pass

    risk_score = record.risk_score or 0
    from app.utils.verdict import get_risk_level
    risk_level = get_risk_level(risk_score)

    return VerifyResponse(
        verification_id=record.id,
        document_type=record.document_type or "DRIVING_LICENSE",
        expected_document_type=record.document_type or "DRIVING_LICENSE",
        detected_document_type=record.document_type or "DRIVING_LICENSE",
        category_match=True,
        extracted_fields=extracted_fields,
        validation=ValidationResult(format_valid=True, expiry_valid=True, issues=[]),
        tampering_score=record.tampering_score or 0,
        tampering_regions=tampering_regions,
        heatmap_image_base64="",
        face_match_score=record.face_match_score,
        risk_score=risk_score,
        risk_level=risk_level,
        risk_factors=[],
        verdict=record.verdict,
        reason=record.reason,
        security_checks=[],
        processing_time_ms=record.processing_time_ms,
        case_number=f"CASE-26188-{record.id:03d}",
        checkpoint_location=record.checkpoint_location,
        officer_email=record.officer_email,
    )


@router.get("/verification/{verification_id}/export")
@router.get("/verifications/{verification_id}/export")
async def export_verification_dossier(
    verification_id: int,
    format: str = Query("json", description="Export format: json | csv | txt"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Export official forensic screening dossier for border law enforcement records.
    Provides structured JSON or summary text/CSV audit file download.
    """
    from fastapi.responses import Response
    from sqlalchemy import select

    res = await db.execute(select(Verification).where(Verification.id == verification_id))
    record = res.scalar_one_or_none()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Verification record with ID {verification_id} not found.",
        )

    case_num = f"CASE-26188-{record.id:03d}"
    dossier = {
        "case_number": case_num,
        "verification_id": record.id,
        "timestamp": record.timestamp.isoformat() if record.timestamp else None,
        "screening_officer": record.officer_email or current_user.email,
        "checkpoint_location": record.checkpoint_location or current_user.checkpoint_location,
        "verdict": record.verdict,
        "risk_score": record.risk_score,
        "verdict_reason": record.reason,
        "document_type": record.document_type,
        "extracted_identity": {
            "name": record.extracted_name,
            "document_number": record.extracted_id_number,
            "dob": record.extracted_dob,
            "address": record.extracted_address,
        },
        "forensic_signals": {
            "tampering_score": record.tampering_score,
            "face_match_score": record.face_match_score,
            "processing_time_ms": record.processing_time_ms,
        },
        "audit_authority": "Ministry of Home Affairs - Smart India Hackathon 26188",
    }

    fmt = format.lower().strip()
    if fmt == "csv":
        import io
        import csv
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Field", "Value"])
        for k, v in dossier.items():
            if isinstance(v, dict):
                for sub_k, sub_v in v.items():
                    writer.writerow([f"{k}.{sub_k}", sub_v])
            else:
                writer.writerow([k, v])
        content = output.getvalue()
        return Response(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{case_num}_dossier.csv"'},
        )
    elif fmt == "txt":
        lines = [
            "=" * 60,
            f"BORDER SECURITY FORENSIC DOSSIER: {case_num}",
            "=" * 60,
            f"Verdict:              {record.verdict}",
            f"Risk Score:           {record.risk_score}/100",
            f"Reason:               {record.reason}",
            f"Document Type:        {record.document_type}",
            f"Subject Name:         {record.extracted_name or 'N/A'}",
            f"Document ID:          {record.extracted_id_number or 'N/A'}",
            f"DOB:                  {record.extracted_dob or 'N/A'}",
            f"Tampering Score:      {record.tampering_score}%",
            f"Face Match Score:     {record.face_match_score if record.face_match_score is not None else 'N/A'}%",
            f"Screening Officer:    {record.officer_email}",
            f"Checkpoint:           {record.checkpoint_location}",
            f"Timestamp:            {record.timestamp}",
            "=" * 60,
        ]
        return Response(
            content="\n".join(lines),
            media_type="text/plain",
            headers={"Content-Disposition": f'attachment; filename="{case_num}_dossier.txt"'},
        )
    else:
        return Response(
            content=json.dumps(dossier, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{case_num}_dossier.json"'},
        )