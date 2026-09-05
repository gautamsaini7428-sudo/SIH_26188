"""
Document Validation Gate Service

Validates whether an uploaded image contains:
1. A detectable face / ID portrait region
2. Extractable identity text lines and document structural features

If either check fails, halts the pipeline immediately with a REJECTED verdict.
"""

import os
from typing import Tuple, Optional
from PIL import Image, ImageStat, ImageFilter


class DocumentValidationError(Exception):
    def __init__(self, message: str = "No valid identity document detected"):
        self.message = message
        self.error_code = "INVALID_DOCUMENT"
        super().__init__(self.message)


class NoFaceDetectedError(Exception):
    def __init__(self, message: str = "No face detected in submitted images"):
        self.message = message
        self.error_code = "NO_FACE_DETECTED"
        super().__init__(self.message)


def validate_identity_document(file_path: str, doc_type: str = "DRIVING_LICENSE") -> Tuple[bool, Optional[str]]:
    """
    Perform pre-flight validation gate on uploaded document image.

    Checks:
    1. Readability & valid dimensions
    2. Aspect ratio compatibility with standard IDs / Passports
    3. Detectable face presence (primary portrait) - skipped for VISA
    4. Extractable text / high-frequency horizontal document structure

    Returns:
        (is_valid, failure_reason)
    """
    if not os.path.exists(file_path):
        return False, "No valid identity document detected"

    try:
        with Image.open(file_path) as img:
            width, height = img.size

            # Check 1: Minimum dimensions
            if width < 150 or height < 100:
                return False, "No valid identity document detected"

            # Check 2: Aspect ratio
            aspect_ratio = width / float(height)
            if aspect_ratio < 0.45 or aspect_ratio > 2.8:
                return False, "No valid identity document detected"

            # Convert to grayscale for text & structural entropy analysis
            gray_img = img.convert("L")
            stat = ImageStat.Stat(gray_img)
            std_dev = stat.stddev[0]
            mean_brightness = stat.mean[0]

            # Uniform canvas or extreme exposure
            if std_dev < 12.0 or mean_brightness < 10 or mean_brightness > 248:
                return False, "No valid identity document detected"

            # Check 3: Extractable Text / Edge Density
            edges = gray_img.filter(ImageFilter.FIND_EDGES)
            edge_stat = ImageStat.Stat(edges)
            edge_mean = edge_stat.mean[0]

            if edge_mean < 4.5:
                return False, "No extractable identity fields found"

            # Check 4: Face Detection in document (skipped for VISA)
            if doc_type.upper() != "VISA":
                has_face = detect_face_presence(file_path)
                if not has_face:
                    return False, "No face detected in submitted document"

            return True, None

    except Exception:
        return False, "No valid identity document detected"


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

    # Fallback skin tone heuristic
    try:
        with Image.open(image_path) as img:
            rgb_img = img.convert("RGB")
            pixels = list(rgb_img.resize((100, 100)).getdata())
            skin_pixels = 0
            for r, g, b in pixels:
                if r > 60 and g > 40 and b > 20 and (max(r, g, b) - min(r, g, b) > 15) and abs(r - g) > 15 and r > g and r > b:
                    skin_pixels += 1

            skin_ratio = skin_pixels / float(len(pixels))
            if skin_ratio < 0.02:
                return False

            return True
    except Exception:
        return False
