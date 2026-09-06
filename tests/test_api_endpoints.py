"""
Integration Tests for Authentication, /verify-document, and /analyze-tampering Endpoints

Validates HTTP responses for:
1. POST /auth/login with demo officer credentials -> returns 200 with JWT access_token
2. Unauthenticated POST /verify-document -> returns 401 Unauthorized
3. Authenticated POST /verify-document -> returns 200 with officer_email in payload
4. Building sketch / invalid document upload -> returns verdict="REJECTED"
5. Passport document_type upload -> returns Passport extracted_fields shape and validation
"""

import unittest
from unittest.mock import patch
import io
from PIL import Image, ImageDraw
from fastapi.testclient import TestClient
from app.main import app
from app.auth import create_access_token


def make_sketch_bytes() -> bytes:
    img = Image.new("RGB", (500, 350), color=(250, 250, 250))
    draw = ImageDraw.Draw(img)
    draw.line([(50, 300), (50, 100), (250, 50), (450, 100), (450, 300)], fill=(20, 20, 20), width=2)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def make_valid_id_bytes() -> bytes:
    img = Image.new("RGB", (700, 440), color=(248, 245, 240))
    draw = ImageDraw.Draw(img)
    draw.rectangle([10, 10, 690, 70], fill=(11, 41, 37))
    for y in range(90, 320, 20):
        draw.line([(200, y), (600, y)], fill=(39, 33, 43), width=2)
    draw.rectangle([30, 90, 180, 290], fill=(215, 175, 145), outline=(11, 41, 37), width=2)
    draw.rectangle([20, 340, 680, 420], fill=(235, 230, 225))
    for y in [360, 390]:
        draw.line([(30, y), (670, y)], fill=(30, 30, 30), width=2)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def get_auth_headers(email="officer.attari@mha.gov.in", role="OFFICER", checkpoint="Attari-Wagah Border") -> dict:
    token = create_access_token({"sub": email, "role": role, "checkpoint_location": checkpoint})
    return {"Authorization": f"Bearer {token}"}


class TestVerificationAndTamperingAPI(unittest.TestCase):
    def test_unauthenticated_verify_document_returns_401(self):
        """Unauthenticated request to protected endpoint /verify-document must return 401."""
        sketch_bytes = make_sketch_bytes()
        files = {"file": ("building_sketch.jpg", sketch_bytes, "image/jpeg")}

        with TestClient(app) as client:
            response = client.post("/verify-document", files=files)

        self.assertEqual(response.status_code, 401)

    def test_demo_login_endpoint(self):
        """POST /auth/login with valid demo credentials returns token and UserDTO."""
        with TestClient(app) as client:
            response = client.post(
                "/auth/login",
                json={"email": "officer.attari@mha.gov.in", "password": "Password@123"},
            )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("success"))
        self.assertIn("access_token", data)
        self.assertEqual(data.get("user", {}).get("email"), "officer.attari@mha.gov.in")
        self.assertEqual(data.get("user", {}).get("role"), "OFFICER")

    def test_upload_building_sketch_returns_rejected_verdict(self):
        """Uploading building sketch with valid JWT returns verdict="REJECTED"."""
        sketch_bytes = make_sketch_bytes()
        files = {"file": ("building_sketch.jpg", sketch_bytes, "image/jpeg")}
        headers = get_auth_headers()

        with TestClient(app) as client:
            response = client.post("/verify-document", files=files, headers=headers)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("verdict"), "REJECTED")
        self.assertEqual(data.get("officer_email"), "officer.attari@mha.gov.in")

    def test_upload_valid_id_returns_structured_verification(self):
        """Uploading valid ID returns structured response with officer_email logged."""
        id_bytes = make_valid_id_bytes()
        files = {"file": ("test_id_license.jpg", id_bytes, "image/jpeg")}
        data_form = {"document_type": "DRIVING_LICENSE"}
        headers = get_auth_headers()

        with TestClient(app) as client:
            response = client.post("/verify-document", files=files, data=data_form, headers=headers)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("verdict", data)
        self.assertIn("risk_score", data)
        self.assertEqual(data.get("officer_email"), "officer.attari@mha.gov.in")

    def test_passport_verification(self):
        """Uploading Passport returns passport specific fields and MRZ status."""
        id_bytes = make_valid_id_bytes()
        files = {"file": ("passport.jpg", id_bytes, "image/jpeg")}
        data_form = {"document_type": "PASSPORT"}
        headers = get_auth_headers()

        mock_res = {
            "fields": {
                "name": "Rajesh Kumar",
                "passport_number": "A1234567",
                "nationality": "IND",
                "dob": "1990-08-15",
                "date_of_expiry": "2029-08-14",
                "gender": "M",
            },
            "confidence": {"name": 0.95, "passport_number": 0.98},
            "mrz_line1": "P<IND<<RAJESH<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<",
            "mrz_line2": "A1234567<6IND9008159M2908146<<<<<<<<<<<<<<<02",
            "mrz_result": None,
            "ocr_lines": [],
            "raw_text": "PASSPORT REPUBLIC OF INDIA A1234567",
            "detected_document_type": "passport",
            "ocr_success": True,
        }

        with patch("app.services.verification.extract_fields", return_value=mock_res):
            with TestClient(app) as client:
                response = client.post("/verify-document", files=files, data=data_form, headers=headers)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("document_type"), "PASSPORT")
        fields = data.get("extracted_fields", {})
        self.assertIn("passport_number", fields)

    def test_analyze_tampering_endpoint(self):
        """POST /analyze-tampering accepts an image and returns composite score, regions, and base64 heatmap."""
        id_bytes = make_valid_id_bytes()
        files = {"file": ("sample_id_tamper.jpg", id_bytes, "image/jpeg")}
        headers = get_auth_headers()

        with TestClient(app) as client:
            response = client.post("/analyze-tampering", files=files, headers=headers)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("tampering_score", data)
        self.assertIn("heatmap_image_base64", data)

    def test_export_dossier_endpoint(self):
        """GET /verification/{id}/export returns 200 with structured case dossier JSON."""
        headers = get_auth_headers()
        with TestClient(app) as client:
            # First, fetch history to get an existing ID
            hist_res = client.get("/history", headers=headers)
            if hist_res.status_code == 200 and hist_res.json().get("items"):
                rec_id = hist_res.json()["items"][0]["id"]
                export_res = client.get(f"/verification/{rec_id}/export?format=json", headers=headers)
                self.assertEqual(export_res.status_code, 200)
                dossier = export_res.json()
                self.assertIn("case_number", dossier)
                self.assertIn("verdict", dossier)
                self.assertIn("audit_authority", dossier)

                # Test CSV export format
                export_csv = client.get(f"/verification/{rec_id}/export?format=csv", headers=headers)
                self.assertEqual(export_csv.status_code, 200)
                self.assertIn("text/csv", export_csv.headers["content-type"])


if __name__ == "__main__":
    unittest.main()
