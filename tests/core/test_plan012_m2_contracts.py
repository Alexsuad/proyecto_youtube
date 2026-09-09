from copy import deepcopy

import pytest

from src.application.contracts import HumanInput
from src.application.research_planning import ResearchPlanningService
from src.application.research_b2 import ResearchB2Persistence
from src.application.storage import VaultEpisodeStore
from src.core.editorial_profile_registry import load_active_profile_authority
from src.ai.role_execution import RoleExecutionContractError, resolve_role_execution_contract
from src.core.contract_validation import (
    validate_against_schema,
    validate_claims_ledger,
    validate_research_pack,
    validate_research_plan,
    validate_research_ready_manifest,
    validate_source_access_and_evidence_report,
)
from tests.core.test_all_schemas import VALID_FIXTURES


def test_research_plan_is_explicit_and_has_no_silent_three_work_default() -> None:
    plan = deepcopy(VALID_FIXTURES["research_plan"])
    assert validate_research_plan(plan) == []
    assert plan["target_final_works_decision"]["requested_count"] == 4

    plan["target_final_works_decision"] = {
        "status": "CONFIRMED",
        "requested_count": None,
        "decision_basis": "Sin cantidad explícita.",
        "decision_ref": "DEC-1",
    }
    assert validate_research_plan(plan)

    plan = deepcopy(VALID_FIXTURES["research_plan"])
    plan["dimensions"] = []
    assert validate_research_plan(plan)


def test_research_plan_uses_claim_specific_evidence_dimensions_without_universal_taxonomy() -> None:
    plan = deepcopy(VALID_FIXTURES["research_plan"])
    plan["evidence_requirements"][0].update({
        "minimum_strength": "primary record appropriate to the claim",
        "claim_specific_basis": "Identity, reproducible locator and correspondence with the statement.",
        "required_evidence_properties": ["identity", "locator", "claim_alignment"],
        "disqualifying_conditions": ["unresolvable source"],
    })
    plan["critical_claims"][0].update({
        "strength": "descriptive within declared scope",
        "claim_dimensions": {
            "nature": "descriptive observation",
            "scope": "declared corpus only",
            "contestation": "open to rival explanation",
            "conditions": ["no causal generalization"],
        },
    })
    assert validate_research_plan(plan) == []


def test_intake_keeps_research_role_and_editorial_intent_separate() -> None:
    without_research_fields = HumanInput.create(mode="tema", content="Fenómeno").to_dict()
    assert "research_role" not in without_research_fields
    assert "editorial_intent" not in without_research_fields
    assert validate_against_schema(without_research_fields, "human_episode_input") == []

    explicit = HumanInput.create(
        mode="tema",
        content="Fenómeno",
        research_role="ANCLA",
        editorial_intent="PREFERIDA",
    ).to_dict()
    assert explicit["research_role"] == "ANCLA"
    assert explicit["editorial_intent"] == "PREFERIDA"
    assert validate_against_schema(explicit, "human_episode_input") == []


def test_pre_research_planning_builds_separate_context_and_source_access() -> None:
    profile = load_active_profile_authority()
    service = ResearchPlanningService()
    brief = service.build_episode_brief(episode_id="EP-PLAN", topic="Tema", question="Pregunta", intended_use="Uso de prueba explícito", profile=profile)
    context = service.build_channel_context(episode_id="EP-PLAN", profile=profile, origin_ref="profile:EP-PLAN")
    source_access = service.build_source_access(episode_id="EP-PLAN", brief_version=brief["brief_version"], materials=[], origin_refs=["human:EP-PLAN"])
    assert brief["brief_stage"] == "PRE_RESEARCH"
    assert context["episode_id"] == "EP-PLAN"
    assert source_access["contract"] == "research_source_access"
    assert source_access["capabilities"]["web_search"] == "UNAVAILABLE"


