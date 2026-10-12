# QICP Equality: Engineering Workflow Design & Lifecycle Architecture

## Document Purpose & Scope

This specification formalizes the engineering workflows, automated continuous integration and continuous deployment (CI/CD) pipelines, canister upgrade lifecycles, governance dispute timelocks, and payment settlement flows governing the **QICP Equality** protocol.

All workflows follow a **strict fail-closed, zero-simulation** engineering standard.

---

## 1. Automated CI / CD Pipeline Architecture

The Continuous Integration and Deployment pipeline enforces cryptographic validation, deterministic mathematical models, canister Wasm builds, and fail-closed mainnet release controls.

```mermaid
flowchart TD
    A["Git Push / Pull Request (main)"] --> B["GitHub Actions Matrix"]
    
    subgraph CI ["Continuous Integration (ci.yml)"]
        B --> C1["Python 3.12 Setup & Linters"]
        B --> C2["Rust Toolchain Setup (stable)"]
        C1 --> D1["NIST PQC ML-DSA-65 & ML-KEM-768 Tests"]
        C1 --> D2["Conway Toroidal Automaton Math Tests"]
        C1 --> D3["Elastic Tokenomics & Demurrage Tests"]
        C1 --> D4["FastAPI & ASGI Security Limiter Tests"]
        C2 --> E1["Cargo Check Workspace (all 4 canisters)"]
        C2 --> E2["Wasm32-unknown-unknown Compilation"]
    end
    
    subgraph Gate ["Reality Gate (scripts/check.py)"]
        D1 & D2 & D3 & D4 & E1 & E2 --> F["Live IC Boundary Node Reachability Check"]
        F --> G["Candid IDL (.did) Interface Parity Audit"]
    end
    
    subgraph CD ["Continuous Deployment Gate (cd.yml)"]
        G --> H{"Production Credentials Present?\n(IC_PRODUCTION_IDENTITY & CYCLES_WALLET)"}
        H -- "Missing (Default Security Baseline)" --> J["HALT: Exit Code 2\n(Fail-Closed Audit Report)"]
        H -- "Verified Valid Credentials" --> K["dfx deploy --network ic\nLive Canister Upgrades"]
    end
```

---

## 2. Canister State Machine & Upgrade Lifecycle

Canisters on the Internet Computer maintain persistent memory across code upgrades. QICP canisters utilize deterministic state transitions and pre/post-upgrade serialization hooks.

```mermaid
stateDiagram-v2
    [*] --> Uninitialized: Canister Created on Subnet
    Uninitialized --> Active: canister_init() with Default State
    
    state Active {
        [*] --> ServingRequests: Query & Update Calls
        ServingRequests --> StateMutation: Treasury Proposal / Token Transfer
        StateMutation --> ServingRequests: State Persisted in RefCell
    }
    
    Active --> Upgrading: canister_pre_upgrade() Hook Invoked
    state Upgrading {
        SerializeState: Candid / Stable Memory Binary Snapshot
        WriteStable: Pack into Stable Memory
        SerializeState --> WriteStable
    }
    
    Upgrading --> Upgraded: Code Bytecode Replaced by Controller
    state Upgraded {
        ReadStable: Unpack from Stable Memory
        RestoreState: canister_post_upgrade() Validation
        ReadStable --> RestoreState
    }
    
    Upgraded --> Active: Resume Serving with Preserved Balances
    Active --> [*]: Canister Stopped / Deleted
```

---

## 3. Grassroots Grant Proposal & Conway Timelock Flow

The grant allocation pipeline combines multi-model AI proposal drafting, anti-sybil auditing, deterministic Conway automaton velocity weighting, and a mandatory 7-day dispute window before disbursement.

