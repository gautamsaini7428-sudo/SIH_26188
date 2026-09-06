"""
Aadhaar Secure QR Cryptographic Verification Service — SIH26188

Dedicated module for National ID (Aadhaar) Secure QR Code verification:
1. Multi-scale / adaptive QR detection & decoding from document image
2. Payload decompression (gzip/zlib integer representation) & structural parsing
3. Cryptographic RSA PKCS#1 v1.5 SHA-256 digital signature verification using trusted UIDAI certificates
4. Signed demographic data extraction (Name, DOB, Gender, Address, Photo bytes)
5. Strict cross-checking between Signed QR Data and Printed OCR Data
6. Generation of strongly-typed AadhaarQRResult with honest status codes (never fake PASS)
"""

import os
import re
import io
import zlib
import gzip
import logging
import unicodedata
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
import xml.etree.ElementTree as ET

import cv2
import numpy as np
from PIL import Image

from app.schemas import AadhaarQRResult
from app.config import get_settings

logger = logging.getLogger(__name__)

# Trusted certificates directory
CERTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "certs")

# ── 1. Cryptographic Key & Certificate Loader ──

_TRUSTED_PUBLIC_KEYS = []
_CERTS_LOADED = False


def load_trusted_certificates(certs_dir: Optional[str] = None) -> List[Any]:
    """
    Load all trusted UIDAI X.509 public certificates from the certs directory.
    Returns a list of cryptography RSA public key objects.
    """
    global _TRUSTED_PUBLIC_KEYS, _CERTS_LOADED
    target_dir = certs_dir or CERTS_DIR
    keys = []

    if not os.path.isdir(target_dir):
        return keys

    try:
        from cryptography import x509
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives.serialization import load_pem_public_key, load_der_public_key

        for fname in os.listdir(target_dir):
            fpath = os.path.join(target_dir, fname)
            if not os.path.isfile(fpath):
                continue

            try:
                with open(fpath, "rb") as f:
                    cert_bytes = f.read()

                # Try PEM certificate
                if b"-----BEGIN CERTIFICATE-----" in cert_bytes:
                    cert = x509.load_pem_x509_certificate(cert_bytes, default_backend())
                    keys.append(cert.public_key())
                elif b"-----BEGIN PUBLIC KEY-----" in cert_bytes or b"-----BEGIN RSA PUBLIC KEY-----" in cert_bytes:
                    pub_key = load_pem_public_key(cert_bytes, default_backend())
                    keys.append(pub_key)
                else:
                    # Try DER certificate
                    try:
                        cert = x509.load_der_x509_certificate(cert_bytes, default_backend())
                        keys.append(cert.public_key())
                    except Exception:
                        try:
                            pub_key = load_der_public_key(cert_bytes, default_backend())
                            keys.append(pub_key)
                        except Exception:
                            pass
            except Exception as cert_err:
                logger.debug(f"Could not load certificate from {fname}: {cert_err}")

    except ImportError:
        logger.warning("cryptography package not available for certificate loading")

    _TRUSTED_PUBLIC_KEYS = keys
    _CERTS_LOADED = True
    return keys


def get_trusted_public_keys() -> List[Any]:
    global _TRUSTED_PUBLIC_KEYS, _CERTS_LOADED
    if not _CERTS_LOADED or not _TRUSTED_PUBLIC_KEYS:
        return load_trusted_certificates()
    return _TRUSTED_PUBLIC_KEYS


# ── 2. Image Preprocessing & Multi-Strategy QR Detection ──

def _preprocess_variants(img_cv: np.ndarray) -> List[np.ndarray]:
    """Generate image variants with different enhancements to maximize QR detection success."""
    variants = [img_cv]

    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY) if len(img_cv.shape) == 3 else img_cv
    variants.append(gray)

    # 1. CLAHE Contrast enhancement
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced_gray = clahe.apply(gray)
    variants.append(enhanced_gray)

    # 2. Otsu thresholding
    _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    variants.append(otsu)

    # 3. Adaptive thresholding
    adaptive = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 21, 5
    )
    variants.append(adaptive)

    # 4. Sharpened
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    sharpened = cv2.filter2D(gray, -1, kernel)
    variants.append(sharpened)

    return variants


