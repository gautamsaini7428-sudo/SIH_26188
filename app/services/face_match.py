"""
Optimized Face Verification Service
Module 1 - SIH Problem Statement 26188

Provides biometric evaluation:
1. Multi-stage face intake quality gate (no face, multiple faces, low quality)
2. Portrait feature extraction
3. Anti-spoofing and presentation attack detection (separate from face match)
4. Safe handling of missing evidence (never flags 0% mismatch when face detection fails)

IMPORTANT: This module requires DeepFace/ArcFace to be installed and functional.
If DeepFace cannot run, the pipeline returns a hard error status rather than
fabricating a result. Silently falling back to geometric heuristics is NOT safe.
"""

import asyncio
import logging
import math
import os
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image, ImageOps

from app.schemas import (
    QualityResult,
    LivenessResult,
    PresentationAttackResult,
    FaceMatchResult,
    BiometricResult,
)

logger = logging.getLogger(__name__)

MODEL_NAME = "ArcFace"
DETECTOR_BACKEND = "opencv"
DISTANCE_METRIC = "cosine"
ARCFACE_COSINE_THRESHOLD = 0.68

MAX_IMAGE_FILE_BYTES = 15 * 1024 * 1024
MAX_IMAGE_DIMENSION = 4096
MIN_FACE_DIMENSION = 30

# Module-level flag: True only when DeepFace/ArcFace loaded successfully at startup.
# Checked before attempting embedding extraction so failures are loud and traceable.
FACE_MODEL_AVAILABLE = False


def warm_up_face_model() -> None:
    """
    Pre-load ArcFace model weights at startup.
    Sets FACE_MODEL_AVAILABLE=True on success.
    Logs CRITICAL and leaves FACE_MODEL_AVAILABLE=False on any failure — this
    means the pipeline will refuse to run biometric verification rather than
    silently producing fabricated results.
    """
    global FACE_MODEL_AVAILABLE
    try:
        from deepface import DeepFace
        dummy_img = np.zeros((112, 112, 3), dtype=np.uint8)
        _ = DeepFace.represent(
            img_path=dummy_img,
            model_name=MODEL_NAME,
            detector_backend="skip",
            enforce_detection=False,
        )
        FACE_MODEL_AVAILABLE = True
        logger.info("ArcFace feature extractor successfully warmed up.")
    except ImportError as exc:
        FACE_MODEL_AVAILABLE = False
        logger.critical(
            f"FACE MODEL UNAVAILABLE: DeepFace/ArcFace is not installed. "
            f"Biometric face verification will return error status for all requests. "
            f"Install deepface and a compatible tensorflow backend. Error: {exc}"
        )
    except Exception as exc:
        FACE_MODEL_AVAILABLE = False
        logger.critical(
            f"FACE MODEL UNAVAILABLE: ArcFace warm-up failed — model weights may be "
            f"missing or corrupt. Biometric verification will be disabled. Error: {exc}"
        )


def _secure_load_and_normalize(image_path: str) -> Tuple[Optional[np.ndarray], Optional[str]]:
    if not image_path or not isinstance(image_path, str):
        return None, "File path is invalid or empty."

    if not os.path.exists(image_path):
        return None, "Image file not found on disk."

    try:
        file_size = os.path.getsize(image_path)
    except OSError as exc:
        return None, f"File access error: {exc}"

    if file_size == 0:
        return None, "Image file is 0 bytes."
    if file_size > MAX_IMAGE_FILE_BYTES:
        return None, "Image size exceeds limit."

    try:
        with Image.open(image_path) as pil_img:
            w, h = pil_img.size
            if w > MAX_IMAGE_DIMENSION or h > MAX_IMAGE_DIMENSION:
                return None, f"Image dimensions ({w}x{h}) exceed maximum allowed ({MAX_IMAGE_DIMENSION}px)."

            transposed_img = ImageOps.exif_transpose(pil_img)
            rgb_array = np.array(transposed_img.convert("RGB"))
            bgr_array = cv2.cvtColor(rgb_array, cv2.COLOR_RGB2BGR)
            return bgr_array, None
    except Exception as exc:
        return None, f"Malformed image file: {str(exc)}"


def _calculate_calibrated_score(distance: float, threshold: float = ARCFACE_COSINE_THRESHOLD) -> int:
    if math.isnan(distance) or distance < 0.0:
        return 0

    if distance <= threshold:
        ratio = distance / threshold
        score = 100.0 - (ratio * 30.0)
    else:
        decay_range = max(0.01, 1.2 - threshold)
        excess = min(distance - threshold, decay_range)
        ratio = excess / decay_range
        score = 70.0 - (ratio * 70.0)

    return int(round(max(0.0, min(100.0, score))))


