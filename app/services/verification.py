"""
Verification Orchestration Service — SIH26188

Coordinates the full document verification pipeline with fast-fail validation:
1. Save uploaded files
2. FAST-FAIL INTAKE GATE (detectable text & face presence except for VISA) -> returns verdict="REJECTED" immediately on non-documents or building sketches
3. Run OCR field extraction (type-aware for PASSPORT, VISA, NATIONAL_ID, DRIVING_LICENSE, PERMIT)
4. Run Standalone Document Validation module (format, expiry, MRZ checksum math, blacklist check)
5. Run Tampering / ELA forensic analysis (generates palette heatmap base64)
6. Run Face Match module (skip for VISA or missing selfie)
7. Compute weighted risk_score (primary output 0-100)
8. Derive verdict (GENUINE | SUSPICIOUS | FAKE | REJECTED) from risk_score + hard gates
9. Store record with checkpoint_location in SQLite database and return structured response
"""

import time
import json
import random
import logging
from datetime import datetime, timezone
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import UploadFile

from app.services.document_validator import (
    validate_identity_document,
    detect_face_presence,
)
from app.services.document_validation import validate_document
from app.services.ocr import extract_fields
from app.services.tampering import detect_tampering
from app.services.face_match import match_faces, run_biometric_evaluation
from app.services.audit_log import log_verification
from app.services.alert_service import create_alert_for_verification
from app.utils.verdict import (
    compute_risk_score,
    get_risk_level,
    compute_risk_factors,
    compute_verdict,
    generate_security_checks,
    get_verdict_reason,
)

logger = logging.getLogger(__name__)

VERDICT_TO_AUDIT_MAP = {
    "GENUINE": "VERIFIED",
    "SUSPICIOUS": "SUSPECTED",
    "FAKE": "REJECTED",
    "REJECTED": "REJECTED",
}

from app.utils.file_handler import save_upload_file
from app.models import Verification
from app.schemas import (
    VerifyResponse,
    ValidationResult,
    TamperingRegion,
    SecurityCheckItem,
    BiometricResult,
    IdentityLinkItem,
)
from app.config import get_settings


