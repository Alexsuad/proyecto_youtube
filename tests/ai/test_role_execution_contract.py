from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from src.ai.contracts import ExecutionRequest, ExecutionStatus, InputArtifact
from src.ai.execution import _bind_runtime_fields, editorial_only_payload, execute
from src.ai.providers.ollama import OllamaProvider
from src.ai.role_execution import RoleExecutionContractError, build_model_prompt, resolve_role_execution_contract
from src.core.contract_validation import validate_against_schema
from tests.core.test_plan_005_real_consumer_integration import _request as governed_request, _setup as setup_governed_repo
from tests.harness.test_b5_i2 import _analysis, _refresh_b5_i2_audit, _write_case
from tests.harness.test_youtube_adaptation_b5_i2 import _early_packaging, _valid_package


def _runtime_values() -> dict[str, object]:
    return {"smoke_id":"SMOKE-1","role_id":"SCRIPT_PRODUCT_PRODUCER","execution_profile":"ollama_local","execution_route":"local_model","selected_executor":"native_provider","selected_provider":"ollama","selected_model":"Qwen2.5-Coder:latest","actual_executor":"native_provider","actual_provider":"ollama","actual_model":"Qwen2.5-Coder:latest","result":"SUCCEEDED","decision":"CONTRACTUAL_SMOKE_PASS","stdout_preview":"ok","stderr_preview":"","exit_code":0,"notes":[]}


def _producer_input() -> dict[str, object]:
    return {
        "active_editorial_profile_reference": {"profile_id": "mas_alla_del_guion", "version": "1.2.2"},
        "episode_brief": {"episode_id": "EP-1"},
        "research_pack": {"research_id": "R-1"},
        "source_access_and_evidence_report": {"report_id": "ER-1"},
        "provisional_thesis": {"thesis_id": "TP-1"},
        "semantic_sufficiency_audit": {"audit_id": "SSA-1"},
        "claims_ledger": [{"claim_id": "C-1"}],
        "approved_material_candidates": [{"material_id": "M-1"}],
        "excluded_claims": [],
        "limited_claims": [],
        "mandatory_disclosures": [],
    }


def test_role_contract_loads_prompt_profile_and_output_schema() -> None:
    contract=resolve_role_execution_contract("SCRIPT_PRODUCT_PRODUCER","execution_smoke_report",_producer_input(),_runtime_values())
    prompt=build_model_prompt(contract)
    assert contract["prompt_id"] == "prompt_script_product_producer"
    assert len(contract["prompt_checksum"]) == 64
    assert contract["compiled_profile"]["profile_checksum"]
    assert '"execution_smoke_report"' in prompt and '"input_payload"' in prompt


def test_b5_i2_model_contract_exposes_only_cognitive_fields() -> None:
    contract = resolve_role_execution_contract(
        "SCRIPT_PRODUCT_PRODUCER",
        "refined_thesis",
        {
            "active_editorial_profile_reference": {},
            "episode_brief": {},
            "research_pack": {},
            "source_access_and_evidence_report": {},
            "provisional_thesis": {},
            "semantic_sufficiency_audit": {},
            "claims_ledger": [],
            "approved_material_candidates": [],
            "excluded_claims": [],
            "limited_claims": [],
            "mandatory_disclosures": [],
        },
        _runtime_values(),
    )
    prompt = build_model_prompt(contract)
    assert '"statement"' in prompt
    assert '"thesis_id"' not in prompt
    assert '"created_at"' not in prompt


def test_semantic_audit_model_contract_keeps_cognitive_findings() -> None:
    contract = resolve_role_execution_contract(
        "SCRIPT_PRODUCT_AUDITOR",
        "b5_i2_semantic_sufficiency_audit",
        {
            "b5_i1_package": {},
            "narrative_human_analyses": [{}],
            "material_curation": {},
            "refined_thesis": {},
            "editorial_script_promise": {},
            "producer_run_reference": "RUN-PRODUCER",
            "artifact_checksums": [{"artifact_id": "A-1"}],
        },
        _runtime_values(),
    )
    prompt = build_model_prompt(contract)
    assert "required_changes" in contract["output_schema"]["properties"]
    assert "artifact_checksums" not in contract["output_schema"]["properties"]
    assert "auditor_run_id" not in contract["output_schema"]["properties"]
    assert '"output_contract"' in prompt


