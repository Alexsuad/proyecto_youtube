from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from src.ai.contracts import ExecutionRequest, ExecutionResult, ExecutionStatus, InputArtifact
from src.ai.execution import execute, manifest_checksum
from src.ai.manifest import manifest_checksum as shared_manifest_checksum
from src.ai.providers.agent_handoff import AgentHandoffProvider
from src.ai.providers.openai_compatible import OpenAICompatibleProvider
from src.ai.registry import append_result
from src.ai.router import resolve_provider
from src.scripts.run_b5_i2_semantic_audit import build_editorial_prompt, execute_b5_i2_audit, import_b5_i2_handoff
import src.scripts.run_b5_i2_semantic_audit as audit_runner


def _checksum(value: object) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _audit() -> dict:
    criteria = [
        "ANALYSIS_SPECIFICITY", "MATERIAL_ANALYSIS_COVERAGE", "RIVAL_INTERPRETATION_AND_LIMITS",
        "INHERITED_RESTRICTION_PROPAGATION", "CURATION_COMPLETENESS", "CURATION_CONTRAST_AND_PROGRESSION",
        "THESIS_REFINEMENT_SUBSTANCE", "EVIDENCE_TRACEABILITY", "SCRIPT_PROMISE_HONESTY",
    ]
    critical = {"ANALYSIS_SPECIFICITY", "CURATION_CONTRAST_AND_PROGRESSION", "THESIS_REFINEMENT_SUBSTANCE"}
    anchored = {"artifact_kind": "analysis", "artifact_id": "A-1", "artifact_field": "summary", "evaluated_excerpt": "texto", "evidence_refs": ["F-1"], "evidence_excerpts": [{"evidence_ref": "F-1", "excerpt": "texto"}], "editorial_comparison": "comparación", "why_specific_or_generic": "es específico", "decision": "SATISFIED"}
    return {
        "audit_id": "B5I2-SSA-1", "episode_id": "EP-1", "auditor_role": "INDEPENDENT_EDITORIAL_AUDITOR",
        "auditor_run_id": "RUN-AUDIT", "auditor_skill_id": "skill_qa_editorial", "auditor_skill_version": "2.0.0",
        "provider_or_adapter": "mock", "model_or_evaluator": "test", "execution_timestamp": "2026-07-25T08:00:00Z",
        "input_manifest_checksum": "a" * 64,
        "artifact_checksums": [{"artifact_kind": kind, "artifact_id": artifact_id, "checksum": "a" * 64, "producer_run_id": "RUN-P"} for kind, artifact_id in [("research", "R-1"), ("evidence_report", "E-1"), ("provisional_thesis", "TP-1"), ("analysis", "A-1"), ("curation", "C-1"), ("thesis", "T-1"), ("script_promise", "SP-1")]],
        "audit_method": "AI_SEMANTIC_REVIEW",
        "findings": [{"criterion": criterion, "status": "SATISFIED", "anchored_findings": [anchored] if criterion in critical else [], "rationale": "hallazgo trazable"} for criterion in criteria],
        "decision": "PASS", "created_at": "2026-07-25T08:00:00Z",
    }


def _request(tmp_path: Path, **overrides) -> ExecutionRequest:
    source = tmp_path / "analysis.json"
    source.write_text('{"analysis_id":"A-1"}', encoding="utf-8")
    kwargs = {"capability_id": "editorial_semantic_audit_b5_i2", "skill_id": "skill_qa_editorial", "skill_version": "2.0.0", "input_artifacts": [InputArtifact("analysis", "A-1", source, "RUN-P")], "output_schema": "b5_i2_semantic_sufficiency_audit", "execution_mode": "mock", "provider": "mock", "mock_output": _audit(), "output_artifact_id": "B5I2-SSA-1"}
    kwargs.update(overrides)
    return ExecutionRequest(**kwargs)


