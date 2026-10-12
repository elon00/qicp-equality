# Incident Response & Disaster Recovery Runbook

## 1. Classification & Severity

| Incident Level | Scenario | Action Protocol |
| :--- | :--- | :--- |
| **P0 - Critical** | Canister controller key exposure or treasury drain attempt. | Trigger immediate canister controller freeze via emergency governance; cancel active proposals within dispute timelock. |
| **P1 - High** | Suspected sybil swarm proposal collusion. | Initiate governance dispute flag; halt treasury disbursement during 7-day timelock window. |
| **P2 - Moderate** | Boundary node outage or local replica degradation. | Failover traffic to secondary boundary node (`https://icp-api.io`). |

---

## 2. Emergency Proposal Cancellation (During Timelock)

Any proposal flagged by community audit or AI fraud detection can be frozen during its 7-day dispute window:

```bash
dfx canister call treasury cancel_disputed_grant '("PROP-QICP-000042", "Fraudulent sybil cluster detected")'
```
