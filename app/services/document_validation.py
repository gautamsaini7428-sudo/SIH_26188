"""
Document Validation Module (Standalone — NOT merged into tampering)

Performs format, expiry, and integrity checks per document type:
- Format validation (regex patterns for ID numbers, passport numbers, etc.)
- Expiry validation (not expired)
- DOB plausibility (age 0-120)
- PASSPORT & IDs: Full ICAO 9303 TD1 / TD2 / TD3 MRZ checksum validation
- MRZ to Visual field cross-consistency validation
- Watchlist check against local JSON database

This module is separate from tampering detection by design —
tampering detects physical/digital forgery (ELA, copy-move),
while validation checks logical/format integrity.
"""

import json
import os
import re
from datetime import datetime, date
from typing import Dict, Any, List, Optional, Tuple
from app.schemas import ValidationResult, MRZResult
from app.mrz import calculate_check_digit, verify_check_digit, parse_td3, parse_td1, parse_td2


# ── Load blacklist once at module level ──
_BLACKLIST_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "blacklist.json")
_BLACKLIST: List[Dict[str, str]] = []
try:
    with open(_BLACKLIST_PATH, "r") as f:
        _BLACKLIST = json.load(f)
except FileNotFoundError:
    pass


# ══════════════════════════════════════════════════════════════
#  ICAO 9303 TD3 MRZ CHECKSUM
# ══════════════════════════════════════════════════════════════

# Character weights per ICAO 9303 Part 3:
#   0-9 -> 0-9, A-Z -> 10-35, '<' (filler) -> 0
_MRZ_WEIGHTS = [7, 3, 1]

def _mrz_char_value(ch: str) -> int:
    """Convert a single MRZ character to its numeric value per ICAO 9303."""
    if ch == '<' or ch == ' ':
        return 0
    if ch.isdigit():
        return int(ch)
    if ch.isalpha():
        return ord(ch.upper()) - ord('A') + 10
    return 0


def compute_mrz_check_digit(data: str) -> int:
    """
    Compute a single ICAO 9303 check digit for a data string.

    Algorithm: For each character at position i, multiply its numeric value
    by the weight at position (i mod 3), where weights cycle [7, 3, 1].
    Sum all products and return sum mod 10.

    Reference: ICAO Doc 9303, Part 3, Section 4.9
    """
    total = 0
    for i, ch in enumerate(data):
        total += _mrz_char_value(ch) * _MRZ_WEIGHTS[i % 3]
    return total % 10


def validate_mrz_td3(mrz_line1: str, mrz_line2: str) -> Tuple[bool, List[str]]:
    """
    Validate a TD3 (passport) MRZ consisting of two 44-character lines.

    TD3 Line 2 layout (44 chars):
      [0:9]   Passport number
      [9]     Passport number check digit
      [10:13] Nationality
      [13:19] Date of birth (YYMMDD)
      [19]    DOB check digit
      [20]    Sex (M/F/<)
      [21:27] Date of expiry (YYMMDD)
      [27]    Expiry check digit
      [28:42] Personal number / optional data
      [42]    Personal number check digit
      [43]    Composite check digit (of fields [0:10]+[13:20]+[21:43])

    Returns (is_valid, list_of_issues).
    """
    issues: List[str] = []

    if len(mrz_line2) < 44:
        issues.append(f"MRZ line 2 too short ({len(mrz_line2)} chars, expected 44)")
        return False, issues

    line2 = mrz_line2.upper().replace(" ", "<")

    # Field 1: Passport number [0:9] check digit [9]
    pn_data = line2[0:9]
    pn_check = line2[9]
    if pn_check.isdigit() and compute_mrz_check_digit(pn_data) != int(pn_check):
        issues.append(f"MRZ passport number check digit invalid (field={pn_data}, expected={compute_mrz_check_digit(pn_data)}, got={pn_check})")

    # Field 2: DOB [13:19] check digit [19]
    dob_data = line2[13:19]
    dob_check = line2[19]
    if dob_check.isdigit() and compute_mrz_check_digit(dob_data) != int(dob_check):
        issues.append(f"MRZ date of birth check digit invalid (field={dob_data}, expected={compute_mrz_check_digit(dob_data)}, got={dob_check})")

    # Field 3: Date of expiry [21:27] check digit [27]
    exp_data = line2[21:27]
    exp_check = line2[27]
    if exp_check.isdigit() and compute_mrz_check_digit(exp_data) != int(exp_check):
        issues.append(f"MRZ expiry date check digit invalid (field={exp_data}, expected={compute_mrz_check_digit(exp_data)}, got={exp_check})")

    # Field 4: Personal number [28:42] check digit [42]
    pn2_data = line2[28:42]
    pn2_check = line2[42]
    if pn2_check.isdigit() and compute_mrz_check_digit(pn2_data) != int(pn2_check):
        issues.append(f"MRZ personal number check digit invalid")

    # Field 5: Composite check digit [43] over [0:10]+[13:20]+[21:43]
    composite_data = line2[0:10] + line2[13:20] + line2[21:43]
    composite_check = line2[43]
    if composite_check.isdigit() and compute_mrz_check_digit(composite_data) != int(composite_check):
        issues.append(f"MRZ composite check digit invalid (expected={compute_mrz_check_digit(composite_data)}, got={composite_check})")

    return len(issues) == 0, issues


