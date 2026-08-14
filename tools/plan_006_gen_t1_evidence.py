"""Generate PLAN 006 T1 evidence report — controlled demonstration of the T1 mechanism.

Reproducible from the repo root:  python -3 tools/plan_006_gen_t1_evidence.py

Demonstrates, using the existing T1 + MissionAuthorization surfaces only, the
separation between:

    A. historical validity of a completed execution
    B. active authorization for a new execution
    C. current applicability of evidence

The frozen completion snapshot uses DISTINCT real bindings derived from a
controlled demonstration authorization (PLAN_006_T1_DEMO_AUTHORIZATION.json)
and its authority artifact (PLAN_006_T1_DEMO_AUTHORITY.json). This is a new,
verifiable controlled case; it does NOT pretend the old historical bindings
existed. It never weakens MissionAuthorization.verify(), freshness, fail-closed
or owner-closure verification.
"""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.core.contract_validation import validate_against_schema
from src.core.historical_completion import (
    build_completion_record,
    evaluate_current_applicability,
    freeze_completion_snapshot,
    owner_closure,
    verify_historical_completion,
)
from src.core.lean_measurement import _evidence_identity, _repository_revision, _sha256_file
from src.core.mission_authorization import (
    MissionAuthorizationError,
    load_mission_authorization,
    scope_checksum,
)

LIVE_STATE_PATH = "plans/001_CONTROL_OPERATIVO.md"
PLAN_DOC_PATH = "plans/plan_006/006_LEAN_HARNESS_ASSURANCE_ORQUESTACION_EFICIENCIA.md"
DEMO_AUTHORITY_PATH = "plans/plan_006/PLAN_006_T1_DEMO_AUTHORITY.json"
DEMO_CONTRACT_PATH = "plans/plan_006/PLAN_006_T1_DEMO_AUTHORIZATION.json"
T1_REPORT_PATH = "reports/implementation/plan_006/T1_HISTORICAL_COMPLETION.json"
TEST_PATH = "tests/core/test_plan_006_t1_historical_completion.py"

MISSION_ID = "PLAN_006_T1_DEMO_CONTROLLED"

SCOPE = {
    "mission_id": MISSION_ID,
    "capability_ids": ["PLAN_006_T1_DEMO"],
    "role_ids": ["ENGINEERING_IMPLEMENTER"],
    "execution_profile_ids": ["ANY"],
    "execution_interface": "ANY",
    "allowed_operations": ["VERIFY_EVIDENCE", "EXECUTE_CAPABILITY"],
    "allowed_paths": ["reports/implementation/plan_006/"],
    "allowed_routes": ["ANY"],
    "execution_mode": "SYNTHETIC",
    "contains_material_repair": False,
    "repair_integrity_evidence_path": "NONE",
}

AUTHORITY = {
    "mission_id": MISSION_ID,
    "decision": "APPROVE",
    "artifact_version": "1.0.0",
    "authorization_source": "EXPLICIT_OWNER_DEMO_CONTROLLED_CASE_2026-08-14",
    "historical_note": (
        "Controlled T1 demonstration only: authorization bound to live state A "
        "(reconciled control operativo). It is used to show A->B separation, "
        "not to authorize any real product execution."
    ),
}


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _demonstrate_a_to_b(root: Path, live_sha_a: str) -> dict[str, str]:
    """Simulate live state A -> B and verify the three T1 properties.

    Uses the controlled demonstration authorization artifacts in a temporary
    repository root. This mirrors tests/core/test_plan_006_t1_historical_completion.py
    without weakening any fail-closed check.
    """
    results: dict[str, str] = {}
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp) / "repo"
        (tmp_root / "plans/001").mkdir(parents=True)
        (tmp_root / "plans/plan_006").mkdir(parents=True)

        state_a = (root / LIVE_STATE_PATH).read_bytes()
        (tmp_root / LIVE_STATE_PATH).write_bytes(state_a)

        contract_src = root / DEMO_CONTRACT_PATH
        authority_src = root / DEMO_AUTHORITY_PATH
        (tmp_root / DEMO_CONTRACT_PATH).write_bytes(contract_src.read_bytes())
        (tmp_root / DEMO_AUTHORITY_PATH).write_bytes(authority_src.read_bytes())

        authorization = load_mission_authorization(tmp_root / DEMO_CONTRACT_PATH)

        # (B1) Active authorization A used against live state A -> OK.
        try:
            authorization.verify(
                tmp_root,
                capability_id="PLAN_006_T1_DEMO",
                role_id="ENGINEERING_IMPLEMENTER",
                operation="VERIFY_EVIDENCE",
                path="reports/implementation/plan_006/",
                execution_mode="SYNTHETIC",
            )
            results["active_authorization_against_A"] = "OK"
        except MissionAuthorizationError as exc:
            results["active_authorization_against_A"] = f"FAIL:{exc}"

        # Live state changes to B by an administrative action.
        (tmp_root / LIVE_STATE_PATH).write_bytes(
            b"# LIVE STATE B (administrative change after completion)\n"
            b"CONTENIDO DISTINTO AL ESTADO A\n"
        )
        live_sha_b = hashlib.sha256((tmp_root / LIVE_STATE_PATH).read_bytes()).hexdigest()

        # (B2) Active authorization A used against live state B -> must fail.
        try:
            authorization.verify(
                tmp_root,
                capability_id="PLAN_006_T1_DEMO",
                role_id="ENGINEERING_IMPLEMENTER",
                operation="VERIFY_EVIDENCE",
                path="reports/implementation/plan_006/",
                execution_mode="SYNTHETIC",
            )
            results["active_authorization_against_B"] = "FAIL: authorization did NOT block"
        except MissionAuthorizationError as exc:
            results["active_authorization_against_B"] = f"BLOCKED:{exc}"

        results["live_state_sha256_A"] = live_sha_a
        results["live_state_sha256_B"] = live_sha_b
    return results


