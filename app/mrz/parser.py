import re
import logging
from typing import Any, Optional, Tuple, Dict, List

logger = logging.getLogger(__name__)

# ICAO 9303 check digit weights
WEIGHTS = [7, 3, 1]


def char_to_value(c: str) -> int:
    """
    Converts MRZ character to its numeric value according to ICAO 9303.
    0-9 -> 0-9
    A-Z -> 10-35
    < -> 0
    """
    c = c.upper()
    if c.isdigit():
        return int(c)
    if 'A' <= c <= 'Z':
        return ord(c) - ord('A') + 10
    return 0


def calculate_check_digit(data: str) -> str:
    """
    Calculates single-character ICAO 9303 check digit for given data string.
    """
    total = 0
    for i, char in enumerate(data):
        weight = WEIGHTS[i % 3]
        total += char_to_value(char) * weight
    return str(total % 10)


def verify_check_digit(data: str, check_digit: str) -> bool:
    """
    Verifies that the check digit matches for the given data string.
    """
    if not check_digit or not check_digit.isdigit():
        return False
    return calculate_check_digit(data) == check_digit


def format_mrz_date(date_str: str) -> Optional[str]:
    """
    Converts YYMMDD into YYYY-MM-DD format (heuristic for century based on year).
    """
    if not date_str or len(date_str) != 6 or not date_str.isdigit():
        return None

    yy = int(date_str[0:2])
    mm = date_str[2:4]
    dd = date_str[4:6]

    # Simple century heuristic (e.g., > 40 is 19YY, <= 40 is 20YY)
    current_short_year = 26  # reference current year 2026
    if yy > current_short_year + 15:
        year = f"19{yy:02d}"
    else:
        year = f"20{yy:02d}"

    return f"{year}-{mm}-{dd}"


def clean_mrz_line(line: str) -> str:
    """
    Normalizes OCR errors commonly occurring in MRZ strings.
    """
    line = line.strip().upper()
    line = re.sub(r'[\s\t\r\n]+', '', line)
    # Common character substitutions in MRZ filler
    for ch in ['«', '»', '‹', '›', '{', '}', '(', ')', '[', ']', '|']:
        line = line.replace(ch, '<')
    # Filter only allowed ICAO MRZ characters: A-Z, 0-9, <
    line = re.sub(r'[^A-Z0-9<]', '', line)
    return line


def parse_td3(lines: List[str]) -> Tuple[bool, Dict[str, Any]]:
    """
    Parses TD3 (Passport) MRZ - 2 lines of 44 characters each.
    """
    l1 = lines[0].ljust(44, '<')[:44]
    l2 = lines[1].ljust(44, '<')[:44]

    doc_type = l1[0:2].replace('<', '')
    issuing_country = l1[2:5].replace('<', '')

    # Name parsing (Surname<<Given Names)
    name_part = l1[5:44]
    name_parts = name_part.split('<<')
    surname = name_parts[0].replace('<', ' ').strip()
    given_names = name_parts[1].replace('<', ' ').strip() if len(name_parts) > 1 else ""
    full_name = f"{given_names} {surname}".strip() if given_names else surname

    # Line 2 components
    doc_number = l2[0:9].replace('<', '')
    doc_num_check = l2[9]
    nationality = l2[10:13].replace('<', '')
    birth_date_raw = l2[13:19]
    birth_check = l2[19]
    sex = l2[20].replace('<', '')
    if sex == 'M':
        sex_full = "MALE"
    elif sex == 'F':
        sex_full = "FEMALE"
    else:
        sex_full = sex if sex else None

    expiry_date_raw = l2[21:27]
    expiry_check = l2[27]
    optional_data = l2[28:42].replace('<', '')
    optional_check = l2[42] if l2[42].isdigit() else None
    composite_check = l2[43]

    # Verify check digits
    v_doc_num = verify_check_digit(l2[0:9], doc_num_check)
    v_birth = verify_check_digit(birth_date_raw, birth_check)
    v_expiry = verify_check_digit(expiry_date_raw, expiry_check)

    # Composite data: doc_number+check + birth+check + expiry+check + optional+check (if optional check present)
    comp_data = l2[0:10] + l2[13:20] + l2[21:43]
    v_composite = verify_check_digit(comp_data, composite_check)

    is_valid = v_doc_num and v_birth and v_expiry

    fields = {
        "document_type": "passport",
        "document_code": doc_type,
        "issuing_country": issuing_country,
        "full_name": full_name,
        "surname": surname,
        "given_names": given_names,
        "document_number": doc_number,
        "nationality": nationality,
        "date_of_birth": format_mrz_date(birth_date_raw),
        "raw_date_of_birth": birth_date_raw,
        "gender": sex_full,
        "expiry_date": format_mrz_date(expiry_date_raw),
        "raw_expiry_date": expiry_date_raw,
        "optional_data": optional_data if optional_data else None,
        "valid_doc_number": v_doc_num,
        "valid_birth_date": v_birth,
        "valid_expiry_date": v_expiry,
        "valid_composite": v_composite
    }

    return is_valid, fields


