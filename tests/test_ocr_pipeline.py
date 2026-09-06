"""Tests for OCR image preprocessing and pipeline functions."""
import numpy as np
import pytest
from unittest.mock import patch, MagicMock
from PIL import Image

from app.preprocessing import (
    compute_skew_angle,
    rotate_image,
    smart_resize,
    enhance_contrast_clahe,
    denoise_image,
    preprocess_image,
    load_image_from_bytes,
)
from app.engines import get_ocr_engine


def test_smart_resize_upscale():
    # Small 200x150 image should be upscaled so long side is >= min_dim
    img = np.zeros((150, 200, 3), dtype=np.uint8)
    resized = smart_resize(img, min_dim=1000, max_dim=2500)
    assert max(resized.shape[:2]) >= 1000


def test_smart_resize_downscale():
    # Huge 4000x3000 image should be downscaled so long side is <= max_dim
    img = np.zeros((3000, 4000, 3), dtype=np.uint8)
    resized = smart_resize(img, min_dim=1000, max_dim=2500)
    assert max(resized.shape[:2]) <= 2500


def test_contrast_and_denoise_preserves_shape():
    img = np.ones((300, 400, 3), dtype=np.uint8) * 128
    enhanced = enhance_contrast_clahe(img)
    assert enhanced.shape == (300, 400, 3)
    denoised = denoise_image(enhanced)
    assert denoised.shape == (300, 400, 3)


def test_load_image_from_bytes():
    pil_img = Image.new("RGB", (200, 200), color=(255, 0, 0))
    import io
    buf = io.BytesIO()
    pil_img.save(buf, format="JPEG")
    pages = load_image_from_bytes(buf.getvalue(), filename="sample.jpg")
    assert len(pages) == 1
    assert pages[0].shape == (200, 200, 3)


def test_get_ocr_engine_returns_instance():
    engine = get_ocr_engine()
    assert engine is not None
    assert hasattr(engine, "recognize")
    assert hasattr(engine, "name")


# ─── Bug 2 Regression: OCR Engine Unavailable ───

def test_ocr_engine_unavailable_raises_distinct_error():
    """
    REGRESSION — Bug 2: When both OCR engines (EasyOCR and PaddleOCR) fail to load,
    get_ocr_engine() must raise OCREngineUnavailableError — NOT silently return None
    or raise a generic ImportError that gets swallowed upstream.
    """
    from app.engines import OCREngineUnavailableError
    import app.engines as engines_module

    # Reset the cached engine so get_ocr_engine() re-initializes
    original_active = engines_module._active_engine
    engines_module._active_engine = None

    try:
        with patch("app.engines.easyocr_engine.EasyOCREngine", side_effect=ImportError("no easyocr")), \
             patch("app.engines.paddleocr_engine.PaddleOCREngine", side_effect=ImportError("no paddleocr")):
            with pytest.raises(OCREngineUnavailableError):
                engines_module._active_engine = None
                get_ocr_engine()
    finally:
        engines_module._active_engine = original_active


def test_ocr_engine_unavailable_status_not_no_text_detected(tmp_path):
    """
    REGRESSION — Bug 2: When the OCR engine fails to load, process_image_ndarray
    must propagate OCR_ENGINE_UNAVAILABLE status, NOT silently return NO_TEXT_DETECTED
    (which implies the document was blank rather than the engine being broken).
    """
    from app.engines import OCREngineUnavailableError
    from app.services.ocr import process_image_ndarray
    import numpy as np

    # A real-looking image with content
    img = np.full((300, 400, 3), 200, dtype=np.uint8)

    with patch("app.services.ocr.get_ocr_engine") as mock_get_engine:
        mock_engine = MagicMock()
        mock_engine.recognize.side_effect = OCREngineUnavailableError("easyocr not installed")
        mock_get_engine.return_value = mock_engine

        # process_image_ndarray must re-raise OCREngineUnavailableError
        # so that extract_fields() can catch it and set OCR_ENGINE_UNAVAILABLE
        with pytest.raises(OCREngineUnavailableError):
            process_image_ndarray(img)


@pytest.mark.asyncio
async def test_extract_fields_preserves_gender_and_nationality_for_national_id(tmp_path):
    """
    REGRESSION — P1.5: Verify gender and nationality are NOT dropped for NATIONAL_ID.
    When raw OCR text contains gender indicators (e.g. 'MALE'), fields['gender']
    must be populated, and domestic ID default nationality ('INDIAN') must be inferred.
    """
    from PIL import Image, ImageDraw
    from app.services.ocr import extract_fields

    test_img = Image.new("RGB", (600, 400), color=(240, 240, 240))
    draw = ImageDraw.Draw(test_img)
    draw.text((30, 30), "GOVERNMENT OF INDIA", fill=(0, 0, 0))
    draw.text((30, 60), "AADHAAR CARD", fill=(0, 0, 0))
    draw.text((30, 90), "Name: ROHAN VERMA", fill=(0, 0, 0))
    draw.text((30, 120), "DOB: 15/08/1992", fill=(0, 0, 0))
    draw.text((30, 150), "Gender: MALE", fill=(0, 0, 0))
    draw.text((30, 180), "1234 5678 9012", fill=(0, 0, 0))

    img_path = str(tmp_path / "aadhaar_with_gender.jpg")
    test_img.save(img_path)

    # Mock process_image_ndarray to return structured OCR result with gender
    mock_ocr_res = {
        "raw_text": "GOVERNMENT OF INDIA\nAADHAAR CARD\nName: ROHAN VERMA\nDOB: 15/08/1992\nGender: MALE\n1234 5678 9012",
        "lines": [],
        "mrz": MagicMock(detected=False),
        "document_type": "id",
        "fields": {
            "name": "ROHAN VERMA",
            "date_of_birth": "15/08/1992",
            "gender": "MALE",
            "document_number": "1234 5678 9012",
        },
        "provenance": {},
        "ocr_status": "SUCCESS",
    }

    with patch("app.services.ocr.process_image_ndarray", return_value=mock_ocr_res):
        res = await extract_fields(img_path, doc_type="NATIONAL_ID")
        fields = res["fields"]

        assert "gender" in fields
        assert fields["gender"] == "MALE"
        assert "nationality" in fields
        assert fields["nationality"] == "INDIAN"
        assert fields.get("nationality_source") == "inferred"


