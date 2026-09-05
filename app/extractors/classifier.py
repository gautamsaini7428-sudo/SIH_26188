import re
from typing import Any, Dict, List, Optional, Tuple


DOCUMENT_KEYWORD_MAP = {
    "passport": [
        "PASSPORT", "PASSEPORT", "REPUBLIC OF", "TYPE P", "COUNTRY CODE",
        "SURNAME", "GIVEN NAMES", "NATIONALITY", "TRAVEL DOCUMENT", "P<"
    ],
    "license": [
        "DRIVING LICENCE", "DRIVING LICENSE", "DRIVER LICENSE", "DRIVER LICENCE",
        "MOTOR VEHICLES", "DRIVING PERMIT", "LICENCE NO", "LICENSE NO", "DL NO",
        "UNION OF INDIA DRIVING", "TRANSPORT DEPARTMENT", "VALID TILL", "AUTHORIZATION TO DRIVE"
    ],
    "visa": [
        "VISA", "ENTRY VISA", "SCHENGEN", "VALID FOR", "NUMBER OF ENTRIES",
        "TYPE OF VISA", "DURATION OF STAY", "BEARER", "ISSUED AT"
    ],
    "id": [
        "AADHAAR", "AADHAR", "UNIQUE IDENTIFICATION", "UIDAI", "GOVERNMENT OF INDIA",
        "BHARAT SARKAR", "ELECTION COMMISSION", "ELECTOR PHOTO", "VOTER ID", "EPIC",
        "NATIONAL ID", "PERMANENT ACCOUNT NUMBER", "INCOME TAX DEPARTMENT", "CITIZEN CARD",
        "RESIDENCE PERMIT", "IDENTIFICATION CARD", "MERA AADHAAR", "YEAR OF BIRTH",
        "YOB", "ENROLMENT NO", "VID"
    ],
    "permit": [
        "RESIDENCE PERMIT", "WORK PERMIT", "SPECIAL PERMIT", "ENTRY PERMIT",
        "BORDER PERMIT", "TEMPORARY PERMIT", "PERMIT NO"
    ],
    "invoice": [
        "INVOICE", "TAX INVOICE", "BILL TO", "SHIP TO", "SUBTOTAL",
        "TOTAL AMOUNT", "AMOUNT DUE", "INVOICE NUMBER", "INVOICE NO",
        "DUE DATE", "PURCHASE ORDER", "GSTIN", "RECEIPT"
    ],
    "certificate": [
        "CERTIFICATE", "CERTIFIES THAT", "HEREBY CERTIFIES", "BACHELOR OF",
        "MASTER OF", "DIPLOMA IN", "COMPLETION OF", "ACADEMIC TRANSCRIPT",
        "DEGREE OF", "BIRTH CERTIFICATE", "MARRIAGE CERTIFICATE"
    ],
}


def classify_document_detailed(
    raw_text: str,
    lines: Optional[List[Dict[str, Any]]] = None,
    mrz_result: Optional[Dict[str, Any]] = None,
    expected_type: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Detailed document classification returning document category, family,
    confidence score (0.0 - 1.0), and matched evidence.
    """
    text_upper = (raw_text or "").upper()
    mrz_dict = mrz_result or {}

    scores: Dict[str, float] = {k: 0.0 for k in DOCUMENT_KEYWORD_MAP}
    matched_evidence: Dict[str, List[str]] = {k: [] for k in DOCUMENT_KEYWORD_MAP}
    family = "UNKNOWN"

    # 1. MRZ signals
    if mrz_dict.get("detected"):
        mrz_fields = mrz_dict.get("fields", {}) or {}
        mrz_doc_type = str(mrz_fields.get("document_type", "")).lower()
        if mrz_doc_type in scores:
            scores[mrz_doc_type] += 3.5
            matched_evidence[mrz_doc_type].append(f"ICAO MRZ detected as {mrz_doc_type.upper()}")
        elif "passport" in mrz_doc_type:
            scores["passport"] += 3.5
            matched_evidence["passport"].append("ICAO MRZ TD3 Passport detected")

    # 2. Aadhaar Specific Patterns
    if re.search(r'\b\d{4}\s\d{4}\s\d{4}\b', raw_text or ""):
        scores["id"] += 2.5
        matched_evidence["id"].append("12-digit Aadhaar UID format detected")
        family = "AADHAAR"

    if any(k in text_upper for k in ["AADHAAR", "AADHAR", "UNIQUE IDENTIFICATION", "UIDAI", "MERA AADHAAR"]):
        scores["id"] += 2.0
        matched_evidence["id"].append("UIDAI/Aadhaar header keywords")
        family = "AADHAAR"

    # Voter ID patterns
    if re.search(r'\b[A-Z]{3}[0-9]{7}\b', raw_text or ""):
        scores["id"] += 2.0
        matched_evidence["id"].append("EPIC / Voter ID number format detected")
        if family == "UNKNOWN":
            family = "VOTER_ID"

    # PAN pattern
    if re.search(r'\b[A-Z]{5}[0-9]{4}[A-Z]\b', raw_text or ""):
        scores["id"] += 2.0
        matched_evidence["id"].append("Income Tax PAN number format detected")
        if family == "UNKNOWN":
            family = "PAN"

    # Driving License pattern
    if re.search(r'\b[A-Z]{2}[- ]?[0-9]{2}[- ]?[0-9]{4,11}\b', raw_text or ""):
        scores["license"] += 2.0
        matched_evidence["license"].append("Standard Driving License state-code number pattern")

    # Keyword matching
    for doc_type, keywords in DOCUMENT_KEYWORD_MAP.items():
        for kw in keywords:
            if kw in text_upper:
                scores[doc_type] += 1.0
                if kw not in matched_evidence[doc_type]:
                    matched_evidence[doc_type].append(kw)

    # Find winning category
    best_type = "unknown"
    best_score = 0.0

    for doc_type, score in scores.items():
        if score > best_score:
            best_score = score
            best_type = doc_type

    # Normalize confidence score
    confidence = 0.0
    if best_score > 0:
        confidence = round(min(1.0, 0.40 + (best_score * 0.15)), 2)

    # Determine specific document family
    if best_type == "id":
        if family == "UNKNOWN":
            family = "GENERIC_NATIONAL_ID"
    elif best_type == "passport":
        family = "PASSPORT"
    elif best_type == "license":
        family = "DRIVING_LICENSE"
    elif best_type == "visa":
        family = "VISA"
    elif best_type == "permit":
        family = "PERMIT"
    elif best_type == "invoice":
        family = "INVOICE"
    elif best_type == "certificate":
        family = "CERTIFICATE"

    # Map category to standard schema names
    type_map = {
        "passport": "passport",
        "id": "id",
        "license": "license",
        "visa": "visa",
        "permit": "permit",
        "invoice": "invoice",
        "certificate": "certificate",
        "unknown": "unknown",
    }

    final_type = type_map.get(best_type, "unknown")
    if best_score < 1.0:
        final_type = "unknown"
        confidence = 0.0

    return {
        "document_type": final_type,
        "document_family": family,
        "confidence": confidence,
        "score": best_score,
        "evidence": matched_evidence.get(final_type, []),
        "all_scores": scores,
    }


def classify_document(raw_text: str, lines: List[Dict[str, Any]], mrz_result: Dict[str, Any]) -> str:
    """
    Backwards-compatible classification entry point.
    Returns: passport | id | license | visa | permit | invoice | certificate | unknown
    """
    res = classify_document_detailed(raw_text, lines, mrz_result)
    return res["document_type"]

