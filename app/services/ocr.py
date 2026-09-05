"""
OCR & Document Analysis Service - SIH26188

Unified OCR pipeline integrating:
1. Image and multi-page PDF loading
2. Orientation and perspective deskewing
3. Multi-pass enhancement (Base, CLAHE, Scaled, Adaptive, Sharpened)
4. Line deduplication, spatial merging, and confidence weighting
5. ICAO 9303 MRZ zone detection and TD1 / TD2 / TD3 parser
6. Rule-based Document Classifier
7. Type-aware structured field extraction with field provenance and diagnostic status
"""

import os
import re
import logging
from typing import Dict, Any, Optional, List, Tuple

import cv2
import numpy as np

from app.config import get_settings
from app.engines import get_ocr_engine
from app.preprocessing import (
    load_image_from_bytes,
    deskew_and_orient,
    preprocess_image,
    evaluate_document_quality,
)
from app.mrz import detect_and_parse_mrz, clean_mrz_line
from app.extractors.classifier import classify_document, classify_document_detailed
from app.extractors.generic import extract_generic_fields
from app.schemas import OCRLine, MRZResult, ExtractedFields

logger = logging.getLogger(__name__)


def _generate_ocr_image_variants(image_np: np.ndarray) -> List[Tuple[str, np.ndarray]]:
    """
    Generate diverse image processing passes to maximize OCR recognition
    across degraded, low-contrast, skewed, or low-resolution documents.
    """
    variants: List[Tuple[str, np.ndarray]] = []
    
    # 1. Base pass
    variants.append(("base", image_np))

    # Convert to grayscale for thresholding passes
    if len(image_np.shape) == 3:
        gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
    else:
        gray = image_np

    # 2. CLAHE Contrast Pass (re-expanded to RGB for engine compatibility)
    try:
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        enhanced_gray = clahe.apply(gray)
        clahe_rgb = cv2.cvtColor(enhanced_gray, cv2.COLOR_GRAY2RGB)
        variants.append(("clahe", clahe_rgb))
    except Exception as e:
        logger.debug(f"CLAHE pass skipped: {e}")

    # 3. 2x Upscaled Pass (for small fonts / fine print)
    try:
        h, w = image_np.shape[:2]
        if max(h, w) < 2200:
            upscaled = cv2.resize(image_np, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)
            variants.append(("upscaled_2x", upscaled))
    except Exception as e:
        logger.debug(f"Upscale pass skipped: {e}")

    # 4. Sharpened Pass
    try:
        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]], dtype=np.float32)
        sharpened = cv2.filter2D(image_np, -1, kernel)
        variants.append(("sharpened", sharpened))
    except Exception as e:
        logger.debug(f"Sharpen pass skipped: {e}")

    # 5. Adaptive / Otsu Binarization Pass
    try:
        _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        otsu_rgb = cv2.cvtColor(otsu, cv2.COLOR_GRAY2RGB)
        variants.append(("otsu", otsu_rgb))
    except Exception as e:
        logger.debug(f"Otsu pass skipped: {e}")

    return variants


def _normalize_line_text(text: str) -> str:
    """Normalize whitespace and punctuation for fuzzy line deduplication."""
    return re.sub(r"\s+", " ", text).strip().upper()