def _four_artifacts(tmp_path: Path) -> list[InputArtifact]:
    rows = [("research", "R-1"), ("evidence_report", "E-1"), ("provisional_thesis", "TP-1"), ("analysis", "A-1"), ("curation", "C-1"), ("thesis", "T-1"), ("script_promise", "SP-1")]
    return [InputArtifact(kind, artifact_id, _write_artifact(tmp_path, f"{kind}.json", artifact_id), "RUN-P") for kind, artifact_id in rows]


def _write_artifact(root: Path, name: str, artifact_id: str) -> Path:
    path = root / name
    path.write_text(json.dumps({"id": artifact_id, "content": "contenido editorial concreto"}), encoding="utf-8")
    return path


def test_mock_produces_structurally_valid_output_but_is_not_real_editorial(tmp_path: Path) -> None:
    result = execute(_request(tmp_path))
    assert result.status is ExecutionStatus.SUCCEEDED
    assert result.output["audit_id"] == _audit()["audit_id"]
    assert "auditor_run_id" not in result.output
    assert not result.is_real_editorial_execution


def test_unknown_provider_fails(tmp_path: Path) -> None:
    result = execute(_request(tmp_path, provider="unknown", execution_mode="custom"))
    assert result.status is ExecutionStatus.FAILED


def test_api_without_key_blocks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AI_API_KEY", raising=False)
    result = execute(_request(tmp_path, provider="openai_compatible", execution_mode="api"))
    assert result.status is ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR


def test_local_unavailable_blocks(tmp_path: Path) -> None:
    result = execute(_request(tmp_path, provider="ollama", execution_mode="local", model="local", timeout=0.01, config={"base_url": "http://127.0.0.1:1"}))
    assert result.status is ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR


def test_agent_handoff_package_is_importable_and_rejects_bad_checksum(tmp_path: Path) -> None:
    request = _request(tmp_path, provider="agent_handoff", execution_mode="agent_handoff", handoff_directory=tmp_path / "handoff")
    result = execute(request)
    assert result.status is ExecutionStatus.HANDOFF_PREPARED
    package = Path(result.usage["package"])
    imported = tmp_path / "result.json"
    package_data = json.loads(package.read_text(encoding="utf-8"))
    payload = {"handoff_id": result.run_id, "package_checksum": package_data["package_checksum"], "skill_id": "skill_qa_editorial", "skill_version": "2.0.0", "input_manifest_checksum": result.input_manifest_checksum, "output": _audit()}
    payload["output_checksum"] = _checksum(payload["output"])
    imported.write_text(json.dumps(payload), encoding="utf-8")
    assert AgentHandoffProvider().import_result(package, imported) == _audit()
    payload["output_checksum"] = "b" * 64
    imported.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="checksum incorrecto"):
        AgentHandoffProvider().import_result(package, imported)


