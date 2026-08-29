from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.ai.contracts import ExecutionRequest, ExecutionStatus
from src.ai.execution import execute
from src.ai.providers.ollama import OllamaProvider
from src.ai.role_execution import RoleExecutionContractError, build_model_prompt, resolve_role_execution_contract
from tests.core.test_plan_005_real_consumer_integration import _request as governed_request, _setup as setup_governed_repo


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
