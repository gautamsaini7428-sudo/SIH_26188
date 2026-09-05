"""
End-to-End Test for /verify-document and /audit-log
SIH26188
"""
import os
import sys
import io
import json
import asyncio
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

# Ensure repo root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app
from app.auth import create_access_token
from app.services.face_match import match_faces, match_faces_detailed

def create_synthetic_id_card(filename: str, name: str, id_num: str, photo_np: np.ndarray) -> str:
    """Create a structured ID document image with embedded photo and text."""
    # Base ID card: 700x450
    card = np.full((450, 700, 3), 245, dtype=np.uint8)
    
    # Header bar
    cv2.rectangle(card, (0, 0), (700, 70), (37, 41, 11), -1) # Dark green
    cv2.putText(card, "NATIONAL IDENTITY CARD", (140, 45), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
    
    # Text fields
    cv2.putText(card, f"NAME: {name}", (250, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (30, 30, 30), 2)
    cv2.putText(card, f"ID NO: {id_num}", (250, 190), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (30, 30, 30), 2)
    cv2.putText(card, "DOB: 1992-05-14", (250, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (30, 30, 30), 2)
    cv2.putText(card, "NATIONALITY: IND", (250, 290), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (30, 30, 30), 2)
    
    # Bottom security band
    cv2.rectangle(card, (0, 380), (700, 450), (220, 220, 220), -1)
    cv2.putText(card, f"IDIND{id_num}<<<<<<<<<<<<<<<<<<", (30, 420), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (50, 50, 50), 1)

    # Embed face photo in (30, 100, 180, 240)
    resized_photo = cv2.resize(photo_np, (180, 240))
    card[100:340, 30:210] = resized_photo
    cv2.rectangle(card, (28, 98), (212, 342), (50, 50, 50), 2)
    
    os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)
    cv2.imwrite(filename, card)
    return filename

def create_synthetic_selfie(filename: str, photo_np: np.ndarray, add_variation: bool = False) -> str:
    """Create a live selfie image with natural dimensions and optional subtle lighting variation."""
    selfie = photo_np.copy()
    if add_variation:
        # Slight brightness / angle adjustment to simulate real live capture
        selfie = cv2.convertScaleAbs(selfie, alpha=1.05, beta=10)
    
    os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)
    cv2.imwrite(filename, selfie)
    return filename

def generate_face_canvas(seed: int = 42) -> np.ndarray:
    """Generate a 250x250 face image with distinct features based on seed."""
    np.random.seed(seed)
    face = np.full((300, 300, 3), 200, dtype=np.uint8) # Neutral skin/bg
    
    # Head contour (oval)
    skin_tone = (160 + (seed * 17) % 50, 180 + (seed * 13) % 40, 225)
    cv2.ellipse(face, (150, 150), (95, 125), 0, 0, 360, skin_tone, -1)
    
    # Eyes
    eye_offset = (seed * 3) % 10
    cv2.circle(face, (115 + eye_offset, 130), 14, (255, 255, 255), -1)
    cv2.circle(face, (185 - eye_offset, 130), 14, (255, 255, 255), -1)
    pupil_color = ((seed * 30) % 60, (seed * 20) % 50, 30)
    cv2.circle(face, (115 + eye_offset, 130), 7, pupil_color, -1)
    cv2.circle(face, (185 - eye_offset, 130), 7, pupil_color, -1)
    
    # Eyebrows
    cv2.line(face, (95, 110), (135, 112), (30, 20, 10), 4)
    cv2.line(face, (165, 112), (205, 110), (30, 20, 10), 4)
    
    # Nose
    cv2.line(face, (150, 135), (145, 175), (140, 150, 180), 3)
    cv2.line(face, (145, 175), (158, 175), (140, 150, 180), 3)
    
    # Mouth
    cv2.ellipse(face, (150, 215), (28 + seed % 8, 12), 0, 0, 180, (80, 80, 180), -1)
    
    # Hair
    cv2.ellipse(face, (150, 75), (105, 55), 0, 180, 360, (25, 20, 15), -1)
    return face

def run_e2e_verification():
    os.makedirs("test_samples", exist_ok=True)
    
    # Create Face A and Face B
    face_a = generate_face_canvas(seed=101)
    face_b = generate_face_canvas(seed=505)
    
    # Pair 1: Matching Pair (Face A on ID + Face A Selfie with subtle lighting change)
    id_1_path = create_synthetic_id_card("test_samples/id_case_1.jpg", "AARAV SHARMA", "DL-94102941", face_a)
    selfie_1_path = create_synthetic_selfie("test_samples/selfie_case_1.jpg", face_a, add_variation=True)
    
    # Pair 2: Mismatched / Different Individual (Face B on ID + Face A as selfie)
    id_2_path = create_synthetic_id_card("test_samples/id_case_2.jpg", "VIKRAM MALHOTRA", "DL-88204910", face_b)
    selfie_2_path = create_synthetic_selfie("test_samples/selfie_case_2.jpg", face_a, add_variation=False)

    token = create_access_token({"sub": "officer.attari@mha.gov.in", "role": "OFFICER", "checkpoint_location": "Attari-Wagah Border"})
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n" + "="*70)
    print("RUNNING END-TO-END VERIFICATION DEMO (2 DISTINCT TEST RUNS)")
    print("="*70)
    
    with TestClient(app) as client:
        # Run 1: Matching Face Pair
        print("\n[TEST RUN 1] - Matching ID Document + Live Selfie")
        with open(id_1_path, "rb") as f_id, open(selfie_1_path, "rb") as f_selfie:
            res1 = client.post(
                "/verify-document",
                files={
                    "file": ("id_aarav_sharma.jpg", f_id.read(), "image/jpeg"),
                    "selfie": ("selfie_aarav.jpg", f_selfie.read(), "image/jpeg"),
                },
                data={"document_type": "DRIVING_LICENSE"},
                headers=headers,
            )
        
        data1 = res1.json()
        print(f"  HTTP Status: {res1.status_code}")
        print(f"  Case Number: {data1.get('case_number')}")
        print(f"  Verdict: {data1.get('verdict')}")
        print(f"  Risk Score: {data1.get('risk_score')}/100")
        print(f"  Tampering Score: {data1.get('tampering_score')}/100")
        print(f"  Face Match Score: {data1.get('face_match_score')}%")
        print(f"  Reason: {data1.get('reason')}")
        
        # Run 2: Different Face Pair
        print("\n[TEST RUN 2] - Different Individual ID vs Selfie (Mismatch Scenario)")
        with open(id_2_path, "rb") as f_id, open(selfie_2_path, "rb") as f_selfie:
            res2 = client.post(
                "/verify-document",
                files={
                    "file": ("id_vikram_malhotra.jpg", f_id.read(), "image/jpeg"),
                    "selfie": ("selfie_unmatched.jpg", f_selfie.read(), "image/jpeg"),
                },
                data={"document_type": "DRIVING_LICENSE"},
                headers=headers,
            )
        
        data2 = res2.json()
        print(f"  HTTP Status: {res2.status_code}")
        print(f"  Case Number: {data2.get('case_number')}")
        print(f"  Verdict: {data2.get('verdict')}")
        print(f"  Risk Score: {data2.get('risk_score')}/100")
        print(f"  Tampering Score: {data2.get('tampering_score')}/100")
        print(f"  Face Match Score: {data2.get('face_match_score')}%")
        print(f"  Reason: {data2.get('reason')}")
        
        print("\n" + "="*70)
        print("TESTING AUDIT LOG ENDPOINTS (GET /audit-log and GET /audit-log/verify)")
        print("="*70)
        
        # Audit Log Read
        res_log = client.get("/audit-log")
        records = res_log.json()
        print(f"  Total Audit Log Records: {len(records)}")
        if records:
            last_record = records[-1]
            print(f"  Last Entry Block #{last_record.get('index')}:")
            print(f"    Hash: {last_record.get('hash')}")
            print(f"    Prev Hash: {last_record.get('previous_hash')}")
            print(f"    Payload: {last_record.get('record')}")
            
        # Audit Log Integrity Verification
        res_verify = client.get("/audit-log/verify")
        verify_data = res_verify.json()
        print(f"\n  Audit Chain Integrity Check:")
        print(f"    Valid: {verify_data.get('valid')}")
        print(f"    Entries Checked: {verify_data.get('entries_checked')}")
        print(f"    Tampered Index: {verify_data.get('tampered_index')}")
        print(f"    Reason: {verify_data.get('reason')}")
        
        assert res1.status_code == 200
        assert res2.status_code == 200
        assert data1.get('face_match_score') != data2.get('face_match_score'), "Scores must be dynamic and distinct!"
        assert verify_data.get('valid') is True, "Audit chain integrity must be valid!"
        print("\n>>> ALL END-TO-END CRITERIA VERIFIED SUCCESSFULLY! <<<")

if __name__ == "__main__":
    run_e2e_verification()
