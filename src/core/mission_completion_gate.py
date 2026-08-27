"""Deterministic, provider-neutral completion gate for repository missions."""

from __future__ import annotations

import ast
import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from src.core.contract_validation import validate_against_schema
from src.core.gate_result import GateResult
from src.core.mission_authorization import MissionAuthorizationError, load_mission_authorization, scope_checksum, sha256_file
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
    protected_untracked_baseline: tuple[tuple[str, str], ...]
    required_tests: tuple[RequiredTest, ...]
    push_allowed: bool
    push_guard: tuple[str, str, str]
    contains_material_repair: bool
    repair_integrity_evidence_path: str | None
    mission_authorization_path: str | None
    mission_authorization_sha256: str | None
    control_path: str
    required_state: dict[str, str]
    forbidden_state: dict[str, tuple[str, ...]]
    schema_checks: tuple[tuple[str, str], ...]
    contract_sha256: str
    mission_mode: str
    objective: str | None
    reduced_fields: dict[str, Any]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MissionContract":
        violations = validate_against_schema(data, "mission_contract")
        if violations:
            raise MissionContractError("MissionContract inválido: " + "; ".join(violations))

        mission_mode = str(data.get("mission_mode", "LEGACY")).upper()
        if mission_mode == "REDUCED":
            required_reduced = (
                "objective", "canonical_inputs", "allowed_files", "expected_outputs",
                "deterministic_validations", "stop_conditions", "review_policy", "owner_closure",
            )
            missing = [key for key in required_reduced if key not in data]
            if missing:
                raise MissionContractError("REDUCED_MISSION_FIELDS_MISSING:" + ",".join(missing))
            if any(not _in_scope(path, data["authorized_paths"]) for path in data["allowed_files"]):
                raise MissionContractError("REDUCED_ALLOWED_FILES_OUTSIDE_AUTHORIZED_SCOPE")
            if not isinstance(data["review_policy"], dict) or data["review_policy"].get("required_review") not in {"SELF_ONLY", "INDEPENDENT_REVIEW", "OWNER_REVIEW"}:
                raise MissionContractError("REDUCED_REVIEW_POLICY_UNRESOLVED")
            if not isinstance(data["owner_closure"], dict) or not isinstance(data["owner_closure"].get("required"), bool):
                raise MissionContractError("REDUCED_OWNER_CLOSURE_UNRESOLVED")
        elif mission_mode != "LEGACY":
            raise MissionContractError("MISSION_MODE_UNRESOLVED")

        contains_material_repair = data["contains_material_repair"]
        repair_path = data.get("repair_integrity_evidence_path")
        if contains_material_repair and not repair_path:
            raise MissionContractError("REPAIR_EVIDENCE_PATH_REQUIRED")
        if repair_path and not _in_scope(_normalize_path(repair_path), data["authorized_paths"]):
            raise MissionContractError("REPAIR_EVIDENCE_PATH_OUT_OF_SCOPE")
        authorization_path = data.get("mission_authorization_path")
        authorization_sha256 = data.get("mission_authorization_sha256")
        if contains_material_repair and not authorization_path:
            raise MissionContractError("MISSION_AUTHORIZATION_PATH_REQUIRED")
        if contains_material_repair and not authorization_sha256:
            raise MissionContractError("MISSION_AUTHORIZATION_CHECKSUM_REQUIRED")

        state = data["state_requirements"]
        forbidden = {
            key: (value,) if isinstance(value, str) else tuple(value)
            for key, value in state["forbidden"].items()
        }
        baseline = tuple((_normalize_path(item["path"]), item["sha256"].lower()) for item in data["protected_untracked_baseline"])
        push_guard = data["push_guard"]
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
            protected_untracked_baseline=baseline,
            required_tests=tests,
            push_allowed=data["push_allowed"],
            push_guard=(push_guard["remote"], push_guard["ref"], push_guard["baseline_remote_commit"].lower()),
            contains_material_repair=contains_material_repair,
            repair_integrity_evidence_path=_normalize_path(repair_path) if repair_path else None,
            mission_authorization_path=_normalize_path(authorization_path) if authorization_path else None,
            mission_authorization_sha256=str(authorization_sha256).lower() if authorization_sha256 else None,
            control_path=_normalize_path(state["control_path"]),
            required_state=dict(state["required"]),
            forbidden_state=forbidden,
            schema_checks=tuple((_normalize_path(item["path"]), item["schema"]) for item in data["schema_checks"]),
            contract_sha256=_json_checksum(data),
            mission_mode=mission_mode,
            objective=data.get("objective"),
            reduced_fields={key: data[key] for key in ("preconditions", "canonical_inputs", "allowed_files", "non_objectives", "expected_outputs", "deterministic_validations", "adversarial_cases", "stop_conditions", "review_policy", "owner_closure") if key in data},
        )


def load_verified_completion_gate(path: str | Path) -> GateResult:
    result_path = Path(path)
    try:
        data = json.loads(result_path.read_text(encoding="utf-8"))
        result = GateResult.from_dict(data)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise PermissionError(f"MISSION_COMPLETION_GATE_REQUIRED: {exc}") from exc
    return validate_verified_completion_gate(result)


def validate_verified_completion_gate(result: GateResult) -> GateResult:
    if result.gate_id != "MISSION_COMPLETION" or result.status is not GateStatus.PASS or result.exit_code != 0 or result.violations:
        raise PermissionError("MISSION_COMPLETION_GATE_REQUIRED: result is not PASS")
    _validate_gate_evidence(result)
    return result


def verify_completion_gate_for_repository(
    path: str | Path,
    contract_path: str | Path,
    repo_root: str | Path,
) -> GateResult:
    supplied = load_verified_completion_gate(path)
    contract = load_mission_contract(contract_path)
    fresh = run_mission_completion_gate(contract, repo_root)
    if fresh.status is not GateStatus.PASS:
        raise PermissionError(
            "MISSION_COMPLETION_GATE_REQUIRED: fresh gate is not PASS: "
            + ", ".join(fresh.violations)
        )
    if _gate_semantic_payload(supplied) != _gate_semantic_payload(fresh):
        raise PermissionError(
            "MISSION_COMPLETION_GATE_REQUIRED: supplied result does not match a fresh gate execution"
        )
    return fresh


def _validate_gate_evidence(result: GateResult) -> None:
    evidence = result.evidence
    required_sections = {"binding", "git", "protected_untracked", "structural", "required_tests", "state", "push_policy"}
    if not isinstance(evidence, dict) or not required_sections.issubset(evidence):
        raise PermissionError("MISSION_COMPLETION_GATE_REQUIRED: mandatory evidence is missing")
    binding = evidence.get("binding")
    required_binding = {"binding_version", "gate_source", "mission_contract_sha256", "git_head", "git_status_sha256", "repo_root"}
    if not isinstance(binding, dict) or not required_binding.issubset(binding):
        raise PermissionError("MISSION_COMPLETION_GATE_REQUIRED: binding evidence is missing")
    if binding["binding_version"] != "1.0.0" or binding["gate_source"] != "run_mission_completion_gate":
        raise PermissionError("MISSION_COMPLETION_GATE_REQUIRED: invalid gate binding")
    for key in ("mission_contract_sha256", "git_status_sha256"):
        if not re.fullmatch(r"[0-9a-f]{64}", str(binding[key]).lower()):
            raise PermissionError(f"MISSION_COMPLETION_GATE_REQUIRED: invalid binding checksum {key}")


