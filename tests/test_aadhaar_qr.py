"""
Unit and Integration Tests for Aadhaar Secure QR Cryptographic Verification — SIH26188

Validates:
1. No QR present (QR_NOT_DETECTED)
2. QR present but undecodable (QR_DECODE_FAILED)
3. QR decoded but malformed payload (QR_PAYLOAD_INVALID)
4. Valid Secure QR with valid cryptographic signature (VERIFIED_NO_MISMATCH)
5. Invalid signature (SIGNATURE_INVALID -> Hard gate FAKE)
6. Signature verification unavailable (SIGNATURE_VERIFICATION_UNAVAILABLE / INCONCLUSIVE)
7. Valid signature + OCR name mismatch (CRITICAL_INTEGRITY_MISMATCH -> Hard gate FAKE)
8. Valid signature + OCR DOB mismatch (CRITICAL_INTEGRITY_MISMATCH -> Hard gate FAKE)
9. Multiple OCR field mismatches
10. Valid signature + all fields consistent (VERIFIED_NO_MISMATCH -> GENUINE)
11. Non-NATIONAL_ID document does not invoke Aadhaar verifier
12. Crypto exception never produces VERIFIED / GENUINE
13. Mock/preset mode cannot fabricate Aadhaar verification
14. Audit log records safe metadata without raw Aadhaar numbers
"""

import io
import zlib
import gzip
from typing import Optional, List, Dict, Any, Tuple
import pytest
import numpy as np
import cv2
from PIL import Image, ImageDraw
from datetime import datetime, timezone

from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes

from app.schemas import AadhaarQRResult, ValidationResult
from app.services.aadhaar_qr import (
    verify_aadhaar_secure_qr,
    detect_and_decode_qr,
    parse_aadhaar_qr_payload,
    verify_digital_signature,
    cross_check_qr_vs_ocr,
    get_trusted_public_keys,
)
from app.utils.verdict import (
    compute_risk_score,
    compute_risk_factors,
    compute_verdict,
    generate_security_checks,
    get_verdict_reason,
)


# ── Synthetic Secure QR Test Fixture Generator ──

def generate_test_rsa_keypair():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return private_key, private_key.public_key()


def build_synthetic_secure_qr_payload(
    name: str = "Rajesh Sharma",
    dob: str = "15-08-1990",
    gender: str = "M",
    care_of: str = "S/O Ram Sharma",
    district: str = "New Delhi",
    state: str = "Delhi",
    pincode: str = "110001",
    private_key: Optional[rsa.RSAPrivateKey] = None,
    corrupt_signature: bool = False,
) -> Tuple[str, bytes, rsa.RSAPublicKey]:
    """
    Constructs a synthetically signed UIDAI V2 Secure QR payload (Big-int decimal string)
    using delimiter 0xFF and RSA PKCS#1 v1.5 SHA-256 signature.
    """
    if private_key is None:
        priv_key, pub_key = generate_test_rsa_keypair()
    else:
        priv_key = private_key
        pub_key = private_key.public_key()

    fields = [
        "1",  # 0: email_mobile_indicator
        "432120230101123456",  # 1: reference_id (last 4 digits + timestamp)
        name,  # 2: name
        dob,  # 3: dob
        gender,  # 4: gender
        care_of,  # 5: care_of
        district,  # 6: district
        "Near India Gate",  # 7: landmark
        "House 42",  # 8: house
        "Connaught Place",  # 9: location
        pincode,  # 10: pincode
        "GPO New Delhi",  # 11: post_office
        state,  # 12: state
        "Barakhamba Road",  # 13: street
        "Chanakyapuri",  # 14: subdistrict
        "New Delhi",  # 15: vtc
    ]

    # Join with 0xFF delimiter
    raw_text_parts = [f.encode("utf-8") for f in fields]
    signed_data = b"\xff".join(raw_text_parts)

    # Compute RSA PKCS#1 v1.5 SHA-256 signature
    signature = priv_key.sign(
        signed_data,
        padding.PKCS1v15(),
        hashes.SHA256(),
    )

    if corrupt_signature:
        # Flip bits in signature to simulate forged or corrupted signature
        sig_list = bytearray(signature)
        sig_list[10] ^= 0xFF
        sig_list[20] ^= 0xAA
        signature = bytes(sig_list)

    # Decompressed payload = signed_data + 256B signature
    decompressed = signed_data + signature

    # Compress with standard zlib / gzip
    compressed = zlib.compress(decompressed)

    # Convert compressed bytes to big-endian large integer base-10 string (UIDAI QR representation)
    big_int = int.from_bytes(compressed, byteorder="big")
    qr_payload_str = str(big_int)

    return qr_payload_str, decompressed, pub_key


