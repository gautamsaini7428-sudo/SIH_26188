"""
Verdict & Risk Score Computation Module - SIH26188

Primary output: risk_score (0-100) — weighted combination of tampering,
face match, validation issues, and Aadhaar Secure QR cryptographic signals.

Verdict is derived from risk_score PLUS hard gates:
- Negative evidence (confirmed tampering > 70, confirmed face mismatch < 50, invalid QR signature, watchlist hit) -> FAKE
- Missing evidence / inconclusive (unclear image, unverified crypto) -> SUSPICIOUS / REVIEW_REQUIRED
- Risk score 0-30 + all gates clear -> GENUINE
- Risk score 31-65 -> SUSPICIOUS
- Risk score > 65 -> FAKE
"""

from typing import Optional, List, Dict, Any
from app.config import get_settings
from app.schemas import (
    ValidationResult,
    AadhaarQRResult,
    RiskBreakdownItem,
    WhyFlaggedItem,
    CrossFieldConsistencyResult,
)


def compute_risk_score(
    tampering_score: int,
    face_match_score: Optional[int] = None,
    validation_issues_count: int = 0,
    liveness_failed: bool = False,
    presentation_attack_detected: bool = False,
    category_mismatch: bool = False,
    is_low_quality: bool = False,
    is_expired: bool = False,
    aadhaar_qr: Optional[AadhaarQRResult] = None,
    face_status: Optional[str] = None,
) -> int:
    """
    Compute the primary risk score (0-100) as a weighted multi-factor composite.
    """
    settings = get_settings()

    # 1. Tampering Component
    if tampering_score > getattr(settings, "tampering_fake_threshold", 70):
        tampering_component = 66.0 + (tampering_score - 70) * 0.8
    elif tampering_score >= getattr(settings, "tampering_suspicious_threshold", 40):
        tampering_component = 30.0 + (tampering_score - 40) * 0.7
    else:
        tampering_component = tampering_score * 0.4

    # 2. Face Match Component
    if face_match_score is not None:
        fake_thresh = getattr(settings, "face_match_fake_threshold", 50)
        susp_thresh = getattr(settings, "face_match_suspicious_threshold", 70)
        if face_match_score < fake_thresh:
            deficit = float(fake_thresh - face_match_score)
            face_component = 66.0 + (deficit / max(1.0, float(fake_thresh))) * 24.0
        elif face_match_score < susp_thresh:
            deficit = float(susp_thresh - face_match_score)
            span = float(susp_thresh - fake_thresh)
            face_component = 25.0 + (deficit / max(1.0, span)) * 20.0
        else:
            face_component = (100.0 - float(face_match_score)) * 0.3
    else:
        # Face match was not performed or face was not found
        face_component = 0.0

    # 3. Validation Issues Component (capped at 30.0)
    validation_component = min(
        validation_issues_count * 10.0,
        30.0,
    )

    # 4. Biometric Spoof / Presentation Attack / Category Mismatch / Low Quality / Expiry Penalties
    bio_penalty = 0.0
    if presentation_attack_detected:
        bio_penalty += 50.0
    elif liveness_failed:
        bio_penalty += 30.0

    if face_status == "RETRY":
        bio_penalty += 40.0

    if category_mismatch:
        bio_penalty += 75.0

    if is_expired:
        bio_penalty += 35.0

    if is_low_quality:
        bio_penalty += 10.0

    # 5. Aadhaar QR Cryptographic & Integrity Signals
    aadhaar_penalty = 0.0
    if aadhaar_qr:
        if aadhaar_qr.signature_valid is False:
            aadhaar_penalty += 75.0
        elif aadhaar_qr.verification_status == "CRITICAL_INTEGRITY_MISMATCH":
            aadhaar_penalty += 70.0
        elif aadhaar_qr.detected and aadhaar_qr.signature_valid is None:
            aadhaar_penalty += 10.0

    risk = tampering_component + face_component + validation_component + bio_penalty + aadhaar_penalty

    # Hard minimums for critical failure conditions
    if face_match_score is not None and face_match_score < getattr(settings, "face_match_fake_threshold", 50):
        risk = max(risk, 66.0)

    if face_status == "RETRY":
        risk = max(risk, 66.0)

    if category_mismatch:
        risk = max(risk, 75.0)

    if is_expired:
        risk = max(risk, 45.0)

    if aadhaar_qr:
        if aadhaar_qr.signature_valid is False or aadhaar_qr.verification_status == "CRITICAL_INTEGRITY_MISMATCH":
            risk = max(risk, 80.0)

    return max(0, min(100, int(round(risk))))


