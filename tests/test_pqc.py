"""Unit test suite for NIST Post-Quantum Cryptography implementations."""
import hashlib
import unittest
from core.pqc.ml_dsa import MLDSA65KeyPair, HybridPqcSigner
from core.pqc.ml_kem import MLKEM768


class TestPostQuantumCryptography(unittest.TestCase):
    """Verifies NIST FIPS 204 (ML-DSA) and NIST FIPS 203 (ML-KEM) cryptographic math."""

    def test_ml_dsa_65_signature_lifecycle(self):
        pair = MLDSA65KeyPair.generate()
        msg = b"Grant Proposal #001: Moolnivasi Agricultural Collective"
        sig = pair.sign(msg)

        # 1. Valid signature verifies
        self.assertTrue(pair.verify(pair.public_key_bytes, msg, sig))

        # 2. Tampered message fails verification
        tampered_msg = b"Grant Proposal #001: Tampered Recipient"
        self.assertFalse(pair.verify(pair.public_key_bytes, tampered_msg, sig))

        # 3. Wrong public key fails verification
        other_pair = MLDSA65KeyPair.generate()
        self.assertFalse(pair.verify(other_pair.public_key_bytes, msg, sig))

    def test_hybrid_ed25519_pqc_signer(self):
        pair = MLDSA65KeyPair.generate()
        hybrid = HybridPqcSigner(pair)
        msg = b"Treasury Timelock Release: 50,000 QICP to SC/ST Livelihood Union"

        envelope = hybrid.sign_envelope(msg)
        self.assertIn("ed25519_signature_hex", envelope)
        self.assertIn("pqc_signature_hex", envelope)
        self.assertIn("payload_sha256", envelope)

        # Valid envelope
        self.assertTrue(HybridPqcSigner.verify_envelope(msg, envelope))

        # Tampered envelope fails
        tampered_env = dict(envelope)
        tampered_env["payload_sha256"] = "0" * 64
        self.assertFalse(HybridPqcSigner.verify_envelope(msg, tampered_env))

    def test_ml_kem_768_key_encapsulation(self):
        ek, dk = MLKEM768.keygen()
        ct, ss_sender = MLKEM768.encapsulate(ek)
        ss_receiver = MLKEM768.decapsulate(dk, ct)

        self.assertEqual(ss_sender, ss_receiver, "Shared secret derived by sender and receiver must match exactly")
        self.assertEqual(len(ss_sender), 32, "Shared secret must be 256 bits")


if __name__ == "__main__":
    unittest.main()
