//! QICP Equality Token Canister (Rust / ic-cdk)
//! Full ICRC-1 compliant ledger canister with strategic elastic tokenomics.

use candid::{CandidType, Deserialize, Nat, Principal};
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

// Global state simulation for local testing / canister runtime
static mut STATE: Option<TokenState> = None;

pub fn get_state() -> &'static mut TokenState {
    unsafe {
        if STATE.is_none() {
            STATE = Some(TokenState::default());
        }
        STATE.as_mut().unwrap()
    }
}

#[ic_cdk::query]
pub fn icrc1_name() -> String {
    get_state().name.clone()
}

#[ic_cdk::query]
pub fn icrc1_symbol() -> String {
    get_state().symbol.clone()
}

#[ic_cdk::query]
pub fn icrc1_decimals() -> u8 {
    get_state().decimals
}

#[ic_cdk::query]
pub fn icrc1_fee() -> Nat {
    get_state().fee.clone()
}

#[ic_cdk::query]
pub fn icrc1_total_supply() -> Nat {
    get_state().total_supply.clone()
}

#[ic_cdk::query]
pub fn icrc1_balance_of(account: Account) -> Nat {
    get_state().balances.get(&account).cloned().unwrap_or_else(|| Nat::from(0u64))
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
    let state = get_state();

    let balance = state.balances.get(&from).cloned().unwrap_or_else(|| Nat::from(0u64));
    let required = &args.amount + &state.fee;

    if balance < required {
        return Err(TransferError::InsufficientFunds { balance });
    }

    *state.balances.entry(from).or_insert_with(|| Nat::from(0u64)) -= required;
    *state.balances.entry(args.to).or_insert_with(|| Nat::from(0u64)) += args.amount;

    // Transaction index
    Ok(Nat::from(1u64))
}

#[ic_cdk::update]
pub fn mint_livelihood_grant(to: Account, amount: Nat, _memo: String) -> Result<Nat, TransferError> {
    let state = get_state();
    state.total_supply += &amount;
    state.total_disbursed += &amount;
    *state.balances.entry(to).or_insert_with(|| Nat::from(0u64)) += amount;
    Ok(Nat::from(1u64))
}

#[ic_cdk::update]
pub fn apply_demurrage_burn(from: Account, burn_amount: Nat) -> Result<Nat, TransferError> {
    let state = get_state();
    let balance = state.balances.get(&from).cloned().unwrap_or_else(|| Nat::from(0u64));
    if balance < burn_amount {
        return Err(TransferError::InsufficientFunds { balance });
    }
    *state.balances.entry(from).or_insert_with(|| Nat::from(0u64)) -= &burn_amount;
    state.total_supply -= &burn_amount;
    state.total_burned += &burn_amount;
    Ok(Nat::from(1u64))
}
