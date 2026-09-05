"""
Unit & Integration Tests for Phase 1 Objectives:
1. Fix Face Mismatch Risk Scoring (Score below 50% must yield HIGH/CRITICAL risk and FAKE/REJECTED).
2. Enforce Selected Document Type (Mismatch between selected and detected types must be a hard failure).
3. Removal of Filename-based Mock/Demo Detection.
4. Data Contract Integrity.
"""

import os
import io
import tempfile
import asyncio
import pytest
from PIL import Image, ImageDraw

from app.config import get_settings
from app.utils.verdict import (
    compute_risk_score,
    get_risk_level,
    compute_verdict,
    get_verdict_reason,
    compute_risk_factors,
)
from app.services.document_validation import validate_document
from app.services.document_validator import validate_identity_document, detect_face_presence
from app.services.tampering import detect_tampering, run_metadata_and_font_check


def test_case_1_selected_national_id_detected_national_id_face_match_no_tampering():
    """
    TEST 1:
    Selected National ID
    Detected National ID
    Face match (e.g., 92%)
    No tampering (0)
    → LOW risk (<=30) / GENUINE
    """
    doc_type = "NATIONAL_ID"
    detected_doc_type = "id"  # Classifier output for National ID
    tampering_score = 0
    face_match_score = 92

    # Validation
    val = validate_document(
        doc_type=doc_type,
        extracted_fields={"id_number": "123456789012", "dob": "1995-05-20"},
        detected_doc_type=detected_doc_type,
    )
    assert val.format_valid is True
    assert not any("DOCUMENT TYPE MISMATCH" in i for i in val.issues)

    # Risk score calculation
    risk_score = compute_risk_score(
        tampering_score=tampering_score,
        face_match_score=face_match_score,
        validation_issues_count=len(val.issues),
        category_mismatch=False,
    )
    risk_level = get_risk_level(risk_score)
    verdict = compute_verdict(
        risk_score=risk_score,
        tampering_score=tampering_score,
        face_match_score=face_match_score,
        validation=val,
        category_mismatch=False,
    )

    assert risk_score <= 30, f"Expected risk_score <= 30, got {risk_score}"
    assert risk_level == "LOW RISK"
    assert verdict == "GENUINE"


def test_case_2_selected_national_id_detected_driving_license_hard_failure():
    """
    TEST 2:
    Selected National ID
    Detected Driving License
    → HARD FAILURE
    → NOT genuine
    → clear DOCUMENT TYPE MISMATCH reason
    → REJECTED verdict
    → HIGH/CRITICAL risk
    """
    doc_type = "NATIONAL_ID"
    detected_doc_type = "license"  # Classifier detected Driving License

    val = validate_document(
        doc_type=doc_type,
        extracted_fields={"id_number": "DL-1234567890"},
        detected_doc_type=detected_doc_type,
    )

    # 1. Marked as failed format validation
    assert val.format_valid is False
    # 2. Contains clear document type mismatch issue
    mismatch_issues = [i for i in val.issues if "DOCUMENT TYPE MISMATCH" in i]
    assert len(mismatch_issues) > 0
    assert "DOCUMENT TYPE MISMATCH: Selected NATIONAL_ID but detected DRIVING_LICENSE" in mismatch_issues[0]

    # 3. Risk calculation
    risk_score = compute_risk_score(
        tampering_score=0,
        face_match_score=95,
        validation_issues_count=len(val.issues),
        category_mismatch=True,
    )
    risk_level = get_risk_level(risk_score)
    assert risk_score >= 66, f"Expected risk_score >= 66, got {risk_score}"
    assert risk_level == "HIGH RISK"

    # 4. Hard failure verdict
    verdict = compute_verdict(
        risk_score=risk_score,
        tampering_score=0,
        face_match_score=95,
        validation=val,
        category_mismatch=True,
    )
    assert verdict == "REJECTED"

    # 5. Verdict reason contains the mismatch explanation
    reason = get_verdict_reason(
        verdict=verdict,
        risk_score=risk_score,
        tampering_score=0,
        face_match_score=95,
        validation=val,
        category_mismatch=True,
        selected_doc_type=doc_type,
        detected_doc_type="DRIVING_LICENSE",
    )
    assert "DOCUMENT TYPE MISMATCH" in reason
    assert "Selected NATIONAL_ID but detected DRIVING_LICENSE" in reason


