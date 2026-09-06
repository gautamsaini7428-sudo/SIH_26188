"""Tests for MRZ parser and detector."""
import pytest

from app.mrz import (
    parse_mrz_string,
    parse_td3,
    parse_td1,
    parse_td2,
    clean_mrz_line,
    detect_and_parse_mrz,
    is_mrz_line_candidate,
    calculate_check_digit,
    verify_check_digit,
)


def test_calculate_check_digit_basic():
    # ICAO algorithm: weights 7,3,1 cycling; digits are 0-9, A-Z, < mapped to 0-9/10-35/0.
    assert calculate_check_digit("12345678") == "8"


def test_verify_check_digit_ok_and_bad():
    assert verify_check_digit("12345678", "8") is True
    assert verify_check_digit("12345678", "0") is False
    assert verify_check_digit("12345678", "X") is False


def test_clean_mrz_line_normalizes_chars():
    line = "P<INDSPECIMEN<<NAME<<<<<<<<<<<<<<<<<<<<<<<<<<<<"
    cleaned = clean_mrz_line(line)
    assert "<" in cleaned
    assert cleaned == line


def test_is_mrz_line_candidate_true():
    assert is_mrz_line_candidate("P<INDSPECIMEN<<NAME<<<<<<<<<<<<<<<<<<<<<<<<<<")
    assert is_mrz_line_candidate("A12345678<IND9000000000000000000")


def test_is_mrz_line_candidate_false():
    assert not is_mrz_line_candidate("HELLO WORLD")
    assert not is_mrz_line_candidate("Receipt #12345")


def test_parse_td3_valid_passport():
    l1 = "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<<<<<"
    l1 = (l1 + "<" * 44)[:44]
    l2 = "L898902C36UTO7408122F1204159ZE184226B<<<<<10"
    assert len(l2) == 44, f"l2 length {len(l2)}"
    valid, fields = parse_td3([l1, l2])
    assert fields["document_type"] == "passport"
    assert fields["issuing_country"] == "UTO"
    assert "full_name" in fields
    assert fields["document_number"] == "L898902C3"


def test_parse_td1_id_card():
    l1 = "I<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<"
    l1 = (l1 + "<" * 30)[:30]
    l2 = "9901015F2012315UTO<<<<<<<<<<<6"
    l2 = (l2 + "<" * 30)[:30]
    l3 = "ERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<"
    l3 = (l3 + "<" * 30)[:30]
    valid, fields = parse_td1([l1, l2, l3])
    assert fields["document_type"] == "id"
    assert "issuing_country" in fields


def test_parse_mrz_string_detects_td3():
    l1 = ("P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<" + "<" * 44)[:44]
    l2 = "L898902C36UTO7408122F1204159ZE184226B<<<<<10"
    raw = "\n".join([l1, l2])
    detected, valid, fields = parse_mrz_string(raw)
    assert detected is True
    assert isinstance(fields, dict)
    assert fields.get("document_type") == "passport"


def test_parse_mrz_string_unrelated_text():
    detected, valid, fields = parse_mrz_string("THIS IS JUST NORMAL TEXT")
    assert detected is False


def test_detect_and_parse_mrz_from_lines():
    l1 = ("P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<" + "<" * 44)[:44]
    l2 = "L898902C36UTO7408122F1204159ZE184226B<<<<<10"
    ocr_lines = [
        {"text": "PASSPORT", "confidence": 0.99},
        {"text": "REPUBLIC OF UTO", "confidence": 0.95},
        {"text": l1, "confidence": 0.95},
        {"text": l2, "confidence": 0.95},
    ]
    result = detect_and_parse_mrz(ocr_lines)
    assert result["detected"] is True
    assert result["fields"]["document_type"] == "passport"


def test_detect_and_parse_mrz_no_mrz_returns_false():
    ocr_lines = [
        {"text": "INVOICE", "confidence": 0.99},
        {"text": "Total: 100.00", "confidence": 0.95},
    ]
    result = detect_and_parse_mrz(ocr_lines)
    assert result["detected"] is False
    assert result["fields"] == {}
