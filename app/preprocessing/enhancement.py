import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)


def smart_resize(
    image: np.ndarray,
    min_dim: int = 1000,
    max_dim: int = 2500
) -> np.ndarray:
    """
    Resizes image preserving aspect ratio so that:
    - Small images are upscaled to at least min_dim on the longer side (great for reading small text).
    - Extremely large images are downscaled to at most max_dim to keep OCR fast and crisp.
    """
    h, w = image.shape[:2]
    long_side = max(h, w)

    if long_side < min_dim:
        scale = min_dim / float(long_side)
        new_w = int(w * scale)
        new_h = int(h * scale)
        return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
    elif long_side > max_dim:
        scale = max_dim / float(long_side)
        new_w = int(w * scale)
        new_h = int(h * scale)
        return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)

    return image


def enhance_contrast_clahe(image: np.ndarray) -> np.ndarray:
    """
    Enhances contrast using CLAHE on the Lightness channel in LAB color space.
    Preserves colors while boosting faint or unevenly illuminated text.
    """
    try:
        lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
        l, a, b = cv2.split(lab)

        # Apply CLAHE to L-channel
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)

        limg = cv2.merge((cl, a, b))
        enhanced = cv2.cvtColor(limg, cv2.COLOR_LAB2RGB)
        return enhanced
    except Exception as e:
        logger.debug(f"CLAHE enhancement failed: {e}")
        return image


def denoise_image(image: np.ndarray) -> np.ndarray:
    """
    Applies edge-preserving bilateral filtering to reduce sensor noise and compression artifacts.
    """
    try:
        # Bilateral filter preserves sharp character edges while smoothing flat noise
        denoised = cv2.bilateralFilter(image, d=5, sigmaColor=50, sigmaSpace=50)
        return denoised
    except Exception as e:
        logger.debug(f"Denoising failed: {e}")
        return image


def evaluate_document_quality(image: np.ndarray) -> dict:
    """
    Evaluates comprehensive document quality signals:
    - Dimensions & resolution
    - Sharpness / Blur (Laplacian variance)
    - Brightness mean & Contrast standard deviation
    - Glare / Overexposure percentage
    - Aspect ratio suitability

    Returns structured dict:
    {
        "status": "GOOD" | "ACCEPTABLE" | "POOR" | "UNUSABLE",
        "score": float (0.0 to 1.0),
        "blur_score": float,
        "brightness": float,
        "contrast": float,
        "glare_ratio": float,
        "is_blurry": bool,
        "is_glary": bool,
        "is_low_res": bool,
        "reasons": List[str],
        "summary": str
    }
    """
    if image is None or image.size == 0:
        return {
            "status": "UNUSABLE",
            "score": 0.0,
            "blur_score": 0.0,
            "brightness": 0.0,
            "contrast": 0.0,
            "glare_ratio": 0.0,
            "is_blurry": True,
            "is_glary": False,
            "is_low_res": True,
            "reasons": ["Empty or corrupted image data."],
            "summary": "UNUSABLE: No readable pixel data.",
        }

    h, w = image.shape[:2]
    reasons = []

    # 1. Resolution Check
    is_low_res = False
    if w < 200 or h < 150:
        is_low_res = True
        reasons.append(f"Image resolution too low ({w}x{h}px; minimum 300x200px recommended for reliable analysis).")
    elif w < 400 or h < 300:
        is_low_res = True
        reasons.append(f"Low image resolution ({w}x{h}px).")

    # Grayscale conversion for photometric signals
    if len(image.shape) == 3 and image.shape[2] >= 3:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    else:
        gray = image

    # 2. Sharpness / Blur (Laplacian variance)
    laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    is_blurry = False
    if laplacian_var < 35.0:
        is_blurry = True
        reasons.append(f"Severe blur detected (sharpness variance {laplacian_var:.1f} < 35.0).")
    elif laplacian_var < 70.0:
        reasons.append(f"Slight blur detected (sharpness variance {laplacian_var:.1f}).")

    # 3. Brightness & Contrast
    mean_brightness = float(np.mean(gray))
    contrast_std = float(np.std(gray))

    if mean_brightness < 30.0:
        reasons.append(f"Image is underexposed / very dark (brightness {mean_brightness:.1f}/255).")
    elif mean_brightness > 235.0:
        reasons.append(f"Image is severely overexposed (brightness {mean_brightness:.1f}/255).")

    if contrast_std < 18.0:
        reasons.append(f"Extremely low contrast (std dev {contrast_std:.1f}).")

    # 4. Glare / Saturation
    glare_pixels = int(np.sum(gray >= 250))
    total_pixels = gray.size
    glare_ratio = float(glare_pixels / max(1, total_pixels))
    is_glary = False
    if glare_ratio > 0.20:
        is_glary = True
        reasons.append(f"Significant specular reflection / glare ({glare_ratio * 100:.1f}% saturated pixels).")

    # 5. Classify Overall Quality State
    # Quality scale: GOOD, ACCEPTABLE, POOR, UNUSABLE
    if w < 150 or h < 100 or contrast_std < 10.0 or (is_blurry and laplacian_var < 15.0):
        status = "UNUSABLE"
        score = 0.15
    elif is_blurry or is_low_res or mean_brightness < 40.0 or mean_brightness > 230.0 or is_glary:
        status = "POOR"
        score = 0.45
    elif laplacian_var < 100.0 or contrast_std < 30.0 or glare_ratio > 0.08:
        status = "ACCEPTABLE"
        score = 0.75
    else:
        status = "GOOD"
        score = 0.95

    summary = (
        "Document quality is adequate for forensic screening."
        if status in ("GOOD", "ACCEPTABLE")
        else f"Document quality is {status}: {'; '.join(reasons)}"
    )

    return {
        "status": status,
        "score": score,
        "blur_score": laplacian_var,
        "brightness": mean_brightness,
        "contrast": contrast_std,
        "glare_ratio": glare_ratio,
        "is_blurry": is_blurry,
        "is_glary": is_glary,
        "is_low_res": is_low_res,
        "reasons": reasons,
        "summary": summary,
    }


def preprocess_image(
    image: np.ndarray,
    min_dim: int = 1000,
    max_dim: int = 2500,
    enable_clahe: bool = True,
    enable_denoise: bool = True
) -> np.ndarray:
    """
    Full enhancement pipeline: smart resize -> contrast enhancement -> denoising.
    """
    resized = smart_resize(image, min_dim=min_dim, max_dim=max_dim)
    enhanced = resized
    if enable_clahe:
        enhanced = enhance_contrast_clahe(enhanced)
    if enable_denoise:
        enhanced = denoise_image(enhanced)
    return enhanced

