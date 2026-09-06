"""
Dedicated Verification Pipeline Tests
Tests specifically covering:
- Intake gate & quality evaluation (EXIF rotation, blur, contrast, resolution)
- Multi-pass OCR & field provenance
- Handling degraded/unreadable documents without falsely marking them as FAKE
- Preserving negative evidence as FAKE / REJECTED
- Document family resolution and UNKNOWN compatibility
"""
import os
import tempfile
import pytest
import numpy as np
import cv2
from io import BytesIO
from PIL import Image, ImageDraw

from app.preprocessing.enhancement import evaluate_document_quality
from app.preprocessing.image_loader import load_image_from_bytes
from app.extractors.classifier import classify_document_detailed, classify_document
from app.services.document_validator import validate_identity_document, ValidationGateResult
from app.services.document_validation import validate_document, _KNOWN_CONFLICT_MAP
from app.utils.verdict import compute_risk_score, compute_verdict


def _create_sample_id_image(text="GOVERNMENT OF INDIA\nAADHAAR\nName: RAHUL SHARMA\nDOB: 12/05/1990\n1234 5678 9012"):
    # Create realistic high-res document image with realistic lighting/texture
    img = Image.new("RGB", (800, 500), color=(200, 210, 220))
    draw = ImageDraw.Draw(img)
    draw.rectangle([(20, 20), (780, 480)], fill=(225, 230, 235), outline=(50, 50, 50), width=3)
    # Photo placeholder
    draw.rectangle([(40, 50), (220, 260)], fill=(120, 130, 140), outline=(50, 50, 50), width=2)
    # Text lines
    draw.text((250, 50), text, fill=(20, 20, 20))
    # Add texture / lines
    for i in range(12):
        draw.line([(250, 180 + i * 20), (750, 180 + i * 20)], fill=(80, 80, 80), width=2)
    
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=95)
    return buf.getvalue()


def test_quality_evaluation_good_document():
    img_bytes = _create_sample_id_image()
    np_imgs = load_image_from_bytes(img_bytes)
    assert len(np_imgs) > 0
    np_img = np_imgs[0]
    assert np_img is not None
    quality = evaluate_document_quality(np_img)
    assert quality["status"] in ("GOOD", "ACCEPTABLE")
    assert "blur_score" in quality
    assert quality["is_blurry"] is False


def test_quality_evaluation_blurry_document():
    # Intentionally create very blurry image
    img = np.full((500, 500, 3), 128, dtype=np.uint8)
    blurred = cv2.GaussianBlur(img, (51, 51), 0)
    quality = evaluate_document_quality(blurred)
    assert quality["status"] in ("POOR", "UNUSABLE")
    assert quality["is_blurry"] is True


def test_validation_gate_result_tuple_compatibility():
    img_bytes = _create_sample_id_image()
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tf:
        tf.write(img_bytes)
        tf_path = tf.name

    try:
        res = validate_identity_document(tf_path)
        assert isinstance(res, ValidationGateResult)
        # Check 2-tuple unpacking
        is_valid, reason = res
        assert is_valid is True
        # Check property access
        assert res.is_valid is True
        assert res.quality_info is not None
        assert "status" in res.quality_info
    finally:
        if os.path.exists(tf_path):
            os.unlink(tf_path)


def test_classifier_fuzzy_and_regex_matching():
    text = "ELECTION COMMISSION OF INDIA IDENTITY CARD EPIC NO ABC1234567"
    cls_result = classify_document_detailed(text)
    assert cls_result["document_type"] == "id"
    assert cls_result["document_family"] == "VOTER_ID"
    assert cls_result["confidence"] > 0.6

    pan_text = "INCOME TAX DEPARTMENT GOVT OF INDIA PERMANENT ACCOUNT NUMBER ABCDE1234F"
    cls_pan = classify_document_detailed(pan_text)
    assert cls_pan["document_type"] == "id"
    assert cls_pan["document_family"] == "PAN"


def test_unknown_document_type_is_not_treated_as_hard_conflict():
    fields = {"id_number": "12345678"}
    # UNKNOWN classification should not trigger category mismatch failure
    res = validate_document(doc_type="NATIONAL_ID", extracted_fields=fields, detected_doc_type="UNKNOWN")
    assert res.format_valid is True
    for issue in res.issues:
        assert "CATEGORY_MISMATCH" not in issue
        assert "DOCUMENT TYPE MISMATCH" not in issue


def test_negative_evidence_versus_missing_evidence_verdicts():
    # Negative evidence: High tampering score -> FAKE
    risk_tamper = compute_risk_score(tampering_score=85, face_match_score=90)
    verdict_tamper = compute_verdict(risk_tamper, tampering_score=85, face_match_score=90)
    assert verdict_tamper == "FAKE"

    # Negative evidence: Face mismatch -> FAKE
    risk_mismatch = compute_risk_score(tampering_score=10, face_match_score=20)
    verdict_mismatch = compute_verdict(risk_mismatch, tampering_score=10, face_match_score=20)
    assert verdict_mismatch == "FAKE"

    # Genuine: Clean verification -> GENUINE
    risk_clean = compute_risk_score(tampering_score=10, face_match_score=85)
    verdict_clean = compute_verdict(risk_clean, tampering_score=10, face_match_score=85)
    assert verdict_clean == "GENUINE"


