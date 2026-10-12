"""Unit test suite for Strategic Elastic Tokenomics Engine."""
import unittest
from core.tokenomics.model import QICPElasticTokenomics


class TestStrategicElasticTokenomics(unittest.TestCase):
    """Verifies quadratic community caps, demurrage decay, and BME equilibrium."""

    def test_quadratic_grant_cap_scaling(self):
        # 25 beneficiaries
        res_25 = QICPElasticTokenomics.calculate_community_grant_cap(25, velocity_factor=1.0)
        # 100 beneficiaries (4x population should give ~2x cap due to sqrt)
        res_100 = QICPElasticTokenomics.calculate_community_grant_cap(100, velocity_factor=1.0)

        self.assertAlmostEqual(res_100["grant_cap_qicp"] / res_25["grant_cap_qicp"], 2.0, delta=0.01)
        self.assertLessEqual(res_100["per_capita_effective_qicp"], 25_000.0)

    def test_demurrage_decay_threshold(self):
        # Balance under 1M is completely exempt
        small_holder = QICPElasticTokenomics.calculate_demurrage_decay(500_000.0, inactive_days=300)
        self.assertEqual(small_holder["decay_qicp"], 0.0)
        self.assertEqual(small_holder["post_decay_balance_qicp"], 500_000.0)

        # Active balance (<90 days inactive) is exempt even if >1M
        active_whale = QICPElasticTokenomics.calculate_demurrage_decay(5_000_000.0, inactive_days=45)
        self.assertEqual(active_whale["decay_qicp"], 0.0)

        # Speculative idle whale (>1M and >90 days inactive) incurs decay
        idle_whale = QICPElasticTokenomics.calculate_demurrage_decay(2_000_000.0, inactive_days=180)
        self.assertGreater(idle_whale["decay_qicp"], 0.0)
        self.assertEqual(idle_whale["burned_qicp"], idle_whale["recycled_to_treasury_qicp"])

    def test_bme_equilibrium_calculation(self):
        bme = QICPElasticTokenomics.calculate_bme_equilibrium(
            monthly_grant_mint_qicp=400_000.0,
            monthly_bazaar_volume_qicp=1_000_000.0,
            idle_demurrage_burned_qicp=50_000.0,
        )
        # 50% of 1M bazaar = 500k burn + 50k demurrage burn = 550k burn
        # 400k mint - 550k burn = -150k delta (deflationary)
        self.assertEqual(bme["total_burned_qicp"], 550_000.0)
        self.assertEqual(bme["net_supply_delta_qicp"], -150_000.0)
        self.assertEqual(bme["economic_state"], "DEFLATIONARY_PRESSURE")


if __name__ == "__main__":
    unittest.main()