@pytest.mark.parametrize("selection_authority", ["OWNER_DECIDES", "DELEGATED_TO_RESEARCH"])
def test_pre_research_topic_only_preserves_owner_authority_without_inventing_work(selection_authority: str) -> None:
    profile = load_active_profile_authority()
    brief = ResearchPlanningService().build_episode_brief(
        episode_id="EP-TOPIC-ONLY",
        topic="Fenómeno sin obra suministrada",
        question="¿Qué debemos investigar?",
        intended_use="Delimitar el alcance solicitado por el OWNER.",
        profile=profile,
        selection_authority=selection_authority,
        material_refs=["owner:doc"],
        owner_restrictions=["No inferir una obra no suministrada"],
    )
    assert brief["narrative_materials"] == []
    assert brief["work_intents"] == []
    assert brief["selection_authority"] == selection_authority
    assert brief["owner_material_refs"] == ["owner:doc"]
    assert brief["owner_restrictions"] == ["No inferir una obra no suministrada"]
    assert brief["initial_question"] == "¿Qué debemos investigar?"
    assert brief["objetivo"] == "Delimitar el alcance solicitado por el OWNER."


def test_pre_research_channel_context_projects_canonical_audience_hypotheses() -> None:
    profile = load_active_profile_authority()
    context = ResearchPlanningService().build_channel_context(
        episode_id="EP-AUDIENCE",
        profile=profile,
        origin_ref="human:EP-AUDIENCE",
    )
    assert "AUDIENCE_HYPOTHESIS_INITIAL" in context["audience_context"]
    assert "Utilizar historias" in context["editorial_purpose"]
    assert context["profile_checksum"] == profile["profile_checksum"]


def test_owner_material_is_snapshotted_checksum_bound_and_exposed_in_source_access(tmp_path) -> None:
    import shutil
    from uuid import uuid4
    from pathlib import Path

    profile = load_active_profile_authority()
    # Keep the path short enough for Windows when the snapshot filename
    # includes its full SHA-256 digest.
    isolated_root = Path.cwd() / f"m2b1-{uuid4().hex[:8]}"
    isolated_root.mkdir(parents=True, exist_ok=False)
    try:
        store = VaultEpisodeStore(isolated_root / "vault", "MAS_ALLA_DEL_GUION")
        handle = store.create_episode(
            HumanInput.create(mode="tema", content="Tema con material"),
            handoff={},
            profile=profile,
            run_id="RUN-PRE-RESEARCH",
        )
        source = isolated_root / "owner.md"
        source.write_text("# Evidencia local\n", encoding="utf-8")
        (handle.folder / "research_materials").mkdir(parents=True, exist_ok=True)
        records = store.materialize_owner_materials(handle, source_paths=[source])
        assert len(records) == 1
        record = records[0]
        snapshot = handle.folder / record["artifact_ref"]
        assert snapshot.is_file()
        assert record["checksum"] == __import__("hashlib").sha256(snapshot.read_bytes()).hexdigest()
        provenance = handle.folder / "research_material_provenance.json"
        assert provenance.is_file()
        access = ResearchPlanningService().build_source_access(
            episode_id=handle.episode_id,
            brief_version="2.0.0",
            materials=records,
            origin_refs=["human:EP-MATERIAL"],
        )
        assert access["capabilities"]["owner_material_ingestion"] == "AVAILABLE"
        assert access["materials"][0]["availability"] == "AVAILABLE_LOCAL"
    finally:
        shutil.rmtree(isolated_root, ignore_errors=True)


