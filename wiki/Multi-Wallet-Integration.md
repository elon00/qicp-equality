# Multi-Wallet Integration Guide

## 1. Supported Internet Computer Wallets

The QICP Equality frontend natively supports four primary authentication providers:

1. **Internet Identity (II)**:
   - Zero-password, hardware-backed WebAuthn biometric passkey authentication.
   - Pseudonymous delegation identity protecting user privacy across canisters.
2. **Plug Wallet**:
   - Browser extension & mobile wallet supporting ICRC-1 tokens and direct canister inter-calls.
3. **NFID**:
   - Web3 sovereign identity with Google/Email single sign-on options for non-technical community organizers.
4. **Bitfinity Wallet**:
   - Multi-chain wallet bridging Ethereum Virtual Machine (EVM) and native ICP canister operations.

---

## 2. Multi-Crypto QR Payment Specifications

For field disbursements where internet bandwidth is constrained:
- **QICP (ICRC-1)**: `icp:<principal>?amount=<e8s>&token=QICP`
- **Bitcoin (ckBTC)**: `bitcoin:<btc_address>?amount=<sats>`
- **Ethereum (ckETH)**: `ethereum:<eth_address>?value=<wei>`
