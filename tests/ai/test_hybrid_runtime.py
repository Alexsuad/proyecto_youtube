from __future__ import annotations

import copy
import hashlib
import json
import sys
import subprocess
from pathlib import Path

import pytest

from src.ai.contracts import ExecutionRequest, ExecutionResult, ExecutionStatus, InputArtifact
from src.ai.execution import execute, manifest_checksum, persist_execution_result
from src.ai.manifest import manifest_checksum as shared_manifest_checksum
from src.ai.providers.agent_handoff import AgentHandoffProvider
from src.ai.runtime_profiles import READY, ResolvedExecutionRoute
from src.ai.providers.deepseek import DeepSeekProvider
from src.ai.providers.openai_compatible import OpenAICompatibleProvider
from src.ai.registry import append_result
from src.ai.router import resolve_provider
from src.core.mission_completion_gate import load_mission_contract, run_mission_completion_gate
from src.scripts.run_b5_i2_semantic_audit import build_editorial_prompt, execute_b5_i2_audit, import_b5_i2_handoff
import src.scripts.run_b5_i2_semantic_audit as audit_runner
from tests.core.test_all_schemas import VALID_FIXTURES
from tests.core.test_plan_005_real_consumer_integration import _setup as setup_governed_repo


CAPABILITY = "B5_I2_SEMANTIC_AUDITOR"
SKILL_ID = "skill_auditar_suficiencia_semantica_b5_i2"
SKILL_VERSION = "1.0.0"
AUDITOR_ROLE = "SCRIPT_PRODUCT_AUDITOR"
PRODUCER_CASES = [
    ("ANALYSIS_PRODUCER", "analysis", "narrative_human_analysis"),
    ("CURATION_PRODUCER", "curation", "material_curation"),
    ("THESIS_PRODUCER", "refined_thesis", "refined_thesis"),
    ("SCRIPT_PROMISE_PRODUCER", "script_promise", "editorial_script_promise"),
    ("SCRIPT_PRODUCT_PRODUCER", "claims_ledger", "claims_ledger"),
    ("SCRIPT_PRODUCT_PRODUCER", "work_lifecycle", "work_lifecycle"),
    ("SCRIPT_PRODUCT_PRODUCER", "work_research_dossier", "work_research_dossier"),
]


def _checksum(value: object) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _audit() -> dict:
    criteria = [
        "ANALYSIS_SPECIFICITY", "EVIDENCE_TRACEABILITY", "EPISTEMIC_SEPARATION", "EDITORIAL_DEPTH_AND_UTILITY",
        "MATERIAL_COVERAGE", "CURATION_FUNCTION", "CURATION_CONTRAST_AND_PROGRESSION", "REDUNDANCY_AND_CONTEXT_COST",
        "THESIS_REFINEMENT_SUBSTANCE", "THESIS_ARGUMENTATIVE_QUALITY", "MATERIAL_THESIS_CONTRIBUTION",
        "INHERITED_RESTRICTIONS", "SCRIPT_PROMISE_HONESTY", "EARLY_PACKAGING_HONESTY", "B5_I3_READINESS",
    ]
    critical = {"ANALYSIS_SPECIFICITY", "EVIDENCE_TRACEABILITY", "EPISTEMIC_SEPARATION", "MATERIAL_COVERAGE", "CURATION_FUNCTION", "CURATION_CONTRAST_AND_PROGRESSION", "THESIS_REFINEMENT_SUBSTANCE", "THESIS_ARGUMENTATIVE_QUALITY", "MATERIAL_THESIS_CONTRIBUTION", "INHERITED_RESTRICTIONS", "B5_I3_READINESS"}
    anchored = {"artifact_kind": "analysis", "artifact_id": "A-1", "artifact_field": "summary", "evaluated_excerpt": "texto", "evidence_refs": ["F-1"], "evidence_excerpts": [{"evidence_ref": "F-1", "excerpt": "texto"}], "editorial_comparison": "comparación", "why_specific_or_generic": "es específico", "decision": "SATISFIED"}
    return {
        "audit_id": "B5I2-SSA-1", "episode_id": "EP-1", "auditor_role": AUDITOR_ROLE,
        "auditor_run_id": "RUN-AUDIT", "auditor_skill_id": SKILL_ID, "auditor_skill_version": SKILL_VERSION,
        "provider_or_adapter": "mock", "model_or_evaluator": "test", "execution_timestamp": "2026-07-25T08:00:00Z",
        "input_manifest_checksum": "a" * 64,
        "artifact_checksums": [{"artifact_kind": kind, "artifact_id": artifact_id, "checksum": "a" * 64, "producer_run_id": "RUN-P"} for kind, artifact_id in [("research", "R-1"), ("evidence_report", "E-1"), ("provisional_thesis", "TP-1"), ("analysis", "A-1"), ("curation", "C-1"), ("refined_thesis", "T-1"), ("script_promise", "SP-1")]],
        "audit_method": "AI_SEMANTIC_REVIEW",
        "audited_artifact_ids": ["analysis:A-1", "curation:C-1", "refined_thesis:T-1", "script_promise:SP-1"],
        "audited_artifact_versions": [{"artifact_kind": "analysis", "artifact_id": "A-1", "checksum": "a" * 64, "producer_run_id": "RUN-P"}, {"artifact_kind": "curation", "artifact_id": "C-1", "checksum": "a" * 64, "producer_run_id": "RUN-P"}, {"artifact_kind": "refined_thesis", "artifact_id": "T-1", "checksum": "a" * 64, "producer_run_id": "RUN-P"}, {"artifact_kind": "script_promise", "artifact_id": "SP-1", "checksum": "a" * 64, "producer_run_id": "RUN-P"}],
        "criteria_results": [{"criterion": criterion, "status": "SATISFIED", "summary": "hallazgo trazable"} for criterion in criteria],
        "findings": [{"criterion": criterion, "status": "SATISFIED", "anchored_findings": [anchored] if criterion in critical else [], "rationale": "hallazgo trazable"} for criterion in criteria],
        "dimension_results": [{"dimension": name, "status": "PASS", "summary": "Dimensión controlada por fixture."} for name in ["TRIVIAL_THESIS", "INTERCHANGEABLE_ANALYSIS", "DECORATIVE_OBJECTION", "FALSE_DEPTH", "REPHRASED_NOT_REFINED_THESIS", "REDUNDANT_CURATION", "NO_ARGUMENTATIVE_PROGRESSION", "UNSUPPORTED_INFERENCE", "SUMMARY_INSTEAD_OF_ANALYSIS", "MISSING_INTERPRETIVE_LIMIT"]],
        "thesis_refinement_finding": {"status": "PASS", "summary": "El fixture sintetiza el estado de refinamiento."},
        "blocking_defects": [], "non_blocking_defects": [], "cited_evidence": ["F-1"], "required_corrections": [], "unresolved_questions": [], "inherited_restrictions_checked": [], "auditor_statement": "Decision PASS emitida sobre artefactos B5-I2 con evidencia citada.",
        "decision": "PASS", "readiness": "BLOCKED", "created_at": "2026-07-25T08:00:00Z",
    }