def detect_and_decode_qr(image_source: Any) -> Tuple[bool, bool, Optional[str], Optional[np.ndarray]]:
    """
    Detect and decode QR code from image source (file path, bytes, or numpy ndarray).
    
    Returns:
        (detected, decoded, decoded_text_payload, qr_crop_image)
    """
    if isinstance(image_source, str):
        if not os.path.exists(image_source):
            return False, False, None, None
        img_cv = cv2.imread(image_source)
    elif isinstance(image_source, bytes):
        nparr = np.frombuffer(image_source, np.uint8)
        img_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    elif isinstance(image_source, np.ndarray):
        img_cv = image_source
    else:
        return False, False, None, None

    if img_cv is None or img_cv.size == 0:
        return False, False, None, None

    detector = cv2.QRCodeDetector()

    # Try standard and enhanced variants
    variants = _preprocess_variants(img_cv)

    for var in variants:
        try:
            val, points, _ = detector.detectAndDecode(var)
            if val and len(val.strip()) > 0:
                return True, True, val.strip(), None
            elif points is not None and len(points) > 0:
                # Detected bbox but failed decoding on this variant
                pass
        except Exception as e:
            logger.debug(f"OpenCV QR detect step error: {e}")

    # Check if QR detector detected corners on any variant
    qr_detected = False
    for var in variants:
        try:
            detected, points = detector.detect(var)
            if detected:
                qr_detected = True
                break
        except Exception:
            pass

    if qr_detected:
        return True, False, None, None

    return False, False, None, None


# ── 3. Secure QR Payload Decompression & Field Extraction ──

def _decompress_payload(raw_bytes: bytes) -> Optional[bytes]:
    """Decompress gzip / zlib or raw deflate payload bytes."""
    # Try gzip decompression
    try:
        return gzip.decompress(raw_bytes)
    except Exception:
        pass

    # Try standard zlib decompression
    try:
        return zlib.decompress(raw_bytes)
    except Exception:
        pass

    # Try raw deflate (wbits = -15)
    try:
        return zlib.decompress(raw_bytes, -15)
    except Exception:
        pass

    # Try zlib with header detection (wbits = 32 + 15)
    try:
        return zlib.decompress(raw_bytes, 32 + 15)
    except Exception:
        pass

    return None