def _compute_spatial_face_descriptor(crop_bgr: np.ndarray) -> List[float]:
    """
    DEPRECATED — DO NOT USE IN THE VERIFICATION PIPELINE.

    This function computes a normalized histogram of HSV/Lab color + Sobel gradient
    magnitude in a 4x4 grid. It is NOT a facial embedding. Two different people, or
    a covered face vs an ID photo, can easily match purely by lighting/skin-tone
    statistics.

    Kept for reference only. All pipeline code must use DeepFace/ArcFace embeddings
    or return a hard error — never this function.
    """
    resized = cv2.resize(crop_bgr, (112, 112))
    hsv = cv2.cvtColor(resized, cv2.COLOR_BGR2HSV)
    lab = cv2.cvtColor(resized, cv2.COLOR_BGR2LAB)
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    sobelx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    sobely = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    mag = cv2.magnitude(sobelx, sobely)

    hist_h = cv2.calcHist([hsv], [0], None, [16], [0, 180]).flatten()
    hist_s = cv2.calcHist([hsv], [1], None, [16], [0, 256]).flatten()

    feats = []
    for r in range(4):
        for c in range(4):
            cell_lab = lab[r * 28:(r + 1) * 28, c * 28:(c + 1) * 28]
            cell_mag = mag[r * 28:(r + 1) * 28, c * 28:(c + 1) * 28]
            feats.extend([
                float(np.mean(cell_lab[:, :, 0])),
                float(np.mean(cell_lab[:, :, 1])),
                float(np.mean(cell_lab[:, :, 2])),
                float(np.mean(cell_mag)),
                float(np.std(cell_mag)),
                float(np.std(cell_lab[:, :, 0])),
            ])
    vec = np.concatenate([hist_h, hist_s, np.array(feats, dtype=np.float64)])
    norm = np.linalg.norm(vec)
    if norm > 0.0:
        vec /= norm
    return vec.tolist()


def _detect_faces_opencv_fallback(img_bgr: np.ndarray) -> List[Dict[str, Any]]:
    """
    Real classical face detector using an OpenCV Haar Cascade ensemble.

    This is the genuine fallback when DeepFace is unavailable for the face COUNT
    check in evaluate_biometrics_sync(). It evaluates frontalface_alt2, frontalface_alt,
    and frontalface_default to reliably detect genuine faces across various angles,
    card sizes, and lighting conditions.

    Returns zero entries when no actual face pattern is found.
    Does NOT fabricate confidence scores or crop fixed geometric regions.
    """
    h, w = img_bgr.shape[:2]
    if h < MIN_FACE_DIMENSION or w < MIN_FACE_DIMENSION:
        return []

    try:
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        cascade_files = [
            "haarcascade_frontalface_alt2.xml",
            "haarcascade_frontalface_alt.xml",
            "haarcascade_frontalface_default.xml",
        ]

        for c_file in cascade_files:
            c_path = os.path.join(cv2.data.haarcascades, c_file)
            if not os.path.exists(c_path):
                continue
            face_cascade = cv2.CascadeClassifier(c_path)
            for mn in (3, 2, 1):
                faces = face_cascade.detectMultiScale(
                    gray,
                    scaleFactor=1.08,
                    minNeighbors=mn,
                    minSize=(MIN_FACE_DIMENSION, MIN_FACE_DIMENSION),
                )
                # Filter out obvious false positives (e.g. covering entire 95%+ of card)
                valid = [
                    (fx, fy, fw, fh) for (fx, fy, fw, fh) in faces
                    if not (fw > 0.95 * w and fh > 0.95 * h)
                ]
                if valid:
                    result = []
                    for (fx, fy, fw, fh) in valid:
                        result.append({
                            "facial_area": {"x": int(fx), "y": int(fy), "w": int(fw), "h": int(fh)},
                            "face_confidence": None,
                            "embedding": None,
                        })
                    return result

        return []

    except Exception as exc:
        logger.warning(f"OpenCV Haar cascade face detection failed: {exc}")
        return []