def test_explicit_routing_is_respected_and_auto_never_falls_back_to_external_api(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    assert resolve_provider(_request(tmp_path, execution_mode="mock", provider="mock")) == "mock"
    monkeypatch.delenv("AI_API_KEY", raising=False)
    monkeypatch.delenv("AI_BASE_URL", raising=False)
    assert resolve_provider(_request(tmp_path, execution_mode="auto", provider=None, config={"local_available": False})) is None


def test_real_run_is_recorded_in_canonical_provenance(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AI_API_KEY", "test-key")
    monkeypatch.setenv("AI_BASE_URL", "https://provider.invalid")
    monkeypatch.setattr(OpenAICompatibleProvider, "execute", lambda self, request: (_audit(), {"provider_test_double": True}))
    policy = tmp_path / "routing.yaml"
    policy.write_text("capabilities:\n  editorial_semantic_audit_b5_i2:\n    routing:\n      allow_external_api: true\n", encoding="utf-8")
    result = execute(_request(tmp_path, provider="openai_compatible", execution_mode="api", model="semantic-test", config={"routing_policy_path": policy}))
    assert result.is_real_editorial_execution
    registry = tmp_path / "execution_registry.json"
    append_result(registry, result, execution_mode="REAL")
    saved = json.loads(registry.read_text(encoding="utf-8"))
    assert saved["runs"][0]["run_id"] == result.run_id


def test_mock_b5_i2_flow_remains_blocked_for_editorial_decision(tmp_path: Path) -> None:
    result = execute_b5_i2_audit(
        artifacts=_four_artifacts(tmp_path),
        output_path=tmp_path / "audit.json",
        registry_path=tmp_path / "execution_registry.json",
        provider="mock",
        execution_mode="mock",
        mock_output=_audit(),
    )
    assert result.status is ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR


def test_runner_rejects_audit_without_original_b5_i1_evidence(tmp_path: Path) -> None:
    request = _request(tmp_path)
    result = execute_b5_i2_audit(
        artifacts=request.input_artifacts,
        output_path=tmp_path / "audit.json",
        registry_path=tmp_path / "execution_registry.json",
        provider="mock",
        execution_mode="mock",
        mock_output=_audit(),
    )
    assert result.status is ExecutionStatus.FAILED
    assert "research" in (result.error or "")


def test_runner_builds_nonempty_editorial_prompt_and_imposes_runtime_provenance(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    artifacts = _four_artifacts(tmp_path)
    policy = tmp_path / "routing.yaml"
    policy.write_text("capabilities:\n  editorial_semantic_audit_b5_i2:\n    routing:\n      allow_external_api: true\n", encoding="utf-8")
    captured: dict[str, object] = {}
    def provider(self, request):
        captured["prompt"] = request.config["prompt"]
        payload = _audit()
        payload.update({"auditor_run_id": "FORGED", "provider_or_adapter": "forged", "model_or_evaluator": "forged", "input_manifest_checksum": "b" * 64})
        return payload, {"provider_or_adapter": "openai_compatible", "model_or_evaluator": "actual-semantic-model"}
    monkeypatch.setattr(OpenAICompatibleProvider, "execute", provider)
    result = execute_b5_i2_audit(artifacts=artifacts, output_path=tmp_path / "audit.json", registry_path=tmp_path / "registry.json", episode_id="EP-1", provider="openai_compatible", execution_mode="api", model="ignored", config={"routing_policy_path": policy})
    prompt = str(captured["prompt"])
    assert all(token in prompt for token in ("skill_qa_editorial@2.0.0", "ANALYSIS_SPECIFICITY", "CURATION_CONTRAST_AND_PROGRESSION", "THESIS_REFINEMENT_SUBSTANCE", "Artefactos reales", "schema estructural"))
    assert result.status is ExecutionStatus.SUCCEEDED
    assert result.output["auditor_run_id"] == result.run_id
    assert result.output["model_or_evaluator"] == "actual-semantic-model"
    assert result.output["input_manifest_checksum"] == manifest_checksum(ExecutionRequest("x", "x", "x", artifacts, "x", episode_id="EP-1"))
    saved = json.loads((tmp_path / "registry.json").read_text(encoding="utf-8"))
    assert saved["runs"][0]["outputs"][0]["checksum"] == _checksum(result.output) or saved["runs"][0]["outputs"][0]["checksum"] == result.output_checksum


def test_shared_manifest_matches_gate_representation(tmp_path: Path) -> None:
    artifacts = _four_artifacts(tmp_path)
    request = ExecutionRequest("editorial_semantic_audit_b5_i2", "skill_qa_editorial", "2.0.0", artifacts, "b5_i2_semantic_sufficiency_audit", episode_id="EP-1")
    rows = [{"artifact_kind": item.artifact_kind, "artifact_id": item.artifact_id, "checksum": hashlib.sha256(item.path.read_bytes()).hexdigest()} for item in artifacts]
    assert manifest_checksum(request) == shared_manifest_checksum("EP-1", rows)


def test_auto_and_api_do_not_authorize_external_use_from_environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AI_API_KEY", "present-but-not-authorized")
    monkeypatch.setenv("AI_BASE_URL", "https://provider.invalid")
    request = _request(tmp_path, provider=None, execution_mode="auto", config={"local_available": False})
    assert execute(request).status is ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR
    request = _request(tmp_path, provider="openai_compatible", execution_mode="api")
    assert execute(request).status is ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR


def test_handoff_import_rejects_foreign_package_and_persists_valid_result(tmp_path: Path) -> None:
    artifacts = _four_artifacts(tmp_path)
    request = ExecutionRequest("editorial_semantic_audit_b5_i2", "skill_qa_editorial", "2.0.0", artifacts, "b5_i2_semantic_sufficiency_audit", execution_mode="agent", provider="agent_handoff", output_artifact_id="B5I2-SSA-1", handoff_directory=tmp_path / "handoff", episode_id="EP-1", config={"prompt": "instrucciones editoriales", "execution_registry_path": str(tmp_path / "registry.json")})
    prepared = execute(request)
    package = Path(prepared.usage["package"])
    data = json.loads(package.read_text(encoding="utf-8"))
    imported = tmp_path / "import.json"
    payload = {"handoff_id": prepared.run_id, "package_checksum": data["package_checksum"], "skill_id": "skill_qa_editorial", "skill_version": "2.0.0", "input_manifest_checksum": prepared.input_manifest_checksum, "output": _audit()}
    payload["output_checksum"] = _checksum(payload["output"])
    imported.write_text(json.dumps(payload), encoding="utf-8")
    result = import_b5_i2_handoff(package_path=package, result_path=imported, artifacts=artifacts, output_path=tmp_path / "audit.json", registry_path=tmp_path / "registry.json", episode_id="EP-1")
    assert result.status is ExecutionStatus.SUCCEEDED
    payload["package_checksum"] = "0" * 64; imported.write_text(json.dumps(payload), encoding="utf-8")
    rejected = import_b5_i2_handoff(package_path=package, result_path=imported, artifacts=artifacts, output_path=tmp_path / "audit-2.json", registry_path=tmp_path / "registry-2.json", episode_id="EP-1")
    assert rejected.status is ExecutionStatus.FAILED


def test_registry_failure_does_not_leave_orphan_audit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    output, registry = tmp_path / "audit.json", tmp_path / "registry.json"
    output.write_text('{"previous":true}\n', encoding="utf-8")
    result = ExecutionResult("RUN-AI-atomic", ExecutionStatus.SUCCEEDED, "provider", "ollama", "editorial-local", "a" * 64, _audit(), "b" * 64, "2026-07-25T08:00:00Z", "2026-07-25T08:01:00Z", usage={"skill_id": "skill_qa_editorial", "skill_version": "2.0.0"}, output_artifact_id="B5I2-SSA-1", is_real_editorial_execution=True)
    original_replace = audit_runner.os.replace
    def fail_registry(source, destination):
        if Path(destination) == registry:
            raise OSError("simulated registry failure")
        return original_replace(source, destination)
    monkeypatch.setattr(audit_runner.os, "replace", fail_registry)
    with pytest.raises(OSError, match="simulated registry failure"):
        audit_runner._atomic_persist(output, registry, _audit(), result)
    assert output.read_text(encoding="utf-8") == '{"previous":true}\n'
    assert not registry.exists()


def test_provider_may_return_editorial_fields_only(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    artifacts = _four_artifacts(tmp_path)
    policy = tmp_path / "routing.yaml"
    policy.write_text("capabilities:\n  editorial_semantic_audit_b5_i2:\n    routing:\n      allow_external_api: true\n", encoding="utf-8")
    editorial = {"audit_id": "B5I2-SSA-1", "findings": _audit()["findings"], "decision": "PASS"}
    monkeypatch.setattr(OpenAICompatibleProvider, "execute", lambda self, request: (editorial, {"provider_or_adapter": "openai_compatible", "model_or_evaluator": "model-real"}))
    result = execute_b5_i2_audit(artifacts=artifacts, output_path=tmp_path / "audit.json", registry_path=tmp_path / "registry.json", episode_id="EP-1", provider="openai_compatible", execution_mode="api", config={"routing_policy_path": policy})
    assert result.status is ExecutionStatus.SUCCEEDED
    assert result.output["auditor_run_id"] == result.run_id


def test_fabricated_self_consistent_handoff_without_registry_is_rejected(tmp_path: Path) -> None:
    artifacts = _four_artifacts(tmp_path)
    request = ExecutionRequest("editorial_semantic_audit_b5_i2", "skill_qa_editorial", "2.0.0", artifacts, "b5_i2_semantic_sufficiency_audit", execution_mode="agent", provider="agent_handoff", output_artifact_id="B5I2-SSA-1", handoff_directory=tmp_path / "handoff", episode_id="EP-1", config={"prompt": "prompt"})
    prepared = execute(request)
    package = Path(prepared.usage["package"])
    registry = tmp_path / "missing-registry.json"
    payload = json.loads(package.read_text(encoding="utf-8"))
    result_file = tmp_path / "result.json"
    result_payload = {"handoff_id": prepared.run_id, "package_checksum": payload["package_checksum"], "skill_id": payload["skill_id"], "skill_version": payload["skill_version"], "input_manifest_checksum": payload["input_manifest_checksum"], "output": _audit()}
    result_payload["output_checksum"] = _checksum(result_payload["output"])
    result_file.write_text(json.dumps(result_payload), encoding="utf-8")
    rejected = import_b5_i2_handoff(package_path=package, result_path=result_file, artifacts=artifacts, output_path=tmp_path / "audit.json", registry_path=registry, episode_id="EP-1")
    assert rejected.status is ExecutionStatus.FAILED
    assert "inexistente" in (rejected.error or "")


def test_modified_package_with_recalculated_checksum_is_rejected_against_registry(tmp_path: Path) -> None:
    registry = tmp_path / "registry.json"
    artifacts = _four_artifacts(tmp_path)
    request = ExecutionRequest("editorial_semantic_audit_b5_i2", "skill_qa_editorial", "2.0.0", artifacts, "b5_i2_semantic_sufficiency_audit", execution_mode="agent", provider="agent_handoff", output_artifact_id="B5I2-SSA-1", handoff_directory=tmp_path / "handoff", episode_id="EP-1", config={"prompt": "prompt", "execution_registry_path": str(registry)})
    prepared = execute(request); package = Path(prepared.usage["package"])
    package_data = json.loads(package.read_text(encoding="utf-8")); package_data["prompt"] = "altered"; package_data["package_checksum"] = _checksum({key: value for key, value in package_data.items() if key != "package_checksum"}); package.write_text(json.dumps(package_data), encoding="utf-8")
    result_file = tmp_path / "result.json"; payload = {"handoff_id": prepared.run_id, "package_checksum": package_data["package_checksum"], "skill_id": package_data["skill_id"], "skill_version": package_data["skill_version"], "input_manifest_checksum": package_data["input_manifest_checksum"], "output": _audit()}; payload["output_checksum"] = _checksum(payload["output"]); result_file.write_text(json.dumps(payload), encoding="utf-8")
    rejected = import_b5_i2_handoff(package_path=package, result_path=result_file, artifacts=artifacts, output_path=tmp_path / "audit.json", registry_path=registry, episode_id="EP-1")
    assert rejected.status is ExecutionStatus.FAILED
    assert "package_checksum" in (rejected.error or "")


def test_handoff_cannot_be_consumed_twice(tmp_path: Path) -> None:
    registry = tmp_path / "registry.json"; artifacts = _four_artifacts(tmp_path)
    request = ExecutionRequest("editorial_semantic_audit_b5_i2", "skill_qa_editorial", "2.0.0", artifacts, "b5_i2_semantic_sufficiency_audit", execution_mode="agent", provider="agent_handoff", output_artifact_id="B5I2-SSA-1", handoff_directory=tmp_path / "handoff", episode_id="EP-1", config={"prompt": "prompt", "execution_registry_path": str(registry)})
    prepared = execute(request); package = Path(prepared.usage["package"]); data = json.loads(package.read_text(encoding="utf-8")); result_file = tmp_path / "result.json"; payload = {"handoff_id": prepared.run_id, "package_checksum": data["package_checksum"], "skill_id": data["skill_id"], "skill_version": data["skill_version"], "input_manifest_checksum": data["input_manifest_checksum"], "output": _audit()}; payload["output_checksum"] = _checksum(payload["output"]); result_file.write_text(json.dumps(payload), encoding="utf-8")
    first = import_b5_i2_handoff(package_path=package, result_path=result_file, artifacts=artifacts, output_path=tmp_path / "audit.json", registry_path=registry, episode_id="EP-1")
    second = import_b5_i2_handoff(package_path=package, result_path=result_file, artifacts=artifacts, output_path=tmp_path / "audit2.json", registry_path=registry, episode_id="EP-1")
    assert first.status is ExecutionStatus.SUCCEEDED and second.status is ExecutionStatus.FAILED


def _registered_handoff_fixture(tmp_path: Path):
    registry = tmp_path / "registry.json"; artifacts = _four_artifacts(tmp_path)
    request = ExecutionRequest("editorial_semantic_audit_b5_i2", "skill_qa_editorial", "2.0.0", artifacts, "b5_i2_semantic_sufficiency_audit", execution_mode="agent", provider="agent_handoff", output_artifact_id="B5I2-SSA-1", handoff_directory=tmp_path / "handoff", episode_id="EP-1", config={"prompt": "prompt", "execution_registry_path": str(registry)})
    prepared = execute(request); package = Path(prepared.usage["package"]); data = json.loads(package.read_text(encoding="utf-8")); result_file = tmp_path / "result.json"; payload = {"handoff_id": prepared.run_id, "package_checksum": data["package_checksum"], "skill_id": data["skill_id"], "skill_version": data["skill_version"], "input_manifest_checksum": data["input_manifest_checksum"], "output": _audit()}; payload["output_checksum"] = _checksum(payload["output"]); result_file.write_text(json.dumps(payload), encoding="utf-8")
    return package, result_file, artifacts, registry


def test_skill_changed_after_prepare_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    package, result_file, artifacts, registry = _registered_handoff_fixture(tmp_path)
    monkeypatch.setattr(audit_runner, "skill_checksum", lambda: "f" * 64)
    rejected = import_b5_i2_handoff(package_path=package, result_path=result_file, artifacts=artifacts, output_path=tmp_path / "audit.json", registry_path=registry, episode_id="EP-1")
    assert rejected.status is ExecutionStatus.FAILED and "skill_checksum" in (rejected.error or "")


def test_persistence_failure_does_not_mark_handoff_consumed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    package, result_file, artifacts, registry = _registered_handoff_fixture(tmp_path)
    monkeypatch.setattr(audit_runner, "_atomic_persist", lambda *args, **kwargs: (_ for _ in ()).throw(OSError("persist failed")))
    rejected = import_b5_i2_handoff(package_path=package, result_path=result_file, artifacts=artifacts, output_path=tmp_path / "audit.json", registry_path=registry, episode_id="EP-1")
    assert rejected.status is ExecutionStatus.FAILED
    saved = json.loads(registry.read_text(encoding="utf-8"))
    assert saved["handoffs"][0]["status"] == "HANDOFF_PREPARED"


def test_auto_explicit_openai_provider_requires_authorization(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AI_API_KEY", "present"); monkeypatch.setenv("AI_BASE_URL", "https://provider.invalid")
    result = execute(_request(tmp_path, provider="openai_compatible", execution_mode="auto", config={"local_available": False}))
    assert result.status is ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR
