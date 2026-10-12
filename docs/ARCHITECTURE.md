# QICP Canister & Gateway Architecture

## 1. System Overview

QICP Equality is structured as a decentralized, multi-canister architecture running natively on the Internet Computer Protocol (ICP), supported by an ASGI gateway and responsive Web client.

```
+-----------------------------------------------------------------------------------+
|                                 CLIENT LAYER                                      |
|  - Modern Responsive Web UI (HTML5, CSS3, ES6)                                    |
|  - Wallets: Internet Identity (II), Plug Wallet, NFID, Bitfinity                  |
|  - Multi-Currency Dynamic QR Code Generator (ICP, QICP, ckBTC, ckETH)            |
+------------------------------------------+----------------------------------------+
                                           |
                                           v
+-----------------------------------------------------------------------------------+
|                           ASGI GATEWAY & MIDDLEWARE                               |
|  - Pure ASGI Streaming Request Body Limiter (1 MB Max Chunk Enforcer)             |
|  - Production Security Headers (HSTS, CSP, Frame-Options, X-Content-Type)         |
|  - Multi-Model AI Agent Routing & PQC Signature Verification Engine               |
|  - RFC HTTP 402 Payment Challenge & Receipt Processor                             |
+------------------------------------------+----------------------------------------+
                                           |
                                           v
+-----------------------------------------------------------------------------------+
|                             INTERNET COMPUTER PROTOCOL                            |
|                                                                                   |
|  +--------------------+  +--------------------+  +------------------------------+ |
|  |     qicp_token     |  |      treasury      |  |         x402_bazaar          | |
|  |   ICRC-1 / ICRC-2  |  |  Community Escrow  |  |    Pay-per-Inference Bazaar  | |
|  |   Elastic Ledger   |  |  Dispute Timelocks |  |    50% Burn BME Settlement   | |
|  +---------+----------+  +---------+----------+  +--------------+---------------+ |
|            ^                       ^                            ^                 |
|            |                       |                            |                 |
|            +-----------------------+----------------------------+                 |
|                                    |                                              |
|                         +----------+----------+                                   |
|                         |    conway_engine    |                                   |
|                         |  Toroidal 32x32     |                                   |
|                         |  Consensus Velocity |                                   |
|                         +---------------------+                                   |
+-----------------------------------------------------------------------------------+
```

## 2. Canister Specifications

### 2.1 `qicp_token` (ICRC-1 / ICRC-2 Ledger Canister)
- **Candid**: `canisters/qicp_token/qicp_token.did`
- **Source**: `canisters/qicp_token/src/lib.rs`
- **Standards**: ICRC-1, ICRC-2, ICRC-3
- **Decimals**: 8 (`e8s` precision)
- **Transaction Fee**: 10,000 e8s (0.0001 QICP)
- **Key Functions**:
  - `icrc1_transfer`: Standard token transfers.
  - `mint_livelihood_grant`: Authorized minting for verified community proposals.
  - `apply_demurrage_burn`: Algorithmic burn on idle speculative balances.

### 2.2 `treasury` (Community Escrow & Governance Canister)
- **Candid**: `canisters/treasury/treasury.did`
- **Source**: `canisters/treasury/src/lib.rs`
- **Dispute Timelock**: 7 days (604,800 seconds).
- **Key Functions**:
  - `submit_proposal`: Create new grant application with quadratic cap check.
  - `disburse_grant`: Execute payout to beneficiary after dispute timelock.
  - `cancel_disputed_grant`: Governance cancellation during dispute window.

### 2.3 `x402_bazaar` (Resource & AI Inference Bazaar Canister)
- **Candid**: `canisters/x402_bazaar/x402_bazaar.did`
- **Source**: `canisters/x402_bazaar/src/lib.rs`
- **Key Functions**:
  - `request_challenge`: Generate cryptographic payment challenge with unique nonce.
  - `settle_payment`: Verify block index and nonce; execute 50% burn and 50% treasury deposit.

### 2.4 `conway_engine` (Cellular Automaton Canister)
- **Candid**: `canisters/conway_engine/conway_engine.did`
- **Source**: `canisters/conway_engine/src/lib.rs`
- **Lattice Size**: 32x32 cells (1,024 toroidal nodes).
- **Key Functions**:
  - `init_automaton`: Seed grid deterministically from proposal/block hash.
  - `step_automaton`: Evolve grid by $N$ steps using B3/S23 Conway rules.
  - `get_current_metrics`: Return active nodes, density, velocity factor, and SHA-256 state digest.
