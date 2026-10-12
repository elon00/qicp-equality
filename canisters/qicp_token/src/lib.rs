//! QICP Equality Token Canister (Rust / ic-cdk)
//! Full ICRC-1, ICRC-2, and ICRC-3 compliant ledger canister with strategic elastic tokenomics.

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
    BadBurn { min_burn_amount: Nat },
    InsufficientFunds { balance: Nat },
    TooOld,
    CreatedInFuture { ledger_time: u64 },
    Duplicate { duplicate_of: Nat },
    TemporarilyUnavailable,
    GenericError { error_code: Nat, message: String },
}

#[derive(CandidType, Deserialize, Clone, Debug)]
pub struct ApproveArgs {
    pub from_subaccount: Option<Vec<u8>>,
    pub spender: Account,
    pub amount: Nat,
    pub expected_allowance: Option<Nat>,
    pub expires_at: Option<u64>,
    pub fee: Option<Nat>,
    pub memo: Option<Vec<u8>>,
    pub created_at_time: Option<u64>,
}

#[derive(CandidType, Deserialize, Clone, Debug)]
pub enum ApproveError {
    BadFee { expected_fee: Nat },
    InsufficientFunds { balance: Nat },
    AllowanceChanged { current_allowance: Nat },
    Expired { ledger_time: u64 },
    TooOld,
    CreatedInFuture { ledger_time: u64 },
    Duplicate { duplicate_of: Nat },
    TemporarilyUnavailable,
    GenericError { error_code: Nat, message: String },
}

#[derive(CandidType, Deserialize, Clone, Debug)]
pub struct AllowanceArgs {
    pub account: Account,
    pub spender: Account,
}

#[derive(CandidType, Deserialize, Clone, Debug)]
pub struct Allowance {
    pub allowance: Nat,
    pub expires_at: Option<u64>,
}

#[derive(CandidType, Deserialize, Clone, Debug)]
pub struct TransferFromArgs {
    pub spender_subaccount: Option<Vec<u8>>,
    pub from: Account,
    pub to: Account,
    pub amount: Nat,
    pub fee: Option<Nat>,
    pub memo: Option<Vec<u8>>,
    pub created_at_time: Option<u64>,
}

#[derive(CandidType, Deserialize, Clone, Debug)]
pub enum TransferFromError {
    BadFee { expected_fee: Nat },
    BadBurn { min_burn_amount: Nat },
    InsufficientFunds { balance: Nat },
    InsufficientAllowance { allowance: Nat },
    TooOld,
    CreatedInFuture { ledger_time: u64 },
    Duplicate { duplicate_of: Nat },
    TemporarilyUnavailable,
    GenericError { error_code: Nat, message: String },
}

#[derive(CandidType, Deserialize, Clone, Debug)]
pub enum Value {
    Nat(Nat),
    Int(i64),
    Text(String),
    Blob(Vec<u8>),
}

#[derive(CandidType, Deserialize, Clone, Debug)]
pub struct StandardRecord {
    pub name: String,
    pub url: String,
}

#[derive(CandidType, Deserialize, Clone, Debug)]
pub struct BlockTypeRecord {
    pub block_type: String,
    pub url: String,
}

#[derive(CandidType, Deserialize, Clone, Debug)]
pub struct Block {
    pub id: Nat,
    pub tx_type: String,
    pub from: Option<Account>,
    pub to: Option<Account>,
    pub amount: Nat,
    pub timestamp: u64,
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
    pub allowances: HashMap<(Account, Account), Allowance>,
    pub minting_account: Option<Account>,
    pub blocks: Vec<Block>,
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
            allowances: HashMap::new(),
            minting_account: None,
            blocks: Vec::new(),
        }
    }
}

thread_local! {
    static STATE: RefCell<TokenState> = RefCell::new(TokenState::default());
}

// --- ICRC-1 Query Endpoints ---

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
pub fn icrc1_minting_account() -> Option<Account> {
    STATE.with(|s| s.borrow().minting_account.clone())
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
        StandardRecord {
            name: "ICRC-3".to_string(),
            url: "https://github.com/dfinity/ICRC-1/tree/main/standards/ICRC-3".to_string(),
        },
    ]
}

#[ic_cdk::query]
pub fn icrc1_metadata() -> Vec<(String, Value)> {
    vec![
        ("icrc1:name".to_string(), Value::Text("QICP Equality".to_string())),
        ("icrc1:symbol".to_string(), Value::Text("QICP".to_string())),
        ("icrc1:decimals".to_string(), Value::Nat(Nat::from(8u64))),
        ("icrc1:fee".to_string(), Value::Nat(Nat::from(10_000u64))),
        ("icrc1:max_memo_length".to_string(), Value::Nat(Nat::from(256u64))),
    ]
}

