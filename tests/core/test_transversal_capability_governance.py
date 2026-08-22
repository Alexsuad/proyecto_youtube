from __future__ import annotations

import concurrent.futures
import hashlib
import json
from pathlib import Path

import pytest

from src.core.capability_governance import find_executable_capabilities_outside_registry, validate_capability_registry
from src.core.context_resolution import ContextResolutionError, resolve_context
from src.core.mission_authorization import MissionAuthorizationError, load_mission_authorization, scope_checksum, sha256_file
from src.core.portability_gate import evaluate_portability
from src.core.replay_protection import ReplayProtectionError, reserve_mission_execution
from src.scripts.channel_intelligence import active_profile, validate_topic_input


def _write(path: Path, content: str | bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, str):
        path.write_text(content, encoding="utf-8")
    else:
        path.write_bytes(content)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _material_decision(root: Path, *, decision_id: str = "MD-1", subject_ref: str = "capability:CAP", state: str = "VIGENTE", controlled_demonstration: bool = True) -> tuple[dict, dict]:
    _write(root / "legacy.md", "legacy")
    decision = {
        "decision_id": decision_id,
        "subject_ref": subject_ref,
        "decision": "Controlled capability demonstration.",
        "reason": "Fixture.",
        "authority": "CHANNEL_INTELLIGENCE",
        "state": state,
        "authorization_scope": {
            "capability_id": "CAP",
            "controlled_demonstration": controlled_demonstration,
            "general_activation": False,
            "product_use": False,
            "successor_capabilities": False,
        },
        "evidence_refs": ["legacy.md"],
        "superseded_by": None,
        "recorded_at": "2026-08-22T00:00:00Z",
    }
    registry = {
        "registry_version": "1.1.0",
        "decisions": [decision],
        "legacy_files": [{
            "file_path": "legacy.md", "decision_id": decision_id, "estado": "HISTORICA",
            "autoridad_sucesor": None, "consumer_activo": None, "duplicacion_material": None,
            "disposicion": "HISTORICAL_REFERENCE", "ejecutable": False,
        }],
    }
    _write(root / "docs/legacy/material_decision_registry.json", json.dumps(registry))
    _write(root / "config/capability_registry.json", json.dumps({
        "capabilities": [{
            "capability_id": "CAP",
            "functional_authority_domain": "CHANNEL_INTELLIGENCE",
        }],
    }))
    return decision, registry


def _bound_authorization(root: Path, decision: dict, *, binding_overrides: dict | None = None) -> tuple[object, dict]:
    state_digest = _write(root / "state.md", "STATE")
    scope = {
        "mission_id": "MATERIAL-BOUND", "capability_ids": ["CAP"], "role_ids": ["ROLE"],
        "execution_profile_ids": ["PROFILE"], "execution_interface": "INTERFACE",
        "allowed_operations": ["EXECUTE_CAPABILITY"], "allowed_paths": ["output/"],
        "allowed_routes": ["route"], "execution_mode": "SYNTHETIC", "live_state_sha256": state_digest,
        "contains_material_repair": False, "repair_integrity_evidence_path": "NONE",
    }
    binding = {
        "registry_path": "docs/legacy/material_decision_registry.json",
        "decision_id": decision["decision_id"],
        "subject_ref": decision["subject_ref"],
        "decision_sha256": scope_checksum(decision),
    }
    binding.update(binding_overrides or {})
    authority = {
        "mission_id": "MATERIAL-BOUND", "decision": "AUTHORIZED", "artifact_version": "1.0.0",
        "authorized_scope_sha256": scope_checksum(scope), "material_decision_binding": binding,
    }
    authority_digest = _write(root / "authority.json", json.dumps(authority))
    contract = {"mission_id": "MATERIAL-BOUND", "authorization": {
        "live_state_path": "state.md", "live_state_sha256": state_digest, "capability_ids": ["CAP"],
        "role_ids": ["ROLE"], "execution_profile_ids": ["PROFILE"], "execution_interface": "INTERFACE",
        "allowed_operations": ["EXECUTE_CAPABILITY"], "allowed_paths": ["output/"], "allowed_routes": ["route"],
        "execution_mode": "SYNTHETIC", "single_use": False, "authority_ref": "authority.json",
        "authority_sha256": authority_digest, "authorized_scope_sha256": scope_checksum(scope),
        "executor_substitution_policy": "COMPATIBLE_INTERFACE_ONLY", "contains_material_repair": False,
        "repair_integrity_evidence_path": "NONE",
    }}
    contract_path = root / "mission.json"
    contract_path.write_text(json.dumps(contract), encoding="utf-8")
    return load_mission_authorization(contract_path), binding


