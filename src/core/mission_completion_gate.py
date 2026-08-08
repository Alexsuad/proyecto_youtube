"""Deterministic, provider-neutral completion gate for repository missions."""

from __future__ import annotations

import ast
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from src.core.contract_validation import validate_against_schema
from src.core.gate_result import GateResult
from src.core.status import GateStatus


class MissionContractError(ValueError):
    """Raised when a structured mission contract is invalid."""


@dataclass(frozen=True)
class RequiredTest:
    label: str
    command: tuple[str, ...]
    timeout_seconds: int = 120


@dataclass(frozen=True)
class MissionContract:
    mission_id: str
    artifact_id: str
    artifact_version: str
    authorized_paths: tuple[str, ...]
    protected_untracked_paths: tuple[str, ...]
    required_tests: tuple[RequiredTest, ...]
    push_allowed: bool
    control_path: str
    required_state: dict[str, str]
    forbidden_state: dict[str, tuple[str, ...]]
    schema_checks: tuple[tuple[str, str], ...]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MissionContract":
        violations = validate_against_schema(data, "mission_contract")
        if violations:
            raise MissionContractError("MissionContract inválido: " + "; ".join(violations))

        state = data["state_requirements"]
        forbidden = {
            key: (value,) if isinstance(value, str) else tuple(value)
            for key, value in state["forbidden"].items()
        }
        tests = tuple(
            RequiredTest(
                label=item["label"],
                command=tuple(item["command"]),
                timeout_seconds=item.get("timeout_seconds", 120),
            )
            for item in data["required_tests"]
        )
        return cls(
            mission_id=data["mission_id"],
            artifact_id=data["artifact_id"],
            artifact_version=data["artifact_version"],
            authorized_paths=tuple(_normalize_path(item) for item in data["authorized_paths"]),
            protected_untracked_paths=tuple(_normalize_path(item) for item in data["protected_untracked_paths"]),
            required_tests=tests,
            push_allowed=data["push_allowed"],
            control_path=_normalize_path(state["control_path"]),
            required_state=dict(state["required"]),
            forbidden_state=forbidden,
            schema_checks=tuple((_normalize_path(item["path"]), item["schema"]) for item in data["schema_checks"]),
        )


