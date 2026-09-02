"""Behavioral tests for the provider-neutral mission completion gate."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from src.core.gate_result import GateResult
from src.core.mission_completion_gate import MissionContract, MissionContractError, run_mission_completion_gate
from src.core.status import GateStatus
from src.core.repair_integrity import evidence_checksum
from src.core.mission_authorization import scope_checksum
from tests.core.test_repair_integrity import valid_evidence


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)


def _repo(tmp_path: Path, *, state: str = "NO", protected_path: str = "protected.txt") -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "--quiet")
    _git(root, "config", "user.email", "gate@example.test")
    _git(root, "config", "user.name", "Gate Test")
    (root / "control.md").write_text(
        f"CURRENT_MISSION: TECHNICAL_HARDENING\nR1_M4_OPENED: {state}\n",
        encoding="utf-8",
    )
    (root / "README.md").write_text("base\n", encoding="utf-8")
    _git(root, "add", ".")
    _git(root, "commit", "-m", "base", "--quiet")

    protected = root / protected_path
    protected.parent.mkdir(parents=True, exist_ok=True)
    protected.write_text("preserve me\n", encoding="utf-8")
    return root


def _contract(root: Path, *, authorized: list[str] | None = None, tests: list[dict[str, object]] | None = None, forbidden: dict[str, object] | None = None, material_auth: bool = False, protected_path: str = "protected.txt") -> MissionContract:
    state_sha256 = hashlib.sha256((root / "control.md").read_bytes()).hexdigest()
    authorization_scope = {
        "mission_id": "TECHNICAL_HARDENING", "capability_ids": ["CAP"], "role_ids": ["ROLE"],
        "execution_profile_ids": ["PROFILE"], "execution_interface": "ANY",
        "allowed_operations": ["EXECUTE_CAPABILITY"], "allowed_paths": ["output"],
        "allowed_routes": ["ANY"], "execution_mode": "ANY", "live_state_sha256": state_sha256,
        "contains_material_repair": True, "repair_integrity_evidence_path": "repair.json",
    }
    authority_decision = root / "authorization-decision.json"
    authority_decision.write_text(json.dumps({
        "mission_id": "TECHNICAL_HARDENING", "decision": "APPROVE", "artifact_version": "1.0.0",
        "authorized_scope_sha256": scope_checksum(authorization_scope),
    }) + "\n", encoding="utf-8")
    authorization_path = root / "mission-authorization.json"
    authorization_path.write_text(json.dumps({"mission_id": "TECHNICAL_HARDENING", "authorization": {
        "live_state_path": "control.md", "live_state_sha256": state_sha256,
        "capability_ids": ["CAP"], "role_ids": ["ROLE"], "execution_profile_ids": ["PROFILE"],
        "execution_interface": "ANY", "allowed_operations": ["EXECUTE_CAPABILITY"], "allowed_paths": ["output"],
        "allowed_routes": ["ANY"], "execution_mode": "ANY", "single_use": False,
        "authority_ref": "authorization-decision.json", "authority_sha256": hashlib.sha256(authority_decision.read_bytes()).hexdigest(),
        "authorized_scope_sha256": scope_checksum(authorization_scope), "executor_substitution_policy": "COMPATIBLE_INTERFACE_ONLY",
        "contains_material_repair": True, "repair_integrity_evidence_path": "repair.json",
    }}) + "\n", encoding="utf-8")
    authorized_paths = list(authorized or ["src/", "control.md"])
    for path in ("mission-authorization.json", "authorization-decision.json", "repair.json"):
        if path not in authorized_paths:
            authorized_paths.append(path)
    data = {
        "mission_id": "TECHNICAL_HARDENING",
        "artifact_id": "mission-completion-gate",
        "artifact_version": "1.0.0",
        "authorized_paths": authorized_paths,
        "protected_untracked_paths": [protected_path],
        "protected_untracked_baseline": [{"path": protected_path, "sha256": hashlib.sha256((root / protected_path).read_bytes()).hexdigest()}],
        "required_tests": tests or [{"label": "required smoke", "command": [sys.executable, "-c", "raise SystemExit(0)"]}],
        "push_allowed": False,
        "contains_material_repair": material_auth,
        **({"repair_integrity_evidence_path": "repair.json", "mission_authorization_path": "mission-authorization.json"} if material_auth else {}),
        **({"mission_authorization_sha256": hashlib.sha256(authorization_path.read_bytes()).hexdigest()} if material_auth else {}),
        "push_guard": {"remote": "LOCAL", "ref": "HEAD", "baseline_remote_commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True).stdout.strip()},
        "state_requirements": {
            "control_path": "control.md",
            "required": {"CURRENT_MISSION": "TECHNICAL_HARDENING"},
            "forbidden": forbidden or {"R1_M4_OPENED": ["YES"]},
        },
        "schema_checks": [],
    }
    return MissionContract.from_dict(data)


def test_valid_mission_gets_pass_and_preserves_protected_untracked(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    (root / "src").mkdir()
    (root / "src" / "new.py").write_text("answer = 42\n", encoding="utf-8")

    result = run_mission_completion_gate(_contract(root), root)

    assert result.status is GateStatus.PASS
    assert result.evidence["protected_untracked"]["preserved"] is True
    assert result.evidence["push_policy"]["push_allowed"] is False


def test_non_repair_authorization_does_not_require_repair_evidence(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    contract = _contract(root, material_auth=True)
    contract = replace(
        contract,
        contains_material_repair=False,
        repair_integrity_evidence_path=None,
    )
    authorization = json.loads((root / contract.mission_authorization_path).read_text(encoding="utf-8"))
    authorization["authorization"]["contains_material_repair"] = False
    authorization["authorization"]["repair_integrity_evidence_path"] = "NONE"
    scope = {
        key: authorization.get(key, authorization["authorization"].get(key))
        for key in (
            "mission_id", "capability_ids", "role_ids", "execution_profile_ids",
            "execution_interface", "allowed_operations", "allowed_paths",
            "allowed_routes", "execution_mode", "live_state_sha256",
            "contains_material_repair", "repair_integrity_evidence_path",
        )
    }
    authorization["authorization"]["authorized_scope_sha256"] = scope_checksum(scope)
    authority_path = root / authorization["authorization"]["authority_ref"]
    authority = json.loads(authority_path.read_text(encoding="utf-8"))
    authority["authorized_scope_sha256"] = authorization["authorization"]["authorized_scope_sha256"]
    authority_path.write_text(json.dumps(authority) + "\n", encoding="utf-8")
    authorization["authorization"]["authority_sha256"] = hashlib.sha256(authority_path.read_bytes()).hexdigest()
    auth_path = root / contract.mission_authorization_path
    auth_path.write_text(json.dumps(authorization) + "\n", encoding="utf-8")
    contract = replace(contract, mission_authorization_sha256=hashlib.sha256(auth_path.read_bytes()).hexdigest())
    result = run_mission_completion_gate(contract, root)
    assert "REPAIR_COMPLETION_BLOCKED" not in result.violations
    assert "REQUIRED_REFERENCE_UNRESOLVED" not in result.violations


def test_material_repair_requires_an_evidence_path(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    with pytest.raises(MissionContractError, match="REPAIR_EVIDENCE_PATH_REQUIRED"):
        MissionContract.from_dict({
            "mission_id": "TECHNICAL_HARDENING", "artifact_id": "repair", "artifact_version": "1.0.0",
            "authorized_paths": ["src/", "control.md"], "protected_untracked_paths": [],
            "protected_untracked_baseline": [], "required_tests": [], "push_allowed": False,
            "push_guard": {"remote": "LOCAL", "ref": "HEAD", "baseline_remote_commit": "0" * 40},
            "contains_material_repair": True,
            "state_requirements": {"control_path": "control.md", "required": {}, "forbidden": {}}, "schema_checks": [],
        })


def test_material_repair_without_resolvable_evidence_blocks_completion(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    contract = replace(_contract(root, material_auth=True), contains_material_repair=True, repair_integrity_evidence_path="missing-repair.json")
    result = run_mission_completion_gate(contract, root)
    assert result.status is GateStatus.FAIL
    assert "REPAIR_COMPLETION_BLOCKED" in result.violations
    assert "REQUIRED_REFERENCE_UNRESOLVED" in result.violations


def test_material_repair_with_verified_evidence_can_complete(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    contract = replace(
        _contract(root, authorized=["src/", "control.md", "config/", "output/", "repair.json", "origin.md", "regression.txt", "review.txt", "review-output.json", "invalidation.txt", "revalidation.txt"], material_auth=True),
        contains_material_repair=True,
        repair_integrity_evidence_path="repair.json",
    )
    evidence = valid_evidence(root)
    evidence["mission_id"] = contract.mission_id
    evidence["mission_contract_sha256"] = contract.contract_sha256
    evidence["evidence_sha256"] = evidence_checksum(evidence)
    (root / "repair.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result = run_mission_completion_gate(contract, root)
    assert result.status is GateStatus.PASS, result.to_dict()
    assert result.evidence["repair_integrity"]["status"] == "PASS"


def test_material_completion_blocks_dependency_omitted_from_canonical_registry(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    contract = replace(
        _contract(root, authorized=["src/", "control.md", "config/", "output/", "repair.json", "origin.md", "regression.txt", "review.txt", "review-output.json", "invalidation.txt", "revalidation.txt"], material_auth=True),
        contains_material_repair=True,
        repair_integrity_evidence_path="repair.json",
    )
    evidence = valid_evidence(root)
    provenance_path = root / "output" / "execution_provenance_registry.json"
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    provenance["dependencies"] = {"origin_001": ["artifact_003"]}
    provenance_path.write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    evidence["provenance"]["registry_sha256"] = hashlib.sha256(provenance_path.read_bytes()).hexdigest()
    evidence["mission_id"] = contract.mission_id
    evidence["mission_contract_sha256"] = contract.contract_sha256
    evidence["evidence_sha256"] = evidence_checksum(evidence)
    (root / "repair.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result = run_mission_completion_gate(contract, root)
    assert result.status is GateStatus.FAIL
    assert "REPAIR_DOWNSTREAM_DEPENDENCY_OMITTED" in result.violations


def test_material_completion_blocks_unknown_canonical_downstream(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    contract = replace(
        _contract(root, authorized=["src/", "control.md", "config/", "output/", "repair.json", "origin.md", "regression.txt", "review.txt", "review-output.json", "invalidation.txt", "revalidation.txt"], material_auth=True),
        contains_material_repair=True,
        repair_integrity_evidence_path="repair.json",
    )
    evidence = valid_evidence(root)
    provenance_path = root / "output" / "execution_provenance_registry.json"
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    provenance.pop("dependencies", None)
    provenance_path.write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    evidence["provenance"]["registry_sha256"] = hashlib.sha256(provenance_path.read_bytes()).hexdigest()
    evidence["mission_id"] = contract.mission_id
    evidence["mission_contract_sha256"] = contract.contract_sha256
    evidence["evidence_sha256"] = evidence_checksum(evidence)
    (root / "repair.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result = run_mission_completion_gate(contract, root)
    assert result.status is GateStatus.FAIL
    assert "REPAIR_DOWNSTREAM_KNOWLEDGE_UNKNOWN" in result.violations


def test_mission_scope_boolean_mismatch_blocks(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    contract = replace(_contract(root, material_auth=True), contains_material_repair=False, repair_integrity_evidence_path="NONE")
    result = run_mission_completion_gate(contract, root)
    assert "MISSION_SCOPE_AUTHORIZATION_MISMATCH" in result.violations


def test_mission_scope_evidence_path_mismatch_blocks(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    contract = replace(_contract(root, material_auth=True), repair_integrity_evidence_path="other-repair.json")
    result = run_mission_completion_gate(contract, root)
    assert "MISSION_SCOPE_AUTHORIZATION_MISMATCH" in result.violations


def test_post_authorization_tampering_invalidates_authorization(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    contract = _contract(root, material_auth=True)
    authorization_path = root / contract.mission_authorization_path
    tampered = json.loads(authorization_path.read_text(encoding="utf-8"))
    tampered["authorization"]["contains_material_repair"] = False
    authorization_path.write_text(json.dumps(tampered) + "\n", encoding="utf-8")
    result = run_mission_completion_gate(contract, root)
    assert "MISSION_AUTHORIZATION_INVALID" in result.violations


def test_diff_check_failure_prevents_pass(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    (root / "src").mkdir()
    (root / "src" / "new.py").write_text("answer = 42  \n", encoding="utf-8")
    _git(root, "add", "src/new.py")

    result = run_mission_completion_gate(_contract(root), root)

    assert result.status is GateStatus.FAIL
    assert "DIFF_CHECK_FAILED" in result.violations


def test_out_of_scope_change_prevents_pass(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    (root / "README.md").write_text("outside\n", encoding="utf-8")

    result = run_mission_completion_gate(_contract(root), root)

    assert result.status is GateStatus.FAIL
    assert "UNEXPECTED_FILE_MODIFIED" in result.violations


def test_duplicate_yaml_key_is_detected(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    (root / "src").mkdir()
    (root / "src" / "config.yml").write_text("name: one\nname: two\n", encoding="utf-8")

    result = run_mission_completion_gate(_contract(root), root)

    assert result.status is GateStatus.FAIL
    assert "DUPLICATE_YAML_KEY" in result.violations


def test_required_test_failure_prevents_pass(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    failing = [{"label": "required failure", "command": [sys.executable, "-c", "raise SystemExit(9)"]}]

    result = run_mission_completion_gate(_contract(root, tests=failing), root)

    assert result.status is GateStatus.FAIL
    assert "REQUIRED_TEST_FAILED" in result.violations
    assert result.evidence["required_tests"][0]["returncode"] == 9


def test_forbidden_state_transition_prevents_pass(tmp_path: Path) -> None:
    root = _repo(tmp_path, state="YES")

    result = run_mission_completion_gate(_contract(root), root)

    assert result.status is GateStatus.FAIL
    assert "UNAUTHORIZED_STATE_TRANSITION" in result.violations


def test_gate_result_with_violations_cannot_be_pass() -> None:
    with pytest.raises(ValueError, match="Contradiccion detectada"):
        GateResult(
            gate_id="MISSION_COMPLETION",
            artifact_id="x",
            artifact_version="1.0.0",
            status=GateStatus.PASS,
            summary="free text says pass",
            violations=["REQUIRED_TEST_FAILED"],
        )


def test_contract_rejects_free_form_llm_claims() -> None:
    data = {
        "mission_id": "TECHNICAL_HARDENING",
        "artifact_id": "mission-completion-gate",
        "artifact_version": "1.0.0",
        "authorized_paths": ["src/"],
        "protected_untracked_paths": [],
        "required_tests": [],
        "push_allowed": False,
        "contains_material_repair": False,
        "push_guard": {"remote": "LOCAL", "ref": "HEAD", "baseline_remote_commit": "0" * 40},
        "state_requirements": {"control_path": "control.md", "required": {}, "forbidden": {}},
        "schema_checks": [],
        "llm_claim": "PASS",
    }
    with pytest.raises(MissionContractError):
        MissionContract.from_dict(data)


def test_gate_is_provider_and_ide_agnostic(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    result = run_mission_completion_gate(_contract(root), root)

    assert result.status is GateStatus.PASS
    assert "OpenCode" not in json.dumps(result.to_dict())
    assert "Codex" not in json.dumps(result.to_dict())


def test_schema_check_uses_real_json_validation(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    (root / "src").mkdir()
    (root / "src" / "payload.json").write_text(json.dumps({"name": 7}) + "\n", encoding="utf-8")
    (root / "src" / "payload.schema.json").write_text(
        json.dumps({"type": "object", "required": ["name"], "properties": {"name": {"type": "string"}}}) + "\n",
        encoding="utf-8",
    )
    contract = _contract(root, authorized=["src/", "control.md"])
    object.__setattr__(contract, "schema_checks", (("src/payload.json", "src/payload.schema.json"),))

    result = run_mission_completion_gate(contract, root)

    assert result.status is GateStatus.FAIL
    assert "SCHEMA_VALIDATION_FAILED" in result.violations


def test_duplicate_yaml_key_inside_markdown_is_detected(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    (root / "src").mkdir()
    (root / "src" / "control.md").write_text("```yaml\nR1_M1_STATUS: COMPLETED\nR1_M1_STATUS: BROKEN\n```\n", encoding="utf-8")

    result = run_mission_completion_gate(_contract(root), root)

    assert result.status is GateStatus.FAIL
    assert "DUPLICATE_YAML_KEY" in result.violations
    assert result.evidence["structural"]["yaml_markdown"]


def test_protected_untracked_content_change_prevents_pass(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    contract = _contract(root)
    (root / "protected.txt").write_text("tampered\n", encoding="utf-8")

    result = run_mission_completion_gate(contract, root)

    assert result.status is GateStatus.FAIL
    assert "PROTECTED_UNTRACKED_INTEGRITY_FAILED" in result.violations
    assert result.evidence["protected_untracked"]["checksum_mismatches"]


def test_dot_prefixed_protected_untracked_path_preserves_pass(tmp_path: Path) -> None:
    protected_path = ".agents/skills/tests-validacion-cierre/SKILL.md"
    root = _repo(tmp_path, protected_path=protected_path)
    contract = _contract(root, protected_path=protected_path)

    result = run_mission_completion_gate(contract, root)

    assert result.status is GateStatus.PASS, result.to_dict()
    assert result.evidence["protected_untracked"]["preserved"] is True
    assert result.evidence["protected_untracked"]["checksum_mismatches"] == []


def test_dot_prefixed_protected_untracked_content_change_prevents_pass(tmp_path: Path) -> None:
    protected_path = ".agents/skills/tests-validacion-cierre/SKILL.md"
    root = _repo(tmp_path, protected_path=protected_path)
    contract = _contract(root, protected_path=protected_path)
    (root / protected_path).write_text("tampered\n", encoding="utf-8")

    result = run_mission_completion_gate(contract, root)

    assert result.status is GateStatus.FAIL
    assert "PROTECTED_UNTRACKED_INTEGRITY_FAILED" in result.violations
    assert result.evidence["protected_untracked"]["checksum_mismatches"]


def test_new_file_inside_protected_tree_prevents_pass(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    protected_dir = root / "protected-dir"
    protected_dir.mkdir()
    base = protected_dir / "base.txt"
    base.write_text("base\n", encoding="utf-8")
    contract = replace(
        _contract(root),
        protected_untracked_paths=("protected.txt", "protected-dir"),
        protected_untracked_baseline=(
            ("protected.txt", hashlib.sha256((root / "protected.txt").read_bytes()).hexdigest()),
            ("protected-dir/base.txt", hashlib.sha256(base.read_bytes()).hexdigest()),
        ),
    )
    (protected_dir / "new.txt").write_text("new\n", encoding="utf-8")

    result = run_mission_completion_gate(contract, root)

    assert result.status is GateStatus.FAIL
    assert "protected-dir/new.txt" in result.evidence["protected_untracked"]["unexpected_files"]

def test_changed_remote_reference_prevents_pass(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    contract = _contract(root)
    object.__setattr__(contract, "push_guard", ("LOCAL", "HEAD", "0" * 40))

    result = run_mission_completion_gate(contract, root)

    assert result.status is GateStatus.FAIL
    assert "PUSH_DETECTED_OR_REMOTE_CHANGED" in result.violations
    assert result.evidence["push_policy"]["enforced"] is False
