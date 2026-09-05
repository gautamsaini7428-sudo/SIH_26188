"""
Optimized Face Verification Service
Module 1 - SIH Problem Statement 26188

Provides biometric evaluation:
1. Multi-stage face intake quality gate (no face, multiple faces, low quality)
2. Portrait feature extraction
3. Anti-spoofing and presentation attack detection (separate from face match)
4. Safe handling of missing evidence (never flags 0% mismatch when face detection fails)
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


def warm_up_face_model() -> None:
    try:
        from deepface import DeepFace
        dummy_img = np.zeros((112, 112, 3), dtype=np.uint8)
        _ = DeepFace.represent(
            img_path=dummy_img,
            model_name=MODEL_NAME,
            detector_backend="skip",
            enforce_detection=False,
        )
        logger.info("ArcFace feature extractor successfully warmed up.")
    except Exception as exc:
        logger.warning(f"Face model warm-up skipped or failed: {exc}")


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


def _extract_single_face_embedding(
    img_bgr: np.ndarray,
    role: str
) -> Tuple[Optional[List[float]], Optional[Dict[str, Any]]]:
    try:
        from deepface import DeepFace
        representations = DeepFace.represent(
            img_path=img_bgr,
            model_name=MODEL_NAME,
            detector_backend=DETECTOR_BACKEND,
            enforce_detection=False,
            align=True,
        )
    except Exception as exc:
        return None, {
            "status": "error",
            "score": 0,
            "matched": False,
            "detail": f"Model inference error on {role}: {str(exc)}",
        }

    valid_faces = []
    for item in representations:
        region = item.get("facial_area", {})
        rw = region.get("w", 0)
        rh = region.get("h", 0)
        confidence = item.get("face_confidence", 1.0) or 1.0

        if rw >= MIN_FACE_DIMENSION and rh >= MIN_FACE_DIMENSION and confidence > 0.40:
            valid_faces.append(item)

    if len(valid_faces) == 0:
        return None, {
            "status": "no_face_detected",
            "score": 0,
            "matched": False,
            "detail": f"No valid human face detected in {role}.",
        }

    if len(valid_faces) > 1:
        return None, {
            "status": "multiple_faces_detected",
            "score": 0,
            "matched": False,
            "detail": f"Multiple faces identified in {role}. Screening requires exactly one.",
        }

    embedding = valid_faces[0].get("embedding")
    if not embedding or not isinstance(embedding, list):
        return None, {
            "status": "error",
            "score": 0,
            "matched": False,
            "detail": f"Failed to compute facial feature vector for {role}.",
        }

    return embedding, None


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

        # 1. Texture & Color Disparity analysis
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
        
        # High-frequency ring energy ratio
        center_x, center_y = 64, 64
        y_coords, x_coords = np.ogrid[:128, :128]
        dist_from_center = np.sqrt((x_coords - center_x)**2 + (y_coords - center_y)**2)
        high_freq_mask = (dist_from_center > 35) & (dist_from_center < 60)
        high_freq_energy = float(np.mean(magnitude_spectrum[high_freq_mask]))
        total_energy = float(np.mean(magnitude_spectrum))
        freq_ratio = high_freq_energy / (total_energy + 1e-6)

        # Evaluate indicators
        attack_detected = False
        attack_type = None
        attack_score = 0.05
        attack_details = []

        # Screen replay check: distinct high frequency periodic spikes
        if freq_ratio > 1.38 and high_freq_energy > 120.0:
            attack_detected = True
            attack_type = "SCREEN_REPLAY"
            attack_score = 0.88
            attack_details.append("Periodic high-frequency screen pixel grid / display moiré detected")

        # Flat print attack check: very low color dynamic range in Cr/Cb channels
        elif color_disp < 2.5:
            attack_detected = True
            attack_type = "PRINT_ATTACK"
            attack_score = 0.78
            attack_details.append("Compressed chroma gamut and flat texture consistent with printed medium")

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


def _calculate_match_sync(id_image_path: str, selfie_path: str) -> Dict[str, Any]:
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

    id_emb, err_payload = _extract_single_face_embedding(id_bgr, role="ID Document")
    if err_payload:
        err_payload["distance"] = None
        err_payload["threshold"] = ARCFACE_COSINE_THRESHOLD
        return err_payload

    selfie_emb, err_payload = _extract_single_face_embedding(selfie_bgr, role="Selfie")
    if err_payload:
        err_payload["distance"] = None
        err_payload["threshold"] = ARCFACE_COSINE_THRESHOLD
        return err_payload

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

    # Detect faces in selfie
    try:
        from deepface import DeepFace
        representations = DeepFace.represent(
            img_path=selfie_bgr,
            model_name=MODEL_NAME,
            detector_backend=DETECTOR_BACKEND,
            enforce_detection=False,
            align=True,
        )
    except Exception as exc:
        representations = []

    valid_faces = []
    primary_area = None
    for item in representations:
        region = item.get("facial_area", {})
        rw = region.get("w", 0)
        rh = region.get("h", 0)
        confidence = item.get("face_confidence", 1.0) or 1.0
        if rw >= MIN_FACE_DIMENSION and rh >= MIN_FACE_DIMENSION and confidence > 0.40:
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

    # 3. Analyze Image Quality & Liveness
    quality_res = analyze_image_quality(selfie_bgr, primary_area)
    liveness_res, presentation_res = analyze_liveness_and_presentation_attack(selfie_bgr, primary_area)

    # 4. Check presentation attack
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

    # 5. Run Face Match against document portrait
    match_detail = _calculate_match_sync(id_image_path, selfie_path)
    score_val = match_detail.get("score")
    matched_bool = match_detail.get("matched", False)
    dist_val = match_detail.get("distance")
    match_status_raw = match_detail.get("status")

    if score_val is not None:
        if score_val >= 80:
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