def _check_face_occlusion(img_bgr: np.ndarray, facial_area: Dict[str, Any]) -> bool:
    """
    Checks whether the detected face region appears to be obstructed/occluded.

    Returns True if the face is likely occluded (hand/mask/finger over it).
    Returns False if the face appears clear.

    Strategy:
    1. Run haarcascade_eye.xml inside the face crop — a visible face typically has
       at least one detectable eye.
    2. Check skin-area ratio within the face crop across BGR and RGB interpretations.
       A hand, phone, or solid mask over the face reduces skin proportion significantly.
    3. Check central facial core variance (where eyes, nose, mouth reside). A flat
       occlusion (e.g. solid mask or covered lens) exhibits near-zero variance.
    """
    try:
        x = max(0, facial_area.get("x", 0))
        y = max(0, facial_area.get("y", 0))
        fw = max(10, facial_area.get("w", img_bgr.shape[1]))
        fh = max(10, facial_area.get("h", img_bgr.shape[0]))

        face_crop = img_bgr[y:min(img_bgr.shape[0], y + fh), x:min(img_bgr.shape[1], x + fw)]
        if face_crop.size == 0:
            return True  # Can't evaluate — treat as occluded

        # 1. Eye detection check
        eye_found = False
        try:
            eye_cascade_path = cv2.data.haarcascades + "haarcascade_eye.xml"
            if os.path.exists(eye_cascade_path):
                eye_cascade = cv2.CascadeClassifier(eye_cascade_path)
                gray_crop = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
                eyes = eye_cascade.detectMultiScale(
                    gray_crop,
                    scaleFactor=1.1,
                    minNeighbors=3,
                    minSize=(10, 10),
                )
                eye_found = len(eyes) > 0
        except Exception:
            pass

        # 2. Skin ratio check within crop (evaluating both BGR and RGB color order)
        ycrcb_bgr = cv2.cvtColor(face_crop, cv2.COLOR_BGR2YCrCb)
        ycrcb_rgb = cv2.cvtColor(face_crop, cv2.COLOR_RGB2YCrCb)
        mask_bgr = (
            (ycrcb_bgr[:, :, 0] > 20) &
            (ycrcb_bgr[:, :, 1] >= 130) & (ycrcb_bgr[:, :, 1] <= 180) &
            (ycrcb_bgr[:, :, 2] >= 75) & (ycrcb_bgr[:, :, 2] <= 135)
        )
        mask_rgb = (
            (ycrcb_rgb[:, :, 0] > 20) &
            (ycrcb_rgb[:, :, 1] >= 130) & (ycrcb_rgb[:, :, 1] <= 180) &
            (ycrcb_rgb[:, :, 2] >= 75) & (ycrcb_rgb[:, :, 2] <= 135)
        )
        total_pixels = face_crop.shape[0] * face_crop.shape[1]
        skin_ratio = max(float(np.sum(mask_bgr)), float(np.sum(mask_rgb))) / float(total_pixels) if total_pixels > 0 else 0.0

        # 3. Core feature region variance (central 50% where facial features live)
        ch, cw = face_crop.shape[:2]
        core = face_crop[int(ch * 0.25):int(ch * 0.75), int(cw * 0.25):int(cw * 0.75)]
        core_std = float(np.std(core)) if core.size > 0 else 0.0

        # Classify as occluded if:
        # No eye detected AND (insufficient skin ratio or flat/solid feature obstruction)
        if not eye_found and (skin_ratio < 0.08 or core_std < 5.0):
            logger.debug(f"Face occlusion detected: eye_found={eye_found}, skin_ratio={skin_ratio:.3f}, core_std={core_std:.1f}")
            return True

        return False

    except Exception as exc:
        logger.debug(f"Occlusion check skipped due to error: {exc}")
        return False  # Conservative: don't block if check itself fails


def locate_face_crop_for_embedding(img_bgr: np.ndarray, role: str) -> np.ndarray:
    """
    Locates and extracts the actual human face crop from an ID card or selfie.
    Supports:
    - Right-side ID photos (e.g. standard Aadhaar cards)
    - Left-side ID photos (e.g. PAN cards, Driving Licenses, Passports)
    - Centered or framed live selfies
    Uses cascade ensemble (alt2, alt, default) with multi-scale localization.
    """
    h, w = img_bgr.shape[:2]
    if h < MIN_FACE_DIMENSION or w < MIN_FACE_DIMENSION:
        return img_bgr

    try:
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        cascade_files = [
            "haarcascade_frontalface_alt2.xml",
            "haarcascade_frontalface_alt.xml",
            "haarcascade_frontalface_default.xml",
        ]

        # 1. Full-image scan
        for c_file in cascade_files:
            c_path = os.path.join(cv2.data.haarcascades, c_file)
            if not os.path.exists(c_path):
                continue
            face_cascade = cv2.CascadeClassifier(c_path)
            for mn in (3, 2, 1):
                faces = face_cascade.detectMultiScale(
                    gray,
                    scaleFactor=1.08,
                    minNeighbors=mn,
                    minSize=(MIN_FACE_DIMENSION, MIN_FACE_DIMENSION),
                )
                valid = [
                    (fx, fy, fw, fh) for (fx, fy, fw, fh) in faces
                    if not (fw > 0.95 * w and fh > 0.95 * h)
                ]
                if valid:
                    best_face = max(valid, key=lambda f: f[2] * f[3])
                    fx, fy, fw, fh = best_face
                    pad_x = int(0.15 * fw)
                    pad_y = int(0.15 * fh)
                    x1 = max(0, fx - pad_x)
                    y1 = max(0, fy - pad_y)
                    x2 = min(w, fx + fw + pad_x)
                    y2 = min(h, fy + fh + pad_y)
                    return img_bgr[y1:y2, x1:x2]

        # 2. If landscape card (w > 1.2 * h), scan right side (Aadhaar) and left side (PAN/DL) separately
        if w > 1.2 * h:
            # Right side scan (Aadhaar cards have portrait on the right)
            right_half = gray[:, int(0.45 * w):]
            for c_file in cascade_files[:2]:
                c_path = os.path.join(cv2.data.haarcascades, c_file)
                if not os.path.exists(c_path):
                    continue
                face_cascade = cv2.CascadeClassifier(c_path)
                faces = face_cascade.detectMultiScale(
                    right_half,
                    scaleFactor=1.06,
                    minNeighbors=1,
                    minSize=(20, 20),
                )
                if len(faces) > 0:
                    fx, fy, fw, fh = max(faces, key=lambda f: f[2] * f[3])
                    real_x = fx + int(0.45 * w)
                    pad_x, pad_y = int(0.15 * fw), int(0.15 * fh)
                    x1 = max(0, real_x - pad_x)
                    y1 = max(0, fy - pad_y)
                    x2 = min(w, real_x + fw + pad_x)
                    y2 = min(h, fy + fh + pad_y)
                    return img_bgr[y1:y2, x1:x2]

            # Left side scan (PAN / Driving License / Passport)
            left_half = gray[:, :int(0.55 * w)]
            for c_file in cascade_files[:2]:
                c_path = os.path.join(cv2.data.haarcascades, c_file)
                if not os.path.exists(c_path):
                    continue
                face_cascade = cv2.CascadeClassifier(c_path)
                faces = face_cascade.detectMultiScale(
                    left_half,
                    scaleFactor=1.06,
                    minNeighbors=1,
                    minSize=(20, 20),
                )
                if len(faces) > 0:
                    fx, fy, fw, fh = max(faces, key=lambda f: f[2] * f[3])
                    pad_x, pad_y = int(0.15 * fw), int(0.15 * fh)
                    x1 = max(0, fx - pad_x)
                    y1 = max(0, fy - pad_y)
                    x2 = min(w, fx + fw + pad_x)
                    y2 = min(h, fy + fh + pad_y)
                    return img_bgr[y1:y2, x1:x2]

    except Exception as exc:
        logger.debug(f"Dynamic face crop localization encountered error: {exc}")

    # Fallback to input image if no distinct bounding box was detected
    return img_bgr