def test_current_capability_registry_has_resolvable_authority_domains() -> None:
    assert validate_capability_registry() == []


def test_executable_capability_outside_registry_is_reported(tmp_path: Path) -> None:
    canonical = tmp_path / "capability.json"
    external = tmp_path / "traceability.json"
    _write(canonical, json.dumps({"capabilities": [{"capability_id": "KNOWN"}]}))
    _write(external, json.dumps({"capabilities": [{"capability_id": "KNOWN"}, {"capability_id": "OUTSIDE"}]}))
    assert find_executable_capabilities_outside_registry(canonical, [external]) == ["CAPABILITY_OUTSIDE_CANONICAL_REGISTRY:OUTSIDE"]


def test_context_required_is_resolved_with_exact_bytes(tmp_path: Path) -> None:
    _write(tmp_path / "config/context_resolution_policy.json", json.dumps({
        "normative_allowed_roots": ["policies"],
        "evidentiary_allowed_roots": ["input"],
        "historical_allowed_roots": ["history"],
    }))
    digest = _write(tmp_path / "policies/rule.md", "regla\r\n")
    manifest = resolve_context([{
        "ref_id": "RULE-1", "context_class": "NORMATIVE", "artifact_path": "policies/rule.md",
        "artifact_type": "markdown", "artifact_version": "1.0.0", "artifact_sha256": digest,
        "authority_domain": "CHANNEL_INTELLIGENCE", "required": True,
    }], root=tmp_path, capability_id="CAP", role_id="ROLE", run_id="RUN")
    assert manifest["normative_refs"][0]["artifact_sha256"] == digest
    assert len(manifest["manifest_sha256"]) == 64


def test_context_blocks_traversal_and_required_checksum_mismatch(tmp_path: Path) -> None:
    _write(tmp_path / "config/context_resolution_policy.json", json.dumps({"normative_allowed_roots": ["policies"], "evidentiary_allowed_roots": [], "historical_allowed_roots": []}))
    _write(tmp_path / "policies/rule.md", "rule")
    base = {"ref_id": "R", "context_class": "NORMATIVE", "artifact_type": "markdown", "artifact_version": "UNDECLARED", "artifact_sha256": "0" * 64, "authority_domain": "D", "required": True}
    with pytest.raises(ContextResolutionError, match="CONTEXT_REQUIRED_UNRESOLVED"):
        resolve_context([{**base, "artifact_path": "policies/rule.md"}], root=tmp_path, capability_id="C", role_id="R", run_id="RUN")
    with pytest.raises(ContextResolutionError):
        resolve_context([{**base, "artifact_path": "../policies/rule.md"}], root=tmp_path, capability_id="C", role_id="R", run_id="RUN")


