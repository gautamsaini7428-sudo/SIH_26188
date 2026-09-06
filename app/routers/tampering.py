"""
Tampering Analysis Router

Endpoint: POST /analyze-tampering
Accepts an image file and executes the 3-signal tampering detection pipeline (ELA, Copy-Move, Metadata/Font).
Returns composite tampering score, regions, signals breakdown, and palette-accurate heatmap base64.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends
from app.services.tampering import detect_tampering
from app.utils.file_handler import save_upload_file
from app.schemas import AnalyzeTamperingResponse, TamperingRegion
from app.config import get_settings
from app.auth import require_officer
from app.models import User

router = APIRouter(prefix="", tags=["tampering"])
settings = get_settings()


@router.post("/analyze-tampering", response_model=AnalyzeTamperingResponse)
async def analyze_tampering_endpoint(
    file: UploadFile = File(..., description="Document image file to analyze for forgery and tampering"),
    current_user: User = Depends(require_officer),
):
    """
    Forensic Document Tampering Analysis Endpoint.

    Evaluates:
    1. Error Level Analysis (ELA) resave noise gradients
    2. Duplicated patch / copy-move cloning detection
    3. Image editing metadata & font baseline irregularities

    Returns:
    - tampering_score (0-100)
    - tampering_regions (bounding boxes of anomalies)
    - heatmap_image_base64 (data URI with theme-accurate mint/mauve overlay)
    - signals (individual metric scores & metadata traces)
    - summary
    """
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file uploaded")

    # Save uploaded file temporarily for inspection
    rel_path = await save_upload_file(file, "tamper_analysis")
    full_path = settings.upload_dir + "/" + rel_path

    result = await detect_tampering(full_path)

    return AnalyzeTamperingResponse(
        tampering_score=result.score,
        tampering_regions=[
            TamperingRegion(
                x=r["x"],
                y=r["y"],
                w=r["w"],
                h=r["h"],
                field=r.get("field"),
                confidence=r.get("confidence"),
                reason=r.get("reason"),
            )
            for r in result.regions
        ],
        heatmap_image_base64=result.heatmap_base64,
        signals=result.signals,
        summary=result.summary,
    )