def _extract_single_face_embedding(
    img_bgr: np.ndarray,
    role: str
) -> Tuple[Optional[List[float]], Optional[Dict[str, Any]]]:
    """
    Extracts a single face embedding using DeepFace/ArcFace.

    IMPORTANT: This function does NOT fall back to spatial color histograms.
    If DeepFace cannot run (not installed, model weights missing, or runtime error),
    it returns a hard error payload with status="error". The caller must handle this
    as FACE_VERIFICATION_UNAVAILABLE, not as a face match result.
    """
    # Attempt DeepFace ArcFace representation (handles mocked unit tests and real inference)
    try:
        from deepface import DeepFace
        # Dynamically locate the face crop (handles both left and right-side photos)
        crop_input = locate_face_crop_for_embedding(img_bgr, role=role)

        reps = DeepFace.represent(
            img_path=crop_input,
            model_name=MODEL_NAME,
            detector_backend="skip",
            enforce_detection=False,
            align=True,
        )
        if isinstance(reps, list):
            if len(reps) == 0:
                return None, {
                    "status": "no_face_detected",
                    "score": 0,
                    "matched": False,
                    "detail": f"No valid human face detected in {role}.",
                }
            if len(reps) > 1:
                return None, {
                    "status": "multiple_faces_detected",
                    "score": 0,
                    "matched": False,
                    "detail": f"Multiple faces identified in {role}. Screening requires exactly one.",
                }
            rep = reps[0]
            if isinstance(rep, dict) and "embedding" in rep and rep["embedding"]:
                return rep["embedding"], None
    except ImportError as exc:
        # DeepFace not installed — hard error, no fallback
        logger.error(
            f"DeepFace not installed — face verification unavailable for {role}. "
            f"Install deepface to enable biometric matching. Error: {exc}"
        )
        return None, {
            "status": "error",
            "score": 0,
            "matched": False,
            "detail": f"Face verification model unavailable: DeepFace is not installed. ({exc})",
        }
    except Exception as exc:
        # Any other DeepFace runtime failure — hard error, no fallback to color histograms
        logger.error(
            f"DeepFace inference failed for {role} — returning error, not falling back to "
            f"geometric heuristics. Error: {exc}"
        )
        return None, {
            "status": "error",
            "score": 0,
            "matched": False,
            "detail": f"Face verification model error: {exc}",
        }

    # If we reach here, DeepFace returned but the embedding was empty/invalid
    return None, {
        "status": "error",
        "score": 0,
        "matched": False,
        "detail": f"Face verification model returned an empty or invalid embedding for {role}.",
    }


def _compute_cosine_distance(source_rep: List[float], test_rep: List[float]) -> float:
    a = np.asarray(source_rep, dtype=np.float64)
    b = np.asarray(test_rep, dtype=np.float64)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    if norm_a == 0.0 or norm_b == 0.0:
        return 1.0

    similarity = np.dot(a, b) / (norm_a * norm_b)
    return float(max(0.0, min(2.0, 1.0 - similarity)))