def test_mission_authorization_binds_live_state_and_authority(tmp_path: Path) -> None:
    state = tmp_path / "state.md"
    authority = tmp_path / "authority.json"
    state_digest = _write(state, "CURRENT_MISSION: TEST \n")
    scope = {
        "mission_id": "M-1", "capability_ids": ["CAP"], "role_ids": ["ROLE"], "execution_profile_ids": ["PROFILE"],
        "execution_interface": "INTERFACE", "allowed_operations": ["EXECUTE_CAPABILITY"], "allowed_paths": ["output"],
        "allowed_routes": ["ANY"], "execution_mode": "SYNTHETIC", "live_state_sha256": state_digest,
        "contains_material_repair": False, "repair_integrity_evidence_path": "NONE",
    }
    contract = {"mission_id": "M-1", "authorization": {
        "live_state_path": "state.md", "live_state_sha256": state_digest,
        "capability_ids": ["CAP"], "role_ids": ["ROLE"], "execution_profile_ids": ["PROFILE"],
        "execution_interface": "INTERFACE", "allowed_operations": ["EXECUTE_CAPABILITY"], "allowed_paths": ["output"],
        "allowed_routes": ["ANY"], "execution_mode": "SYNTHETIC", "single_use": True,
        "contains_material_repair": False, "repair_integrity_evidence_path": "NONE",
        "authority_ref": "authority.json", "authority_sha256": "0" * 64,
        "authorized_scope_sha256": scope_checksum(scope), "executor_substitution_policy": "COMPATIBLE_INTERFACE_ONLY",
    }}
    authority_digest = _write(authority, json.dumps({
        "decision": "APPROVE", "artifact_version": "1.0.0", "mission_id": "M-1",
        "authorized_scope_sha256": scope_checksum(scope),
    }))
    contract["authorization"]["authority_sha256"] = authority_digest
    contract_path = tmp_path / "mission.json"
    contract_path.write_text(json.dumps(contract), encoding="utf-8")
    auth = load_mission_authorization(contract_path)
    for field, value in (("contains_material_repair", True), ("repair_integrity_evidence_path", "other-repair.json")):
        tampered = json.loads(json.dumps(contract))
        tampered["authorization"][field] = value
        contract_path.write_text(json.dumps(tampered), encoding="utf-8")
        with pytest.raises(MissionAuthorizationError, match="authorized scope checksum"):
            load_mission_authorization(contract_path)
    contract_path.write_text(json.dumps(contract), encoding="utf-8")
    tampered = json.loads(json.dumps(contract))
    tampered["authorization"]["contains_material_repair"] = True
    contract_path.write_text(json.dumps(tampered), encoding="utf-8")
    with pytest.raises(MissionAuthorizationError, match="contract checksum"):
        auth.verify(tmp_path, capability_id="CAP", role_id="ROLE", operation="EXECUTE_CAPABILITY")
    contract_path.write_text(json.dumps(contract), encoding="utf-8")
    auth.verify(tmp_path, capability_id="CAP", role_id="ROLE", operation="EXECUTE_CAPABILITY",
               path="output/result.json", execution_mode="SYNTHETIC", execution_route="route_a",
               execution_profile_id="PROFILE", execution_interface="INTERFACE")
    state.write_text("CURRENT_MISSION: CHANGED \n", encoding="utf-8")
    with pytest.raises(MissionAuthorizationError, match="MISSION_STALE_AGAINST_LIVE_STATE"):
        auth.verify(tmp_path, capability_id="CAP", role_id="ROLE", operation="EXECUTE_CAPABILITY",
                    path="output/result.json", execution_mode="SYNTHETIC", execution_route="route_a",
                    execution_profile_id="PROFILE", execution_interface="INTERFACE")


def test_mission_authorization_material_decision_binding_is_fail_closed(tmp_path: Path) -> None:
    decision, registry = _material_decision(tmp_path)
    auth, binding = _bound_authorization(tmp_path, decision)
    auth.verify(
        tmp_path, capability_id="CAP", role_id="ROLE", operation="EXECUTE_CAPABILITY",
        path="output/result.json", execution_mode="SYNTHETIC", execution_route="route",
        execution_profile_id="PROFILE", execution_interface="INTERFACE",
        required_material_decision_ref={key: binding[key] for key in ("registry_path", "decision_id", "subject_ref")},
    )
    registry["decisions"][0]["state"] = "HISTORICA"
    _write(tmp_path / "docs/legacy/material_decision_registry.json", json.dumps(registry))
    with pytest.raises(MissionAuthorizationError, match="MATERIAL_DECISION_BINDING_INVALID"):
        auth.verify(
            tmp_path, capability_id="CAP", role_id="ROLE", operation="EXECUTE_CAPABILITY",
            required_material_decision_ref={key: binding[key] for key in ("registry_path", "decision_id", "subject_ref")},
        )


def test_mission_authorization_accepts_canonical_material_decision_binding(tmp_path: Path) -> None:
    decision, _ = _material_decision(tmp_path, decision_id="MD-CI-001")
    auth, binding = _bound_authorization(tmp_path, decision)
    auth.verify(
        tmp_path, capability_id="CAP", role_id="ROLE", operation="EXECUTE_CAPABILITY",
        path="output/result.json", execution_mode="SYNTHETIC", execution_route="route",
        execution_profile_id="PROFILE", execution_interface="INTERFACE",
        required_material_decision_ref={key: binding[key] for key in ("registry_path", "decision_id", "subject_ref")},
    )


