# Canister Deployment Guide

## 1. Prerequisites

- **DFINITY SDK (`dfx`)**: Version 0.24.0 or higher.
- **Rust Toolchain**: `rustup target add wasm32-unknown-unknown`
- **Node.js**: Version 20.x or higher.

---

## 2. Local Replica Deployment

```bash
# 1. Start local Internet Computer replica
dfx start --clean --background

# 2. Deploy all canisters locally
dfx deploy

# 3. Obtain deployed local canister IDs
dfx canister id qicp_token
dfx canister id treasury
dfx canister id x402_bazaar
dfx canister id conway_engine
dfx canister id frontend
```

---

## 3. Mainnet Deployment

```bash
# 1. Configure production identity
dfx identity use default

# 2. Verify cycles wallet balance
dfx wallet --network ic balance

# 3. Deploy to Internet Computer Mainnet
dfx deploy --network ic --with-cycles 10000000000000
```
