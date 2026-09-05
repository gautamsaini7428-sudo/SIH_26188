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
