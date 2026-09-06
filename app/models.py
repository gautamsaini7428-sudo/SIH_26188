from datetime import datetime
from typing import Optional
from sqlalchemy import Integer, String, Text, DateTime, Index, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="OFFICER", nullable=False)
    checkpoint_location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Verification(Base):
    __tablename__ = "verifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=True)
    selfie_path: Mapped[str] = mapped_column(String(500), nullable=True)

    # Document metadata
    document_type: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    checkpoint_location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    officer_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)

    # Extracted fields (JSON string — shape varies by document_type)
    extracted_name: Mapped[str] = mapped_column(Text, nullable=True)
    extracted_dob: Mapped[str] = mapped_column(Text, nullable=True)
    extracted_id_number: Mapped[str] = mapped_column(Text, nullable=True)
    extracted_address: Mapped[str] = mapped_column(Text, nullable=True)
    extracted_confidence: Mapped[str] = mapped_column(Text, nullable=True)
    extracted_fields_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    full_response_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Scores
    tampering_score: Mapped[int] = mapped_column(Integer, nullable=True)
    tampering_regions: Mapped[str] = mapped_column(Text, nullable=True)
    heatmap_path: Mapped[str] = mapped_column(String(500), nullable=True)
    face_match_score: Mapped[int] = mapped_column(Integer, nullable=True)
    risk_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Verdict
    verdict: Mapped[str] = mapped_column(String(20), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    processing_time_ms: Mapped[int] = mapped_column(Integer, nullable=True)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=True)

    __table_args__ = (
        CheckConstraint("verdict IN ('GENUINE', 'SUSPICIOUS', 'FAKE', 'REJECTED')", name="check_verdict"),
        Index("idx_verifications_verdict", "verdict"),
        Index("idx_verifications_timestamp_verdict", "timestamp", "verdict"),
    )


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    verification_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    severity: Mapped[str] = mapped_column(String(20), default="HIGH", nullable=False, index=True)  # CRITICAL | HIGH | MEDIUM | LOW
    status: Mapped[str] = mapped_column(String(20), default="UNREVIEWED", nullable=False, index=True)  # UNREVIEWED | REVIEWED | RESOLVED | ESCALATED

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    document_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    person_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    document_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    officer_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    checkpoint: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    risk_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    verdict: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    face_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tampering_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    details_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_alerts_status_severity", "status", "severity"),
        Index("idx_alerts_created_at", "created_at"),
    )