def test_software_rebinds_b5_i2_metadata_after_cognitive_projection(tmp_path) -> None:
    research_path = tmp_path / "research.json"
    research_path.write_text(
        '{"research_id":"R-1","narrative_evidence":[{"item_id":"N-1","material_id":"M-1","statement":"Evidencia concreta"}]}',
        encoding="utf-8",
    )
    request = ExecutionRequest(
        capability_id="B5_I2_SEMANTIC_AUDITOR",
        skill_id="skill_analisis_patrones",
        skill_version="1.0.0",
        input_artifacts=[InputArtifact("research", "R-1", research_path, "RUN-R-1")],
        output_schema="narrative_human_analysis",
        execution_mode="SYNTHETIC_TEST",
        output_artifact_id="A-1",
        episode_id="EP-1",
        role="SCRIPT_PRODUCT_PRODUCER",
        mock_output={},
    )
    projected = editorial_only_payload({
        "analysis_id": "AI-CREATED",
        "episode_id": "AI-EPISODE",
        "research_id": "AI-RESEARCH",
        "created_at": "2020-01-01T00:00:00Z",
        "material_checksum": "AI-CHECKSUM",
        "material_id": "M-1",
        "main_interpretation": "Una lectura concreta y situada.",
    })
    bound, run_id = _bind_runtime_fields(request, projected)
    assert bound["analysis_id"] == "A-1"
    assert bound["episode_id"] == "EP-1"
    assert bound["research_id"] == "R-1"
    assert bound["material_checksum"] != "AI-CHECKSUM"
    assert bound["created_at"] != "2020-01-01T00:00:00Z"
    assert run_id and run_id.startswith("RUN-AI-")


def test_software_binds_semantic_audit_runtime_envelope(tmp_path) -> None:
    artifacts = []
    for kind, artifact_id in (
        ("research", "R-1"),
        ("evidence_report", "ER-1"),
        ("provisional_thesis", "TP-1"),
        ("analysis", "A-1"),
        ("curation", "C-1"),
        ("refined_thesis", "T-1"),
        ("script_promise", "SP-1"),
    ):
        path = tmp_path / f"{artifact_id}.json"
        path.write_text(json.dumps({"artifact_id": artifact_id}), encoding="utf-8")
        artifacts.append(InputArtifact(kind, artifact_id, path, f"RUN-{artifact_id}"))
    request = ExecutionRequest(
        capability_id="B5_I2_SEMANTIC_AUDITOR",
        skill_id="skill_auditar_suficiencia_semantica_b5_i2",
        skill_version="1.0.0",
        input_artifacts=artifacts,
        output_schema="b5_i2_semantic_sufficiency_audit",
        execution_mode="SYNTHETIC_TEST",
        output_artifact_id="SSA-1",
        episode_id="EP-1",
        role="SCRIPT_PRODUCT_AUDITOR",
        provider="mock",
        model="structural-test-double",
        mock_output={},
    )
    bound, run_id = _bind_runtime_fields(request, {})
    assert bound["audit_id"] == "SSA-1"
    assert bound["auditor_role"] == "SCRIPT_PRODUCT_AUDITOR"
    assert bound["audit_method"] == "AI_SEMANTIC_REVIEW"
    assert len(bound["artifact_checksums"]) == 7
    assert bound["auditor_write_scope"] == "AUDIT_ONLY"
    assert bound["readiness"] == "BLOCKED"
    assert bound["independence_result"] == "BLOCKED"
    assert run_id == bound["auditor_run_id"]


