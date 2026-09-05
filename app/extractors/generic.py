import re
from typing import Any, Dict, List, Optional


DATE_PATTERNS = [
    # YYYY-MM-DD or YYYY/MM/DD
    r'\b(19\d{2}|20\d{2})[-/.](0[1-9]|1[0-2])[-/.](0[1-9]|[12]\d|3[01])\b',
    # DD-MM-YYYY or DD/MM/YYYY
    r'\b(0[1-9]|[12]\d|3[01])[-/.](0[1-9]|1[0-2])[-/.](19\d{2}|20\d{2})\b',
    # DD Month YYYY (e.g. 15 Jan 1995 or 15 January 2020)
    r'\b(0[1-9]|[12]\d|3[01])\s+(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+(19\d{2}|20\d{2})\b',
    # Month DD, YYYY
    r'\b(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+(0[1-9]|[12]\d|3[01]),?\s+(19\d{2}|20\d{2})\b',
]

MONTH_MAP = {
    "jan": "01", "january": "01",
    "feb": "02", "february": "02",
    "mar": "03", "march": "03",
    "apr": "04", "april": "04",
    "may": "05",
    "jun": "06", "june": "06",
    "jul": "07", "july": "07",
    "aug": "08", "august": "08",
    "sep": "09", "september": "09",
    "oct": "10", "october": "10",
    "nov": "11", "november": "11",
    "dec": "12", "december": "12"
}


def normalize_date(date_text: str) -> Optional[str]:
    """
    Attempts to normalize any matched date into standard YYYY-MM-DD.
    """
    if not date_text:
        return None
    date_text = date_text.strip()

    # Check DD/MM/YYYY or DD-MM-YYYY
    m = re.match(r'^(\d{2})[-/.](\d{2})[-/.](\d{4})$', date_text)
    if m:
        d, mth, y = m.groups()
        return f"{y}-{mth}-{d}"

    # Check YYYY/MM/DD or YYYY-MM-DD
    m = re.match(r'^(\d{4})[-/.](\d{2})[-/.](\d{2})$', date_text)
    if m:
        y, mth, d = m.groups()
        return f"{y}-{mth}-{d}"

    # Check DD Mon YYYY
    m = re.match(r'^(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})$', date_text)
    if m:
        d, mon, y = m.groups()
        mon_num = MONTH_MAP.get(mon.lower(), "01")
        return f"{y}-{mon_num}-{int(d):02d}"

    return date_text


def extract_dates(text: str) -> List[str]:
    """
    Finds all date occurrences in text.
    """
    dates = []
    for pattern in DATE_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            full_str = match.group(0)
            norm = normalize_date(full_str)
            if norm and norm not in dates:
                dates.append(norm)
    return dates


def extract_gender(text: str) -> Optional[str]:
    """
    Extracts gender/sex if present.
    """
    # Look for explicit key-value like Gender: Female, Sex: M
    m = re.search(r'\b(?:GENDER|SEX)\b[\s:/-]*\b(MALE|FEMALE|TRANSGENDER|M|F)\b', text, re.IGNORECASE)
    if m:
        val = m.group(1).upper()
        if val in ("M", "MALE"):
            return "MALE"
        if val in ("F", "FEMALE"):
            return "FEMALE"
        return val

    # Standalone words if isolated
    if re.search(r'\b(?:FEMALE)\b', text, re.IGNORECASE):
        return "FEMALE"
    if re.search(r'\b(?:MALE)\b', text, re.IGNORECASE):
        return "MALE"
    return None


def extract_key_value_pairs(lines: List[Dict[str, Any]]) -> Dict[str, str]:
    """
    Extracts key: value pairs from OCR lines.
    """
    kv = {}
    for i, line_item in enumerate(lines):
        line = line_item.get("text", "")
        if ":" in line:
            parts = line.split(":", 1)
            k = parts[0].strip().lower()
            v = parts[1].strip()
            if k and v:
                kv[k] = v
        elif "-" in line and len(line.split("-")[0].split()) <= 3:
            parts = line.split("-", 1)
            k = parts[0].strip().lower()
            v = parts[1].strip()
            if k and v:
                kv[k] = v
    return kv


