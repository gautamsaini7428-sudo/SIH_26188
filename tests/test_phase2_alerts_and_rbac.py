"""
Comprehensive Unit & Integration Tests for Phase 2:
- Real Alert Database Model & Persistence
- Automatic Alert Generation on Verification
- Real Alert API Endpoints (/alerts, /alerts/{id}, /alerts/{id}/review)
- Supervisor-Only RBAC & 403 / 401 Enforcement
- Audit Trail Integrity for Supervisor Actions
- Verification Preservation (AI results cannot be overwritten)
"""

import pytest
import json
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app
from app.auth import create_access_token
from app.models import User, Verification, Alert
from app.database import async_session_maker, init_db
from app.schemas import ValidationResult
from app.services.alert_service import (
    create_alert_for_verification,
    get_alerts,
    get_alert_by_id,
    review_alert,
)


@pytest.fixture(autouse=True)
async def setup_test_db():
    await init_db()


def get_token(email: str, role: str, checkpoint: str = "Central HQ") -> str:
    return create_access_token({"sub": email, "role": role, "checkpoint_location": checkpoint})


@pytest.mark.asyncio
async def test_alert_creation_for_genuine_low_risk_does_not_create_high_alert():
    """
    Test 1: Genuine low-risk verification (GENUINE + risk <= 30)
    should NOT generate a high/critical alert.
    """
    async with async_session_maker() as db:
        v = Verification(
            filename="clean_passport.jpg",
            document_type="PASSPORT",
            extracted_name="Priya Sharma",
            extracted_id_number="Z1234567",
            tampering_score=5,
            face_match_score=95,
            risk_score=10,
            verdict="GENUINE",
            checkpoint_location="Attari-Wagah Border",
            officer_email="officer.attari@mha.gov.in",
        )
        db.add(v)
        await db.commit()
        await db.refresh(v)

        alert = await create_alert_for_verification(
            db=db,
            verification=v,
            validation_result=ValidationResult(format_valid=True, expiry_valid=True, issues=[]),
        )

        assert alert is None, "Genuine low-risk verification should not trigger a security alert"


@pytest.mark.asyncio
async def test_alert_creation_for_fake_and_rejected_verifications():
    """
    Test 2 & 3: FAKE and REJECTED verifications generate persistent alerts with correct severity.
    """
    async with async_session_maker() as db:
        # Case A: Fake document
        v_fake = Verification(
            filename="forged_id.jpg",
            document_type="NATIONAL_ID",
            extracted_name="Alexander Reed",
            extracted_id_number="ID-9999",
            tampering_score=85,
            face_match_score=15,
            risk_score=92,
            verdict="FAKE",
            checkpoint_location="Attari-Wagah Border",
            officer_email="officer.attari@mha.gov.in",
            reason="Severe digital tampering and face mismatch",
        )
        db.add(v_fake)
        await db.commit()
        await db.refresh(v_fake)

        alert_fake = await create_alert_for_verification(
            db=db,
            verification=v_fake,
            validation_result=ValidationResult(format_valid=True, expiry_valid=True, issues=[]),
        )

        assert alert_fake is not None
        assert alert_fake.severity == "CRITICAL"
        assert alert_fake.status == "UNREVIEWED"
        assert alert_fake.verification_id == v_fake.id
        assert alert_fake.risk_score == 92

        # Case B: Rejected category mismatch
        v_rej = Verification(
            filename="dl_uploaded_as_id.jpg",
            document_type="NATIONAL_ID",
            extracted_name="John Doe",
            extracted_id_number="DL-123",
            tampering_score=0,
            face_match_score=90,
            risk_score=75,
            verdict="REJECTED",
            checkpoint_location="Petrapole-Benapole Crossing",
            officer_email="officer.petrapole@mha.gov.in",
            reason="REJECTED: DOCUMENT TYPE MISMATCH: Selected NATIONAL_ID but detected DRIVING_LICENSE",
        )
        db.add(v_rej)
        await db.commit()
        await db.refresh(v_rej)

        alert_rej = await create_alert_for_verification(
            db=db,
            verification=v_rej,
            validation_result=ValidationResult(
                format_valid=False,
                expiry_valid=True,
                issues=["DOCUMENT TYPE MISMATCH: Selected NATIONAL_ID but detected DRIVING_LICENSE"],
            ),
        )

        assert alert_rej is not None
        assert alert_rej.severity in ("HIGH", "CRITICAL")
        assert "DOCUMENT TYPE MISMATCH" in alert_rej.message