def test_mission_authorization_rejects_non_canonical_material_registry(tmp_path: Path) -> None:
    decision, registry = _material_decision(tmp_path)
    alternate = tmp_path / "alternate-material-decisions.json"
    _write(alternate, json.dumps(registry))
    auth, binding = _bound_authorization(
        tmp_path,
        decision,
        binding_overrides={"registry_path": "alternate-material-decisions.json"},
    )
    with pytest.raises(MissionAuthorizationError, match="non-canonical registry"):
        auth.verify(
            tmp_path, capability_id="CAP", role_id="ROLE", operation="EXECUTE_CAPABILITY",
            required_material_decision_ref={key: binding[key] for key in ("registry_path", "decision_id", "subject_ref")},
        )


def test_mission_authorization_rejects_material_authority_domain_mismatch(tmp_path: Path) -> None:
    decision, registry = _material_decision(tmp_path)
    registry["decisions"][0]["authority"] = "SCRIPT_PRODUCT"
    _write(tmp_path / "docs/legacy/material_decision_registry.json", json.dumps(registry))
    auth, binding = _bound_authorization(tmp_path, decision)
    with pytest.raises(MissionAuthorizationError, match="authority mismatch"):
        auth.verify(
            tmp_path, capability_id="CAP", role_id="ROLE", operation="EXECUTE_CAPABILITY",
            required_material_decision_ref={key: binding[key] for key in ("registry_path", "decision_id", "subject_ref")},
        )


def test_mission_authorization_rejects_invalid_material_decision_variants(tmp_path: Path) -> None:
    decision, registry = _material_decision(tmp_path)
    auth, binding = _bound_authorization(tmp_path, decision)
    required_ref = {key: binding[key] for key in ("registry_path", "decision_id", "subject_ref")}
    for mutation in (
        lambda item: item.update({"state": "SUSTITUIDA"}),
        lambda item: item.update({"subject_ref": "capability:OTHER"}),
        lambda item: item["authorization_scope"].update({"controlled_demonstration": False}),
    ):
        current = json.loads(json.dumps(registry))
        mutation(current["decisions"][0])
        _write(tmp_path / "docs/legacy/material_decision_registry.json", json.dumps(current))
        with pytest.raises(MissionAuthorizationError, match="MATERIAL_DECISION_BINDING_INVALID"):
            auth.verify(
                tmp_path, capability_id="CAP", role_id="ROLE", operation="EXECUTE_CAPABILITY",
                required_material_decision_ref=required_ref,
            )

    _write(tmp_path / "docs/legacy/material_decision_registry.json", json.dumps(registry))
    missing_auth, missing_binding = _bound_authorization(
        tmp_path,
        decision,
        binding_overrides={"decision_id": "MD-MISSING"},
    )
    with pytest.raises(MissionAuthorizationError, match="MATERIAL_DECISION_BINDING_INVALID"):
        missing_auth.verify(
            tmp_path, capability_id="CAP", role_id="ROLE", operation="EXECUTE_CAPABILITY",
            required_material_decision_ref={key: missing_binding[key] for key in ("registry_path", "decision_id", "subject_ref")},
        )

    mismatched_auth, _ = _bound_authorization(
        tmp_path,
        decision,
        binding_overrides={"subject_ref": "capability:OTHER"},
    )
    with pytest.raises(MissionAuthorizationError, match="MATERIAL_DECISION_BINDING_MISMATCH"):
        mismatched_auth.verify(
            tmp_path, capability_id="CAP", role_id="ROLE", operation="EXECUTE_CAPABILITY",
            required_material_decision_ref=required_ref,
        )

def test_mission_replay_reservation_is_single_use(tmp_path: Path) -> None:
    registry = tmp_path / "provenance.json"
    first = reserve_mission_execution(registry, mission_id="M-1", contract_sha256="a" * 64, run_id="RUN-1")
    assert first["status"] == "RESERVED"
    with pytest.raises(ReplayProtectionError, match="MISSION_REPLAY_DETECTED"):
        reserve_mission_execution(registry, mission_id="M-1", contract_sha256="a" * 64, run_id="RUN-2")