def _completion_gate_config(tmp_path: Path) -> dict[str, str]:
    repo = tmp_path / "gate_repo"
    repo.mkdir()
    def git(*args: str) -> str:
        return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True).stdout.strip()
    git("init", "--quiet")
    git("config", "user.email", "gate@example.test")
    git("config", "user.name", "Gate Test")
    (repo / "control.md").write_text("CURRENT_MISSION: TEST_MISSION\n", encoding="utf-8")
    git("add", "control.md")
    git("commit", "-m", "control", "--quiet")
    baseline_commit = git("rev-parse", "HEAD")
    contract_path = repo / "mission_contract.json"
    contract_path.write_text(json.dumps({
        "mission_id": "TEST_MISSION",
        "artifact_id": "test-mission",
        "artifact_version": "1.0.0",
        "authorized_paths": ["control.md", "mission_contract.json"],
        "protected_untracked_paths": [],
        "protected_untracked_baseline": [],
        "required_tests": [{"label": "fixture", "command": [sys.executable, "-c", "pass"]}],
        "push_allowed": False,
        "contains_material_repair": False,
        "push_guard": {"remote": "LOCAL", "ref": "HEAD~1", "baseline_remote_commit": baseline_commit},
        "state_requirements": {"control_path": "control.md", "required": {"CURRENT_MISSION": "TEST_MISSION"}, "forbidden": {}},
        "schema_checks": [],
    }), encoding="utf-8")
    git("add", "mission_contract.json")
    git("commit", "-m", "contract", "--quiet")
    contract = load_mission_contract(contract_path)
    result = run_mission_completion_gate(contract, repo)
    assert result.status.value == "PASS", result.to_dict()
    result_path = tmp_path / "completion_gate.json"
    result_path.write_text(json.dumps(result.to_dict(), ensure_ascii=False), encoding="utf-8")
    return {
        "completion_gate_result_path": str(result_path),
        "mission_contract_path": str(contract_path),
        "mission_repo_root": str(repo),
    }


def _register_synthetic_auditor(root: Path) -> None:
    (root / "config").mkdir(exist_ok=True)
    (root / "config" / "capability_registry.json").write_text(json.dumps({
        "registry_version": "1.0.0",
        "authority": "CAPABILITY_FUNCTIONAL_AUTHORITY",
        "routing_consumer": "HYBRID_RUNTIME_TEST",
        "compatibility_tokens": {"maturity": {}, "availability": {}, "assurance": {}, "approval": {}, "evidence": {}},
        "capabilities": [{
            "capability_id": CAPABILITY,
            "domain": "SCRIPT_PRODUCT",
            "functional_authority_domain": "SCRIPT_PRODUCT",
            "purpose": "Synthetic semantic auditor fixture.",
            "functional_requirements": [],
            "implementation_kind": "DETERMINISTIC",
            "maturity_status": "DEFINED",
            "assigned_role": [AUDITOR_ROLE],
            "routing_required": False,
        }],
    }), encoding="utf-8")

def _governed_request(tmp_path: Path, *, allowed_routes: list[str], **overrides) -> ExecutionRequest:
    setup_governed_repo(tmp_path, allowed_routes=allowed_routes, role_id=AUDITOR_ROLE)
    request = _request(tmp_path, **overrides)
    request.config.update({
        "repository_root": str(tmp_path),
        "mission_authorization_path": "mission-authorization.json",
        "context_policy_path": "config/context_resolution_policy.json",
    })
    if isinstance(request.config.get("routing_policy_path"), str):
        request.config["routing_policy_path"] = Path(request.config["routing_policy_path"])
    return request


def _request(tmp_path: Path, **overrides) -> ExecutionRequest:
    _register_synthetic_auditor(tmp_path)
    source = tmp_path / "analysis.json"
    source.write_text('{"analysis_id":"A-1"}', encoding="utf-8")
    kwargs = {"capability_id": CAPABILITY, "skill_id": SKILL_ID, "skill_version": SKILL_VERSION, "input_artifacts": [InputArtifact("analysis", "A-1", source, "RUN-P")], "output_schema": "b5_i2_semantic_sufficiency_audit", "execution_mode": "mock", "provider": "mock", "mock_output": _audit(), "output_artifact_kind": "semantic_audit", "output_artifact_id": "B5I2-SSA-1", "output_artifact_ref": "semantic_audit:B5I2-SSA-1", "episode_id": "EP-1", "role": AUDITOR_ROLE}
    kwargs.update(overrides)
    if kwargs.get("provider") == "agent_handoff" and "config" not in overrides:
        kwargs["config"] = _completion_gate_config(tmp_path)
    kwargs.setdefault("config", {})
    kwargs["config"].setdefault("repository_root", str(tmp_path))
    return ExecutionRequest(**kwargs)


def test_handoff_without_completion_gate_is_blocked(tmp_path: Path) -> None:
    result = execute(_request(
        tmp_path,
        provider="agent_handoff",
        execution_mode="agent_handoff",
        handoff_directory=tmp_path / "handoff",
        config={},
    ))
    assert result.status is ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR
    assert "MISSION_COMPLETION_GATE_REQUIRED" in (result.error or "")


