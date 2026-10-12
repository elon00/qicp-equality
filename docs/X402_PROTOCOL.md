# RFC HTTP 402 Pay-Per-Inference Bazaar Protocol Specification

## 1. Abstract

The **x402 Bazaar Protocol** is an implementation of standard RFC HTTP 402 ("Payment Required") tailored for the Internet Computer Protocol (ICP). It provides micro-payment capabilities for AI agents, decentralized compute services, and canister API access using native ICRC-1 tokens.

---

## 2. Protocol Flow

```
   CLIENT                                              CANISTER / GATEWAY
     |                                                          |
     |   1. POST /api/ai/inclusion-audit (No Receipt)           |
     |--------------------------------------------------------->|
     |                                                          |
     |   2. HTTP 402 Payment Required                           |
     |      Header: WWW-Authenticate: x402-icp                  |
     |      Header: X-Payment-Challenge: <Base64 JSON>          |
     |<---------------------------------------------------------|
     |                                                          |
     |   3. Client executes ICRC-1 Transfer on ICP Ledger       |
     |      (Pays amount to Canister Principal, notes nonce)    |
     |                                                          |
     |   4. POST /api/ai/inclusion-audit                        |
     |      Header: X-Payment-Receipt: <Base64 Receipt>         |
     |      Header: X-Payment-Signature: <PQC ML-DSA-65 Sig>    |
     |--------------------------------------------------------->|
     |                                                          |
     |   5. Gateway verifies block index, nonce & amount        |
     |      Executes 50% BME Burn + 50% Treasury Deposit        |
     |      Processes AI Inference / Service                    |
     |                                                          |
     |   6. HTTP 200 OK (With Service Output & Settlement Audit)|
     |<---------------------------------------------------------|
```

---

## 3. Challenge Specification

When an unauthenticated or unpaid request arrives at a protected endpoint, the server responds with:

```http
HTTP/1.1 402 Payment Required
Content-Type: application/json
WWW-Authenticate: x402-icp realm="qicp-bazaar"
X-Payment-Challenge: eyJ2ZXJzaW9uIjogIng0MDI6djE6aWNwIiwg...
```

Decoded JSON payload:
```json
{
  "version": "x402:v1:icp",
  "currency": "QICP",
  "pay_to_principal": "qicp-treasury-rrkah-fqaaa-aaaaa-aaaaq-cai",
  "amount_e8s": 200000,
  "service_id": "ai:inclusion-audit",
  "nonce": "110f4a755461e3299f3fc34b09a9535d",
  "issued_at": 1773489000,
  "expires_at": 1773489300
}
```

---

## 4. Payment Receipt Specification

The client submits payment proof via the `X-Payment-Receipt` header:

```json
{
  "version": "x402:v1:icp",
  "service_id": "ai:inclusion-audit",
  "nonce": "110f4a755461e3299f3fc34b09a9535d",
  "block_index": 104829,
  "payer_principal": "rdmx6-jaaaa-aaaaa-aaadq-cai",
  "amount_e8s": 200000
}
```

---

## 5. Security Invariants & Anti-Replay

1. **Composite Uniqueness**: Each receipt is tracked by its unique key `block_index:nonce`. Once settled, any duplicate presentation is immediately rejected with HTTP 400.
2. **TTL Expiration**: Challenges expire after 300 seconds (5 minutes). Unclaimed expired nonces are purged from memory.
3. **Burn-and-Mint Equilibrium (BME)**: 50% of the payment fee is burned on-chain, and 50% is credited to the treasury escrow.
