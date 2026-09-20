from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.ai import execution as ai_execution
from src.ai.contracts import ExecutionRequest
from src.core import execution_preflight
from src.core.product_authorization import ProductAuthorizationError, authorization_checksum, resolve_product_authorization


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