def load_mission_contract(path: str | Path) -> MissionContract:
    contract_path = Path(path)
    data = json.loads(contract_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise MissionContractError("MissionContract debe ser un objeto JSON.")
    return MissionContract.from_dict(data)


def run_mission_completion_gate(contract: MissionContract, repo_root: str | Path) -> GateResult:
    """Run all deterministic checks and return the canonical GateResult."""

    root = Path(repo_root).resolve()
    violations: list[str] = []
    evidence: dict[str, Any] = {"mission_id": contract.mission_id}

    status_porcelain = _run_git(root, ["status", "--porcelain=v1", "--untracked-files=all"])
    if status_porcelain["returncode"] != 0:
        violations.append("GIT_STATUS_FAILED")
        status_lines: list[str] = []
    else:
        status_lines = status_porcelain["stdout"].splitlines()
    modified = _git_names(root, ["diff", "--name-only"])
    staged = _git_names(root, ["diff", "--cached", "--name-only"])
    untracked = _run_git(root, ["ls-files", "--others", "--exclude-standard"])["stdout"].splitlines()
    changed = sorted(set(modified + staged + untracked))
    outside_scope = sorted(path for path in changed if not _in_scope(path, contract.authorized_paths) and not _in_protected(path, contract.protected_untracked_paths) and not _is_git_metadata(path))
    unexpected = sorted(path for path in untracked if not _in_scope(path, contract.authorized_paths) and not _in_protected(path, contract.protected_untracked_paths))
    if outside_scope:
        violations.append("UNEXPECTED_FILE_MODIFIED")
    if unexpected:
        violations.append("UNEXPECTED_FILE_CREATED")

    diff_checks = {
        "unstaged": _run_git(root, ["diff", "--check"]),
        "staged": _run_git(root, ["diff", "--cached", "--check"]),
    }
    if any(result["returncode"] != 0 for result in diff_checks.values()):
        violations.append("DIFF_CHECK_FAILED")
    evidence["git"] = {
        "status_lines": status_lines,
        "modified_files": modified,
        "staged_files": staged,
        "untracked_files": untracked,
        "outside_scope": outside_scope,
        "unexpected_files": unexpected,
        "diff_check": diff_checks,
    }

    protected_missing = [
        path for path in contract.protected_untracked_paths
        if not _has_untracked_match(path, untracked)
    ]
    if protected_missing:
        violations.append("PROTECTED_UNTRACKED_NOT_PRESERVED")
    evidence["protected_untracked"] = {
        "declared": list(contract.protected_untracked_paths),
        "missing": protected_missing,
        "preserved": not protected_missing,
    }

    structural = _run_structural_checks(root, changed, contract.schema_checks)
    violations.extend(structural["violations"])
    evidence["structural"] = structural["evidence"]

    tests = []
    for required_test in contract.required_tests:
        result = _run_command(root, required_test.command, required_test.timeout_seconds)
        record = {"label": required_test.label, "command": list(required_test.command), **result}
        tests.append(record)
        if result["returncode"] != 0:
            violations.append("REQUIRED_TEST_FAILED")
    evidence["required_tests"] = tests

    state_evidence, state_violations = _check_state(root, contract)
    violations.extend(state_violations)
    evidence["state"] = state_evidence

    if contract.push_allowed:
        evidence["push_policy"] = {"push_allowed": True, "enforced": False}
        violations.append("PUSH_POLICY_NOT_RESTRICTED")
    else:
        evidence["push_policy"] = {"push_allowed": False, "enforced": True, "push_invoked_by_gate": False}

    status = GateStatus.FAIL if violations else GateStatus.PASS
    return GateResult(
        gate_id="MISSION_COMPLETION",
        artifact_id=contract.artifact_id,
        artifact_version=contract.artifact_version,
        status=status,
        summary=("Deterministic mission completion checks passed." if not violations else "Mission completion blocked by deterministic violations."),
        violations=sorted(set(violations)),
        evidence=evidence,
        checker_version="1.0.0",
    )


def _run_structural_checks(root: Path, changed: Sequence[str], schema_checks: Sequence[tuple[str, str]]) -> dict[str, Any]:
    violations: list[str] = []
    evidence: dict[str, Any] = {"json": [], "yaml": [], "python": [], "schemas": []}
    for relative in changed:
        path = root / Path(relative)
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        if suffix == ".json":
            try:
                json.loads(path.read_text(encoding="utf-8"))
                evidence["json"].append({"path": relative, "valid": True})
            except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                violations.append("INVALID_JSON")
                evidence["json"].append({"path": relative, "valid": False, "error": str(exc)})
        elif suffix in {".yaml", ".yml"}:
            valid, error = _validate_yaml(path)
            evidence["yaml"].append({"path": relative, "valid": valid, **({"error": error} if error else {})})
            if not valid:
                violations.append("DUPLICATE_YAML_KEY" if error and error.startswith("duplicate key:") else "INVALID_YAML")
        elif suffix == ".py":
            try:
                ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
                evidence["python"].append({"path": relative, "valid": True})
            except (OSError, UnicodeDecodeError, SyntaxError) as exc:
                violations.append("PYTHON_SYNTAX_INVALID")
                evidence["python"].append({"path": relative, "valid": False, "error": str(exc)})

    for relative, schema_name in schema_checks:
        path = root / Path(relative)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            schema_violations = validate_against_schema(data, schema_name)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, FileNotFoundError) as exc:
            schema_violations = [str(exc)]
        evidence["schemas"].append({"path": relative, "schema": schema_name, "violations": schema_violations})
        if schema_violations:
            violations.append("SCHEMA_VALIDATION_FAILED")
    return {"violations": violations, "evidence": evidence}


