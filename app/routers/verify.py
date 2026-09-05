from fastapi import APIRouter, UploadFile, File, Form, Depends, Request, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.database import get_db
from app.services.verification import run_verification
from app.schemas import VerifyResponse, ErrorResponse, FaceVerifyResponse
from app.config import get_settings
from app.auth import require_officer
from app.models import User

router = APIRouter(prefix="", tags=["verification"])
settings = get_settings()


@router.post(
    "/verify-document",
    response_model=VerifyResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Verification processing error"},
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {"model": ErrorResponse, "description": "Officer permission required"},
    },
)
async def verify_document(
    request: Request,
    file: UploadFile = File(..., description="ID document image or PDF"),
    document_type: str = Form("DRIVING_LICENSE", description="PASSPORT | VISA | NATIONAL_ID | DRIVING_LICENSE | PERMIT"),
    selfie: Optional[UploadFile] = File(None, description="Optional live selfie for face matching (skipped for VISA)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_officer),
) -> VerifyResponse:
    """
    Verify an identity document for border screening (SIH26188). Requires officer or supervisor authentication.

    Pipeline execution:
    1. FAST-FAIL INTAKE GATE: Validates image contains detectable text and (except for VISA) a face.
       If invalid (e.g. building sketch / non-document), returns immediately with verdict="REJECTED".
    2. OCR module: Type-aware field extraction based on document_type.
    3. Document Validation module: Format checks, expiry check, MRZ checksum (PASSPORT), and mock blacklist.
    4. Tampering Detection module: ELA, copy-move/splicing, font/metadata consistency, generating palette heatmap base64.
    5. Face Match module: 128-d ArcFace vector correlation (skipped for VISA).
    6. Primary output: Weighted risk_score (0-100).
    7. Verdict label: Derived from risk_score + hard gates.
    8. Records officer email (`current_user.email`) and officer's checkpoint location.
    """
    client_ip = request.client.host if request.client else None
    officer_email = current_user.email or current_user.username
    result = await run_verification(
        db=db,
        id_file=file,
        document_type=document_type,
        selfie_file=selfie,
        client_ip=client_ip,
        officer_email=officer_email,
        user_checkpoint_location=current_user.checkpoint_location,
    )
    return result


@router.post(
    "/verify/face",
    response_model=FaceVerifyResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Face verification error"},
        401: {"model": ErrorResponse, "description": "Authentication required"},
    },
)
@router.post(
    "/verify-face",
    response_model=FaceVerifyResponse,
    include_in_schema=False,
)
async def verify_face(
    id_file: UploadFile = File(..., description="ID document portrait photo"),
    selfie_file: UploadFile = File(..., description="Live captured selfie photo"),
    current_user: User = Depends(require_officer),
) -> FaceVerifyResponse:
    """
    Standalone Face Biometrics Verification endpoint.
    Compares facial landmarks between an ID portrait and a live selfie using ArcFace.
    Requires authenticated officer or supervisor.
    """
    import os
    import tempfile
    from app.services._face_match_impl import match_faces_detailed
    from app.utils.file_handler import IMAGE_EXTENSIONS, validate_file_content

    # Validate extensions
    id_ext = os.path.splitext(id_file.filename or "")[1].lower()
    selfie_ext = os.path.splitext(selfie_file.filename or "")[1].lower()

    if id_ext not in IMAGE_EXTENSIONS or selfie_ext not in IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format. Supported image types: {', '.join(sorted(IMAGE_EXTENSIONS))}",
        )

    # Read bytes and validate size
    id_bytes = await id_file.read()
    selfie_bytes = await selfie_file.read()

    if len(id_bytes) == 0 or len(selfie_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded image files cannot be empty.",
        )

    if len(id_bytes) > settings.max_file_size_bytes or len(selfie_bytes) > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum size of {settings.max_file_size_mb}MB.",
        )

    validate_file_content(id_bytes, id_file.filename or "")
    validate_file_content(selfie_bytes, selfie_file.filename or "")

    temp_id_path = None
    temp_selfie_path = None
    try:
        # Create secure temp files
        with tempfile.NamedTemporaryFile(suffix=id_ext, delete=False) as f_id:
            f_id.write(id_bytes)
            temp_id_path = f_id.name

        with tempfile.NamedTemporaryFile(suffix=selfie_ext, delete=False) as f_selfie:
            f_selfie.write(selfie_bytes)
            temp_selfie_path = f_selfie.name

        detailed = await match_faces_detailed(temp_id_path, temp_selfie_path)
        score_val = detailed.get("score")

        return FaceVerifyResponse(
            status=detailed.get("status", "error"),
            score=int(score_val) if score_val is not None else 0,
            matched=bool(detailed.get("matched", False)),
            distance=detailed.get("distance"),
            threshold=float(detailed.get("threshold", 0.68)),
            detail=str(detailed.get("detail", "")),
        )
    finally:
        if temp_id_path and os.path.exists(temp_id_path):
            try:
                os.unlink(temp_id_path)
            except Exception:
                pass
        if temp_selfie_path and os.path.exists(temp_selfie_path):
            try:
                os.unlink(temp_selfie_path)
            except Exception:
                pass
