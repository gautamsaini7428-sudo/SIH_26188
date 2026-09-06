"""Tests for generic field extractor and document classifier."""
import pytest

from app.extractors.generic import (
    extract_generic_fields,
    extract_gender,
    extract_dates,
    normalize_date,
)
from app.extractors.classifier import classify_document


def test_extract_gender_key_value():
    assert extract_gender("Gender: MALE") == "MALE"
    assert extract_gender("Sex: F") == "FEMALE"
    assert extract_gender("Nothing here") is None


def test_extract_gender_noisy_ocr():
    assert extract_gender("DOB : 04/03/1996 Se x MALE") == "MALE"
    assert extract_gender("GENDER:F") == "FEMALE"
    assert extract_gender("M ALE") == "MALE"
    assert extract_gender("DOB: 12/05/1990  Sex: MAI E") == "MALE"


def test_extract_gender_unrelated_address():
    # An address containing "FEMALE HOSTEL ROAD" without gender context line should not falsely return FEMALE if no context line matches
    assert extract_gender("ADDRESS: 123 FEMALE HOSTEL ROAD NAGAR DIST 560001") is None


def test_normalize_date_formats():
    assert normalize_date("15/01/1995") == "1995-01-15"
    assert normalize_date("1995-01-15") == "1995-01-15"
    assert normalize_date("15 Jan 1995") == "1995-01-15"


def test_extract_dates_finds_multiple():
    text = "DOB: 15/01/1990, Expiry: 2025-12-31"
    dates = extract_dates(text)
    assert "1990-01-15" in dates
    assert "2025-12-31" in dates


def test_extract_generic_fields_dob():
    text = "Name: John Doe\nDOB: 15/01/1990\nGender: MALE"
    fields = extract_generic_fields(text, [])
    assert fields["date_of_birth"] == "1990-01-15"
    assert fields["gender"] == "MALE"


def test_extract_generic_fields_returns_null_for_missing():
    text = "This is a receipt with no relevant fields"
    fields = extract_generic_fields(text, [])
    assert fields["name"] is None
    assert fields["date_of_birth"] is None


def test_classify_invoice():
    text = "TAX INVOICE\nInvoice No: INV-001\nTotal: 500"
    doc_type = classify_document(text, [], {"detected": False, "fields": {}})
    assert doc_type == "invoice"


def test_classify_passport_by_keyword():
    text = "PASSPORT\nREPUBLIC OF UTO\nSURNAME: ERICSSON"
    doc_type = classify_document(text, [], {"detected": True, "fields": {"document_type": "passport"}})
    assert doc_type == "passport"


def test_classify_unknown():
    text = "Random text that doesn't match anything"
    doc_type = classify_document(text, [], {"detected": False, "fields": {}})
    assert doc_type == "unknown"


def test_classify_driving_license():
    text = "DRIVING LICENCE\nDL NO: AB1234\nMOTOR VEHICLES"
    doc_type = classify_document(text, [], {"detected": False, "fields": {}})
    assert doc_type == "license"


def test_classify_aadhaar_id():
    text = "GOVERNMENT OF INDIA\nAADHAAR\n1234 5678 9012"
    doc_type = classify_document(text, [], {"detected": False, "fields": {}})
    assert doc_type == "id"
