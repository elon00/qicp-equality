"""Strategic Elastic Tokenomics Model for QICP Universal Economic Inclusion.

Mathematical Specification:
1. Elastic Uncapped Supply: Designed for generational economic inclusion across billions
   of underserved individuals without artificial deflationary elite-hoarding.
2. Quadratic Community Minting: MaxGrant = alpha * sqrt(verified_beneficiaries) * velocity_factor.
3. Anti-Hoarding Demurrage: Idle speculative balances above threshold incur a monthly
   decay rate, recycling capital into community public goods and burning excess.
4. Burn-and-Mint Equilibrium (BME): x402 resource bazaar transactions burn 50% of fees,
   creating organic value stabilization.
"""
import math
from typing import Dict, Tuple

# Baseline Tokenomics Constants
BASE_LIVELIHOOD_INDEX = 50_000.0        # alpha: base QICP grant per unit sqrt(beneficiary)
MAX_PER_CAPITA_LIVELIHOOD = 25_000.0    # Hard individual cap per grant cycle
IDLE_THRESHOLD_QICP = 1_000_000.0       # Balances above this incur demurrage if inactive
MONTHLY_DEMURRAGE_RATE = 0.005          # 0.5% per month on excess idle balance
E8S_PER_QICP = 100_000_000              # Standard ICP 8-decimal precision


class QICPElasticTokenomics:
    """Deterministic Mathematical Engine for QICP Economic Inclusion Tokenomics."""

    @staticmethod
    def calculate_community_grant_cap(
        verified_beneficiaries: int,
        velocity_factor: float = 1.0,
        alpha: float = BASE_LIVELIHOOD_INDEX,
    ) -> Dict[str, float]:
        """Compute quadratic community grant allocation cap.
        Formula: Cap = alpha * sqrt(N) * velocity_factor.
        Enforces quadratic scaling to prevent sybil swarming and elite capture.
        """
        if verified_beneficiaries <= 0:
            return {
                "verified_beneficiaries": 0,
                "velocity_factor": velocity_factor,
                "grant_cap_qicp": 0.0,
                "per_capita_effective_qicp": 0.0,
            }

        raw_cap = alpha * math.sqrt(verified_beneficiaries) * velocity_factor
        # Ensure per-capita does not exceed individual livelihood cap
        max_total_cap = verified_beneficiaries * MAX_PER_CAPITA_LIVELIHOOD
        grant_cap = min(raw_cap, max_total_cap)
        effective_per_capita = grant_cap / verified_beneficiaries

        return {
            "verified_beneficiaries": verified_beneficiaries,
            "velocity_factor": round(velocity_factor, 4),
            "grant_cap_qicp": round(grant_cap, 2),
            "per_capita_effective_qicp": round(effective_per_capita, 2),
            "grant_cap_e8s": int(grant_cap * E8S_PER_QICP),
        }

    @staticmethod
    def calculate_demurrage_decay(
        balance_qicp: float,
        inactive_days: int,
        idle_threshold: float = IDLE_THRESHOLD_QICP,
        monthly_rate: float = MONTHLY_DEMURRAGE_RATE,
    ) -> Dict[str, float]:
        """Compute demurrage on speculative idle balances inactive for > 90 days.
        Balances below idle_threshold are 100% exempt from demurrage.
        """
        if inactive_days < 90 or balance_qicp <= idle_threshold:
            return {
                "balance_qicp": balance_qicp,
                "inactive_days": inactive_days,
                "excess_balance_qicp": 0.0,
                "decay_qicp": 0.0,
                "burned_qicp": 0.0,
                "recycled_to_treasury_qicp": 0.0,
                "post_decay_balance_qicp": balance_qicp,
            }

        excess = balance_qicp - idle_threshold
        months_inactive = inactive_days / 30.0
        # Compound decay formula on excess: decay = excess * (1 - (1 - rate)^months)
        decay = excess * (1.0 - math.pow(1.0 - monthly_rate, months_inactive))
        decay = min(decay, excess)

        burned = decay * 0.5
        recycled = decay * 0.5
        post_balance = balance_qicp - decay

        return {
            "balance_qicp": round(balance_qicp, 2),
            "inactive_days": inactive_days,
            "excess_balance_qicp": round(excess, 2),
            "decay_qicp": round(decay, 2),
            "burned_qicp": round(burned, 2),
            "recycled_to_treasury_qicp": round(recycled, 2),
            "post_decay_balance_qicp": round(post_balance, 2),
        }

    @staticmethod
    def calculate_bme_equilibrium(
        monthly_grant_mint_qicp: float,
        monthly_bazaar_volume_qicp: float,
        idle_demurrage_burned_qicp: float,
    ) -> Dict[str, float]:
        """Compute Burn-and-Mint Equilibrium (BME) balance and inflation rate.
        Net Supply Delta = Minted - (Bazaar Burn + Demurrage Burn).
        """
        bazaar_burn = monthly_bazaar_volume_qicp * 0.5  # 50% burned in x402 bazaar
        total_burned = bazaar_burn + idle_demurrage_burned_qicp
        net_delta = monthly_grant_mint_qicp - total_burned

        is_deflationary = net_delta < 0
        burn_to_mint_ratio = total_burned / monthly_grant_mint_qicp if monthly_grant_mint_qicp > 0 else 1.0

        return {
            "monthly_mint_qicp": round(monthly_grant_mint_qicp, 2),
            "bazaar_burn_qicp": round(bazaar_burn, 2),
            "demurrage_burn_qicp": round(idle_demurrage_burned_qicp, 2),
            "total_burned_qicp": round(total_burned, 2),
            "net_supply_delta_qicp": round(net_delta, 2),
            "burn_to_mint_ratio": round(burn_to_mint_ratio, 4),
            "economic_state": "DEFLATIONARY_PRESSURE" if is_deflationary else "CONTROLLED_EXPANSION",
        }


if __name__ == "__main__":
    print("Evaluating Strategic Elastic Tokenomics Engine...")
    cap_info = QICPElasticTokenomics.calculate_community_grant_cap(
        verified_beneficiaries=100,
        velocity_factor=1.25,
    )
    print(f"Community Cap (100 Beneficiaries): {cap_info['grant_cap_qicp']} QICP ({cap_info['per_capita_effective_qicp']} per capita)")

    demurrage_info = QICPElasticTokenomics.calculate_demurrage_decay(
        balance_qicp=2_500_000.0,
        inactive_days=180,
    )
    print(f"Demurrage on 2.5M QICP idle for 180 days: Decay={demurrage_info['decay_qicp']} QICP, Burned={demurrage_info['burned_qicp']} QICP")

    bme_info = QICPElasticTokenomics.calculate_bme_equilibrium(
        monthly_grant_mint_qicp=500_000.0,
        monthly_bazaar_volume_qicp=800_000.0,
        idle_demurrage_burned_qicp=150_000.0,
    )
    print(f"BME State: Net Delta={bme_info['net_supply_delta_qicp']} QICP, State={bme_info['economic_state']}")