def test_topic_first_no_work_is_valid_and_other_modes_block() -> None:
    profile = active_profile()
    base = {
        "topic_input_id": "T-1", "profile_id": profile["profile_id"], "profile_version": profile["profile_version"],
        "profile_checksum": profile["profile_checksum"], "topic": "Tema", "narrative_work": "NO_WORK_YET",
        "central_question": "Pregunta", "proposed_angle": "Angulo", "proposed_territory": "Territorio",
        "initial_evidence": ["evidence"], "strategic_triggers": {key: False for key in (
            "political_partisan_sensitivity", "high_sensitivity", "audience_matrix_change", "excluded_boundary_reinterpretation",
            "new_personal_exposure", "voice_or_author_persona_change", "positioning_expansion", "permanent_effect",
            "high_precedent_risk", "experimental_territory")}, "submitted_at": "2026-08-08T10:00:00Z",
    }
    assert validate_topic_input({**base, "entry_mode": "TOPIC_FIRST"}) == []
    assert "ENTRY_MODE_REQUIRES_ANCHOR_WORK" in validate_topic_input({**base, "entry_mode": "ANCHOR_WORK_FIRST"})
    assert "ENTRY_MODE_REQUIRES_CORPUS" in validate_topic_input({**base, "entry_mode": "CORPUS_FIRST"})