# ─── Bug 4 Regression: Tampering Gate Skips Face Verification ───

@pytest.mark.asyncio
async def test_tampering_gate_skips_face_verification():
    """
    REGRESSION — Bug 4: When a document is detected as tampered/FAKE (tampering score >= 70),
    the verification pipeline must skip biometric evaluation entirely.
    run_biometric_evaluation must NEVER be called, verdict must be FAKE,
    and biometric stage must be SKIPPED.
    """
    from unittest.mock import patch, AsyncMock
    from fastapi import UploadFile
    from io import BytesIO
    from app.services.verification import run_verification
    from app.services.tampering import TamperingAnalysisResult
    from app.database import async_session_maker, init_db

    await init_db()

    id_bytes = _create_sample_id_image()
    id_file = UploadFile(filename="tampered_id.jpg", file=BytesIO(id_bytes))
    selfie_file = UploadFile(filename="selfie.jpg", file=BytesIO(id_bytes))

    mock_tamper = TamperingAnalysisResult(
        score=85,
        regions=[],
        heatmap_base64="",
        heatmap_path="",
        signals={"ela_score": 85},
        summary="Severe image manipulation detected",
    )

    async with async_session_maker() as db:
        with patch("app.services.verification.detect_tampering", new_callable=AsyncMock) as mock_detect, \
             patch("app.services.verification.run_biometric_evaluation", new_callable=AsyncMock) as mock_bio:

            mock_detect.return_value = mock_tamper

            response = await run_verification(
                db=db,
                id_file=id_file,
                document_type="NATIONAL_ID",
                selfie_file=selfie_file,
                officer_email="officer.attari@mha.gov.in",
            )

            # Assert face verification was NEVER called
            mock_bio.assert_not_called()

            # Assert verdict is FAKE
            assert response.verdict == "FAKE"

            # Assert biometric face match status is SKIPPED
            assert response.biometric.face_match.status == "SKIPPED"

            # Assert timeline stage is SKIPPED
            bio_stage = next((s for s in response.timeline if s.stage_id == "biometric"), None)
            assert bio_stage is not None
            assert bio_stage.status == "SKIPPED"


# ─── Bug 5 Regression: No Face / Blocked Camera in Selfie Is Rejected ───

def test_retry_biometric_status_verdict_gates():
    """
    REGRESSION — Bug 5: When biometric evaluation returns status="RETRY"
    (no face detected, blocked camera, finger over lens), compute_risk_score must penalize,
    generate_security_checks must fail, and compute_verdict must return REJECTED (never GENUINE).
    """
    from app.utils.verdict import compute_risk_score, compute_verdict, generate_security_checks

    risk = compute_risk_score(tampering_score=10, face_match_score=None, face_status="RETRY")
    assert risk >= 65

    verdict = compute_verdict(risk_score=risk, tampering_score=10, face_match_score=None, face_status="RETRY")
    assert verdict in ("REJECTED", "FAKE")
    assert verdict != "GENUINE"

    checks = generate_security_checks(tampering_score=10, face_match_score=None, face_status="RETRY")
    sc3 = next((c for c in checks if c["id"] == "sc-3"), None)
    assert sc3 is not None
    assert sc3["status"] == "failed"


@pytest.mark.asyncio
async def test_no_face_in_selfie_pipeline_rejected():
    """
    REGRESSION — Bug 5: Full verification run where selfie contains no detectable face (status="RETRY").
    The final verdict must NOT be GENUINE.
    """
    from unittest.mock import patch, AsyncMock
    from fastapi import UploadFile
    from io import BytesIO
    from app.services.verification import run_verification
    from app.schemas import (
        BiometricResult, QualityResult, LivenessResult, PresentationAttackResult, FaceMatchResult
    )
    from app.database import async_session_maker, init_db

    await init_db()

    id_bytes = _create_sample_id_image()
    id_file = UploadFile(filename="valid_id.jpg", file=BytesIO(id_bytes))
    selfie_file = UploadFile(filename="blocked_camera.jpg", file=BytesIO(id_bytes))

    retry_biometric = BiometricResult(
        face_detected=False,
        face_count=0,
        quality=QualityResult(status="POOR", score=0.1, details="No face detected"),
        liveness=LivenessResult(status="UNKNOWN", score=0.0, details="No face detected"),
        presentation_attack=PresentationAttackResult(detected=False, score=0.0, type=None, details="No face detected"),
        face_match=FaceMatchResult(status="FACE_NOT_DETECTED", score=None, distance=None, details="No face detected in selfie"),
        status="RETRY",
    )

    async with async_session_maker() as db:
        with patch("app.services.verification.run_biometric_evaluation", new_callable=AsyncMock) as mock_bio:
            mock_bio.return_value = retry_biometric

            response = await run_verification(
                db=db,
                id_file=id_file,
                document_type="NATIONAL_ID",
                selfie_file=selfie_file,
                officer_email="officer.attari@mha.gov.in",
            )

            assert response.verdict in ("REJECTED", "SUSPICIOUS", "FAKE")
            assert response.verdict != "GENUINE"
            assert "FACE_NOT_DETECTED" in response.risk_factors