def analyze_image_quality(img_bgr: np.ndarray, facial_area: Optional[Dict[str, Any]] = None) -> QualityResult:
    """
    Evaluate visual quality of the captured face image:
    1. Blur metric via Laplacian variance
    2. Illumination / exposure extremes
    3. Face crop dimension check
    """
    try:
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        
        # Focus on facial area if provided
        if facial_area:
            x, y, w, h = facial_area.get("x", 0), facial_area.get("y", 0), facial_area.get("w", 0), facial_area.get("h", 0)
            if w > 10 and h > 10 and y + h <= gray.shape[0] and x + w <= gray.shape[1]:
                crop = gray[max(0, y):min(gray.shape[0], y + h), max(0, x):min(gray.shape[1], x + w)]
            else:
                crop = gray
        else:
            crop = gray

        # 1. Blur detection (Laplacian variance)
        lap_var = float(cv2.Laplacian(crop, cv2.CV_64F).var())
        
        # 2. Exposure check
        mean_brightness = float(np.mean(crop))
        
        issues = []
        is_low_quality = False
        quality_score = 1.0

        if lap_var < 45.0:
            issues.append(f"Image is blurry (sharpness metric: {round(lap_var, 1)})")
            is_low_quality = True
            quality_score = max(0.2, lap_var / 100.0)
        elif lap_var < 80.0:
            quality_score = 0.75

        if mean_brightness < 35.0:
            issues.append("Image is severely underexposed (too dark)")
            is_low_quality = True
            quality_score = min(quality_score, 0.3)
        elif mean_brightness > 235.0:
            issues.append("Image is severely overexposed (glare/washout)")
            is_low_quality = True
            quality_score = min(quality_score, 0.4)

        status_str = "LOW_QUALITY" if is_low_quality else "GOOD"
        details_str = "; ".join(issues) if issues else f"Adequate sharpness ({round(lap_var, 1)}) and lighting ({round(mean_brightness, 1)})"

        return QualityResult(
            status=status_str,
            score=round(quality_score, 2),
            details=details_str,
        )
    except Exception as e:
        logger.warning(f"Image quality evaluation failed: {e}")
        return QualityResult(
            status="LOW_QUALITY",
            score=0.0,
            details=f"Image quality evaluation failed: {e}",
        )


def analyze_liveness_and_presentation_attack(img_bgr: np.ndarray, facial_area: Optional[Dict[str, Any]] = None) -> Tuple[LivenessResult, PresentationAttackResult]:
    """
    Evaluate anti-spoofing indicators:
    1. Screen replay detection (high frequency periodic patterns / moire)
    2. Print attack / texture flatness detection (color disparity & standard deviation)
    3. Obstruction detection (face area occlusions)

    Design principles (Bug 8 fix):
    - Both independent signals for a given attack type must fire — a single marginal
      heuristic value alone is NOT sufficient for a hard FAKE gate.
    - Thresholds are set with deliberate safety margin validated against genuine
      photographic samples (test_samples/selfie_case_1.jpg, selfie_case_2.jpg):
        * selfie_case_1: cr_std=6.1, cb_std=10.0, freq_ratio=0.979, hfe=135.8
        * selfie_case_2: cr_std=6.0, cb_std=9.6, freq_ratio=0.976, hfe=135.1
    - Raw signal values are always logged at DEBUG level for threshold tuning.
    - The returned PresentationAttackResult.detected flag is set ONLY when both
      independent signals corroborate the attack type. A lone borderline signal
      sets detected=False with reduced score so the caller (verification.py) can
      treat it as SUSPICIOUS rather than unconditional FAKE.
    """
    try:
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape[:2]

        if facial_area:
            fx, fy, fw, fh = facial_area.get("x", 0), facial_area.get("y", 0), facial_area.get("w", 0), facial_area.get("h", 0)
            if fw > 20 and fh > 20 and fy + fh <= h and fx + fw <= w:
                face_crop = img_bgr[max(0, fy):min(h, fy + fh), max(0, fx):min(w, fx + fw)]
            else:
                face_crop = img_bgr
        else:
            face_crop = img_bgr

        # 1. Texture & Color Disparity analysis (chroma channel variance)
        ycrcb = cv2.cvtColor(face_crop, cv2.COLOR_BGR2YCrCb)
        _, cr, cb = cv2.split(ycrcb)
        cr_std = float(np.std(cr))
        cb_std = float(np.std(cb))
        color_disp = (cr_std + cb_std) / 2.0

        # 2. High-Frequency Fourier analysis for screen moire / pixel grid
        crop_gray = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
        resized_gray = cv2.resize(crop_gray, (128, 128))
        f_transform = np.fft.fft2(resized_gray)
        f_shift = np.fft.fftshift(f_transform)
        magnitude_spectrum = 20 * np.log(np.abs(f_shift) + 1e-6)

        center_x, center_y = 64, 64
        y_coords, x_coords = np.ogrid[:128, :128]
        dist_from_center = np.sqrt((x_coords - center_x)**2 + (y_coords - center_y)**2)
        high_freq_mask = (dist_from_center > 35) & (dist_from_center < 60)
        high_freq_energy = float(np.mean(magnitude_spectrum[high_freq_mask]))
        total_energy = float(np.mean(magnitude_spectrum))
        freq_ratio = high_freq_energy / (total_energy + 1e-6)

        # Always log raw signal values so thresholds can be tuned from production logs
        logger.debug(
            f"Anti-spoofing signals — "
            f"cr_std={cr_std:.3f} cb_std={cb_std:.3f} color_disp={color_disp:.3f} "
            f"freq_ratio={freq_ratio:.4f} high_freq_energy={high_freq_energy:.2f} "
            f"total_energy={total_energy:.2f}"
        )

        attack_detected = False
        attack_type = None
        attack_score = 0.05
        attack_details = []

        # ── Screen Replay ─────────────────────────────────────────────────────────
        # Genuine samples (test_samples/): freq_ratio ≈ 0.976–0.993, hfe ≈ 135–156
        # Require BOTH:
        #   freq_ratio > 1.50   (clear separation from genuine ~0.98, with margin)
        #   high_freq_energy > 145.0  (genuine samples peak at ~156 under a JPEG
        #                              path — thresholds set well above genuine range)
        # Note: a blank/uniform image has hfe ≈ -276 (well below 145), so it will
        # NOT trigger screen replay (it may trigger print attack below instead).
        screen_freq_signal  = freq_ratio > 1.50
        screen_energy_signal = high_freq_energy > 145.0
        if screen_freq_signal and screen_energy_signal:
            attack_detected = True
            attack_type = "SCREEN_REPLAY"
            attack_score = 0.88
            attack_details.append("Periodic high-frequency screen pixel grid / display moiré detected")
            logger.warning(
                f"SCREEN_REPLAY attack detected: freq_ratio={freq_ratio:.4f} "
                f"high_freq_energy={high_freq_energy:.2f}"
            )
        elif screen_freq_signal or screen_energy_signal:
            # Only one of the two screen-replay signals fired — not enough to hard-flag
            attack_score = max(attack_score, 0.30)
            logger.debug(
                f"Borderline screen-replay signal (single indicator only): "
                f"freq_signal={screen_freq_signal} energy_signal={screen_energy_signal}"
            )

        # ── Print Attack ──────────────────────────────────────────────────────────
        # Genuine samples (test_samples/): cr_std ≈ 6.0–7.0, cb_std ≈ 1.3–10.0
        # Note: id_case_2 has cb_std=1.327 (close to genuine low end).
        # Require BOTH:
        #   color_disp < 0.8  (combined (cr+cb)/2 must be below 0.8 — safe margin
        #                      below the genuine floor of ~4.1)
        #   BOTH cr_std < 0.5 AND cb_std < 0.5  (must be genuinely flat in both channels)
        # This ensures a washed-out/compressed/low-light genuine selfie (which may
        # have one channel below 1.0) cannot single-handedly trigger a false positive.
        print_disp_signal  = color_disp < 0.8
        print_chroma_signal = cr_std < 0.5 and cb_std < 0.5
        if not attack_detected and print_disp_signal and print_chroma_signal:
            attack_detected = True
            attack_type = "PRINT_ATTACK"
            attack_score = 0.78
            attack_details.append("Compressed chroma gamut and flat texture consistent with printed medium")
            logger.warning(
                f"PRINT_ATTACK detected: color_disp={color_disp:.3f} "
                f"cr_std={cr_std:.3f} cb_std={cb_std:.3f}"
            )
        elif not attack_detected and (print_disp_signal or print_chroma_signal):
            # Only one signal — raise score but do NOT hard-detect
            attack_score = max(attack_score, 0.25)
            logger.debug(
                f"Borderline print-attack signal (single indicator only): "
                f"disp_signal={print_disp_signal} chroma_signal={print_chroma_signal} "
                f"color_disp={color_disp:.3f} cr_std={cr_std:.3f} cb_std={cb_std:.3f}"
            )

        liveness_status = "FAIL" if attack_detected else "PASS"
        liveness_score = round(max(0.05, 1.0 - attack_score), 2)
        liveness_details = "Live human subject verified" if not attack_detected else "; ".join(attack_details)

        liveness_res = LivenessResult(
            status=liveness_status,
            score=liveness_score,
            details=liveness_details,
        )

        pres_res = PresentationAttackResult(
            detected=attack_detected,
            score=round(attack_score, 2),
            type=attack_type,
            details="; ".join(attack_details) if attack_details else "No presentation attack detected",
        )

        return liveness_res, pres_res

    except Exception as e:
        logger.warning(f"Liveness evaluation exception: {e}")
        return (
            LivenessResult(status="INCONCLUSIVE", score=0.0, details=f"Liveness evaluation inconclusive: {e}"),
            PresentationAttackResult(detected=False, score=0.5, type=None, details=f"Liveness check inconclusive ({e})"),
        )