@pytest.mark.asyncio
async def test_alert_indicators_include_tampering_and_face_mismatch():
    """
    Test 4: Alert details include clear forensic indicators with scores.
    """
    async with async_session_maker() as db:
        v = Verification(
            filename="tampered_face.jpg",
            document_type="PASSPORT",
            extracted_name="Target Specimen",
            extracted_id_number="P7654321",
            tampering_score=78,
            face_match_score=35,
            risk_score=88,
            verdict="FAKE",
            checkpoint_location="Delhi HQ",
            officer_email="officer@mha.gov.in",
        )
        db.add(v)
        await db.commit()
        await db.refresh(v)

        alert = await create_alert_for_verification(
            db=db,
            verification=v,
            validation_result=ValidationResult(format_valid=True, expiry_valid=True, issues=[]),
        )

        assert alert is not None
        indicators = json.loads(alert.details_json or "[]")
        assert any("facial mismatch" in i.lower() or "35%" in i for i in indicators)
        assert any("tampering" in i.lower() or "78" in i for i in indicators)


def test_supervisor_can_fetch_alerts_and_details():
    """
    Test 5 & 6: Supervisor can fetch alert list and detail via API.
    """
    sup_token = get_token("supervisor.delhi@mha.gov.in", "SUPERVISOR")
    headers = {"Authorization": f"Bearer {sup_token}"}

    with TestClient(app) as client:
        # Fetch alerts list
        resp = client.get("/alerts", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert "unreviewed_count" in data

        if data["items"]:
            first_id = data["items"][0]["id"]
            detail_resp = client.get(f"/alerts/{first_id}", headers=headers)
            assert detail_resp.status_code == 200
            detail = detail_resp.json()
            assert detail["id"] == first_id
            assert "severity" in detail
            assert "status" in detail


def test_officer_cannot_review_or_resolve_alerts_rbac():
    """
    Test 7: Officers receive 403 Forbidden when attempting supervisor-only review.
    """
    officer_token = get_token("officer.attari@mha.gov.in", "OFFICER")
    headers = {"Authorization": f"Bearer {officer_token}"}

    with TestClient(app) as client:
        # Get an alert ID first
        list_resp = client.get("/alerts", headers=headers)
        assert list_resp.status_code == 200
        items = list_resp.json().get("items", [])
        alert_id = items[0]["id"] if items else 1

        # Officer attempts review action -> must receive 403 Forbidden
        review_resp = client.patch(
            f"/alerts/{alert_id}/review",
            headers=headers,
            json={"status": "RESOLVED", "notes": "Officer attempting unauthorized resolve"},
        )
        assert review_resp.status_code == 403
        assert "Supervisor access required" in review_resp.json().get("detail", "")


def test_unauthenticated_user_rejected_on_protected_endpoints():
    """
    Test 8: Unauthenticated requests to /alerts return 401.
    """
    with TestClient(app) as client:
        resp = client.get("/alerts")
        assert resp.status_code == 401

        resp_rev = client.patch("/alerts/1/review", json={"status": "RESOLVED"})
        assert resp_rev.status_code == 401


def test_supervisor_review_workflow_and_verification_preservation():
    """
    Test 9, 10, 11, 12, 13:
    Supervisor can mark reviewed, resolve, add notes.
    Review records reviewer email + timestamp.
    Original AI verification record & scores remain unaltered.
    """
    sup_token = get_token("supervisor.delhi@mha.gov.in", "SUPERVISOR")
    headers = {"Authorization": f"Bearer {sup_token}"}

    with TestClient(app) as client:
        list_resp = client.get("/alerts", headers=headers)
        items = list_resp.json().get("items", [])
        if not items:
            pytest.skip("No alerts available in DB for review test")

        alert = items[0]
        alert_id = alert["id"]
        ver_id = alert.get("verification_id")

        # 1. Review action
        review_payload = {
            "status": "RESOLVED",
            "notes": "Secondary forensic manual inspection completed. Concurrence granted.",
        }
        res = client.patch(f"/alerts/{alert_id}/review", headers=headers, json=review_payload)
        assert res.status_code == 200
        updated = res.json()

        assert updated["status"] == "RESOLVED"
        assert updated["reviewed_by"] == "supervisor.delhi@mha.gov.in"
        assert updated["reviewed_at"] is not None
        assert updated["resolved_at"] is not None
        assert "Secondary forensic manual inspection completed" in updated["review_notes"]

        # 2. Check that original Verification record is completely intact
        if ver_id:
            ver_resp = client.get(f"/verification/{ver_id}", headers=headers)
            assert ver_resp.status_code == 200
            ver_data = ver_resp.json()
            # Original AI scores and verdict must not be modified by supervisor review
            assert ver_data["verdict"] == alert["verdict"]
            assert ver_data["risk_score"] == alert["risk_score"]
            assert ver_data["tampering_score"] == alert["tampering_score"]