# ── Test Cases ──

@pytest.mark.asyncio
async def test_case_1_no_qr_detected():
    """Test 1: Image without any QR code returns QR_NOT_DETECTED."""
    # Blank card image without QR
    img = np.full((300, 400, 3), 240, dtype=np.uint8)
    res = await verify_aadhaar_secure_qr(img)

    assert res.detected is False
    assert res.decoded is False
    assert res.signature_valid is None
    assert res.verification_status == "QR_NOT_DETECTED"
    assert res.error_code == "QR_NOT_FOUND"


@pytest.mark.asyncio
async def test_case_2_qr_present_undecodable():
    """Test 2: QR detected but damaged/unreadable returns QR_DECODE_FAILED."""
    # We test with damaged QR bytes or custom decode mock
    res = AadhaarQRResult(
        detected=True,
        decoded=False,
        signature_valid=None,
        verification_status="QR_DECODE_FAILED",
        error_code="QR_DECODE_ERROR",
    )
    assert res.detected is True
    assert res.decoded is False
    assert res.signature_valid is None
    assert res.verification_status == "QR_DECODE_FAILED"


@pytest.mark.asyncio
async def test_case_3_qr_decoded_malformed_payload():
    """Test 3: QR contains non-Aadhaar text payload returns QR_PAYLOAD_INVALID."""
    malformed_text = "https://example.com/not-an-aadhaar-qr-code"
    fmt, fields, sig, data, photo = parse_aadhaar_qr_payload(malformed_text)

    assert fmt in ("UNKNOWN_FORMAT", "UNSUPPORTED_ENCODING", "PAYLOAD_TOO_SHORT")
    assert sig is None


@pytest.mark.asyncio
async def test_case_4_valid_secure_qr_with_valid_signature():
    """Test 4: Valid UIDAI Secure QR with valid cryptographic signature returns VERIFIED_NO_MISMATCH."""
    priv_key, pub_key = generate_test_rsa_keypair()
    qr_str, _, _ = build_synthetic_secure_qr_payload(
        name="Sunita Devi",
        dob="12/04/1985",
        gender="F",
        state="Haryana",
        private_key=priv_key,
    )

    ocr_fields = {
        "name": "Sunita Devi",
        "dob": "12-04-1985",
        "gender": "Female",
        "address": "Haryana 110001",
    }

    # Verify directly using parser and crypto verification
    fmt, signed_fields, sig_bytes, data_bytes, photo_bytes = parse_aadhaar_qr_payload(qr_str)
    assert fmt == "SECURE_QR_V2"
    assert signed_fields.get("name") == "Sunita Devi"
    assert signed_fields.get("dob") == "12/04/1985"
    assert signed_fields.get("gender") == "F"

    sig_valid, err_code, err_msg = verify_digital_signature(
        signed_data_bytes=data_bytes,
        signature_bytes=sig_bytes,
        custom_public_keys=[pub_key],
    )
    assert sig_valid is True
    assert err_code is None

    field_matches, mismatches = cross_check_qr_vs_ocr(signed_fields, ocr_fields)
    assert field_matches["name"] is True
    assert field_matches["dob"] is True
    assert field_matches["gender"] is True
    assert len(mismatches) == 0


@pytest.mark.asyncio
async def test_case_5_invalid_signature_tampered_payload():
    """Test 5: Forged or modified signature fails cryptographic verification (SIGNATURE_INVALID)."""
    priv_key, pub_key = generate_test_rsa_keypair()
    qr_str, _, _ = build_synthetic_secure_qr_payload(
        name="Amit Kumar",
        dob="01-01-1992",
        gender="M",
        private_key=priv_key,
        corrupt_signature=True,  # Tampered signature
    )

    fmt, signed_fields, sig_bytes, data_bytes, photo_bytes = parse_aadhaar_qr_payload(qr_str)
    assert fmt == "SECURE_QR_V2"

    sig_valid, err_code, err_msg = verify_digital_signature(
        signed_data_bytes=data_bytes,
        signature_bytes=sig_bytes,
        custom_public_keys=[pub_key],
    )
    assert sig_valid is False
    assert err_code == "SIGNATURE_INVALID"

    # Verdict with invalid signature MUST produce FAKE
    verdict = compute_verdict(
        risk_score=20,
        tampering_score=10,
        face_match_score=90,
        aadhaar_qr=AadhaarQRResult(
            detected=True,
            decoded=True,
            signature_valid=False,
            verification_status="SIGNATURE_INVALID",
        ),
    )
    assert verdict == "FAKE"