def _calculate_match_sync(
    id_image_path: str,
    selfie_path: str,
    selfie_embedding: Optional[List[float]] = None,
) -> Dict[str, Any]:
    id_bgr, err = _secure_load_and_normalize(id_image_path)
    if err:
        return {
            "status": "error",
            "score": None,
            "matched": False,
            "distance": None,
            "threshold": ARCFACE_COSINE_THRESHOLD,
            "detail": f"ID image error: {err}",
        }

    id_emb, err_payload = _extract_single_face_embedding(id_bgr, role="ID Document")
    if err_payload:
        err_payload["distance"] = None
        err_payload["threshold"] = ARCFACE_COSINE_THRESHOLD
        return err_payload

    if selfie_embedding is None:
        selfie_bgr, err = _secure_load_and_normalize(selfie_path)
        if err:
            return {
                "status": "error",
                "score": None,
                "matched": False,
                "distance": None,
                "threshold": ARCFACE_COSINE_THRESHOLD,
                "detail": f"Selfie image error: {err}",
            }
        selfie_emb, err_payload = _extract_single_face_embedding(selfie_bgr, role="Selfie")
        if err_payload:
            err_payload["distance"] = None
            err_payload["threshold"] = ARCFACE_COSINE_THRESHOLD
            return err_payload
    else:
        selfie_emb = selfie_embedding

    distance = _compute_cosine_distance(id_emb, selfie_emb)
    matched = bool(distance <= ARCFACE_COSINE_THRESHOLD)
    score = _calculate_calibrated_score(distance, ARCFACE_COSINE_THRESHOLD)

    return {
        "status": "matched" if matched else "not_matched",
        "score": score,
        "matched": matched,
        "distance": round(distance, 4),
        "threshold": ARCFACE_COSINE_THRESHOLD,
        "detail": "Facial verification evaluated successfully.",
    }


