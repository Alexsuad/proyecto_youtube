"""Focal synthetic boundary tests for PLAN011 M3/B5-I3."""
from __future__ import annotations

import hashlib
import json
import runpy
from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import pytest

from src.ai.contracts import ExecutionRequest, ExecutionStatus, InputArtifact
from src.ai.execution import M3_CANONICAL_ID_FIELDS, editorial_only_payload, execute
from src.ai.role_execution import build_model_prompt, resolve_role_execution_contract
from src.application.contracts import HumanInput
from src.application.storage import StorageError, VaultEpisodeStore
from src.core.contract_validation import validate_against_schema
from src.core.duration_envelope import resolve_narrative_budget


EPISODE = "EP-M3-001"
_CANONICAL_FIXTURES = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "core" / "test_all_schemas.py")
)["VALID_FIXTURES"]


def _write(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def _inputs(tmp_path: Path, episode_id: str = EPISODE, duration_target: int | None = 15) -> list[InputArtifact]:
    human_payload = deepcopy(_CANONICAL_FIXTURES["human_episode_input"])
    human_payload.update({
        "duration_target_minutes": duration_target,
        "target_language": "es",
        "user_instructions": [{"category": "MUST_INCLUDE_VERBATIM", "text": "Conservar esta indicación."}],
    })
    human = _write(tmp_path / "human_input.json", human_payload)
    artifacts = [InputArtifact("human_input", human_payload["interaction_id"], human, "RUN-INPUT")]
    profile = _write(
        tmp_path / "active_editorial_profile_reference.json",
        json.loads((Path(__file__).resolve().parents[2] / "config" / "active_editorial_profile.json").read_text(encoding="utf-8")),
    )
    artifacts.append(InputArtifact("active_editorial_profile_reference", "PROFILE-REF-M3", profile, "RUN-PROFILE"))
    for kind, fixture_key in (
        ("episode_brief", "episode_brief"), ("research_pack", "research_pack"),
        ("claims_ledger", "claims_ledger"), ("source_access_and_evidence_report", "source_access_and_evidence_report"),
        ("narrative_human_analysis", "narrative_human_analysis"), ("material_curation", "material_curation"),
        ("refined_thesis", "refined_thesis"), ("editorial_script_promise", "editorial_script_promise"),
        ("early_packaging_hypothesis", "early_packaging_hypothesis"),
        ("b5_i2_semantic_audit", "b5_i2_semantic_sufficiency_audit"),
        ("youtube_adaptation_review", "youtube_adaptation_review"),
    ):
        payload = deepcopy(_CANONICAL_FIXTURES[fixture_key])
        if "episode_id" in payload:
            payload["episode_id"] = episode_id
        canonical_id_field = M3_CANONICAL_ID_FIELDS.get(kind)
        artifact_id = str(payload[canonical_id_field]) if canonical_id_field else "EPISODE_BRIEF_REFERENCE-M3"
        path = _write(tmp_path / f"{kind}.json", payload)
        artifacts.append(InputArtifact(kind, artifact_id, path, f"RUN-{kind}"))
    return artifacts


def _cognitive(schema: str) -> dict:
    if schema == "viewer_journey":
        return {
            "estado_inicial_del_espectador": "Llega con una intuición simple.",
            "creencia_inicial_probable": "El conflicto parece individual.",
            "pregunta_que_lo_mantiene": "¿Qué cambia cuando aparece el contexto?",
            "primer_descubrimiento": "La decisión tiene un costo visible.",
            "complicacion": "El entorno limita las opciones.",
            "cambio_de_perspectiva": "La responsabilidad deja de parecer aislada.",
            "tension_principal": "Agencia personal frente a condiciones compartidas.",
            "revelacion_o_payoff": "La contradicción explica el resultado sin volverlo universal.",
            "estado_final_del_espectador": "Puede leer el conflicto con más matiz.",
            "blocks": [{
                "block_id": "OPEN", "que_sabe_antes": "Intuición inicial", "que_sabe_despues": "Ve el costo",
                "que_siente_o_cuestiona": "Cuestiona su explicación", "por_que_quiere_continuar": "Falta el contexto",
                "promesa_parcial_resuelta": "Se confirma la tensión", "pregunta_abierta": "¿Qué la produce?",
            }],
        }
    if schema == "opening_design":
        return {
            "hook_function": "Abrir una tensión concreta.", "opening_question": "¿Qué estamos dejando fuera?",
            "initial_tension": "Una decisión parece libre y condicionada.", "minimum_context": "Presentar la escena y su situación.",
            "early_payoff": "Mostrar pronto la consecuencia observable.", "promise": "Seguir el cambio de perspectiva.",
            "first_transition": "Pasar de la escena al contexto.", "word_budget": 180, "risks": ["No sobregeneralizar."],
        }
    if schema == "closing_design":
        return {
            "central_question_answer": "La decisión también revela sus condiciones.",
            "thesis_payoff": "La tesis queda demostrada con su límite.",
            "opening_callback": "Retomar la primera pregunta desde otra perspectiva.",
            "final_image_or_idea": "Una puerta que no estaba cerrada ni completamente abierta.",
            "emotional_resolution": "La incertidumbre queda situada, no eliminada.",
            "cta_strategy": "NONE", "new_ideas_prohibited": True, "word_budget": 270,
        }
    return {
        "script_type": "VIDEO_ESSAY", "thesis": "La decisión individual se entiende mejor al mirar su contexto.",
        "main_objection": "No toda decisión responde al mismo patrón.", "nuance": "La lectura depende de condiciones observables.",
        "promise": "Examinar una decisión sin simplificarla.", "viewer_journey_ref": "pending", "opening_design_ref": "pending",
        "closing_design_ref": "pending", "climax": "La contradicción cambia la lectura inicial.",
        "blocks": [
            {"block_id": "B1", "function": "ADD", "central_question": "¿Qué ocurre?", "new_information": "La escena concreta.", "emotional_or_intellectual_change": "Aparece el conflicto.", "source_refs": ["narrative_human_analysis:ANALYSIS-M3"], "word_budget": 700, "entry_transition": "Desde la apertura.", "exit_transition": "Abrir el contexto.", "must_not_repeat": "La descripción inicial.", "prepares_next": "El costo.", "viewer_state_before": "Intuición.", "viewer_state_after": "Conflicto visible.", "partial_payoff": "La escena aclara la tensión.", "open_question": "¿Qué la condiciona?"},
            {"block_id": "B2", "function": "COMPLICATE", "central_question": "¿Qué queda fuera?", "new_information": "El entorno modifica las opciones.", "emotional_or_intellectual_change": "La explicación se vuelve menos simple.", "source_refs": ["material_curation:CURATION-M3"], "word_budget": 800, "entry_transition": "Desde el costo.", "exit_transition": "Hacia la contradicción.", "must_not_repeat": "La escena base.", "prepares_next": "El límite de la tesis.", "viewer_state_before": "Busca una causa.", "viewer_state_after": "Acepta condiciones.", "partial_payoff": "Se explica la complicación.", "open_question": "¿Qué interpretación resiste?"},
            {"block_id": "B3", "function": "TRANSFORM", "central_question": "¿Cómo cambia la lectura?", "new_information": "La contradicción permanece.", "emotional_or_intellectual_change": "La tesis se vuelve situada.", "source_refs": ["refined_thesis:THESIS-M3"], "word_budget": 750, "entry_transition": "Desde la objeción.", "exit_transition": "Hacia el cierre.", "must_not_repeat": "La explicación causal universal.", "prepares_next": "La respuesta final.", "viewer_state_before": "Considera alternativas.", "viewer_state_after": "Integra matiz.", "partial_payoff": "La tesis se limita y se sostiene.", "open_question": "¿Qué aprendimos?"},
        ],
    }


def _convergence_callbacks() -> dict[str, object]:
    def passed(stage: str) -> dict[str, object]:
        return {"passed": True, "evidence": [{"kind": "M3_SYNTHETIC_TEST", "ref": stage}]}

    return {
        "implement": lambda: passed("IMPLEMENT"),
        "verify": lambda: passed("VERIFY"),
        "adversarial_review": lambda: passed("SELF_ADVERSARIAL_REVIEW"),
        "repair": lambda finding: passed("REPAIR"),
    }


def _mission_config() -> dict[str, object]:
    return {
        "repository_root": str(Path(__file__).resolve().parents[2]),
        "mission_authorization_path": "plans/plan_011/m3_b5_i3/mission-authorization.json",
        "mission_contract_path": "plans/plan_011/m3_b5_i3/mission_contract.json",
        "execution_interface": "PLAN011_M3_B5_I3_SYNTHETIC",
        "mission_operation": "EXECUTE_CAPABILITY",
        "execution_route": "synthetic",
        "convergence_callbacks": _convergence_callbacks(),
    }


def _execute_with_inputs(tmp_path: Path, schema: str, inputs: list[InputArtifact], episode_id: str = EPISODE):
    request = ExecutionRequest(
        capability_id="B5_I3_NARRATIVE_ARCHITECTURE", skill_id="skill_mapa_eventos_y_outline", skill_version="1.0.0",
        input_artifacts=inputs, output_schema=schema, execution_mode="SYNTHETIC_TEST", provider="mock",
        mock_output=editorial_only_payload(_cognitive(schema), schema), output_artifact_id=f"{schema.upper()}-M3",
        episode_id=episode_id, role="NARRATIVE_ARCHITECTURE", config={"wpm_target": 150, **_mission_config()},
    )
    return execute(request)


def _execute(tmp_path: Path, schema: str, episode_id: str = EPISODE, duration_target: int | None = 15):
    tmp_path.mkdir(parents=True, exist_ok=True)
    request = ExecutionRequest(
        capability_id="B5_I3_NARRATIVE_ARCHITECTURE", skill_id="skill_mapa_eventos_y_outline", skill_version="1.0.0",
        input_artifacts=_inputs(tmp_path, episode_id, duration_target), output_schema=schema, execution_mode="SYNTHETIC_TEST", provider="mock",
        mock_output=editorial_only_payload(_cognitive(schema), schema), output_artifact_id=f"{schema.upper()}-M3",
        episode_id=episode_id, role="NARRATIVE_ARCHITECTURE",
        config={"wpm_target": 150, **_mission_config()},
    )
    return execute(request)


@pytest.mark.parametrize("schema", ["viewer_journey", "opening_design", "closing_design", "narrative_plan"])
def test_final_schemas_are_valid_and_software_owns_runtime_fields(tmp_path: Path, schema: str) -> None:
    result = _execute(tmp_path, schema)
    assert result.status is ExecutionStatus.SUCCEEDED, result.error
    assert validate_against_schema(result.output or {}, schema) == []
    output = result.output or {}
    assert output["episode_id"] == EPISODE
    assert output["checksum"] == hashlib.sha256(
        json.dumps({key: value for key, value in output.items() if key != "checksum"}, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def test_m2_inputs_preserved_and_cognitive_boundary_isolated(tmp_path: Path) -> None:
    result = _execute(tmp_path, "narrative_plan")
    assert result.status is ExecutionStatus.SUCCEEDED, result.error
    plan = result.output or {}
    assert plan["duration_target_minutes"] == 15
    assert plan["target_language"] == "es"
    assert plan["user_instructions"][0]["text"] == "Conservar esta indicación."
    assert plan["word_budget_total"] == 2250
    assert plan["lineage"]["generated_by"] == "SOFTWARE"
    assert {item["function"] for item in plan["blocks"]} == {"ADD", "COMPLICATE", "TRANSFORM"}


def test_cognitive_output_that_writes_protected_fields_is_rejected(tmp_path: Path) -> None:
    request = ExecutionRequest(
        capability_id="B5_I3_NARRATIVE_ARCHITECTURE", skill_id="skill_mapa_eventos_y_outline", skill_version="1.0.0",
        input_artifacts=_inputs(tmp_path), output_schema="viewer_journey", execution_mode="SYNTHETIC_TEST", provider="mock",
        mock_output={**_cognitive("viewer_journey"), "episode_id": "AI-CHANGED"}, output_artifact_id="VJ-M3",
            episode_id=EPISODE, role="NARRATIVE_ARCHITECTURE",
            config=_mission_config(),
    )
    result = execute(request)
    assert result.status is ExecutionStatus.FAILED
    assert "metadata técnica de IA no permitida" in (result.error or "")


def test_m3_requires_the_canonical_input_set(tmp_path: Path) -> None:
    request = ExecutionRequest(
        capability_id="B5_I3_NARRATIVE_ARCHITECTURE", skill_id="skill_mapa_eventos_y_outline", skill_version="1.0.0",
        input_artifacts=[], output_schema="viewer_journey", execution_mode="SYNTHETIC_TEST", provider="mock",
        mock_output=editorial_only_payload(_cognitive("viewer_journey"), "viewer_journey"), output_artifact_id="VJ-M3",
        episode_id=EPISODE, role="NARRATIVE_ARCHITECTURE", config=_mission_config(),
    )
    result = execute(request)
    assert result.status is ExecutionStatus.FAILED
    assert "inputs canónicos ausentes" in (result.error or "")


@pytest.mark.parametrize(
    ("kind", "payload", "expected_error"),
    [
        ("research_pack", "{not-json", "JSON inválido"),
        ("research_pack", '{"research_id":"RP-001"}', "schema inválido"),
    ],
)
def test_invalid_canonical_input_fails_closed(tmp_path: Path, kind: str, payload: object, expected_error: str) -> None:
    inputs = _inputs(tmp_path)
    target = next(item for item in inputs if item.artifact_kind == kind)
    if isinstance(payload, str):
        target.path.write_text(payload, encoding="utf-8")
    else:
        target.path.write_text(json.dumps(payload), encoding="utf-8")
    result = _execute_with_inputs(tmp_path, "viewer_journey", inputs)
    assert result.status is ExecutionStatus.FAILED
    assert expected_error in (result.error or "")


def test_canonical_input_episode_binding_fails_closed(tmp_path: Path) -> None:
    inputs = _inputs(tmp_path)
    target = next(item for item in inputs if item.artifact_kind == "research_pack")
    payload = deepcopy(_CANONICAL_FIXTURES["research_pack"])
    payload["episode_id"] = "OTHER-EP"
    target.path.write_text(json.dumps(payload), encoding="utf-8")
    result = _execute_with_inputs(tmp_path, "viewer_journey", inputs)
    assert result.status is ExecutionStatus.FAILED
    assert "episode_id inconsistente" in (result.error or "")


@pytest.mark.parametrize("kind", ["refined_thesis", "material_curation"])
def test_canonical_artifact_id_mismatch_fails_closed(tmp_path: Path, kind: str) -> None:
    inputs = _inputs(tmp_path)
    index = next(index for index, item in enumerate(inputs) if item.artifact_kind == kind)
    inputs[index] = replace(inputs[index], artifact_id="WRONG-ID")
    result = _execute_with_inputs(tmp_path, "viewer_journey", inputs)
    assert result.status is ExecutionStatus.FAILED
    assert result.error == f"OUTPUT_BINDING_INVALID: B5_I3_CANONICAL_ARTIFACT_ID_MISMATCH:{kind}"


@pytest.mark.parametrize(("duration", "expected_total"), [(15, 2250), (20, 3000), (17, 2550)])
def test_duration_budget_is_deterministic_for_positive_targets(duration: int, expected_total: int) -> None:
    result = resolve_narrative_budget(duration, wpm_target=150)
    assert result == {"duration_target_minutes": duration, "wpm_target": 150, "word_budget_total": expected_total}


@pytest.mark.parametrize("duration", [0, -1])
def test_invalid_duration_fails_closed(duration: int) -> None:
    with pytest.raises(ValueError, match="entero positivo"):
        resolve_narrative_budget(duration)


def test_automatic_duration_remains_unresolved_and_blocks_numeric_plan(tmp_path: Path) -> None:
    assert resolve_narrative_budget(None) == {"duration_target_minutes": None, "wpm_target": 150, "word_budget_total": None}
    result = _execute(tmp_path, "narrative_plan", duration_target=None)
    assert result.status is ExecutionStatus.FAILED
    assert "STOP_LOCAL_DURATION_UNRESOLVED" in (result.error or "")


def test_role_prompt_exposes_cognitive_contract_only() -> None:
    payload = {key: {} for key in (
        "active_editorial_profile_reference", "episode_brief", "research_pack", "claims_ledger",
        "source_access_and_evidence_report", "narrative_human_analysis", "material_curation", "refined_thesis",
        "editorial_script_promise", "early_packaging_hypothesis", "b5_i2_semantic_audit", "youtube_adaptation_review",
        "user_instructions", "target_duration", "target_language",
    )}
    contract = resolve_role_execution_contract("NARRATIVE_ARCHITECTURE", "narrative_plan", payload, {"stage": "M3"})
    prompt = build_model_prompt(contract)
    assert '"checksum"' not in contract["output_schema"]["properties"]
    assert "viewer_journey" in prompt and "narrative_plan" in prompt


def test_narrative_architecture_is_proposal_only() -> None:
    root = Path(__file__).resolve().parents[2]
    prompt_entry = next(
        item for item in json.loads((root / "config" / "agent_prompt_registry.json").read_text(encoding="utf-8"))["prompts"]
        if item["role_id"] == "NARRATIVE_ARCHITECTURE"
    )
    responsibility_entry = next(
        item for item in json.loads((root / "config" / "responsibility_registry.json").read_text(encoding="utf-8"))["responsibilities"]
        if item["role_id"] == "NARRATIVE_ARCHITECTURE"
    )
    assert "ThesisArtifact" not in prompt_entry["authority"]
    assert "thesis_artifact" not in responsibility_entry["outputs"]
    assert "viewer_journey_proposal" in prompt_entry["required_outputs"]
    assert "NarrativePlanProposal" in responsibility_entry["outputs"]
    assert any("RefinedThesis" in item for item in responsibility_entry["read_permissions"])
    assert any("refinar RefinedThesis" in item for item in responsibility_entry["forbidden_actions"])


def test_persistence_recovery_and_dependency_invalidation(tmp_path: Path) -> None:
    (tmp_path / "CHANNEL").mkdir()
    store = VaultEpisodeStore(tmp_path, "CHANNEL")
    human = HumanInput.create(mode="TOPIC_FIRST", content="Tema M3", duration_target_minutes=15, target_language="es")
    handle = store.create_episode(human, handoff={"target_contract": "editorial_intake_handoff"}, profile={"ACTIVE_PROFILE_ID": "mas_alla_del_guion", "ACTIVE_PROFILE_VERSION": "1.2.2", "profile_checksum": "a" * 64}, run_id="RUN-M3")
    artifacts = {schema: _execute(tmp_path / "artifacts", schema, handle.episode_id).output for schema in ("viewer_journey", "opening_design", "closing_design", "narrative_plan")}
    dependency = tmp_path / "refined_thesis.json"
    dependency.write_text("approved-v1", encoding="utf-8")
    snapshot = [{"artifact_id": "THESIS-M3", "checksum": hashlib.sha256(dependency.read_bytes()).hexdigest(), "artifact_path": str(dependency)}]
    manifest = store.record_b5_i3_design(handle, artifacts=artifacts, dependency_snapshot=snapshot)
    recovered = store.recover_b5_i3_design(handle)
    assert manifest["status"] == recovered["status"] == "PERSISTED"
    assert recovered["artifacts"]["narrative_plan"]["script_plan_id"] == "NARRATIVE_PLAN-M3"
    dependency.write_text("approved-v2", encoding="utf-8")
    with pytest.raises(StorageError, match="B5_I3_DESIGN_INVALIDATED"):
        store.recover_b5_i3_design(handle)