def extract_passport_fields(raw_text: str, lines: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Passport visual & semantic field extraction.
    """
    fields: Dict[str, Any] = {}
    
    # Passport Number
    pn_match = re.search(r'(?:PASSPORT\s*(?:NO|NUMBER|#)?|PASS\s*NO)[\s:.]*([A-Z][0-9]{7,8}|[A-Z0-9]{8,9})', raw_text, re.IGNORECASE)
    if pn_match:
        fields["document_number"] = pn_match.group(1).strip()

    # Name
    name_match = re.search(r'(?:GIVEN\s*NAME[S]?|SURNAME|NAME)[\s:.]*([A-Z\s.]{3,35})', raw_text, re.IGNORECASE)
    if name_match:
        cand = name_match.group(1).strip()
        if not any(w in cand.upper() for w in ["PASSPORT", "REPUBLIC", "INDIA", "DATE", "BIRTH", "NATIONALITY", "SEX"]):
            fields["name"] = cand

    # Nationality
    nat_match = re.search(r'(?:NATIONALITY|CITIZENSHIP)[\s:.]*([A-Z]{3,20})', raw_text, re.IGNORECASE)
    if nat_match:
        fields["nationality"] = nat_match.group(1).strip().upper()

    # Dates
    dob_match = re.search(r'(?:DATE\s*OF\s*BIRTH|DOB|D\.O\.B)[\s:.]*([0-9A-Za-z\s/.,-]+)', raw_text, re.IGNORECASE)
    if dob_match:
        extracted = extract_dates(dob_match.group(1))
        if extracted:
            fields["date_of_birth"] = extracted[0]

    exp_match = re.search(r'(?:DATE\s*OF\s*EXPIRY|EXPIRY\s*DATE|EXPIRATION)[\s:.]*([0-9A-Za-z\s/.,-]+)', raw_text, re.IGNORECASE)
    if exp_match:
        extracted = extract_dates(exp_match.group(1))
        if extracted:
            fields["expiry_date"] = extracted[0]

    gen = extract_gender(raw_text)
    if gen:
        fields["gender"] = gen

    return fields


def extract_visa_fields(raw_text: str, lines: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Visa field extraction (supports variable visa formats).
    """
    fields: Dict[str, Any] = {}

    # Visa Number
    vn_match = re.search(r'(?:VISA\s*(?:NO|NUMBER|#)|DOCUMENT\s*NO)[\s:.]*([A-Z0-9]{6,15})', raw_text, re.IGNORECASE)
    if vn_match:
        fields["document_number"] = vn_match.group(1).strip()

    # Visa Type / Category
    vt_match = re.search(r'(?:VISA\s*TYPE|CATEGORY|CLASS|TYPE)[\s:.]*([A-Z0-9/-]{1,10})', raw_text, re.IGNORECASE)
    if vt_match:
        fields["visa_type"] = vt_match.group(1).strip()

    # Name
    name_match = re.search(r'(?:NAME|APPLICANT|BEARER)[\s:.]*([A-Z\s.]{3,35})', raw_text, re.IGNORECASE)
    if name_match:
        cand = name_match.group(1).strip()
        if not any(w in cand.upper() for w in ["VISA", "REPUBLIC", "DATE", "VALID", "ENTRIES"]):
            fields["name"] = cand

    # Passport Number on Visa
    pn_match = re.search(r'(?:PASSPORT\s*NO|PPT\s*NO)[\s:.]*([A-Z0-9]{7,10})', raw_text, re.IGNORECASE)
    if pn_match:
        fields["passport_number"] = pn_match.group(1).strip()

    # Number of Entries (Multiple / Single)
    entries_match = re.search(r'(?:NO\s*OF\s*ENTRIES|ENTRIES)[\s:.]*(MULTIPLE|SINGLE|DOUBLE|[0-9]+|M|S)', raw_text, re.IGNORECASE)
    if entries_match:
        fields["entries"] = entries_match.group(1).strip().upper()

    # Expiry / Validity
    exp_match = re.search(r'(?:EXPIRY\s*DATE|VALID\s*UNTIL|EXPIRATION|DATE\s*OF\s*EXPIRY)[\s:.]*([0-9A-Za-z\s/.,-]+)', raw_text, re.IGNORECASE)
    if exp_match:
        extracted = extract_dates(exp_match.group(1))
        if extracted:
            fields["expiry_date"] = extracted[0]

    return fields


def extract_national_id_fields(raw_text: str, lines: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    National ID extraction (Aadhaar, Voter ID, Generic National ID).
    """
    fields: Dict[str, Any] = {}

    # Aadhaar 12-digit pattern: \b\d{4}\s\d{4}\s\d{4}\b
    aadhaar_match = re.search(r'\b(\d{4}\s\d{4}\s\d{4})\b', raw_text)
    if aadhaar_match:
        fields["document_number"] = aadhaar_match.group(1).strip()
        fields["id_type"] = "AADHAAR"

    # Voter ID / EPIC pattern: 3 letters + 7 digits (e.g. WBF1234567)
    epic_match = re.search(r'\b([A-Z]{3}[0-9]{7})\b', raw_text)
    if epic_match and "document_number" not in fields:
        fields["document_number"] = epic_match.group(1).strip()
        fields["id_type"] = "VOTER_ID"

    # Generic ID number fallback
    if "document_number" not in fields:
        id_match = re.search(r'(?:ID\s*NO|IDENTITY\s*NO|CARD\s*NO|UID|EPIC\s*NO)[\s:.]*([A-Z0-9/-]{6,20})', raw_text, re.IGNORECASE)
        if id_match:
            fields["document_number"] = id_match.group(1).strip()

    # Name
    name_match = re.search(r'(?:NAME|HOLDER\s*NAME|FULL\s*NAME)[\s:.]*([A-Za-z\s.]{3,35})', raw_text, re.IGNORECASE)
    if name_match:
        cand = name_match.group(1).strip()
        if not any(w in cand.upper() for w in ["GOVERNMENT", "INDIA", "MALE", "FEMALE", "YEAR", "BIRTH", "ADDRESS"]):
            fields["name"] = cand

    # DOB / Year of Birth
    dob_match = re.search(r'(?:DOB|DATE\s*OF\s*BIRTH|BIRTH\s*DATE|YEAR\s*OF\s*BIRTH|YOB)[\s:.]*([0-9A-Za-z\s/.,-]+)', raw_text, re.IGNORECASE)
    if dob_match:
        extracted = extract_dates(dob_match.group(1))
        if extracted:
            fields["date_of_birth"] = extracted[0]
        else:
            # Year only
            y_match = re.search(r'\b(19\d{2}|20\d{2})\b', dob_match.group(1))
            if y_match:
                fields["date_of_birth"] = y_match.group(1)

    gen = extract_gender(raw_text)
    if gen:
        fields["gender"] = gen

    # Address
    addr_match = re.search(r'(?:ADDRESS|ADDR)[\s:.]*([\w\s,.-]{10,120})', raw_text, re.IGNORECASE)
    if addr_match:
        fields["address"] = addr_match.group(1).strip()

    return fields


def extract_driving_license_fields(raw_text: str, lines: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Driving license extraction (supports Indian & standard driving licenses).
    """
    fields: Dict[str, Any] = {}

    # Driving License Number (e.g. DL-0420110012345 or DL04 20110012345 or RJ14 20180012345)
    dl_match = re.search(r'(?:DL\s*NO|LICENCE\s*NO|LICENSE\s*NO|D\.L\.\s*NO)[\s:.]*([A-Z]{2}[0-9\s/-]{9,18})', raw_text, re.IGNORECASE)
    if dl_match:
        fields["document_number"] = dl_match.group(1).strip()
    else:
        # State prefix license pattern
        dl_gen = re.search(r'\b([A-Z]{2}[- ]?[0-9]{2}[- ]?[0-9]{4,11})\b', raw_text)
        if dl_gen:
            fields["document_number"] = dl_gen.group(1).strip()

    # Name
    name_match = re.search(r'(?:NAME|HOLDER)[\s:.]*([A-Za-z\s.]{3,35})', raw_text, re.IGNORECASE)
    if name_match:
        cand = name_match.group(1).strip()
        if not any(w in cand.upper() for w in ["DRIVING", "LICENCE", "LICENSE", "UNION", "STATE", "TRANSPORT", "AUTHORITY"]):
            fields["name"] = cand

    # DOB
    dob_match = re.search(r'(?:DOB|DATE\s*OF\s*BIRTH|BIRTH)[\s:.]*([0-9A-Za-z\s/.,-]+)', raw_text, re.IGNORECASE)
    if dob_match:
        extracted = extract_dates(dob_match.group(1))
        if extracted:
            fields["date_of_birth"] = extracted[0]

    # Expiry / Validity
    exp_match = re.search(r'(?:VALID\s*(?:TILL|UNTIL|UPTO|THRU)|EXPIRY|EXP\s*DATE)[\s:.]*([0-9A-Za-z\s/.,-]+)', raw_text, re.IGNORECASE)
    if exp_match:
        extracted = extract_dates(exp_match.group(1))
        if extracted:
            fields["expiry_date"] = extracted[0]

    # Address
    addr_match = re.search(r'(?:ADDRESS|ADDR)[\s:.]*([\w\s,.-]{10,120})', raw_text, re.IGNORECASE)
    if addr_match:
        fields["address"] = addr_match.group(1).strip()

    return fields


def extract_permit_fields(raw_text: str, lines: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Permit extraction (Border entry permit, inner line permit, travel pass).
    """
    fields: Dict[str, Any] = {}

    # Permit Number
    pn_match = re.search(r'(?:PERMIT\s*(?:NO|NUMBER|#)|PASS\s*NO|REG\s*NO)[\s:.]*([A-Z0-9/-]{5,20})', raw_text, re.IGNORECASE)
    if pn_match:
        fields["document_number"] = pn_match.group(1).strip()

    # Permit Type
    pt_match = re.search(r'(?:PERMIT\s*TYPE|CATEGORY|PURPOSE)[\s:.]*([A-Za-z\s-]{4,30})', raw_text, re.IGNORECASE)
    if pt_match:
        fields["permit_type"] = pt_match.group(1).strip()

    # Name
    name_match = re.search(r'(?:NAME|HOLDER|PERSON)[\s:.]*([A-Za-z\s.]{3,35})', raw_text, re.IGNORECASE)
    if name_match:
        cand = name_match.group(1).strip()
        if not any(w in cand.upper() for w in ["PERMIT", "AUTHORITY", "VALID", "ENTRY", "DATE"]):
            fields["name"] = cand

    # Validity
    exp_match = re.search(r'(?:VALID\s*(?:UNTIL|UPTO|THRU)|EXPIRY|EXPIRATION)[\s:.]*([0-9A-Za-z\s/.,-]+)', raw_text, re.IGNORECASE)
    if exp_match:
        extracted = extract_dates(exp_match.group(1))
        if extracted:
            fields["expiry_date"] = extracted[0]

    return fields


def extract_generic_fields(raw_text: str, lines: List[Dict[str, Any]], doc_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Extracts structured fields using document-family specialized extractors
    with generic semantic fallback. REAL DATA ONLY - returns None for missing fields.
    """
    doc_type_upper = (doc_type or "").upper()
    
    if doc_type_upper == "PASSPORT":
        fields = extract_passport_fields(raw_text, lines)
    elif doc_type_upper == "VISA":
        fields = extract_visa_fields(raw_text, lines)
    elif doc_type_upper == "NATIONAL_ID":
        fields = extract_national_id_fields(raw_text, lines)
    elif doc_type_upper == "DRIVING_LICENSE":
        fields = extract_driving_license_fields(raw_text, lines)
    elif doc_type_upper == "PERMIT":
        fields = extract_permit_fields(raw_text, lines)
    else:
        fields = {}

    # Generic Fallbacks for any fields not found by specialized extractors
    if not fields.get("date_of_birth"):
        dob_match = re.search(r'(?:DOB|DATE OF BIRTH|BIRTH DATE|D\.O\.B)[\s:/-]*([0-9A-Za-z\s/.,-]+)', raw_text, re.IGNORECASE)
        if dob_match:
            extracted = extract_dates(dob_match.group(1))
            if extracted:
                fields["date_of_birth"] = extracted[0]

    if not fields.get("issue_date"):
        issue_match = re.search(r'(?:ISSUE DATE|DATE OF ISSUE|ISSUED ON)[\s:/-]*([0-9A-Za-z\s/.,-]+)', raw_text, re.IGNORECASE)
        if issue_match:
            extracted = extract_dates(issue_match.group(1))
            if extracted:
                fields["issue_date"] = extracted[0]

    if not fields.get("expiry_date"):
        exp_match = re.search(r'(?:EXPIRY DATE|EXP DATE|VALID UNTIL|VALID UPTO|VALID THRU|EXPIRATION DATE)[\s:/-]*([0-9A-Za-z\s/.,-]+)', raw_text, re.IGNORECASE)
        if exp_match:
            extracted = extract_dates(exp_match.group(1))
            if extracted:
                fields["expiry_date"] = extracted[0]

    if not fields.get("document_number"):
        doc_num_match = re.search(r'(?:NO|NUMBER|ID|DOC NO|REF NO|SERIAL NO|DL NO|PASSPORT NO)[\s:.]*([A-Z0-9/-]{5,20})', raw_text, re.IGNORECASE)
        if doc_num_match:
            fields["document_number"] = doc_num_match.group(1).strip()

    if not fields.get("name"):
        name_match = re.search(r'(?:NAME|HOLDER NAME|CUSTOMER NAME|FULL NAME)[\s:.]*([A-Za-z\s.]{3,35})', raw_text, re.IGNORECASE)
        if name_match:
            candidate = name_match.group(1).strip()
            if not any(k in candidate.upper() for k in ["DATE", "NUMBER", "ADDRESS", "INDIA", "REPUBLIC", "EXPIRY", "BIRTH"]):
                fields["name"] = candidate

    if not fields.get("address"):
        addr_match = re.search(r'(?:ADDRESS|ADDR)[\s:.]*([\w\s,.-]{10,120})', raw_text, re.IGNORECASE)
        if addr_match:
            fields["address"] = addr_match.group(1).strip()

    if not fields.get("gender"):
        fields["gender"] = extract_gender(raw_text)

    # Standard schema with None for missing values
    standard_fields = {
        "name": fields.get("name"),
        "document_number": fields.get("document_number"),
        "date_of_birth": fields.get("date_of_birth"),
        "gender": fields.get("gender"),
        "nationality": fields.get("nationality"),
        "issue_date": fields.get("issue_date"),
        "expiry_date": fields.get("expiry_date"),
        "address": fields.get("address"),
    }
    # Also include any specialized keys (e.g. visa_type, permit_type, entries, id_type)
    for k, v in fields.items():
        if k not in standard_fields and v is not None:
            standard_fields[k] = v

    return standard_fields