def test_neutral_agent_harness_family_prepares_handoff_without_concrete_identity(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    gate_config = _completion_gate_config(tmp_path)
    monkeypatch.setattr("src.ai.runtime_profiles.shutil.which", lambda command: pytest.fail("neutral family must not inspect a concrete executor"))
    result = execute(_request(
        tmp_path,
        provider=None,
        execution_mode="agent_harness",
        execution_route="agent_harness",
        execution_family="AGENT_HARNESS",
        execution_profile=None,
        model=None,
        config={"execution_family": "AGENT_HARNESS"},
        run_configuration={
            "role_id": AUDITOR_ROLE,
            "execution_route": "agent_harness",
            "execution_profile": None,
            "execution_family": "AGENT_HARNESS",
            "executor_override": None,
            "provider_override": None,
            "model_override": None,
            "reasoning_effort": None,
            "mission_contract_path": gate_config["mission_contract_path"],
            "completion_gate_result_path": gate_config["completion_gate_result_path"],
            "mission_repo_root": gate_config["mission_repo_root"],
            "timeout_seconds": 180,
            "max_retries": 1,
            "temperature": None,
            "max_tokens": None,
            "budget_limit": None,
            "paid_cost_approved": False,
        },
        handoff_directory=tmp_path / "handoff",
    ))
    assert result.status is ExecutionStatus.HANDOFF_PREPARED
    package = json.loads(Path(result.usage["package"]).read_text(encoding="utf-8"))
    assert package["execution_family"] == "AGENT_HARNESS"
    assert package["execution_profile"] is None
    assert package["model_override"] is None


def test_direct_neutral_agent_harness_handoff_requires_verified_route(tmp_path: Path) -> None:
    config = _completion_gate_config(tmp_path)
    request = _request(
        tmp_path,
        provider="agent_handoff",
        execution_mode="agent_harness",
        execution_route="agent_harness",
        execution_family="AGENT_HARNESS",
        execution_profile=None,
        model=None,
        config={**config, "execution_family": "AGENT_HARNESS"},
        handoff_directory=tmp_path / "handoff",
    )
    with pytest.raises(PermissionError, match="RUNTIME_CONFIGURATION_NOT_RESOLVED_BEFORE_HANDOFF"):
        AgentHandoffProvider().prepare(request, "manifest", "RUN-DIRECT-NEUTRAL")
    assert not (tmp_path / "handoff" / "RUN-DIRECT-NEUTRAL.json").exists()


def test_handoff_rejects_forged_pass_even_with_binding_shape(tmp_path: Path) -> None:
    config = _completion_gate_config(tmp_path)
    genuine = json.loads(Path(config["completion_gate_result_path"]).read_text(encoding="utf-8"))
    genuine["evidence"]["binding"]["git_head"] = "0" * 40
    forged = tmp_path / "forged_gate.json"
    forged.write_text(json.dumps(genuine), encoding="utf-8")
    config["completion_gate_result_path"] = str(forged)

    result = execute(_request(
        tmp_path,
        provider="agent_handoff",
        execution_mode="agent_handoff",
        handoff_directory=tmp_path / "handoff",
        config=config,
    ))

    assert result.status is ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR
    assert "MISSION_COMPLETION_GATE_REQUIRED" in (result.error or "")


def test_profile_reasoning_effort_is_blocked_before_handoff_package(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config = _completion_gate_config(tmp_path)
    config["execution_profiles_path"] = str(Path(__file__).resolve().parents[2] / "config/agent_execution_profiles.json")
    monkeypatch.setattr("src.ai.runtime_profiles.shutil.which", lambda command: f"C:/tools/{command}")
    request = _request(
        tmp_path,
        provider="agent_handoff",
        execution_mode="agent_handoff",
        execution_profile="codex_current",
        model="gpt-5.6-luna",
        reasoning_effort="medium",
        run_configuration={
            "role_id": AUDITOR_ROLE,
            "execution_route": "agent_harness",
            "execution_profile": "codex_current",
            "executor_override": "codex_cli",
            "provider_override": None,
            "model_override": "gpt-5.6-luna",
            "reasoning_effort": "medium",
            "timeout_seconds": 180,
            "max_retries": 1,
            "temperature": None,
            "max_tokens": None,
            "budget_limit": None,
            "paid_cost_approved": False,
        },
        handoff_directory=tmp_path / "handoff",
        config=config,
    )
    result = execute(request)
    assert result.status is ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR
    assert "reasoning_effort no soportado" in (result.error or "")
    assert not list((tmp_path / "handoff").glob("*.json"))


def test_resolved_agent_profile_prepares_handoff_without_integrated_executor(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config = _completion_gate_config(tmp_path)
    config["execution_profiles_path"] = str(Path(__file__).resolve().parents[2] / "config/agent_execution_profiles.json")
    monkeypatch.setattr("src.ai.runtime_profiles.shutil.which", lambda command: f"C:/tools/{command}")
    request = _request(
        tmp_path,
        provider="agent_handoff",
        execution_mode="agent_handoff",
        execution_profile="codex_current",
        model="gpt-5.6-luna",
        reasoning_effort=None,
        run_configuration={
            "role_id": AUDITOR_ROLE,
            "execution_route": "agent_harness",
            "execution_profile": "codex_current",
            "executor_override": "codex_cli",
            "provider_override": None,
            "model_override": "gpt-5.6-luna",
            "reasoning_effort": None,
            "timeout_seconds": 180,
            "max_retries": 1,
            "temperature": None,
            "max_tokens": None,
            "budget_limit": None,
            "paid_cost_approved": False,
        },
        handoff_directory=tmp_path / "handoff",
        config=config,
    )
    result = execute(request)
    assert result.status is ExecutionStatus.HANDOFF_PREPARED
    assert result.usage["execution_profile"] == "codex_current"
    assert result.usage["execution_route"] == "agent_harness"
    package = json.loads(Path(result.usage["package"]).read_text(encoding="utf-8"))
    assert package["execution_profile"] == "codex_current"
    assert package["model_override"] == "gpt-5.6-luna"
    assert package["reasoning_effort"] is None


def test_forged_runtime_resolution_marker_cannot_prepare_profile_handoff(tmp_path: Path) -> None:
    config = _completion_gate_config(tmp_path)
    request = _request(
        tmp_path,
        provider="agent_handoff",
        execution_mode="agent_handoff",
        execution_profile="codex_current",
        run_configuration={"execution_profile": "codex_current", "reasoning_effort": "medium"},
        config={**config, "runtime_route_resolved": True},
        handoff_directory=tmp_path / "handoff",
    )
    with pytest.raises(PermissionError, match="RUNTIME_CONFIGURATION_NOT_RESOLVED_BEFORE_HANDOFF"):
        AgentHandoffProvider().prepare(request, "manifest", "RUN-DIRECT")
    assert not (tmp_path / "handoff" / "RUN-DIRECT.json").exists()


def test_forged_resolved_route_without_canonical_token_cannot_prepare_handoff(tmp_path: Path) -> None:
    config = _completion_gate_config(tmp_path)
    request = _request(
        tmp_path,
        provider="agent_handoff",
        execution_mode="agent_handoff",
        execution_profile="codex_current",
        model="gpt-5.6-luna",
        executor="codex_cli",
        execution_route="agent_harness",
        run_configuration={"execution_profile": "codex_current", "reasoning_effort": "medium"},
        config={**config, "runtime_route_resolved": True},
        handoff_directory=tmp_path / "handoff",
    )
    request.resolved_route = ResolvedExecutionRoute(
        role_id="CHANNEL_INTELLIGENCE_PRODUCER",
        execution_route="agent_harness",
        execution_profile="codex_current",
        route_type="AGENT_HARNESS_RUNTIME",
        executor="codex_cli",
        provider="MANAGED_BY_EXECUTOR",
        provider_adapter="agent_executor",
        model="gpt-5.6-luna",
        status=READY,
    )
    with pytest.raises(PermissionError, match="RUNTIME_CONFIGURATION_NOT_RESOLVED_BEFORE_HANDOFF"):
        AgentHandoffProvider().prepare(request, "manifest", "RUN-FORGED-ROUTE")
    assert not (tmp_path / "handoff" / "RUN-FORGED-ROUTE.json").exists()

def test_handoff_rejects_pass_without_mandatory_evidence(tmp_path: Path) -> None:
    config = _completion_gate_config(tmp_path)
    forged = tmp_path / "forged_empty_evidence.json"
    forged.write_text(json.dumps({
        "gate_id": "MISSION_COMPLETION",
        "artifact_id": "test-mission",
        "artifact_version": "1.0.0",
        "status": "PASS",
        "summary": "fabricated",
        "violations": [],
        "warnings": [],
        "evidence": {},
        "checked_at": "2026-08-08T00:00:00Z",
        "checker_version": "1.0.0",
        "exit_code": 0,
    }), encoding="utf-8")
    config["completion_gate_result_path"] = str(forged)

    result = execute(_request(
        tmp_path,
        provider="agent_handoff",
        execution_mode="agent_handoff",
        handoff_directory=tmp_path / "handoff",
        config=config,
    ))

    assert result.status is ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR
    assert "mandatory evidence" in (result.error or "")

def _four_artifacts(tmp_path: Path) -> list[InputArtifact]:
    _register_synthetic_auditor(tmp_path)
    rows = [("research", "R-1"), ("evidence_report", "E-1"), ("provisional_thesis", "TP-1"), ("analysis", "A-1"), ("curation", "C-1"), ("refined_thesis", "T-1"), ("script_promise", "SP-1")]
    return [InputArtifact(kind, artifact_id, _write_artifact(tmp_path, f"{kind}.json", artifact_id), "RUN-P") for kind, artifact_id in rows]


def _artifacts_with_optional_early_packaging(tmp_path: Path) -> list[InputArtifact]:
    artifacts = _four_artifacts(tmp_path)
    artifacts.append(InputArtifact("early_packaging_hypothesis", "EPH-1", _write_artifact(tmp_path, "early_packaging_hypothesis.json", "EPH-1"), "RUN-PKG"))
    return artifacts


def _write_artifact(root: Path, name: str, artifact_id: str) -> Path:
    path = root / name
    path.write_text(json.dumps({"id": artifact_id, "content": "contenido editorial concreto"}), encoding="utf-8")
    return path


def _producer_output(schema_name: str) -> dict:
    fixture = copy.deepcopy(VALID_FIXTURES[schema_name])
    if schema_name == "narrative_human_analysis":
        fixture.update({"analysis_id": "A-1", "episode_id": "EP-1", "research_id": "RP-1", "evidence_report_id": "ER-1", "semantic_audit_id": "SSA-1", "material_id": "M-1"})
    elif schema_name == "material_curation":
        fixture.update({"curation_id": "C-1", "episode_id": "EP-1", "research_id": "RP-1", "analysis_ids": ["A-1"]})
    elif schema_name == "refined_thesis":
        fixture.update({"thesis_id": "T-1", "episode_id": "EP-1", "research_id": "RP-1", "evidence_report_id": "ER-1", "semantic_audit_id": "SSA-1", "provisional_thesis_id": "TP-1", "analysis_ids": ["A-1"], "curation_id": "C-1"})
    elif schema_name == "editorial_script_promise":
        fixture.update({"promise_id": "SP-1", "episode_id": "EP-1", "refined_thesis_id": "T-1"})
    return fixture


def _output_id(kind: str) -> str:
    return {"analysis": "A-1", "curation": "C-1", "refined_thesis": "T-1", "script_promise": "SP-1", "claims_ledger": "CL-001", "work_lifecycle": "WL-001", "work_research_dossier": "WRD-001"}[kind]


def _output_file(tmp_path: Path, kind: str, payload: dict) -> Path:
    path = tmp_path / f"{kind}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def _register_synthetic_producer(root: Path, role: str) -> None:
    (root / "config").mkdir(exist_ok=True)
    (root / "config" / "capability_registry.json").write_text(json.dumps({
        "registry_version": "1.0.0",
        "authority": "CAPABILITY_FUNCTIONAL_AUTHORITY",
        "routing_consumer": "HYBRID_RUNTIME_TEST",
        "compatibility_tokens": {"maturity": {}, "availability": {}, "assurance": {}, "approval": {}, "evidence": {}},
        "capabilities": [{
            "capability_id": "PRODUCER",
            "domain": "SCRIPT_PRODUCT",
            "functional_authority_domain": "SCRIPT_PRODUCT",
            "purpose": "Synthetic provenance fixture.",
            "functional_requirements": [],
            "implementation_kind": "DETERMINISTIC",
            "maturity_status": "DEFINED",
            "assigned_role": [role],
            "routing_required": False,
        }],
    }), encoding="utf-8")


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
    result = execute(_governed_request(tmp_path, allowed_routes=["local_model"], provider="ollama", execution_mode="local", model="local", timeout=0.01, config={"base_url": "http://127.0.0.1:1"}))
    assert result.status is ExecutionStatus.BLOCKED_BY_RUNTIME_PROVIDER


def test_agent_handoff_package_is_importable_and_rejects_bad_checksum(tmp_path: Path) -> None:
    request = _request(tmp_path, provider="agent_handoff", execution_mode="agent_handoff", handoff_directory=tmp_path / "handoff")
    result = execute(request)
    assert result.status is ExecutionStatus.HANDOFF_PREPARED
    package = Path(result.usage["package"])
    imported = tmp_path / "result.json"
    package_data = json.loads(package.read_text(encoding="utf-8"))
    payload = {"handoff_id": result.run_id, "package_checksum": package_data["package_checksum"], "skill_id": SKILL_ID, "skill_version": SKILL_VERSION, "input_manifest_checksum": result.input_manifest_checksum, "output": _audit()}
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
    policy.write_text("capabilities:\n  B5_I2_SEMANTIC_AUDITOR:\n    routing:\n      allow_external_api: true\n", encoding="utf-8")
    governed = _governed_request(tmp_path, allowed_routes=["api_model"], provider="openai_compatible", execution_mode="api", model="semantic-test", config={"routing_policy_path": str(policy)})
    result = execute(governed)
    assert result.is_real_editorial_execution
    registry = tmp_path / "execution_registry.json"
    append_result(registry, result, execution_mode="REAL", role=AUDITOR_ROLE, request=governed)
    saved = json.loads(registry.read_text(encoding="utf-8"))
    assert saved["runs"][0]["run_id"] == result.run_id
    assert saved["runs"][0]["role"] == AUDITOR_ROLE


def test_mock_b5_i2_flow_remains_blocked_for_editorial_decision(tmp_path: Path) -> None:
    result = execute_b5_i2_audit(
        artifacts=_four_artifacts(tmp_path),
        output_path=tmp_path / "audit.json",
        registry_path=tmp_path / "execution_registry.json",
        provider="mock",
        execution_mode="mock",
        mock_output=_audit(),
        config={"repository_root": str(tmp_path)},
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
        config={"repository_root": str(tmp_path)},
    )
    assert result.status is ExecutionStatus.FAILED
    assert "research" in (result.error or "")


def test_runner_builds_nonempty_editorial_prompt_and_imposes_runtime_provenance(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    artifacts = _four_artifacts(tmp_path)
    setup_governed_repo(tmp_path, allowed_routes=["api_model"], role_id=AUDITOR_ROLE)
    policy = tmp_path / "routing.yaml"
    policy.write_text("capabilities:\n  B5_I2_SEMANTIC_AUDITOR:\n    routing:\n      allow_external_api: true\n", encoding="utf-8")
    captured: dict[str, object] = {}
    def provider(self, request):
        captured["prompt"] = request.config["prompt"]
        payload = _audit()
        payload.update({"auditor_run_id": "FORGED", "provider_or_adapter": "forged", "model_or_evaluator": "forged", "input_manifest_checksum": "b" * 64})
        return payload, {"provider_or_adapter": "openai_compatible", "model_or_evaluator": "actual-semantic-model"}
    monkeypatch.setattr(OpenAICompatibleProvider, "execute", provider)
    result = execute_b5_i2_audit(artifacts=artifacts, output_path=tmp_path / "audit.json", registry_path=tmp_path / "registry.json", episode_id="EP-1", provider="openai_compatible", execution_mode="api", model="ignored", config={"routing_policy_path": policy, "repository_root": str(tmp_path), "mission_authorization_path": "mission-authorization.json", "context_policy_path": "config/context_resolution_policy.json"})
    prompt = str(captured["prompt"])
    assert all(token in prompt for token in ("skill_auditar_suficiencia_semantica_b5_i2@1.0.0", "ANALYSIS_SPECIFICITY", "B5_I3_READINESS", "EarlyPackagingHypothesis", "Artefactos reales", "schema estructural"))
    assert result.status is ExecutionStatus.SUCCEEDED
    assert result.output["auditor_run_id"] == result.run_id
    assert result.output["model_or_evaluator"] == "actual-semantic-model"
    assert result.output["input_manifest_checksum"] == manifest_checksum(ExecutionRequest("x", "x", "x", artifacts, "x", episode_id="EP-1"))
    saved = json.loads((tmp_path / "registry.json").read_text(encoding="utf-8"))
    assert saved["runs"][0]["outputs"][0]["checksum"] == _checksum(result.output) or saved["runs"][0]["outputs"][0]["checksum"] == result.output_checksum


def test_shared_manifest_matches_gate_representation(tmp_path: Path) -> None:
    artifacts = _four_artifacts(tmp_path)
    request = ExecutionRequest(CAPABILITY, SKILL_ID, SKILL_VERSION, artifacts, "b5_i2_semantic_sufficiency_audit", episode_id="EP-1", role=AUDITOR_ROLE)
    rows = [{"artifact_kind": item.artifact_kind, "artifact_id": item.artifact_id, "checksum": hashlib.sha256(item.path.read_bytes()).hexdigest()} for item in artifacts]
    assert manifest_checksum(request) == shared_manifest_checksum("EP-1", rows)


@pytest.mark.parametrize(("role", "artifact_kind", "schema_name"), PRODUCER_CASES)
def test_runtime_persists_real_producer_provenance(tmp_path: Path, role: str, artifact_kind: str, schema_name: str) -> None:
    _register_synthetic_producer(tmp_path, role)
    source = tmp_path / "input.json"
    source.write_text('{"source":"ok"}', encoding="utf-8")
    payload = _producer_output(schema_name)
    output_path = _output_file(tmp_path, artifact_kind, payload)
    request = ExecutionRequest(
        capability_id="PRODUCER",
        skill_id=f"skill_{artifact_kind}",
        skill_version="1.0.0",
        input_artifacts=[InputArtifact("research", "R-1", source, "RUN-R")],
        output_schema=schema_name,
        execution_mode="mock",
        provider="mock",
        mock_output=payload,
        episode_id="EP-1",
        role=role,
        output_artifact_kind=artifact_kind,
        output_artifact_id=_output_id(artifact_kind),
        output_artifact_path=output_path,
        output_artifact_ref=f"{artifact_kind}:{_output_id(artifact_kind)}",
        config={"repository_root": str(tmp_path)},
    )
    result = execute(request)
    assert result.status is ExecutionStatus.SUCCEEDED
    registry = tmp_path / f"{artifact_kind}_registry.json"
    persist_execution_result(registry, result, request, execution_mode="SYNTHETIC")
    saved = json.loads(registry.read_text(encoding="utf-8"))
    run = saved["runs"][0]
    assert run["episode_id"] == "EP-1"
    assert run["role"] == role
    assert run["outputs"][0]["artifact_kind"] == artifact_kind
    assert run["outputs"][0]["artifact_id"] == _output_id(artifact_kind)
    assert run["outputs"][0]["artifact_path"] == str(output_path)


def test_registry_checksum_follows_physical_json_bytes_across_indentation(tmp_path: Path) -> None:
    _register_synthetic_producer(tmp_path, "SCRIPT_PRODUCT_PRODUCER")
    payload = _producer_output("claims_ledger")
    compact = _output_file(tmp_path, "claims_ledger_compact", payload)
    indented = _output_file(tmp_path, "claims_ledger_indented", payload)
    indented.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def persist(output_path: Path, registry_path: Path, run_id: str) -> str:
        request = ExecutionRequest(
            capability_id="PRODUCER",
            skill_id="skill_claims_ledger",
            skill_version="1.0.0",
            input_artifacts=[InputArtifact("research", "R-1", compact, "RUN-R")],
            output_schema="claims_ledger",
            execution_mode="mock",
            provider="mock",
            mock_output=payload,
            episode_id="EP-1",
            role="SCRIPT_PRODUCT_PRODUCER",
            output_artifact_kind="claims_ledger",
                output_artifact_id="CL-001",
                output_artifact_path=output_path,
                output_artifact_ref="claims_ledger:CL-001",
                config={"repository_root": str(tmp_path)},
        )
        result = execute(request)
        result.run_id = run_id
        persist_execution_result(registry_path, result, request, execution_mode="SYNTHETIC")
        return json.loads(registry_path.read_text(encoding="utf-8"))["runs"][0]["outputs"][0]["checksum"]

    compact_checksum = persist(compact, tmp_path / "compact_registry.json", "RUN-COMPACT")
    indented_checksum = persist(indented, tmp_path / "indented_registry.json", "RUN-INDENTED")
    assert compact_checksum == hashlib.sha256(compact.read_bytes()).hexdigest()
    assert indented_checksum == hashlib.sha256(indented.read_bytes()).hexdigest()
    assert compact_checksum != indented_checksum


def test_incompatible_role_artifact_is_rejected(tmp_path: Path) -> None:
    output = _output_file(tmp_path, "analysis", _producer_output("narrative_human_analysis"))
    result = ExecutionResult(
        run_id="RUN-FAIL-1",
        status=ExecutionStatus.SUCCEEDED,
        executor_type="provider",
        provider="mock",
        model="mock",
        input_manifest_checksum="a" * 64,
        output={"ok": True},
        output_checksum=hashlib.sha256(output.read_bytes()).hexdigest(),
        started_at="2026-07-25T08:00:00Z",
        completed_at="2026-07-25T08:01:00Z",
        usage={"skill_id": "skill_bad", "skill_version": "1.0.0"},
        episode_id="EP-1",
        output_artifact_id="A-1",
        output_artifact_kind="analysis",
        output_artifact_path=output,
        output_artifact_ref="analysis:A-1",
    )
    with pytest.raises(ValueError, match="incompatible"):
        append_result(tmp_path / "registry.json", result, execution_mode="SYNTHETIC", role="INDEPENDENT_EDITORIAL_AUDITOR")


def test_unknown_role_cannot_produce_b5_i2_analysis(tmp_path: Path) -> None:
    output = _output_file(tmp_path, "analysis", _producer_output("narrative_human_analysis"))
    result = ExecutionResult(
        run_id="RUN-FAIL-UNKNOWN",
        status=ExecutionStatus.SUCCEEDED,
        executor_type="provider",
        provider="mock",
        model="mock",
        input_manifest_checksum="a" * 64,
        output={"ok": True},
        output_checksum=hashlib.sha256(output.read_bytes()).hexdigest(),
        started_at="2026-07-25T08:00:00Z",
        completed_at="2026-07-25T08:01:00Z",
        usage={"skill_id": "skill_bad", "skill_version": "1.0.0"},
        episode_id="EP-1",
        output_artifact_id="A-1",
        output_artifact_kind="analysis",
        output_artifact_path=output,
        output_artifact_ref="analysis:A-1",
    )
    with pytest.raises(ValueError, match="no registrado"):
        append_result(tmp_path / "registry.json", result, execution_mode="SYNTHETIC", role="UNKNOWN_ROLE")


def test_missing_output_path_is_rejected_for_producer(tmp_path: Path) -> None:
    result = ExecutionResult(
        run_id="RUN-FAIL-2",
        status=ExecutionStatus.SUCCEEDED,
        executor_type="provider",
        provider="mock",
        model="mock",
        input_manifest_checksum="a" * 64,
        output={"ok": True},
        output_checksum="a" * 64,
        started_at="2026-07-25T08:00:00Z",
        completed_at="2026-07-25T08:01:00Z",
        usage={"skill_id": "skill_analysis", "skill_version": "1.0.0"},
        episode_id="EP-1",
        output_artifact_id="A-1",
        output_artifact_kind="analysis",
        output_artifact_ref="analysis:A-1",
    )
    with pytest.raises(ValueError, match="output_artifact_path"):
        append_result(tmp_path / "registry.json", result, execution_mode="SYNTHETIC", role="ANALYSIS_PRODUCER")


def test_duplicate_run_id_and_checksum_mismatch_are_rejected(tmp_path: Path) -> None:
    output = _output_file(tmp_path, "script_promise", _producer_output("editorial_script_promise"))
    checksum = hashlib.sha256(output.read_bytes()).hexdigest()
    result = ExecutionResult(
        run_id="RUN-DUP-1",
        status=ExecutionStatus.SUCCEEDED,
        executor_type="provider",
        provider="mock",
        model="mock",
        input_manifest_checksum="a" * 64,
        output={"ok": True},
        output_checksum=checksum,
        started_at="2026-07-25T08:00:00Z",
        completed_at="2026-07-25T08:01:00Z",
        usage={"skill_id": "skill_promise", "skill_version": "1.0.0"},
        episode_id="EP-1",
        output_artifact_id="SP-1",
        output_artifact_kind="script_promise",
        output_artifact_path=output,
        output_artifact_ref="script_promise:SP-1",
    )
    registry = tmp_path / "registry.json"
    append_result(registry, result, execution_mode="SYNTHETIC", role="SCRIPT_PROMISE_PRODUCER")
    with pytest.raises(ValueError, match="run_id duplicado"):
        append_result(registry, result, execution_mode="SYNTHETIC", role="SCRIPT_PROMISE_PRODUCER")
    bad = copy.deepcopy(result)
    bad.run_id = "RUN-DUP-2"
    bad.output_checksum = "b" * 64
    with pytest.raises(ValueError, match="checksum incorrecto"):
        append_result(tmp_path / "registry2.json", bad, execution_mode="SYNTHETIC", role="SCRIPT_PROMISE_PRODUCER")


def test_auto_and_api_do_not_authorize_external_use_from_environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AI_API_KEY", "present-but-not-authorized")
    monkeypatch.setenv("AI_BASE_URL", "https://provider.invalid")
    request = _request(tmp_path, provider=None, execution_mode="auto", config={"local_available": False})
    assert execute(request).status is ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR
    request = _request(tmp_path, provider="openai_compatible", execution_mode="api")
    assert execute(request).status is ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR


def test_handoff_import_rejects_foreign_package_and_persists_valid_result(tmp_path: Path) -> None:
    artifacts = _four_artifacts(tmp_path)
    request = ExecutionRequest(CAPABILITY, SKILL_ID, SKILL_VERSION, artifacts, "b5_i2_semantic_sufficiency_audit", execution_mode="agent", provider="agent_handoff", output_artifact_id="B5I2-SSA-1", handoff_directory=tmp_path / "handoff", episode_id="EP-1", config={**_completion_gate_config(tmp_path), "repository_root": str(tmp_path), "prompt": "instrucciones editoriales", "execution_registry_path": str(tmp_path / "registry.json")}, role=AUDITOR_ROLE)
    prepared = execute(request)
    package = Path(prepared.usage["package"])
    data = json.loads(package.read_text(encoding="utf-8"))
    imported = tmp_path / "import.json"
    payload = {"handoff_id": prepared.run_id, "package_checksum": data["package_checksum"], "skill_id": SKILL_ID, "skill_version": SKILL_VERSION, "input_manifest_checksum": prepared.input_manifest_checksum, "output": _audit()}
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
    result = ExecutionResult(run_id="RUN-AI-atomic", status=ExecutionStatus.SUCCEEDED, executor_type="provider", provider="ollama", model="editorial-local", input_manifest_checksum="a" * 64, output=_audit(), output_checksum="b" * 64, started_at="2026-07-25T08:00:00Z", completed_at="2026-07-25T08:01:00Z", usage={"skill_id": SKILL_ID, "skill_version": SKILL_VERSION}, episode_id="EP-1", output_artifact_id="B5I2-SSA-1", output_artifact_kind="semantic_audit", output_artifact_ref="semantic_audit:B5I2-SSA-1", is_real_editorial_execution=True)
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
    assert not (tmp_path / "audit.json.txn.json").exists()
    assert not (tmp_path / "audit.json.bak").exists()
    assert not (tmp_path / "registry.json.bak").exists()


def test_recovery_after_interruption_between_replaces_restores_previous_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _, _, _, registry = _registered_handoff_fixture(tmp_path)
    output = tmp_path / "audit.json"
    output.write_text('{"previous":"audit"}\n', encoding="utf-8")
    previous_registry_text = registry.read_text(encoding="utf-8")
    result = ExecutionResult(run_id="RUN-AI-interrupt", status=ExecutionStatus.SUCCEEDED, executor_type="provider", provider="ollama", model="editorial-local", input_manifest_checksum="a" * 64, output=_audit(), output_checksum="b" * 64, started_at="2026-07-25T08:00:00Z", completed_at="2026-07-25T08:01:00Z", usage={"skill_id": SKILL_ID, "skill_version": SKILL_VERSION}, episode_id="EP-1", output_artifact_id="B5I2-SSA-1", output_artifact_kind="semantic_audit", output_artifact_ref="semantic_audit:B5I2-SSA-1", is_real_editorial_execution=True)
    original_replace = audit_runner.os.replace
    state = {"count": 0}

    def interrupt_after_first_replace(source, destination):
        state["count"] += 1
        original_replace(source, destination)
        if state["count"] == 1:
            raise KeyboardInterrupt("simulated interruption")

    monkeypatch.setattr(audit_runner.os, "replace", interrupt_after_first_replace)
    with pytest.raises(KeyboardInterrupt, match="simulated interruption"):
        audit_runner._atomic_persist(output, registry, _audit(), result)

    journal = tmp_path / "audit.json.txn.json"
    assert journal.exists()
    assert json.loads(journal.read_text(encoding="utf-8"))["status"] == "PREPARED"
    assert json.loads(output.read_text(encoding="utf-8"))["audit_id"] == "B5I2-SSA-1"
    assert json.loads(registry.read_text(encoding="utf-8"))["handoffs"][0]["status"] == "HANDOFF_PREPARED"

    monkeypatch.setattr(audit_runner.os, "replace", original_replace)
    audit_runner._recover_prepared_transaction(output, registry)

    assert output.read_text(encoding="utf-8") == '{"previous":"audit"}\n'
    assert registry.read_text(encoding="utf-8") == previous_registry_text
    restored = json.loads(previous_registry_text)
    assert restored["handoffs"][0]["status"] == "HANDOFF_PREPARED"
    assert not journal.exists()
    assert not (tmp_path / "audit.json.bak").exists()
    assert not (tmp_path / "registry.json.bak").exists()


def test_complete_commit_cleans_journal_and_backups(tmp_path: Path) -> None:
    output, registry = tmp_path / "audit.json", tmp_path / "registry.json"
    result = ExecutionResult(run_id="RUN-AI-clean", status=ExecutionStatus.SUCCEEDED, executor_type="provider", provider="ollama", model="editorial-local", input_manifest_checksum="a" * 64, output=_audit(), output_checksum="b" * 64, started_at="2026-07-25T08:00:00Z", completed_at="2026-07-25T08:01:00Z", usage={"skill_id": SKILL_ID, "skill_version": SKILL_VERSION}, episode_id="EP-1", output_artifact_id="B5I2-SSA-1", output_artifact_kind="semantic_audit", output_artifact_ref="semantic_audit:B5I2-SSA-1", is_real_editorial_execution=True)

    audit_runner._atomic_persist(output, registry, _audit(), result)

    assert output.exists()
    assert registry.exists()
    assert not (tmp_path / "audit.json.txn.json").exists()
    assert not (tmp_path / "audit.json.bak").exists()
    assert not (tmp_path / "registry.json.bak").exists()


def test_provider_may_return_editorial_fields_only(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    artifacts = _four_artifacts(tmp_path)
    setup_governed_repo(tmp_path, allowed_routes=["api_model"], role_id=AUDITOR_ROLE)
    policy = tmp_path / "routing.yaml"
    policy.write_text("capabilities:\n  B5_I2_SEMANTIC_AUDITOR:\n    routing:\n      allow_external_api: true\n", encoding="utf-8")
    editorial = {
        "audit_id": "B5I2-SSA-1",
        "audited_artifact_ids": ["analysis:A-1", "curation:C-1", "refined_thesis:T-1", "script_promise:SP-1"],
        "audited_artifact_versions": [{"artifact_kind": "analysis", "artifact_id": "A-1", "checksum": "a" * 64, "producer_run_id": "RUN-P"}, {"artifact_kind": "curation", "artifact_id": "C-1", "checksum": "a" * 64, "producer_run_id": "RUN-P"}, {"artifact_kind": "refined_thesis", "artifact_id": "T-1", "checksum": "a" * 64, "producer_run_id": "RUN-P"}, {"artifact_kind": "script_promise", "artifact_id": "SP-1", "checksum": "a" * 64, "producer_run_id": "RUN-P"}],
        "criteria_results": _audit()["criteria_results"],
        "findings": _audit()["findings"],
        "dimension_results": _audit()["dimension_results"],
        "thesis_refinement_finding": _audit()["thesis_refinement_finding"],
        "blocking_defects": [],
        "non_blocking_defects": [],
        "cited_evidence": ["F-1"],
        "required_corrections": [],
        "unresolved_questions": [],
        "inherited_restrictions_checked": [],
        "auditor_statement": "Decision PASS emitida sobre artefactos B5-I2 con evidencia citada.",
        "decision": "PASS",
    }
    monkeypatch.setattr(OpenAICompatibleProvider, "execute", lambda self, request: (editorial, {"provider_or_adapter": "openai_compatible", "model_or_evaluator": "model-real"}))
    result = execute_b5_i2_audit(artifacts=artifacts, output_path=tmp_path / "audit.json", registry_path=tmp_path / "registry.json", episode_id="EP-1", provider="openai_compatible", execution_mode="api", config={"routing_policy_path": policy, "repository_root": str(tmp_path), "mission_authorization_path": "mission-authorization.json", "context_policy_path": "config/context_resolution_policy.json"})
    assert result.status is ExecutionStatus.SUCCEEDED
    assert result.output["auditor_run_id"] == result.run_id


def test_runner_accepts_audit_without_optional_early_packaging(tmp_path: Path) -> None:
    result = execute_b5_i2_audit(
        artifacts=_four_artifacts(tmp_path),
        output_path=tmp_path / "audit.json",
        registry_path=tmp_path / "execution_registry.json",
        provider="mock",
        execution_mode="mock",
        mock_output=_audit(),
        config={"repository_root": str(tmp_path)},
    )
    assert result.status is ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR
    assert result.error == "mock solo valida el flujo estructural; no cierra la auditoría editorial"


def test_runner_accepts_optional_early_packaging_when_present(tmp_path: Path) -> None:
    result = execute_b5_i2_audit(
        artifacts=_artifacts_with_optional_early_packaging(tmp_path),
        output_path=tmp_path / "audit.json",
        registry_path=tmp_path / "execution_registry.json",
        provider="mock",
        execution_mode="mock",
        mock_output=_audit(),
        config={"repository_root": str(tmp_path)},
    )
    assert result.status is ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR
    assert result.error == "mock solo valida el flujo estructural; no cierra la auditoría editorial"


def test_fabricated_self_consistent_handoff_without_registry_is_rejected(tmp_path: Path) -> None:
    artifacts = _four_artifacts(tmp_path)
    request = ExecutionRequest(CAPABILITY, SKILL_ID, SKILL_VERSION, artifacts, "b5_i2_semantic_sufficiency_audit", execution_mode="agent", provider="agent_handoff", output_artifact_id="B5I2-SSA-1", handoff_directory=tmp_path / "handoff", episode_id="EP-1", config={**_completion_gate_config(tmp_path), "repository_root": str(tmp_path), "prompt": "prompt"}, role=AUDITOR_ROLE)
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
    request = ExecutionRequest(CAPABILITY, SKILL_ID, SKILL_VERSION, artifacts, "b5_i2_semantic_sufficiency_audit", execution_mode="agent", provider="agent_handoff", output_artifact_id="B5I2-SSA-1", handoff_directory=tmp_path / "handoff", episode_id="EP-1", config={**_completion_gate_config(tmp_path), "repository_root": str(tmp_path), "prompt": "prompt", "execution_registry_path": str(registry)}, role=AUDITOR_ROLE)
    prepared = execute(request); package = Path(prepared.usage["package"])
    package_data = json.loads(package.read_text(encoding="utf-8")); package_data["prompt"] = "altered"; package_data["package_checksum"] = _checksum({key: value for key, value in package_data.items() if key != "package_checksum"}); package.write_text(json.dumps(package_data), encoding="utf-8")
    result_file = tmp_path / "result.json"; payload = {"handoff_id": prepared.run_id, "package_checksum": package_data["package_checksum"], "skill_id": package_data["skill_id"], "skill_version": package_data["skill_version"], "input_manifest_checksum": package_data["input_manifest_checksum"], "output": _audit()}; payload["output_checksum"] = _checksum(payload["output"]); result_file.write_text(json.dumps(payload), encoding="utf-8")
    rejected = import_b5_i2_handoff(package_path=package, result_path=result_file, artifacts=artifacts, output_path=tmp_path / "audit.json", registry_path=registry, episode_id="EP-1")
    assert rejected.status is ExecutionStatus.FAILED
    assert "package_checksum" in (rejected.error or "")


def test_handoff_cannot_be_consumed_twice(tmp_path: Path) -> None:
    registry = tmp_path / "registry.json"; artifacts = _four_artifacts(tmp_path)
    request = ExecutionRequest(CAPABILITY, SKILL_ID, SKILL_VERSION, artifacts, "b5_i2_semantic_sufficiency_audit", execution_mode="agent", provider="agent_handoff", output_artifact_id="B5I2-SSA-1", handoff_directory=tmp_path / "handoff", episode_id="EP-1", config={**_completion_gate_config(tmp_path), "repository_root": str(tmp_path), "prompt": "prompt", "execution_registry_path": str(registry)}, role=AUDITOR_ROLE)
    prepared = execute(request); package = Path(prepared.usage["package"]); data = json.loads(package.read_text(encoding="utf-8")); result_file = tmp_path / "result.json"; payload = {"handoff_id": prepared.run_id, "package_checksum": data["package_checksum"], "skill_id": data["skill_id"], "skill_version": data["skill_version"], "input_manifest_checksum": data["input_manifest_checksum"], "output": _audit()}; payload["output_checksum"] = _checksum(payload["output"]); result_file.write_text(json.dumps(payload), encoding="utf-8")
    first = import_b5_i2_handoff(package_path=package, result_path=result_file, artifacts=artifacts, output_path=tmp_path / "audit.json", registry_path=registry, episode_id="EP-1")
    second = import_b5_i2_handoff(package_path=package, result_path=result_file, artifacts=artifacts, output_path=tmp_path / "audit2.json", registry_path=registry, episode_id="EP-1")
    assert first.status is ExecutionStatus.SUCCEEDED and second.status is ExecutionStatus.FAILED


def _registered_handoff_fixture(tmp_path: Path):
    registry = tmp_path / "registry.json"; artifacts = _four_artifacts(tmp_path)
    request = ExecutionRequest(CAPABILITY, SKILL_ID, SKILL_VERSION, artifacts, "b5_i2_semantic_sufficiency_audit", execution_mode="agent", provider="agent_handoff", output_artifact_id="B5I2-SSA-1", handoff_directory=tmp_path / "handoff", episode_id="EP-1", config={**_completion_gate_config(tmp_path), "repository_root": str(tmp_path), "prompt": "prompt", "execution_registry_path": str(registry)}, role=AUDITOR_ROLE)
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


def test_handoff_consume_failure_rolls_back_audit_and_registry(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    package, result_file, artifacts, registry = _registered_handoff_fixture(tmp_path)
    monkeypatch.setattr(audit_runner, "consume_handoff", lambda *args, **kwargs: (_ for _ in ()).throw(ValueError("consume failed")))
    rejected = import_b5_i2_handoff(package_path=package, result_path=result_file, artifacts=artifacts, output_path=tmp_path / "audit.json", registry_path=registry, episode_id="EP-1")
    assert rejected.status is ExecutionStatus.FAILED
    assert not (tmp_path / "audit.json").exists()
    saved = json.loads(registry.read_text(encoding="utf-8"))
    assert saved["handoffs"][0]["status"] == "HANDOFF_PREPARED"
    assert all(run["run_id"] != rejected.run_id for run in saved.get("runs", []))
    assert not (tmp_path / "audit.json.txn.json").exists()
    assert not (tmp_path / "audit.json.bak").exists()
    assert not (tmp_path / "registry.json.bak").exists()


def test_auto_explicit_openai_provider_requires_authorization(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AI_API_KEY", "present"); monkeypatch.setenv("AI_BASE_URL", "https://provider.invalid")
    result = execute(_request(tmp_path, provider="openai_compatible", execution_mode="auto", config={"local_available": False}))
    assert result.status is ExecutionStatus.BLOCKED_BY_SEMANTIC_EVALUATOR


def test_deepseek_availability_and_response_errors_are_classified_explicitly(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEEPSEEK_API_KEY", "secret")
    policy = tmp_path / "routing.yaml"
    policy.write_text("capabilities:\n  B5_I2_SEMANTIC_AUDITOR:\n    routing:\n      allow_external_api: true\n", encoding="utf-8")
    request = _governed_request(tmp_path, allowed_routes=["api_model"], provider="deepseek", execution_mode="deepseek", model="deepseek-chat", config={"routing_policy_path": str(policy)})
    monkeypatch.setattr(DeepSeekProvider, "execute", lambda self, req: (_ for _ in ()).throw(RuntimeError("PROVIDER_UNAVAILABLE")))
    result = execute(request)
    assert result.status is ExecutionStatus.BLOCKED_BY_RUNTIME_PROVIDER
    assert result.usage["availability_status"] == "PROVIDER_UNAVAILABLE"
    monkeypatch.setattr(DeepSeekProvider, "execute", lambda self, req: (_ for _ in ()).throw(RuntimeError("TIMEOUT")))
    timeout_result = execute(request)
    assert timeout_result.status is ExecutionStatus.BLOCKED_BY_RUNTIME_PROVIDER
    assert timeout_result.usage["availability_status"] == "TIMEOUT"
    monkeypatch.setattr(DeepSeekProvider, "execute", lambda self, req: (_ for _ in ()).throw(ValueError("INVALID_RESPONSE")))
    invalid_result = execute(request)
    assert invalid_result.status is ExecutionStatus.FAILED
    assert invalid_result.usage["availability_status"] == "INVALID_RESPONSE"
