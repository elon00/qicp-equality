# DevOps, CI/CD & Canister Release Engineering

This guide details the continuous integration, continuous delivery, and release verification infrastructure powering the **QICP Equality** protocol.

---

## 1. Automated GitHub Actions Pipelines

The project maintains two production workflows in `.github/workflows/`:

1. **`ci.yml` (Continuous Integration)**:
   - Triggers on every push and pull request.
   - Sets up Python 3.12 and stable Rust.
   - Executes unit and integration test suites:
     - `tests/test_pqc.py` (NIST FIPS 204 ML-DSA-65 & FIPS 203 ML-KEM-768)
     - `tests/test_conway.py` (Toroidal automaton state hashing & velocity factors)
     - `tests/test_tokenomics.py` (Elastic supply expansion & demurrage decay)
     - `tests/test_x402.py` (HTTP 402 challenge negotiation & replay defense)
     - `tests/test_api.py` (FastAPI endpoints, streaming chunk limiters, CORS/HSTS)
   - Checks Rust workspace compilation: `cargo check --workspace`.
   - Validates Candid IDL interface consistency.

2. **`cd.yml` (Continuous Deployment & Release Gate)**:
   - Triggers on push to `main` and `workflow_dispatch`.
   - Compiles canisters to `wasm32-unknown-unknown` in release mode.
   - Calculates cryptographic SHA-256 checksums of compiled Wasm artifacts.
   - Evaluates the **Fail-Closed Release Gate**:
     - Requires repository secrets `IC_PRODUCTION_IDENTITY` and `IC_CYCLES_WALLET_ID`.
     - In the absence of signed production credentials, the gate securely exits with code `2`, maintaining audit compliance without mock or simulation workarounds.

---

## 2. Local Environment Setup

To run tests and audits locally:

```bash
# 1. Clone the repository
git clone https://github.com/elon00/qicp-equality.git
cd qicp-equality

# 2. Set up Python virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .\.venv\Scripts\activate
pip install -r requirements.txt

# 3. Check Rust canisters
cargo check --workspace

# 4. Run automated test suites
pytest -v

# 5. Execute full reality gate
python scripts/check.py
```

---

## 3. Candid Interface Compatibility

Each canister defines a strict Candid (`.did`) contract in `canisters/<canister_name>/<canister_name>.did`:

- `qicp_token.did`: ICRC-1 standard types, queries, and transfer methods.
- `treasury.did`: Proposal submission, dispute timelock checks, and disbursement.
- `x402_bazaar.did`: Challenge generation, receipt settlement, and burn statistics.
- `conway_engine.did`: Cellular automaton stepping, active node density, and hash digests.

Any changes to Rust structs must be mirrored in `.did` declarations to prevent upgrade incompatibilities.