def test_execute_synthetic_b5_i2_validates_projection_then_final_schema(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("src.ai.execution.preflight_controlled_execution", lambda request, root: {"authorization": None, "mission_contract": None})
    research_path = tmp_path / "research.json"
    research_path.write_text(
        json.dumps({"research_id": "R-1", "narrative_evidence": [{"material_id": "M1", "evidence_id": "N1", "statement": "Evidencia concreta"}]}),
        encoding="utf-8",
    )
    evidence_path = tmp_path / "evidence.json"
    evidence_path.write_text('{"report_id":"ER-1"}', encoding="utf-8")
    audit_path = tmp_path / "audit.json"
    audit_path.write_text('{"audit_id":"SSA-1"}', encoding="utf-8")
    cognitive_output = _analysis(material_id="M1", analysis_id="AI-CHOSEN")
    cognitive_output.update({
        "material_function_candidate": "Complicación",
        "specific_scene_or_passage": "Escena concreta donde el personaje cambia una decisión central.",
        "observable_decision_or_action": "El personaje decide sostener la contradicción aun con coste visible.",
        "conflict": "La decisión enfrenta deseo personal y presión social.",
        "consequence": "La consecuencia modifica la lectura del material y la tesis provisional.",
        "main_interpretation": "La escena muestra que el conflicto no se resuelve sin costo moral.",
        "supporting_evidence": ["N1"],
        "interpretive_limit": "La escena no demuestra por sí sola una regla universal.",
        "relationship_to_provisional_thesis": "Confirma la intuición central pero la vuelve más condicional.",
        "potential_contribution_to_progression": "Introduce la primera complicación real del recorrido argumental.",
    })
    request = ExecutionRequest(
        capability_id="B5_I2_SEMANTIC_AUDITOR",
        skill_id="skill_analisis_patrones",
        skill_version="1.0.0",
        input_artifacts=[
            InputArtifact("research", "R-1", research_path, "RUN-R-1"),
            InputArtifact("evidence_report", "ER-1", evidence_path, "RUN-E-1"),
            InputArtifact("semantic_sufficiency_audit", "SSA-1", audit_path, "RUN-A-1"),
        ],
        output_schema="narrative_human_analysis",
        execution_mode="SYNTHETIC_TEST",
        provider="mock",
        output_artifact_id="A-1",
        episode_id="EP-1",
        role="SCRIPT_PRODUCT_PRODUCER",
        mock_output=editorial_only_payload(cognitive_output),
    )
    result = execute(request)

    assert result.status is ExecutionStatus.SUCCEEDED, result.error
    assert result.output["analysis_id"] == "A-1"
    assert result.output["research_id"] == "R-1"
    assert result.output["created_at"] != cognitive_output["created_at"]
    assert validate_against_schema(result.output, "narrative_human_analysis") == []

    request.mock_output = {**request.mock_output, "artifact_version": "9.9.9"}
    rejected = execute(request)
    assert rejected.status is ExecutionStatus.FAILED
    assert "metadata técnica de IA no permitida" in (rejected.error or "")


def test_execute_synthetic_youtube_package_reuses_canonical_handoff(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("src.ai.execution.preflight_controlled_execution", lambda request, root: {"authorization": None, "mission_contract": None})
    artifacts = {}
    payloads = {
        "episode_brief": {"episode_id": "EP-1", "artifact_version": "1.1.0"},
        "refined_thesis": {"thesis_id": "T-1", "artifact_version": "2.2.0"},
        "editorial_script_promise": {"promise_id": "SP-1", "artifact_version": "3.3.0"},
        "evidence_report": {"report_id": "ER-1", "artifact_version": "4.4.0"},
        "claims_ledger": {"ledger_id": "CL-1", "script_version": "5.5.0"},
    }
    for kind, payload in payloads.items():
        path = tmp_path / f"{kind}.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        artifacts[kind] = InputArtifact(kind, payload.get("episode_id") or payload.get("thesis_id") or payload.get("promise_id") or payload.get("report_id") or payload.get("ledger_id"), path, f"RUN-{kind}")

    result = execute(ExecutionRequest(
        capability_id="YT_EARLY_AUDIENCE_FIT",
        skill_id="skill_packaging",
        skill_version="1.0.0",
        input_artifacts=list(artifacts.values()),
        output_schema="youtube_adaptation_b5_i2_package",
        execution_mode="SYNTHETIC_TEST",
        provider="mock",
        mock_output=editorial_only_payload(_valid_package()),
        output_artifact_id="YT-PKG-EXEC",
        role="YOUTUBE_ADAPTATION_PRODUCER",
    ))

    assert result.status is ExecutionStatus.SUCCEEDED, result.error
    references = result.output["input_references"]
    assert set(references) == {
        "episode_brief", "refined_thesis", "editorial_script_promise",
        "evidence_or_claims_reference", "claims_ledger", "evidence_report",
    }
    assert references["episode_brief"]["artifact_id"] == "EP-1"
    assert references["refined_thesis"]["version"] == "2.2.0"
    assert references["editorial_script_promise"]["version"] == "3.3.0"
    assert references["claims_ledger"]["artifact_id"] == "CL-1"
    assert references["evidence_or_claims_reference"] == references["evidence_report"]
    assert validate_against_schema(result.output, "youtube_adaptation_b5_i2_package") == []


def test_execute_synthetic_early_packaging_rebinds_nested_runtime_metadata(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("src.ai.execution.preflight_controlled_execution", lambda request, root: {"authorization": None, "mission_contract": None})
    brief_path = tmp_path / "episode_brief.json"
    brief_path.write_text('{"episode_id":"EP-1","brief_version":"1.1.0"}', encoding="utf-8")
    thesis_path = tmp_path / "refined_thesis.json"
    thesis_path.write_text('{"thesis_id":"T-1","brief_version":"2.2.0"}', encoding="utf-8")
    request = ExecutionRequest(
        capability_id="YT_EARLY_PACKAGING_HYPOTHESIS",
        skill_id="skill_packaging",
        skill_version="1.0.0",
        input_artifacts=[
            InputArtifact("episode_brief", "EP-1", brief_path, "RUN-BRIEF"),
            InputArtifact("refined_thesis", "T-1", thesis_path, "RUN-THESIS"),
        ],
        output_schema="early_packaging_hypothesis",
        execution_mode="SYNTHETIC_TEST",
        provider="mock",
        mock_output=editorial_only_payload(_early_packaging(), "early_packaging_hypothesis"),
        output_artifact_id="PKG-EXEC",
        role="YOUTUBE_ADAPTATION_PRODUCER",
    )

    result = execute(request)

    assert result.status is ExecutionStatus.SUCCEEDED, result.error
    assert result.output["packaging_id"] == "PKG-EXEC"
    assert result.output["refined_thesis_id"] == "T-1"
    assert result.output["status"] == "PROVISIONAL_YOUTUBE_ADAPTATION_INPUT"
    assert result.output["audience"]["brief_checksum"] == __import__("hashlib").sha256(brief_path.read_bytes()).hexdigest()
    assert validate_against_schema(result.output, "early_packaging_hypothesis") == []


def test_execute_synthetic_semantic_audit_preserves_nested_status_and_final_schema(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("src.ai.execution.preflight_controlled_execution", lambda request, root: {"authorization": None, "mission_contract": None})
    paths = _write_case(tmp_path)
    _refresh_b5_i2_audit(paths)
    input_kinds = (
        ("research", "research"),
        ("evidence_report", "evidence"),
        ("provisional_thesis", "provisional"),
        ("analysis", "analysis"),
        ("curation", "curation"),
        ("refined_thesis", "thesis"),
        ("script_promise", "script_promise"),
    )
    artifacts = [
        InputArtifact(kind, "INPUT", paths[path_key], f"RUN-{kind}")
        for kind, path_key in input_kinds
    ]
    request = ExecutionRequest(
        capability_id="B5_I2_SEMANTIC_AUDITOR",
        skill_id="skill_auditar_suficiencia_semantica_b5_i2",
        skill_version="1.0.0",
        input_artifacts=artifacts,
        output_schema="b5_i2_semantic_sufficiency_audit",
        execution_mode="SYNTHETIC_TEST",
        provider="mock",
        mock_output=editorial_only_payload(json.loads(paths["b5_i2_audit"].read_text(encoding="utf-8")), "b5_i2_semantic_sufficiency_audit"),
        output_artifact_id="SSA-EXEC",
        episode_id="EP-001",
        role="SCRIPT_PRODUCT_AUDITOR",
    )

    result = execute(request)

    assert result.status is ExecutionStatus.SUCCEEDED, result.error
    assert result.output["criteria_results"][0]["status"] == "SATISFIED"
    assert result.output["independence_result"] == "BLOCKED"
    assert validate_against_schema(result.output, "b5_i2_semantic_sufficiency_audit") == []


def test_invalid_input_and_missing_role_are_classified() -> None:
    with pytest.raises(RoleExecutionContractError, match="INPUT_CONTRACT_INVALID"):
        resolve_role_execution_contract("SCRIPT_PRODUCT_PRODUCER","execution_smoke_report",[],_runtime_values())
    with pytest.raises(RoleExecutionContractError, match="ROLE_NOT_REGISTERED"):
        resolve_role_execution_contract("UNKNOWN_ROLE","execution_smoke_report",{},_runtime_values())


def test_channel_intelligence_producer_prompt_is_stage_aware() -> None:
    enrichment_payload = {
        "EditorialIntakeHandoff": {"contract": "editorial_intake_handoff"},
        "active_editorial_profile": {"profile_id": "mas_alla_del_guion"},
        "initial_evidence": [],
    }
    enrichment = build_model_prompt(resolve_role_execution_contract(
        "CHANNEL_INTELLIGENCE_PRODUCER",
        "topic_belonging_input",
        enrichment_payload,
        {"stage": "ENRICHMENT", "execution_profile": "codex_current"},
    ))
    producer_payload = {
        "TopicBelongingInput": {"topic_input_id": "TBI-1"},
        "active_editorial_profile": {"profile_id": "mas_alla_del_guion"},
        "initial_evidence": [],
    }
    producer = build_model_prompt(resolve_role_execution_contract(
        "CHANNEL_INTELLIGENCE_PRODUCER",
        "topic_belonging_assessment",
        producer_payload,
        {"stage": "PRODUCER", "execution_profile": "codex_current"},
    ))
    assert '"stage": "ENRICHMENT"' in enrichment
    assert "produce únicamente un `TopicBelongingInput`" in enrichment
    assert '"stage": "PRODUCER"' in producer
    assert "produce únicamente `TopicBelongingAssessment`" in producer


def test_channel_intelligence_stage_input_contracts_are_not_circular() -> None:
    with pytest.raises(RoleExecutionContractError, match="TopicBelongingInput"):
        resolve_role_execution_contract(
            "CHANNEL_INTELLIGENCE_PRODUCER",
            "topic_belonging_assessment",
            {"active_editorial_profile": {}, "initial_evidence": []},
            {"stage": "PRODUCER", "execution_profile": "codex_current"},
        )
    contract = resolve_role_execution_contract(
        "CHANNEL_INTELLIGENCE_PRODUCER",
        "topic_belonging_input",
        {"EditorialIntakeHandoff": {}, "active_editorial_profile": {}, "initial_evidence": []},
        {"stage": "ENRICHMENT", "execution_profile": "codex_current"},
    )
    assert contract["output_schema_name"] == "topic_belonging_input"


def test_ollama_response_parsing_allows_only_documented_fence_cleanup() -> None:
    assert OllamaProvider._parse_response({"response":"```json" + chr(10) + '{"ok": true}' + chr(10) + "```"}) == {"ok":True}
    with pytest.raises(ValueError, match="EMPTY_RESPONSE"): OllamaProvider._parse_response({"response":""})
    with pytest.raises(ValueError, match="INVALID_JSON"): OllamaProvider._parse_response({"response":"not json"})




def test_model_invocation_timeout_is_runtime_block(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    def _raise_timeout(self, request):
        raise RuntimeError("MODEL_INVOCATION_FAILED: TIMEOUT")

    monkeypatch.setattr(OllamaProvider, "execute", _raise_timeout)
    setup_governed_repo(tmp_path, allowed_routes=["local_model"], role_id="SCRIPT_PRODUCT_PRODUCER")
    request = governed_request(tmp_path, execution_route="local_model", execution_profile="ollama_local", provider="ollama")
    request.role = "SCRIPT_PRODUCT_PRODUCER"
    request.output_schema = "execution_smoke_report"
    request.input_artifacts = []
    request.skill_id = "test"
    request.skill_version = "1"
    request.model = "Qwen2.5-Coder:latest"
    request.config["context_policy_path"] = "config/context_resolution_policy.json"
    result = execute(request)
    print("DEBUG_RESULT", result.status, result.error, result.usage)
    assert result.status is ExecutionStatus.BLOCKED_BY_RUNTIME_PROVIDER
    assert result.error == "MODEL_INVOCATION_FAILED: TIMEOUT"

def test_output_contract_invalid_is_not_success(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setattr(OllamaProvider,"execute",lambda self,request: ({"bad":True},{}))
    setup_governed_repo(tmp_path, allowed_routes=["local_model"], role_id="SCRIPT_PRODUCT_PRODUCER")
    request = governed_request(tmp_path, execution_route="local_model", execution_profile="ollama_local", provider="ollama")
    request.role = "SCRIPT_PRODUCT_PRODUCER"
    request.output_schema = "execution_smoke_report"
    request.input_artifacts = []
    request.skill_id = "test"
    request.skill_version = "1"
    request.model = "fake"
    request.config["context_policy_path"] = "config/context_resolution_policy.json"
    result=execute(request)
    print("DEBUG_RESULT", result.status, result.error, result.usage)
    assert result.status.value == "FAILED"
    assert result.error and result.error.startswith("OUTPUT_CONTRACT_INVALID")
