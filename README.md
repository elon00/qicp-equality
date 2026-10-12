# QICP Equality Protocol (QICP)

An independent, sovereign economic-inclusion platform natively hosted on the **Internet Computer Protocol (ICP)**, dedicated to structural empowerment for **Moolnivasi, Scheduled Castes (SC), Scheduled Tribes (ST), Other Backward Classes (OBC), minorities, and underserved communities worldwide** through transparent livelihood grants, social micro-enterprises, and public goods.

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Protocol](https://img.shields.io/badge/Network-Internet_Computer_(ICP)-darkblue.svg)](https://internetcomputer.org)
[![PQC](https://img.shields.io/badge/PQC-NIST_FIPS_204_(ML--DSA--65)-emerald.svg)](docs/WHITEPAPER.md)
[![Reality Gate](https://img.shields.io/badge/Reality_Gate-Zero_Simulation-brightgreen.svg)](scripts/check.py)
[![x402 Bazaar](https://img.shields.io/badge/x402-Pay--per--Inference-orange.svg)](docs/X402_PROTOCOL.md)

---

## ⚖️ Legal & Independence Disclosures

- **Independent Open-Source Initiative**: QICP Equality is an independent public good protocol. It is not affiliated with, sponsored by, or endorsed by Muhammad Yunus or any external foundation or individuals.
- **No Financial Guarantees**: Token creation does not eliminate poverty automatically or generate guaranteed yields. QICP does not offer, promise, or market financial returns, staking yields, dividends, or fixed income.
- **Pre-Market Status**: QICP tokens are designed for on-chain community governance, micro-resource settlement, and grant tracking. The token is unlisted on centralized exchanges and possesses zero guaranteed secondary market liquidity.

---

## 🌐 Verified Technical Architecture

```
                      ┌──────────────────────────────────────────────┐
                      │             Internet Computer L1             │
                      │        (Consensus, Subnets & Boundary)       │
                      └───────┬──────────────┬──────────────┬────────┘
                              │              │              │
                ┌─────────────▼────┐  ┌──────▼──────┐  ┌────▼─────────────┐
                │    qicp_token    │  │   treasury  │  │   x402_bazaar    │
                │  ICRC-1 Ledger   │◄─┤  Escrow &   │◄─┤  Pay-per-Infer.  │
                │  Elastic Mint &  │  │  Timelocks  │  │  50% Burn BME    │
                │  Demurrage Burn  │  │             │  │                  │
                └──────────────────┘  └──────┬──────┘  └──────────────────┘
                                             │
                                      ┌──────▼─────────────┐
                                      │   conway_engine    │
                                      │  Deterministic     │
                                      │  Toroidal Lattice  │
                                      └────────────────────┘
```

The system comprises four decoupled, interoperating Rust canisters with official Candid IDL interfaces:
1. **`qicp_token`** ([`canisters/qicp_token/qicp_token.did`](canisters/qicp_token/qicp_token.did)): Fully compliant with DFINITY ICRC-1, ICRC-2, and ICRC-3 standards with elastic livelihood minting and anti-hoarding demurrage burns.
2. **`treasury`** ([`canisters/treasury/treasury.did`](canisters/treasury/treasury.did)): Community proposal escrow, Conway voting aggregation, and 7-day dispute period timelocks.
3. **`x402_bazaar`** ([`canisters/x402_bazaar/x402_bazaar.did`](canisters/x402_bazaar/x402_bazaar.did)): RFC HTTP 402 Pay-per-Inference challenge and settlement engine with 50% Burn-and-Mint Equilibrium (BME).
4. **`conway_engine`** ([`canisters/conway_engine/conway_engine.did`](canisters/conway_engine/conway_engine.did)): Deterministic 32x32 toroidal cellular automaton deriving consensus velocity multipliers from on-chain block hashes without simulations.

---

## 🛡️ Reality Gate Protocol (Zero Simulation)

This project strictly adheres to the **Reality Gate**:
- **Real Post-Quantum Cryptography**: Real implementations of NIST FIPS 204 **ML-DSA-65** lattice signatures and NIST FIPS 203 **ML-KEM-768** key encapsulation with hybrid Ed25519 envelopes.
- **Live Boundary Node Verification**: Direct connectivity against live Internet Computer boundary nodes (`https://ic0.app` and `https://icp-api.io`).
- **Fail-Closed Release Audit**: The production release gate strictly halts with exit code 2 if mainnet cycles wallets or production identities are unconfigured, ensuring zero fabricated deployment claims.

---

## 📊 Strategic Elastic Tokenomics

Unlike deflationary fixed-cap tokens that concentrate wealth among early elites, QICP implements an **uncapped, elastic supply architecture**:
1. **Livelihood-Bound Minting**: Tokens are generated *only* upon verified disbursement of grassroots grants and public goods.
2. **Quadratic Community Cap**:
   $$\text{GrantCap}(C) = \alpha \cdot \sqrt{N} \cdot V_{\text{conway}}$$
   Where $\alpha = 50,000\text{ QICP}$, $N$ is verified beneficiaries, and $V_{\text{conway}}$ is the Conway velocity multiplier.
3. **Anti-Hoarding Demurrage**: Speculative idle balances exceeding $1,000,000\text{ QICP}$ inactive for $>90$ days incur a $0.5\%$ monthly decay (50% burned, 50% recycled into community escrow).
4. **Burn-and-Mint Equilibrium (BME)**: 50% of all x402 resource bazaar fees are burned permanently, counterbalancing supply expansion with organic utility demand.

---

## 💻 Local Setup & Technical Verification

Recommended environment: Python 3.12+ and Node.js 20+.

```bash
# 1. Clone repository
git clone https://github.com/elon00/qicp-equality.git
cd qicp-equality

# 2. Setup Python environment
python -m venv .venv
# Windows:
.\.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
npm install
```

### Complete Reality Gate Verification Suite
```bash
python scripts/check.py
```

### Modular Verification Commands
- `python scripts/check.py --pqc`: Evaluates NIST FIPS 204/203 lattice signatures and hybrid signers.
- `python scripts/check.py --conway`: Tests deterministic 32x32 toroidal automaton transitions.
- `python scripts/check.py --tokenomics`: Verifies quadratic scaling, demurrage decay, and BME math.
- `python scripts/check.py --x402`: Verifies RFC 402 challenge negotiation, receipts, and replay defense.
- `python scripts/check.py --api`: Tests streaming request limits (1 MB), security headers, and gateway routes.
- `python scripts/check.py --canisters`: Audits Candid IDL files against `dfx.json`.
- `python scripts/check.py --boundary`: Tests live queries to Internet Computer boundary nodes.
- `python scripts/check.py --release`: Audits mainnet production release readiness (fails closed with code 2 if prerequisites are unconfigured).

---

## 🚀 Launching the Production Gateway & dApp

1. **Start the Production Gateway**:
   ```bash
   uvicorn backend.main:app --host 0.0.0.0 --port 8000
   ```
2. **Access the dApp Frontend**:
   Open `http://localhost:8000` in any web browser.
   - **Multi-Wallet Support**: Internet Identity (II), Plug Wallet, NFID, Bitfinity.
   - **Multi-Crypto QR Terminal**: Instant scan-ready QR codes for QICP, ICP, ckBTC, and ckETH.
   - **Live Conway Visualizer**: Interactive canvas rendering deterministic consensus lattice state.
   - **Community Grant Portal**: Real-time quadratic cap calculation and proposal application pipeline.
   - **x402 AI Chatbot**: Multi-model inference assistant with NIST ML-DSA-65 signature proof badges.

---

## 🛠️ DFINITY Canister Deployment (`dfx`)

```bash
# Local replica deployment
dfx start --clean --background
dfx deploy

# Mainnet production deployment
dfx deploy --network ic --with-cycles 10000000000000
```

---

- [**Academic Whitepaper**](docs/WHITEPAPER.md) (or [WHITEPAPER.md](WHITEPAPER.md)) — Comprehensive scientific, cryptographic, and economic whitepaper.
- [**Workflow Design & Lifecycle Architecture**](docs/WORKFLOW_DESIGN.md) — CI/CD pipelines, canister upgrades, governance dispute timelocks, and emergency recovery runbooks.
- [**About QICP Equality**](ABOUT.md) — Mission, target demographics (Moolnivasi, SC/ST/OBC/minorities), and independence disclosures.
- [**Canister Architecture**](docs/ARCHITECTURE.md) — Multi-canister layout, state structures, and inter-canister calls.
- [**Strategic Tokenomics**](docs/TOKENOMICS.md) — Elastic supply mathematics, quadratic formulas, and demurrage proofs.
- [**x402 Protocol Specification**](docs/X402_PROTOCOL.md) — RFC 402 Pay-per-Inference technical specification.
- [**Conway Automaton Specification**](docs/CONWAY_AUTOMATON.md) — Deterministic cellular governance mathematics.
- [**Wiki Documentation**](wiki/Home.md) — Operations, mission, wallet integration, and disaster recovery runbooks.
- [**Automated Security Audit**](scripts/audit_security.py) — Static code analysis, zero-mock PQC verification, and memory safety checks.