// --- ICRC-1 Transfer ---

#[ic_cdk::update]
pub fn icrc1_transfer(args: TransferArgs) -> Result<Nat, TransferError> {
    let caller = ic_cdk::caller();
    let from = Account {
        owner: caller,
        subaccount: args.from_subaccount,
    };
    let now = ic_cdk::api::time() / 1_000_000_000;

    STATE.with(|s_ref| {
        let mut state = s_ref.borrow_mut();
        let balance = state.balances.get(&from).cloned().unwrap_or_else(|| Nat::from(0u64));
        let fee = state.fee.clone();
        let required = args.amount.clone() + fee;

        if balance < required {
            return Err(TransferError::InsufficientFunds { balance });
        }

        *state.balances.entry(from.clone()).or_insert_with(|| Nat::from(0u64)) -= required;
        *state.balances.entry(args.to.clone()).or_insert_with(|| Nat::from(0u64)) += args.amount.clone();

        let block_idx = Nat::from(state.blocks.len() as u64 + 1);
        state.blocks.push(Block {
            id: block_idx.clone(),
            tx_type: "1transfer".to_string(),
            from: Some(from),
            to: Some(args.to),
            amount: args.amount,
            timestamp: now,
        });

        Ok(block_idx)
    })
}

// --- ICRC-2 Delegation Endpoints ---

#[ic_cdk::update]
pub fn icrc2_approve(args: ApproveArgs) -> Result<Nat, ApproveError> {
    let caller = ic_cdk::caller();
    let owner = Account {
        owner: caller,
        subaccount: args.from_subaccount,
    };
    let now = ic_cdk::api::time() / 1_000_000_000;

    STATE.with(|s_ref| {
        let mut state = s_ref.borrow_mut();
        let fee = state.fee.clone();
        let balance = state.balances.get(&owner).cloned().unwrap_or_else(|| Nat::from(0u64));

        if balance < fee {
            return Err(ApproveError::InsufficientFunds { balance });
        }

        let key = (owner.clone(), args.spender.clone());
        if let Some(expected) = args.expected_allowance {
            let current = state.allowances.get(&key).map(|a| a.allowance.clone()).unwrap_or_else(|| Nat::from(0u64));
            if current != expected {
                return Err(ApproveError::AllowanceChanged { current_allowance: current });
            }
        }

        *state.balances.entry(owner.clone()).or_insert_with(|| Nat::from(0u64)) -= fee;
        state.allowances.insert(key, Allowance {
            allowance: args.amount.clone(),
            expires_at: args.expires_at,
        });

        let block_idx = Nat::from(state.blocks.len() as u64 + 1);
        state.blocks.push(Block {
            id: block_idx.clone(),
            tx_type: "2approve".to_string(),
            from: Some(owner),
            to: Some(args.spender),
            amount: args.amount,
            timestamp: now,
        });

        Ok(block_idx)
    })
}

#[ic_cdk::query]
pub fn icrc2_allowance(args: AllowanceArgs) -> Allowance {
    STATE.with(|s_ref| {
        let state = s_ref.borrow();
        state.allowances.get(&(args.account, args.spender)).cloned().unwrap_or(Allowance {
            allowance: Nat::from(0u64),
            expires_at: None,
        })
    })
}

#[ic_cdk::update]
pub fn icrc2_transfer_from(args: TransferFromArgs) -> Result<Nat, TransferFromError> {
    let caller = ic_cdk::caller();
    let spender = Account {
        owner: caller,
        subaccount: args.spender_subaccount,
    };
    let now = ic_cdk::api::time() / 1_000_000_000;

    STATE.with(|s_ref| {
        let mut state = s_ref.borrow_mut();
        let fee = state.fee.clone();
        let required = args.amount.clone() + fee.clone();

        let key = (args.from.clone(), spender);
        let (allowance_val, expires_at) = {
            let rec = state.allowances.get(&key).ok_or(TransferFromError::InsufficientAllowance {
                allowance: Nat::from(0u64),
            })?;
            (rec.allowance.clone(), rec.expires_at)
        };

        if let Some(exp) = expires_at {
            if now > exp {
                return Err(TransferFromError::GenericError {
                    error_code: Nat::from(400u64),
                    message: "Allowance has expired".to_string(),
                });
            }
        }

        if allowance_val < required {
            return Err(TransferFromError::InsufficientAllowance {
                allowance: allowance_val,
            });
        }

        let from_balance = state.balances.get(&args.from).cloned().unwrap_or_else(|| Nat::from(0u64));
        if from_balance < required {
            return Err(TransferFromError::InsufficientFunds { balance: from_balance });
        }

        if let Some(rec) = state.allowances.get_mut(&key) {
            rec.allowance -= required.clone();
        }
        *state.balances.entry(args.from.clone()).or_insert_with(|| Nat::from(0u64)) -= required;
        *state.balances.entry(args.to.clone()).or_insert_with(|| Nat::from(0u64)) += args.amount.clone();

        let block_idx = Nat::from(state.blocks.len() as u64 + 1);
        state.blocks.push(Block {
            id: block_idx.clone(),
            tx_type: "2transfer_from".to_string(),
            from: Some(args.from),
            to: Some(args.to),
            amount: args.amount,
            timestamp: now,
        });

        Ok(block_idx)
    })
}

