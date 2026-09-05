"""
Unit Tests for SIH26188 Document Verification, MRZ, Risk Score & Tampering

Tests:
1. MRZ checksum math (valid/invalid TD3 passport lines)
2. Risk score weighted computation & formula capping
3. Strict verdict hard-gate derivation
4. Standalone document validation (format, expiry, blacklist)
5. Document validation fast-fail gate on building sketch / non-document
6. Tampering service ELA and palette heatmap base64 output
"""

import unittest
import os
import tempfile
import asyncio
from PIL import Image, ImageDraw

from app.utils.verdict import compute_verdict, compute_risk_score, generate_security_checks
from app.services.document_validation import validate_mrz_td3, validate_document, compute_mrz_check_digit
from app.services.document_validator import validate_identity_document
from app.services.tampering import detect_tampering, run_ela_analysis


class TestMRZChecksumMath(unittest.TestCase):
    """Test ICAO 9303 TD3 MRZ check digit algorithm."""

    def test_mrz_check_digit_calculation(self):
        """Test single field check digit algorithm (weights 7, 3, 1)."""
        # "A1234567" -> 7*10 + 3*1 + 1*2 + 7*3 + 3*4 + 1*5 + 7*6 + 3*7 = 70+3+2+21+12+5+42+21 = 176 => 176 mod 10 = 6
        check = compute_mrz_check_digit("A1234567")
        self.assertEqual(check, 6)

    def _make_test_td3_line2(self, passport_num: str, nationality: str, dob_mrz: str, gender: str, exp_mrz: str) -> str:
        """Build a syntactically valid 44-char TD3 MRZ line 2 for testing."""
        from app.services.document_validation import compute_mrz_check_digit
        pn = (passport_num.upper() + "<<<<<<<<<")[:9]
        pn_c = str(compute_mrz_check_digit(pn))
        nat = (nationality.upper() + "<<<")[:3]
        dob = (dob_mrz + "000000")[:6]
        dob_c = str(compute_mrz_check_digit(dob))
        sex = gender[0].upper() if gender else "<"
        exp = (exp_mrz + "000000")[:6]
        exp_c = str(compute_mrz_check_digit(exp))
        pers = "<<<<<<<<<<<<<<"
        pers_c = str(compute_mrz_check_digit(pers))
        partial = pn + pn_c + nat + dob + dob_c + sex + exp + exp_c + pers + pers_c
        comp_data = partial[0:10] + partial[13:20] + partial[21:43]
        comp_c = str(compute_mrz_check_digit(comp_data))
        return partial + comp_c

    def test_valid_td3_mrz_line_passes(self):
        """Test complete 44-character TD3 line 2 validation with correct check digits."""
        line2 = self._make_test_td3_line2("A1234567", "IND", "900815", "M", "290814")
        is_valid, issues = validate_mrz_td3("", line2)
        self.assertTrue(is_valid, f"Expected MRZ to pass, got issues: {issues}")

    def test_invalid_mrz_check_digit_fails(self):
        """Test corrupted check digit in MRZ line 2."""
        line2 = self._make_test_td3_line2("A1234567", "IND", "900815", "M", "290814")
        # Corrupt single character
        corrupted_line2 = line2[:19] + "0" + line2[20:]
        is_valid, issues = validate_mrz_td3("", corrupted_line2)
        self.assertFalse(is_valid)

class TestRiskScoreAndVerdict(unittest.TestCase):
    """Test primary risk_score weighted formula and strict verdict gates."""

    def test_risk_score_calculation(self):
        """Test risk_score formula: tampering*0.4 + (100-face)*0.3 + issues*10."""
        # tampering=20 (20*0.4=8), face_match=90 ((100-90)*0.3=3), issues=1 (1*10=10) => total = 21
        score = compute_risk_score(tampering_score=20, face_match_score=90, validation_issues_count=1)
        self.assertEqual(score, 21)

    def test_risk_score_capped_at_100(self):
        """High tampering, zero face match, and multiple issues cap at 100."""
        score = compute_risk_score(tampering_score=100, face_match_score=0, validation_issues_count=5)
        self.assertEqual(score, 100)

    def test_low_face_match_hard_gate_yields_fake(self):
        """Face match score < 50% must yield FAKE regardless of low tampering."""
        risk = compute_risk_score(tampering_score=5, face_match_score=40, validation_issues_count=0)
        verdict = compute_verdict(risk_score=risk, tampering_score=5, face_match_score=40)
        self.assertEqual(verdict, "FAKE")

    def test_high_tampering_hard_gate_yields_fake(self):
        """Tampering score > 70 must yield FAKE."""
        risk = compute_risk_score(tampering_score=85, face_match_score=95, validation_issues_count=0)
        verdict = compute_verdict(risk_score=risk, tampering_score=85, face_match_score=95)
        self.assertEqual(verdict, "FAKE")

    def test_blacklist_hit_yields_fake(self):
        """Blacklist hit in validation issues must yield FAKE."""
        val = validate_document("PASSPORT", {"passport_number": "A1234567"})  # Blacklisted number
        self.assertTrue(any("BLACKLIST" in issue for issue in val.issues))
        risk = compute_risk_score(tampering_score=10, face_match_score=90, validation_issues_count=len(val.issues))
        verdict = compute_verdict(risk_score=risk, tampering_score=10, face_match_score=90, validation=val)
        self.assertEqual(verdict, "FAKE")

    def test_safe_scores_yields_genuine(self):
        """Low risk score and all gates clear yields GENUINE."""
        risk = compute_risk_score(tampering_score=5, face_match_score=95, validation_issues_count=0)
        verdict = compute_verdict(risk_score=risk, tampering_score=5, face_match_score=95)
        self.assertEqual(verdict, "GENUINE")


class TestDocumentValidationGate(unittest.TestCase):
    """Test fast-fail document validation gate."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_building_sketch_rejected(self):
        """Unrelated building sketch or non-document image must fail document validation."""
        sketch_path = os.path.join(self.temp_dir.name, "building_sketch.jpg")
        img = Image.new("RGB", (600, 400), color=(250, 250, 250))
        draw = ImageDraw.Draw(img)
        draw.line([(50, 350), (50, 100), (300, 50), (550, 100), (550, 350)], fill=(30, 30, 30), width=2)
        draw.line([(50, 350), (550, 350)], fill=(30, 30, 30), width=2)
        img.save(sketch_path)

        is_valid, reason = validate_identity_document(sketch_path)
        self.assertFalse(is_valid)
        self.assertIsNotNone(reason)


class TestTamperingDetectionService(unittest.TestCase):
    """Test tampering detection algorithms (ELA, copy-move, metadata, heatmap)."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_tampering_service_generates_palette_heatmap(self):
        """Tampering detection returns composite score, regions, and base64 heatmap."""
        img_path = os.path.join(self.temp_dir.name, "test_tamper_doc.jpg")
        img = Image.new("RGB", (700, 440), color=(248, 245, 243))
        draw = ImageDraw.Draw(img)
        draw.rectangle([10, 10, 690, 70], fill=(11, 41, 37))
        img.save(img_path)

        result = asyncio.run(detect_tampering(img_path))
        self.assertIsInstance(result.score, int)
        self.assertTrue(result.heatmap_base64.startswith("data:image/png;base64,"))


if __name__ == "__main__":
    unittest.main()