def _gate_semantic_payload(result: GateResult) -> dict[str, Any]:
    data = result.to_dict()
    data.pop("checked_at", None)
    return data

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
    head_result = _run_git(root, ["rev-parse", "HEAD"])
    if head_result["returncode"] != 0:
        violations.append("GIT_HEAD_UNAVAILABLE")
    evidence["binding"] = {
        "binding_version": "1.0.0",
        "gate_source": "run_mission_completion_gate",
        "mission_contract_sha256": contract.contract_sha256,
        "git_head": head_result["stdout"].strip(),
        "git_status_sha256": _sha256_bytes(status_porcelain["stdout"].encode("utf-8")),
        "repo_root": str(root),
    }
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
    baseline_paths = {path for path, _ in contract.protected_untracked_baseline}
    baseline_missing = sorted(
        path for path in contract.protected_untracked_paths
        if not any(_in_protected(candidate, (path,)) for candidate in baseline_paths)
    )
    baseline_outside_scope = sorted(
        path for path in baseline_paths
        if not _in_protected(path, contract.protected_untracked_paths)
    )
    protected_untracked_files = sorted(
        path for path in untracked
        if _in_protected(path, contract.protected_untracked_paths)
    )
    unexpected_files = sorted(
        path for path in protected_untracked_files
        if not _in_protected(path, baseline_paths)
    )
    checksum_mismatches = []
    for path, expected_checksum in contract.protected_untracked_baseline:
        target = root / Path(path)
        if not _has_untracked_match(path, untracked) or not target.is_file():
            checksum_mismatches.append({"path": path, "expected": expected_checksum, "observed": None})
            continue
        observed_checksum = _file_checksum(target)
        if observed_checksum != expected_checksum:
            checksum_mismatches.append({"path": path, "expected": expected_checksum, "observed": observed_checksum})
    protected_failed = bool(
        protected_missing or baseline_missing or baseline_outside_scope or unexpected_files or checksum_mismatches
    )
    if protected_failed:
        violations.append("PROTECTED_UNTRACKED_INTEGRITY_FAILED")
    evidence["protected_untracked"] = {
        "declared": list(contract.protected_untracked_paths),
        "missing": protected_missing,
        "baseline_missing": baseline_missing,
        "baseline_outside_scope": baseline_outside_scope,
        "untracked_files": protected_untracked_files,
        "unexpected_files": unexpected_files,
        "checksum_mismatches": checksum_mismatches,
        "preserved": not protected_failed,
    }

    structural_paths = sorted(set(changed + [contract.control_path]))
    structural = _run_structural_checks(root, structural_paths, contract.schema_checks)
    violations.extend(structural["violations"])
    evidence["structural"] = structural["evidence"]

    authorization_result = _verify_mission_scope_authorization(contract, root)
    evidence["mission_authorization"] = authorization_result["evidence"]
    violations.extend(authorization_result["violations"])

    repair_result = _run_repair_integrity_if_required(contract, root)
    evidence["repair_integrity"] = repair_result["evidence"]
    violations.extend(repair_result["violations"])

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

    push_evidence, push_violations = _check_push_policy(root, contract)
    violations.extend(push_violations)
    evidence["push_policy"] = push_evidence

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
    evidence: dict[str, Any] = {"json": [], "yaml": [], "yaml_markdown": [], "python": [], "schemas": []}
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
        elif suffix == ".md":
            markdown_results = _validate_markdown_yaml(path)
            evidence["yaml_markdown"].append({"path": relative, "blocks": markdown_results})
            if any(not item["valid"] for item in markdown_results):
                violations.append("DUPLICATE_YAML_KEY" if any(item.get("error", "").startswith("duplicate key:") for item in markdown_results) else "INVALID_YAML")
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