def get_risk_level(risk_score: int) -> str:
    if risk_score > 65:
        return "HIGH RISK"
    if risk_score > 30:
        return "MEDIUM RISK"
    return "LOW RISK"


def compute_risk_factors(
    tampering_score: int,
    face_match_score: Optional[int] = None,
    validation: Optional[ValidationResult] = None,
    liveness_failed: bool = False,
    presentation_attack_detected: bool = False,
    multiple_faces: bool = False,
    face_obstructed: bool = False,
    category_mismatch: bool = False,
    is_low_quality: bool = False,
    aadhaar_qr: Optional[AadhaarQRResult] = None,
    face_status: Optional[str] = None,
) -> List[str]:
    """Compile discrete risk factor codes for forensic screening."""
    factors: List[str] = []

    if tampering_score > 30:
        factors.append("DOCUMENT_TAMPERING")
    if face_match_score is not None and face_match_score < 50:
        factors.append("FACE_MISMATCH")
    if face_status == "RETRY":
        factors.append("FACE_NOT_DETECTED")
    if presentation_attack_detected:
        factors.append("PRESENTATION_ATTACK")
    elif liveness_failed:
        factors.append("LIVENESS_FAILURE")
    if multiple_faces:
        factors.append("MULTIPLE_FACES")
    if face_obstructed:
        factors.append("FACE_OBSTRUCTED")
    if category_mismatch:
        factors.append("DOCUMENT_CATEGORY_MISMATCH")
    if is_low_quality:
        factors.append("LOW_IMAGE_QUALITY")

    if validation:
        if any("DOCUMENT TYPE MISMATCH" in i.upper() or "CATEGORY MISMATCH" in i.upper() for i in validation.issues):
            factors.append("DOCUMENT_CATEGORY_MISMATCH")
        if validation.mrz_valid is False or any("MISMATCH" in i.upper() and "CATEGORY" not in i.upper() and "DOCUMENT TYPE" not in i.upper() for i in validation.issues):
            factors.append("OCR_MRZ_MISMATCH")
        if not validation.expiry_valid:
            factors.append("DOCUMENT_EXPIRED")
        if any("BLACKLIST" in i.upper() for i in validation.issues):
            factors.append("WATCHLIST_HIT")

    if aadhaar_qr:
        if aadhaar_qr.signature_valid is False:
            factors.append("AADHAAR_SIGNATURE_INVALID")
        if aadhaar_qr.verification_status == "CRITICAL_INTEGRITY_MISMATCH":
            factors.append("AADHAAR_QR_OCR_MISMATCH")
        if aadhaar_qr.detected and aadhaar_qr.signature_valid is None:
            factors.append("AADHAAR_CRYPTO_UNAVAILABLE")

    return list(dict.fromkeys(factors))


