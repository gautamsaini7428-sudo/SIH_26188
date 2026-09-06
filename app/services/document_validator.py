"""
Identity Document Intake Validation Gate — SIH26188

Pre-flight verification gate for uploaded identity document files:
1. Valid dimensions & standard ID card / Passport aspect ratio
2. Non-uniform content, non-blank, non-saturated
3. Structural text & edge density check (rejects building sketches / drawings)
"""

import os
import numpy as np
from typing import Tuple, Optional, Dict, Any
from PIL import Image, ImageStat, ImageFilter

from app.preprocessing.enhancement import evaluate_document_quality


class ValidationGateResult(tuple):
    """
    2-tuple subclass (is_valid, failure_reason) that also carries quality_info
    attribute for backward-compatible 2-tuple unpacking.
    """
    def __new__(cls, is_valid: bool, failure_reason: Optional[str] = None, quality_info: Optional[Dict[str, Any]] = None):
        instance = super().__new__(cls, (is_valid, failure_reason))
        instance.is_valid = is_valid
        instance.failure_reason = failure_reason
        instance.quality_info = quality_info or {}
        return instance


def validate_identity_document(
    file_path: str,
    doc_type: str = "DRIVING_LICENSE"
) -> ValidationGateResult:
    """
    Perform pre-flight validation gate on uploaded document image.

    Checks:
    1. Readability & valid dimensions
    2. Aspect ratio compatibility with standard IDs / Passports
    3. Structural entropy & non-uniform content
    4. Quality evaluation

    Returns:
        ValidationGateResult(is_valid, failure_reason, quality_info)
        which supports standard 2-tuple unpacking: `is_valid, reason = validate_identity_document(path)`
    """
    default_quality = {
        "status": "UNUSABLE",
        "score": 0.0,
        "reasons": ["File not accessible"],
        "summary": "UNUSABLE: File not accessible",
    }

    if not os.path.exists(file_path):
        return ValidationGateResult(False, "No valid identity document detected", default_quality)

    try:
        with Image.open(file_path) as img:
            try:
                from PIL import ImageOps
                img = ImageOps.exif_transpose(img)
            except Exception:
                pass

            width, height = img.size

            # Check 1: Minimum dimensions
            if width < 100 or height < 80:
                return ValidationGateResult(
                    False,
                    "Image dimensions are too small to be a document",
                    {
                        "status": "UNUSABLE",
                        "score": 0.1,
                        "reasons": [f"Image dimensions {width}x{height}px too small"],
                        "summary": f"UNUSABLE: Image dimensions {width}x{height}px too small",
                    },
                )

            # Check 2: Aspect ratio
            aspect_ratio = width / float(height)
            if aspect_ratio < 0.3 or aspect_ratio > 3.5:
                return ValidationGateResult(
                    False,
                    f"Extreme aspect ratio ({aspect_ratio:.2f}) incompatible with identity documents",
                    {
                        "status": "UNUSABLE",
                        "score": 0.1,
                        "reasons": [f"Extreme aspect ratio ({aspect_ratio:.2f})"],
                        "summary": "UNUSABLE: Extreme aspect ratio",
                    },
                )

            rgb_img = img.convert("RGB")
            img_np = np.array(rgb_img)
            quality_info = evaluate_document_quality(img_np)

            # Convert to grayscale for text & structural entropy analysis
            gray_img = img.convert("L")
            stat = ImageStat.Stat(gray_img)
            std_dev = stat.stddev[0]
            mean_brightness = stat.mean[0]

            # Uniform canvas or completely blank
            if std_dev < 10.0 or mean_brightness < 8 or mean_brightness > 250:
                return ValidationGateResult(
                    False,
                    "Image contains blank, uniform, or completely saturated content",
                    quality_info,
                )

            # Check 3: Structural text / edge density for non-document drawings/sketches
            edges = gray_img.filter(ImageFilter.FIND_EDGES)
            edge_stat = ImageStat.Stat(edges)
            edge_mean = edge_stat.mean[0]

            has_face = detect_face_presence(file_path)
            if std_dev < 22.0 and not has_face:
                return ValidationGateResult(
                    False,
                    "No extractable identity fields or document structure found",
                    quality_info,
                )
            if edge_mean < 4.0 or (edge_mean < 6.5 and not has_face and std_dev < 25.0):
                return ValidationGateResult(
                    False,
                    "No extractable identity fields or document structure found",
                    quality_info,
                )

            return ValidationGateResult(True, None, quality_info)

    except Exception as exc:
        return ValidationGateResult(False, f"Failed to parse document image file: {str(exc)}", default_quality)


def detect_face_presence(image_path: str) -> bool:
    """
    Fast-fail gate: Verify whether a face region is present in an image.
    Uses OpenCV Haar Cascade first, falling back to skin tone heuristic.
    """
    if not os.path.exists(image_path):
        return False

    # Try Haar Cascade via OpenCV
    try:
        import cv2
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        if os.path.exists(cascade_path):
            cv_img = cv2.imread(image_path)
            if cv_img is not None:
                gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
                face_cascade = cv2.CascadeClassifier(cascade_path)
                faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=3, minSize=(30, 30))
                if len(faces) > 0:
                    return True
    except Exception:
        pass

    # Fallback skin tone heuristic using numpy
    try:
        with Image.open(image_path) as img:
            rgb_img = img.convert("RGB").resize((100, 100))
            arr = np.array(rgb_img, dtype=np.int32)
            r = arr[:, :, 0]
            g = arr[:, :, 1]
            b = arr[:, :, 2]

            skin_mask = (
                (r > 60) & (g > 40) & (b > 20) &
                ((np.maximum(np.maximum(r, g), b) - np.minimum(np.minimum(r, g), b)) > 15) &
                (np.abs(r - g) > 10) &
                (r > g) & (r > b)
            )
            skin_ratio = float(np.sum(skin_mask)) / float(arr.shape[0] * arr.shape[1])
            return skin_ratio >= 0.015
    except Exception:
        return False
