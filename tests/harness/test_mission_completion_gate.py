"""Behavioral tests for the provider-neutral mission completion gate."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from src.core.gate_result import GateResult
from src.core.mission_completion_gate import MissionContract, MissionContractError, run_mission_completion_gate
from src.core.status import GateStatus


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)


def _repo(tmp_path: Path, *, state: str = "NO") -> Path:
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

    (root / "protected.txt").write_text("preserve me\n", encoding="utf-8")
    return root


def _contract(root: Path, *, authorized: list[str] | None = None, tests: list[dict[str, object]] | None = None, forbidden: dict[str, object] | None = None) -> MissionContract:
    data = {
        "mission_id": "TECHNICAL_HARDENING",
        "artifact_id": "mission-completion-gate",
        "artifact_version": "1.0.0",
        "authorized_paths": authorized or ["src/", "control.md"],
        "protected_untracked_paths": ["protected.txt"],
        "protected_untracked_baseline": [{"path": "protected.txt", "sha256": hashlib.sha256((root / "protected.txt").read_bytes()).hexdigest()}],
        "required_tests": tests or [{"label": "required smoke", "command": [sys.executable, "-c", "raise SystemExit(0)"]}],
        "push_allowed": False,
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


def test_changed_remote_reference_prevents_pass(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    contract = _contract(root)
    object.__setattr__(contract, "push_guard", ("LOCAL", "HEAD", "0" * 40))

    result = run_mission_completion_gate(contract, root)

    assert result.status is GateStatus.FAIL
    assert "PUSH_DETECTED_OR_REMOTE_CHANGED" in result.violations
    assert result.evidence["push_policy"]["enforced"] is False
