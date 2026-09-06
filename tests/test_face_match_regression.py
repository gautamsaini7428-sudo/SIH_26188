import os
import sys
from unittest.mock import patch, MagicMock
import pytest
import numpy as np
import cv2

if "deepface" not in sys.modules:
    mock_deepface_mod = MagicMock()
    mock_deepface_mod.DeepFace = MagicMock()
    sys.modules["deepface"] = mock_deepface_mod

from app.services.face_match import (
    _calculate_calibrated_score,
    analyze_image_quality,
    analyze_liveness_and_presentation_attack,
    evaluate_biometrics_sync,
    _compute_cosine_distance,
    ARCFACE_COSINE_THRESHOLD,
)


def _create_temp_image_file(tmp_path, filename="test_face.jpg", color=(180, 150, 130)):
    """Generate a clean synthetic face-like image and save to disk."""
    width, height = 300, 300
    img = np.zeros((height, width, 3), dtype=np.uint8)
    img[:] = (240, 240, 240)
    # Head oval
    cv2.ellipse(img, (width // 2, height // 2), (width // 3, height // 2 - 20), 0, 0, 360, color, -1)
    # Eyes
    cv2.circle(img, (width // 2 - 40, height // 2 - 30), 10, (50, 50, 50), -1)
    cv2.circle(img, (width // 2 + 40, height // 2 - 30), 10, (50, 50, 50), -1)
    # Mouth
    cv2.ellipse(img, (width // 2, height // 2 + 50), (30, 10), 0, 0, 180, (50, 50, 50), 2)

    file_path = str(tmp_path / filename)
    cv2.imwrite(file_path, img)
    return file_path


def test_calibrated_score_same_person_recent():
    """Distance 0.20 (identical/recent) should produce a high match score >= 90."""
    score = _calculate_calibrated_score(0.20, ARCFACE_COSINE_THRESHOLD)
    assert score >= 90, f"Expected score >= 90 for recent photo, got {score}"


def test_calibrated_score_same_person_aged_2_years():
    """
    REGRESSION TEST:
    A ~2-year-old aged photo typically has ArcFace cosine distance between 0.40 and 0.60.
    Under the calibrated curve (threshold 0.68), distance 0.50 must yield score >= 70 and match.
    """
    distance_aged = 0.50
    score = _calculate_calibrated_score(distance_aged, ARCFACE_COSINE_THRESHOLD)
    assert score >= 70, f"Expected calibrated score >= 70 for 2-year-old photo (distance {distance_aged}), got {score}"

    # Boundary near 0.60
    score_60 = _calculate_calibrated_score(0.60, ARCFACE_COSINE_THRESHOLD)
    assert score_60 >= 70, f"Expected calibrated score >= 70 for distance 0.60, got {score_60}"


def test_calibrated_score_different_person():
    """Distance 0.85 (different person) should yield score < 50."""
    score = _calculate_calibrated_score(0.85, ARCFACE_COSINE_THRESHOLD)
    assert score < 50, f"Expected score < 50 for different person, got {score}"


def test_evaluate_biometrics_same_person_aged_match(tmp_path):
    """
    Test that evaluate_biometrics_sync correctly assigns MATCH for an aged photo
    with distance 0.50 (within threshold 0.68) and clean quality.
    """
    doc_path = _create_temp_image_file(tmp_path, "doc.jpg")
    selfie_path = _create_temp_image_file(tmp_path, "selfie.jpg")

    mock_doc_rep = [0.1] * 128
    mock_selfie_rep = [0.1] * 128
    # Slight perturbation simulating aging
    mock_selfie_rep[0] = 0.5

    with patch("app.services.face_match._calculate_match_sync") as mock_match, \
         patch("deepface.DeepFace.represent") as mock_rep:

        mock_rep.return_value = [{
            "facial_area": {"x": 50, "y": 50, "w": 150, "h": 150},
            "face_confidence": 0.95,
            "embedding": mock_selfie_rep,
        }]

        mock_match.return_value = {
            "status": "matched",
            "score": 78,
            "matched": True,
            "distance": 0.50,
            "threshold": ARCFACE_COSINE_THRESHOLD,
            "detail": "Facial verification evaluated successfully.",
        }

        result = evaluate_biometrics_sync(doc_path, selfie_path)

        assert result.status == "VERIFIED"
        assert result.face_match.status == "MATCH", f"Expected MATCH for aged photo, got {result.face_match.status}"
        assert result.face_match.score == 78
        assert result.face_detected is True
        assert result.face_count == 1


def test_evaluate_biometrics_different_person_mismatch(tmp_path):
    """
    Test that evaluate_biometrics_sync assigns NO_MATCH / REJECTED when distance is high (e.g. 0.85).
    """
    doc_path = _create_temp_image_file(tmp_path, "doc_diff.jpg")
    selfie_path = _create_temp_image_file(tmp_path, "selfie_diff.jpg")

    with patch("app.services.face_match._calculate_match_sync") as mock_match, \
         patch("deepface.DeepFace.represent") as mock_rep:

        mock_rep.return_value = [{
            "facial_area": {"x": 50, "y": 50, "w": 150, "h": 150},
            "face_confidence": 0.95,
            "embedding": [0.2] * 128,
        }]

        mock_match.return_value = {
            "status": "not_matched",
            "score": 42,
            "matched": False,
            "distance": 0.85,
            "threshold": ARCFACE_COSINE_THRESHOLD,
            "detail": "Facial verification evaluated successfully.",
        }

        result = evaluate_biometrics_sync(doc_path, selfie_path)

        assert result.status == "REJECTED"
        assert result.face_match.status == "NO_MATCH"
        assert result.face_match.score == 42


def test_evaluate_biometrics_no_face_detected(tmp_path):
    """Test clear validation failure when no face is found in selfie image."""
    doc_path = _create_temp_image_file(tmp_path, "doc_noface.jpg")
    selfie_path = _create_temp_image_file(tmp_path, "selfie_noface.jpg")

    with patch("deepface.DeepFace.represent") as mock_rep:
        # No faces returned
        mock_rep.return_value = []

        result = evaluate_biometrics_sync(doc_path, selfie_path)

        assert result.status == "RETRY"
        assert result.face_detected is False
        assert result.face_count == 0
        assert result.face_match.status == "NO_MATCH"


def test_evaluate_biometrics_multiple_faces(tmp_path):
    """Test that multiple faces in a single frame trigger RETRY."""
    doc_path = _create_temp_image_file(tmp_path, "doc_multi.jpg")
    selfie_path = _create_temp_image_file(tmp_path, "selfie_multi.jpg")

    with patch("deepface.DeepFace.represent") as mock_rep:
        mock_rep.return_value = [
            {"facial_area": {"x": 50, "y": 50, "w": 80, "h": 80}, "face_confidence": 0.90},
            {"facial_area": {"x": 180, "y": 50, "w": 80, "h": 80}, "face_confidence": 0.92},
        ]

        result = evaluate_biometrics_sync(doc_path, selfie_path)

        assert result.status == "RETRY"
        assert result.face_detected is True
        assert result.face_count == 2
        assert "Multiple faces" in result.quality.details
        assert "Border screening requires exactly one subject" in result.face_match.details


def test_face_quality_assessment_low_contrast():
    """Test that extreme low contrast or severe blur is caught."""
    blank_gray = np.ones((200, 200, 3), dtype=np.uint8) * 128
    quality = analyze_image_quality(blank_gray)
    assert quality.status == "LOW_QUALITY"
    assert quality.score <= 0.4


def test_liveness_not_falsely_flagging_matte_photo():
    """Test that standard matte photo with normal color variation does not falsely trigger PRINT_ATTACK."""
    width, height = 300, 300
    img = np.zeros((height, width, 3), dtype=np.uint8)
    img[:] = (240, 240, 240)
    cv2.ellipse(img, (width // 2, height // 2), (width // 3, height // 2 - 20), 0, 0, 360, (180, 150, 130), -1)

    liveness_res, pres_res = analyze_liveness_and_presentation_attack(img)
    assert pres_res.type != "PRINT_ATTACK" or liveness_res.status == "PASS"
