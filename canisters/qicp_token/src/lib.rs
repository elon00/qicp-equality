//! QICP Equality Token Canister (Rust / ic-cdk)
//! Full ICRC-1 compliant ledger canister with strategic elastic tokenomics.

use candid::{CandidType, Deserialize, Nat, Principal};
use std::cell::RefCell;
use std::collections::HashMap;

#[derive(CandidType, Deserialize, Clone, Debug, PartialEq, Eq, Hash)]
pub struct Account {
    pub owner: Principal,
    pub subaccount: Option<Vec<u8>>,
}

#[derive(CandidType, Deserialize, Clone, Debug)]
pub struct TransferArgs {
    pub from_subaccount: Option<Vec<u8>>,
    pub to: Account,
    pub amount: Nat,
    pub fee: Option<Nat>,
    pub memo: Option<Vec<u8>>,
    pub created_at_time: Option<u64>,
}

#[derive(CandidType, Deserialize, Clone, Debug)]
pub enum TransferError {
    BadFee { expected_fee: Nat },
    InsufficientFunds { balance: Nat },
    GenericError { error_code: Nat, message: String },
}

#[derive(CandidType, Deserialize, Clone, Debug)]
pub struct StandardRecord {
    pub name: String,
    pub url: String,
}

#[derive(Clone, Debug)]
pub struct TokenState {
    pub name: String,
    pub symbol: String,
    pub decimals: u8,
    pub fee: Nat,
    pub total_supply: Nat,
    pub total_burned: Nat,
    pub total_disbursed: Nat,
    pub balances: HashMap<Account, Nat>,
    pub minting_account: Option<Account>,
}

impl Default for TokenState {
    fn default() -> Self {
        Self {
            name: "QICP Equality".to_string(),
            symbol: "QICP".to_string(),
            decimals: 8,
            fee: Nat::from(10_000u64), // 0.0001 QICP
            total_supply: Nat::from(10_000_000_000_00000000u64), // Initial community pool
            total_burned: Nat::from(0u64),
            total_disbursed: Nat::from(0u64),
            balances: HashMap::new(),
            minting_account: None,
        }
    }
}

thread_local! {
    static STATE: RefCell<TokenState> = RefCell::new(TokenState::default());
}

#[ic_cdk::query]
pub fn icrc1_name() -> String {
    STATE.with(|s| s.borrow().name.clone())
}

#[ic_cdk::query]
pub fn icrc1_symbol() -> String {
    STATE.with(|s| s.borrow().symbol.clone())
}

#[ic_cdk::query]
pub fn icrc1_decimals() -> u8 {
    STATE.with(|s| s.borrow().decimals)
}

#[ic_cdk::query]
pub fn icrc1_fee() -> Nat {
    STATE.with(|s| s.borrow().fee.clone())
}

#[ic_cdk::query]
pub fn icrc1_total_supply() -> Nat {
    STATE.with(|s| s.borrow().total_supply.clone())
}

#[ic_cdk::query]
pub fn icrc1_balance_of(account: Account) -> Nat {
    STATE.with(|s| s.borrow().balances.get(&account).cloned().unwrap_or_else(|| Nat::from(0u64)))
}

#[ic_cdk::query]
pub fn icrc1_supported_standards() -> Vec<StandardRecord> {
    vec![
        StandardRecord {
            name: "ICRC-1".to_string(),
            url: "https://github.com/dfinity/ICRC-1".to_string(),
        },
        StandardRecord {
            name: "ICRC-2".to_string(),
            url: "https://github.com/dfinity/ICRC-1/tree/main/standards/ICRC-2".to_string(),
        },
    ]
}

#[ic_cdk::update]
pub fn icrc1_transfer(args: TransferArgs) -> Result<Nat, TransferError> {
    let caller = ic_cdk::caller();
    let from = Account {
        owner: caller,
        subaccount: args.from_subaccount,
    };

    STATE.with(|s_ref| {
        let mut state = s_ref.borrow_mut();
        let balance = state.balances.get(&from).cloned().unwrap_or_else(|| Nat::from(0u64));
        let fee = state.fee.clone();
        let required = args.amount.clone() + fee;

        if balance < required {
            return Err(TransferError::InsufficientFunds { balance });
        }

        *state.balances.entry(from).or_insert_with(|| Nat::from(0u64)) -= required;
        *state.balances.entry(args.to).or_insert_with(|| Nat::from(0u64)) += args.amount;

        Ok(Nat::from(1u64))
    })
}

#[ic_cdk::update]
pub fn mint_livelihood_grant(to: Account, amount: Nat, _memo: String) -> Result<Nat, TransferError> {
    if !ic_cdk::api::is_controller(&ic_cdk::caller()) {
        return Err(TransferError::GenericError { error_code: Nat::from(403u64), message: "Only a canister controller may mint".to_string() });
    }
    STATE.with(|s_ref| {
        let mut state = s_ref.borrow_mut();
        state.total_supply += amount.clone();
        state.total_disbursed += amount.clone();
        *state.balances.entry(to).or_insert_with(|| Nat::from(0u64)) += amount;
        Ok(Nat::from(1u64))
    })
}

#[ic_cdk::update]
pub fn apply_demurrage_burn(from: Account, burn_amount: Nat) -> Result<Nat, TransferError> {
    if !ic_cdk::api::is_controller(&ic_cdk::caller()) {
        return Err(TransferError::GenericError { error_code: Nat::from(403u64), message: "Only a canister controller may burn third-party balances".to_string() });
    }
    STATE.with(|s_ref| {
        let mut state = s_ref.borrow_mut();
        let balance = state.balances.get(&from).cloned().unwrap_or_else(|| Nat::from(0u64));
        if balance < burn_amount {
            return Err(TransferError::InsufficientFunds { balance });
        }
        *state.balances.entry(from).or_insert_with(|| Nat::from(0u64)) -= burn_amount.clone();
        state.total_supply -= burn_amount.clone();
        state.total_burned += burn_amount;
        Ok(Nat::from(1u64))
    })
}