def parse_aadhaar_qr_payload(decoded_str: str) -> Tuple[str, Dict[str, Any], Optional[bytes], Optional[bytes], Optional[bytes]]:
    """
    Parse QR payload.
    
    Supports:
    1. UIDAI Secure QR Code (large integer representation containing compressed data + 256B RSA signature)
    2. Direct binary / base64 payload
    3. Legacy UIDAI XML QR format (<PrintLetterBarcodeData ...>)
    
    Returns:
        (format_type, signed_fields_dict, signature_bytes, signed_data_bytes, photo_bytes)
    """
    cleaned = decoded_str.strip()

    # Case A: Legacy XML Format
    if cleaned.startswith("<?xml") or cleaned.startswith("<PrintLetterBarcodeData"):
        try:
            root = ET.fromstring(cleaned)
            fields = {
                "uid": root.get("uid", ""),
                "name": root.get("name", ""),
                "gender": root.get("gender", ""),
                "yob": root.get("yob", ""),
                "dob": root.get("dob", ""),
                "care_of": root.get("co", ""),
                "house": root.get("house", ""),
                "street": root.get("street", ""),
                "landmark": root.get("lm", ""),
                "location": root.get("loc", ""),
                "vtc": root.get("vtc", ""),
                "post_office": root.get("po", ""),
                "district": root.get("dist", ""),
                "subdistrict": root.get("subdist", ""),
                "state": root.get("state", ""),
                "pincode": root.get("pc", ""),
            }
            # Combine address
            addr_parts = [
                fields.get("care_of"),
                fields.get("house"),
                fields.get("street"),
                fields.get("landmark"),
                fields.get("location"),
                fields.get("vtc"),
                fields.get("post_office"),
                fields.get("district"),
                fields.get("state"),
                fields.get("pincode"),
            ]
            fields["address"] = ", ".join([p for p in addr_parts if p])
            # Filter empty
            fields = {k: v for k, v in fields.items() if v}
            return "LEGACY_XML", fields, None, None, None
        except Exception as xml_err:
            logger.debug(f"Failed to parse legacy XML QR: {xml_err}")

    # Case B: UIDAI Secure QR (Big Integer Base-10 String)
    raw_bytes = None
    if cleaned.isdigit():
        try:
            big_int = int(cleaned)
            byte_len = (big_int.bit_length() + 7) // 8
            raw_bytes = big_int.to_bytes(byte_len, byteorder="big")
        except Exception as int_err:
            logger.debug(f"Could not convert large integer: {int_err}")
    
    if raw_bytes is None:
        # Check if bytes are encoded as ISO-8859-1 or raw characters
        try:
            raw_bytes = cleaned.encode("latin-1")
        except Exception:
            raw_bytes = None

    if not raw_bytes:
        return "UNKNOWN_FORMAT", {}, None, None, None

    # Decompress
    decompressed = _decompress_payload(raw_bytes)
    if not decompressed:
        # Could already be uncompressed byte sequence if signature is 256 bytes
        if len(raw_bytes) > 256:
            decompressed = raw_bytes
        else:
            return "UNSUPPORTED_ENCODING", {}, None, None, None

    # UIDAI Secure QR structure:
    # 2048-bit RSA signature = last 256 bytes
    if len(decompressed) <= 256:
        return "PAYLOAD_TOO_SHORT", {}, None, None, None

    signed_data_bytes = decompressed[:-256]
    signature_bytes = decompressed[-256:]

    # Parse delimiter-separated fields (0xFF / \xff)
    parts = signed_data_bytes.split(b"\xff")
    fields: Dict[str, Any] = {}
    photo_bytes: Optional[bytes] = None

    # UIDAI V2 Standard Specification (15 to 17 fields):
    # 0: Email/Mobile Presence (int / 1-2 bytes)
    # 1: Reference ID (last 4 digits + timestamp)
    # 2: Name
    # 3: DOB (DD-MM-YYYY or YYYY-MM-DD or DD/MM/YYYY)
    # 4: Gender (M/F/T)
    # 5: Care of (S/O, D/O, W/O, C/O)
    # 6: District
    # 7: Landmark
    # 8: House
    # 9: Location
    # 10: PIN Code
    # 11: Post Office
    # 12: State
    # 13: Street
    # 14: Sub-district
    # 15: VTC
    # 16: Photo bytes (JPEG / JP2)
    
    field_names = [
        "email_mobile_indicator",
        "reference_id",
        "name",
        "dob",
        "gender",
        "care_of",
        "district",
        "landmark",
        "house",
        "location",
        "pincode",
        "post_office",
        "state",
        "street",
        "subdistrict",
        "vtc",
    ]

    for idx, part in enumerate(parts):
        if idx < len(field_names):
            name = field_names[idx]
            try:
                val = part.decode("utf-8", errors="ignore").strip()
                if val:
                    fields[name] = val
            except Exception:
                pass
        elif idx == 16 or (idx >= len(field_names) and len(part) > 100):
            # Photo bytes
            photo_bytes = part

    # Format synthesized Address
    addr_parts = [
        fields.get("care_of"),
        fields.get("house"),
        fields.get("street"),
        fields.get("landmark"),
        fields.get("location"),
        fields.get("vtc"),
        fields.get("post_office"),
        fields.get("district"),
        fields.get("state"),
        fields.get("pincode"),
    ]
    formatted_addr = ", ".join([p for p in addr_parts if p and str(p).strip()])
    if formatted_addr:
        fields["address"] = formatted_addr

    return "SECURE_QR_V2", fields, signature_bytes, signed_data_bytes, photo_bytes


# ── 4. Cryptographic Signature Verification ──