def test_b1_registry_and_prompt_remain_non_executable_and_pre_b2() -> None:
    import json
    from pathlib import Path

    registry = json.loads(Path("config/capability_registry.json").read_text(encoding="utf-8"))
    capability = next(item for item in registry["capabilities"] if item["capability_id"] == "EXTEND_01_RESEARCH_V2_REAL_E2E")
    assert capability["availability_status"] == "NON_EXECUTABLE_CURRENT"
    assert capability["executability_evidence"]["context_resolvable"] is True
    assert capability["executability_evidence"]["real_b2_input_binding_available"] is True
    prompt_registry = json.loads(Path("config/agent_prompt_registry.json").read_text(encoding="utf-8"))
    prompt = next(item for item in prompt_registry["prompts"] if item["role_id"] == "RESEARCH_AND_CURATION")
    assert prompt["prompt_version"] == "1.1.0"
    assert "Research V2" in prompt["authority"]


def test_research_planning_role_requires_all_pre_research_inputs() -> None:
    payload = {
        "topic": "Fenómeno de prueba",
        "source_access": {"contract": "research_source_access"},
        "brief": {"brief_id": "BRIEF-1"},
        "channel_context": {"channel_id": "CHANNEL-1"},
    }
    contract = resolve_role_execution_contract(
        "RESEARCH_AND_CURATION", "research_plan_proposal", payload, {"stage": "RESEARCH_PLANNING"}
    )
    assert contract["output_schema_name"] == "research_plan_proposal"
    for missing in payload:
        incomplete = dict(payload)
        incomplete.pop(missing)
        with pytest.raises(RoleExecutionContractError, match="INPUT_CONTRACT_INVALID"):
            resolve_role_execution_contract(
                "RESEARCH_AND_CURATION", "research_plan_proposal", incomplete, {"stage": "RESEARCH_PLANNING"}
            )


def test_research_prompt_1_1_is_a_superset_of_1_0() -> None:
    from pathlib import Path

    legacy = Path("prompts/roles/RESEARCH_AND_CURATION/1.0.0.md").read_text(encoding="utf-8")
    current = Path("prompts/roles/RESEARCH_AND_CURATION/1.1.0.md").read_text(encoding="utf-8")
    assert "RESEARCH_PLANNING" in current
    for line in legacy.splitlines():
        if line.strip() and not line.startswith("# RESEARCH_AND_CURATION"):
            assert line in current


def test_research_planning_binds_lightweight_proposal_to_canonical_plan() -> None:
    proposal = deepcopy(VALID_FIXTURES["research_plan_proposal"])
    plan = ResearchPlanningService().bind_research_plan(
        proposal, episode_id="EP-PLAN", brief_version="2.0.0", research_role="NORMAL", editorial_intent="NO_DECLARADA", origin_ref="brief:EP-PLAN"
    )
    assert validate_research_plan(plan) == []
    assert plan["contract"] == "research_plan"
    assert plan["origin"]["source_kind"] == "EPISODE_BRIEF"


def test_research_planning_productive_producer_binds_and_persists_with_injected_executor(tmp_path) -> None:
    profile = load_active_profile_authority()
    service = ResearchPlanningService()
    brief = service.build_episode_brief(
        episode_id="EP-PLAN-PRODUCER", topic="Tema", question="Pregunta",
        intended_use="Uso explícito", profile=profile,
    )
    channel_context = service.build_channel_context(
        episode_id=brief["episode_id"], profile=profile, origin_ref="profile:EP-PLAN-PRODUCER",
    )
    source_access = service.build_source_access(
        episode_id=brief["episode_id"], brief_version=brief["brief_version"],
        materials=[], origin_refs=["human:EP-PLAN-PRODUCER"],
    )
    seen = []

    def cognitive(request):
        seen.append(request)
        return deepcopy(VALID_FIXTURES["research_plan_proposal"])

    result = service.produce_research_plan(
        episode_brief=brief,
        channel_context=channel_context,
        source_access=source_access,
        cognitive_executor=cognitive,
        persistence=ResearchB2Persistence(tmp_path),
        research_role="NORMAL",
        editorial_intent="NO_DECLARADA",
    )
    assert [request.stage for request in seen] == ["RESEARCH_PLANNING"]
    assert seen[0].prepared_contract["output_schema_name"] == "research_plan_proposal"
    assert result["research_plan_proposal"]["artifact_kind"] == "ResearchPlanProposal"
    assert result["research_plan"]["artifact_kind"] == "ResearchPlan"
    assert validate_research_plan(result["research_plan_payload"]) == []
    assert result["research_plan_payload"]["origin_artifact_refs"][0]["checksum"] == result["research_plan_proposal"]["checksum"]


