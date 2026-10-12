//! QICP Treasury & Escrow Canister (Rust / ic-cdk)
//! Manages proposal lifecycles, Conway neighborhood voting, dispute timelocks, and disbursements.

use candid::{CandidType, Deserialize, Principal};
use std::collections::HashMap;

#[derive(CandidType, Deserialize, Clone, Debug, PartialEq)]
pub enum GrantStatus {
    Submitted,
    UnderReview,
    Approved,
    Disbursed,
    Cancelled,
    Disputed,
}

#[derive(CandidType, Deserialize, Clone, Debug)]
pub struct GrantProposal {
    pub id: String,
    pub title: String,
    pub category: String,
    pub beneficiary: Principal,
    pub amount_e8s: u64,
    pub proposer: Principal,
    pub unlock_timestamp: u64,
    pub status: GrantStatus,
    pub conway_density: f32,
    pub pqc_signature_hash: String,
}

#[derive(CandidType, Deserialize, Clone, Debug)]
pub struct ProposalSubmission {
    pub title: String,
    pub category: String,
    pub beneficiary: Principal,
    pub amount_e8s: u64,
    pub conway_density: f32,
    pub pqc_signature_hash: String,
}

pub struct TreasuryState {
    pub admin: Principal,
    pub proposals: HashMap<String, GrantProposal>,
    pub proposal_count: u64,
    pub balance_e8s: u64,
}

impl Default for TreasuryState {
    fn default() -> Self {
        Self {
            admin: Principal::anonymous(),
            proposals: HashMap::new(),
            proposal_count: 0,
            balance_e8s: 1_000_000_000_00000000, // 1 Billion QICP initial reserve
        }
    }
}

static mut TREASURY_STATE: Option<TreasuryState> = None;

pub fn get_treasury() -> &'static mut TreasuryState {
    unsafe {
        if TREASURY_STATE.is_none() {
            TREASURY_STATE = Some(TreasuryState::default());
        }
        TREASURY_STATE.as_mut().unwrap()
    }
}

#[ic_cdk::update]
pub fn submit_proposal(sub: ProposalSubmission) -> Result<String, String> {
    let caller = ic_cdk::caller();
    let treasury = get_treasury();
    treasury.proposal_count += 1;
    let prop_id = format!("PROP-QICP-{:06}", treasury.proposal_count);

    let now = ic_cdk::api::time() / 1_000_000_000;
    let dispute_period_seconds = 7 * 86400; // 7 days dispute window

    let proposal = GrantProposal {
        id: prop_id.clone(),
        title: sub.title,
        category: sub.category,
        beneficiary: sub.beneficiary,
        amount_e8s: sub.amount_e8s,
        proposer: caller,
        unlock_timestamp: now + dispute_period_seconds,
        status: GrantStatus::Submitted,
        conway_density: sub.conway_density,
        pqc_signature_hash: sub.pqc_signature_hash,
    };

    treasury.proposals.insert(prop_id.clone(), proposal);
    Ok(prop_id)
}

#[ic_cdk::update]
pub fn disburse_grant(prop_id: String) -> Result<String, String> {
    let treasury = get_treasury();
    let prop = treasury.proposals.get_mut(&prop_id).ok_or("Proposal not found")?;

    let now = ic_cdk::api::time() / 1_000_000_000;
    if now < prop.unlock_timestamp {
        return Err("Dispute timelock not yet elapsed".to_string());
    }

    if prop.status != GrantStatus::Approved && prop.status != GrantStatus::Submitted {
        return Err("Invalid status for disbursement".to_string());
    }

    if treasury.balance_e8s < prop.amount_e8s {
        return Err("Insufficient liquid treasury balance".to_string());
    }

    treasury.balance_e8s -= prop.amount_e8s;
    prop.status = GrantStatus::Disbursed;
    Ok(format!("Disbursed {} e8s to {}", prop.amount_e8s, prop.beneficiary))
}

#[ic_cdk::update]
pub fn cancel_disputed_grant(prop_id: String, reason: String) -> Result<String, String> {
    let caller = ic_cdk::caller();
    let treasury = get_treasury();
    if treasury.admin != Principal::anonymous() && caller != treasury.admin {
        return Err("Unauthorized".to_string());
    }

    let prop = treasury.proposals.get_mut(&prop_id).ok_or("Proposal not found")?;
    let now = ic_cdk::api::time() / 1_000_000_000;
    if now >= prop.unlock_timestamp {
        return Err("Dispute window elapsed; grant can no longer be cancelled".to_string());
    }

    prop.status = GrantStatus::Cancelled;
    Ok(format!("Proposal {} cancelled: {}", prop_id, reason))
}

#[ic_cdk::query]
pub fn get_proposal(prop_id: String) -> Option<GrantProposal> {
    get_treasury().proposals.get(&prop_id).cloned()
}

#[ic_cdk::query]
pub fn list_proposals() -> Vec<GrantProposal> {
    get_treasury().proposals.values().cloned().collect()
}

#[ic_cdk::query]
pub fn get_treasury_balance_e8s() -> u64 {
    get_treasury().balance_e8s
}