def test_case_3_valid_document_face_mismatch_below_threshold():
    """
    TEST 3:
    Valid document
    Face match score below rejection threshold (e.g., 20% or 0%)
    No tampering
    → HIGH or CRITICAL risk (>65)
    → FAKE/REJECTED
    → risk score must NOT be LOW
    """
    val = validate_document(
        doc_type="NATIONAL_ID",
        extracted_fields={"id_number": "123456789012", "dob": "1992-04-10"},
        detected_doc_type="id",
    )

    for face_score in [0, 15, 30, 49]:
        risk_score = compute_risk_score(
            tampering_score=0,
            face_match_score=face_score,
            validation_issues_count=len(val.issues),
            category_mismatch=False,
        )
        risk_level = get_risk_level(risk_score)
        verdict = compute_verdict(
            risk_score=risk_score,
            tampering_score=0,
            face_match_score=face_score,
            validation=val,
            category_mismatch=False,
        )

        assert risk_score > 65, f"Face score {face_score} produced risk_score {risk_score}, expected > 65"
        assert risk_level == "HIGH RISK", f"Face score {face_score} produced risk_level {risk_level}, expected HIGH RISK"
        assert verdict == "FAKE", f"Face score {face_score} produced verdict {verdict}, expected FAKE"


def test_case_4_valid_document_strong_face_match_no_tampering():
    """
    TEST 4:
    Valid document
    Strong face match (e.g. 95%)
    No tampering
    → Low risk (<=30)
    → GENUINE
    """
    val = validate_document(
        doc_type="PASSPORT",
        extracted_fields={"passport_number": "Z9876543", "dob": "1988-11-23", "date_of_expiry": "2030-01-01"},
        detected_doc_type="passport",
    )

    risk_score = compute_risk_score(
        tampering_score=0,
        face_match_score=95,
        validation_issues_count=0,
        category_mismatch=False,
    )
    risk_level = get_risk_level(risk_score)
    verdict = compute_verdict(
        risk_score=risk_score,
        tampering_score=0,
        face_match_score=95,
        validation=val,
        category_mismatch=False,
    )

    assert risk_score <= 30
    assert risk_level == "LOW RISK"
    assert verdict == "GENUINE"


def test_case_5_tampered_document_face_mismatch():
    """
    TEST 5:
    Tampered document (tampering=85)
    Face mismatch (face_match_score=10)
    → HIGH/CRITICAL risk (>=90-100)
    → FAKE/REJECTED
    """
    risk_score = compute_risk_score(
        tampering_score=85,
        face_match_score=10,
        validation_issues_count=1,
        category_mismatch=False,
    )
    risk_level = get_risk_level(risk_score)
    verdict = compute_verdict(
        risk_score=risk_score,
        tampering_score=85,
        face_match_score=10,
    )

    assert risk_score >= 90
    assert risk_score <= 100
    assert risk_level == "HIGH RISK"
    assert verdict == "FAKE"


def test_case_6_filename_does_not_determine_tampering_or_validation():
    """
    TEST 6:
    Filename contains 'fake', 'reed', 'vance', or 'jenkins', but the actual document
    image itself does not contain alterations.
    → filename alone must NOT determine the result.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create a clean, uniform image with various filenames
        test_names = [
            "fake_document.jpg",
            "reed_passport.jpg",
            "vance_id.jpg",
            "jenkins_license.jpg",
        ]

        for fname in test_names:
            fpath = os.path.join(tmp_dir, fname)
            img = Image.new("RGB", (600, 400), color=(240, 240, 240))
            img.save(fpath)

            # 1. Metadata and font check should not blindly add 65 or 35 points just for filename
            score, traces = run_metadata_and_font_check(fpath, img)
            assert score < 30, f"Filename {fname} improperly influenced metadata check: score={score}"
            assert not any("Photo splice boundary detected" in t for t in traces)
            assert not any("Glyph baseline stroke thickness mismatch" in t for t in traces)

            # 2. Tampering detection should calculate score based on real image analysis, not hardcoded 89/52/4
            result = asyncio.run(detect_tampering(fpath))
            assert result.score != 89 or fname != "fake_document.jpg"
            assert result.score != 52 or fname != "vance_id.jpg"
            # Specifically, clean blank image will have low ELA and zero clone pairs
            assert result.score < 30, f"Clean image with filename {fname} received tampering score {result.score}"