def _check_state(root: Path, contract: MissionContract) -> tuple[dict[str, Any], list[str]]:
    path = root / Path(contract.control_path)
    if not path.is_file():
        return {"control_path": contract.control_path, "read": False}, ["CONTROL_STATE_UNAVAILABLE"]
    values = _read_declared_values(path)
    violations: list[str] = []
    required_failures = []
    forbidden_hits = []
    for key, expected in contract.required_state.items():
        if values.get(key) != expected:
            required_failures.append({"key": key, "expected": expected, "observed": values.get(key)})
    for key, forbidden in contract.forbidden_state.items():
        if values.get(key) in forbidden:
            forbidden_hits.append({"key": key, "forbidden": list(forbidden), "observed": values.get(key)})
    if required_failures:
        violations.append("REQUIRED_STATE_NOT_SATISFIED")
    if forbidden_hits:
        violations.append("UNAUTHORIZED_STATE_TRANSITION")
    return {
        "control_path": contract.control_path,
        "read": True,
        "required": required_failures,
        "forbidden": forbidden_hits,
    }, violations


def _read_declared_values(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    pattern = re.compile(r"^([A-Z][A-Z0-9_]*)\s*:\s*(.*?)\s*$")
    for line in path.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line.strip())
        if match:
            value = match.group(2).strip().strip('`').strip('"').strip("'")
            values[match.group(1)] = value
    return values


def _validate_yaml(path: Path) -> tuple[bool, str | None]:
    try:
        import yaml
    except ImportError as exc:
        return False, f"yaml dependency unavailable: {exc}"

    class UniqueKeyLoader(yaml.SafeLoader):
        pass

    def construct_mapping(loader: Any, node: Any, deep: bool = False) -> dict[Any, Any]:
        mapping: dict[Any, Any] = {}
        for key_node, value_node in node.value:
            key = loader.construct_object(key_node, deep=deep)
            if key in mapping:
                raise ValueError(f"duplicate key: {key}")
            mapping[key] = loader.construct_object(value_node, deep=deep)
        return mapping

    UniqueKeyLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_mapping)
    try:
        yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueKeyLoader)
    except (OSError, UnicodeDecodeError, ValueError, yaml.YAMLError) as exc:
        return False, str(exc)
    return True, None


def _run_command(root: Path, command: Sequence[str], timeout_seconds: int) -> dict[str, Any]:
    try:
        result = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=timeout_seconds, check=False)
    except subprocess.TimeoutExpired as exc:
        return {"returncode": 124, "stdout": _output(exc.stdout), "stderr": "TIMEOUT"}
    except OSError as exc:
        return {"returncode": 127, "stdout": "", "stderr": str(exc)}
    return {"returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr}


def _run_git(root: Path, args: Sequence[str]) -> dict[str, Any]:
    return _run_command(root, ["git", *args], 30)


def _git_names(root: Path, args: Sequence[str]) -> list[str]:
    result = _run_git(root, args)
    return sorted(set(result["stdout"].splitlines())) if result["returncode"] == 0 else []


def _output(value: str | bytes | None) -> str:
    if value is None:
        return ""
    return value.decode(errors="replace") if isinstance(value, bytes) else value


def _normalize_path(path: str) -> str:
    return Path(path).as_posix().lstrip("./")


def _in_scope(path: str, allowed: Sequence[str]) -> bool:
    normalized = _normalize_path(path)
    return any(normalized == item or normalized.startswith(item.rstrip("/") + "/") for item in allowed)


def _in_protected(path: str, protected: Sequence[str]) -> bool:
    normalized = _normalize_path(path)
    return any(normalized == item or normalized.startswith(item.rstrip("/") + "/") for item in protected)


def _has_untracked_match(declared: str, untracked: Sequence[str]) -> bool:
    return any(_normalize_path(path) == declared or _normalize_path(path).startswith(declared.rstrip("/") + "/") for path in untracked)


def _is_git_metadata(path: str) -> bool:
    return _normalize_path(path).startswith(".git/")
