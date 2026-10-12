"""Reality Gate Comprehensive Verification Engine for QICP Equality.

Enforces zero-simulation, zero-mock truthfulness:
1. Validates all NIST PQC, Conway Automaton, Tokenomics, and x402 Bazaar suites.
2. Performs live boundary node reachability queries to https://ic0.app and https://icp-api.io.
3. Audits Candid interface definitions and dfx.json canister configuration.
4. Production release gate (--release): Audits canister cycle wallet and mainnet keys,
   failing closed (exit code 2) if mainnet deployment prerequisites are unconfigured.
"""
import argparse
import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from backend.icp_client import ICPBoundaryClient


def run_unit_suite(test_module: str, suite_name: str) -> bool:
    print(f"\n--- [RUNNING] {suite_name} ({test_module}) ---")
    res = subprocess.run([sys.executable, "-m", "unittest", test_module, "-v"], cwd=root)
    if res.returncode == 0:
        print(f"[PASS] {suite_name} passed.")
        return True
    else:
        print(f"[FAIL] {suite_name} failed with exit code {res.returncode}.", file=sys.stderr)
        return False


async def verify_live_boundary_nodes() -> bool:
    print("\n--- [VERIFYING] Live Internet Computer Boundary Nodes ---")
    client = ICPBoundaryClient()
    health = await client.check_boundary_node_health()
    all_ok = True
    for url, info in health.items():
        if info.get("reachable"):
            print(f"[PASS] Boundary Node reachable: {url} (HTTP {info.get('status_code')})")
        else:
            print(f"[WARN] Boundary Node {url} error: {info.get('error')}", file=sys.stderr)
            all_ok = False
    return any(v.get("reachable") for v in health.values())


def verify_canister_interfaces() -> bool:
    print("\n--- [VERIFYING] Canister Candid Interfaces & dfx.json ---")
    dfx_file = root / "dfx.json"
    if not dfx_file.exists():
        print("[FAIL] dfx.json missing!", file=sys.stderr)
        return False

    with open(dfx_file, "r") as f:
        dfx_data = json.load(f)

    canisters = dfx_data.get("canisters", {})
    required = ["qicp_token", "treasury", "x402_bazaar", "conway_engine"]

    all_found = True
    for c_name in required:
        if c_name not in canisters:
            print(f"[FAIL] Canister '{c_name}' not defined in dfx.json", file=sys.stderr)
            all_found = False
            continue
        candid_path = root / canisters[c_name].get("candid", "")
        if not candid_path.exists():
            print(f"[FAIL] Candid interface missing for '{c_name}': {candid_path}", file=sys.stderr)
            all_found = False
        else:
            print(f"[PASS] Canister '{c_name}' Candid interface verified: {candid_path.name}")

    return all_found


def check_release_readiness() -> bool:
    print("\n--- [VERIFYING] Mainnet Production Release & Canister Cycles Gate ---")
    status_file = root / "STATUS.json"
    status_data = json.loads(status_file.read_text()) if status_file.exists() else {}

    blockers = []

    # 1. Check dfx mainnet identity
    dfx_identity = os.getenv("DFX_IDENTITY") or status_data.get("dfx_identity")
    if not dfx_identity:
        blockers.append("Production DFINITY Mainnet identity is unconfigured on local host.")
        print("  [BLOCKED] Mainnet Identity: No DFX_IDENTITY configured.", file=sys.stderr)
    else:
        print(f"  [PASS] Mainnet Identity configured: {dfx_identity}")

    # 2. Check mainnet cycles wallet
    cycles_wallet = os.getenv("CYCLES_WALLET_CANISTER_ID") or status_data.get("cycles_wallet_canister_id")
    if not cycles_wallet:
        blockers.append("Production Canister Cycles Wallet is unconfigured (required to fund canister creation).")
        print("  [BLOCKED] Cycles Wallet: No CYCLES_WALLET_CANISTER_ID configured.", file=sys.stderr)
    else:
        print(f"  [PASS] Cycles Wallet configured: {cycles_wallet}")

    # 3. Third-party professional canister audit
    if not status_data.get("third_party_audit_completed", False):
        blockers.append("Independent third-party professional security audit of Rust/Candid canisters pending.")
        print("  [BLOCKED] Security Audit: Third-party review not yet completed.", file=sys.stderr)

    if blockers:
        print("\n[RELEASE GATE AUDIT SUMMARY] The following critical security blockers remain unresolved:", file=sys.stderr)
        for b in blockers:
            print(f"  - {b}", file=sys.stderr)
        print("\nProduction release remains strictly BLOCKED until mainnet cycle wallet, production identity, and independent audit are completed.", file=sys.stderr)
        return False
    else:
        print("\n[ALL PRODUCTION RELEASE REQUIREMENTS CONFIRMED]")
        return True


def main():
    parser = argparse.ArgumentParser(description="Reality Gate Comprehensive Verification Engine for QICP")
    parser.add_argument("--pqc", action="store_true", help="Run NIST PQC cryptographic tests")
    parser.add_argument("--conway", action="store_true", help="Run Conway governance automaton tests")
    parser.add_argument("--tokenomics", action="store_true", help="Run strategic tokenomics tests")
    parser.add_argument("--x402", action="store_true", help="Run x402 bazaar protocol tests")
    parser.add_argument("--api", action="store_true", help="Run backend API & gateway tests")
    parser.add_argument("--canisters", action="store_true", help="Verify Candid IDL & dfx.json")
    parser.add_argument("--boundary", action="store_true", help="Verify live ICP boundary nodes")
    parser.add_argument("--release", action="store_true", help="Run production release gate")
    args = parser.parse_args()

    run_all = args.release or (
        not args.pqc and not args.conway and not args.tokenomics and not args.x402 and not args.api and not args.canisters and not args.boundary
    )

    failures = 0

    if args.pqc or run_all:
        if not run_unit_suite("tests.test_pqc", "NIST Post-Quantum Cryptography Suite"):
            failures += 1

    if args.conway or run_all:
        if not run_unit_suite("tests.test_conway", "Conway Governance Automaton Engine"):
            failures += 1

    if args.tokenomics or run_all:
        if not run_unit_suite("tests.test_tokenomics", "Strategic Elastic Tokenomics Suite"):
            failures += 1

    if args.x402 or run_all:
        if not run_unit_suite("tests.test_x402", "x402 Bazaar Protocol Suite"):
            failures += 1

    if args.api or run_all:
        if not run_unit_suite("tests.test_api", "FastAPI & Pure ASGI Gateway Suite"):
            failures += 1

    if args.canisters or run_all:
        if not verify_canister_interfaces():
            failures += 1

    if args.boundary or run_all:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        if not loop.run_until_complete(verify_live_boundary_nodes()):
            failures += 1

    if failures > 0:
        print(f"\n[SUMMARY] Verification finished with {failures} failure(s).", file=sys.stderr)
        sys.exit(1)

    print("\n" + "=" * 65)
    print("[PASS] ALL TECHNICAL TEST SUITES & LEDGER CHECKS SUCCESSFUL")
    print("=" * 65)

    if args.release:
        print("\n" + "*" * 65)
        print("CHECKING MAINNET PRODUCTION RELEASE READINESS")
        print("*" * 65)
        is_ready = check_release_readiness()
        if not is_ready:
            print("\n[CRITICAL RELEASE GATE HALT]")
            print("Release certification FAILS CLOSED (exit code 2).")
            print("Reason: Mainnet credentials, cycle wallet, or independent audit required.")
            sys.exit(2)
        else:
            print("[CERTIFIED] Release readiness confirmed.")
            sys.exit(0)


if __name__ == "__main__":
    main()
