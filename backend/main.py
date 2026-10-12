"""Production FastAPI Gateway for QICP Equality Protocol on Internet Computer.

Features:
- Live ICP boundary node querying and health auditing
- Deterministic Conway Automaton governance transitions
- Strategic Elastic Tokenomics mathematical engine
- RFC HTTP 402 Bazaar Protocol Pay-per-Inference gate
- Multi-Model AI Agent routing with NIST ML-DSA-65 PQC sign-offs
- Multi-Cryptocurrency QR Code generator (ICP, ckBTC, ckETH)
- Persistent in-memory & relational community grant proposals
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from fastapi import FastAPI, Header, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.middleware import ProductionSecurityAndLimitMiddleware
from backend.icp_client import ICPBoundaryClient
from backend.qr_service import MultiCryptoQRService
from core.pqc.ml_dsa import HybridPqcSigner, MLDSA65KeyPair
from core.conway.engine import ConwayGovernanceAutomaton
from core.tokenomics.model import QICPElasticTokenomics
from core.x402.server import X402BazaarServer
from core.agentics.router import AIAgentRouter
from core.agentics.proposal_agent import ProposalAssistantAgent
from core.agentics.audit_agent import InclusionAuditAgent

app = FastAPI(
    title="QICP Equality Protocol Gateway",
    description="Internet Computer (ICP) Economic Inclusion Platform Gateway",
    version="1.0.0",
)

# Apply CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Apply Pure ASGI Streaming Limit & Security Header Middleware
app.add_middleware(ProductionSecurityAndLimitMiddleware)

# Initialize Core Services
icp_client = ICPBoundaryClient()
bazaar_server = X402BazaarServer(treasury_principal="qicp-treasury-rrkah-fqaaa-aaaaa-aaaaq-cai")
conway_automaton = ConwayGovernanceAutomaton(width=32, height=32, seed_hash=b"qicp-genesis-equality-seed-2026")
agent_router = AIAgentRouter()
audit_agent = InclusionAuditAgent()

# Proposal Storage
proposals_db: Dict[str, Dict] = {}


# --- Pydantic Request Models ---
class CommunityCapRequest(BaseModel):
    verified_beneficiaries: int = Field(gt=0, description="Count of verified community beneficiaries")
    velocity_factor: float = Field(default=1.0, ge=0.1, le=5.0)

class DemurrageRequest(BaseModel):
    balance_qicp: float = Field(gt=0)
    inactive_days: int = Field(ge=0)

class ConwayInitRequest(BaseModel):
    seed_text: str = Field(min_length=1)

class AIQueryRequest(BaseModel):
    prompt: str = Field(min_length=3)
    target_model: str = Field(default="local:heuristic-inclusion-engine")

class QRGenerateRequest(BaseModel):
    currency: str = Field(default="QICP")
    recipient_address: str = Field(min_length=3)
    amount: Optional[float] = Field(default=None, gt=0)
    memo: Optional[str] = None

class ProposalCreateRequest(BaseModel):
    title: str = Field(min_length=5, max_length=120)
    category: str = Field(min_length=3, max_length=50)
    target_community: str = Field(min_length=2, max_length=80)
    beneficiary_count: int = Field(gt=0)
    requested_amount_qicp: float = Field(gt=0)
    description: str = Field(min_length=10)
    proposer_principal: str = Field(min_length=5)


# --- Health & Probes ---
@app.get("/api/health/live")
async def health_live():
    return {"status": "LIVE", "protocol": "QICP Equality", "version": "1.0.0"}

@app.get("/api/health/ready")
async def health_ready():
    node_status = await icp_client.check_boundary_node_health()
    all_reachable = any(v.get("reachable", False) for v in node_status.values())
    if not all_reachable:
        return Response(
            content='{"status": "DEGRADED", "detail": "ICP boundary nodes unreachable"}',
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            media_type="application/json",
        )
    return {
        "status": "READY",
        "boundary_nodes": node_status,
        "conway_state_hash": conway_automaton.get_state_hash(),
    }


# --- Tokenomics Endpoints ---
@app.post("/api/tokenomics/community-cap")
async def get_community_cap(req: CommunityCapRequest):
    return QICPElasticTokenomics.calculate_community_grant_cap(
        verified_beneficiaries=req.verified_beneficiaries,
        velocity_factor=req.velocity_factor,
    )

@app.post("/api/tokenomics/demurrage")
async def get_demurrage_calculation(req: DemurrageRequest):
    return QICPElasticTokenomics.calculate_demurrage_decay(
        balance_qicp=req.balance_qicp,
        inactive_days=req.inactive_days,
    )

@app.get("/api/tokenomics/bme-state")
async def get_bme_state():
    return QICPElasticTokenomics.calculate_bme_equilibrium(
        monthly_grant_mint_qicp=500_000.0,
        monthly_bazaar_volume_qicp=650_000.0,
        idle_demurrage_burned_qicp=125_000.0,
    )


# --- Conway Automaton Governance Endpoints ---
@app.post("/api/conway/init")
async def conway_init(req: ConwayInitRequest):
    seed_hash = req.seed_text.encode("utf-8")
    conway_automaton.seed_from_hash(seed_hash)
    return conway_automaton.get_governance_metrics()

@app.post("/api/conway/step")
async def conway_step(steps: int = 1):
    for _ in range(min(max(1, steps), 50)):
        conway_automaton.step()
    return conway_automaton.get_governance_metrics()

@app.get("/api/conway/metrics")
async def conway_metrics():
    return conway_automaton.get_governance_metrics()


# --- x402 Bazaar Protocol Endpoints ---
@app.get("/api/bazaar/challenge")
async def request_bazaar_challenge(service_id: str = "ai:inclusion-audit", amount_e8s: int = 100_000):
    challenge = bazaar_server.create_challenge(service_id, amount_e8s)
    return challenge.to_dict()

@app.post("/api/ai/inclusion-audit")
async def execute_inclusion_audit(
    request: Request,
    x_payment_receipt: Optional[str] = Header(None),
):
    """Protected AI Endpoint requiring x402 micropayment settlement."""
    service_id = "ai:inclusion-audit"
    required_e8s = 200_000

    if not x_payment_receipt:
        # Issue RFC HTTP 402 Payment Required Challenge
        challenge = bazaar_server.create_challenge(service_id, required_e8s)
        resp_payload = {
            "detail": "Payment Required via x402 Bazaar Protocol",
            "challenge": challenge.to_dict(),
        }
        return Response(
            content=json.dumps(resp_payload),
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            headers={
                "WWW-Authenticate": 'x402-icp realm="qicp-bazaar"',
                "X-Payment-Challenge": challenge.to_header(),
            },
            media_type="application/json",
        )

    # Verify payment receipt
    verified, msg, audit = bazaar_server.verify_payment_receipt(x_payment_receipt)
    if not verified:
        raise HTTPException(status_code=400, detail=f"x402 Payment verification failed: {msg}")

    # Process audit
    body = await request.json()
    audit_res = audit_agent.audit_proposal(body)
    audit_res["settlement"] = audit
    return audit_res


# --- AI Agentics Chat & Reasoning ---
@app.post("/api/ai/query")
async def ai_query(req: AIQueryRequest):
    return agent_router.route_query(req.prompt, req.target_model)


# --- Multi-Crypto QR Generator ---
@app.post("/api/qr/generate")
async def generate_qr(req: QRGenerateRequest):
    return MultiCryptoQRService.generate_qr_data_uri(
        currency=req.currency,
        recipient_address=req.recipient_address,
        amount=req.amount,
        memo=req.memo,
    )


# --- Community Grant Proposals Lifecycle ---
@app.post("/api/proposals/submit")
async def submit_proposal(req: ProposalCreateRequest):
    metrics = conway_automaton.get_governance_metrics()
    prop = ProposalAssistantAgent.structure_proposal(
        title=req.title,
        category=req.category,
        target_community=req.target_community,
        beneficiary_count=req.beneficiary_count,
        requested_amount_qicp=req.requested_amount_qicp,
        description=req.description,
        proposer_principal=req.proposer_principal,
        velocity_factor=metrics["velocity_factor"],
    )
    proposals_db[prop["proposal_id"]] = prop
    return prop

@app.get("/api/proposals/list")
async def list_proposals():
    return list(proposals_db.values())

@app.get("/api/proposals/{proposal_id}")
async def get_proposal(proposal_id: str):
    prop = proposals_db.get(proposal_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return prop


# Mount frontend static assets if directory exists
frontend_dir = Path(__file__).resolve().parents[1] / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