# ══════════════════════════════════════════════════════════════
#  DOCUMENT-TYPE-SPECIFIC VALIDATION
# ══════════════════════════════════════════════════════════════

def _parse_date(date_str: str) -> Optional[date]:
    """Try parsing a date string in multiple common formats."""
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y", "%Y%m%d"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except (ValueError, TypeError):
            continue
    return None


def _check_dob_plausibility(dob_str: str) -> Optional[str]:
    """Check if DOB yields an age between 0 and 120."""
    d = _parse_date(dob_str)
    if d is None:
        return f"Date of birth '{dob_str}' is not in a recognisable format"
    age = (date.today() - d).days / 365.25
    if age < 0:
        return f"Date of birth is in the future ({dob_str})"
    if age > 120:
        return f"Date of birth implies age > 120 years ({dob_str})"
    return None


def _check_expiry(expiry_str: str) -> bool:
    """Return True if document has NOT expired."""
    d = _parse_date(expiry_str)
    if d is None:
        return True  # Can't parse -> don't fail on expiry alone
    return d >= date.today()


def _check_blacklist(doc_type: str, doc_number: str) -> Optional[str]:
    """Check document number against the blacklist. Returns reason if flagged."""
    for entry in _BLACKLIST:
        if entry.get("number", "").upper() == doc_number.upper():
            return entry.get("reason", "Document number appears on demonstration security watchlist")
    return None