def test_context_json_uses_separate_raw_and_canonical_checksums(tmp_path: Path) -> None:
    _write(tmp_path / "config/context_resolution_policy.json", json.dumps({
        "normative_allowed_roots": ["policies"], "evidentiary_allowed_roots": [], "historical_allowed_roots": [],
    }))
    raw = '{ "b": 2, "a": 1 }'
    raw_digest = hashlib.sha256(raw.encode()).hexdigest()
    canonical_digest = hashlib.sha256(json.dumps({"a": 1, "b": 2}, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    _write(tmp_path / "policies/rule.json", raw)
    manifest = resolve_context([{
        "ref_id": "JSON-1", "context_class": "NORMATIVE", "artifact_path": "policies/rule.json",
        "artifact_type": "json", "artifact_version": "", "artifact_sha256": raw_digest,
        "canonical_payload_sha256": canonical_digest, "authority_domain": "INFRASTRUCTURE_GOVERNANCE", "required": True,
    }], root=tmp_path, capability_id="CAP", role_id="ROLE", run_id="RUN")
    row = manifest["normative_refs"][0]
    assert row["artifact_sha256"] == raw_digest
    assert row["canonical_payload_sha256"] == canonical_digest
    assert row["artifact_version"] == "UNDECLARED"

def test_optional_context_failure_is_explicitly_recorded(tmp_path: Path) -> None:
    _write(tmp_path / "config/context_resolution_policy.json", json.dumps({
        "normative_allowed_roots": ["policies"], "evidentiary_allowed_roots": [], "historical_allowed_roots": [],
    }))
    manifest = resolve_context([{
        "ref_id": "OPTIONAL-1", "context_class": "NORMATIVE", "artifact_path": "policies/missing.md",
        "artifact_type": "markdown", "artifact_version": "1.0.0", "artifact_sha256": "0" * 64,
        "authority_domain": "INFRASTRUCTURE_GOVERNANCE", "required": False,
    }], root=tmp_path, capability_id="CAP", role_id="ROLE", run_id="RUN")
    assert manifest["unresolved_optional_refs"] == ["CONTEXT_OPTIONAL_UNRESOLVED:OPTIONAL-1"]


def test_symlink_escape_is_blocked_when_platform_allows_symlinks(tmp_path: Path) -> None:
    _write(tmp_path / "config/context_resolution_policy.json", json.dumps({
        "normative_allowed_roots": ["policies"], "evidentiary_allowed_roots": [], "historical_allowed_roots": [],
    }))
    _write(tmp_path / "outside.md", "outside")
    (tmp_path / "policies").mkdir()
    try:
        (tmp_path / "policies/link.md").symlink_to(tmp_path / "outside.md")
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation is unavailable in this environment")
    with pytest.raises(ContextResolutionError):
        resolve_context([{
            "ref_id": "LINK", "context_class": "NORMATIVE", "artifact_path": "policies/link.md",
            "artifact_type": "markdown", "artifact_version": "1.0.0", "artifact_sha256": "0" * 64,
            "authority_domain": "INFRASTRUCTURE_GOVERNANCE", "required": True,
        }], root=tmp_path, capability_id="CAP", role_id="ROLE", run_id="RUN")


def test_compatible_executor_substitution_does_not_change_functional_authority(tmp_path: Path) -> None:
    state = tmp_path / "state.md"
    authority = tmp_path / "authority.json"
    state_digest = _write(state, "STATE")
    scope = {
        "mission_id": "M-EXEC", "capability_ids": ["CAP"], "role_ids": ["ROLE"], "execution_profile_ids": ["PROFILE"],
        "execution_interface": "INTERFACE", "allowed_operations": ["EXECUTE_CAPABILITY"], "allowed_paths": ["output"],
        "allowed_routes": ["route_a"], "execution_mode": "SYNTHETIC", "live_state_sha256": state_digest,
        "contains_material_repair": False, "repair_integrity_evidence_path": "NONE",
    }
    authority_digest = _write(authority, json.dumps({
        "decision": "APPROVE", "artifact_version": "1.0.0", "mission_id": "M-EXEC",
        "authorized_scope_sha256": scope_checksum(scope),
    }))
    contract = {"mission_id": "M-EXEC", "authorization": {
        "live_state_path": "state.md", "live_state_sha256": state_digest, "capability_ids": ["CAP"],
        "role_ids": ["ROLE"], "execution_profile_ids": ["PROFILE"], "execution_interface": "INTERFACE",
        "allowed_operations": ["EXECUTE_CAPABILITY"], "allowed_paths": ["output"], "allowed_routes": ["route_a"],
        "execution_mode": "SYNTHETIC", "single_use": True, "authority_ref": "authority.json",
        "contains_material_repair": False, "repair_integrity_evidence_path": "NONE",
        "authority_sha256": authority_digest, "authorized_scope_sha256": scope_checksum(scope),
        "executor_substitution_policy": "COMPATIBLE_INTERFACE_ONLY",
    }}
    path = tmp_path / "mission.json"
    path.write_text(json.dumps(contract), encoding="utf-8")
    auth = load_mission_authorization(path)
    auth.verify(tmp_path, capability_id="CAP", role_id="ROLE", operation="EXECUTE_CAPABILITY",
               path="output/result.json", execution_mode="SYNTHETIC", execution_route="route_a",
               execution_profile_id="PROFILE", execution_interface="INTERFACE")
    with pytest.raises(MissionAuthorizationError, match="execution interface"):
        auth.verify(tmp_path, capability_id="CAP", role_id="ROLE", operation="EXECUTE_CAPABILITY",
                    path="output/result.json", execution_mode="SYNTHETIC", execution_route="route_a",
                    execution_profile_id="PROFILE", execution_interface="INCOMPATIBLE_INTERFACE")
    forbidden = json.loads(json.dumps(contract))
    forbidden["authorization"]["executor_substitution_policy"] = "FORBIDDEN"
    forbidden_path = tmp_path / "mission_forbidden.json"
    forbidden_path.write_text(json.dumps(forbidden), encoding="utf-8")
    with pytest.raises(MissionAuthorizationError, match="MISSION_CONTRACT_INVALID"):
        load_mission_authorization(forbidden_path)

def test_replay_reservation_is_atomic_under_concurrency(tmp_path: Path) -> None:
    registry = tmp_path / "provenance.json"
    def reserve(index: int):
        try:
            return ("ok", reserve_mission_execution(registry, mission_id="M-CONCURRENT", contract_sha256="b" * 64, run_id=f"RUN-{index}"))
        except ReplayProtectionError as exc:
            return ("error", str(exc))
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(reserve, range(8)))
    assert sum(kind == "ok" for kind, _ in results) == 1
    assert sum(value == "MISSION_REPLAY_DETECTED" for kind, value in results if kind == "error") == 7


def test_topic_modes_require_corpus_and_clarify_real_topic_first() -> None:
    profile = active_profile()
    base = {
        "topic_input_id": "T-2", "profile_id": profile["profile_id"], "profile_version": profile["profile_version"],
        "profile_checksum": profile["profile_checksum"], "topic": "Tema", "narrative_work": "NO_WORK_YET",
        "central_question": "Pregunta", "proposed_angle": "Angulo", "proposed_territory": "Territorio",
        "initial_evidence": ["evidence"], "strategic_triggers": {key: False for key in (
            "political_partisan_sensitivity", "high_sensitivity", "audience_matrix_change", "excluded_boundary_reinterpretation",
            "new_personal_exposure", "voice_or_author_persona_change", "positioning_expansion", "permanent_effect",
            "high_precedent_risk", "experimental_territory")}, "submitted_at": "2026-08-08T10:00:00Z",
    }
    assert "ENTRY_MODE_REQUIRES_CORPUS" in validate_topic_input({**base, "entry_mode": "CORPUS_FIRST"})
    assert validate_topic_input({**base, "entry_mode": "CORPUS_FIRST", "corpus_ref": "corpus-1"}) == []
    assert validate_topic_input({**base, "entry_mode": "TOPIC_FIRST", "narrative_work": "Obra"}) == []

def test_missing_entry_mode_is_rejected_by_canonical_schema() -> None:
    profile = active_profile()
    data = {
        "topic_input_id": "T-MISSING-MODE", "profile_id": profile["profile_id"],
        "profile_version": profile["profile_version"], "profile_checksum": profile["profile_checksum"],
        "topic": "Tema", "narrative_work": "NO_WORK_YET", "central_question": "Pregunta",
        "proposed_angle": "Angulo", "proposed_territory": "Territorio", "initial_evidence": ["evidence"],
        "strategic_triggers": {key: False for key in (
            "political_partisan_sensitivity", "high_sensitivity", "audience_matrix_change",
            "excluded_boundary_reinterpretation", "new_personal_exposure", "voice_or_author_persona_change",
            "positioning_expansion", "permanent_effect", "high_precedent_risk", "experimental_territory",
        )}, "submitted_at": "2026-08-08T10:00:00Z",
    }
    violations = validate_topic_input(data)
    assert any("entry_mode" in violation for violation in violations)


def test_readiness_is_not_inferred_from_implemented_maturity() -> None:
    registry = json.loads((Path(__file__).parents[2] / "config" / "capability_registry.json").read_text(encoding="utf-8"))
    assert registry["compatibility_tokens"]["availability"]["IMPLEMENTED_NOT_DEMONSTRATED"] == "UNMAPPED_IMPLEMENTED_NOT_DEMONSTRATED"
    assert registry["capabilities"][0]["availability_status"] == "NON_EXECUTABLE_CURRENT"
    assert validate_capability_registry() == []


def test_portability_gate_preserves_operational_metadata_but_rejects_functional_binding() -> None:
    operational = evaluate_portability({"provenance": {"provider": "provider-x", "model": "model-y", "cost": 1.5}})
    assert operational.status == "PASS"
    assert "provenance.provider" in operational.operational_metadata
    assert "provenance.model" in operational.operational_metadata
    rejected = evaluate_portability({"functional_identity": {"provider": "provider-x"}})
    assert rejected.status == "FAIL"
    assert "FUNCTIONAL_IDENTITY_DEPENDENCY:functional_identity.provider" in rejected.violations


def _minimal_capability_registry(path: Path, capability: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "registry_version": "1.0.0",
        "authority": "CAPABILITY_FUNCTIONAL_AUTHORITY",
        "routing_consumer": "config/capability_routing.yaml",
        "compatibility_tokens": {"maturity": {}, "availability": {}, "assurance": {}, "approval": {}, "evidence": {}},
        "capabilities": [capability],
    }), encoding="utf-8")
    return path


