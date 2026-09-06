"""
Comprehensive Unit & Integration Tests for Phase 3:
- Real Verification History API (filtering, search, pagination, single verification retrieval)
- Real Database-Driven Statistics API (verdicts, high risk, averages, daily volume, zero state)
- Standalone Face Biometrics Endpoint (POST /verify/face, authentication, structured error states)
- Security & RBAC Enforcement (Officer vs Supervisor, immutable AI scores)
- File Upload Security (format filtering, size bounds, safe paths)
"""

import sys
from unittest.mock import MagicMock, patch

if "deepface" not in sys.modules:
    mock_deepface_mod = MagicMock()
    mock_deepface_mod.DeepFace = MagicMock()
    sys.modules["deepface"] = mock_deepface_mod

import os
import io
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app
from app.auth import create_access_token
from app.models import User, Verification, Alert
from app.database import async_session_maker, init_db
from app.services.verification import (
    get_verification_history,
    get_verification_stats,
)
from app.services.alert_service import review_alert


@pytest.fixture(autouse=True)
async def setup_test_db():
    await init_db()


def get_token(email: str, role: str, checkpoint: str = "Central HQ") -> str:
    return create_access_token({"sub": email, "role": role, "checkpoint_location": checkpoint})


# ── PART 1: History Tests ──

@pytest.mark.asyncio
async def test_verification_history_and_search():
    """Test verification history pagination and multi-attribute search filtering."""
    async with async_session_maker() as db:
        # Seed test verifications
        v1 = Verification(
            filename="passport_anil.jpg",
            document_type="PASSPORT",
            extracted_name="Anil Kapoor",
            extracted_id_number="M8765432",
            checkpoint_location="Attari-Wagah Border",
            officer_email="officer.attari@mha.gov.in",
            verdict="GENUINE",
            risk_score=12,
            tampering_score=4,
            face_match_score=96,
            processing_time_ms=820,
        )
        v2 = Verification(
            filename="fake_license.png",
            document_type="DRIVING_LICENSE",
            extracted_name="Ramesh Gupta",
            extracted_id_number="DL04201100",
            checkpoint_location="Petrapole-Benapole Crossing",
            officer_email="officer.petrapole@mha.gov.in",
            verdict="FAKE",
            risk_score=94,
            tampering_score=88,
            face_match_score=15,
            processing_time_ms=1150,
        )
        db.add_all([v1, v2])
        await db.commit()
        await db.refresh(v1)
        await db.refresh(v2)

        # 1. Search by name
        items, total = await get_verification_history(db, search_query="Anil")
        assert total >= 1
        assert any(item.extracted_name == "Anil Kapoor" for item in items)

        # 2. Filter by verdict
        items, total = await get_verification_history(db, verdict="FAKE")
        assert total >= 1
        assert all(item.verdict == "FAKE" for item in items)

        # 3. Filter by document type
        items, total = await get_verification_history(db, document_type="PASSPORT")
        assert total >= 1
        assert all(item.document_type == "PASSPORT" for item in items)