def _run_repair_integrity_if_required(contract: MissionContract, root: Path) -> dict[str, Any]:
    # MissionAuthorization may govern a non-repair execution mission.  Its
    # validation is handled by _verify_mission_scope_authorization; repair
    # evidence is required only when the mission actually declares a material
    # repair.  Do not turn the presence of an authorization path into a repair
    # obligation.
    if not contract.contains_material_repair:
        return {"violations": [], "evidence": {"required": False, "status": "NOT_REQUIRED"}}
    from src.scripts.repair_integrity_gate import run_repair_integrity_gate

    path = root / Path(contract.repair_integrity_evidence_path or "")
    if not path.is_file():
        return {
            "violations": ["REPAIR_COMPLETION_BLOCKED", "REQUIRED_REFERENCE_UNRESOLVED"],
            "evidence": {"required": True, "status": "UNRESOLVED", "path": contract.repair_integrity_evidence_path},
        }
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return {
            "violations": ["REPAIR_COMPLETION_BLOCKED", "REQUIRED_REFERENCE_UNRESOLVED"],
            "evidence": {"required": True, "status": "UNRESOLVED", "path": contract.repair_integrity_evidence_path, "error": str(exc)},
        }
    result = run_repair_integrity_gate(
        payload,
        repo_root=root,
        expected_mission_id=contract.mission_id,
        expected_contract_sha256=contract.contract_sha256,
        protected_paths=(contract.repair_integrity_evidence_path or "",),
        repair_evidence_path=contract.repair_integrity_evidence_path,
    )
    violations = list(result.violations)
    if result.status is not GateStatus.PASS:
        violations.extend(["REPAIR_COMPLETION_BLOCKED"])
    return {"violations": sorted(set(violations)), "evidence": result.to_dict()}


def _verify_mission_scope_authorization(contract: MissionContract, root: Path) -> dict[str, Any]:
    if not contract.contains_material_repair and (
        not contract.mission_authorization_path or contract.mission_authorization_path == "NONE"
    ):
        return {"violations": [], "evidence": {"required": False, "status": "NOT_REQUIRED"}}
    if not contract.mission_authorization_path:
        return {"violations": ["MISSION_AUTHORIZATION_INVALID"], "evidence": {"required": True, "status": "UNRESOLVED"}}
    path = root / Path(contract.mission_authorization_path)
    evidence: dict[str, Any] = {
        "required": True,
        "path": contract.mission_authorization_path,
        "expected_sha256": contract.mission_authorization_sha256,
    }
    try:
        path = path.resolve(strict=True)
        path.relative_to(root)
        actual_sha256 = sha256_file(path)
        evidence["actual_sha256"] = actual_sha256
        if actual_sha256.lower() != str(contract.mission_authorization_sha256).lower():
            return {"violations": ["MISSION_AUTHORIZATION_INVALID"], "evidence": {**evidence, "status": "CHECKSUM_MISMATCH"}}
        authorization = load_mission_authorization(path)
        evidence.update({
            "mission_id": authorization.mission_id,
            "contains_material_repair": authorization.contains_material_repair,
            "repair_integrity_evidence_path": authorization.repair_integrity_evidence_path,
            "authorized_scope_sha256": authorization.authorized_scope_sha256,
        })
        if authorization.mission_id != contract.mission_id:
            return {"violations": ["MISSION_SCOPE_AUTHORIZATION_MISMATCH"], "evidence": {**evidence, "status": "MISMATCH"}}
        if authorization.contains_material_repair != contract.contains_material_repair:
            return {"violations": ["MISSION_SCOPE_AUTHORIZATION_MISMATCH"], "evidence": {**evidence, "status": "MISMATCH"}}
        if _normalize_path(authorization.repair_integrity_evidence_path) != _normalize_path(contract.repair_integrity_evidence_path or "NONE"):
            return {"violations": ["MISSION_SCOPE_AUTHORIZATION_MISMATCH"], "evidence": {**evidence, "status": "MISMATCH"}}
        if scope_checksum(authorization.scope_payload()) != authorization.authorized_scope_sha256:
            return {"violations": ["MISSION_AUTHORIZATION_INVALID"], "evidence": {**evidence, "status": "SCOPE_CHECKSUM_MISMATCH"}}
        authorization.verify(
            root,
            capability_id=authorization.capability_ids[0],
            role_id=authorization.role_ids[0],
            operation=authorization.allowed_operations[0],
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError, MissionAuthorizationError, IndexError):
        return {"violations": ["MISSION_AUTHORIZATION_INVALID"], "evidence": {**evidence, "status": "INVALID"}}
    return {"violations": [], "evidence": {**evidence, "status": "PASS"}}


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