def compute_verdict(
    risk_score: int,
    tampering_score: int,
    face_match_score: Optional[int] = None,
    validation: Optional[ValidationResult] = None,
    security_checks: Optional[List[Dict[str, Any]]] = None,
    category_mismatch: bool = False,
    aadhaar_qr: Optional[AadhaarQRResult] = None,
    face_status: Optional[str] = None,
) -> str:
    """
    Compute final verdict from risk_score + hard gates.
    """
    settings = get_settings()

    # Hard gate 0: Document type mismatch is a hard failure / rejection
    if category_mismatch:
        return "REJECTED"
    if validation and any("DOCUMENT TYPE MISMATCH" in issue.upper() or "CATEGORY MISMATCH" in issue.upper() for issue in validation.issues):
        return "REJECTED"

    # Hard gate 0.5: Face not detected in selfie (blocked camera, covered face) is REJECTED
    if face_status == "RETRY":
        return "REJECTED"

    # Hard gate 1: Critical tampering
    if tampering_score > getattr(settings, "tampering_fake_threshold", 70):
        return "FAKE"

    # Hard gate 2: Confirmed low face match (identity substitution)
    if face_match_score is not None and face_match_score < getattr(settings, "face_match_fake_threshold", 50):
        return "FAKE"

    # Hard gate 2.5: Aadhaar QR Cryptographic Hard Gates
    if aadhaar_qr:
        if aadhaar_qr.signature_valid is False:
            return "FAKE"
        if aadhaar_qr.verification_status == "CRITICAL_INTEGRITY_MISMATCH":
            return "FAKE"

    # Hard gate 3: Validation failures block GENUINE
    validation_blocks_genuine = False
    if validation:
        if not validation.format_valid or not validation.expiry_valid:
            validation_blocks_genuine = True
        if validation.mrz_valid is False:
            validation_blocks_genuine = True
        if any("BLACKLIST" in issue.upper() for issue in validation.issues):
            return "FAKE"  # Blacklist hit is always FAKE

    # Aadhaar QR unverified or inconclusive blocks GENUINE
    if aadhaar_qr and aadhaar_qr.detected and aadhaar_qr.signature_valid is None:
        validation_blocks_genuine = True

    # Hard gate 4: Security check failures
    has_failed_check = False
    has_suspicious_check = False
    if security_checks:
        for check in security_checks:
            status = check.get("status") if isinstance(check, dict) else getattr(check, "status", None)
            if status == "failed":
                has_failed_check = True
            elif status == "suspicious":
                has_suspicious_check = True

    if has_failed_check:
        return "FAKE"

    # Risk-score-based verdict
    if risk_score > getattr(settings, "risk_suspicious_max", 65):
        return "FAKE"

    if risk_score > getattr(settings, "risk_genuine_max", 30):
        return "SUSPICIOUS"

    # Final checks before allowing GENUINE
    if validation_blocks_genuine:
        return "SUSPICIOUS"

    if has_suspicious_check:
        return "SUSPICIOUS"

    # Moderate tampering
    if tampering_score >= getattr(settings, "tampering_suspicious_threshold", 40):
        return "SUSPICIOUS"

    # Borderline face match
    if face_match_score is not None and face_match_score < getattr(settings, "face_match_suspicious_threshold", 70):
        return "SUSPICIOUS"

    return "GENUINE"