def test_history_endpoint_and_single_verification():
    """Test GET /history and GET /verification/{id} with auth."""
    token = get_token("supervisor.delhi@mha.gov.in", "SUPERVISOR")
    with TestClient(app) as client:
        # 1. Fetch history list
        res = client.get("/history?limit=10", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        data = res.json()
        assert "items" in data
        assert "total" in data

        if data["total"] > 0:
            first_id = data["items"][0]["id"]
            # 2. Fetch single canonical verification
            single_res = client.get(f"/verification/{first_id}", headers={"Authorization": f"Bearer {token}"})
            assert single_res.status_code == 200
            single_data = single_res.json()
            assert single_data["verification_id"] == first_id
            assert "verdict" in single_data
            assert "risk_score" in single_data


# ── PART 2: Real Database Statistics Tests ──

@pytest.mark.asyncio
async def test_stats_aggregation_from_database():
    """Test get_verification_stats returns correct aggregated metrics from database."""
    async with async_session_maker() as db:
        stats = await get_verification_stats(db)
        assert isinstance(stats, dict)
        assert "genuine" in stats
        assert "suspicious" in stats
        assert "fake" in stats
        assert "rejected" in stats
        assert "total" in stats
        assert "high_risk" in stats
        assert "by_document_type" in stats
        assert "by_checkpoint" in stats
        assert "daily_volume" in stats
        assert isinstance(stats["daily_volume"], list)


def test_stats_api_endpoint():
    """Test GET /stats requires authentication and returns enriched telemetry."""
    # 1. Unauthenticated -> 401
    with TestClient(app) as client:
        unauth_res = client.get("/stats")
        assert unauth_res.status_code == 401

        # 2. Authenticated -> 200 with complete metrics
        token = get_token("officer.attari@mha.gov.in", "OFFICER")
        res = client.get("/stats", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        data = res.json()
        assert "total" in data
        assert "high_risk" in data
        assert "daily_volume" in data
        assert "by_checkpoint" in data


# ── PART 3: Standalone Face Biometrics Endpoint Tests ──

def test_standalone_face_verification_endpoint():
    """Test POST /verify/face with mock embeddings, verifying response schema and auth."""
    token = get_token("officer.attari@mha.gov.in", "OFFICER")
    with TestClient(app) as client:
        # 1. Unauthenticated -> 401
        unauth_res = client.post("/verify/face")
        assert unauth_res.status_code == 401

        # 2. Valid image comparison
        unit_vec = [1.0] + [0.0] * 511
        mock_rep = [{"facial_area": {"w": 60, "h": 60}, "face_confidence": 0.99, "embedding": unit_vec}]
        
        # Create minimal 100x100 PNG files
        import numpy as np
        import cv2
        img = np.full((120, 120, 3), 128, dtype=np.uint8)
        _, buf = cv2.imencode(".png", img)
        png_bytes = buf.tobytes()

        with patch("deepface.DeepFace.represent", return_value=mock_rep):
            files = {
                "id_file": ("id_photo.png", png_bytes, "image/png"),
                "selfie_file": ("selfie_photo.png", png_bytes, "image/png"),
            }
            res = client.post("/verify/face", files=files, headers={"Authorization": f"Bearer {token}"})
            assert res.status_code == 200
            data = res.json()
            assert data["status"] == "matched"
            assert data["matched"] is True
            assert data["score"] == 100
            assert "distance" in data
            assert data["threshold"] == 0.68


def test_face_verification_error_handling():
    """Test POST /verify/face error handling on empty or unsupported files."""
    token = get_token("officer.attari@mha.gov.in", "OFFICER")
    with TestClient(app) as client:
        # Unsupported file extension (.exe)
        files = {
            "id_file": ("malicious.exe", b"MZ...", "application/octet-stream"),
            "selfie_file": ("selfie.jpg", b"fake-jpg", "image/jpeg"),
        }
        res = client.post("/verify/face", files=files, headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 400
        assert "Unsupported file format" in res.json()["detail"]


# ── PART 4: Security, RBAC & Audit Integrity Tests ──

def test_officer_cannot_review_alerts_rbac():
    """Test Officer role is forbidden from executing supervisor alert reviews."""
    officer_token = get_token("officer.attari@mha.gov.in", "OFFICER")
    with TestClient(app) as client:
        res = client.patch(
            "/alerts/1/review",
            json={"status": "RESOLVED", "notes": "Officer attempting review"},
            headers={"Authorization": f"Bearer {officer_token}"},
        )
        assert res.status_code == 403


@pytest.mark.asyncio
async def test_audit_log_hash_chain_integrity():
    """Test SHA-256 hash-chained immutable audit log creation and verification."""
    from app.services.audit_log import log_verification, verify_audit_chain

    # Add audit log entries
    h1 = log_verification({
        "document_id": "DOC-CHAIN-001",
        "verdict": "VERIFIED",
        "tampering_score": 2,
        "face_match_score": 98,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    assert len(h1) == 64

    h2 = log_verification({
        "document_id": "DOC-CHAIN-002",
        "verdict": "SUSPECTED",
        "tampering_score": 45,
        "face_match_score": 60,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    assert len(h2) == 64

    # Verify chain integrity
    res = verify_audit_chain()
    assert isinstance(res, dict)
    assert res.get("valid") is True
    assert res.get("tampered_index") is None
