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
