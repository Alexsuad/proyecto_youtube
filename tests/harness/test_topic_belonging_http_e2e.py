"""Software-only E2E coverage for the public Topic Belonging entrypoint.

The test exercises ``src.cli.main`` with the REAL API family and an explicitly
selected provider/model.  The DeepSeek HTTP adapter is real, but the
server is a local pytest-httpserver fixture and returns deterministic
cognitive-only JSON.  No production source is patched and no real AI call is
made.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest
from pytest_httpserver import HTTPServer
from werkzeug.wrappers import Response as WerkzeugResponse

import src.cli as cli
from src.application.topic_belonging import (
    API_PRODUCER_ACTOR_ID,
    API_REVIEWER_ACTOR_ID,
    M1_ALLOWED_EPISODE_ARTIFACTS,
)
from src.scripts.channel_intelligence import canonical_checksum
from tests.harness.test_plan009_m1_vertical import (
    _authority_path_for_authorization,
    _mission_authorization,
)


ROOT = Path(__file__).resolve().parents[2]
FAKE_KEY = "topic-belonging-http-test-key"
FAKE_MODEL = "deepseek-chat"
TOPIC = "La pertenencia cuando una identidad cambia"
QUESTION = "¿Qué revela este conflicto sobre vivir con otros?"
TRIGGERS = {
    "political_partisan_sensitivity": False,
    "high_sensitivity": False,
    "audience_matrix_change": False,
    "excluded_boundary_reinterpretation": False,
    "new_personal_exposure": False,
    "voice_or_author_persona_change": False,
    "positioning_expansion": False,
    "permanent_effect": False,
    "high_precedent_risk": False,
    "experimental_territory": False,
}


def _deepseek_response(content: dict) -> dict:
    return {
        "id": "chatcmpl-topic-belonging-test",
        "object": "chat.completion",
        "created": 1700000000,
        "model": FAKE_MODEL,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": json.dumps(content, ensure_ascii=False),
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30,
            "actual_executor": "FORGED-EXECUTOR-FROM-PROVIDER",
            "actual_provider": "FORGED-PROVIDER-FROM-PROVIDER",
            "actual_model": "FORGED-MODEL-FROM-PROVIDER",
            "execution_route": "FORGED-ROUTE-FROM-PROVIDER",
            "execution_profile": "FORGED-PROFILE-FROM-PROVIDER",
        },
    }


def _cognitive_outputs() -> dict[tuple[str, str], dict]:
    return {
        ("ENRICHMENT", "topic_belonging_cognitive_proposal"): {
            "proposed_angle": "Observar la tensión entre identidad y pertenencia sin convertirla en consejo.",
            "proposed_territory": "Individuo e identidad",
            "initial_evidence": ["fixture://topic-belonging/http-e2e"],
            "strategic_triggers": TRIGGERS,
        },
        ("PRODUCER", "topic_belonging_cognitive_assessment"): {
            "strategic_triggers": TRIGGERS,
            "sensitive_risks": [],
            "territory_classification": "ACTIVE",
            "identity_alignment": "ALIGNED",
            "promise_alignment": "ALIGNED",
            "risks": [],
            "recommended_conditions": [],
            "recommended_exclusions": [],
            "owner_escalation_recommended": False,
            "evidence": ["fixture://topic-belonging/http-e2e-assessment"],
            "status": "CLOSED_FOR_REVIEW",
        },
        ("REVIEWER", "topic_belonging_cognitive_decision"): {
            "decision": "REQUEST_MORE_EVIDENCE",
            "conditions": [],
            "exclusions": [],
            "risks": [],
            "owner_escalation_required": False,
            "owner_escalation_reason": "",
            "strategic_dimensions_affected": [],
            "temporary_or_permanent_effect": "NONE",
            "precedent_risk": "LOW",
            "evidence": ["fixture://topic-belonging/http-e2e-review"],
        },
    }


def test_public_cli_real_profile_reaches_topic_belonging_stop_over_local_http(
    tmp_path: Path,
    httpserver: HTTPServer,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    request: pytest.FixtureRequest,
) -> None:
    """Run CLI -> service -> workflow -> REAL DeepSeek HTTP -> technical stop."""

    outputs = _cognitive_outputs()
    requests: list[dict] = []

    def handler(request):
        body = json.loads(request.data.decode("utf-8"))
        requests.append(
            {
                "method": request.method,
                "path": request.path,
                "authorization": request.headers.get("Authorization"),
                "body": body,
            }
        )
        assert body["model"] == FAKE_MODEL
        assert body["response_format"] == {"type": "json_object"}
        prompt = body["messages"][0]["content"]
        assert prompt
        prompt_payload = json.loads(prompt.split("\n", 1)[1])
        contract = (
            prompt_payload["runtime_values"]["stage"],
            prompt_payload["output_contract"]["schema_name"],
        )
        requests[-1]["contract"] = contract
        assert contract in outputs, f"unexpected cognitive contract: {contract}"
        assert contract not in [item.get("contract") for item in requests[:-1]]
        return WerkzeugResponse(
            response=json.dumps(_deepseek_response(outputs[contract]), ensure_ascii=False),
            status=200,
            content_type="application/json",
        )

    httpserver.expect_request("/chat/completions", method="POST").respond_with_handler(handler)
    monkeypatch.setenv("DEEPSEEK_API_KEY", FAKE_KEY)
    monkeypatch.setenv("DEEPSEEK_MODEL", FAKE_MODEL)
    monkeypatch.setenv("DEEPSEEK_API_BASE", httpserver.url_for(""))

    settings = tmp_path / "settings.json"
    vault_id = hashlib.sha256(str(tmp_path).encode("utf-8")).hexdigest()[:12]
    vault_root = ROOT / ".runtime-tmp" / f"tb-http-e2e-{vault_id}"
    request.addfinalizer(lambda: shutil.rmtree(vault_root, ignore_errors=True))
    settings.write_text(
        json.dumps({"vault_root": str(vault_root), "channel_id": "CHANNEL"}),
        encoding="utf-8",
    )
    family_selection = tmp_path / "execution-family-selection.json"
    family_selection.write_text(
        json.dumps(
            {
                "selection_version": "1.0.0",
                "families": {
                    "AGENT_HARNESS": False,
                    "API_PROVIDER": True,
                },
            }
        ),
        encoding="utf-8",
    )
    family_selection_ref = family_selection.relative_to(ROOT).as_posix()
    mission_auth = _mission_authorization(
        tmp_path,
        execution_interface="TOPIC_BELONGING_TERMINAL",
        execution_mode="REAL",
        execution_profile="deepseek_chat",
        allowed_routes=["api_model"],
    )

    resume_exit_code = None
    tampered_resume_exit_code = None
    try:
        exit_code = cli.main(
            [
                "iniciar",
                "--config",
                str(settings),
                "--mission-authorization",
                mission_auth,
                "--operational-authority",
                _authority_path_for_authorization(mission_auth),
                "--execution-family",
                "API_PROVIDER",
                "--provider",
                "deepseek",
                "--execution-family-selection",
                family_selection_ref,
                "--paid-cost-approved",
                "--modo",
                "tema",
                "--tema",
                TOPIC,
                "--pregunta",
                QUESTION,
            ]
        )
        episode_root = vault_root / "CHANNEL" / "episodios"
        episode_folder = next(episode_root.iterdir())
        episode_id = json.loads((episode_folder / "episode_state.json").read_text(encoding="utf-8"))["episode_id"]
        resume_exit_code = cli.main(
            [
                "reanudar",
                episode_id,
                "--config",
                str(settings),
                "--mission-authorization",
                mission_auth,
                "--operational-authority",
                _authority_path_for_authorization(mission_auth),
                "--execution-family",
                "API_PROVIDER",
                "--provider",
                "deepseek",
                "--execution-family-selection",
                family_selection_ref,
                "--paid-cost-approved",
            ]
        )
        decision_path = episode_folder / "04_topic_belonging_decision.json"
        decision = json.loads(decision_path.read_text(encoding="utf-8"))
        decision["pre_b5_i1_evidence"] = {
            "topic_input_checksum": "f" * 64,
            "research_ref": "FORGED-RESEARCH",
            "narrative_door_evidence_refs": ["FORGED-EVIDENCE"],
            "candidate_work_refs": ["FORGED-WORK"],
        }
        decision["provenance"]["output_checksum"] = canonical_checksum(decision, "decision")
        decision_path.write_text(json.dumps(decision, ensure_ascii=False), encoding="utf-8")
        lineage_path = episode_folder / "topic_belonging_lineage.json"
        lineage = json.loads(lineage_path.read_text(encoding="utf-8"))
        lineage["decision_checksum"] = decision["provenance"]["output_checksum"]
        lineage_path.write_text(json.dumps(lineage, ensure_ascii=False), encoding="utf-8")
        execution_path = episode_folder / "topic_belonging_execution.json"
        execution = json.loads(execution_path.read_text(encoding="utf-8"))
        next(item for item in execution["executions"] if item["stage"] == "REVIEWER")["artifact_checksum"] = decision["provenance"]["output_checksum"]
        execution_path.write_text(json.dumps(execution, ensure_ascii=False), encoding="utf-8")
        tampered_resume_exit_code = cli.main(
            [
                "reanudar",
                episode_id,
                "--config",
                str(settings),
                "--mission-authorization",
                mission_auth,
                "--operational-authority",
                _authority_path_for_authorization(mission_auth),
                "--execution-profile",
                "deepseek_chat",
                "--execution-family-selection",
                family_selection_ref,
                "--paid-cost-approved",
            ]
        )
    finally:
        shutil.rmtree(ROOT / Path(mission_auth).parent, ignore_errors=True)

    httpserver.check()
    assert len(requests) == 3, [item["body"] for item in requests]
    assert all(item["method"] == "POST" for item in requests)
    assert all(item["path"] == "/chat/completions" for item in requests)
    assert all(item["authorization"] == f"Bearer {FAKE_KEY}" for item in requests)
    assert exit_code == 0, capsys.readouterr().out

    assert json.loads((episode_folder / "workflow_state.json").read_text(encoding="utf-8"))["status"] == (
        "TOPIC_BELONGING_TECHNICAL_STOP"
    )
    human_input = json.loads((episode_folder / "00_human_input.json").read_text(encoding="utf-8"))
    topic_input = json.loads((episode_folder / "02_topic_belonging_input.json").read_text(encoding="utf-8"))
    assert human_input["content"] == TOPIC
    assert human_input["initial_question"] == QUESTION
    assert topic_input["topic"] == TOPIC
    assert topic_input["central_question"] == QUESTION
    assert resume_exit_code == 0
    assert tampered_resume_exit_code == 2

    lineage = json.loads((episode_folder / "topic_belonging_lineage.json").read_text(encoding="utf-8"))
    assert lineage["field_ownership"]["USER_PROVIDED"]
    assert "topic" in lineage["field_ownership"]["USER_PROVIDED"]
    assert "central_question" in lineage["field_ownership"]["USER_PROVIDED"]
    assert "topic_input_id" in lineage["field_ownership"]["SOFTWARE_OWNED"]

    executions = json.loads((episode_folder / "topic_belonging_execution.json").read_text(encoding="utf-8"))["executions"]
    assert [item["stage"] for item in executions] == ["ENRICHMENT", "PRODUCER", "REVIEWER"]
    assert all(item["provider_or_adapter"] == "deepseek" for item in executions)
    assert all(item["execution_route"] == "api_model" for item in executions)
    assert all(item["execution_profile"] is None for item in executions)
    assert all(item["provider_kind"] == "REAL" for item in executions)

    assessment = json.loads((episode_folder / "03_topic_belonging_assessment.json").read_text(encoding="utf-8"))
    decision = json.loads((episode_folder / "04_topic_belonging_decision.json").read_text(encoding="utf-8"))
    assert assessment["producer_actor_id"] == API_PRODUCER_ACTOR_ID
    assert assessment["provenance"]["actor_id"] == assessment["producer_actor_id"]
    assert assessment["producer_run_id"] == assessment["provenance"]["run_id"]
    assert assessment["provenance"]["executor_identity"] == "native_provider"
    assert assessment["provenance"]["provider"] == "deepseek"
    assert assessment["provenance"]["model"] == FAKE_MODEL
    assert assessment["artifact_checksum"] == canonical_checksum(assessment, "assessment")
    assert decision["reviewer_actor_id"] == API_REVIEWER_ACTOR_ID
    assert decision["provenance"]["actor_id"] == decision["reviewer_actor_id"]
    assert decision["reviewer_run_id"] == decision["provenance"]["run_id"]
    assert decision["provenance"]["executor_identity"] == "native_provider"
    assert decision["provenance"]["provider"] == "deepseek"
    assert decision["provenance"]["model"] == FAKE_MODEL
    assert decision["producer_artifact_checksum"] == assessment["artifact_checksum"]
    assert decision["provenance"]["output_checksum"] == canonical_checksum(decision, "decision")
    assert assessment["provenance"]["executor_identity"] == decision["provenance"]["executor_identity"]
    assert not assessment["provenance"]["executor_identity"].startswith("AGENT_HARNESS_EXTERNAL_")
    assert assessment["producer_run_id"] != decision["reviewer_run_id"]
    assert assessment["producer_actor_id"] != decision["reviewer_actor_id"]

    assert set(path.name for path in episode_folder.iterdir()) == set(M1_ALLOWED_EPISODE_ARTIFACTS)
    assert not any(
        (episode_folder / name).exists()
        for name in (
            "episode_brief.json",
            "research_pack.json",
            "thesis_provisional.json",
            "script.json",
        )
    )
