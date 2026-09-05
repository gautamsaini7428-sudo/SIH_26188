"""Tests for the standalone /ocr and /health endpoints."""
import pytest
import io
from PIL import Image, ImageDraw
from fastapi.testclient import TestClient
from app.main import app
from app.auth import create_access_token


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def auth_headers():
    token = create_access_token({"sub": "officer.attari@mha.gov.in", "role": "OFFICER", "checkpoint_location": "Attari-Wagah Border"})
    return {"Authorization": f"Bearer {token}"}


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "engine" in data
    assert isinstance(data["gpu_available"], bool)


def test_ocr_endpoint_unauthenticated(client):
    resp = client.post("/ocr")
    assert resp.status_code == 401


def test_ocr_endpoint_requires_file(client, auth_headers):
    resp = client.post("/ocr", headers=auth_headers)
    assert resp.status_code in (400, 415, 422)


def test_ocr_endpoint_empty_file(client, auth_headers):
    resp = client.post("/ocr", files={"file": ("empty.bin", b"", "application/octet-stream")}, headers=auth_headers)
    assert resp.status_code == 400


def test_ocr_endpoint_invalid_image(client, auth_headers):
    resp = client.post("/ocr", files={"file": ("bad.jpg", b"NOTANIMAGE", "image/jpeg")}, headers=auth_headers)
    assert resp.status_code in (400, 500)


def test_ocr_endpoint_valid_image(client, auth_headers):
    img = Image.new("RGB", (600, 300), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((20, 20), "PASSPORT", fill=(0, 0, 0))
    draw.text((20, 60), "REPUBLIC OF UTO", fill=(0, 0, 0))
    draw.text((20, 100), "Name: Anna Eriksson", fill=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    img_bytes = buf.getvalue()

    resp = client.post("/ocr", files={"file": ("passport_sample.jpg", img_bytes, "image/jpeg")}, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "raw_text" in data
    assert "lines" in data
    assert "fields" in data
    assert "mrz" in data
    assert "document_type" in data

