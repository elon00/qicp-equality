//! QICP Treasury & Escrow Canister (Rust / ic-cdk)
//! Manages proposal lifecycles, Conway neighborhood voting, dispute timelocks, and disbursements.

use candid::{CandidType, Deserialize, Principal};
use std::cell::RefCell;
use std::collections::{HashMap, HashSet};

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
    pub votes_for: u64,
    pub votes_against: u64,
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

#[derive(Clone, Debug)]
pub struct TreasuryState {
    pub admin: Principal,
    pub proposals: HashMap<String, GrantProposal>,
    pub voters: HashMap<String, HashSet<Principal>>,
    pub proposal_count: u64,
    pub balance_e8s: u64,
}

impl Default for TreasuryState {
    fn default() -> Self {
        Self {
            admin: Principal::anonymous(),
            proposals: HashMap::new(),
            voters: HashMap::new(),
            proposal_count: 0,
            balance_e8s: 1_000_000_000_00000000, // 1 Billion QICP initial reserve
        }
    }
}

thread_local! {
    static TREASURY_STATE: RefCell<TreasuryState> = RefCell::new(TreasuryState::default());
}

#[ic_cdk::update]
pub fn submit_proposal(sub: ProposalSubmission) -> Result<String, String> {
    let caller = ic_cdk::caller();
    let now = ic_cdk::api::time() / 1_000_000_000;
    let dispute_period_seconds = 7 * 86400; // 7 days dispute window

    TREASURY_STATE.with(|t_ref| {
        let mut treasury = t_ref.borrow_mut();
        treasury.proposal_count += 1;
        let prop_id = format!("PROP-QICP-{:06}", treasury.proposal_count);

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
            votes_for: 0,
            votes_against: 0,
        };

        treasury.proposals.insert(prop_id.clone(), proposal);
        treasury.voters.insert(prop_id.clone(), HashSet::new());
        Ok(prop_id)
    })
}

#[ic_cdk::update]
pub fn vote_proposal(prop_id: String, support: bool) -> Result<String, String> {
    let caller = ic_cdk::caller();

    TREASURY_STATE.with(|t_ref| {
        let mut treasury = t_ref.borrow_mut();
        if treasury.voters.entry(prop_id.clone()).or_default().contains(&caller) {
            return Err("Caller has already voted on this proposal".to_string());
        }

        let prop = treasury.proposals.get_mut(&prop_id).ok_or("Proposal not found")?;
        if prop.status != GrantStatus::Submitted && prop.status != GrantStatus::UnderReview {
            return Err("Proposal not in voting state".to_string());
        }

        if support {
            prop.votes_for += 1;
        } else {
            prop.votes_against += 1;
        }

        let votes_for = prop.votes_for;
        let votes_against = prop.votes_against;
        if votes_for >= 3 && votes_for > votes_against {
            prop.status = GrantStatus::Approved;
        }
        let status = prop.status.clone();

        treasury.voters.entry(prop_id.clone()).or_default().insert(caller);

        Ok(format!(
            "Vote recorded. Current tally: {} for, {} against. Status: {:?}",
            votes_for, votes_against, status
        ))
    })
}

#[ic_cdk::update]
pub fn approve_proposal(prop_id: String) -> Result<String, String> {
    if !ic_cdk::api::is_controller(&ic_cdk::caller()) {
        return Err("Only canister controller can manually approve proposals".to_string());
    }

    TREASURY_STATE.with(|t_ref| {
        let mut treasury = t_ref.borrow_mut();
        let prop = treasury.proposals.get_mut(&prop_id).ok_or("Proposal not found")?;
        if prop.status != GrantStatus::Submitted && prop.status != GrantStatus::UnderReview {
            return Err("Proposal cannot be approved in its current state".to_string());
        }

        prop.status = GrantStatus::Approved;
        Ok(format!("Proposal {} approved by controller", prop_id))
    })
}

#[ic_cdk::update]
pub fn disburse_grant(prop_id: String) -> Result<String, String> {
    if !ic_cdk::api::is_controller(&ic_cdk::caller()) {
        return Err("Unauthorized disbursement: caller must be controller".to_string());
    }
    let now = ic_cdk::api::time() / 1_000_000_000;

    TREASURY_STATE.with(|t_ref| {
        let mut treasury = t_ref.borrow_mut();

        let (amount_e8s, unlock_timestamp, status, beneficiary) = {
            let prop = treasury.proposals.get(&prop_id).ok_or("Proposal not found")?;
            (prop.amount_e8s, prop.unlock_timestamp, prop.status.clone(), prop.beneficiary)
        };

        if status != GrantStatus::Approved {
            return Err("Invalid status: grant must be Approved before disbursement".to_string());
        }

        if now < unlock_timestamp {
            return Err("Dispute timelock not yet elapsed (7-day window active)".to_string());
        }

        if treasury.balance_e8s < amount_e8s {
            return Err("Insufficient liquid treasury balance".to_string());
        }

        treasury.balance_e8s -= amount_e8s;
        if let Some(prop) = treasury.proposals.get_mut(&prop_id) {
            prop.status = GrantStatus::Disbursed;
        }

        Ok(format!("Disbursed {} e8s to {}", amount_e8s, beneficiary))
    })
}

#[ic_cdk::update]
pub fn cancel_disputed_grant(prop_id: String, reason: String) -> Result<String, String> {
    let caller = ic_cdk::caller();
    let now = ic_cdk::api::time() / 1_000_000_000;

    TREASURY_STATE.with(|t_ref| {
        let mut treasury = t_ref.borrow_mut();
        if !ic_cdk::api::is_controller(&caller) {
            return Err("Unauthorized: only controller may cancel disputed grants".to_string());
        }

        let prop = treasury.proposals.get_mut(&prop_id).ok_or("Proposal not found")?;
        if now >= prop.unlock_timestamp {
            return Err("Dispute window elapsed; grant can no longer be cancelled".to_string());
        }

        prop.status = GrantStatus::Cancelled;
        Ok(format!("Proposal {} cancelled: {}", prop_id, reason))
    })
}

#[ic_cdk::query]
pub fn get_proposal(prop_id: String) -> Option<GrantProposal> {
    TREASURY_STATE.with(|t_ref| t_ref.borrow().proposals.get(&prop_id).cloned())
}

#[ic_cdk::query]
pub fn list_proposals() -> Vec<GrantProposal> {
    TREASURY_STATE.with(|t_ref| t_ref.borrow().proposals.values().cloned().collect())
}

#[ic_cdk::query]
pub fn get_treasury_balance_e8s() -> u64 {
    TREASURY_STATE.with(|t_ref| t_ref.borrow().balance_e8s)
}
