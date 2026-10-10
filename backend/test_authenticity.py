import unittest
from fastapi.testclient import TestClient
from app.services.authenticity_engine import brand_authenticity_engine, WEIGHTS
from app.main import app

class TestBrandAuthenticityEngine(unittest.TestCase):
    def test_weights_sum(self):
        total = sum(WEIGHTS.values())
        self.assertAlmostEqual(total, 100.0, places=1, msg=f"Weights must sum to 100%, got {total}%")

    def test_live_website_analysis_example(self):
        brand_doc = {
            "brand_name": "Example Corp",
            "official_website": "https://example.com",
            "official_domain": "example.com"
        }
        res = brand_authenticity_engine.verify_website("https://example.com", brand_doc)
        self.assertEqual(res["candidate_domain"], "example.com")
        self.assertTrue(res["is_official"])
        self.assertEqual(res["risk"]["score"], 0.0)
        self.assertEqual(res["risk"]["level"], "TRUSTED")
        self.assertEqual(res["live_site_data"]["status_code"], 200)
        self.assertIn("Example Domain", res["live_site_data"]["title"])

    def test_unreachable_domain_returns_error(self):
        res = brand_authenticity_engine.verify_website("https://this-is-a-completely-fake-unregistered-domain-999888.org")
        self.assertFalse(res["success"])
        self.assertIn("Unable to analyze website URL", res["error"])

    def test_trust_score(self):
        report = brand_authenticity_engine.compute_brand_trust_score({"name": "Nike"})
        self.assertGreaterEqual(report["digital_trust_score"], 85)
        self.assertIn("breakdown", report)
        self.assertGreaterEqual(len(report["breakdown"]), 5)


class TestAuthenticityAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_api_verify_brand(self):
        resp = self.client.post("/api/authenticity/verify-brand", json={
            "brand_name": "Nike",
            "official_website": "https://nike.com",
            "official_domain": "nike.com",
            "instagram": "@nike",
            "official_logo": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=200"
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["brand_name"], "Nike")
        self.assertIn("trust_report", data)

    def test_api_analyze_website_live(self):
        resp = self.client.post("/api/authenticity/analyze-website", json={
            "url": "https://example.com"
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["candidate_domain"], "example.com")
        self.assertEqual(data["live_site_data"]["status_code"], 200)
        self.assertIn("Example Domain", data["live_site_data"]["title"])
        # Verify no hardcoded demo leak
        self.assertNotIn("nike", data["visual_ai_analysis"]["candidate_screenshot"].lower())
        self.assertNotIn("blackberrys", data["visual_ai_analysis"]["candidate_screenshot"].lower())

    def test_api_analyze_website_unreachable_error(self):
        resp = self.client.post("/api/authenticity/analyze-website", json={
            "url": "https://this-is-a-completely-fake-unregistered-domain-999888.org"
        })
        self.assertEqual(resp.status_code, 400)
        data = resp.json()
        self.assertIn("Unable to analyze website URL", data.get("detail", ""))

    def test_api_verify_image_real(self):
        github_logo = "https://github.githubassets.com/favicons/favicon.png"
        resp = self.client.post("/api/authenticity/verify-image", json={
            "candidate_image_url": github_logo,
            "official_image_url": github_logo
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["similarity_pct"], 100.0)
        self.assertEqual(data["match_status"], "AUTHENTIC")
        self.assertEqual(data["risk_severity"], "NORMAL")
        self.assertEqual(data["hamming_distance"], 0)

    def test_api_override_and_alerts(self):
        # Override
        resp = self.client.post("/api/authenticity/override-verdict", json={
            "candidate_domain": "nike-support-login.com",
            "override_verdict": "Confirmed Threat",
            "notes": "Verified malicious spear-phishing domain",
            "analyst": "SecOps Lead"
        })
        self.assertEqual(resp.status_code, 200)
        
        # Alerts
        resp2 = self.client.get("/api/authenticity/alerts")
        self.assertEqual(resp2.status_code, 200)
        data2 = resp2.json()
        self.assertTrue(data2["success"])
        self.assertGreater(data2["total"], 0)


if __name__ == "__main__":
    unittest.main()
