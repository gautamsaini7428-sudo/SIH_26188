import logging
from typing import Optional, List
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.schemas import OCRResponse, OCRLine, ExtractedFields, MRZResult
from app.preprocessing import load_image_from_bytes
from app.services.ocr import process_image_ndarray
from app.auth import require_officer
from app.models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["ocr"])


@router.post("/ocr", response_model=OCRResponse)
async def ocr_endpoint(
    file: UploadFile = File(...),
    current_user: User = Depends(require_officer),
):
    """
    Standalone Document OCR API Endpoint.

    Processes uploaded image or PDF document:
    - Image loading & orientation correction
    - Smart enhancement (CLAHE + bilateral denoising)
    - OCR text and bounding box extraction
    - MRZ zone detection & ICAO 9303 checksum validation
    - Document classification & structured field extraction
    """
    try:
        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(status_code=400, detail="Empty file uploaded.")

        filename: Optional[str] = file.filename or ""
        images = load_image_from_bytes(file_bytes, filename=filename)
        if not images:
            raise HTTPException(status_code=400, detail="No images could be decoded from the upload.")

        aggregated_text_parts = []
        aggregated_lines = []
        aggregated_fields_dict: dict = {}
        last_mrz: Optional[MRZResult] = None
        last_doc_type = "unknown"

        for idx, image in enumerate(images):
            result = process_image_ndarray(image)
            aggregated_text_parts.append(result["raw_text"])

            if idx == 0:
                aggregated_lines = result["lines"]
            if result["mrz"].detected:
                last_mrz = result["mrz"]
            if result["document_type"] != "unknown":
                last_doc_type = result["document_type"]

            for k, v in result["fields"].items():
                if v is not None and (k not in aggregated_fields_dict or aggregated_fields_dict.get(k) is None):
                    aggregated_fields_dict[k] = v

        raw_text = "\n\n".join(aggregated_text_parts)
        fields = ExtractedFields(**aggregated_fields_dict)
        if last_mrz is not None:
            mrz_result = last_mrz
        else:
            mrz_result = MRZResult(detected=False, raw=None, valid=None, fields={})

        response = OCRResponse(
            raw_text=raw_text,
            lines=aggregated_lines,
            fields=fields,
            mrz=mrz_result,
            document_type=last_doc_type,
        )
        return response
    except HTTPException:
        raise
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.exception("OCR processing failed: %s", e)
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {e}")
