"""
Canonical Face Verification Interface Adapter.
Consolidates all face matching operations into app.services.face_match as the single source of truth.
"""

from app.services.face_match import (
    MODEL_NAME,
    DETECTOR_BACKEND,
    DISTANCE_METRIC,
    ARCFACE_COSINE_THRESHOLD,
    MAX_IMAGE_FILE_BYTES,
    MAX_IMAGE_DIMENSION,
    MIN_FACE_DIMENSION,
    warm_up_face_model,
    _secure_load_and_normalize,
    _calculate_calibrated_score,
    _compute_cosine_distance,
    _calculate_match_sync,
    match_faces,
    match_faces_detailed,
    run_face_verification,
    evaluate_biometrics_sync,
    analyze_image_quality,
    analyze_liveness_and_presentation_attack,
)

__all__ = [
    "MODEL_NAME",
    "DETECTOR_BACKEND",
    "DISTANCE_METRIC",
    "ARCFACE_COSINE_THRESHOLD",
    "MAX_IMAGE_FILE_BYTES",
    "MAX_IMAGE_DIMENSION",
    "MIN_FACE_DIMENSION",
    "warm_up_face_model",
    "_secure_load_and_normalize",
    "_calculate_calibrated_score",
    "_compute_cosine_distance",
    "_calculate_match_sync",
    "match_faces",
    "match_faces_detailed",
    "run_face_verification",
    "evaluate_biometrics_sync",
    "analyze_image_quality",
    "analyze_liveness_and_presentation_attack",
]