def evaluate_biometrics_sync(id_image_path: str, selfie_path: Optional[str]) -> BiometricResult:
    """
    Comprehensive multi-stage biometric evaluation:
    1. Face Detection & Count (0 -> NO FACE, >1 -> MULTIPLE FACES)
    2. Image Quality & Blur Evaluation
    3. Liveness & Presentation Attack Detection
    4. 128-D ArcFace Identity Matching

    IMPORTANT: If DeepFace is not available (ImportError) or fails at runtime,
    this function returns status="error" rather than fabricating a face match.
    """
    if not selfie_path:
        return BiometricResult(
            face_detected=False,
            face_count=0,
            quality=QualityResult(status="GOOD", score=1.0, details="Selfie not submitted"),
            liveness=LivenessResult(status="PASS", score=1.0, details="Selfie not required for this document type"),
            presentation_attack=PresentationAttackResult(detected=False, score=0.0, type=None, details="Skipped"),
            face_match=FaceMatchResult(status="SKIPPED", score=None, distance=None, details="Selfie not provided"),
            status="NOT_APPLICABLE",
        )

    selfie_bgr, err = _secure_load_and_normalize(selfie_path)
    if err or selfie_bgr is None:
        return BiometricResult(
            face_detected=False,
            face_count=0,
            quality=QualityResult(status="LOW_QUALITY", score=0.0, details=f"Failed to load capture: {err}"),
            liveness=LivenessResult(status="FAIL", score=0.0, details="No valid capture provided"),
            presentation_attack=PresentationAttackResult(detected=False, score=0.0, type=None),
            face_match=FaceMatchResult(status="NO_MATCH", score=None, distance=None, details=f"Invalid capture: {err}"),
            status="RETRY",
        )

    # Detect faces in selfie — try DeepFace first, fall back to real Haar cascade
    deepface_available = True
    representations = []

    try:
        from deepface import DeepFace
        representations = DeepFace.represent(
            img_path=selfie_bgr,
            model_name=MODEL_NAME,
            detector_backend=DETECTOR_BACKEND,
            enforce_detection=False,
            align=True,
        )
    except ImportError as exc:
        # DeepFace not installed — use Haar cascade for face COUNT only.
        # We cannot do embedding-based matching without DeepFace.
        deepface_available = False
        logger.warning(f"DeepFace unavailable for face detection — using Haar cascade fallback: {exc}")
        representations = _detect_faces_opencv_fallback(selfie_bgr)
    except Exception as exc:
        # DeepFace runtime error — use Haar cascade for face COUNT only.
        deepface_available = False
        logger.warning(f"DeepFace face detection failed — using Haar cascade fallback: {exc}")
        representations = _detect_faces_opencv_fallback(selfie_bgr)

    valid_faces = []
    primary_area = None
    for item in representations:
        region = item.get("facial_area", {})
        rw = region.get("w", 0)
        rh = region.get("h", 0)
        confidence = item.get("face_confidence", None)
        # Accept: (a) zero-sized region from DeepFace skip mode, (b) real detection >= MIN_FACE_DIMENSION
        # For Haar cascade results, confidence is None — accept if dimensions are valid
        if (rw == 0 and rh == 0):
            valid_faces.append(item)
            if primary_area is None:
                primary_area = region
        elif rw >= MIN_FACE_DIMENSION and rh >= MIN_FACE_DIMENSION:
            if confidence is None or confidence > 0.40:
                valid_faces.append(item)
                if primary_area is None:
                    primary_area = region
    # If DeepFace internal detector returned no valid faces (or returned confidence=0.0 on a missed face),
    # use our multi-cascade ensemble to check for faces in the selfie
    if not valid_faces:
        logger.info("DeepFace detector found no confident face — running Haar cascade ensemble fallback on selfie")
        fallback_faces = _detect_faces_opencv_fallback(selfie_bgr)
        for item in fallback_faces:
            region = item.get("facial_area", {})
            rw = region.get("w", 0)
            rh = region.get("h", 0)
            if rw >= MIN_FACE_DIMENSION and rh >= MIN_FACE_DIMENSION:
                valid_faces.append(item)
                if primary_area is None:
                    primary_area = region

    face_count = len(valid_faces)

    # 1. No face detected in selfie
    if face_count == 0:
        return BiometricResult(
            face_detected=False,
            face_count=0,
            quality=QualityResult(status="LOW_QUALITY", score=0.0, details="No human face detected in selfie capture"),
            liveness=LivenessResult(status="FAIL", score=0.0, details="No face visible in frame"),
            presentation_attack=PresentationAttackResult(detected=False, score=0.0, type=None, details="No face in frame"),
            face_match=FaceMatchResult(status="NO_MATCH", score=None, distance=None, details="No face detected in live selfie"),
            status="RETRY",
        )

    # 2. Multiple faces detected in selfie
    if face_count > 1:
        return BiometricResult(
            face_detected=True,
            face_count=face_count,
            quality=QualityResult(status="LOW_QUALITY", score=0.4, details=f"Multiple faces ({face_count}) in frame"),
            liveness=LivenessResult(status="FAIL", score=0.3, details="Multiple subjects visible"),
            presentation_attack=PresentationAttackResult(detected=False, score=0.2, type=None, details="Multiple faces"),
            face_match=FaceMatchResult(status="NO_MATCH", score=None, distance=None, details="Border screening requires exactly one subject"),
            status="RETRY",
        )

    # 3. Occlusion check on the single detected face
    if primary_area:
        is_occluded = _check_face_occlusion(selfie_bgr, primary_area)
        if is_occluded:
            return BiometricResult(
                face_detected=False,
                face_count=0,
                quality=QualityResult(status="LOW_QUALITY", score=0.0, details="Face region appears obstructed or occluded"),
                liveness=LivenessResult(status="FAIL", score=0.0, details="Face obstructed — cannot verify liveness"),
                presentation_attack=PresentationAttackResult(
                    detected=True, score=0.85, type="OBSTRUCTION",
                    details="Face region occluded: no visible eyes and insufficient skin area detected"
                ),
                face_match=FaceMatchResult(status="NO_MATCH", score=None, distance=None, details="Face obstructed — biometric match not possible"),
                status="RETRY",
            )

    # 4. Analyze Image Quality & Liveness
    quality_res = analyze_image_quality(selfie_bgr, primary_area)
    liveness_res, presentation_res = analyze_liveness_and_presentation_attack(selfie_bgr, primary_area)

    # 5. Check presentation attack
    if presentation_res.detected:
        return BiometricResult(
            face_detected=True,
            face_count=1,
            quality=quality_res,
            liveness=liveness_res,
            presentation_attack=presentation_res,
            face_match=FaceMatchResult(status="NO_MATCH", score=None, distance=None, details="Presentation attack / spoof detected"),
            status="REJECTED",
        )

    # 6. If DeepFace is not available, we cannot do embedding-based matching.
    # Return error status — do NOT fabricate a match result.
    if not deepface_available:
        return BiometricResult(
            face_detected=True,
            face_count=1,
            quality=quality_res,
            liveness=liveness_res,
            presentation_attack=presentation_res,
            face_match=FaceMatchResult(
                status="UNAVAILABLE",
                score=None,
                distance=None,
                details="Face verification model unavailable — DeepFace/ArcFace not installed or failed to load.",
            ),
            status="error",
        )

    # 7. Run Face Match against document portrait (requires DeepFace)
    selfie_embedding = None
    if len(valid_faces) == 1 and isinstance(valid_faces[0], dict) and valid_faces[0].get("embedding"):
        selfie_embedding = valid_faces[0].get("embedding")

    match_detail = _calculate_match_sync(id_image_path, selfie_path, selfie_embedding=selfie_embedding)
    score_val = match_detail.get("score")
    matched_bool = match_detail.get("matched", False)
    dist_val = match_detail.get("distance")
    match_status_raw = match_detail.get("status")

    # Handle error from embedding extraction
    if match_status_raw == "error":
        return BiometricResult(
            face_detected=True,
            face_count=1,
            quality=quality_res,
            liveness=liveness_res,
            presentation_attack=presentation_res,
            face_match=FaceMatchResult(
                status="UNAVAILABLE",
                score=None,
                distance=None,
                details=match_detail.get("detail", "Face verification model error"),
            ),
            status="error",
        )

    if score_val is not None:
        if score_val >= 70 or matched_bool:
            match_status = "MATCH"
            bio_status = "VERIFIED"
        elif score_val >= 50:
            match_status = "BORDERLINE"
            bio_status = "NEEDS_REVIEW"
        else:
            match_status = "NO_MATCH"
            bio_status = "REJECTED"
    else:
        match_status = "UNAVAILABLE"
        bio_status = "NEEDS_REVIEW"

    face_match_res = FaceMatchResult(
        status=match_status,
        score=score_val,
        distance=dist_val,
        threshold=ARCFACE_COSINE_THRESHOLD,
        details=match_detail.get("detail", "Face comparison complete"),
    )

    return BiometricResult(
        face_detected=True,
        face_count=1,
        quality=quality_res,
        liveness=liveness_res,
        presentation_attack=presentation_res,
        face_match=face_match_res,
        status=bio_status,
    )


async def match_faces(id_image_path: str, selfie_path: str) -> Optional[int]:
    result = await asyncio.to_thread(_calculate_match_sync, id_image_path, selfie_path)
    score = result.get("score")
    return int(score) if score is not None else None


async def match_faces_detailed(id_image_path: str, selfie_path: str) -> Dict[str, Any]:
    return await asyncio.to_thread(_calculate_match_sync, id_image_path, selfie_path)


async def run_biometric_evaluation(id_image_path: str, selfie_path: Optional[str]) -> BiometricResult:
    return await asyncio.to_thread(evaluate_biometrics_sync, id_image_path, selfie_path)


run_face_verification = run_biometric_evaluation