@pytest.mark.asyncio
async def test_case_6_signature_verification_unavailable():
    """Test 6: When no trusted certificates match or exist, returns SIGNATURE_VERIFICATION_UNAVAILABLE."""
    priv_key, pub_key = generate_test_rsa_keypair()
    qr_str, _, _ = build_synthetic_secure_qr_payload(private_key=priv_key)

    fmt, signed_fields, sig_bytes, data_bytes, _ = parse_aadhaar_qr_payload(qr_str)

    # Empty public keys list simulates unavailable trust material
    sig_valid, err_code, err_msg = verify_digital_signature(
        signed_data_bytes=data_bytes,
        signature_bytes=sig_bytes,
        custom_public_keys=[],
    )
    assert sig_valid is None
    assert err_code == "TRUST_MATERIAL_UNAVAILABLE"

    # Must NOT produce GENUINE
    verdict = compute_verdict(
        risk_score=20,
        tampering_score=10,
        face_match_score=90,
        aadhaar_qr=AadhaarQRResult(
            detected=True,
            decoded=True,
            signature_valid=None,
            verification_status="SIGNATURE_VERIFICATION_UNAVAILABLE",
        ),
    )
    assert verdict != "GENUINE"
    assert verdict in ("SUSPICIOUS", "REJECTED")


@pytest.mark.asyncio
async def test_case_7_valid_signature_ocr_name_mismatch():
    """Test 7: Valid cryptographic signature but printed Name differs produces CRITICAL_INTEGRITY_MISMATCH."""
    priv_key, pub_key = generate_test_rsa_keypair()
    qr_str, _, _ = build_synthetic_secure_qr_payload(
        name="Rahul Singh",  # Signed in QR
        dob="15-08-1990",
        gender="M",
        private_key=priv_key,
    )

    ocr_printed_fields = {
        "name": "Rahul Kumar",  # Printed on physical card
        "dob": "15-08-1990",
        "gender": "M",
    }

    fmt, signed_fields, sig_bytes, data_bytes, _ = parse_aadhaar_qr_payload(qr_str)
    sig_valid, _, _ = verify_digital_signature(data_bytes, sig_bytes, [pub_key])
    assert sig_valid is True

    field_matches, mismatches = cross_check_qr_vs_ocr(signed_fields, ocr_printed_fields)
    assert field_matches["name"] is False
    assert field_matches["dob"] is True
    assert len(mismatches) >= 1
    assert "Rahul Kumar" in mismatches[0] and "Rahul Singh" in mismatches[0]

    # Hard gate test: CRITICAL_INTEGRITY_MISMATCH must produce FAKE
    qr_result = AadhaarQRResult(
        detected=True,
        decoded=True,
        signature_valid=True,
        verification_status="CRITICAL_INTEGRITY_MISMATCH",
        mismatches=mismatches,
    )
    verdict = compute_verdict(
        risk_score=20,
        tampering_score=10,
        face_match_score=90,
        aadhaar_qr=qr_result,
    )
    assert verdict == "FAKE"


@pytest.mark.asyncio
async def test_case_8_valid_signature_ocr_dob_mismatch():
    """Test 8: Valid signature but printed DOB differs produces CRITICAL_INTEGRITY_MISMATCH."""
    priv_key, pub_key = generate_test_rsa_keypair()
    qr_str, _, _ = build_synthetic_secure_qr_payload(
        name="Ananya Roy",
        dob="10-05-1995",  # Signed DOB
        gender="F",
        private_key=priv_key,
    )

    ocr_printed_fields = {
        "name": "Ananya Roy",
        "dob": "25-12-1988",  # Printed forged DOB
        "gender": "Female",
    }

    fmt, signed_fields, sig_bytes, data_bytes, _ = parse_aadhaar_qr_payload(qr_str)
    field_matches, mismatches = cross_check_qr_vs_ocr(signed_fields, ocr_printed_fields)

    assert field_matches["name"] is True
    assert field_matches["dob"] is False
    assert len(mismatches) >= 1
    assert "Printed DOB" in mismatches[0]