def test_claims_ledger_can_exist_before_script() -> None:
    ledger = deepcopy(VALID_FIXTURES["claims_ledger"])
    ledger.pop("script_version")
    ledger.update({
        "contract_version": "2.0.0",
        "ledger_stage": "RESEARCH_PRE_SCRIPT",
        "research_id": "R-1",
        "episode_id": "EP-1",
        "artifact_version": "2.0.0",
    })
    for claim in ledger["claims"]:
        claim.pop("script_location", None)
    assert validate_claims_ledger(ledger) == []

    ledger["claims"][0]["script_location"] = "script.md#1"
    assert validate_claims_ledger(ledger)


def test_research_pack_v2_separates_evidence_and_states() -> None:
    research = deepcopy(VALID_FIXTURES["research_pack"])
    research.pop("narrative_opportunities", None)
    research.pop("editorial_uses", None)
    research.update({
        "research_contract_version": "2.0.0",
        "research_stage": "DEEP_RESEARCH",
        "research_sufficiency": "LIMITED_BUT_USABLE",
        "artifact_validity": "VALID",
        "thesis_stage": "PROVISIONAL",
        "evidence_type_separation": {
            "work_evidence_refs": ["WORK-1"],
            "external_reality_evidence_refs": ["EXT-1"],
        },
        "acquisition_bindings": [{
            "request_ref": "REQ-1",
            "execution_ref": "EXEC-1",
            "recovery_artifact_ref": "recovery:S-1",
            "source_ref": "S1",
            "retrieval_status": "RECOVERED",
            "evidence_status": "VERIFIED",
            "software_controlled": True,
        }],
    })
    research["source_registry"][0].update({
        "evidence_status": "VERIFIED",
        "retrieval_status": "RECOVERED",
        "recovery_artifact_ref": "recovery:S1",
    })
    assert validate_research_pack(research) == []

    research["acquisition_bindings"][0].update({"recovery_artifact_ref": None, "retrieval_status": "NOT_RECOVERED"})
    assert validate_research_pack(research)


def _v2_source_report() -> dict:
    report = deepcopy(VALID_FIXTURES["source_access_and_evidence_report"])
    report.update({
        "research_contract_version": "2.0.0",
        "research_stage": "DEEP_RESEARCH",
        "research_sufficiency": "LIMITED_BUT_USABLE",
        "artifact_validity": "VALID",
        "thesis_stage": "PROVISIONAL",
        "evidence_type_separation": {"work_evidence_refs": ["WORK-1"], "external_reality_evidence_refs": ["EXT-1"]},
        "acquisition_bindings": [{
            "request_ref": "REQ-1",
            "execution_ref": "EXEC-1",
            "recovery_artifact_ref": "recovery:S1",
            "source_ref": "S1",
            "retrieval_status": "RECOVERED",
            "evidence_status": "VERIFIED",
            "software_controlled": True,
        }],
    })
    report["fuentes_primarias"][0].update({
        "evidence_status": "VERIFIED",
        "retrieval_status": "RECOVERED",
        "recovery_artifact_ref": "recovery:S1",
    })
    return report