def verify_digital_signature(
    signed_data_bytes: Optional[bytes],
    signature_bytes: Optional[bytes],
    custom_public_keys: Optional[List[Any]] = None,
) -> Tuple[Optional[bool], Optional[str], Optional[str]]:
    """
    Cryptographically verify RSA PKCS#1 v1.5 SHA-256 digital signature against trusted UIDAI certificates.
    
    Returns:
        (signature_valid, error_code, message)
        
        signature_valid:
            True  -> Cryptographically validated with trusted public key
            False -> Verification attempted and failed (signature invalid / tampered)
            None  -> Verification could not be performed (no trust material / unsupported)
    """
    if signed_data_bytes is None or signature_bytes is None:
        return None, "NO_SIGNATURE_DATA", "Payload does not contain digital signature"

    if len(signature_bytes) != 256:
        return False, "INVALID_SIGNATURE_LENGTH", f"Expected 256-byte RSA signature, got {len(signature_bytes)} bytes"

    trusted_keys = custom_public_keys if custom_public_keys is not None else get_trusted_public_keys()

    if not trusted_keys:
        return None, "TRUST_MATERIAL_UNAVAILABLE", "No trusted UIDAI public certificates found in certs directory"

    try:
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography.hazmat.primitives import hashes
        from cryptography.exceptions import InvalidSignature

        # Try verification against each trusted public key
        for key in trusted_keys:
            # 1. Try SHA-256 (Standard Secure QR)
            try:
                key.verify(
                    signature_bytes,
                    signed_data_bytes,
                    padding.PKCS1v15(),
                    hashes.SHA256(),
                )
                return True, None, "Digital signature cryptographically verified against UIDAI certificate"
            except InvalidSignature:
                pass
            except Exception as e:
                logger.debug(f"Error during key verification (SHA256): {e}")

            # 2. Try SHA-1 (Legacy Secure QR format fallback)
            try:
                key.verify(
                    signature_bytes,
                    signed_data_bytes,
                    padding.PKCS1v15(),
                    hashes.SHA1(),
                )
                return True, None, "Digital signature cryptographically verified (SHA-1 legacy)"
            except InvalidSignature:
                pass
            except Exception as e:
                logger.debug(f"Error during key verification (SHA1): {e}")

        # If none of the trusted keys validated the signature
        return False, "SIGNATURE_INVALID", "Cryptographic signature verification failed against trusted public keys"

    except ImportError:
        return None, "CRYPTO_LIBRARY_UNAVAILABLE", "cryptography package is not installed"
    except Exception as general_err:
        logger.error(f"Unexpected cryptographic verification error: {general_err}")
        return False, "CRYPTO_VERIFIER_ERROR", f"Cryptographic verification error: {str(general_err)}"


# ── 5. Field Normalization & OCR Cross-Checking ──

def _normalize_text(s: Optional[str]) -> str:
    if not s:
        return ""
    # Normalize unicode
    s = unicodedata.normalize("NFKD", str(s))
    # Uppercase
    s = s.upper()
    # Strip common salutations/honorifics ONLY (never strip names)
    s = re.sub(r"\b(SHRI|SHREE|SMT|SHRIMATI|MR|MRS|MS|DR|PROF|COL|LT|GEN|CAPT)\b", " ", s)
    # Remove punctuation
    s = re.sub(r"[^\w\s]", " ", s)
    # Collapse whitespace
    s = " ".join(s.split())
    return s


def _parse_date_flexible(d_str: Optional[str]) -> Optional[str]:
    """Parse date from multiple formats and return normalized YYYY-MM-DD."""
    if not d_str:
        return None
    cleaned = re.sub(r"[^\d/-]", " ", str(d_str)).strip()
    patterns = [
        ("%d/%m/%Y", r"^\d{2}/\d{2}/\d{4}$"),
        ("%d-%m-%Y", r"^\d{2}-\d{2}-\d{4}$"),
        ("%Y-%m-%d", r"^\d{4}-\d{2}-\d{2}$"),
        ("%Y/%m/%d", r"^\d{4}/\d{2}/\d{2}$"),
        ("%d %m %Y", r"^\d{2}\s\d{2}\s\d{4}$"),
    ]
    for fmt, regex in patterns:
        try:
            dt = datetime.strptime(cleaned, fmt)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            pass

    # Extract digits
    digits = re.findall(r"\d+", cleaned)
    if len(digits) == 3:
        if len(digits[0]) == 4:  # YYYY MM DD
            return f"{digits[0]}-{digits[1].zfill(2)}-{digits[2].zfill(2)}"
        elif len(digits[2]) == 4:  # DD MM YYYY
            return f"{digits[2]}-{digits[1].zfill(2)}-{digits[0].zfill(2)}"
    return None