def test_semantic_artifacts_are_required_only_after_implementation(tmp_path: Path) -> None:
    path = _minimal_capability_registry(tmp_path / "config" / "capability_registry.json", {
        "capability_id": "DEFINED_SEMANTIC", "domain": "CHANNEL_INTELLIGENCE",
        "functional_authority_domain": "CHANNEL_INTELLIGENCE", "purpose": "deferred semantic definition",
        "functional_requirements": [], "implementation_kind": "SEMANTIC", "maturity_status": "DEFINED",
    })
    assert validate_capability_registry(path) == []


def test_deterministic_executability_does_not_require_semantic_artifacts(tmp_path: Path) -> None:
    _write(tmp_path / "impl.py", "VALUE = 1\n")
    path = _minimal_capability_registry(tmp_path / "config" / "capability_registry.json", {
        "capability_id": "DETERMINISTIC_READY", "domain": "INFRASTRUCTURE_GOVERNANCE",
        "functional_authority_domain": "INFRASTRUCTURE_GOVERNANCE", "purpose": "deterministic check",
        "functional_requirements": [], "implementation_kind": "DETERMINISTIC", "maturity_status": "IMPLEMENTED",
        "availability_status": "READY_NOT_AUTHORIZED", "implementation_refs": ["impl.py"],
        "executability_evidence": {
            "contracts_resolvable": True, "implementation_present": True, "dependencies_satisfied": True,
        },
    })
    assert validate_capability_registry(path) == []