async def find_identity_links(
    db: AsyncSession,
    current_verification_id: int,
    extracted_name: Optional[str],
    extracted_id_number: Optional[str],
) -> List[IdentityLinkItem]:
    """
    Query historical verification records in DB for investigative correlations:
    - Same document number under a different name (possible identity cloning / recycling)
    - Same name presenting a different document number (possible alias / multiple credentials)
    - Prior record matches for this individual

    Returns investigative correlation items without declaring definitive identity.
    """
    links: List[IdentityLinkItem] = []
    seen_ids = set()

    clean_id = (extracted_id_number or "").strip()
    clean_name = (extracted_name or "").strip()

    # 1. Check same document number in historical records
    if clean_id and len(clean_id) >= 4:
        query_doc = select(Verification).where(
            Verification.id != current_verification_id,
            Verification.extracted_id_number == clean_id,
        ).order_by(Verification.timestamp.desc()).limit(10)

        res_doc = await db.execute(query_doc)
        for rec in res_doc.scalars().all():
            if rec.id in seen_ids:
                continue
            seen_ids.add(rec.id)
            rec_name = (rec.extracted_name or "").strip()

            if clean_name and rec_name and clean_name.lower() != rec_name.lower():
                links.append(
                    IdentityLinkItem(
                        historical_verification_id=rec.id,
                        case_number=f"CASE-26188-{rec.id:03d}",
                        historical_name=rec.extracted_name,
                        historical_document_number=rec.extracted_id_number,
                        similarity_score=95,
                        relationship_type="SAME_DOCUMENT_DIFFERENT_NAME",
                        recommendation="INVESTIGATION RECOMMENDED",
                        details=f"Historical case CASE-26188-{rec.id:03d} used document number '{clean_id}' under name '{rec.extracted_name}' (current name: '{clean_name}'). Possible credential recycling or synthetic identity.",
                    )
                )
            else:
                links.append(
                    IdentityLinkItem(
                        historical_verification_id=rec.id,
                        case_number=f"CASE-26188-{rec.id:03d}",
                        historical_name=rec.extracted_name,
                        historical_document_number=rec.extracted_id_number,
                        similarity_score=100,
                        relationship_type="PRIOR_RECORD_MATCH",
                        recommendation="INVESTIGATION RECOMMENDED",
                        details=f"Individual previously processed under case CASE-26188-{rec.id:03d}. Prior verdict: {rec.verdict} (Risk: {rec.risk_score}). Checkpoint: {rec.checkpoint_location}.",
                    )
                )

    # 2. Check same name presenting a different document number
    if clean_name and len(clean_name) >= 3:
        query_name = select(Verification).where(
            Verification.id != current_verification_id,
            Verification.extracted_name.ilike(clean_name),
        ).order_by(Verification.timestamp.desc()).limit(10)

        res_name = await db.execute(query_name)
        for rec in res_name.scalars().all():
            if rec.id in seen_ids:
                continue
            rec_id = (rec.extracted_id_number or "").strip()
            if clean_id and rec_id and clean_id.lower() != rec_id.lower():
                seen_ids.add(rec.id)
                links.append(
                    IdentityLinkItem(
                        historical_verification_id=rec.id,
                        case_number=f"CASE-26188-{rec.id:03d}",
                        historical_name=rec.extracted_name,
                        historical_document_number=rec.extracted_id_number,
                        similarity_score=80,
                        relationship_type="SAME_NAME_DIFFERENT_DOCUMENT",
                        recommendation="INVESTIGATION RECOMMENDED",
                        details=f"Subject '{clean_name}' was previously recorded with document number '{rec.extracted_id_number}' (current: '{clean_id}'). Verify dual citizenship, renewal, or alias.",
                    )
                )

    return links