def parse_td1(lines: List[str]) -> Tuple[bool, Dict[str, Any]]:
    """
    Parses TD1 (ID card) MRZ - 3 lines of 30 characters each.
    """
    l1 = lines[0].ljust(30, '<')[:30]
    l2 = lines[1].ljust(30, '<')[:30]
    l3 = lines[2].ljust(30, '<')[:30]

    doc_type = l1[0:2].replace('<', '')
    issuing_country = l1[2:5].replace('<', '')
    doc_number = l1[5:14].replace('<', '')
    doc_num_check = l1[14]
    optional_data1 = l1[15:30].replace('<', '')

    birth_date_raw = l2[0:6]
    birth_check = l2[6]
    sex = l2[7].replace('<', '')
    sex_full = "MALE" if sex == 'M' else "FEMALE" if sex == 'F' else sex or None
    expiry_date_raw = l2[8:14]
    expiry_check = l2[14]
    nationality = l2[15:18].replace('<', '')
    optional_data2 = l2[18:29].replace('<', '')
    composite_check = l2[29]

    # Line 3: Name
    name_parts = l3.split('<<')
    surname = name_parts[0].replace('<', ' ').strip()
    given_names = name_parts[1].replace('<', ' ').strip() if len(name_parts) > 1 else ""
    full_name = f"{given_names} {surname}".strip() if given_names else surname

    v_doc_num = verify_check_digit(l1[5:14], doc_num_check)
    v_birth = verify_check_digit(birth_date_raw, birth_check)
    v_expiry = verify_check_digit(expiry_date_raw, expiry_check)

    comp_data = l1[5:30] + l2[0:7] + l2[8:15] + l2[18:29]
    v_composite = verify_check_digit(comp_data, composite_check)

    is_valid = v_doc_num and v_birth and v_expiry

    fields = {
        "document_type": "id",
        "document_code": doc_type,
        "issuing_country": issuing_country,
        "full_name": full_name,
        "surname": surname,
        "given_names": given_names,
        "document_number": doc_number,
        "nationality": nationality,
        "date_of_birth": format_mrz_date(birth_date_raw),
        "raw_date_of_birth": birth_date_raw,
        "gender": sex_full,
        "expiry_date": format_mrz_date(expiry_date_raw),
        "raw_expiry_date": expiry_date_raw,
        "optional_data": (optional_data1 + " " + optional_data2).strip() or None,
        "valid_doc_number": v_doc_num,
        "valid_birth_date": v_birth,
        "valid_expiry_date": v_expiry,
        "valid_composite": v_composite
    }

    return is_valid, fields


