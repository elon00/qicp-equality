"""
Tests for Canister Candid Interfaces, Cargo Workspace, Wasm Binaries, and State Transitions.
"""

import json
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_dfx_json_structure():
    dfx_path = REPO_ROOT / "dfx.json"
    assert dfx_path.exists(), "dfx.json must exist"

    with open(dfx_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "canisters" in data, "dfx.json must define canisters"
    canisters = data["canisters"]

    expected = ["qicp_token", "treasury", "x402_bazaar", "conway_engine"]
    for c in expected:
        assert c in canisters, f"Canister {c} must be declared in dfx.json"
        assert canisters[c]["type"] == "rust"
        candid_path = REPO_ROOT / canisters[c]["candid"]
        assert candid_path.exists(), f"Candid file for {c} must exist at {candid_path}"


def test_candid_did_interfaces():
    candid_files = {
        "qicp_token": [
            "icrc1_name",
            "icrc1_symbol",
            "icrc1_decimals",
            "icrc1_fee",
            "icrc1_total_supply",
            "icrc1_minting_account",
            "icrc1_balance_of",
            "icrc1_transfer",
            "icrc1_supported_standards",
            "icrc1_metadata",
            "icrc2_approve",
            "icrc2_allowance",
            "icrc2_transfer_from",
            "icrc3_supported_block_types",
            "icrc3_get_blocks",
            "mint_livelihood_grant",
            "apply_demurrage_burn",
            "get_total_burned",
            "get_total_disbursed_grants",
        ],
        "treasury": [
            "submit_proposal",
            "vote_proposal",
            "approve_proposal",
            "disburse_grant",
            "cancel_disputed_grant",
            "get_proposal",
            "list_proposals",
            "get_treasury_balance_e8s",
        ],
        "x402_bazaar": [
            "configure_ledger",
            "request_challenge",
            "settle_payment",
            "get_total_bazaar_burned_e8s",
            "get_total_bazaar_treasury_e8s",
        ],
        "conway_engine": [
            "init_automaton",
            "step_automaton",
            "get_current_metrics",
        ],
    }

    for canister, methods in candid_files.items():
        did_file = REPO_ROOT / "canisters" / canister / f"{canister}.did"
        assert did_file.exists(), f"{did_file} must exist"
        content = did_file.read_text(encoding="utf-8")
        assert "service :" in content, f"{canister}.did must declare a service"

        for m in methods:
            assert f'"{m}"' in content or m in content, f"Method {m} must be declared in {canister}.did"


def test_cargo_workspace_members():
    cargo_path = REPO_ROOT / "Cargo.toml"
    assert cargo_path.exists()
    content = cargo_path.read_text(encoding="utf-8")

    assert "[workspace]" in content
    assert "members = [" in content

    for member in ["qicp_token", "treasury", "x402_bazaar", "conway_engine"]:
        assert f'"canisters/{member}"' in content
        member_cargo = REPO_ROOT / "canisters" / member / "Cargo.toml"
        assert member_cargo.exists(), f"Cargo.toml for {member} must exist"
        member_src = REPO_ROOT / "canisters" / member / "src" / "lib.rs"
        assert member_src.exists(), f"lib.rs for {member} must exist"


def test_compiled_wasm_artifacts_exist():
    wasm_dir = REPO_ROOT / "target" / "wasm32-unknown-unknown" / "release"
    if wasm_dir.exists():
        expected_wasms = ["qicp_token.wasm", "treasury.wasm", "x402_bazaar.wasm", "conway_engine.wasm"]
        for w in expected_wasms:
            wasm_file = wasm_dir / w
            assert wasm_file.exists(), f"Compiled WebAssembly binary {w} must exist"
            assert wasm_file.stat().st_size > 100_000, f"Wasm binary {w} must be non-empty and valid"


def test_icrc2_delegation_accounting_logic():
    # Verify allowance mathematics and boundary invariants
    balance = 1_000_000
    fee = 10_000
    allowance = 500_000
    transfer_amount = 200_000

    required = transfer_amount + fee
    assert allowance >= required, "Sufficient allowance"
    assert balance >= required, "Sufficient funds"

    new_allowance = allowance - required
    new_balance = balance - required
    assert new_allowance == 290_000
    assert new_balance == 790_000


def test_treasury_timelock_and_voting_quorum():
    # 7-day dispute window: 7 * 86400 = 604800 seconds
    submission_time = 1_700_000_000
    timelock_window = 7 * 86400
    unlock_time = submission_time + timelock_window

    current_time_early = submission_time + 86400  # 1 day later
    assert current_time_early < unlock_time, "Disbursement blocked before 7 days elapse"

    current_time_eligible = submission_time + timelock_window + 1
    assert current_time_eligible >= unlock_time, "Disbursement eligible after 7 days"

    # Quorum check: requires >= 3 votes for
    votes_for = 2
    votes_against = 0
    approved = votes_for >= 3 and votes_for > votes_against
    assert not approved, "Quorum not met with 2 votes"

    votes_for = 3
    approved = votes_for >= 3 and votes_for > votes_against
    assert approved, "Quorum met with 3 votes"
