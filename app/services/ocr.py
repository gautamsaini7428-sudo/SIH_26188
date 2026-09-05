"""
OCR & Document Analysis Service - SIH26188

Unified OCR pipeline integrating:
1. Image and multi-page PDF loading
2. Orientation and perspective deskewing
3. Smart contrast and bilateral denoising enhancement
4. Modular OCR Engine (EasyOCR / PaddleOCR)
5. ICAO 9303 MRZ zone detection and TD1 / TD2 / TD3 parser
6. Rule-based Document Classifier
7. Type-aware structured field extraction - REAL DATA ONLY, no fallbacks
"""

import os
import logging
from typing import Dict, Any, Optional, List

from app.config import get_settings
from app.engines import get_ocr_engine
from app.preprocessing import (
    load_image_from_bytes,
    deskew_and_orient,
    preprocess_image,
)
from app.mrz import detect_and_parse_mrz, clean_mrz_line
from app.extractors.classifier import classify_document
from app.extractors.generic import extract_generic_fields
from app.schemas import OCRLine, MRZResult, ExtractedFields

logger = logging.getLogger(__name__)

# NOTE: No fallback/mock pools defined here.
# This service returns ONLY what is actually extracted from the uploaded document.
# Callers must handle None / missing fields as "Not detected".


def process_image_ndarray(image_np, doc_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Run full OCR, preprocessing, MRZ, and extraction on a single RGB numpy image.
    Returns only information actually present in the document - never synthetic data.
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

    try:
        raw_lines = engine.recognize(pre)
    except Exception as e:
        logger.warning(f"OCR engine recognize error ({e}), returning empty lines.")
        raw_lines = []

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

    # Note: Retain visual OCR fields as extracted. Do NOT overwrite with MRZ data
    # so that document validation can cross-check visual text against MRZ check digits.
    return {
        "raw_text": raw_text,
        "lines": lines,
        "raw_lines": raw_lines,
        "fields": fields_dict,
        "mrz": mrz_result,
        "document_type": detected_doc_type,
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
    ocr_success = False

    if os.path.exists(file_path):
        try:
            with open(file_path, "rb") as f:
                file_bytes = f.read()

            filename = os.path.basename(file_path)
            images = load_image_from_bytes(file_bytes, filename=filename)

            if images:
                res = process_image_ndarray(images[0], doc_type=doc_type_upper)
                raw_text = res["raw_text"]
                ocr_lines = res["lines"]
                mrz_result = res["mrz"]
                detected_doc_type = res["document_type"]
                extracted_generic = res["fields"]
                ocr_success = True
            else:
                logger.warning(f"No images could be loaded from {file_path}")

        except Exception as e:
            logger.warning(f"OCR processing failed on {file_path}: {e}")
    else:
        logger.warning(f"File not found for OCR: {file_path}")

    # Compute average OCR confidence from recognized lines
    avg_conf = 0.0
    if ocr_lines:
        scores = [ln.confidence for ln in ocr_lines if ln.confidence > 0]
        if scores:
            avg_conf = round(sum(scores) / len(scores), 2)

    # Build type-specific field dict.
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
        id_number = extracted_generic.get("document_number") or extracted_generic.get("id_number") or extracted_generic.get("license_number")
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
        base_score = max(matched_scores) if matched_scores else (avg_conf or 0.70)

        # Bonus for structured format compliance
        bonus = 0.0
        if "date" in k or k in ("dob", "date_of_birth", "date_of_expiry", "expiry_date"):
            import re
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
        "mrz_line1": mrz_line1,
        "mrz_line2": mrz_line2,
        "mrz_result": mrz_result,
        "ocr_lines": ocr_lines,
        "raw_text": raw_text,
        "detected_document_type": detected_doc_type,
        "ocr_success": ocr_success,
    }