```mermaid
sequenceDiagram
    autonumber
    actor Proposer as Grassroots Proposer (Moolnivasi / SC / ST / Minority)
    participant Agent as AI Agent (Proposal Assistant)
    participant Auditor as AI Anti-Sybil Auditor
    participant Conway as Conway Automaton Engine
    participant Treasury as Treasury Canister (ic0.app)
    participant Token as QICP Token Canister

    Proposer->>Agent: Submit community project details & budget
    Agent->>Auditor: Audit grant for duplicates and sybil patterns
    Auditor->>Auditor: Sign verification with NIST ML-DSA-65 PQC
    Auditor->>Conway: Query current lattice velocity factor
    Conway-->>Treasury: Supply cellular density factor V ∈ [0.5, 2.0]
    Proposer->>Treasury: submit_proposal(title, beneficiary, amount, pqc_sig)
    Treasury-->>Treasury: Lock grant in 'Submitted' state for 7 days
    
    alt Dispute Raised within 7-Day Window
        actor Reviewer as Authorized Reviewer
        Reviewer->>Treasury: cancel_disputed_grant(prop_id, reason)
        Treasury-->>Treasury: Update status to 'Cancelled' (No funds disbursed)
    else Dispute Window Elapses (7 Days)
        Proposer->>Treasury: disburse_grant(prop_id)
        Treasury->>Token: Mint / Transfer verified livelihood grant
        Token-->>Proposer: Grant funds credited to beneficiary subaccount
        Treasury-->>Treasury: Update status to 'Disbursed'
    end
```

---

## 4. RFC HTTP 402 Pay-Per-Inference Settlement Loop

The x402 bazaar canister provides micro-payment monetization for AI model inference while enforcing Burn-and-Mint Equilibrium (BME).

```mermaid
sequenceDiagram
    autonumber
    actor Client as AI Client / Edge Device
    participant API as Gateway (/api/ai/bazaar/chat)
    participant Bazaar as x402 Bazaar Canister
    participant Ledger as QICP Token Ledger

    Client->>API: HTTP POST /api/ai/bazaar/chat (without payment)
    API-->>Client: HTTP 402 Payment Required + Challenge Nonce & Target Principal
    
    Client->>Ledger: Transfer 100,000 e8s (0.001 QICP) with Nonce Memo
    Ledger-->>Client: Block Index #B10294
    
    Client->>API: Retry HTTP POST with X-402-Receipt: {nonce, block_index, payer}
    API->>Bazaar: settle_payment(receipt)
    
    Bazaar->>Bazaar: Verify replay resistance & expiration
    Bazaar->>Bazaar: Burn 50% (50,000 e8s) & Credit Treasury 50%
    Bazaar-->>API: Settlement Audit Confirmed (SETTLED)
    
    API->>API: Execute Multi-Model Agent Inference
    API-->>Client: HTTP 200 OK + Inference Result & Settlement Audit Data
```

---

## 5. Emergency Incident Response & Key Rotation Runbook

In the event of anomalous transactions, suspected private key compromise, or upstream infrastructure disruption, the protocol follows this emergency protocol:

```mermaid
flowchart TD
    A["Anomaly Detected (Oracle Divergence / Replay Spike)"] --> B["Security Circuit Breaker Activated"]
    B --> C["Freeze Sensitive Canister Updates (Admin Access Restricted)"]
    C --> D["Gather Multi-Signature Key Rotation Committee"]
    D --> E["Generate NIST ML-DSA-65 & Ed25519 Replacement Keypair"]
    E --> F["Deploy Hardened Canister Bytecode via Controller Quorum"]
    F --> G["Execute scripts/check.py Full Verification"]
    G --> H{"100% Pass On-Chain Reality Audit?"}
    H -- "No" --> C
    H -- "Yes" --> I["Resume Production Operations & Publish Incident Report"]
```

---

## 6. Verification and Maintenance Checklist

1. **Rust Workspace**: Always run `cargo check --workspace` before submitting pull requests.
2. **Boundary Connectivity**: Maintain low-latency endpoints for `https://ic0.app` and `https://icp-api.io`.
3. **PQC Signatures**: Every governance action requires binding challenge commits with message digests.
4. **Zero-Mock Policy**: Tests and CI workflows must execute real algorithmic code paths.