def cross_check_qr_vs_ocr(
    signed_fields: Dict[str, Any],
    ocr_fields: Dict[str, Any],
) -> Tuple[Dict[str, Optional[bool]], List[str]]:
    """
    Cross-check signed QR demographic fields against printed OCR data.
    
    Returns:
        (field_matches_dict, mismatches_list)
    """
    field_matches: Dict[str, Optional[bool]] = {}
    mismatches: List[str] = []

    # 1. Name Check
    signed_name = signed_fields.get("name")
    ocr_name = ocr_fields.get("name")

    if signed_name and ocr_name:
        norm_signed = _normalize_text(signed_name)
        norm_ocr = _normalize_text(ocr_name)

        if norm_signed == norm_ocr:
            field_matches["name"] = True
        else:
            signed_tokens = norm_signed.split()
            ocr_tokens = norm_ocr.split()

            # Check if all tokens match regardless of order (e.g. "Kumar Rahul" vs "Rahul Kumar")
            if sorted(signed_tokens) == sorted(ocr_tokens) and len(signed_tokens) > 0:
                field_matches["name"] = True
            else:
                field_matches["name"] = False
                mismatches.append(f"Printed Name ('{ocr_name}') does not match digitally signed QR Name ('{signed_name}')")
    elif signed_name:
        field_matches["name"] = None  # OCR could not extract name for comparison

    # 2. DOB Check
    signed_dob = signed_fields.get("dob")
    ocr_dob = ocr_fields.get("dob") or ocr_fields.get("date_of_birth")

    if signed_dob and ocr_dob:
        parsed_signed = _parse_date_flexible(signed_dob)
        parsed_ocr = _parse_date_flexible(ocr_dob)

        if parsed_signed and parsed_ocr:
            if parsed_signed == parsed_ocr:
                field_matches["dob"] = True
            else:
                field_matches["dob"] = False
                mismatches.append(f"Printed DOB ('{ocr_dob}') does not match digitally signed QR DOB ('{signed_dob}')")
        else:
            # Fallback to normalized string compare
            if _normalize_text(signed_dob) == _normalize_text(ocr_dob):
                field_matches["dob"] = True
            else:
                field_matches["dob"] = False
                mismatches.append(f"Printed DOB ('{ocr_dob}') does not match digitally signed QR DOB ('{signed_dob}')")
    elif signed_dob:
        field_matches["dob"] = None

    # 3. Gender Check
    signed_gender = signed_fields.get("gender")
    ocr_gender = ocr_fields.get("gender")

    if signed_gender and ocr_gender:
        sg = str(signed_gender).strip().upper()
        og = str(ocr_gender).strip().upper()
        # Normalize M/MALE, F/FEMALE, T/TRANSGENDER
        sg_char = sg[0] if sg else ""
        og_char = og[0] if og else ""

        if sg_char and og_char and sg_char == og_char:
            field_matches["gender"] = True
        else:
            field_matches["gender"] = False
            mismatches.append(f"Printed Gender ('{ocr_gender}') does not match digitally signed QR Gender ('{signed_gender}')")
    elif signed_gender:
        field_matches["gender"] = None

    # 4. Address Check (if OCR captured address)
    signed_addr = signed_fields.get("address")
    ocr_addr = ocr_fields.get("address")

    if signed_addr and ocr_addr:
        norm_signed_addr = _normalize_text(signed_addr)
        norm_ocr_addr = _normalize_text(ocr_addr)

        signed_tokens = set(norm_signed_addr.split())
        ocr_tokens = set(norm_ocr_addr.split())

        # Check critical tokens (state, pin code, district)
        pincode = signed_fields.get("pincode")
        state = signed_fields.get("state")
        district = signed_fields.get("district")

        crit_matches = 0
        crit_total = 0

        if pincode:
            crit_total += 1
            if pincode in ocr_addr or pincode in norm_ocr_addr:
                crit_matches += 1

        if state:
            crit_total += 1
            if _normalize_text(state) in norm_ocr_addr:
                crit_matches += 1

        if district:
            crit_total += 1
            if _normalize_text(district) in norm_ocr_addr:
                crit_matches += 1

        overlap = len(signed_tokens.intersection(ocr_tokens))
        if (crit_total > 0 and crit_matches >= 1) or (overlap >= 2):
            field_matches["address"] = True
        else:
            # Address OCR is often partial, flag if strongly conflicting
            field_matches["address"] = False
            mismatches.append("Printed address significantly differs from digitally signed QR address")
    elif signed_addr:
        field_matches["address"] = None

    return field_matches, mismatches


# ── 6. Master Aadhaar Secure QR Pipeline Orchestrator ──