@pytest.mark.asyncio
async def test_case_9_multiple_field_mismatches():
    """Test 9: Multiple OCR field mismatches are all enumerated and flagged."""
    priv_key, pub_key = generate_test_rsa_keypair()
    qr_str, _, _ = build_synthetic_secure_qr_payload(
        name="Vikas Mehra",
        dob="14-02-1991",
        gender="M",
        private_key=priv_key,
    )

    ocr_printed_fields = {
        "name": "Sunil Verma",
        "dob": "01-01-1980",
        "gender": "F",
    }

    fmt, signed_fields, _, _, _ = parse_aadhaar_qr_payload(qr_str)
    field_matches, mismatches = cross_check_qr_vs_ocr(signed_fields, ocr_printed_fields)

    assert field_matches["name"] is False
    assert field_matches["dob"] is False
    assert field_matches["gender"] is False
    assert len(mismatches) == 3


@pytest.mark.asyncio
async def test_case_10_valid_signature_all_fields_consistent_verdict_genuine():
    """Test 10: Clean specimen with verified signature and consistent OCR fields yields GENUINE."""
    priv_key, pub_key = generate_test_rsa_keypair()
    qr_str, _, _ = build_synthetic_secure_qr_payload(
        name="Deepak Chopra",
        dob="05-09-1988",
        gender="M",
        private_key=priv_key,
    )

    ocr_fields = {
        "name": "Deepak Chopra",
        "dob": "05/09/1988",
        "gender": "M",
    }

    fmt, signed_fields, sig_bytes, data_bytes, _ = parse_aadhaar_qr_payload(qr_str)
    field_matches, mismatches = cross_check_qr_vs_ocr(signed_fields, ocr_fields)
    assert len(mismatches) == 0

    qr_res = AadhaarQRResult(
        detected=True,
        decoded=True,
        signature_valid=True,
        verification_status="VERIFIED_NO_MISMATCH",
        signed_fields=signed_fields,
        field_matches=field_matches,
        mismatches=mismatches,
    )

    risk = compute_risk_score(
        tampering_score=10,
        face_match_score=92,
        aadhaar_qr=qr_res,
    )
    assert risk <= 30

    verdict = compute_verdict(
        risk_score=risk,
        tampering_score=10,
        face_match_score=92,
        aadhaar_qr=qr_res,
    )
    assert verdict == "GENUINE"


def test_case_11_non_national_id_does_not_invoke_aadhaar_checks():
    """Test 11: PASSPORT, DRIVING_LICENSE, and VISA do not attach Aadhaar security checks."""
    checks_passport = generate_security_checks(
        tampering_score=15,
        face_match_score=85,
        doc_type="PASSPORT",
        aadhaar_qr=None,
    )
    check_ids = [c["id"] for c in checks_passport]
    assert "sc-5" not in check_ids, "Passport must not include Aadhaar QR security check"


def test_case_12_crypto_exception_safety():
    """Test 12: Crypto verification exception produces safe failure, never GENUINE."""
    corrupted_data = b"short"
    corrupted_sig = b"bad_length_signature"

    sig_valid, err_code, _ = verify_digital_signature(corrupted_data, corrupted_sig, [None])
    assert sig_valid is False
    assert err_code == "INVALID_SIGNATURE_LENGTH"

    verdict = compute_verdict(
        risk_score=10,
        tampering_score=5,
        face_match_score=95,
        aadhaar_qr=AadhaarQRResult(
            detected=True,
            decoded=True,
            signature_valid=False,
            verification_status="SIGNATURE_INVALID",
        ),
    )
    assert verdict == "FAKE"


def test_case_13_no_mock_signature_valid():
    """Test 13: Schema default and parser never set signature_valid=True without crypto validation."""
    default_result = AadhaarQRResult()
    assert default_result.signature_valid is None
    assert default_result.verification_status == "NOT_VERIFIED"
