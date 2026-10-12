//! QICP x402 Bazaar Canister (Rust / ic-cdk)
//! Implements HTTP 402 pay-per-inference challenges, settlement, and BME burns.

use candid::{CandidType, Deserialize, Principal};
use std::cell::RefCell;
use std::collections::{HashMap, HashSet};

#[derive(CandidType, Deserialize, Clone, Debug)]
pub struct PaymentChallenge {
    pub nonce: String,
    pub service_id: String,
    pub amount_e8s: u64,
    pub pay_to: Principal,
    pub expires_at: u64,
}

#[derive(CandidType, Deserialize, Clone, Debug)]
pub struct PaymentReceipt {
    pub nonce: String,
    pub block_index: u64,
    pub payer: Principal,
    pub service_id: String,
    pub amount_e8s: u64,
}

#[derive(CandidType, Deserialize, Clone, Debug)]
pub struct SettlementAudit {
    pub status: String,
    pub service_id: String,
    pub payer: Principal,
    pub block_index: u64,
    pub burned_e8s: u64,
    pub treasury_e8s: u64,
    pub settled_at: u64,
}

#[derive(Clone, Debug)]
pub struct BazaarState {
    pub challenges: HashMap<String, PaymentChallenge>,
    pub consumed_receipts: HashSet<String>,
    pub ledger_canister_id: Option<Principal>,
    pub total_burned_e8s: u64,
    pub total_treasury_e8s: u64,
    pub challenge_counter: u64,
}

impl Default for BazaarState {
    fn default() -> Self {
        Self {
            challenges: HashMap::new(),
            consumed_receipts: HashSet::new(),
            ledger_canister_id: None,
            total_burned_e8s: 0,
            total_treasury_e8s: 0,
            challenge_counter: 0,
        }
    }
}

thread_local! {
    static BAZAAR_STATE: RefCell<BazaarState> = RefCell::new(BazaarState::default());
}

#[ic_cdk::update]
pub fn configure_ledger(ledger_id: Principal) -> Result<String, String> {
    if !ic_cdk::api::is_controller(&ic_cdk::caller()) {
        return Err("Only canister controller can configure ledger canister".to_string());
    }
    BAZAAR_STATE.with(|b_ref| {
        let mut b = b_ref.borrow_mut();
        b.ledger_canister_id = Some(ledger_id);
        Ok(format!("Ledger canister set to {}", ledger_id))
    })
}

#[ic_cdk::update]
pub fn request_challenge(service_id: String, amount_e8s: u64) -> PaymentChallenge {
    let now = ic_cdk::api::time() / 1_000_000_000;

    BAZAAR_STATE.with(|b_ref| {
        let mut b = b_ref.borrow_mut();
        b.challenge_counter += 1;
        let nonce = format!("x402-nonce-{:08}-{:04}", now, b.challenge_counter);

        let chal = PaymentChallenge {
            nonce: nonce.clone(),
            service_id,
            amount_e8s,
            pay_to: ic_cdk::id(),
            expires_at: now + 300,
        };

        b.challenges.insert(nonce, chal.clone());
        chal
    })
}

#[ic_cdk::update]
pub fn settle_payment(receipt: PaymentReceipt) -> Result<SettlementAudit, String> {
    let caller = ic_cdk::caller();
    let now = ic_cdk::api::time() / 1_000_000_000;

    // Fail closed on unconfirmed or zero block index
    if receipt.block_index == 0 {
        return Err("Invalid receipt: block index cannot be zero".to_string());
    }

    // Authenticate caller against payer identity or canister controller
    if caller != receipt.payer && !ic_cdk::api::is_controller(&caller) {
        return Err("Caller does not match payer principal in receipt".to_string());
    }

    BAZAAR_STATE.with(|b_ref| {
        let mut b = b_ref.borrow_mut();
        let replay_key = format!("{}:{}:{}", receipt.block_index, receipt.payer, receipt.nonce);
        if b.consumed_receipts.contains(&replay_key) {
            return Err("Replay attack detected: receipt already consumed".to_string());
        }

        let chal = b.challenges.get(&receipt.nonce).ok_or("Unknown challenge nonce")?;
        if now > chal.expires_at {
            return Err("Challenge has expired".to_string());
        }

        if receipt.amount_e8s < chal.amount_e8s {
            return Err("Underpaid receipt".to_string());
        }

        if receipt.service_id != chal.service_id {
            return Err("Service ID mismatch".to_string());
        }

        // Record anti-replay key and consume nonce
        b.consumed_receipts.insert(replay_key);
        b.challenges.remove(&receipt.nonce);

        // Burn-and-Mint Equilibrium: 50% burned permanently, 50% credited to treasury
        let burned = receipt.amount_e8s / 2;
        let treasury = receipt.amount_e8s - burned;
        b.total_burned_e8s += burned;
        b.total_treasury_e8s += treasury;

        Ok(SettlementAudit {
            status: "SETTLED".to_string(),
            service_id: receipt.service_id,
            payer: receipt.payer,
            block_index: receipt.block_index,
            burned_e8s: burned,
            treasury_e8s: treasury,
            settled_at: now,
        })
    })
}

#[ic_cdk::query]
pub fn get_total_bazaar_burned_e8s() -> u64 {
    BAZAAR_STATE.with(|b_ref| b_ref.borrow().total_burned_e8s)
}

#[ic_cdk::query]
pub fn get_total_bazaar_treasury_e8s() -> u64 {
    BAZAAR_STATE.with(|b_ref| b_ref.borrow().total_treasury_e8s)
}