def _validate_markdown_yaml(path: Path) -> list[dict[str, Any]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    blocks: list[dict[str, Any]] = []
    in_yaml = False
    buffer: list[str] = []
    fence = chr(96) * 3
    for line in lines:
        marker = line.strip().lower()
        if not in_yaml and marker in {fence + "yaml", fence + "yml"}:
            in_yaml = True
            buffer = []
            continue
        if in_yaml and marker == fence:
            valid, error = _validate_yaml_text("\n".join(buffer))
            blocks.append({"valid": valid, **({"error": error} if error else {})})
            in_yaml = False
            buffer = []
            continue
        if in_yaml:
            buffer.append(line)
    if in_yaml:
        blocks.append({"valid": False, "error": "unterminated yaml fence"})
    return blocks


def _validate_yaml_text(content: str) -> tuple[bool, str | None]:
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
        yaml.load(content, Loader=UniqueKeyLoader)
    except (ValueError, yaml.YAMLError) as exc:
        return False, str(exc)
    return True, None

def _validate_yaml(path: Path) -> tuple[bool, str | None]:
    try:
        return _validate_yaml_text(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError) as exc:
        return False, str(exc)



def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()

def _json_checksum(value: Any) -> str:
    return _sha256_bytes(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))

def _file_checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _check_push_policy(root: Path, contract: MissionContract) -> tuple[dict[str, Any], list[str]]:
    if contract.push_allowed:
        return {"push_allowed": True, "verified": False, "enforced": False}, ["PUSH_POLICY_NOT_RESTRICTED"]
    remote, ref, baseline = contract.push_guard
    if remote == "LOCAL":
        command = ["git", "rev-parse", ref]
        result = _run_git(root, ["rev-parse", ref])
        verification = "LOCAL_REF"
    else:
        command = ["git", "ls-remote", remote, ref]
        result = _run_git(root, ["ls-remote", remote, ref])
        verification = "REMOTE_REF"
    evidence = {
        "push_allowed": False,
        "verification": verification,
        "remote": remote,
        "ref": ref,
        "baseline_remote_commit": baseline,
        "command": command,
        "returncode": result["returncode"],
        "stdout": result["stdout"],
        "stderr": result["stderr"],
        "verified": False,
        "enforced": False,
    }
    if result["returncode"] != 0:
        return evidence, ["PUSH_POLICY_UNVERIFIABLE"]
    observed = result["stdout"].split()[0].lower() if result["stdout"].split() else ""
    evidence["observed_remote_commit"] = observed
    evidence["verified"] = bool(observed) and observed == baseline
    evidence["enforced"] = evidence["verified"]
    if not evidence["verified"]:
        return evidence, ["PUSH_DETECTED_OR_REMOTE_CHANGED"]
    return evidence, []

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
    return any(
        normalized == _normalize_path(item)
        or normalized.startswith(_normalize_path(item).rstrip("/") + "/")
        for item in allowed
    )


def _in_protected(path: str, protected: Sequence[str]) -> bool:
    normalized = _normalize_path(path)
    return any(normalized == item or normalized.startswith(item.rstrip("/") + "/") for item in protected)


def _has_untracked_match(declared: str, untracked: Sequence[str]) -> bool:
    return any(_normalize_path(path) == declared or _normalize_path(path).startswith(declared.rstrip("/") + "/") for path in untracked)


def _is_git_metadata(path: str) -> bool:
    return _normalize_path(path).startswith(".git/")