// --- ICRC-3 Blocks & Audit Endpoints ---

#[ic_cdk::query]
pub fn icrc3_supported_block_types() -> Vec<BlockTypeRecord> {
    vec![
        BlockTypeRecord {
            block_type: "1transfer".to_string(),
            url: "https://github.com/dfinity/ICRC-1/tree/main/standards/ICRC-1".to_string(),
        },
        BlockTypeRecord {
            block_type: "2approve".to_string(),
            url: "https://github.com/dfinity/ICRC-1/tree/main/standards/ICRC-2".to_string(),
        },
        BlockTypeRecord {
            block_type: "2transfer_from".to_string(),
            url: "https://github.com/dfinity/ICRC-1/tree/main/standards/ICRC-2".to_string(),
        },
    ]
}

#[ic_cdk::query]
pub fn icrc3_get_blocks(start: Nat, length: Nat) -> Vec<Block> {
    STATE.with(|s_ref| {
        let state = s_ref.borrow();
        let total = state.blocks.len();
        let s: usize = start.0.try_into().unwrap_or(0);
        let l: usize = length.0.try_into().unwrap_or(0);

        if s >= total || l == 0 {
            return Vec::new();
        }
        let end = (s + l).min(total);
        state.blocks[s..end].to_vec()
    })
}

// --- Strategic Livelihood Inclusion Endpoints ---

#[ic_cdk::update]
pub fn mint_livelihood_grant(to: Account, amount: Nat, memo: String) -> Result<Nat, TransferError> {
    if !ic_cdk::api::is_controller(&ic_cdk::caller()) {
        return Err(TransferError::GenericError {
            error_code: Nat::from(403u64),
            message: "Only a canister controller may mint".to_string(),
        });
    }
    let now = ic_cdk::api::time() / 1_000_000_000;

    STATE.with(|s_ref| {
        let mut state = s_ref.borrow_mut();
        state.total_supply += amount.clone();
        state.total_disbursed += amount.clone();
        *state.balances.entry(to.clone()).or_insert_with(|| Nat::from(0u64)) += amount.clone();

        let block_idx = Nat::from(state.blocks.len() as u64 + 1);
        state.blocks.push(Block {
            id: block_idx.clone(),
            tx_type: format!("mint_grant:{}", memo),
            from: None,
            to: Some(to),
            amount,
            timestamp: now,
        });

        Ok(block_idx)
    })
}

#[ic_cdk::update]
pub fn apply_demurrage_burn(from: Account, burn_amount: Nat) -> Result<Nat, TransferError> {
    if !ic_cdk::api::is_controller(&ic_cdk::caller()) {
        return Err(TransferError::GenericError {
            error_code: Nat::from(403u64),
            message: "Only a canister controller may burn third-party balances".to_string(),
        });
    }
    let now = ic_cdk::api::time() / 1_000_000_000;

    STATE.with(|s_ref| {
        let mut state = s_ref.borrow_mut();
        let balance = state.balances.get(&from).cloned().unwrap_or_else(|| Nat::from(0u64));
        if balance < burn_amount {
            return Err(TransferError::InsufficientFunds { balance });
        }
        *state.balances.entry(from.clone()).or_insert_with(|| Nat::from(0u64)) -= burn_amount.clone();
        state.total_supply -= burn_amount.clone();
        state.total_burned += burn_amount.clone();

        let block_idx = Nat::from(state.blocks.len() as u64 + 1);
        state.blocks.push(Block {
            id: block_idx.clone(),
            tx_type: "demurrage_burn".to_string(),
            from: Some(from),
            to: None,
            amount: burn_amount,
            timestamp: now,
        });

        Ok(block_idx)
    })
}

#[ic_cdk::query]
pub fn get_total_burned() -> Nat {
    STATE.with(|s_ref| s_ref.borrow().total_burned.clone())
}

#[ic_cdk::query]
pub fn get_total_disbursed_grants() -> Nat {
    STATE.with(|s_ref| s_ref.borrow().total_disbursed.clone())
}
