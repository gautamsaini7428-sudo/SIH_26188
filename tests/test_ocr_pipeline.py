"""Tests for OCR image preprocessing and pipeline functions."""
import numpy as np
import pytest
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