@pytest.mark.parametrize("kind", ["research_pack", "source_access_and_evidence_report"])
def test_v2_positive_source_requires_and_accepts_real_acquisition_binding(kind: str) -> None:
    if kind == "research_pack":
        payload = deepcopy(VALID_FIXTURES["research_pack"])
        payload.pop("narrative_opportunities", None)
        payload.pop("editorial_uses", None)
        payload.update({
            "research_contract_version": "2.0.0",
            "research_stage": "DEEP_RESEARCH",
            "research_sufficiency": "LIMITED_BUT_USABLE",
            "artifact_validity": "VALID",
            "thesis_stage": "PROVISIONAL",
            "evidence_type_separation": {"work_evidence_refs": ["WORK-1"], "external_reality_evidence_refs": ["EXT-1"]},
        })
        source = payload["source_registry"][0]
        source.update({"evidence_status": "VERIFIED", "retrieval_status": "RECOVERED", "recovery_artifact_ref": "recovery:S1"})
        payload["acquisition_bindings"] = [{"request_ref": "REQ-1", "execution_ref": "EXEC-1", "recovery_artifact_ref": "recovery:S1", "source_ref": "S1", "retrieval_status": "RECOVERED", "evidence_status": "VERIFIED", "software_controlled": True}]
        assert validate_research_pack(payload) == []
        payload.pop("acquisition_bindings")
        assert validate_research_pack(payload)
    else:
        payload = _v2_source_report()
        assert validate_source_access_and_evidence_report(payload) == []
        payload.pop("acquisition_bindings")
        assert validate_source_access_and_evidence_report(payload)


@pytest.mark.parametrize("mutation", [
    {"retrieval_status": "NOT_RECOVERED", "evidence_status": "VERIFIED"},
    {"retrieval_status": "RECOVERED", "evidence_status": "VERIFIED", "software_controlled": False},
    {"retrieval_status": "RECOVERED", "evidence_status": "VERIFIED", "recovery_artifact_ref": None},
])
def test_v2_acquisition_binding_rejects_positive_evidence_without_real_recovery(mutation: dict) -> None:
    for kind in ("research_pack", "source_access_and_evidence_report"):
        payload = _v2_source_report() if kind == "source_access_and_evidence_report" else deepcopy(VALID_FIXTURES["research_pack"])
        if kind == "research_pack":
            payload.pop("narrative_opportunities", None)
            payload.pop("editorial_uses", None)
            payload.update({"research_contract_version": "2.0.0", "research_stage": "DEEP_RESEARCH", "research_sufficiency": "LIMITED_BUT_USABLE", "artifact_validity": "VALID", "thesis_stage": "PROVISIONAL", "evidence_type_separation": {"work_evidence_refs": ["WORK-1"], "external_reality_evidence_refs": ["EXT-1"]}})
            payload["source_registry"][0].update({"evidence_status": "VERIFIED", "retrieval_status": "RECOVERED", "recovery_artifact_ref": "recovery:S1"})
            payload["acquisition_bindings"] = [{"request_ref": "REQ-1", "execution_ref": "EXEC-1", "recovery_artifact_ref": "recovery:S1", "source_ref": "S1", "retrieval_status": "RECOVERED", "evidence_status": "VERIFIED", "software_controlled": True}]
        payload["acquisition_bindings"][0].update(mutation)
        validator = validate_research_pack if kind == "research_pack" else validate_source_access_and_evidence_report
        assert validator(payload)


def test_research_ready_with_limitations_requires_downstream_restrictions() -> None:
    manifest = deepcopy(VALID_FIXTURES["research_ready_manifest"])
    assert validate_research_ready_manifest(manifest) == []
    manifest["downstream_restrictions"] = []
    assert validate_research_ready_manifest(manifest)


def test_research_v2_does_not_require_narrative_curation_fields() -> None:
    curation = deepcopy(VALID_FIXTURES["material_curation"])
    for field in (
        "sequence_rationale",
        "progression_evidence",
        "function_of_each_selected_material",
        "progression_map",
        "expected_order",
        "dependency_between_materials",
    ):
        curation.pop(field, None)
    curation["candidates"][0].pop("narrative_use", None)
    curation.update({"research_contract_version": "2.0.0", "selection_state": "SELECTED", "artifact_validity": "VALID"})
    assert validate_against_schema(curation, "material_curation") == []
