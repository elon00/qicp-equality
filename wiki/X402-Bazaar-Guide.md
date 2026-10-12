# RFC HTTP 402 Bazaar Protocol Guide

The **x402 Bazaar Protocol** provides an open, decentralized micro-payment monetization rail for artificial intelligence (AI) model inference and API resource queries on the Internet Computer.

---

## 1. Protocol Architecture

The protocol adheres to standard **RFC 7231 / RFC 9110 HTTP 402 (Payment Required)** specifications, enabling seamless edge client and automated bot interaction.

```
Edge Client                   FastAPI Gateway                 x402 Bazaar Canister
    │                                │                                 │
    ├───── 1. POST /api/chat ───────►│                                 │
    │      (without payment)         │                                 │
    │                                ├──── 2. Request Challenge ──────►│
    │                                │◄─── 3. Nonce & Amount (e8s) ────┤
    │◄──── 4. HTTP 402 Response ─────┤                                 │
    │      (Nonce, Target Principal) │                                 │
    │                                │                                 │
    ├───── 5. Settle On-Chain ───────┼────────────────────────────────►│ (Ledger)
    │      (Transfer with memo)      │                                 │
    │                                │                                 │
    ├───── 6. POST /api/chat ───────►│                                 │
    │      (with X-402-Receipt)      ├──── 7. settle_payment() ───────►│
    │                                │◄─── 8. SETTLED (50% Burned) ────┤
    │                                ├──── 9. Run AI Multi-Model ──────┤
    │◄──── 10. HTTP 200 Success ─────┤                                 │
```

---

## 2. Challenge & Settlement Headers

### Challenge Response (HTTP 402)
```http
HTTP/1.1 402 Payment Required
Content-Type: application/json
WWW-Authenticate: X-402 realm="QICP Bazaar", nonce="x402-nonce-1718000-0001", amount="100000", pay_to="rrkah-fqaaa-aaaaa-aaaaq-cai"

{
  "error": "Payment Required",
  "challenge": {
    "nonce": "x402-nonce-1718000-0001",
    "service_id": "ai-multimodel-reasoning",
    "amount_e8s": 100000,
    "pay_to": "rrkah-fqaaa-aaaaa-aaaaq-cai",
    "expires_at": 1718000300
  }
}
```

### Payment Receipt Request Header
When repeating the API request, attach the payment proof:
```http
POST /api/ai/bazaar/chat HTTP/1.1
Content-Type: application/json
X-402-Receipt: {"nonce": "x402-nonce-1718000-0001", "block_index": 10429, "payer": "2vxsx-fae", "service_id": "ai-multimodel-reasoning", "amount_e8s": 100000}
```

---

## 3. Burn-and-Mint Equilibrium (BME)

Every confirmed payment is automatically partitioned:
- **50% Permanently Burned**: Deflationary mechanism offsetting public goods minting.
- **50% Deposited to Treasury**: Funds community grants for Moolnivasi and marginalized founders.

Anti-replay protection indexes `block_index + nonce` in an in-memory set to prevent double redemption.
