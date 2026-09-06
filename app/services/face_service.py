"""
Face Verification Service Adapter
Wraps teammate's DeepFace / ArcFace implementation into the standard 3-tuple contract:
    match_faces(id_photo_path, selfie_path) -> (distance, is_match, liveness_score)
"""

import logging
from typing import Optional, Tuple, Dict, Any
from ._face_match_impl import (
    _calculate_match_sync,
    match_faces_detailed,
    warm_up_face_model,
)

logger = logging.getLogger(__name__)


def _map_detailed_result(result: Dict[str, Any], liveness_score: float = 0.0) -> Tuple[Optional[float], Optional[bool], Optional[float]]:
    """
    Maps detailed DeepFace response dictionary to standard (distance, is_match, liveness_score) tuple.
    """
    status = result.get("status")
    matched = result.get("matched", False)

    # If face detection fails or an error occurs, distance is None and is_match is False
    if status in ("no_face_detected", "multiple_faces_detected", "error"):
        distance = None
        is_match = False
    else:
        distance = result.get("distance")
        is_match = bool(matched)

    return distance, is_match, liveness_score


def calculate_liveness_score(image_path: str) -> float:
    """
    Analyzes anti-spoofing and liveness heuristics on input face image:
    Evaluates frequency spectrum for moire patterns (screen replay) and
    chrominance gamut variance (print attack).
    """
    try:
        from .face_match import analyze_liveness_and_presentation_attack
        from ._face_match_impl import _secure_load_and_normalize
        bgr, err = _secure_load_and_normalize(image_path)
        if err or bgr is None:
            return 0.0
        liveness_res, _ = analyze_liveness_and_presentation_attack(bgr)
        return float(liveness_res.score)
    except Exception as exc:
        logger.warning(f"Liveness score computation fallback: {exc}")
        return 0.0


def match_faces(
    id_photo_path: str,
    selfie_path: str,
    check_liveness: bool = False,
) -> Tuple[Optional[float], Optional[bool], Optional[float]]:
    """
    Synchronous entrypoint called by the verification pipeline.
    Invokes the synchronous model calculation directly to avoid event-loop blocking or nesting errors.

    Returns:
        (distance, is_match, liveness_score)
        - distance: float (cosine distance) or None if detection fails
        - is_match: bool indicating whether distance <= threshold
        - liveness_score: float (0.05-1.0 if check_liveness=True, else 0.0)
    """
    result = _calculate_match_sync(id_photo_path, selfie_path)
    liveness_score = calculate_liveness_score(selfie_path) if check_liveness else 0.0
    return _map_detailed_result(result, liveness_score=liveness_score)


async def match_faces_async(
    id_photo_path: str,
    selfie_path: str,
    check_liveness: bool = False,
) -> Tuple[Optional[float], Optional[bool], Optional[float]]:
    """
    Asynchronous alternative entrypoint for async workflows.
    """
    result = await match_faces_detailed(id_photo_path, selfie_path)
    liveness_score = calculate_liveness_score(selfie_path) if check_liveness else 0.0
    return _map_detailed_result(result, liveness_score=liveness_score)


__all__ = ["match_faces", "match_faces_async", "calculate_liveness_score", "warm_up_face_model"]