def main() -> None:
    live_sha_a = _sha256_file(ROOT / LIVE_STATE_PATH)
    plan_doc_sha = _sha256_file(ROOT / PLAN_DOC_PATH)
    test_sha = _sha256_file(ROOT / TEST_PATH)

    scope = dict(SCOPE)
    scope["live_state_sha256"] = live_sha_a
    authorized_scope_sha256 = scope_checksum(scope)

    authority = dict(AUTHORITY)
    authority["authorized_scope_sha256"] = authorized_scope_sha256
    authority_path = ROOT / DEMO_AUTHORITY_PATH
    _write_json(authority_path, authority)

    authorization = {
        "mission_id": MISSION_ID,
        "authorization": {
            "live_state_path": LIVE_STATE_PATH,
            "live_state_sha256": live_sha_a,
            "capability_ids": scope["capability_ids"],
            "role_ids": scope["role_ids"],
            "execution_profile_ids": scope["execution_profile_ids"],
            "execution_interface": scope["execution_interface"],
            "allowed_operations": scope["allowed_operations"],
            "allowed_paths": scope["allowed_paths"],
            "allowed_routes": scope["allowed_routes"],
            "execution_mode": scope["execution_mode"],
            "single_use": False,
            "authority_ref": DEMO_AUTHORITY_PATH,
            "authority_sha256": _sha256_file(authority_path),
            "authorized_scope_sha256": authorized_scope_sha256,
            "executor_substitution_policy": "COMPATIBLE_INTERFACE_ONLY",
            "contains_material_repair": False,
            "repair_integrity_evidence_path": "NONE",
        },
    }
    contract_path = ROOT / DEMO_CONTRACT_PATH
    _write_json(contract_path, authorization)
    authorization_artifact_sha = _sha256_file(contract_path)

    # Demonstrate A -> B with the controlled artifacts before freezing the record.
    demo = _demonstrate_a_to_b(ROOT, live_sha_a)
    if demo["active_authorization_against_A"] != "OK":
        raise SystemExit(f"DEMO_BROKEN: authorization against A failed: {demo['active_authorization_against_A']}")
    if not demo["active_authorization_against_B"].startswith("BLOCKED"):
        raise SystemExit(f"DEMO_BROKEN: authorization against B was not blocked: {demo['active_authorization_against_B']}")

    import subprocess

    git_head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
    ).strip()

    snapshot = freeze_completion_snapshot(
        mission_id=MISSION_ID,
        mission_contract_sha256=plan_doc_sha,
        authorization_artifact_sha256=authorization_artifact_sha,
        authorized_scope_sha256=authorized_scope_sha256,
        live_state_path=LIVE_STATE_PATH,
        live_state_sha256_at_execution=live_sha_a,
        authority_ref=DEMO_AUTHORITY_PATH,
        authority_sha256=_sha256_file(authority_path),
        repository_revision=_repository_revision(ROOT),
        required_test_identities=(TEST_PATH,),
        evidence_identities=("PLAN_006_T1_DEMO_CONTROLLED_EVIDENCE",),
        git_binding={"git_head": git_head},
        completion_result="PASS",
    )
    record = build_completion_record(snapshot)
    record["source_inputs"] = [
        {"path": LIVE_STATE_PATH, "sha256": live_sha_a},
        {"path": PLAN_DOC_PATH, "sha256": plan_doc_sha},
        {"path": DEMO_CONTRACT_PATH, "sha256": authorization_artifact_sha},
        {"path": DEMO_AUTHORITY_PATH, "sha256": _sha256_file(authority_path)},
        {"path": TEST_PATH, "sha256": test_sha},
    ]
    record["evidence_refs"] = [
        LIVE_STATE_PATH,
        PLAN_DOC_PATH,
        DEMO_CONTRACT_PATH,
        DEMO_AUTHORITY_PATH,
        TEST_PATH,
    ]
    record["limitations"] = [
        "Controlled T1 demonstration: live state A is the reconciled control operativo; bindings are DISTINCT real artifacts, not the old indistinct historical bindings.",
        f"Demo A->B: {demo['active_authorization_against_A']} against A; {demo['active_authorization_against_B']} against B.",
        f"Live state hashes: A={demo['live_state_sha256_A']}; B={demo['live_state_sha256_B']}.",
        "Historical completion stays valid regardless of A->B; current applicability is evaluated separately (T2/T3 semantics).",
        "owner_identity_sha256 binds owner closure to the controlled demonstration authority artifact.",
    ]

    closure = owner_closure(
        completion_record=record,
        owner_decision="ACCEPTED",
        closure_metadata={
            "owner": "OWNER",
            "owner_identity_sha256": _sha256_file(authority_path),
            "note": "Controlled T1 demonstration closure; no functional approval claimed.",
        },
    )
    record["owner_closure"] = closure
    record["evidence_identity_sha256"] = _evidence_identity(record)

    violations = verify_historical_completion(record)
    if violations:
        raise SystemExit(f"T1_VERIFY_FAILED: {'; '.join(violations)}")

    target = ROOT / T1_REPORT_PATH
    _write_json(target, record)
    errors = validate_against_schema(record, "plan_006_evidence_envelope")
    if errors:
        raise SystemExit(f"SCHEMA_ERROR: {errors}")
    print(f"OK -> {T1_REPORT_PATH}")
    print("COMPLETION_IDENTITY:", record["completion_identity_sha256"])
    print("AUTHORIZATION_AGAINST_A:", demo["active_authorization_against_A"])
    print("AUTHORIZATION_AGAINST_B:", demo["active_authorization_against_B"])


if __name__ == "__main__":
    main()