def _merge_raw_ocr_lines(all_passes_results: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """
    Merge raw lines across multiple passes, deduplicating identical or highly
    overlapping text lines and keeping the highest confidence detection.
    """
    merged: List[Dict[str, Any]] = []
    seen_texts: Dict[str, int] = {}  # norm_text -> index in merged

    for pass_lines in all_passes_results:
        for item in pass_lines:
            text = (item.get("text") or "").strip()
            if not text:
                continue
            conf = float(item.get("confidence", 0.0))
            norm = _normalize_line_text(text)

            if norm in seen_texts:
                idx = seen_texts[norm]
                if conf > float(merged[idx].get("confidence", 0.0)):
                    merged[idx] = item
            else:
                # Also check if a very similar line already exists (substring or prefix)
                matched_existing = False
                for existing_norm, idx in list(seen_texts.items()):
                    if len(norm) > 5 and len(existing_norm) > 5:
                        if norm in existing_norm or existing_norm in norm:
                            if conf > float(merged[idx].get("confidence", 0.0)):
                                merged[idx] = item
                                seen_texts[norm] = idx
                            matched_existing = True
                            break
                if not matched_existing:
                    seen_texts[norm] = len(merged)
                    merged.append(item)

    return merged


def process_image_ndarray(image_np: np.ndarray, doc_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Run full multi-pass OCR, preprocessing, MRZ detection, and field extraction on a single RGB numpy image.
    Returns only information actually extracted from the document.
    """
    settings = get_settings()
    engine = get_ocr_engine()

    pre = image_np
    if getattr(settings, "enable_orientation_correction", True):
        try:
            pre = deskew_and_orient(pre)
        except Exception as e:
            logger.debug(f"Orientation correction skipped: {e}")

    if getattr(settings, "enable_enhancement", True):
        try:
            pre = preprocess_image(
                pre,
                min_dim=getattr(settings, "min_image_dimension", 1000),
                max_dim=getattr(settings, "max_image_dimension", 2500),
            )
        except Exception as e:
            logger.debug(f"Enhancement skipped: {e}")

    # Generate multi-pass image variants
    variants = _generate_ocr_image_variants(pre)
    all_passes_lines: List[List[Dict[str, Any]]] = []

    for variant_name, var_img in variants:
        try:
            raw_lines = engine.recognize(var_img)
            if raw_lines:
                all_passes_lines.append(raw_lines)
                # If the primary/base pass returned good rich text (>= 6 lines), we can stop early to save latency
                if variant_name == "base" and len(raw_lines) >= 8:
                    break
        except Exception as e:
            logger.debug(f"OCR engine recognition error on pass {variant_name}: {e}")

    # Merge lines from all passes
    raw_lines = _merge_raw_ocr_lines(all_passes_lines) if all_passes_lines else []

    lines = [
        OCRLine(
            text=item.get("text", ""),
            confidence=float(item.get("confidence", 0.0)),
            bbox=item.get("bbox", []),
        )
        for item in raw_lines
    ]

    raw_text = "\n".join(line.text for line in lines)
    mrz_dict = detect_and_parse_mrz(raw_lines)
    mrz_result = MRZResult(
        detected=bool(mrz_dict.get("detected", False)),
        raw=mrz_dict.get("raw"),
        valid=mrz_dict.get("valid"),
        fields=mrz_dict.get("fields", {}) or {},
    )

    detected_doc_type = classify_document(raw_text, raw_lines, mrz_dict)
    fields_dict = extract_generic_fields(raw_text, raw_lines, doc_type=doc_type)

    # Compute line confidence and field provenance
    provenance: Dict[str, Any] = {}
    for k, v in fields_dict.items():
        if not v:
            continue
        v_str = str(v).lower().strip()
        matched_line = None
        best_conf = 0.0
        best_bbox = []
        for ln in lines:
            if v_str in ln.text.lower() and ln.confidence > best_conf:
                best_conf = ln.confidence
                best_bbox = ln.bbox
                matched_line = ln.text
        provenance[k] = {
            "value": v,
            "confidence": round(best_conf or 0.85, 2),
            "source": "visual_ocr",
            "matched_line": matched_line,
            "bbox": best_bbox,
        }

    # Evaluate diagnostic OCR status
    if fields_dict and len(fields_dict) >= 3:
        ocr_status = "SUCCESS"
    elif fields_dict and len(fields_dict) > 0:
        ocr_status = "PARTIAL_FIELDS"
    elif lines:
        ocr_status = "NO_CONFIDENT_FIELDS"
    else:
        ocr_status = "NO_TEXT_DETECTED"

    return {
        "raw_text": raw_text,
        "lines": lines,
        "raw_lines": raw_lines,
        "fields": fields_dict,
        "mrz": mrz_result,
        "document_type": detected_doc_type,
        "provenance": provenance,
        "ocr_status": ocr_status,
    }


async def extract_fields(file_path: str, doc_type: str = "DRIVING_LICENSE") -> Dict[str, Any]:
    """
    Extract structured fields from an identity document using the integrated OCR engine.

    REAL DOCUMENT EXTRACTION ONLY.
    This function NEVER returns synthetic, fake, or fallback identity data.
    """
    doc_type_upper = (doc_type or "DRIVING_LICENSE").upper()

    raw_text = ""
    ocr_lines: List[OCRLine] = []
    mrz_result = MRZResult(detected=False, raw=None, valid=None, fields={})
    detected_doc_type = "unknown"
    extracted_generic: Dict[str, Any] = {}
    provenance: Dict[str, Any] = {}
    ocr_status = "NO_TEXT_DETECTED"
    ocr_success = False
    quality_metrics = None

    if os.path.exists(file_path):
        try:
            with open(file_path, "rb") as f:
                file_bytes = f.read()

            filename = os.path.basename(file_path)
            images = load_image_from_bytes(file_bytes, filename=filename)

            if images:
                # Pre-evaluate document visual quality
                quality_metrics = evaluate_document_quality(images[0])
                res = process_image_ndarray(images[0], doc_type=doc_type_upper)
                raw_text = res["raw_text"]
                ocr_lines = res["lines"]
                mrz_result = res["mrz"]
                detected_doc_type = res["document_type"]
                extracted_generic = res["fields"]
                provenance = res.get("provenance", {})
                ocr_status = res.get("ocr_status", "SUCCESS")
                ocr_success = bool(ocr_lines or extracted_generic)
            else:
                logger.warning(f"No images could be loaded from {file_path}")
                ocr_status = "IMAGE_LOAD_FAILED"

        except Exception as e:
            logger.warning(f"OCR processing failed on {file_path}: {e}")
            ocr_status = "OCR_ENGINE_ERROR"
    else:
        logger.warning(f"File not found for OCR: {file_path}")
        ocr_status = "FILE_NOT_FOUND"

    # Compute average OCR confidence from recognized lines
    avg_conf = 0.0
    if ocr_lines:
        scores = [ln.confidence for ln in ocr_lines if ln.confidence > 0]
        if scores:
            avg_conf = round(sum(scores) / len(scores), 2)

    # Build type-specific field dict
    fields: Dict[str, Any] = {}
    mrz_line1: Optional[str] = None
    mrz_line2: Optional[str] = None

    if doc_type_upper == "PASSPORT":
        name = extracted_generic.get("name")
        pn = extracted_generic.get("passport_number") or extracted_generic.get("document_number")
        nat = extracted_generic.get("nationality")
        dob = extracted_generic.get("date_of_birth") or extracted_generic.get("dob")
        exp = extracted_generic.get("expiry_date") or extracted_generic.get("date_of_expiry")
        gen = extracted_generic.get("gender")

        if mrz_result.detected and mrz_result.raw:
            raw_mrz_lines = [clean_mrz_line(l) for l in mrz_result.raw.split("\n") if clean_mrz_line(l)]
            if len(raw_mrz_lines) >= 2:
                mrz_line1 = raw_mrz_lines[0]
                mrz_line2 = raw_mrz_lines[1]
            elif len(raw_mrz_lines) == 1:
                mrz_line1 = raw_mrz_lines[0]

        if name:
            fields["name"] = name
        if pn:
            fields["passport_number"] = pn
        if nat:
            fields["nationality"] = nat
        if dob:
            fields["dob"] = dob
        if exp:
            fields["date_of_expiry"] = exp
        if gen:
            fields["gender"] = gen

    elif doc_type_upper == "VISA":
        visa_number = extracted_generic.get("document_number") or extracted_generic.get("visa_number")
        visa_type = extracted_generic.get("visa_type")
        name = extracted_generic.get("name")
        exp = extracted_generic.get("expiry_date") or extracted_generic.get("date_of_expiry")
        entries = extracted_generic.get("entries")

        if visa_number:
            fields["visa_number"] = visa_number
        if visa_type:
            fields["visa_type"] = visa_type
        if name:
            fields["name"] = name
        if exp:
            fields["expiry_date"] = exp
        if entries:
            fields["entries"] = entries

    elif doc_type_upper == "PERMIT":
        name = extracted_generic.get("name")
        id_number = extracted_generic.get("document_number") or extracted_generic.get("permit_number")
        permit_type = extracted_generic.get("permit_type")
        exp = extracted_generic.get("expiry_date")

        if name:
            fields["name"] = name
        if id_number:
            fields["id_number"] = id_number
        if permit_type:
            fields["permit_type"] = permit_type
        if exp:
            fields["expiry_date"] = exp

    else:  # NATIONAL_ID, DRIVING_LICENSE, etc.
        name = extracted_generic.get("name")
        id_number = (
            extracted_generic.get("document_number")
            or extracted_generic.get("id_number")
            or extracted_generic.get("license_number")
            or extracted_generic.get("aadhaar_number")
            or extracted_generic.get("pan_number")
            or extracted_generic.get("voter_id")
        )
        dob = extracted_generic.get("date_of_birth") or extracted_generic.get("dob")
        address = extracted_generic.get("address")
        exp = extracted_generic.get("expiry_date")

        if name:
            fields["name"] = name
        if id_number:
            fields["id_number"] = id_number
        if dob:
            fields["dob"] = dob
        if address:
            fields["address"] = address
        if exp:
            fields["expiry_date"] = exp

    # Compute dedicated field-level OCR confidence
    confidence: Dict[str, float] = {}
    mrz_fields = mrz_result.fields if (mrz_result and mrz_result.detected) else {}

    for k, v in fields.items():
        if not v:
            continue
        v_str = str(v).lower().strip()
        matched_scores = [
            ln.confidence for ln in ocr_lines
            if v_str in ln.text.lower() and ln.confidence > 0
        ]
        base_score = max(matched_scores) if matched_scores else (avg_conf or 0.75)

        # Bonus for structured format compliance
        bonus = 0.0
        if "date" in k or k in ("dob", "date_of_birth", "date_of_expiry", "expiry_date"):
            if re.search(r"\b(\d{4}[-/]\d{2}[-/]\d{2}|\d{2}[-/]\d{2}[-/]\d{4})\b", str(v)):
                bonus += 0.06
        elif "number" in k or k in ("passport_number", "id_number", "visa_number"):
            if len(str(v)) >= 6 and str(v).isalnum():
                bonus += 0.05

        # Bonus for agreement with MRZ parsed data
        if k == "passport_number" and mrz_fields.get("document_number") == v:
            bonus += 0.08
        elif k == "dob" and mrz_fields.get("date_of_birth") == v:
            bonus += 0.08
        elif k == "name" and mrz_fields.get("full_name") == v:
            bonus += 0.08

        field_conf = min(0.99, max(0.20, round(base_score + bonus, 2)))
        confidence[k] = field_conf

    return {
        "fields": fields,
        "confidence": confidence,
        "provenance": provenance,
        "mrz_line1": mrz_line1,
        "mrz_line2": mrz_line2,
        "mrz_result": mrz_result,
        "ocr_lines": ocr_lines,
        "raw_text": raw_text,
        "detected_document_type": detected_doc_type,
        "ocr_status": ocr_status,
        "ocr_success": ocr_success,
        "quality_metrics": quality_metrics,
    }
