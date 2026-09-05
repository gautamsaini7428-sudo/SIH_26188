from functools import lru_cache
from typing import List
# pyrefly: ignore [missing-import]
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    database_url: str = "sqlite+aiosqlite:///./verifications.db"

    # Admin Auth
    admin_username: str = "admin"
    admin_password_hash: str = ""

    # Session & Auth
    session_secret: str = "dev-secret-change-in-production-32chars-min"
    access_token_expire_minutes: int = 480  # 8-hour shift

    # ── Risk Score Weights (configurable) ──
    risk_weight_tampering: float = 0.4
    risk_weight_face: float = 0.4
    risk_weight_validation_issue: float = 10.0  # per issue, capped at 30 total

    # ── Verdict Hard-Gate Thresholds ──
    tampering_fake_threshold: int = 70
    face_match_fake_threshold: int = 50
    tampering_suspicious_threshold: int = 40
    face_match_suspicious_threshold: int = 70

    # ── Risk Score → Verdict Thresholds ──
    risk_genuine_max: int = 30       # risk_score 0-30 AND all gates clear → GENUINE
    risk_suspicious_max: int = 65    # risk_score 31-65 → SUSPICIOUS
    # risk_score > 65 → FAKE

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:5173,http://localhost:5174,http://127.0.0.1:3000,http://127.0.0.1:5173,http://127.0.0.1:5174,http://localhost:8000,http://127.0.0.1:8000"

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    # File Upload
    upload_dir: str = "./uploads"
    max_file_size_mb: int = 10

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024

    # ── OCR & Preprocessing Settings ──
    ocr_engine: str = "auto"  # "auto", "easyocr", "paddleocr"
    ocr_languages: List[str] = ["en"]
    ocr_gpu: bool = False
    enable_orientation_correction: bool = True
    enable_enhancement: bool = True
    max_image_dimension: int = 2500
    min_image_dimension: int = 1000
    pdf_dpi: int = 200
    min_confidence_threshold: float = 0.20

    # ── Mock Checkpoint Locations (for demo realism) ──
    checkpoint_locations: str = (
        "Attari-Wagah Border,Petrapole-Benapole Crossing,"
        "Moreh ICP,Raxaul Border Post,Dawki-Tamabil Gate,"
        "Agartala ICP,Jogbani Checkpoint,Hili Land Port,"
        "Sutarkandi ICP,Sabroom Land Port"
    )

    @property
    def checkpoint_location_list(self) -> List[str]:
        return [loc.strip() for loc in self.checkpoint_locations.split(",") if loc.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()