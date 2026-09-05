import os
import sys
from unittest.mock import MagicMock, patch
import numpy as np
import pytest
import cv2

if "deepface" not in sys.modules:
    mock_deepface_mod = MagicMock()
    mock_deepface_mod.DeepFace = MagicMock()
    sys.modules["deepface"] = mock_deepface_mod

from app.services._face_match_impl import (
    match_faces as impl_match_faces,
    match_faces_detailed,
    _calculate_calibrated_score,
    _compute_cosine_distance,
    _secure_load_and_normalize,
    ARCFACE_COSINE_THRESHOLD,
    warm_up_face_model,
)
from app.services.face_service import (
    match_faces,
    match_faces_async,
)


@pytest.fixture
def test_images(tmp_path):
    valid_id = str(tmp_path / "valid_id.png")
    valid_selfie = str(tmp_path / "valid_selfie.png")
    img = np.full((150, 150, 3), 128, dtype=np.uint8)
    cv2.imwrite(valid_id, img)
    cv2.imwrite(valid_selfie, img)
    return valid_id, valid_selfie


def test_score_calibration_curve():
    assert _calculate_calibrated_score(0.0) == 100
    assert _calculate_calibrated_score(ARCFACE_COSINE_THRESHOLD) == 70
    assert _calculate_calibrated_score(1.2) == 0


def test_cosine_distance_computation():
    vec1 = [1.0, 0.0, 0.0]
    vec2 = [1.0, 0.0, 0.0]
    vec3 = [0.0, 1.0, 0.0]
    assert _compute_cosine_distance(vec1, vec2) == pytest.approx(0.0, abs=1e-5)
    assert _compute_cosine_distance(vec1, vec3) == pytest.approx(1.0, abs=1e-5)


def test_nonexistent_files():
    data, err = _secure_load_and_normalize("/invalid/path/does_not_exist.jpg")
    assert data is None
    assert "not found" in err.lower()


def test_corrupt_files(tmp_path):
    corrupt = str(tmp_path / "corrupt.jpg")
    with open(corrupt, "wb") as f:
        f.write(b"NOT_JPEG_BINARY")
    data, err = _secure_load_and_normalize(corrupt)
    assert data is None
    assert "malformed" in err.lower()


def test_warm_up_face_model_safe():
    # Should run without crashing even if deepface mock is in place or real model is invoked
    with patch("deepface.DeepFace.represent", return_value=[{"embedding": [0.1] * 512}]):
        warm_up_face_model()


@pytest.mark.asyncio
async def test_no_face_detected_impl(test_images):
    id_path, selfie_path = test_images
    with patch("deepface.DeepFace.represent", return_value=[]):
        res = await match_faces_detailed(id_path, selfie_path)
        assert res["status"] == "no_face_detected"
        assert res["matched"] is False
        assert res["score"] == 0


@pytest.mark.asyncio
async def test_multiple_faces_detected_impl(test_images):
    id_path, selfie_path = test_images
    mock_faces = [
        {"facial_area": {"w": 50, "h": 50}, "face_confidence": 0.95, "embedding": [0.1] * 512},
        {"facial_area": {"w": 60, "h": 60}, "face_confidence": 0.98, "embedding": [0.2] * 512},
    ]
    with patch("deepface.DeepFace.represent", return_value=mock_faces):
        res = await match_faces_detailed(id_path, selfie_path)
        assert res["status"] == "multiple_faces_detected"
        assert res["score"] == 0


@pytest.mark.asyncio
async def test_matched_verification_impl(test_images):
    id_path, selfie_path = test_images
    unit_vec = [1.0] + [0.0] * 511
    mock_rep = [{"facial_area": {"w": 50, "h": 50}, "face_confidence": 0.99, "embedding": unit_vec}]
    with patch("deepface.DeepFace.represent", return_value=mock_rep):
        score = await impl_match_faces(id_path, selfie_path)
        assert score == 100
        detailed = await match_faces_detailed(id_path, selfie_path)
        assert detailed["status"] == "matched"
        assert detailed["matched"] is True


def test_face_service_adapter_matched(test_images):
    """Test standard 3-tuple return contract (distance, is_match, liveness_score) on match."""
    id_path, selfie_path = test_images
    unit_vec = [1.0] + [0.0] * 511
    mock_rep = [{"facial_area": {"w": 50, "h": 50}, "face_confidence": 0.99, "embedding": unit_vec}]
    with patch("deepface.DeepFace.represent", return_value=mock_rep):
        distance, is_match, liveness = match_faces(id_path, selfie_path)
        assert distance is not None
        assert distance == pytest.approx(0.0, abs=1e-4)
        assert is_match is True
        assert liveness == 0.0


def test_face_service_adapter_mismatch(test_images):
    """Test standard 3-tuple return contract on facial mismatch."""
    id_path, selfie_path = test_images
    vec_id = [1.0] + [0.0] * 511
    vec_selfie = [0.0, 1.0] + [0.0] * 510

    def mock_rep_side_effect(img_path, **kwargs):
        # Return different embeddings depending on role or call sequence
        if not hasattr(mock_rep_side_effect, "called_once"):
            mock_rep_side_effect.called_once = True
            return [{"facial_area": {"w": 50, "h": 50}, "face_confidence": 0.99, "embedding": vec_id}]
        return [{"facial_area": {"w": 50, "h": 50}, "face_confidence": 0.99, "embedding": vec_selfie}]

    with patch("deepface.DeepFace.represent", side_effect=mock_rep_side_effect):
        distance, is_match, liveness = match_faces(id_path, selfie_path)
        assert distance is not None
        assert distance > ARCFACE_COSINE_THRESHOLD
        assert is_match is False
        assert liveness == 0.0


def test_face_service_adapter_no_face(test_images):
    """Test standard 3-tuple return contract when no face is detected: distance is None, is_match is False."""
    id_path, selfie_path = test_images
    with patch("deepface.DeepFace.represent", return_value=[]):
        distance, is_match, liveness = match_faces(id_path, selfie_path)
        assert distance is None
        assert is_match is False
        assert liveness == 0.0


def test_face_service_adapter_multiple_faces(test_images):
    """Test standard 3-tuple return contract when multiple faces are detected: distance is None, is_match is False."""
    id_path, selfie_path = test_images
    mock_faces = [
        {"facial_area": {"w": 50, "h": 50}, "face_confidence": 0.95, "embedding": [0.1] * 512},
        {"facial_area": {"w": 60, "h": 60}, "face_confidence": 0.98, "embedding": [0.2] * 512},
    ]
    with patch("deepface.DeepFace.represent", return_value=mock_faces):
        distance, is_match, liveness = match_faces(id_path, selfie_path)
        assert distance is None
        assert is_match is False
        assert liveness == 0.0


@pytest.mark.asyncio
async def test_face_service_async_adapter(test_images):
    """Test async adapter endpoint returns identical 3-tuple contract."""
    id_path, selfie_path = test_images
    unit_vec = [1.0] + [0.0] * 511
    mock_rep = [{"facial_area": {"w": 50, "h": 50}, "face_confidence": 0.99, "embedding": unit_vec}]
    with patch("deepface.DeepFace.represent", return_value=mock_rep):
        distance, is_match, liveness = await match_faces_async(id_path, selfie_path)
        assert distance is not None
        assert is_match is True
        assert liveness == 0.0
