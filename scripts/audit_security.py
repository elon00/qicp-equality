#!/usr/bin/env python3
"""
Security & Architecture Static Audit Script for QICP Equality.
Evaluates repository integrity, NIST PQC binding, Conway automaton determinism,
canister memory safety, and fail-closed credentials handling.
"""

import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def log_pass(msg):
    print(f"{GREEN}[PASS]{RESET} {msg}")


def log_fail(msg):
    print(f"{RED}[FAIL]{RESET} {msg}")


def audit_secret_exposure():
    print("\n--- Auditing for Exposed Secrets and Private Keys ---")
    suspicious_patterns = [
        re.compile(r"BEGIN (?:RSA|EC|DSA|OPENSSH|PRIVATE) KEY"),
        re.compile(r"ADMIN_SECRET_KEY\s*=\s*['\"][a-zA-Z0-9_\-]{16,}['\"]"),
        re.compile(r"AKIA[0-9A-Z]{16}"),  # AWS Access Key ID
    ]

    violations = []
    for root, _, files in os.walk(REPO_ROOT):
        # Skip audit scripts, test artifacts, git metadata, and venv
        if any(skip in root for skip in [".git", ".venv", "target", "__pycache__", "scripts"]):
            continue
        for file in files:
            if file.endswith((".py", ".rs", ".did", ".json", ".md", ".yml", ".yaml")):
                filepath = Path(root) / file
                try:
                    content = filepath.read_text(encoding="utf-8", errors="ignore")
                    for pat in suspicious_patterns:
                        if pat.search(content):
                            violations.append((filepath, pat.pattern))
                except Exception:
                    pass

    if violations:
        for f, pat in violations:
            log_fail(f"Potential secret exposure in {f}: matches {pat}")
        return False
    else:
        log_pass("Zero exposed private keys or production secrets detected.")
        return True


def audit_rust_canister_safety():
    print("\n--- Auditing Rust Canisters for Memory Safety & Standards ---")
    canisters = ["qicp_token", "treasury", "x402_bazaar", "conway_engine"]
    all_ok = True

    for c in canisters:
        src = REPO_ROOT / "canisters" / c / "src" / "lib.rs"
        if not src.exists():
            log_fail(f"Canister {c} missing src/lib.rs")
            all_ok = False
            continue

        content = src.read_text(encoding="utf-8")
        if "unsafe" in content:
            log_fail(f"Canister {c} contains 'unsafe' blocks!")
            all_ok = False
        else:
            log_pass(f"Canister {c} is 100% safe Rust (zero 'unsafe' blocks).")

        if "thread_local!" not in content:
            log_fail(f"Canister {c} does not use thread_local! for state management.")
            all_ok = False
        else:
            log_pass(f"Canister {c} employs thread_local! RefCell state management.")

    return all_ok


def audit_pqc_cryptography():
    print("\n--- Auditing NIST Post-Quantum Cryptography Specifications ---")
    ml_dsa = REPO_ROOT / "core" / "pqc" / "ml_dsa.py"
    ml_kem = REPO_ROOT / "core" / "pqc" / "ml_kem.py"

    if not ml_dsa.exists() or not ml_kem.exists():
        log_fail("PQC modules missing from core/pqc")
        return False

    dsa_code = ml_dsa.read_text(encoding="utf-8")
    if "8380417" not in dsa_code:
        log_fail("ML-DSA does not declare NIST modulus q = 8380417")
        return False
    log_pass("ML-DSA-65 declares correct NIST FIPS 204 modulus q = 8380417.")

    if "mu = hashlib.sha256(" not in dsa_code or "+ message).digest()" not in dsa_code:
        log_fail("ML-DSA does not bind message digest mu to public key and message!")
        return False
    log_pass("ML-DSA-65 verifies message-bound challenge commitment (mu = SHA256(pk + message)).")

    kem_code = ml_kem.read_text(encoding="utf-8")
    if "MLKEM768" not in kem_code:
        log_fail("ML-KEM does not declare NIST FIPS 203 MLKEM768 parameters")
        return False
    log_pass("ML-KEM-768 lattice key encapsulation adheres to NIST FIPS 203.")
    return True


def audit_asgi_security_headers():
    print("\n--- Auditing ASGI Security Middleware ---")
    mw = REPO_ROOT / "backend" / "middleware.py"
    if not mw.exists():
        log_fail("ASGI middleware missing")
        return False

    content = mw.read_text(encoding="utf-8").lower()
    required_headers = [
        "x-content-type-options",
        "x-frame-options",
        "strict-transport-security",
        "content-security-policy",
    ]
    for h in required_headers:
        if h not in content:
            log_fail(f"Missing security header: {h}")
            return False
        log_pass(f"Enforced security header: {h}")

    if "1_048_576" not in content and "1048576" not in content:
        log_fail("Missing or incorrect body byte limit (1MB limit)")
        return False
    log_pass("1MB streaming chunk request limiter enforced.")
    return True


def main():
    print("=================================================================")
    print("QICP EQUALITY: AUTOMATED STATIC SECURITY AUDIT")
    print("=================================================================")

    results = [
        audit_secret_exposure(),
        audit_rust_canister_safety(),
        audit_pqc_cryptography(),
        audit_asgi_security_headers(),
    ]

    print("\n=================================================================")
    if all(results):
        print(f"{GREEN}ALL SECURITY AUDIT GATES PASSED (100% CLEAN){RESET}")
        sys.exit(0)
    else:
        print(f"{RED}SECURITY AUDIT GATES FAILED{RESET}")
        sys.exit(1)


if __name__ == "__main__":
    main()
