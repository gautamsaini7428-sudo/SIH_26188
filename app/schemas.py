"""
Pydantic Schemas — SIH26188 API Contract & OCR Modules

Matches the shared API contract:
{
  "document_type": "PASSPORT | VISA | NATIONAL_ID | DRIVING_LICENSE | PERMIT",
  "extracted_fields": { /* shape varies by document_type */ },
  "validation": { "format_valid": bool, "expiry_valid": bool, "issues": ["..."] },
  "tampering_score": 0-100,
  "tampering_regions": [{x,y,w,h}],
  "heatmap_image_base64": "",
  "face_match_score": 0-100,
  "risk_score": 0-100,
  "verdict": "GENUINE | SUSPICIOUS | FAKE | REJECTED"
}
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, ConfigDict


# ── Document Types ──
DOCUMENT_TYPES = ("PASSPORT", "VISA", "NATIONAL_ID", "DRIVING_LICENSE", "PERMIT")


# ── Sub-models ──

class TamperingRegion(BaseModel):
    x: int
    y: int
    w: int
    h: int
    field: Optional[str] = None
    confidence: Optional[float] = None
    reason: Optional[str] = None


class ValidationResult(BaseModel):
    """Standalone document validation output — separate from tampering."""
    format_valid: bool = True
    expiry_valid: bool = True
    issues: List[str] = Field(default_factory=list)
    mrz_valid: Optional[bool] = None  # Populated when MRZ is detected (PASSPORT / TD1 / TD2)
    mrz_details: Optional[Dict[str, Any]] = None


class SecurityCheckItem(BaseModel):
    id: str
    name: str
    category: str
    status: str
    score: int
    description: str


# ── OCR & MRZ Sub-models (from 4th.zip) ──

class OCRLine(BaseModel):
    text: str = Field(..., description="Recognized line text")
    confidence: float = Field(..., description="OCR confidence score between 0.0 and 1.0")
    bbox: List[Union[List[float], List[int], int, float]] = Field(
        ...,
        description="Bounding box coordinates (e.g. 4 corner points [[x1,y1],[x2,y2],[x3,y3],[x4,y4]] or [x,y,w,h])"
    )


class ExtractedFields(BaseModel):
    name: Optional[str] = None
    document_number: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    nationality: Optional[str] = None
    issue_date: Optional[str] = None
    expiry_date: Optional[str] = None
    address: Optional[str] = None

    class Config:
        extra = "allow"


class MRZResult(BaseModel):
    detected: bool = False
    raw: Optional[str] = None
    valid: Optional[bool] = None
    fields: Dict[str, Any] = Field(default_factory=dict)


class OCRResponse(BaseModel):
    raw_text: str
    lines: List[OCRLine]
    fields: ExtractedFields
    mrz: MRZResult
    document_type: str = Field(
        default="unknown",
        description="Document type classification: passport/id/license/visa/invoice/certificate/unknown"
    )
    ocr_status: Optional[str] = None
    provenance: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "1.0.0"
    engine: str = "auto"
    gpu_available: bool = False


# ── Biometric Sub-models (SIH26188 Advanced Screening) ──

class QualityResult(BaseModel):
    status: str = Field(default="GOOD", description="GOOD | LOW_QUALITY")
    score: float = Field(default=1.0, ge=0.0, le=1.0)
    details: Optional[str] = None


class LivenessResult(BaseModel):
    status: str = Field(default="PASS", description="PASS | FAIL | UNAVAILABLE")
    score: float = Field(default=1.0, ge=0.0, le=1.0)
    details: Optional[str] = None


class PresentationAttackResult(BaseModel):
    detected: bool = Field(default=False)
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    type: Optional[str] = Field(default=None, description="SCREEN_REPLAY | PRINT_ATTACK | OBSTRUCTION | null")
    details: Optional[str] = None


class FaceMatchResult(BaseModel):
    status: str = Field(default="MATCH", description="MATCH | NO_MATCH | BORDERLINE | SKIPPED | UNAVAILABLE")
    score: Optional[int] = Field(default=None, ge=0, le=100)
    distance: Optional[float] = None
    threshold: float = 0.68
    details: Optional[str] = None


class BiometricResult(BaseModel):
    face_detected: bool = True
    face_count: int = 1
    quality: QualityResult = Field(default_factory=QualityResult)
    liveness: LivenessResult = Field(default_factory=LivenessResult)
    presentation_attack: PresentationAttackResult = Field(default_factory=PresentationAttackResult)
    face_match: FaceMatchResult = Field(default_factory=FaceMatchResult)
    status: str = Field(default="VERIFIED", description="VERIFIED | REJECTED | RETRY | NEEDS_REVIEW | NOT_APPLICABLE")


class IdentityLinkItem(BaseModel):
    historical_verification_id: int
    case_number: str
    historical_name: Optional[str] = None
    historical_document_number: Optional[str] = None
    similarity_score: int = Field(default=0, ge=0, le=100)
    relationship_type: str = "FACIAL_MATCH_DIFFERENT_IDENTITY"
    recommendation: str = "INVESTIGATION RECOMMENDED"
    details: str


# ── Aadhaar Secure QR Result ──

class AadhaarQRResult(BaseModel):
    detected: bool = False
    decoded: bool = False
    signature_valid: Optional[bool] = None
    verification_status: str = "NOT_VERIFIED"
    signed_fields: Dict[str, Any] = Field(default_factory=dict)
    field_matches: Dict[str, Optional[bool]] = Field(default_factory=dict)
    mismatches: List[str] = Field(default_factory=list)
    photo_available: bool = False
    error_code: Optional[str] = None
    message: Optional[str] = None


# ── Primary API Response ──

class VerifyResponse(BaseModel):
    verification_id: Optional[int] = None
    document_type: str = Field(default="DRIVING_LICENSE", description="PASSPORT|VISA|NATIONAL_ID|DRIVING_LICENSE|PERMIT")
    expected_document_type: Optional[str] = None
    detected_document_type: Optional[str] = None
    category_match: bool = True
    extracted_fields: Dict[str, Any] = Field(default_factory=dict, description="Shape varies by document_type")
    validation: ValidationResult = Field(default_factory=ValidationResult)
    tampering_score: int = Field(default=0, ge=0, le=100)
    tampering_regions: List[TamperingRegion] = Field(default_factory=list)
    heatmap_image_base64: str = Field(default="", description="Base64 encoded heatmap overlay")
    face_match_score: Optional[int] = Field(default=None, ge=0, le=100)
    biometric: Optional[BiometricResult] = None
    risk_score: int = Field(default=0, ge=0, le=100, description="Primary output: weighted risk composite")
    risk_level: Optional[str] = None
    risk_factors: List[str] = Field(default_factory=list)
    verdict: str = Field(default="GENUINE")
    reason: Optional[str] = None
    security_checks: List[SecurityCheckItem] = Field(default_factory=list)
    identity_links: List[IdentityLinkItem] = Field(default_factory=list)
    aadhaar_qr: Optional[AadhaarQRResult] = None
    processing_time_ms: Optional[int] = None
    case_number: Optional[str] = None
    checkpoint_location: Optional[str] = None
    officer_email: Optional[str] = None
    mrz: Optional[MRZResult] = None
    ocr_lines: Optional[List[OCRLine]] = None
    raw_text: Optional[str] = None
    quality_status: Optional[str] = None
    ocr_status: Optional[str] = None
    face_status: Optional[str] = None
    document_quality: Optional[Dict[str, Any]] = None
    field_provenance: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


# ── Tampering Analysis Response ──

class AnalyzeTamperingResponse(BaseModel):
    tampering_score: int = Field(ge=0, le=100)
    tampering_regions: List[TamperingRegion] = Field(default_factory=list)
    heatmap_image_base64: str = ""
    signals: Dict[str, Any] = Field(default_factory=dict)
    summary: str = ""


# ── History ──

class VerificationHistoryItem(BaseModel):
    id: int
    timestamp: datetime
    filename: str
    document_type: Optional[str] = None
    checkpoint_location: Optional[str] = None
    officer_email: Optional[str] = None
    extracted_name: Optional[str] = None
    extracted_id_number: Optional[str] = None
    tampering_score: Optional[int] = None
    face_match_score: Optional[int] = None
    risk_score: Optional[int] = None
    verdict: str
    reason: Optional[str] = None
    processing_time_ms: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class HistoryResponse(BaseModel):
    items: List[VerificationHistoryItem]
    total: int
    page: int
    limit: int
    total_pages: int


# ── Standalone Face Match ──

class FaceVerifyResponse(BaseModel):
    status: str  # "matched" | "not_matched" | "no_face_detected" | "multiple_faces_detected" | "error"
    score: int = Field(ge=0, le=100)
    matched: bool
    distance: Optional[float] = None
    threshold: float = 0.68
    detail: str = ""


# ── Stats ──

class DailyVolumePoint(BaseModel):
    day: str
    count: int
    date: Optional[str] = None


class StatsResponse(BaseModel):
    genuine: int
    suspicious: int
    fake: int
    rejected: int = 0
    total: int
    high_risk: int = 0
    avg_processing_time_ms: int = 0
    by_document_type: Dict[str, int] = Field(default_factory=dict)
    by_checkpoint: Dict[str, int] = Field(default_factory=dict)
    daily_volume: List[DailyVolumePoint] = Field(default_factory=list)
    alerts_total: int = 0
    alerts_resolved: int = 0
    period_from: Optional[datetime] = None
    period_to: Optional[datetime] = None


# ── Auth ──

class UserDTO(BaseModel):
    email: str
    role: str = "OFFICER"
    checkpoint_location: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None  # fallback support
    password: str


class LoginResponse(BaseModel):
    success: bool
    message: str
    access_token: str = ""
    token_type: str = "bearer"
    user: Optional[UserDTO] = None


class AuthMeResponse(BaseModel):
    authenticated: bool
    user: Optional[UserDTO] = None


class ErrorResponse(BaseModel):
    error: str
    message: str
    detail: Optional[str] = None


# ── Alerts ──

class AlertDTO(BaseModel):
    id: int
    verification_id: Optional[int] = None
    case_number: Optional[str] = None
    severity: str  # CRITICAL | HIGH | MEDIUM | LOW
    status: str  # UNREVIEWED | REVIEWED | RESOLVED | ESCALATED
    title: str
    message: str
    document_number: Optional[str] = None
    person_name: Optional[str] = None
    document_type: Optional[str] = None
    officer_email: Optional[str] = None
    checkpoint: Optional[str] = None
    risk_score: Optional[int] = None
    verdict: Optional[str] = None
    face_score: Optional[int] = None
    tampering_score: Optional[int] = None
    details: List[str] = Field(default_factory=list)
    created_at: datetime
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    review_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AlertListResponse(BaseModel):
    items: List[AlertDTO]
    total: int
    unreviewed_count: int
    critical_count: int
    high_count: int
    resolved_count: int


class AlertReviewRequest(BaseModel):
    status: str = Field(..., description="REVIEWED | RESOLVED | ESCALATED | UNREVIEWED")
    notes: Optional[str] = Field(None, description="Supervisor review notes / disposition")


class AlertStatsResponse(BaseModel):
    total: int
    unreviewed: int
    critical: int
    high: int
    medium: int
    resolved: int
    escalated: int