def parse_td2(lines: List[str]) -> Tuple[bool, Dict[str, Any]]:
    """
    Parses TD2 (ID card / Visa) MRZ - 2 lines of 36 characters each.
    """
    l1 = lines[0].ljust(36, '<')[:36]
    l2 = lines[1].ljust(36, '<')[:36]

    doc_type = l1[0:2].replace('<', '')
    issuing_country = l1[2:5].replace('<', '')

    name_parts = l1[5:36].split('<<')
    surname = name_parts[0].replace('<', ' ').strip()
    given_names = name_parts[1].replace('<', ' ').strip() if len(name_parts) > 1 else ""
    full_name = f"{given_names} {surname}".strip() if given_names else surname

    doc_number = l2[0:9].replace('<', '')
    doc_num_check = l2[9]
    nationality = l2[10:13].replace('<', '')
    birth_date_raw = l2[13:19]
    birth_check = l2[19]
    sex = l2[20].replace('<', '')
    sex_full = "MALE" if sex == 'M' else "FEMALE" if sex == 'F' else sex or None
    expiry_date_raw = l2[21:27]
    expiry_check = l2[27]
    optional_data = l2[28:35].replace('<', '')
    composite_check = l2[35]

    v_doc_num = verify_check_digit(l2[0:9], doc_num_check)
    v_birth = verify_check_digit(birth_date_raw, birth_check)
    v_expiry = verify_check_digit(expiry_date_raw, expiry_check)

    comp_data = l2[0:10] + l2[13:20] + l2[21:35]
    v_composite = verify_check_digit(comp_data, composite_check)

    is_valid = v_doc_num and v_birth and v_expiry

    fields = {
        "document_type": "id" if not doc_type.startswith("V") else "visa",
        "document_code": doc_type,
        "issuing_country": issuing_country,
        "full_name": full_name,
        "surname": surname,
        "given_names": given_names,
        "document_number": doc_number,
        "nationality": nationality,
        "date_of_birth": format_mrz_date(birth_date_raw),
        "raw_date_of_birth": birth_date_raw,
        "gender": sex_full,
        "expiry_date": format_mrz_date(expiry_date_raw),
        "raw_expiry_date": expiry_date_raw,
        "optional_data": optional_data if optional_data else None,
        "valid_doc_number": v_doc_num,
        "valid_birth_date": v_birth,
        "valid_expiry_date": v_expiry,
        "valid_composite": v_composite
    }

    return is_valid, fields


def parse_mrz_string(mrz_raw: str) -> Tuple[bool, Optional[bool], Dict[str, Any]]:
    """
    Parses MRZ raw text. Returns (detected: bool, valid: bool|None, fields: dict).
    """
    if not mrz_raw:
        return False, None, {}

    lines = [clean_mrz_line(l) for l in mrz_raw.split('\n') if clean_mrz_line(l)]

    if len(lines) == 2:
        # Check TD3 (44 chars) or TD2 (36 chars)
        avg_len = sum(len(l) for l in lines) / 2.0
        if avg_len >= 40:
            valid, fields = parse_td3(lines)
            return True, valid, fields
        elif avg_len >= 32:
            valid, fields = parse_td2(lines)
            return True, valid, fields
    elif len(lines) == 3:
        # TD1 (30 chars)
        valid, fields = parse_td1(lines)
        return True, valid, fields
    elif len(lines) > 3:
        # Take the last 2 or 3 lines that look like MRZ
        candidate_lines = [l for l in lines if len(l) >= 28 and '<' in l]
        if len(candidate_lines) == 2:
            avg_len = sum(len(l) for l in candidate_lines) / 2.0
            if avg_len >= 40:
                valid, fields = parse_td3(candidate_lines)
                return True, valid, fields
            else:
                valid, fields = parse_td2(candidate_lines)
                return True, valid, fields
        elif len(candidate_lines) >= 3:
            valid, fields = parse_td1(candidate_lines[-3:])
            return True, valid, fields

    return False, None, {}
