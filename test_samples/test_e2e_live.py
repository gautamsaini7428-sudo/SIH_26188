"""
Live End-to-End Test for /verify-document and /audit-log
SIH26188
"""
import os
import sys
import io
import cv2
import numpy as np
from PIL import Image, ImageDraw

# Ensure repo root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app
from app.auth import create_access_token

def make_test_document_image(doc_name="test_id_license.jpg", face_color=(215, 175, 145)) -> bytes:
    img = Image.new("RGB", (700, 440), color=(248, 245, 240))
    draw = ImageDraw.Draw(img)
    # Header
    draw.rectangle([10, 10, 690, 70], fill=(11, 41, 37))
    # Lines representing text
    for y in range(90, 320, 20):
        draw.line([(200, y), (600, y)], fill=(39, 33, 43), width=2)
    # Face portrait area
    draw.rectangle([30, 90, 180, 290], fill=face_color, outline=(11, 41, 37), width=2)
    # Eyes and mouth features for facial representation
    draw.rectangle([60, 140, 80, 155], fill=(40, 30, 25))
    draw.rectangle([130, 140, 150, 155], fill=(40, 30, 25))
    draw.rectangle([80, 220, 130, 235], fill=(170, 70, 70))
    # Security band & MRZ
    draw.rectangle([20, 340, 680, 420], fill=(235, 230, 225))
    for y in [360, 390]:
        draw.line([(30, y), (670, y)], fill=(30, 30, 30), width=2)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

def make_test_selfie_image(selfie_name="test_selfie.jpg", face_color=(215, 175, 145), variant_offset=0) -> bytes:
    # 250x250 portrait capture
    r = min(255, max(0, face_color[0] + variant_offset))
    g = min(255, max(0, face_color[1] - variant_offset // 2))
    b = min(255, max(0, face_color[2] - variant_offset // 3))
    color = (r, g, b)
    
    img = Image.new("RGB", (250, 250), color=(220, 225, 230))
    draw = ImageDraw.Draw(img)
    # Face region
    draw.ellipse([40, 30, 210, 220], fill=color, outline=(80, 60, 50), width=2)
    # Eyes
    draw.ellipse([75, 90, 105, 115], fill=(255, 255, 255))
    draw.ellipse([85, 98, 97, 110], fill=(20, 20, 20))
    draw.ellipse([145, 90, 175, 115], fill=(255, 255, 255))
    draw.ellipse([153, 98, 165, 110], fill=(20, 20, 20))
    # Eyebrows
    draw.line([(70, 80), (110, 80)], fill=(30, 20, 15), width=3)
    draw.line([(140, 80), (180, 80)], fill=(30, 20, 15), width=3)
    # Nose
    draw.line([(125, 110), (120, 150)], fill=(160, 120, 90), width=2)
    draw.line([(120, 150), (135, 150)], fill=(160, 120, 90), width=2)
    # Mouth
    draw.ellipse([100, 175, 150, 195], fill=(180, 70, 70))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

def run_test():
    token = create_access_token({"sub": "officer.attari@mha.gov.in", "role": "OFFICER", "checkpoint_location": "Attari-Wagah Border"})
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n" + "="*75)
    print("DEMO RUN: END-TO-END VERIFICATION WITH REAL ARCFACE & AUDIT HASH-CHAIN")
    print("="*75)
    
    with TestClient(app) as client:
        # TEST RUN 1: Driving License with Matching Live Selfie
        print("\n--> [TEST RUN 1] Driving License Document + Matching Live Selfie")
        doc1_bytes = make_test_document_image("test_id_license_1.jpg", face_color=(215, 175, 145))
        selfie1_bytes = make_test_selfie_image("test_selfie_1.jpg", face_color=(215, 175, 145), variant_offset=0)
        
        res1 = client.post(
            "/verify-document",
            files={
                "file": ("test_id_license_1.jpg", doc1_bytes, "image/jpeg"),
                "selfie": ("test_selfie_1.jpg", selfie1_bytes, "image/jpeg"),
            },
            data={"document_type": "DRIVING_LICENSE"},
            headers=headers,
        )
        
        d1 = res1.json()
        print(f"  Status Code: {res1.status_code}")
        print(f"  Case Number: {d1.get('case_number')}")
        print(f"  Document Type: {d1.get('document_type')}")
        print(f"  Verdict: {d1.get('verdict')}")
        print(f"  Risk Score: {d1.get('risk_score')}/100")
        print(f"  Tampering Score: {d1.get('tampering_score')}/100")
        print(f"  Face Match Score: {d1.get('face_match_score')}%")
        print(f"  Reason: {d1.get('reason')}")
        print(f"  Officer: {d1.get('officer_email')}")
        
        # TEST RUN 2: Passport Document with Alternate Facial Profile / Lighting
        print("\n--> [TEST RUN 2] Passport Document + Alternate Selfie Capture")
        doc2_bytes = make_test_document_image("passport_doc_2.jpg", face_color=(195, 155, 125))
        selfie2_bytes = make_test_selfie_image("passport_selfie_2.jpg", face_color=(195, 155, 125), variant_offset=30)
        
        res2 = client.post(
            "/verify-document",
            files={
                "file": ("passport_doc_2.jpg", doc2_bytes, "image/jpeg"),
                "selfie": ("passport_selfie_2.jpg", selfie2_bytes, "image/jpeg"),
            },
            data={"document_type": "PASSPORT"},
            headers=headers,
        )
        
        d2 = res2.json()
        print(f"  Status Code: {res2.status_code}")
        print(f"  Case Number: {d2.get('case_number')}")
        print(f"  Document Type: {d2.get('document_type')}")
        print(f"  Verdict: {d2.get('verdict')}")
        print(f"  Risk Score: {d2.get('risk_score')}/100")
        print(f"  Tampering Score: {d2.get('tampering_score')}/100")
        print(f"  Face Match Score: {d2.get('face_match_score')}%")
        print(f"  Reason: {d2.get('reason')}")
        print(f"  Officer: {d2.get('officer_email')}")
        
        print("\n" + "="*75)
        print("VERIFYING TAMPER-EVIDENT SHA-256 AUDIT LOG (GET /audit-log & /audit-log/verify)")
        print("="*75)
        
        # Read audit log entries
        res_audit = client.get("/audit-log")
        entries = res_audit.json()
        print(f"  Total Blocks in Hash Chain: {len(entries)}")
        for entry in entries[-2:]:
            rec = entry["record"]
            print(f"  -> Block #{entry['index']}:")
            print(f"     Case ID: {rec['document_id']} | Mapped Verdict: {rec['verdict']} | Tamper: {rec['tampering_score']} | Face: {rec['face_match_score']}%")
            print(f"     Hash:      {entry['hash']}")
            print(f"     Prev Hash: {entry['previous_hash']}")
        
        # Cryptographic chain verification
        res_verify = client.get("/audit-log/verify")
        verify_result = res_verify.json()
        print(f"\n  Cryptographic Chain Integrity Verification:")
        print(f"     Valid:           {verify_result['valid']}")
        print(f"     Entries Checked: {verify_result['entries_checked']}")
        print(f"     Tampered Index:  {verify_result['tampered_index']}")
        print(f"     Status Message:  {verify_result['reason']}")
        
        assert res1.status_code == 200
        assert res2.status_code == 200
        assert verify_result['valid'] is True

if __name__ == "__main__":
    run_test()
