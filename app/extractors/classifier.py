import re
from typing import Any, Dict, List


def classify_document(raw_text: str, lines: List[Dict[str, Any]], mrz_result: Dict[str, Any]) -> str:
    """
    Classifies document into:
    - passport
    - id (Aadhaar, national identity, voter card, PAN)
    - license (Driving licence)
    - visa
    - invoice (Invoice, receipt, bill)
    - certificate (Degree, diploma, birth/marriage certificate)
    - unknown
    """
    text_upper = raw_text.upper()

    # 1. If MRZ is detected and valid
    if mrz_result.get("detected"):
        mrz_fields = mrz_result.get("fields", {})
        mrz_doc_type = mrz_fields.get("document_type")
        if mrz_doc_type in ["passport", "visa", "id"]:
            return mrz_doc_type

    # 2. Passport check
    passport_keywords = ["PASSPORT", "PASSEPORT", "REPUBLIC OF", "TYPE P", "COUNTRY CODE", "SURNAME", "GIVEN NAMES"]
    if "PASSPORT" in text_upper:
        return "passport"
    if sum(1 for kw in passport_keywords if kw in text_upper) >= 3 and mrz_result.get("detected"):
        return "passport"

    # 3. Driving License check
    dl_keywords = [
        "DRIVING LICENCE", "DRIVING LICENSE", "DRIVER LICENSE", "DRIVER LICENCE",
        "MOTOR VEHICLES", "DRIVING PERMIT", "LICENCE NO", "LICENSE NO", "DL NO"
    ]
    if any(re.search(r'\b' + re.escape(kw) + r'\b', text_upper) for kw in dl_keywords):
        return "license"

    # 4. Visa check
    visa_keywords = ["VISA", "ENTRY VISA", "SCHENGEN", "VALID FOR", "NUMBER OF ENTRIES", "TYPE OF VISA"]
    if "VISA" in text_upper and ("VALID FOR" in text_upper or "ENTRIES" in text_upper or "DURATION" in text_upper):
        return "visa"

    # 5. National ID / Aadhaar / PAN / Identity Cards
    id_keywords = [
        "AADHAAR", "UNIQUE IDENTIFICATION AUTHORITY OF INDIA", "GOVERNMENT OF INDIA",
        "ELECTION COMMISSION OF INDIA", "ELECTOR PHOTO IDENTITY CARD", "IDENTITY CARD",
        "NATIONAL ID", "PERMANENT ACCOUNT NUMBER", "INCOME TAX DEPARTMENT", "CITIZEN CARD",
        "RESIDENCE PERMIT", "IDENTIFICATION CARD"
    ]
    if any(kw in text_upper for kw in id_keywords):
        return "id"
    # Check for Aadhaar 12-digit number pattern
    if re.search(r'\b\d{4}\s\d{4}\s\d{4}\b', raw_text):
        return "id"

    # 6. Invoice / Receipt / Bill
    invoice_keywords = [
        "INVOICE", "TAX INVOICE", "BILL TO", "SHIP TO", "SUBTOTAL",
        "TOTAL AMOUNT", "AMOUNT DUE", "INVOICE NUMBER", "INVOICE NO",
        "DUE DATE", "PURCHASE ORDER", "GSTIN", "RECEIPT"
    ]
    invoice_matches = sum(1 for kw in invoice_keywords if kw in text_upper)
    if invoice_matches >= 2 or "TAX INVOICE" in text_upper or ("INVOICE" in text_upper and "TOTAL" in text_upper):
        return "invoice"

    # 7. Certificate
    cert_keywords = [
        "CERTIFICATE", "CERTIFIES THAT", "HEREBY CERTIFIES", "BACHELOR OF",
        "MASTER OF", "DIPLOMA IN", "COMPLETION OF", "ACADEMIC TRANSCRIPT",
        "DEGREE OF"
    ]
    if any(kw in text_upper for kw in cert_keywords):
        return "certificate"

    return "unknown"