async def verify_aadhaar_secure_qr(
    image_source: Any,
    ocr_fields: Optional[Dict[str, Any]] = None,
    custom_public_keys: Optional[List[Any]] = None,
) -> AadhaarQRResult:
    """
    Complete canonical pipeline for Aadhaar Secure QR verification:
    1. Detect QR code in document image
    2. Decode QR text / payload
    3. Decompress and parse UIDAI Secure QR format
    4. Validate digital signature against trusted certificates
    5. Extract signed fields and photo bytes
    6. Cross-check signed data against OCR printed data
    7. Return strongly typed AadhaarQRResult with honest status
    """
    ocr_fields = ocr_fields or {}

    try:
        # Step 1 & 2: Detection and Decoding
        detected, decoded, decoded_text, _ = detect_and_decode_qr(image_source)

        if not detected:
            return AadhaarQRResult(
                detected=False,
                decoded=False,
                signature_valid=None,
                verification_status="QR_NOT_DETECTED",
                error_code="QR_NOT_FOUND",
                message="No QR code detected in document image",
            )

        if not decoded or not decoded_text:
            return AadhaarQRResult(
                detected=True,
                decoded=False,
                signature_valid=None,
                verification_status="QR_DECODE_FAILED",
                error_code="QR_DECODE_ERROR",
                message="QR code was detected but could not be decoded (possible low resolution or damage)",
            )

        # Step 3: Payload parsing
        fmt, signed_fields, sig_bytes, data_bytes, photo_bytes = parse_aadhaar_qr_payload(decoded_text)

        if fmt in ("UNKNOWN_FORMAT", "PAYLOAD_TOO_SHORT", "UNSUPPORTED_ENCODING"):
            return AadhaarQRResult(
                detected=True,
                decoded=True,
                signature_valid=None,
                verification_status="QR_PAYLOAD_INVALID",
                error_code="QR_FORMAT_UNSUPPORTED",
                message=f"QR payload format is not a recognized UIDAI Secure QR representation ({fmt})",
            )

        # Legacy XML QR format (does not contain digital signature)
        if fmt == "LEGACY_XML":
            field_matches, mismatches = cross_check_qr_vs_ocr(signed_fields, ocr_fields)
            return AadhaarQRResult(
                detected=True,
                decoded=True,
                signature_valid=None,
                verification_status="LEGACY_FORMAT_NO_SIGNATURE",
                signed_fields=signed_fields,
                field_matches=field_matches,
                mismatches=mismatches,
                photo_available=False,
                error_code="NO_DIGITAL_SIGNATURE",
                message="Legacy UIDAI XML QR decoded. Older format does not contain cryptographic RSA signature.",
            )

        # Step 4: Digital Signature Verification
        sig_valid, err_code, err_msg = verify_digital_signature(
            signed_data_bytes=data_bytes,
            signature_bytes=sig_bytes,
            custom_public_keys=custom_public_keys,
        )

        photo_avail = photo_bytes is not None and len(photo_bytes) > 0

        # Step 5: Cross-check against OCR
        field_matches, mismatches = cross_check_qr_vs_ocr(signed_fields, ocr_fields)

        # Step 6: Determine overall verification status
        if sig_valid is True:
            if len(mismatches) == 0:
                verification_status = "VERIFIED_NO_MISMATCH"
                status_msg = "Aadhaar Secure QR cryptographically verified and fully consistent with printed OCR data."
            else:
                verification_status = "CRITICAL_INTEGRITY_MISMATCH"
                status_msg = f"Cryptographic signature is valid, but {len(mismatches)} printed field(s) do NOT match signed data."
        elif sig_valid is False:
            verification_status = "SIGNATURE_INVALID"
            status_msg = "Cryptographic signature validation failed. QR payload may have been altered or forged."
        else:
            # sig_valid is None (e.g. TRUST_MATERIAL_UNAVAILABLE)
            verification_status = "SIGNATURE_VERIFICATION_UNAVAILABLE"
            status_msg = err_msg or "Digital signature could not be verified (trust material unavailable)."

        return AadhaarQRResult(
            detected=True,
            decoded=True,
            signature_valid=sig_valid,
            verification_status=verification_status,
            signed_fields=signed_fields,
            field_matches=field_matches,
            mismatches=mismatches,
            photo_available=photo_avail,
            error_code=err_code,
            message=status_msg,
        )

    except Exception as e:
        logger.error(f"Unhandled exception in verify_aadhaar_secure_qr: {e}", exc_info=True)
        return AadhaarQRResult(
            detected=False,
            decoded=False,
            signature_valid=None,
            verification_status="INCONCLUSIVE",
            error_code="QR_LIBRARY_ERROR",
            message=f"An unexpected error occurred during QR verification: {str(e)}",
        )
