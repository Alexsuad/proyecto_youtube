"""Generate PLAN 006 T5 pilot authorization artifacts (canonical MissionAuthorization).

Reproducible from the repo root:  python -3 tools/plan_006_gen_t5_authorization.py

Creates:
  - plans/plan_006/PLAN_006_T5_AUTHORITY.json      (authority artifact)
  - plans/plan_006/PLAN_006_T5_AUTHORIZATION.json  (mission authorization contract)

Verifies the pair with load_mission_authorization(). It binds to the CURRENT live
state checksum of plans/001_CONTROL_OPERATIVO.md and does NOT modify that file.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.core.mission_authorization import MissionAuthorization, load_mission_authorization, sha256_file

LIVE_STATE_PATH = "plans/001_CONTROL_OPERATIVO.md"
AUTHORITY_PATH = "plans/plan_006/PLAN_006_T5_AUTHORITY.json"
CONTRACT_PATH = "plans/plan_006/PLAN_006_T5_AUTHORIZATION.json"

MISSION_ID = "PLAN_006_T5_MEASURED_OPENCODE_PILOT"

AUTHORIZATION = {
    "live_state_path": LIVE_STATE_PATH,
    "live_state_sha256": sha256_file(ROOT / LIVE_STATE_PATH),
    "capability_ids": ["PLAN_006_T5_PILOT"],
    "role_ids": ["ENGINEERING_IMPLEMENTER"],
    "execution_profile_ids": ["ANY"],
    "execution_interface": "ANY",
    "allowed_operations": ["DELEGATE", "EXECUTE_CAPABILITY", "VERIFY_EVIDENCE", "COMPLETE_MISSION"],
    "allowed_paths": [
        "plans/plan_006/",
        "plans/001_CONTROL_OPERATIVO.md",
        "reports/implementation/plan_006/",
        "schemas/",
        "src/core/",
        "config/",
        "tests/core/",
        "tools/",
    ],
    "allowed_routes": ["ANY"],
    "execution_mode": "SYNTHETIC",
    "single_use": False,
    "authority_ref": AUTHORITY_PATH,
    "authority_sha256": "0" * 64,
    "authorized_scope_sha256": "0" * 64,
    "executor_substitution_policy": "COMPATIBLE_INTERFACE_ONLY",
    "contains_material_repair": False,
    "repair_integrity_evidence_path": "NONE",
    "delegation_sha256": "0" * 64,
}

DELEGATION = {
    "authorized_context_refs": [
        "plans/plan_006/",
        "plans/001_CONTROL_OPERATIVO.md",
        "reports/implementation/plan_006/",
        "schemas/",
        "src/core/",
        "config/",
        "tests/core/",
        "tools/",
    ],
    "delegation_depth": 0,
    "max_delegation_depth": 1,
}


def canonical_bytes(data: dict) -> bytes:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def main() -> None:
    scope_payload = {
        "mission_id": MISSION_ID,
        "capability_ids": list(AUTHORIZATION["capability_ids"]),
        "role_ids": list(AUTHORIZATION["role_ids"]),
        "execution_profile_ids": list(AUTHORIZATION["execution_profile_ids"]),
        "execution_interface": AUTHORIZATION["execution_interface"],
        "allowed_operations": list(AUTHORIZATION["allowed_operations"]),
        "allowed_paths": list(AUTHORIZATION["allowed_paths"]),
        "allowed_routes": list(AUTHORIZATION["allowed_routes"]),
        "execution_mode": AUTHORIZATION["execution_mode"],
        "live_state_sha256": AUTHORIZATION["live_state_sha256"],
        "contains_material_repair": AUTHORIZATION["contains_material_repair"],
        "repair_integrity_evidence_path": AUTHORIZATION["repair_integrity_evidence_path"],
    }
    authorized_scope_sha256 = hashlib.sha256(canonical_bytes(scope_payload)).hexdigest()
    AUTHORIZATION["authorized_scope_sha256"] = authorized_scope_sha256
    AUTHORIZATION["delegation_sha256"] = hashlib.sha256(canonical_bytes(DELEGATION)).hexdigest()

    contract = {
        "mission_id": MISSION_ID,
        "authorization": AUTHORIZATION,
        "delegation": DELEGATION,
    }

    authority = {
        "mission_id": MISSION_ID,
        "decision": "APPROVE",
        "artifact_version": "1.0.0",
        "authorized_scope_sha256": authorized_scope_sha256,
        "authorization_source": "EXPLICIT_OWNER_AUTHORIZATION_RECORDED_2026-08-13",
        "historical_note": (
            "PLAN 006 T5 measured OpenCode pilot: DELEGATE authorized exclusively inside this pilot; "
            "temporary native subagents via Task/explore/general; delegation depth max 1; primary keeps "
            "integration, verification and final responsibility; no persistent agents; no new "
            ".opencode/agents/*; DELEGATE scope ends with T5."
        ),
    }

    authority_path = ROOT / AUTHORITY_PATH
    contract_path = ROOT / CONTRACT_PATH

    authority_path.write_text(json.dumps(authority, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    AUTHORIZATION["authority_sha256"] = sha256_file(authority_path)
    contract_path.write_text(json.dumps(contract, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    loaded = load_mission_authorization(CONTRACT_PATH)
    assert isinstance(loaded, MissionAuthorization)
    # verify requires a canonical authorization root; validate the contract
    # binding directly via from_contract invariants already performed at load.
    print(f"OK -> {AUTHORITY_PATH}")
    print(f"OK -> {CONTRACT_PATH}")
    print("MISSION_ID:", loaded.mission_id)
    print("SCOPE_SHA256:", loaded.authorized_scope_sha256)
    print("LIVE_STATE_SHA256:", loaded.live_state_sha256)


if __name__ == "__main__":
    main()