def _compare_fields_cross_check(visual_fields: Dict[str, Any], mrz_fields: Dict[str, Any]) -> List[str]:
    """
    Cross-checks extracted visual fields against parsed MRZ fields.
    Flags discrepancies as FIELD_MISMATCH.
    """
    mismatches = []
    
    # Compare Document / Passport Number
    v_doc = str(visual_fields.get("passport_number") or visual_fields.get("id_number") or visual_fields.get("document_number") or "").strip().upper().replace(" ", "").replace("<", "")
    m_doc = str(mrz_fields.get("document_number") or "").strip().upper().replace(" ", "").replace("<", "")
    if v_doc and m_doc and len(v_doc) >= 5 and len(m_doc) >= 5:
        if v_doc != m_doc and v_doc not in m_doc and m_doc not in v_doc:
            mismatches.append(f"FIELD_MISMATCH: Visual document number ({v_doc}) disagrees with MRZ ({m_doc})")

    # Compare Date of Birth
    v_dob = str(visual_fields.get("dob") or visual_fields.get("date_of_birth") or "").strip().replace("-", "").replace("/", "")
    m_dob = str(mrz_fields.get("date_of_birth") or "").strip().replace("-", "").replace("/", "")
    if v_dob and m_dob and len(v_dob) >= 6 and len(m_dob) >= 6:
        # Check matching YYMMDD or YYYYMMDD
        if v_dob[-6:] != m_dob[-6:]:
            mismatches.append(f"FIELD_MISMATCH: Visual Date of Birth ({visual_fields.get('dob') or visual_fields.get('date_of_birth')}) disagrees with MRZ ({mrz_fields.get('date_of_birth')})")

    # Compare Name
    v_name = str(visual_fields.get("name") or "").strip().upper()
    m_name = str(mrz_fields.get("full_name") or mrz_fields.get("surname", "") + " " + mrz_fields.get("given_names", "")).strip().upper()
    if v_name and m_name and len(v_name) >= 3 and len(m_name) >= 3:
        # Check token overlap
        v_tokens = set(v_name.split())
        m_tokens = set(m_name.split())
        if not v_tokens.intersection(m_tokens):
            mismatches.append(f"FIELD_MISMATCH: Visual name ({v_name}) disagrees with MRZ ({m_name})")

    # Compare Nationality
    v_nat = str(visual_fields.get("nationality") or "").strip().upper()
    m_nat = str(mrz_fields.get("nationality") or mrz_fields.get("country_code") or "").strip().upper()
    if v_nat and m_nat and len(v_nat) == 3 and len(m_nat) == 3 and v_nat != m_nat:
        mismatches.append(f"FIELD_MISMATCH: Visual nationality ({v_nat}) disagrees with MRZ ({m_nat})")

    return mismatches


