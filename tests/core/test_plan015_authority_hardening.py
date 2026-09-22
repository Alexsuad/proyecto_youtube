from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.ai import execution as ai_execution
from src.ai.contracts import ExecutionRequest
from src.application.research_m7 import RealResearchRoutePreparation
from src.core import execution_preflight
from src.core.mission_authorization import (
    MissionAuthorizationError,
    load_mission_authorization,
    scope_checksum,
)
from src.core.mission_completion_gate import load_mission_contract
from src.core.product_authorization import (
    ProductAuthorizationError,
    authorization_checksum,
    resolve_product_authorization,
)
from src.ai.providers.agent_handoff import AgentHandoffProvider


ROOT = Path(__file__).resolve().parents[2]


def _sha256_json(data: object) -> str:
    return hashlib.sha256(
        json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _product_root(tmp_path: Path) -> tuple[Path, dict]:
    root = tmp_path / "product-authority"
    for relative in (
        "config/product_capability_authorizations.json",
        "docs/legacy/material_decision_registry.json",
    ):
        source = ROOT / relative
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    registry_path = root / "config/product_capability_authorizations.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    return root, registry


def _write_product_registry(root: Path, registry: dict) -> None:
    (root / "config/product_capability_authorizations.json").write_text(
        json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _resolve_topic_product(root: Path) -> object:
    return resolve_product_authorization(
        root,
        capability_id="TOPIC_BELONGING_ASSESSMENT",
        role_id="CHANNEL_INTELLIGENCE_REVIEWER",
        execution_family="AGENT_HARNESS",
        execution_route="agent_harness",
        execution_profile_id="EXECUTOR_MANAGED",
        execution_interface="TOPIC_BELONGING_TERMINAL",
        path="handoff/",
    )[0]


def _replace_topic_material_reference(root: Path, registry: dict, decision_id: str) -> None:
    authorization = registry["authorizations"][0]
    decisions = json.loads(
        (root / "docs/legacy/material_decision_registry.json").read_text(encoding="utf-8")
    )["decisions"]
    decision = next((item for item in decisions if item["decision_id"] == decision_id), None)
    authorization["material_decision_ref"]["decision_id"] = decision_id
    authorization["material_decision_ref"]["decision_sha256"] = (
        _sha256_json(decision) if decision is not None else "0" * 64
    )
    authorization["authorization_checksum"] = authorization_checksum(authorization)
    _write_product_registry(root, registry)


def test_product_material_decision_vigente_passes(tmp_path: Path) -> None:
    root, registry = _product_root(tmp_path)
    _write_product_registry(root, registry)
    assert _resolve_topic_product(root).authorization_id == "PCA-PLAN015-TOPIC-001"


def test_product_material_decision_sustituida_is_blocked(tmp_path: Path) -> None:
    root, registry = _product_root(tmp_path)
    _replace_topic_material_reference(root, registry, "MD-CI-001")
    with pytest.raises(ProductAuthorizationError, match="MATERIAL_DECISION_MISSING"):
        _resolve_topic_product(root)


def test_product_material_decision_checksum_mismatch_is_blocked(tmp_path: Path) -> None:
    root, registry = _product_root(tmp_path)
    authorization = registry["authorizations"][0]
    authorization["material_decision_ref"]["decision_sha256"] = "0" * 64
    authorization["authorization_checksum"] = authorization_checksum(authorization)
    _write_product_registry(root, registry)
    with pytest.raises(ProductAuthorizationError, match="MATERIAL_DECISION_CHECKSUM_MISMATCH"):
        _resolve_topic_product(root)


def test_product_material_decision_unknown_id_is_blocked(tmp_path: Path) -> None:
    root, registry = _product_root(tmp_path)
    _replace_topic_material_reference(root, registry, "MD-UNKNOWN")
    with pytest.raises(ProductAuthorizationError, match="MATERIAL_DECISION_MISSING"):
        _resolve_topic_product(root)


def test_product_authorization_rejects_unlisted_api_family(tmp_path: Path) -> None:
    root, registry = _product_root(tmp_path)
    _write_product_registry(root, registry)
    with pytest.raises(ProductAuthorizationError, match="PRODUCT_AUTHORIZATION_DENY"):
        resolve_product_authorization(
            root,
            capability_id="TOPIC_BELONGING_ASSESSMENT",
            role_id="CHANNEL_INTELLIGENCE_REVIEWER",
            execution_family="API_PROVIDER",
            execution_route="api",
            execution_profile_id="codex_current",
            execution_interface="TOPIC_BELONGING_TERMINAL",
            path="handoff/",
        )


def test_product_authorization_does_not_cross_capability_scopes(tmp_path: Path) -> None:
    root, registry = _product_root(tmp_path)
    _write_product_registry(root, registry)
    with pytest.raises(ProductAuthorizationError, match="PRODUCT_AUTHORIZATION_DENY"):
        resolve_product_authorization(
            root,
            capability_id="EXTEND_01_RESEARCH_V2_REAL_E2E",
            role_id="CHANNEL_INTELLIGENCE_REVIEWER",
            execution_family="AGENT_HARNESS",
            execution_route="agent_harness",
            execution_profile_id="EXECUTOR_MANAGED",
            execution_interface="TOPIC_BELONGING_TERMINAL",
            path="handoff/",
        )


def test_product_authorization_rejects_path_traversal_before_scope_filter(tmp_path: Path) -> None:
    root, registry = _product_root(tmp_path)
    _write_product_registry(root, registry)
    with pytest.raises(ProductAuthorizationError, match="PRODUCT_AUTHORIZATION_PATH_OUTSIDE_REPOSITORY"):
        resolve_product_authorization(
            root,
            capability_id="TOPIC_BELONGING_ASSESSMENT",
            role_id="CHANNEL_INTELLIGENCE_REVIEWER",
            execution_family="AGENT_HARNESS",
            execution_route="agent_harness",
            execution_profile_id="EXECUTOR_MANAGED",
            execution_interface="TOPIC_BELONGING_TERMINAL",
            path="handoff/../../outside.txt",
        )


@pytest.mark.parametrize("path", ["handoff/", "./handoff", "handoff\\"])
def test_product_authorization_accepts_normalized_in_scope_paths(tmp_path: Path, path: str) -> None:
    root, registry = _product_root(tmp_path)
    (root / "handoff").mkdir(parents=True, exist_ok=True)
    _write_product_registry(root, registry)
    authorization, _ = resolve_product_authorization(
        root,
        capability_id="TOPIC_BELONGING_ASSESSMENT",
        role_id="CHANNEL_INTELLIGENCE_REVIEWER",
        execution_family="AGENT_HARNESS",
        execution_route="agent_harness",
        execution_profile_id="EXECUTOR_MANAGED",
        execution_interface="TOPIC_BELONGING_TERMINAL",
        path=path,
    )
    assert authorization.authorization_id == "PCA-PLAN015-TOPIC-001"


def test_product_authorization_rejects_physical_symlink_or_junction_escape(tmp_path: Path) -> None:
    root, registry = _product_root(tmp_path)
    handoff = root / "handoff"
    handoff.mkdir(parents=True, exist_ok=True)
    outside = tmp_path / "outside-repository"
    outside.mkdir()
    link = handoff / "escaped"
    try:
        os.symlink(outside, link, target_is_directory=True)
    except (OSError, NotImplementedError):
        # Directory junctions do not require the SeCreateSymbolicLinkPrivilege
        # on the Windows configurations used by the project.
        result = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(outside)],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0 or not link.exists():
            pytest.skip("Windows session cannot create a symlink or junction for physical containment proof")
    _write_product_registry(root, registry)
    with pytest.raises(ProductAuthorizationError, match="PRODUCT_AUTHORIZATION_PATH_OUTSIDE_REPOSITORY"):
        resolve_product_authorization(
            root,
            capability_id="TOPIC_BELONGING_ASSESSMENT",
            role_id="CHANNEL_INTELLIGENCE_REVIEWER",
            execution_family="AGENT_HARNESS",
            execution_route="agent_harness",
            execution_profile_id="EXECUTOR_MANAGED",
            execution_interface="TOPIC_BELONGING_TERMINAL",
            path="handoff/escaped/",
        )


def test_product_authority_uses_neutral_scope_and_context_manifest_has_no_mission_id(
) -> None:
    request = SimpleNamespace(
        capability_id="TOPIC_BELONGING_ASSESSMENT",
        role="CHANNEL_INTELLIGENCE_REVIEWER",
        provider=None,
        execution_mode="SYNTHETIC_TEST",
        execution_route="agent_harness",
        execution_profile=None,
        execution_family="AGENT_HARNESS",
        config={
            "authorization_mode": "PRODUCT",
            "execution_interface": "TOPIC_BELONGING_TERMINAL",
            "context_references": [],
        },
    )
    result = execution_preflight.preflight_controlled_execution(request, root=ROOT)
    assert result["authorization"].mission_id is None
    assert result["authorization"].authorization_id == "PCA-PLAN015-TOPIC-001"
    assert "mission_id" not in result["context_manifest"]


def test_revoked_product_authorization_is_not_effective(tmp_path: Path) -> None:
    root, registry = _product_root(tmp_path)
    authorization = registry["authorizations"][0]
    authorization.update(
        {
            "status": "REVOKED",
            "revoked_at": "2026-09-18T00:00:00Z",
            "revoked_by": "OWNER",
            "revocation_reason": "fixture revocation",
        }
    )
    authorization["authorization_checksum"] = authorization_checksum(authorization)
    _write_product_registry(root, registry)
    with pytest.raises(ProductAuthorizationError, match="PRODUCT_AUTHORIZATION_DENY"):
        _resolve_topic_product(root)


def _controlled_scope(data: dict) -> dict:
    auth = data["authorization"]
    payload = {
        "mission_id": data["mission_id"],
        "capability_ids": auth["capability_ids"],
        "role_ids": auth["role_ids"],
        "execution_profile_ids": auth.get("execution_profile_ids", []),
        "execution_interface": auth["execution_interface"],
        "allowed_operations": auth["allowed_operations"],
        "allowed_paths": auth["allowed_paths"],
        "allowed_routes": auth["allowed_routes"],
        "execution_mode": auth["execution_mode"],
        "live_state_sha256": auth["live_state_sha256"],
        "contains_material_repair": auth["contains_material_repair"],
        "repair_integrity_evidence_path": auth["repair_integrity_evidence_path"],
        "execution_family_ids": auth["execution_family_ids"],
        "controlled_validation": True,
        "controlled_validation_state_requirements": auth[
            "controlled_validation_state_requirements"
        ],
    }
    return payload


def _controlled_root(tmp_path: Path, *, state_change: tuple[str, str] | None = None) -> Path:
    root = tmp_path / "controlled-authority"
    for relative in (
        "plans/001_CONTROL_OPERATIVO.md",
        "plans/plan_015/PLAN015_controlled_validation_authorization.json",
        "plans/plan_015/PLAN015_controlled_validation_authority.json",
        "plans/plan_015/PLAN015_controlled_validation_mission_contract.json",
    ):
        source = ROOT / relative
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    if state_change:
        state_path = root / "plans/001_CONTROL_OPERATIVO.md"
        state_path.write_text(
            state_path.read_text(encoding="utf-8").replace(*state_change), encoding="utf-8"
        )
    authorization_path = root / "plans/plan_015/PLAN015_controlled_validation_authorization.json"
    authority_path = root / "plans/plan_015/PLAN015_controlled_validation_authority.json"
    authorization = json.loads(authorization_path.read_text(encoding="utf-8"))
    authorization["authorization"]["live_state_sha256"] = hashlib.sha256(
        (root / "plans/001_CONTROL_OPERATIVO.md").read_bytes()
    ).hexdigest()
    scope = _controlled_scope(authorization)
    authorization["authorization"]["authorized_scope_sha256"] = scope_checksum(scope)
    authority = json.loads(authority_path.read_text(encoding="utf-8"))
    authority["authorized_scope_sha256"] = scope_checksum(scope)
    authority_path.write_text(json.dumps(authority, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    authorization["authorization"]["authority_sha256"] = hashlib.sha256(authority_path.read_bytes()).hexdigest()
    authorization_path.write_text(json.dumps(authorization, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return root


def _verify_controlled_authorization(root: Path) -> None:
    authorization = load_mission_authorization(
        root / "plans/plan_015/PLAN015_controlled_validation_authorization.json"
    )
    authorization.verify_controlled_validation_contract(
        load_mission_contract(
            root / "plans/plan_015/PLAN015_controlled_validation_mission_contract.json"
        )
    )
    authorization.verify(
        root,
        capability_id="EXTEND_01_RESEARCH_V2_REAL_E2E",
        role_id="RESEARCH_AND_CURATION",
        operation="VALIDATE_OPERATIONAL_ENTRYPOINT",
        path="handoff/",
        execution_mode="REAL",
        execution_route="agent_harness",
        execution_family="AGENT_HARNESS",
        execution_interface="PLAN015_CONTROLLED_VALIDATION",
    )


def test_controlled_validation_permitted_state_passes(tmp_path: Path) -> None:
    _verify_controlled_authorization(_controlled_root(tmp_path))


@pytest.mark.parametrize(
    "state_change, expected",
    [
        (("REAL_AI_EXECUTION: NO", "REAL_AI_EXECUTION: YES"), "REAL_AI_EXECUTION"),
        (("PRODUCT_USE_AUTHORIZED: NO", "PRODUCT_USE_AUTHORIZED: YES"), "PRODUCT_USE_AUTHORIZED"),
    ],
)
def test_controlled_validation_rejects_forbidden_regenerated_state(
    tmp_path: Path,
    state_change: tuple[str, str],
    expected: str,
) -> None:
    root = _controlled_root(tmp_path, state_change=state_change)
    with pytest.raises(MissionAuthorizationError, match=expected):
        _verify_controlled_authorization(root)


def test_unknown_authorization_mode_is_blocked_before_active_legacy_fallback(tmp_path: Path) -> None:
    request = SimpleNamespace(
        capability_id="CAP",
        role="ROLE",
        execution_mode="REAL",
        execution_route="route",
        execution_profile=None,
        output_artifact_path=None,
        config={"authorization_mode": "TYPO"},
    )
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(
            execution_preflight,
            "_load_registered_capability",
            lambda *_: {"availability_status": "ACTIVE", "assigned_role": ["ROLE"]},
        )
        with pytest.raises(PermissionError, match="AUTHORIZATION_MODE_INVALID:TYPO"):
            execution_preflight.preflight_controlled_execution(request, root=tmp_path)


def test_unknown_authorization_mode_is_blocked_at_all_agent_handoff_boundaries(tmp_path: Path) -> None:
    request = SimpleNamespace(
        execution_mode="REAL",
        execution_family="AGENT_HARNESS",
        execution_route="agent_harness",
        provider=None,
        model=None,
        executor=None,
        execution_profile=None,
        run_configuration=None,
        capability_id="CAP",
        role="ROLE",
        config={"authorization_mode": "TYPO"},
    )
    with pytest.raises(PermissionError, match="AUTHORIZATION_MODE_INVALID:TYPO"):
        AgentHandoffProvider._verify_pre_handoff_authorization(request, tmp_path, tmp_path)
    with pytest.raises(PermissionError, match="AUTHORIZATION_MODE_INVALID:TYPO"):
        AgentHandoffProvider._verify_external_preparation_authorization(request, tmp_path, tmp_path)
    with pytest.raises(PermissionError, match="AUTHORIZATION_MODE_INVALID:TYPO"):
        AgentHandoffProvider._verify_import_authorization({"authorization_mode": "TYPO"})


def test_research_preparation_does_not_report_requested_product_mode_as_authorization() -> None:
    preparation = RealResearchRoutePreparation.from_mapping(
        {
            "episode_id": "ep_0003",
            "topic": "Tema",
            "budget_limit": 1,
            "max_iterations": 1,
            "max_retries": 0,
            "timeout_seconds": 1,
            "authorization_mode": "PRODUCT",
        }
    )
    assert preparation.to_dict()["authorized_for_product_use"] is False


def test_product_preflight_rejects_managed_executor_provider(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request = SimpleNamespace(
        capability_id="CAP",
        role="ROLE",
        provider="agent_executor",
        execution_mode="REAL",
        execution_route="agent_harness",
        execution_profile=None,
        execution_family="AGENT_HARNESS",
        output_artifact_path=None,
        config={
            "authorization_mode": "PRODUCT",
            "execution_family": "AGENT_HARNESS",
            "execution_route": "agent_harness",
        },
    )
    monkeypatch.setattr(
        execution_preflight,
        "_load_registered_capability",
        lambda *_: {"availability_status": "READY_NOT_AUTHORIZED"},
    )

    with pytest.raises(PermissionError, match="PRODUCT_AUTHORIZATION_REQUIRES_NEUTRAL_AGENT_HANDOFF"):
        execution_preflight.preflight_controlled_execution(request, root=tmp_path)


def test_product_execution_without_provider_is_normalized_to_neutral_handoff(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request = ExecutionRequest(
        capability_id="CAP",
        skill_id="skill",
        skill_version="1.0.0",
        input_artifacts=[],
        output_schema="output",
        execution_mode="REAL",
        execution_family="AGENT_HARNESS",
        execution_route="agent_harness",
        config={"authorization_mode": "PRODUCT", "repository_root": str(tmp_path)},
    )
    observed: dict[str, str | None] = {}

    monkeypatch.setattr(
        ai_execution,
        "preflight_controlled_execution",
        lambda *_args, **_kwargs: {"authorization": object(), "context_manifest": None},
    )

    def fake_prepare_external(_provider, current_request, _manifest, _run_id):
        observed["provider"] = current_request.provider
        return tmp_path / "handoff.json"

    monkeypatch.setattr(ai_execution.AgentHandoffProvider, "prepare_external", fake_prepare_external)
    result = ai_execution._execute_unfinalized(request)

    assert result.status.value == "HANDOFF_PREPARED"
    assert observed["provider"] == "agent_handoff"
