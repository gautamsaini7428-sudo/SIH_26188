from app.services.ocr import extract_fields
from app.services.tampering import (
    detect_tampering,
    TamperingAnalysisResult,
    run_ela_analysis,
    run_copy_move_detection,
    generate_thematic_heatmap,
)
from app.services.face_match import (
    match_faces,
    match_faces_detailed,
    warm_up_face_model,
)
from app.services.audit_log import (
    log_verification,
    get_all_records,
    verify_audit_chain,
)
from app.services.document_validator import (
    validate_identity_document,
    detect_face_presence,
)

__all__ = [
    "extract_fields",
    "detect_tampering",
    "TamperingAnalysisResult",
    "run_ela_analysis",
    "run_copy_move_detection",
    "generate_thematic_heatmap",
    "match_faces",
    "match_faces_detailed",
    "warm_up_face_model",
    "log_verification",
    "get_all_records",
    "verify_audit_chain",
    "validate_identity_document",
    "detect_face_presence",
]