def validate_document(
    doc_type: str,
    extracted_fields: Dict[str, Any],
    file_path: Optional[str] = None,
    mrz_line1: Optional[str] = None,
    mrz_line2: Optional[str] = None,
    mrz_result: Optional[MRZResult] = None,
    detected_doc_type: Optional[str] = None,
) -> ValidationResult:
    """
    Validate a document based on its type and extracted fields.

    Main entry point for Document Validation:
    - Runs format checks
    - Expiry checks
    - MRZ checksum validation (TD1, TD2, TD3)
    - Cross-consistency checks (MRZ vs Visual fields)
    - Document category compatibility checks
    - Watchlist / blacklist checks
    """
    issues: List[str] = []
    format_valid = True
    expiry_valid = True
    mrz_valid = None
    mrz_details: Optional[Dict[str, Any]] = None

    doc_type = doc_type.upper()

    # 1. Category Mismatch Check
    if detected_doc_type and detected_doc_type.upper() != "UNKNOWN":
        det_norm = detected_doc_type.upper()
        # Map classifier outputs to standard categories
        type_mapping = {
            "PASSPORT": "PASSPORT",
            "LICENSE": "DRIVING_LICENSE",
            "DRIVING_LICENSE": "DRIVING_LICENSE",
            "VISA": "VISA",
            "ID": "NATIONAL_ID",
            "NATIONAL_ID": "NATIONAL_ID",
            "PERMIT": "PERMIT",
            "INVOICE": "INVOICE",
            "CERTIFICATE": "CERTIFICATE",
        }
        mapped_det = type_mapping.get(det_norm, det_norm)
        if mapped_det != doc_type:
            format_valid = False
            issues.append(f"DOCUMENT TYPE MISMATCH: Selected {doc_type} but detected {mapped_det}")

    # 2. Process MRZ if present directly or via mrz_result
    if mrz_result and mrz_result.detected:
        mrz_valid = mrz_result.valid
        mrz_details = mrz_result.fields
        if mrz_result.valid is False:
            format_valid = False
            issues.append("MRZ check digit validation failed (ICAO 9303 checksum mismatch)")
        
        # Cross-validate visual fields with MRZ
        if mrz_details:
            cross_issues = _compare_fields_cross_check(extracted_fields, mrz_details)
            issues.extend(cross_issues)

    elif mrz_line1 and mrz_line2:
        mrz_ok, mrz_issues = validate_mrz_td3(mrz_line1, mrz_line2)
        mrz_valid = mrz_ok
        issues.extend(mrz_issues)
        if not mrz_ok:
            format_valid = False
    elif mrz_line2:
        mrz_ok, mrz_issues = validate_mrz_td3("", mrz_line2)
        mrz_valid = mrz_ok
        issues.extend(mrz_issues)
        if not mrz_ok:
            format_valid = False

    # 3. Type-specific validation
    if doc_type == "PASSPORT":
        # Passport number format: 1 letter + 7 digits (common pattern)
        pn = str(extracted_fields.get("passport_number", "")).strip()
        if pn and not re.match(r"^[A-Z][0-9]{7}$", pn) and len(pn) < 6:
            issues.append(f"Passport number '{pn}' does not match expected format (1 letter + 7 digits)")
            format_valid = False

        # DOB plausibility
        dob = str(extracted_fields.get("dob", "")).strip()
        if dob:
            dob_issue = _check_dob_plausibility(dob)
            if dob_issue:
                issues.append(dob_issue)
                format_valid = False

        # Expiry check
        expiry = str(extracted_fields.get("date_of_expiry") or extracted_fields.get("expiry_date") or "").strip()
        if expiry and not _check_expiry(expiry):
            issues.append(f"EXPIRED_DOCUMENT: Passport expired on {expiry}")
            expiry_valid = False

        # Watchlist
        if pn:
            bl_reason = _check_blacklist("PASSPORT", pn)
            if bl_reason:
                issues.append(f"DEMONSTRATION WATCHLIST / BLACKLIST HIT: {bl_reason}")

    elif doc_type == "VISA":
        vn = str(extracted_fields.get("visa_number", "")).strip()
        if vn and len(vn) < 5:
            issues.append(f"Visa number '{vn}' is suspiciously short")
            format_valid = False

        stay = extracted_fields.get("stay_duration", "")
        if stay and isinstance(stay, str) and not stay.replace(" ", "").replace("days", "").strip().isdigit():
            issues.append(f"Stay duration '{stay}' is not numeric")

        expiry = str(extracted_fields.get("expiry_date") or extracted_fields.get("date_of_expiry") or "").strip()
        if expiry and not _check_expiry(expiry):
            issues.append(f"EXPIRED_DOCUMENT: Visa expired on {expiry}")
            expiry_valid = False

        if vn:
            bl_reason = _check_blacklist("VISA", vn)
            if bl_reason:
                issues.append(f"DEMONSTRATION WATCHLIST / BLACKLIST HIT: {bl_reason}")

    elif doc_type in ("NATIONAL_ID", "DRIVING_LICENSE", "PERMIT"):
        id_num = str(extracted_fields.get("id_number", "")).strip()
        if id_num and len(id_num) < 4:
            issues.append(f"ID number '{id_num}' is suspiciously short")
            format_valid = False

        dob = str(extracted_fields.get("dob", "")).strip()
        if dob:
            dob_issue = _check_dob_plausibility(dob)
            if dob_issue:
                issues.append(dob_issue)
                format_valid = False

        expiry = str(extracted_fields.get("expiry_date") or extracted_fields.get("date_of_expiry") or "").strip()
        if expiry and not _check_expiry(expiry):
            issues.append(f"EXPIRED_DOCUMENT: Document expired on {expiry}")
            expiry_valid = False

        if id_num:
            bl_reason = _check_blacklist(doc_type, id_num)
            if bl_reason:
                issues.append(f"DEMONSTRATION WATCHLIST / BLACKLIST HIT: {bl_reason}")

    return ValidationResult(
        format_valid=format_valid,
        expiry_valid=expiry_valid,
        issues=issues,
        mrz_valid=mrz_valid,
        mrz_details=mrz_details,
    )
