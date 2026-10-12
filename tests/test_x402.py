"""Unit test suite for x402 Bazaar Protocol Engine."""
import base64
import json
import unittest
from core.x402.server import X402BazaarServer


class TestX402BazaarEngine(unittest.TestCase):
    """Verifies RFC HTTP 402 challenge issuance, settlement, and replay defense."""

    def setUp(self):
        self.server = X402BazaarServer(treasury_principal="qicp-treasury-cai")

    def test_challenge_issuance_and_settlement(self):
        chal = self.server.create_challenge(service_id="ai:policy-audit", amount_e8s=150_000)
        self.assertEqual(chal.amount_e8s, 150_000)

        # Valid client receipt
        client_receipt = {
            "version": "x402:v1:icp",
            "service_id": "ai:policy-audit",
            "nonce": chal.nonce,
            "block_index": 77481,
            "payer_principal": "rdmx6-jaaaa-aaaaa-aaadq-cai",
            "amount_e8s": 150_000,
        }
        b64_receipt = base64.b64encode(json.dumps(client_receipt).encode()).decode()

        ok, msg, audit = self.server.verify_payment_receipt(b64_receipt)
        self.assertTrue(ok, f"Verification failed: {msg}")
        self.assertEqual(audit["burned_e8s"], 75_000)
        self.assertEqual(audit["treasury_e8s"], 75_000)

    def test_replay_attack_prevention(self):
        chal = self.server.create_challenge(service_id="ai:policy-audit", amount_e8s=100_000)
        client_receipt = {
            "version": "x402:v1:icp",
            "service_id": "ai:policy-audit",
            "nonce": chal.nonce,
            "block_index": 88312,
            "payer_principal": "rdmx6-jaaaa-aaaaa-aaadq-cai",
            "amount_e8s": 100_000,
        }
        b64_receipt = base64.b64encode(json.dumps(client_receipt).encode()).decode()

        # First verification succeeds
        ok1, _, _ = self.server.verify_payment_receipt(b64_receipt)
        self.assertTrue(ok1)

        # Replay attempt fails closed
        ok2, msg2, _ = self.server.verify_payment_receipt(b64_receipt)
        self.assertFalse(ok2)
        self.assertIn("replay", msg2.lower())


if __name__ == "__main__":
    unittest.main()
