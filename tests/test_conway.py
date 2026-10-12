"""Unit test suite for Conway Automaton Governance Engine."""
import hashlib
import unittest
from core.conway.engine import ConwayGovernanceAutomaton


class TestConwayGovernanceEngine(unittest.TestCase):
    """Verifies deterministic Conway Automaton consensus derivations."""

    def test_deterministic_seeding(self):
        seed_a = hashlib.sha256(b"proposal-alpha").digest()
        seed_b = hashlib.sha256(b"proposal-beta").digest()

        auto_a1 = ConwayGovernanceAutomaton(width=32, height=32, seed_hash=seed_a)
        auto_a2 = ConwayGovernanceAutomaton(width=32, height=32, seed_hash=seed_a)
        auto_b = ConwayGovernanceAutomaton(width=32, height=32, seed_hash=seed_b)

        # Identical seeds yield identical initial states and hashes
        self.assertEqual(auto_a1.get_state_hash(), auto_a2.get_state_hash())
        # Different seeds yield distinct states
        self.assertNotEqual(auto_a1.get_state_hash(), auto_b.get_state_hash())

    def test_deterministic_evolution(self):
        seed = hashlib.sha256(b"proposal-test-seed").digest()
        auto = ConwayGovernanceAutomaton(width=32, height=32, seed_hash=seed)

        metrics_0 = auto.get_governance_metrics()
        auto.step()
        metrics_1 = auto.get_governance_metrics()

        self.assertEqual(metrics_1["step"], 1)
        self.assertNotEqual(metrics_0["state_hash"], metrics_1["state_hash"])
        # Velocity factor must always stay within bounded range [0.5, 2.0]
        self.assertGreaterEqual(metrics_1["velocity_factor"], 0.5)
        self.assertLessEqual(metrics_1["velocity_factor"], 2.0)


if __name__ == "__main__":
    unittest.main()
