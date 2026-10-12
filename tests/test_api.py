"""Integration test suite for QICP FastAPI backend and gateway."""
import unittest
from fastapi.testclient import TestClient
from backend.main import app


class TestAPIAndGateway(unittest.TestCase):
    """Verifies API routes, streaming limits, x402 interception, and security headers."""

    def setUp(self):
        self.client = TestClient(app)

    def test_health_live_endpoint(self):
        resp = self.client.get("/api/health/live")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "LIVE")

    def test_security_headers_injected(self):
        resp = self.client.get("/api/health/live")
        self.assertEqual(resp.headers.get("x-content-type-options"), "nosniff")
        self.assertEqual(resp.headers.get("x-frame-options"), "DENY")
        self.assertIn("max-age", resp.headers.get("strict-transport-security", ""))

    def test_streaming_request_body_limits(self):
        # 1. Negative Content-Length returns 400
        resp_bad = self.client.post("/api/conway/init", headers={"Content-Length": "-10"}, content=b"{}")
        self.assertEqual(resp_bad.status_code, 400)

        # 2. Oversized payload (> 1 MB) returns 413
        oversized_data = b"X" * (1024 * 1024 + 100)
        resp_oversized = self.client.post("/api/conway/init", content=oversized_data)
        self.assertEqual(resp_oversized.status_code, 413)

    def test_x402_payment_required_challenge(self):
        # Protected endpoint without receipt returns HTTP 402
        resp = self.client.post("/api/ai/inclusion-audit", json={"beneficiary_count": 50})
        self.assertEqual(resp.status_code, 402)
        self.assertIn("WWW-Authenticate", resp.headers)
        self.assertIn("X-Payment-Challenge", resp.headers)
        self.assertIn("Payment Required", resp.json()["detail"])

    def test_multi_crypto_qr_generation(self):
        resp = self.client.post("/api/qr/generate", json={
            "currency": "QICP",
            "recipient_address": "rdmx6-jaaaa-aaaaa-aaadq-cai",
            "amount": 250.0,
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["qr_data_uri"].startswith("data:image/png;base64,"))
        self.assertIn("icp:rdmx6-jaaaa-aaaaa-aaadq-cai", data["payment_uri"])

    def test_proposal_submission_and_retrieval(self):
        sub_resp = self.client.post("/api/proposals/submit", json={
            "title": "Vocational Weaving Collective",
            "category": "Livelihood",
            "target_community": "Moolnivasi Women Union",
            "beneficiary_count": 64,
            "requested_amount_qicp": 300_000.0,
            "description": "Funding handloom weaving training and micro-enterprise capital.",
            "proposer_principal": "rdmx6-jaaaa-aaaaa-aaadq-cai",
        })
        self.assertEqual(sub_resp.status_code, 200)
        prop_id = sub_resp.json()["proposal_id"]

        # Fetch list
        list_resp = self.client.get("/api/proposals/list")
        self.assertEqual(list_resp.status_code, 200)
        self.assertTrue(any(p["proposal_id"] == prop_id for p in list_resp.json()))


if __name__ == "__main__":
    unittest.main()