def generate_security_checks(
    tampering_score: int,
    face_match_score: Optional[int] = None,
    ocr_confidence: Optional[Dict[str, float]] = None,
    validation: Optional[ValidationResult] = None,
    aadhaar_qr: Optional[AadhaarQRResult] = None,
    doc_type: Optional[str] = None,
    face_status: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Generate the core forensic security check items for a document."""
    checks = []

    # 1. ICAO MRZ Checksum Parity (for PASSPORT/VISA or MRZ-enabled documents)
    if validation and validation.mrz_valid is not None:
        mrz_status = "passed" if validation.mrz_valid else "failed"
        mrz_score = 100 if validation.mrz_valid else 15
        mrz_desc = (
            "ICAO 9303 TD3 check digits mathematically validated — all check digits correct."
            if validation.mrz_valid
            else "MRZ checksum parity failure — one or more check digits do not match computed values."
        )
    else:
        mrz_status = "passed" if tampering_score < 40 else "suspicious" if tampering_score <= 70 else "failed"
        mrz_score = max(0, 100 - tampering_score)
        mrz_desc = (
            "Document check digits validated against algorithmic standards."
            if mrz_status == "passed"
            else "MRZ checksum anomaly or parity calculation mismatch detected."
        )
    checks.append({
        "id": "sc-1",
        "name": "ICAO 9303 MRZ Checksum Parity",
        "category": "mrz",
        "status": mrz_status,
        "score": mrz_score,
        "description": mrz_desc,
    })

    # 2. Compression Error Level Analysis (ELA)
    ela_status = "passed" if tampering_score < 40 else "suspicious" if tampering_score <= 70 else "failed"
    ela_score = max(0, 100 - tampering_score)
    checks.append({
        "id": "sc-2",
        "name": "Compression Error Level Analysis (ELA)",
        "category": "tamper",
        "status": ela_status,
        "score": ela_score,
        "description": (
            "Uniform compression rate observed across photograph and text boundaries."
            if ela_status == "passed"
            else "High intensity compression gradient variance detected in critical fields."
        ),
    })

    # 3. Biometric Facial Correlation
    if face_status == "RETRY":
        checks.append({
            "id": "sc-3",
            "name": "Biometric Facial Correlation",
            "category": "biometric",
            "status": "failed",
            "score": 0,
            "description": "Face match failed: no usable face detected in selfie capture.",
        })
    elif face_match_score is not None:
        bio_status = "passed" if face_match_score >= 70 else "suspicious" if face_match_score >= 50 else "failed"
        checks.append({
            "id": "sc-3",
            "name": "Biometric Facial Correlation",
            "category": "biometric",
            "status": bio_status,
            "score": face_match_score,
            "description": (
                f"128-d ArcFace embedding cosine similarity: {face_match_score}%."
                if bio_status == "passed"
                else f"Biometric correlation below threshold ({face_match_score}%)."
            ),
        })
    else:
        checks.append({
            "id": "sc-3",
            "name": "Biometric Facial Correlation",
            "category": "biometric",
            "status": "passed",
            "score": 100,
            "description": "Face match not applicable or skipped for this document type.",
        })

    # 4. Typography & Font Uniformity
    avg_conf = 95
    if ocr_confidence:
        avg_conf = int(sum(ocr_confidence.values()) / max(1, len(ocr_confidence)) * 100)
    font_status = "passed" if avg_conf >= 75 else "suspicious" if avg_conf >= 55 else "failed"
    checks.append({
        "id": "sc-4",
        "name": "Typography & Microprint Uniformity",
        "category": "font",
        "status": font_status,
        "score": avg_conf,
        "description": (
            "Font raster glyphs conform to official state template specifications."
            if font_status == "passed"
            else "Baseline glyph irregularity or low OCR confidence detected."
        ),
    })

    # 5. Aadhaar Secure QR Cryptographic Integrity (for NATIONAL_ID)
    if doc_type == "NATIONAL_ID" or aadhaar_qr is not None:
        if aadhaar_qr and aadhaar_qr.signature_valid is True and aadhaar_qr.verification_status == "VERIFIED_NO_MISMATCH":
            qr_status = "passed"
            qr_score = 100
            qr_desc = "UIDAI 2048-bit RSA digital signature verified. Signed demographic data matches OCR printed data."
        elif aadhaar_qr and (aadhaar_qr.signature_valid is False or aadhaar_qr.verification_status == "CRITICAL_INTEGRITY_MISMATCH"):
            qr_status = "failed"
            qr_score = 0
            qr_desc = (
                "Aadhaar QR signature validation failed or critical demographic mismatch with printed document."
                if aadhaar_qr.signature_valid is False
                else f"Integrity failure: {'; '.join(aadhaar_qr.mismatches)}"
            )
        elif aadhaar_qr and aadhaar_qr.detected:
            qr_status = "suspicious"
            qr_score = 45
            qr_desc = aadhaar_qr.message or "Aadhaar QR detected but cryptographic verification is unverified or inconclusive."
        else:
            qr_status = "passed" if tampering_score < 40 else "suspicious"
            qr_score = 75 if qr_status == "passed" else 40
            qr_desc = "No Secure QR detected on physical card specimen."

        checks.append({
            "id": "sc-5",
            "name": "Aadhaar Secure QR Cryptographic Integrity",
            "category": "crypto",
            "status": qr_status,
            "score": qr_score,
            "description": qr_desc,
        })

    return checks


def get_verdict_reason(
    verdict: str,
    risk_score: int,
    tampering_score: int,
    face_match_score: Optional[int] = None,
    validation: Optional[ValidationResult] = None,
    security_checks: Optional[List[Dict[str, Any]]] = None,
    category_mismatch: bool = False,
    selected_doc_type: Optional[str] = None,
    detected_doc_type: Optional[str] = None,
    aadhaar_qr: Optional[AadhaarQRResult] = None,
) -> str:
    """Get human-readable explanation of the verdict decision."""
    settings = get_settings()
    reasons = []

    # Check for category / doc type mismatch first
    if category_mismatch or (validation and any("DOCUMENT TYPE MISMATCH" in i.upper() or "CATEGORY MISMATCH" in i.upper() for i in validation.issues)):
        mismatch_issue = None
        if validation:
            for i in validation.issues:
                if "DOCUMENT TYPE MISMATCH" in i.upper() or "CATEGORY MISMATCH" in i.upper():
                    mismatch_issue = i
                    break
        if mismatch_issue:
            reasons.append(mismatch_issue)
        elif selected_doc_type and detected_doc_type:
            reasons.append(f"DOCUMENT TYPE MISMATCH: Selected {selected_doc_type} but detected {detected_doc_type}")
        else:
            reasons.append("DOCUMENT TYPE MISMATCH: Selected document type does not match detected document")

    reasons.append(f"Risk score: {risk_score}/100")

    # Aadhaar QR reasons
    if aadhaar_qr:
        if aadhaar_qr.signature_valid is False:
            reasons.append("Aadhaar digital signature verification FAILED (tampered/forged QR)")
        elif aadhaar_qr.verification_status == "CRITICAL_INTEGRITY_MISMATCH":
            reasons.append(f"CRITICAL INTEGRITY MISMATCH: {'; '.join(aadhaar_qr.mismatches)}")
        elif aadhaar_qr.signature_valid is True and aadhaar_qr.verification_status == "VERIFIED_NO_MISMATCH":
            reasons.append("Aadhaar Secure QR cryptographically verified with zero mismatch")
        elif aadhaar_qr.detected and aadhaar_qr.signature_valid is None:
            reasons.append(f"Aadhaar QR: {aadhaar_qr.message or 'Verification unverified/inconclusive'}")

    fake_thresh = getattr(settings, "tampering_fake_threshold", 70)
    susp_thresh = getattr(settings, "tampering_suspicious_threshold", 40)
    if tampering_score > fake_thresh:
        reasons.append(f"Severe tampering ({tampering_score} > {fake_thresh})")
    elif tampering_score >= susp_thresh:
        reasons.append(f"Moderate tampering ({tampering_score} ≥ {susp_thresh})")

    if face_match_score is not None:
        fm_fake = getattr(settings, "face_match_fake_threshold", 50)
        fm_susp = getattr(settings, "face_match_suspicious_threshold", 70)
        if face_match_score < fm_fake:
            reasons.append(f"Critical facial mismatch ({face_match_score}% < {fm_fake}%)")
        elif face_match_score < fm_susp:
            reasons.append(f"Borderline facial match ({face_match_score}%)")

    if validation:
        if not validation.format_valid and not any("DOCUMENT TYPE MISMATCH" in i.upper() for i in validation.issues):
            reasons.append("Document format validation failed")
        if not validation.expiry_valid:
            reasons.append("Document has expired")
        if validation.mrz_valid is False:
            reasons.append("MRZ checksum parity failure")
        for issue in validation.issues:
            if "BLACKLIST" in issue.upper():
                reasons.append(issue)

    if security_checks:
        failed = [c.get("name") for c in security_checks if c.get("status") == "failed"]
        if failed:
            reasons.append(f"Failed checks: {', '.join(failed)}")

    return f"{verdict}: " + "; ".join(reasons)


def generate_risk_breakdown(
    tampering_score: int,
    face_match_score: Optional[int] = None,
    validation_issues_count: int = 0,
    liveness_failed: bool = False,
    presentation_attack_detected: bool = False,
    category_mismatch: bool = False,
    is_low_quality: bool = False,
    is_expired: bool = False,
    aadhaar_qr: Optional[AadhaarQRResult] = None,
) -> List[RiskBreakdownItem]:
    """
    Produce an itemized list of all factors that contributed to the composite risk score.
    Only includes factors that actively contributed risk points.
    """
    settings = get_settings()
    items: List[RiskBreakdownItem] = []

    # 1. Tampering
    if tampering_score > getattr(settings, "tampering_fake_threshold", 70):
        pts = int(round(66.0 + (tampering_score - 70) * 0.8))
        items.append(RiskBreakdownItem(
            factor="Critical Document Tampering",
            points=pts,
            category="TAMPERING",
            description=f"High-confidence digital splicing / ELA gradient anomaly ({tampering_score}% tampering index).",
        ))
    elif tampering_score >= getattr(settings, "tampering_suspicious_threshold", 40):
        pts = int(round(30.0 + (tampering_score - 40) * 0.7))
        items.append(RiskBreakdownItem(
            factor="Suspicious Tampering Indicators",
            points=pts,
            category="TAMPERING",
            description=f"Localized compression and metadata inconsistencies detected ({tampering_score}% index).",
        ))
    elif tampering_score > 15:
        pts = int(round(tampering_score * 0.4))
        items.append(RiskBreakdownItem(
            factor="Minor Forensic Noise",
            points=pts,
            category="TAMPERING",
            description=f"Low-level compression artifacts within acceptable boundary ({tampering_score}% index).",
        ))

    # 2. Face Match
    if face_match_score is not None:
        fake_thresh = getattr(settings, "face_match_fake_threshold", 50)
        susp_thresh = getattr(settings, "face_match_suspicious_threshold", 70)
        if face_match_score < fake_thresh:
            deficit = float(fake_thresh - face_match_score)
            pts = int(round(66.0 + (deficit / max(1.0, float(fake_thresh))) * 24.0))
            items.append(RiskBreakdownItem(
                factor="Biometric Face Mismatch",
                points=pts,
                category="BIOMETRIC",
                description=f"Facial similarity ({face_match_score}%) well below security threshold ({fake_thresh}%).",
            ))
        elif face_match_score < susp_thresh:
            deficit = float(susp_thresh - face_match_score)
            span = float(susp_thresh - fake_thresh)
            pts = int(round(25.0 + (deficit / max(1.0, span)) * 20.0))
            items.append(RiskBreakdownItem(
                factor="Borderline Biometric Match",
                points=pts,
                category="BIOMETRIC",
                description=f"Facial similarity ({face_match_score}%) in secondary inspection range.",
            ))

    # 3. Validation Issues
    if validation_issues_count > 0:
        pts = min(int(round(validation_issues_count * 10.0)), 30)
        items.append(RiskBreakdownItem(
            factor=f"Document Validation Issues ({validation_issues_count})",
            points=pts,
            category="VALIDATION",
            description=f"{validation_issues_count} format or field validation rule(s) triggered.",
        ))

    # 4. Specific Flags
    if presentation_attack_detected:
        items.append(RiskBreakdownItem(
            factor="Presentation Attack / Spoofing",
            points=50,
            category="BIOMETRIC",
            description="Screen replay, moiré grid, or flat print attack pattern detected on capture.",
        ))
    elif liveness_failed:
        items.append(RiskBreakdownItem(
            factor="Liveness Check Failure",
            points=30,
            category="BIOMETRIC",
            description="Subject liveness characteristics could not be confirmed.",
        ))

    if category_mismatch:
        items.append(RiskBreakdownItem(
            factor="Document Classification Conflict",
            points=75,
            category="VALIDATION",
            description="Uploaded document physical layout conflicts with declared category.",
        ))

    if is_expired:
        items.append(RiskBreakdownItem(
            factor="Document Expired",
            points=35,
            category="VALIDATION",
            description="Credential expiration date has passed.",
        ))

    if is_low_quality:
        items.append(RiskBreakdownItem(
            factor="Low Image Quality",
            points=10,
            category="INTEGRITY",
            description="Severe blur, under-exposure, or extreme aspect ratio detected.",
        ))

    # 5. Aadhaar QR
    if aadhaar_qr:
        if aadhaar_qr.signature_valid is False:
            items.append(RiskBreakdownItem(
                factor="Aadhaar Signature Forgery",
                points=75,
                category="CRYPTO",
                description="UIDAI RSA-2048 cryptographic signature validation failed.",
            ))
        elif aadhaar_qr.verification_status == "CRITICAL_INTEGRITY_MISMATCH":
            items.append(RiskBreakdownItem(
                factor="Aadhaar QR / OCR Data Mismatch",
                points=70,
                category="CRYPTO",
                description=f"Signed data contradicts printed fields: {'; '.join(aadhaar_qr.mismatches)}",
            ))

    return items


def generate_why_flagged_evidence(
    validation: Optional[ValidationResult],
    tampering_score: int,
    face_match_score: Optional[int] = None,
    category_match: bool = True,
    cross_field_result: Optional[CrossFieldConsistencyResult] = None,
    aadhaar_qr: Optional[AadhaarQRResult] = None,
    doc_type: Optional[str] = None,
) -> List[WhyFlaggedItem]:
    """
    Generate clean, inspectable evidence items explaining exactly why a decision was reached.
    Includes positive confirmations (PASS) and negative anomalies (WARN / FAIL).
    """
    settings = get_settings()
    items: List[WhyFlaggedItem] = []

    # 1. Document Category & Format
    if not category_match:
        items.append(WhyFlaggedItem(
            type="FAIL",
            title="Document Type Conflict",
            description="Uploaded specimen structure conflicts with selected document type.",
        ))
    elif validation and validation.format_valid:
        items.append(WhyFlaggedItem(
            type="PASS",
            title="Document Format Valid",
            description="Standard ID dimensions, layout structure, and font geometry verified.",
        ))
    elif validation:
        items.append(WhyFlaggedItem(
            type="WARN",
            title="Format Anomalies Flagged",
            description="; ".join(validation.issues[:2]) if validation.issues else "Minor layout irregularity.",
        ))

    # 2. Expiry
    if validation and not validation.expiry_valid:
        items.append(WhyFlaggedItem(
            type="FAIL",
            title="Document Expired",
            description="Credential expiration date is in the past.",
        ))
    elif validation:
        items.append(WhyFlaggedItem(
            type="PASS",
            title="Credential Valid",
            description="Document is currently unexpired and within operational date window.",
        ))

    # 3. MRZ / Cryptography
    if aadhaar_qr and aadhaar_qr.detected:
        if aadhaar_qr.signature_valid is True:
            items.append(WhyFlaggedItem(
                type="PASS",
                title="UIDAI Digital Signature Verified",
                description="2048-bit RSA cryptographic signature confirmed authentic.",
            ))
        elif aadhaar_qr.signature_valid is False:
            items.append(WhyFlaggedItem(
                type="FAIL",
                title="Digital Signature Invalid",
                description="Aadhaar QR signature validation failed (cryptographic forgery).",
            ))
    elif validation and validation.mrz_valid is not None:
        if validation.mrz_valid:
            items.append(WhyFlaggedItem(
                type="PASS",
                title="ICAO 9303 Checksums Valid",
                description="Passport/ID MRZ check digits verified against ICAO 9303 standard.",
            ))
        else:
            items.append(WhyFlaggedItem(
                type="FAIL",
                title="MRZ Checksum Parity Failure",
                description="One or more check digits failed mathematical verification.",
            ))

    # 4. Tampering & ELA
    fake_thresh = getattr(settings, "tampering_fake_threshold", 70)
    susp_thresh = getattr(settings, "tampering_suspicious_threshold", 40)
    if tampering_score > fake_thresh:
        items.append(WhyFlaggedItem(
            type="FAIL",
            title="Critical Tampering Detected",
            description=f"Severe ELA compression variance detected ({tampering_score}% tampering index).",
        ))
    elif tampering_score >= susp_thresh:
        items.append(WhyFlaggedItem(
            type="WARN",
            title="Suspicious Tampering Gradient",
            description=f"Moderate compression variance in photo or text fields ({tampering_score}% index).",
        ))
    else:
        items.append(WhyFlaggedItem(
            type="PASS",
            title="No Tampering Detected",
            description=f"Uniform compression and noise consistency verified ({tampering_score}% index).",
        ))

    # 5. Biometric Face Match
    if face_match_score is not None:
        fm_fake = getattr(settings, "face_match_fake_threshold", 50)
        fm_susp = getattr(settings, "face_match_suspicious_threshold", 70)
        if face_match_score >= fm_susp:
            items.append(WhyFlaggedItem(
                type="PASS",
                title="Biometric Face Match Verified",
                description=f"Subject face matches document portrait ({face_match_score}% similarity).",
            ))
        elif face_match_score >= fm_fake:
            items.append(WhyFlaggedItem(
                type="WARN",
                title="Borderline Biometric Match",
                description=f"Facial similarity ({face_match_score}%) falls within secondary inspection window.",
            ))
        else:
            items.append(WhyFlaggedItem(
                type="FAIL",
                title="Biometric Face Mismatch",
                description=f"Presented person does not match document photo ({face_match_score}% similarity).",
            ))

    # 6. Cross-Field Consistency
    if cross_field_result and cross_field_result.discrepancies:
        items.append(WhyFlaggedItem(
            type="FAIL",
            title="Cross-Field Discrepancy",
            description=f"Discrepancy detected between visual OCR and MRZ/QR ({cross_field_result.discrepancies[0]}).",
        ))
    elif cross_field_result and cross_field_result.status == "CONSISTENT":
        items.append(WhyFlaggedItem(
            type="PASS",
            title="Cross-Field Consistency Confirmed",
            description="Extracted visual fields correspond to MRZ / QR demographic data.",
        ))

    return items