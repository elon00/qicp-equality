"""Grassroots Community Proposal AI Assistant for QICP Equality.

Assists Moolnivasi, SC, ST, OBC, minority, and rural community organizers
in drafting, structuring, and formalizing on-chain grant proposals.
"""
import hashlib
import json
import time
from typing import Dict, List, Optional
from core.tokenomics.model import QICPElasticTokenomics


class ProposalAssistantAgent:
    """Grassroots AI agent helping format verifiable inclusion grant proposals."""

    @staticmethod
    def structure_proposal(
        title: str,
        category: str,
        target_community: str,
        beneficiary_count: int,
        requested_amount_qicp: float,
        description: str,
        proposer_principal: str,
        velocity_factor: float = 1.0,
    ) -> Dict:
        """Analyze, validate, and structure a community grant proposal."""
        cap_analysis = QICPElasticTokenomics.calculate_community_grant_cap(
            verified_beneficiaries=beneficiary_count,
            velocity_factor=velocity_factor,
        )

        allowed_cap = cap_analysis["grant_cap_qicp"]
        is_within_cap = requested_amount_qicp <= allowed_cap

        proposal_id = f"qicp-prop-{hashlib.sha256(f'{title}:{proposer_principal}:{time.time()}'.encode()).hexdigest()[:12]}"

        return {
            "proposal_id": proposal_id,
            "title": title.strip(),
            "category": category.strip(),
            "target_community": target_community.strip(),
            "beneficiary_count": beneficiary_count,
            "requested_amount_qicp": requested_amount_qicp,
            "requested_amount_e8s": int(requested_amount_qicp * 100_000_000),
            "community_cap_qicp": allowed_cap,
            "is_within_quadratic_cap": is_within_cap,
            "proposer_principal": proposer_principal,
            "description": description.strip(),
            "created_at": int(time.time()),
            "status": "READY_FOR_COMMUNITY_SUBMISSION" if is_within_cap else "CAP_EXCEEDED_ADJUSTMENT_REQUIRED",
        }
