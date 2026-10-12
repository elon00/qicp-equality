"""
Tests for Canister Candid Interfaces, Cargo Workspace, and Deterministic Logic.
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
            "icrc1_balance_of",
            "icrc1_transfer",
            "mint_livelihood_grant",
            "apply_demurrage_burn",
        ],
        "treasury": [
            "submit_proposal",
            "disburse_grant",
            "cancel_disputed_grant",
            "get_proposal",
            "list_proposals",
            "get_treasury_balance_e8s",
        ],
        "x402_bazaar": [
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
