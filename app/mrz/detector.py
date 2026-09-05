import re
import logging
from typing import Any, Dict, List
from .parser import clean_mrz_line, parse_mrz_string

logger = logging.getLogger(__name__)


def is_mrz_line_candidate(text: str) -> bool:
    """
    Checks if a line looks like an MRZ line.
    """
    cleaned = clean_mrz_line(text)
    if len(cleaned) < 25:
        return False

    # Must have upper case chars or digits and chevron '<'
    chevron_count = cleaned.count('<')
    if chevron_count >= 2:
        return True

    # Check standard prefixes
    if any(cleaned.startswith(p) for p in ['P<', 'I<', 'V<', 'A<', 'C<']):
        return True

    # Check if length is close to 30, 36, 44 and all valid ICAO chars
    if abs(len(cleaned) - 30) <= 2 or abs(len(cleaned) - 36) <= 2 or abs(len(cleaned) - 44) <= 2:
        if chevron_count >= 1:
            return True

    return False


def detect_and_parse_mrz(ocr_lines: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Scans list of OCR line dicts [{"text": "...", "confidence": ...}] to locate MRZ zone,
    extract raw MRZ, validate ICAO check digits, and parse fields.
    """
    raw_lines = [line.get("text", "") for line in ocr_lines]

    # Identify MRZ candidate line indices
    mrz_indices = []
    for idx, line in enumerate(raw_lines):
        if is_mrz_line_candidate(line):
            mrz_indices.append(idx)

    # Check contiguous clusters of MRZ lines
    if len(mrz_indices) >= 2:
        # Collect candidate lines
        candidate_lines = [clean_mrz_line(raw_lines[i]) for i in mrz_indices]

        # Test TD3 (Passport - 2 lines)
        for i in range(len(candidate_lines) - 1):
            pair = candidate_lines[i:i+2]
            if all(len(p) >= 38 for p in pair):
                raw_mrz = "\n".join(pair)
                detected, valid, fields = parse_mrz_string(raw_mrz)
                if detected:
                    return {
                        "detected": True,
                        "raw": raw_mrz,
                        "valid": valid,
                        "fields": fields
                    }

        # Test TD1 (ID Card - 3 lines)
        if len(candidate_lines) >= 3:
            for i in range(len(candidate_lines) - 2):
                triplet = candidate_lines[i:i+3]
                if all(26 <= len(p) <= 34 for p in triplet):
                    raw_mrz = "\n".join(triplet)
                    detected, valid, fields = parse_mrz_string(raw_mrz)
                    if detected:
                        return {
                            "detected": True,
                            "raw": raw_mrz,
                            "valid": valid,
                            "fields": fields
                        }

        # Test TD2 (Visa / ID - 2 lines)
        for i in range(len(candidate_lines) - 1):
            pair = candidate_lines[i:i+2]
            if all(32 <= len(p) <= 38 for p in pair):
                raw_mrz = "\n".join(pair)
                detected, valid, fields = parse_mrz_string(raw_mrz)
                if detected:
                    return {
                        "detected": True,
                        "raw": raw_mrz,
                        "valid": valid,
                        "fields": fields
                    }

        # Fallback to general parse
        raw_mrz = "\n".join(candidate_lines[-2:] if len(candidate_lines) == 2 else candidate_lines[-3:])
        detected, valid, fields = parse_mrz_string(raw_mrz)
        if detected:
            return {
                "detected": True,
                "raw": raw_mrz,
                "valid": valid,
                "fields": fields
            }

    # No MRZ detected
    return {
        "detected": False,
        "raw": None,
        "valid": None,
        "fields": {}
    }