async def run_verification(
    db: AsyncSession,
    id_file: UploadFile,
    document_type: str = "DRIVING_LICENSE",
    selfie_file: Optional[UploadFile] = None,
    client_ip: Optional[str] = None,
    officer_email: Optional[str] = None,
    user_checkpoint_location: Optional[str] = None,
) -> VerifyResponse:
    """
    Run the complete canonical document verification pipeline.
    """
    start_time = time.time()
    settings = get_settings()

    doc_type = document_type.upper()
    if doc_type not in ("PASSPORT", "VISA", "NATIONAL_ID", "DRIVING_LICENSE", "PERMIT"):
        doc_type = "DRIVING_LICENSE"

    # Use officer's assigned checkpoint location if provided, else random choice
    checkpoint_location = user_checkpoint_location or random.choice(settings.checkpoint_location_list)

    # 1. Save ID file to disk
    id_relative_path = await save_upload_file(id_file, "ids")
    id_full_path = settings.upload_dir + "/" + id_relative_path

    # 2. FAST-FAIL INTAKE GATE: Check if file contains valid document structure
    is_valid_doc, failure_reason = validate_identity_document(id_full_path, doc_type=doc_type)
    if not is_valid_doc:
        processing_time_ms = int((time.time() - start_time) * 1000)
        reason_msg = failure_reason or "No valid identity document detected in uploaded file"

        # Store rejected record in DB
        verification = Verification(
            filename=id_file.filename or "unknown",
            file_path=id_relative_path,
            selfie_path=None,
            document_type=doc_type,
            checkpoint_location=checkpoint_location,
            officer_email=officer_email,
            extracted_name=None,
            extracted_dob=None,
            extracted_id_number=None,
            extracted_address=None,
            extracted_confidence=None,
            extracted_fields_json=json.dumps({}),
            tampering_score=0,
            tampering_regions=None,
            heatmap_path=None,
            face_match_score=None,
            risk_score=100,
            verdict="REJECTED",
            reason=reason_msg,
            processing_time_ms=processing_time_ms,
            ip_address=client_ip,
        )
        db.add(verification)
        await db.commit()
        await db.refresh(verification)

        # Append to tamper-evident SHA-256 audit log
        try:
            log_verification({
                "document_id": f"CASE-26188-{verification.id:03d}",
                "verdict": "REJECTED",
                "tampering_score": 0,
                "face_match_score": 0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
        except Exception as log_err:
            logger.warning(f"Failed to record audit log for intake rejection: {log_err}")

        # Generate persistent alert for rejected specimen
        try:
            await create_alert_for_verification(
                db=db,
                verification=verification,
                validation_result=ValidationResult(format_valid=False, expiry_valid=False, issues=[reason_msg]),
            )
        except Exception as alert_err:
            logger.warning(f"Failed to generate alert for intake rejection: {alert_err}")

        rej_resp = VerifyResponse(
            verification_id=verification.id,
            document_type=doc_type,
            expected_document_type=doc_type,
            detected_document_type="UNKNOWN",
            category_match=False,
            extracted_fields={},
            validation=ValidationResult(format_valid=False, expiry_valid=False, issues=[reason_msg]),
            tampering_score=0,
            tampering_regions=[],
            heatmap_image_base64="",
            face_match_score=None,
            biometric=None,
            risk_score=100,
            risk_level="HIGH RISK",
            risk_factors=["INVALID_SPECIMEN"],
            verdict="REJECTED",
            reason=reason_msg,
            security_checks=[],
            processing_time_ms=processing_time_ms,
            case_number=f"CASE-26188-{verification.id:03d}",
            checkpoint_location=checkpoint_location,
            officer_email=officer_email,
        )
        verification.full_response_json = rej_resp.model_dump_json()
        await db.commit()
        return rej_resp

    # 3. Save selfie if provided and doc_type is NOT VISA
    selfie_relative_path = None
    selfie_full_path = None
    if selfie_file and doc_type != "VISA":
        selfie_relative_path = await save_upload_file(selfie_file, "selfies")
        selfie_full_path = settings.upload_dir + "/" + selfie_relative_path

    # 4. Type-Aware OCR Extraction
    ocr_result = await extract_fields(id_full_path, doc_type)
    extracted_fields_dict = ocr_result.get("fields", {})
    ocr_confidence = ocr_result.get("confidence", {})
    mrz_line1 = ocr_result.get("mrz_line1")
    mrz_line2 = ocr_result.get("mrz_line2")
    mrz_result = ocr_result.get("mrz_result")
    ocr_lines = ocr_result.get("ocr_lines")
    raw_text = ocr_result.get("raw_text")
    detected_doc_type = (ocr_result.get("detected_document_type") or "unknown").upper()

    # Category Match Calculation
    type_alias_map = {
        "PASSPORT": "PASSPORT",
        "LICENSE": "DRIVING_LICENSE",
        "DRIVING_LICENSE": "DRIVING_LICENSE",
        "VISA": "VISA",
        "ID": "NATIONAL_ID",
        "NATIONAL_ID": "NATIONAL_ID",
        "PERMIT": "PERMIT",
        "INVOICE": "INVOICE",
        "CERTIFICATE": "CERTIFICATE",
    }
    mapped_detected = type_alias_map.get(detected_doc_type, detected_doc_type)
    # An unknown classifier result is not proof that the selected category is correct.
    category_match = bool(mapped_detected == doc_type)

    # 5. Standalone Document Validation Module (Format, Expiry, MRZ Checksum, Category Match, Blacklist)
    val_result = validate_document(
        doc_type=doc_type,
        extracted_fields=extracted_fields_dict,
        file_path=id_full_path,
        mrz_line1=mrz_line1,
        mrz_line2=mrz_line2,
        mrz_result=mrz_result,
        detected_doc_type=detected_doc_type,
    )

    # 6. Tampering Forensic Detection (ELA, Frequency, Splicing)
    tampering_result = await detect_tampering(id_full_path)

    # 7. Biometric Multi-Stage Evaluation (Quality, Liveness, Spoof, ArcFace)
    biometric_result = await run_biometric_evaluation(id_full_path, selfie_full_path if doc_type != "VISA" else None)
    face_match_score = biometric_result.face_match.score if (doc_type != "VISA" and selfie_full_path and biometric_result.face_match.score is not None) else None

    liveness_failed = bool(biometric_result.liveness.status == "FAIL")
    presentation_attack_detected = bool(biometric_result.presentation_attack.detected)
    multiple_faces = bool(biometric_result.face_count > 1)
    is_low_quality = bool(biometric_result.quality.status == "LOW_QUALITY")

    # 8. Calculate Primary Risk Score (0-100) & Risk Level
    risk_score = compute_risk_score(
        tampering_score=tampering_result.score,
        face_match_score=face_match_score if doc_type != "VISA" else None,
        validation_issues_count=len(val_result.issues),
        liveness_failed=liveness_failed,
        presentation_attack_detected=presentation_attack_detected,
        category_mismatch=not category_match,
        is_low_quality=is_low_quality,
        is_expired=bool(not val_result.expiry_valid),
    )
    risk_level = get_risk_level(risk_score)

    risk_factors = compute_risk_factors(
        tampering_score=tampering_result.score,
        face_match_score=face_match_score if doc_type != "VISA" else None,
        validation=val_result,
        liveness_failed=liveness_failed,
        presentation_attack_detected=presentation_attack_detected,
        multiple_faces=multiple_faces,
        face_obstructed=False,
        category_mismatch=not category_match,
        is_low_quality=is_low_quality,
    )

    # 9. Generate Security Checks
    raw_checks = generate_security_checks(
        tampering_score=tampering_result.score,
        face_match_score=face_match_score if doc_type != "VISA" else None,
        ocr_confidence=ocr_confidence,
        validation=val_result,
    )

    security_checks = [
        SecurityCheckItem(
            id=c["id"],
            name=c["name"],
            category=c["category"],
            status=c["status"],
            score=c["score"],
            description=c["description"],
        )
        for c in raw_checks
    ]

    # 10. Derive Final Verdict
    verdict = compute_verdict(
        risk_score=risk_score,
        tampering_score=tampering_result.score,
        face_match_score=face_match_score if doc_type != "VISA" else None,
        validation=val_result,
        security_checks=raw_checks,
        category_mismatch=not category_match,
    )

    # Hard Gate overrides for presentation attacks or no-face
    if not category_match:
        verdict = "REJECTED"
    elif presentation_attack_detected:
        verdict = "FAKE"
    elif biometric_result.status == "REJECTED" and verdict == "GENUINE":
        verdict = "SUSPICIOUS"

    verdict_reason = get_verdict_reason(
        verdict=verdict,
        risk_score=risk_score,
        tampering_score=tampering_result.score,
        face_match_score=face_match_score if doc_type != "VISA" else None,
        validation=val_result,
        security_checks=raw_checks,
        category_mismatch=not category_match,
        selected_doc_type=doc_type,
        detected_doc_type=mapped_detected,
    )

    if not category_match:
        verdict_reason = f"REJECTED: DOCUMENT TYPE MISMATCH: Selected {doc_type} but detected {mapped_detected}"
    elif presentation_attack_detected:
        verdict_reason = f"{verdict}: Presentation attack detected ({biometric_result.presentation_attack.details})"

    # 11. Calculate processing time
    processing_time_ms = int((time.time() - start_time) * 1000)

    # 12. Store in Database
    name_val = str(extracted_fields_dict.get("name", ""))
    dob_val = str(extracted_fields_dict.get("dob", extracted_fields_dict.get("date_of_birth", "")))
    id_val = str(extracted_fields_dict.get("id_number", extracted_fields_dict.get("passport_number", extracted_fields_dict.get("visa_number", extracted_fields_dict.get("document_number", "")))))
    addr_val = str(extracted_fields_dict.get("address", ""))

    verification = Verification(
        filename=id_file.filename or "unknown",
        file_path=id_relative_path,
        selfie_path=selfie_relative_path,
        document_type=doc_type,
        checkpoint_location=checkpoint_location,
        officer_email=officer_email,
        extracted_name=name_val,
        extracted_dob=dob_val,
        extracted_id_number=id_val,
        extracted_address=addr_val,
        extracted_confidence=json.dumps(ocr_confidence),
        extracted_fields_json=json.dumps(extracted_fields_dict),
        tampering_score=tampering_result.score,
        tampering_regions=json.dumps([
            {
                "x": r.get("x") if isinstance(r, dict) else r.x,
                "y": r.get("y") if isinstance(r, dict) else r.y,
                "w": r.get("w") if isinstance(r, dict) else r.w,
                "h": r.get("h") if isinstance(r, dict) else r.h,
                "field": r.get("field") if isinstance(r, dict) else getattr(r, "field", None),
                "confidence": r.get("confidence") if isinstance(r, dict) else getattr(r, "confidence", None),
                "reason": r.get("reason") if isinstance(r, dict) else getattr(r, "reason", None),
            }
            for r in tampering_result.regions
        ]),
        heatmap_path=tampering_result.heatmap_path.replace(settings.upload_dir + "/", "") if tampering_result.heatmap_path else None,
        face_match_score=face_match_score if doc_type != "VISA" else None,
        risk_score=risk_score,
        verdict=verdict,
        reason=verdict_reason,
        processing_time_ms=processing_time_ms,
        ip_address=client_ip,
    )
    db.add(verification)
    await db.commit()
    await db.refresh(verification)

    # 13. Append to tamper-evident SHA-256 audit log
    audit_verdict = VERDICT_TO_AUDIT_MAP.get(verdict, "ERROR")
    try:
        log_verification({
            "document_id": f"CASE-26188-{verification.id:03d}",
            "verdict": audit_verdict,
            "tampering_score": int(tampering_result.score),
            "face_match_score": int(face_match_score) if face_match_score is not None else 0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
    except Exception as log_err:
        logger.warning(f"Failed to record audit log: {log_err}")

    # 13.5. Generate persistent Alert for security findings
    try:
        await create_alert_for_verification(
            db=db,
            verification=verification,
            validation_result=val_result,
            biometric_result=biometric_result,
        )
    except Exception as alert_err:
        logger.warning(f"Failed to generate alert for verification #{verification.id}: {alert_err}")

    # 13.6. Identity Link Analysis (Investigative correlation against historical records)
    identity_links = []
    try:
        identity_links = await find_identity_links(
            db=db,
            current_verification_id=verification.id,
            extracted_name=name_val,
            extracted_id_number=id_val,
        )
    except Exception as link_err:
        logger.warning(f"Failed to compute identity links: {link_err}")

    # 14. Build canonical VerifyResponse
    final_response = VerifyResponse(
        verification_id=verification.id,
        document_type=doc_type,
        expected_document_type=doc_type,
        detected_document_type=detected_doc_type,
        category_match=category_match,
        extracted_fields=extracted_fields_dict,
        validation=val_result,
        tampering_score=tampering_result.score,
        tampering_regions=[
            TamperingRegion(
                x=r.get("x") if isinstance(r, dict) else r.x,
                y=r.get("y") if isinstance(r, dict) else r.y,
                w=r.get("w") if isinstance(r, dict) else r.w,
                h=r.get("h") if isinstance(r, dict) else r.h,
                field=r.get("field") if isinstance(r, dict) else getattr(r, "field", None),
                confidence=r.get("confidence") if isinstance(r, dict) else getattr(r, "confidence", None),
                reason=r.get("reason") if isinstance(r, dict) else getattr(r, "reason", None),
            )
            for r in tampering_result.regions
        ],
        heatmap_image_base64=tampering_result.heatmap_base64,
        face_match_score=face_match_score if doc_type != "VISA" else None,
        biometric=biometric_result,
        risk_score=risk_score,
        risk_level=risk_level,
        risk_factors=risk_factors,
        verdict=verdict,
        reason=verdict_reason,
        security_checks=security_checks,
        identity_links=identity_links,
        processing_time_ms=processing_time_ms,
        case_number=f"CASE-26188-{verification.id:03d}",
        checkpoint_location=checkpoint_location,
        officer_email=officer_email,
        mrz=mrz_result,
        ocr_lines=ocr_lines,
        raw_text=raw_text,
    )

    # Store complete response in DB for persistent reload
    verification.full_response_json = final_response.model_dump_json()
    await db.commit()

    return final_response


async def get_verification_history(
    db: AsyncSession,
    page: int = 1,
    limit: int = 20,
    verdict: Optional[str] = None,
    document_type: Optional[str] = None,
    checkpoint_location: Optional[str] = None,
    officer_email: Optional[str] = None,
    search_query: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> Tuple[List[Verification], int]:
    from sqlalchemy import or_

    query = select(Verification).order_by(Verification.timestamp.desc())

    if verdict:
        query = query.where(Verification.verdict == verdict)
    if document_type:
        query = query.where(Verification.document_type == document_type)
    if checkpoint_location:
        query = query.where(Verification.checkpoint_location == checkpoint_location)
    if officer_email:
        query = query.where(Verification.officer_email == officer_email)

    if search_query:
        sq = f"%{search_query.strip()}%"
        # Check if searching for numeric ID or case number
        id_match = None
        cleaned_sq = search_query.strip().upper().replace("CASE-26188-", "").replace("CASE-", "")
        if cleaned_sq.isdigit():
            id_match = int(cleaned_sq)

        conditions = [
            Verification.extracted_name.ilike(sq),
            Verification.extracted_id_number.ilike(sq),
            Verification.filename.ilike(sq),
            Verification.officer_email.ilike(sq),
            Verification.checkpoint_location.ilike(sq),
        ]
        if id_match is not None:
            conditions.append(Verification.id == id_match)

        query = query.where(or_(*conditions))

    if date_from:
        try:
            from datetime import datetime
            dt_from = datetime.fromisoformat(date_from)
            query = query.where(Verification.timestamp >= dt_from)
        except ValueError:
            pass

    if date_to:
        try:
            from datetime import datetime, timedelta
            dt_to = datetime.fromisoformat(date_to) + timedelta(days=1)
            query = query.where(Verification.timestamp < dt_to)
        except ValueError:
            pass

    # Count total
    count_query = select(Verification.id)
    if verdict:
        count_query = count_query.where(Verification.verdict == verdict)
    if document_type:
        count_query = count_query.where(Verification.document_type == document_type)
    if checkpoint_location:
        count_query = count_query.where(Verification.checkpoint_location == checkpoint_location)
    if officer_email:
        count_query = count_query.where(Verification.officer_email == officer_email)
    if search_query:
        count_query = count_query.where(or_(*conditions))
    if date_from:
        try:
            from datetime import datetime
            dt_from = datetime.fromisoformat(date_from)
            count_query = count_query.where(Verification.timestamp >= dt_from)
        except ValueError:
            pass
    if date_to:
        try:
            from datetime import datetime, timedelta
            dt_to = datetime.fromisoformat(date_to) + timedelta(days=1)
            count_query = count_query.where(Verification.timestamp < dt_to)
        except ValueError:
            pass

    from sqlalchemy import func
    count_query = select(func.count()).select_from(count_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()

    return list(items), total


async def get_verification_stats(
    db: AsyncSession,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> dict:
    from sqlalchemy import func, case
    from datetime import datetime, timedelta
    from app.models import Alert

    # Verdict stats
    query_verdict = select(Verification.verdict, func.count(Verification.id)).group_by(Verification.verdict)
    # Document type stats
    query_doctype = select(Verification.document_type, func.count(Verification.id)).group_by(Verification.document_type)
    # Checkpoint stats
    query_checkpoint = select(Verification.checkpoint_location, func.count(Verification.id)).group_by(Verification.checkpoint_location)
    # Aggregates
    query_agg = select(
        func.count(Verification.id),
        func.avg(Verification.processing_time_ms),
        func.sum(case((Verification.risk_score >= 80, 1), else_=0)),
    )

    if date_from:
        try:
            dt_from = datetime.fromisoformat(date_from)
            query_verdict = query_verdict.where(Verification.timestamp >= dt_from)
            query_doctype = query_doctype.where(Verification.timestamp >= dt_from)
            query_checkpoint = query_checkpoint.where(Verification.timestamp >= dt_from)
            query_agg = query_agg.where(Verification.timestamp >= dt_from)
        except ValueError:
            pass

    if date_to:
        try:
            dt_to = datetime.fromisoformat(date_to) + timedelta(days=1)
            query_verdict = query_verdict.where(Verification.timestamp < dt_to)
            query_doctype = query_doctype.where(Verification.timestamp < dt_to)
            query_checkpoint = query_checkpoint.where(Verification.timestamp < dt_to)
            query_agg = query_agg.where(Verification.timestamp < dt_to)
        except ValueError:
            pass

    res_v = await db.execute(query_verdict)
    counts_v = {row[0]: row[1] for row in res_v.all()}

    res_d = await db.execute(query_doctype)
    counts_d = {row[0] or "UNKNOWN": row[1] for row in res_d.all()}

    res_cp = await db.execute(query_checkpoint)
    counts_cp = {row[0] or "Central HQ": row[1] for row in res_cp.all()}

    res_agg = await db.execute(query_agg)
    agg_row = res_agg.one_or_none()
    total_recs = agg_row[0] if agg_row else 0
    avg_proc_time = int(agg_row[1] or 0) if agg_row else 0
    high_risk_recs = int(agg_row[2] or 0) if agg_row else 0

    # Daily volume calculation for past 7 days
    now = datetime.utcnow()
    daily_volume = []
    days_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for i in range(6, -1, -1):
        day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        day_q = select(func.count(Verification.id)).where(
            Verification.timestamp >= day_start,
            Verification.timestamp < day_end,
        )
        day_cnt_res = await db.execute(day_q)
        day_cnt = day_cnt_res.scalar() or 0
        day_name = days_labels[day_start.weekday()]
        daily_volume.append({
            "day": day_name,
            "count": day_cnt,
            "date": day_start.strftime("%Y-%m-%d"),
        })

    # Alert stats
    alerts_total = 0
    alerts_resolved = 0
    try:
        q_al_tot = select(func.count(Alert.id))
        q_al_res = select(func.count(Alert.id)).where(Alert.status.in_(["RESOLVED", "DISMISSED"]))
        al_tot_res = await db.execute(q_al_tot)
        al_res_res = await db.execute(q_al_res)
        alerts_total = al_tot_res.scalar() or 0
        alerts_resolved = al_res_res.scalar() or 0
    except Exception:
        pass

    return {
        "genuine": counts_v.get("GENUINE", 0),
        "suspicious": counts_v.get("SUSPICIOUS", 0),
        "fake": counts_v.get("FAKE", 0),
        "rejected": counts_v.get("REJECTED", 0),
        "total": sum(counts_v.values()) or total_recs,
        "high_risk": high_risk_recs,
        "avg_processing_time_ms": avg_proc_time,
        "by_document_type": counts_d,
        "by_checkpoint": counts_cp,
        "daily_volume": daily_volume,
        "alerts_total": alerts_total,
        "alerts_resolved": alerts_resolved,
    }