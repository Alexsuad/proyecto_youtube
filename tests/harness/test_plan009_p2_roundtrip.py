from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import src.cli as cli
from src.ai.contracts import ExecutionResult, ExecutionStatus
from src.ai.providers.agent_handoff import AgentHandoffProvider
from src.application.contracts import HumanInput
from src.application.service import EpisodeApplicationService
from src.application.storage import VaultEpisodeStore
from src.application.topic_belonging import (
    ExecutionCognitiveBoundary,
    TopicBelongingExecutionError,
    TopicBelongingTechnicalWorkflow,
)
from src.core.mission_authorization import scope_checksum, sha256_file
from src.core.p2_real_reporter import STAGES, build_p2_report, render_p2_report
from src.core.contract_validation import validate_against_schema
from src.scripts.channel_intelligence import active_profile, canonical_checksum
from tests.core.test_application_intake import _temporary_entrypoint_repository


ROOT = Path(__file__).resolve().parents[2]
_TERMINAL_REPORTER = None
TRIGGER_KEYS = [
    "political_partisan_sensitivity", "high_sensitivity", "audience_matrix_change",
    "excluded_boundary_reinterpretation", "new_personal_exposure", "voice_or_author_persona_change",
    "positioning_expansion", "permanent_effect", "high_precedent_risk", "experimental_territory",
]


@pytest.fixture(autouse=True)
def _remove_test_handoffs(tmp_path: Path, request: pytest.FixtureRequest):
    global _TERMINAL_REPORTER
    _TERMINAL_REPORTER = request.config.pluginmanager.get_plugin("terminalreporter")
    handoff_dir = ROOT / "handoff"
    before = set(handoff_dir.glob("*.json")) if handoff_dir.is_dir() else set()
    yield
    _TERMINAL_REPORTER = None
    for path in handoff_dir.glob("*.json") if handoff_dir.is_dir() else ():
        if path not in before:
            path.unlink(missing_ok=True)
    if handoff_dir.is_dir() and not any(handoff_dir.iterdir()):
        handoff_dir.rmdir()
    shutil.rmtree(ROOT / ".runtime-tmp" / f"plan009-p2-{tmp_path.name}", ignore_errors=True)


def _topic_input() -> dict:
    profile = active_profile()
    return {
        "topic_input_id": "TBI-P2-FIXTURE",
        **{key: profile[key] for key in ("profile_id", "profile_version", "profile_checksum")},
        "topic": "T",
        "entry_mode": "TOPIC_FIRST",
        "central_question": "¿Qué revela esta tensión sobre vivir con otros?",
        "proposed_angle": "Observar la tensión sin convertirla en consejo.",
        "proposed_territory": "Individuo e identidad",
        "initial_evidence": ["fixture://p2/initial"],
        "strategic_triggers": {key: False for key in TRIGGER_KEYS},
        "submitted_at": "2026-08-30T10:00:00Z",
    }


def _cognitive_proposal() -> dict:
    topic = _topic_input()
    return {
        key: topic[key]
        for key in (
            "proposed_angle",
            "proposed_territory",
            "initial_evidence",
            "strategic_triggers",
        )
    }


def _materialized_topic_input(episode) -> dict:
    results = json.loads((episode.folder / "roundtrip_results.json").read_text(encoding="utf-8"))
    record = next(item for item in results["results"] if item["stage"] == "ENRICHMENT")
    return json.loads((episode.folder / record["materialized_output_path"]).read_text(encoding="utf-8"))


def _materialized_producer_assessment(episode) -> dict:
    results = json.loads((episode.folder / "roundtrip_results.json").read_text(encoding="utf-8"))
    record = next(item for item in results["results"] if item["stage"] == "PRODUCER")
    return json.loads((episode.folder / record["materialized_output_path"]).read_text(encoding="utf-8"))


def _cognitive_assessment(topic_input: dict, run_id: str) -> dict:
    assessment = _assessment(topic_input, run_id)
    return {
        key: assessment[key]
        for key in (
            "strategic_triggers",
            "sensitive_risks",
            "territory_classification",
            "identity_alignment",
            "promise_alignment",
            "risks",
            "recommended_conditions",
            "recommended_exclusions",
            "owner_escalation_recommended",
            "evidence",
            "status",
        )
    }


def _assessment(topic_input: dict, run_id: str) -> dict:
    profile = active_profile()
    data = {
        "assessment_id": "TBA-P2-FIXTURE",
        "topic_input_id": topic_input["topic_input_id"],
        "producer_actor_id": "actor-p2-producer",
        "producer_role_id": "CHANNEL_INTELLIGENCE_PRODUCER",
        "producer_run_id": run_id,
        **{key: profile[key] for key in ("profile_id", "profile_version", "profile_checksum")},
        **{key: topic_input[key] for key in ("topic", "central_question", "proposed_angle", "proposed_territory", "initial_evidence", "strategic_triggers", "entry_mode")},
        "sensitive_risks": [], "territory_classification": "ACTIVE", "identity_alignment": "ALIGNED",
        "promise_alignment": "ALIGNED", "risks": [], "recommended_conditions": [],
        "recommended_exclusions": [], "owner_escalation_recommended": False,
        "evidence": ["fixture://p2/assessment"], "status": "CLOSED_FOR_REVIEW", "artifact_checksum": "",
        "provenance": {"actor_id": "actor-p2-producer", "role_id": "CHANNEL_INTELLIGENCE_PRODUCER", "run_id": run_id, "input_checksums": [canonical_checksum(topic_input, "input")], "output_checksum": "", "executor_identity": "fixture-producer"},
    }
    checksum = canonical_checksum(data, "assessment")
    data["artifact_checksum"] = checksum
    data["provenance"]["output_checksum"] = checksum
    return data


def _decision(assessment: dict, run_id: str) -> dict:
    profile = active_profile()
    data = {
        "decision_id": "TBD-P2-FIXTURE", "assessment_id": assessment["assessment_id"],
        "reviewer_run_id": run_id,
        **{key: profile[key] for key in ("profile_id", "profile_version", "profile_checksum")},
        "producer_artifact_checksum": assessment["artifact_checksum"], "reviewer_actor_id": "actor-p2-reviewer",
        "reviewer_role_id": "CHANNEL_INTELLIGENCE_REVIEWER", "reviewer_input_checksum": assessment["artifact_checksum"],
        "decision": "REQUEST_MORE_EVIDENCE", "conditions": [], "exclusions": [], "risks": [],
        "owner_escalation_required": False, "owner_escalation_reason": "", "strategic_dimensions_affected": [],
        "temporary_or_permanent_effect": "NONE", "precedent_risk": "LOW", "evidence": ["fixture://p2/review"],
        "decided_at": "2026-08-30T10:01:00Z",
        "provenance": {"actor_id": "actor-p2-reviewer", "role_id": "CHANNEL_INTELLIGENCE_REVIEWER", "run_id": run_id, "input_checksum": assessment["artifact_checksum"], "output_checksum": "", "executor_identity": "fixture-reviewer"},
    }
    data["provenance"]["output_checksum"] = canonical_checksum(data, "decision")
    return data


def _cognitive_decision(assessment: dict, decision_name: str = "REQUEST_MORE_EVIDENCE") -> dict:
    decision = _decision(assessment, "fixture-reviewer-run")
    decision["decision"] = decision_name
    if decision_name == "APPROVE_WITH_CONDITIONS":
        decision["conditions"] = ["Mantener el ángulo dentro del territorio activo."]
    if decision_name == "ESCALATE_TO_OWNER":
        decision["owner_escalation_required"] = True
        decision["owner_escalation_reason"] = "Requiere decisión del owner."
    return {
        key: decision[key]
        for key in (
            "decision",
            "conditions",
            "exclusions",
            "risks",
            "owner_escalation_required",
            "owner_escalation_reason",
            "strategic_dimensions_affected",
            "temporary_or_permanent_effect",
            "precedent_risk",
            "evidence",
        )
    }


def _human_input() -> HumanInput:
    return HumanInput.create(
        mode="TOPIC_FIRST",
        content="T",
        initial_question="¿Qué revela esta tensión sobre vivir con otros?",
        context="Fixture técnico; no es un episodio real.",
        channel="TERMINAL",
    )


def _mission_bundle(tmp_path: Path) -> tuple[str, str, Path, Path]:
    bundle_root = ROOT / ".runtime-tmp" / f"plan009-p2-{tmp_path.name}"
    bundle_root.mkdir(parents=True, exist_ok=True)
    mission_id = f"PLAN009_P2_SYNTHETIC_{tmp_path.name}"
    live_state = bundle_root / "control.md"
    live_state_ref = live_state.relative_to(ROOT).as_posix()
    contract_path = bundle_root / "mission_contract.json"
    contract_ref = contract_path.relative_to(ROOT).as_posix()
    authorization_path = bundle_root / "mission-authorization.json"
    authorization_ref = authorization_path.relative_to(ROOT).as_posix()
    authority_path = bundle_root / "authority.json"
    authority_ref = authority_path.relative_to(ROOT).as_posix()

    control = (ROOT / "plans/001_CONTROL_OPERATIVO.md").read_text(encoding="utf-8")
    control = "\n".join(
        f"CURRENT_MISSION: {mission_id}" if line.startswith("CURRENT_MISSION:")
        else f"CURRENT_MISSION_EXECUTION_BUNDLE: {contract_ref}" if line.startswith("CURRENT_MISSION_EXECUTION_BUNDLE:")
        else line
        for line in control.splitlines()
    ) + "\n"
    live_state.write_text(control, encoding="utf-8")

    scope = {
        "mission_id": mission_id,
        "capability_ids": ["TOPIC_BELONGING_ASSESSMENT"],
        "role_ids": ["CHANNEL_INTELLIGENCE_PRODUCER", "CHANNEL_INTELLIGENCE_REVIEWER"],
        "execution_profile_ids": [],
        "execution_family_ids": ["AGENT_HARNESS"],
        "execution_interface": "TOPIC_BELONGING_TERMINAL",
        "allowed_operations": ["EXECUTE_CAPABILITY"],
        "allowed_paths": ["handoff/", "output/"],
        "allowed_routes": ["agent_harness"],
        "execution_mode": "REAL",
        "live_state_sha256": sha256_file(live_state),
        "contains_material_repair": False,
        "repair_integrity_evidence_path": "NONE",
    }
    material_registry = json.loads((ROOT / "docs/legacy/material_decision_registry.json").read_text(encoding="utf-8"))
    material = next(item for item in material_registry["decisions"] if item["decision_id"] == "MD-CI-001")
    authority = {
        "mission_id": mission_id,
        "decision": "APPROVE",
        "artifact_version": "1.0.0",
        "authorized_scope_sha256": scope_checksum(scope),
        "material_decision_binding": {
            "registry_path": "docs/legacy/material_decision_registry.json",
            "decision_id": "MD-CI-001",
            "subject_ref": "capability:TOPIC_BELONGING_ASSESSMENT",
            "decision_sha256": scope_checksum(material),
        },
    }
    authority_path.write_text(json.dumps(authority, ensure_ascii=False), encoding="utf-8")
    authorization = {
        "mission_id": mission_id,
        "authorization": {
            **scope,
            "live_state_path": live_state_ref,
            "authority_ref": authority_ref,
            "authority_sha256": sha256_file(authority_path),
            "authorized_scope_sha256": scope_checksum(scope),
            "single_use": False,
            "executor_substitution_policy": "COMPATIBLE_INTERFACE_ONLY",
        },
    }
    authorization_path.write_text(json.dumps(authorization, ensure_ascii=False), encoding="utf-8")
    contract = {
        "mission_id": mission_id,
        "mission_mode": "LEGACY",
        "artifact_id": mission_id,
        "artifact_version": "1.0.0",
        "authorized_paths": ["handoff/", "output/"],
        "protected_untracked_paths": [],
        "protected_untracked_baseline": [],
        "required_tests": [],
        "push_allowed": False,
        "push_guard": {"remote": "LOCAL", "ref": "HEAD", "baseline_remote_commit": "0" * 40},
        "contains_material_repair": False,
        "mission_authorization_path": authorization_ref,
        "state_requirements": {
            "control_path": live_state_ref,
            "required": {"CURRENT_MISSION": mission_id},
            "forbidden": {},
        },
        "schema_checks": [],
    }
    contract_path.write_text(json.dumps(contract, ensure_ascii=False), encoding="utf-8")
    (bundle_root / "run_configuration.json").write_text(
        json.dumps(
            {
                "role_id": "CHANNEL_INTELLIGENCE_PRODUCER",
                "execution_route": "agent_harness",
                "execution_profile": None,
                "execution_family": "AGENT_HARNESS",
                "execution_family_selection_path": "config/execution_family_selection.json",
                "executor_override": None,
                "provider_override": None,
                "model_override": None,
                "reasoning_effort": None,
                "mission_contract_path": contract_ref,
                "timeout_seconds": 600,
                "max_retries": 1,
                "temperature": None,
                "max_tokens": None,
                "budget_limit": None,
                "paid_cost_approved": False,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return authorization_ref, contract_ref, live_state, bundle_root


def _service(tmp_path: Path, vault_root: Path | None = None) -> EpisodeApplicationService:
    vault_root = vault_root or (ROOT / ".runtime-tmp" / f"p2-vault-{hashlib.sha256(tmp_path.name.encode()).hexdigest()[:12]}")
    auth, contract, live_state, bundle_root = _mission_bundle(tmp_path)
    store = VaultEpisodeStore(vault_root, "CHANNEL")
    boundary = ExecutionCognitiveBoundary(
        repository_root=ROOT,
        mission_authorization_path=auth,
        mission_contract_path=contract,
        operational_authority_path=str(live_state),
        execution_mode="REAL",
        execution_family="AGENT_HARNESS",
        provider_override="agent_handoff",
        handoff_directory=ROOT / "handoff",
    )
    service = EpisodeApplicationService(store, workflow=TopicBelongingTechnicalWorkflow(store, boundary=boundary))
    service._p2_test_vault_root = vault_root
    service._p2_test_bundle_root = bundle_root
    return service


def _result_for(package_path: Path, output: dict, result_run_id: str, path: Path, *, executor_identity: str | None = None) -> Path:
    package = json.loads(package_path.read_text(encoding="utf-8"))
    output_checksum = hashlib.sha256(json.dumps(output, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    payload = {
        "handoff_id": package["handoff_id"], "package_checksum": package["package_checksum"],
        "input_manifest_checksum": package["input_manifest_checksum"], "skill_id": package["skill_id"],
        "skill_version": package["skill_version"], "mission_id": package["mission_id"],
        "episode_id": package["episode_id"], "capability_id": package["capability_id"],
        "stage": package["stage"], "role": package["role"], "result_run_id": result_run_id,
        "output": output, "output_checksum": output_checksum,
        "provenance": {"mission_id": package["mission_id"], "episode_id": package["episode_id"], "capability_id": package["capability_id"], "stage": package["stage"], "role": package["role"], "run_id": result_run_id, "executor_identity": executor_identity or ("fixture-reviewer" if package["role"] == "CHANNEL_INTELLIGENCE_REVIEWER" else "fixture-producer")},
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def test_public_result_import_entrypoint_uses_real_cli_and_persists(tmp_path: Path) -> None:
    repo, _, _ = _temporary_entrypoint_repository(tmp_path)
    short_vault = ROOT / ".runtime-tmp" / f"p2-cli-vault-{hashlib.sha256(tmp_path.name.encode()).hexdigest()[:10]}"
    (repo / "config" / "local_settings.json").write_text(
        json.dumps({"vault_root": str(short_vault), "channel_id": "CHANNEL"}),
        encoding="utf-8",
    )
    try:
        started = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli",
                "iniciar",
                "--modo",
                "tema",
                "--tema",
                "T",
                "--pregunta",
                "¿Qué revela esta tensión sobre vivir con otros?",
            ],
            cwd=repo,
            text=True,
            capture_output=True,
            check=False,
            timeout=60,
        )
        assert started.returncode == 0, started.stdout + started.stderr
        assert "PENDING_EXTERNAL_RESULT" in started.stdout or "handoff" in started.stdout.lower()

        episodes_path = short_vault / "CHANNEL" / "episodios"
        episode = next(episodes_path.iterdir())
        workflow = json.loads((episode / "workflow_state.json").read_text(encoding="utf-8"))
        package_path = Path(str(workflow["handoff_package_ref"]))
        if not package_path.is_absolute():
            package_path = repo / package_path
        result_path = _result_for(
            package_path,
            _cognitive_proposal(),
            "RESULT-PUBLIC-IMPORT-P2",
            tmp_path / "public-result.json",
        )

        imported = subprocess.run(
            [sys.executable, "-m", "src.cli", "importar-resultado", str(result_path)],
            cwd=repo,
            text=True,
            capture_output=True,
            check=False,
            timeout=60,
        )
        assert imported.returncode == 0, imported.stdout + imported.stderr
        assert "Resultado externo importado: ep_0001" in imported.stdout
        assert "Estado: PERSISTED" in imported.stdout
        persisted = json.loads((episode / "workflow_state.json").read_text(encoding="utf-8"))
        assert persisted["status"] == "PERSISTED"
        results = json.loads((episode / "roundtrip_results.json").read_text(encoding="utf-8"))
        assert len(results["results"]) == 1
    finally:
        shutil.rmtree(short_vault, ignore_errors=True)


def test_public_result_import_entrypoint_rejects_result_without_episode_id(tmp_path: Path) -> None:
    repo, _, _ = _temporary_entrypoint_repository(tmp_path)
    result_path = tmp_path / "invalid-result.json"
    result_path.write_text(json.dumps({"output": {"topic": "incompleto"}}), encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, "-m", "src.cli", "importar-resultado", str(result_path)],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
        timeout=60,
    )
    assert completed.returncode == 2
    assert "ROUNDTRIP_RESULT_INVALID: falta episode_id." in completed.stdout


def _cleanup_handoffs(paths: list[Path], service: EpisodeApplicationService | None = None) -> None:
    if service is not None and service.store.episodes_path.is_dir():
        for episode_folder in sorted(service.store.episodes_path.iterdir()):
            if episode_folder.is_dir():
                rendered = render_p2_report(build_p2_report(episode_folder))
                if _TERMINAL_REPORTER is None:
                    print(rendered, end="")
                else:
                    for line in rendered.rstrip("\n").splitlines():
                        _TERMINAL_REPORTER.write_line(line)
    for path in paths:
        path.unlink(missing_ok=True)
    handoff_dir = ROOT / "handoff"
    if handoff_dir.is_dir() and not any(handoff_dir.iterdir()):
        handoff_dir.rmdir()
    if service is not None:
        shutil.rmtree(getattr(service, "_p2_test_vault_root", ""), ignore_errors=True)


def _start(tmp_path: Path):
    service = _service(tmp_path)
    result = service.start(_human_input())
    package = Path(json.loads((result.episode.folder / "workflow_state.json").read_text(encoding="utf-8"))["handoff_package_ref"])
    return service, result.episode, package


def test_roundtrip_three_stages_persists_and_stops(tmp_path: Path) -> None:
    created: list[Path] = []
    service = None
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        assert json.loads((episode.folder / "workflow_state.json").read_text()) ["status"] == "PENDING_EXTERNAL_RESULT"

        result_path = _result_for(package, _cognitive_proposal(), "RESULT-ENRICHMENT-P2", tmp_path / "enrichment.json")
        service.import_result(episode.episode_id, result_path)
        service.resume(episode.episode_id)
        _, _, package = _pending_package(episode)
        created.append(package)

        topic = _materialized_topic_input(episode)
        cognitive_assessment = _cognitive_assessment(topic, "RESULT-PRODUCER-P2")
        result_path = _result_for(package, cognitive_assessment, "RESULT-PRODUCER-P2", tmp_path / "producer.json")
        service.import_result(episode.episode_id, result_path)
        service.resume(episode.episode_id)
        _, _, package = _pending_package(episode)
        created.append(package)

        assessment = _materialized_producer_assessment(episode)
        decision = _cognitive_decision(assessment)
        result_path = _result_for(package, decision, "RESULT-REVIEWER-P2", tmp_path / "reviewer.json")
        service.import_result(episode.episode_id, result_path)
        final = service.resume(episode.episode_id)
        assert final["state"]["status"] == "TOPIC_BELONGING_TECHNICAL_STOP"
        assert json.loads((episode.folder / "roundtrip_results.json").read_text())["results"]
        execution = json.loads((episode.folder / "topic_belonging_execution.json").read_text())["executions"]
        assert [item["stage"] for item in execution] == ["ENRICHMENT", "PRODUCER", "REVIEWER"]
        assert all(item["execution_family"] == "AGENT_HARNESS" and item["execution_mode"] == "REAL" for item in execution)
        results = json.loads((episode.folder / "roundtrip_results.json").read_text())["results"]
        assert len({item["handoff_id"] for item in results}) == 3
        assert [item["stage"] for item in results] == ["ENRICHMENT", "PRODUCER", "REVIEWER"]
    finally:
        _cleanup_handoffs(created, service)


def test_request_more_evidence_reentry_preserves_first_attempt(tmp_path: Path) -> None:
    created: list[Path] = []
    service = None
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        service.import_result(
            episode.episode_id,
            _result_for(package, _cognitive_proposal(), "RESULT-ENRICHMENT-RECOVERY", tmp_path / "enrichment.json"),
        )
        service.resume(episode.episode_id)
        _, _, package = _pending_package(episode)
        created.append(package)
        topic = _materialized_topic_input(episode)
        service.import_result(
            episode.episode_id,
            _result_for(package, _cognitive_assessment(topic, "RESULT-PRODUCER-RECOVERY"), "RESULT-PRODUCER-RECOVERY", tmp_path / "producer.json"),
        )
        service.resume(episode.episode_id)
        _, _, package = _pending_package(episode)
        created.append(package)
        assessment = _materialized_producer_assessment(episode)
        service.import_result(
            episode.episode_id,
            _result_for(package, _cognitive_decision(assessment), "RESULT-REVIEWER-RECOVERY", tmp_path / "reviewer.json"),
        )
        service.resume(episode.episode_id)
        original_decision = (episode.folder / "04_topic_belonging_decision.json").read_bytes()

        evidence_path = tmp_path / "evidence.json"
        evidence_path.write_text(
            json.dumps(
                {
                    "candidate_work_refs": ["work:concrete-narrative"],
                    "scene_refs": ["scene:concrete-narrative:belonging-boundary"],
                    "evidence": ["La obra concreta permite verificar reconocimiento e exclusion en escenas observables."],
                    "question_answers": {"narrative_door": "work:concrete-narrative"},
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        ready = service.submit_topic_belonging_evidence(
            episode.episode_id,
            evidence_path,
        )
        assert ready["state"]["status"] == "READY_FOR_REASSESSMENT"
        ready_report = build_p2_report(episode.folder)
        assert ready_report.result == "PARTIAL"
        assert any(
            step.name == "READY_FOR_REASSESSMENT" and step.status == "PASS"
            for step in ready_report.steps
        )
        assert (episode.folder / "04_topic_belonging_decision.json").read_bytes() == original_decision

        pending = service.prepare_topic_belonging_reassessment(episode.episode_id)
        assert pending["state"]["status"] == "PENDING_EXTERNAL_RESULT"
        package = Path(pending["state"]["handoff_package_ref"])
        created.append(package)
        package_data = json.loads(package.read_text(encoding="utf-8"))
        assert package_data["output_schema"] == "topic_belonging_cognitive_decision"
        assert any(
            item["artifact_kind"] == "topic_belonging_reassessment_evidence"
            for item in package_data["input_manifest"]["artifacts"]
        )
        service.import_result(
            episode.episode_id,
            _result_for(package, _cognitive_decision(assessment, "REJECT"), "RESULT-REVIEWER-RECOVERY-2", tmp_path / "reviewer-2.json"),
        )
        final = service.resume(episode.episode_id)
        assert final["state"]["status"] == "TOPIC_BELONGING_TECHNICAL_STOP"
        workflow_state = json.loads((episode.folder / "workflow_state.json").read_text(encoding="utf-8"))
        assert workflow_state["editorial_decision"] == "REJECT"
        assert (episode.folder / "04_topic_belonging_decision.json").read_bytes() == original_decision
        reassessments = json.loads((episode.folder / "topic_belonging_reassessments.json").read_text(encoding="utf-8"))
        assert reassessments["reassessments"][-1]["status"] == "COMPLETED"
        reassessment = reassessments["reassessments"][-1]
        assert workflow_state["effective_decision_ref"] == reassessment["decision_ref"]
        assert workflow_state["effective_decision_checksum"] == reassessment["decision_checksum"]
        assert workflow_state["effective_decision_source_attempt"] == 2
        assert reassessment["prior_decision_ref"] == f"episode:{episode.episode_id}/04_topic_belonging_decision.json"
        assert hashlib.sha256((episode.folder / "04_topic_belonging_decision.json").read_bytes()).hexdigest() == reassessment["prior_decision_checksum"]
        decision_ref = reassessment["decision_ref"].split(f"episode:{episode.episode_id}/", 1)[1]
        assert hashlib.sha256((episode.folder / decision_ref).read_bytes()).hexdigest() == reassessment["decision_checksum"]
        assert len(json.loads((episode.folder / "roundtrip_results.json").read_text(encoding="utf-8"))["results"]) == 4

        duplicate = service.submit_topic_belonging_evidence(episode.episode_id, evidence_path)
        assert duplicate["state"]["status"] == "TOPIC_BELONGING_TECHNICAL_STOP"
        duplicate_workflow = json.loads((episode.folder / "workflow_state.json").read_text(encoding="utf-8"))
        assert duplicate_workflow["editorial_decision"] == "REJECT"
        assert duplicate_workflow["reassessment_id"] == reassessments["reassessments"][-1]["reassessment_id"]
        assert len(json.loads((episode.folder / "topic_belonging_reassessments.json").read_text(encoding="utf-8"))["reassessments"]) == 1
    finally:
        _cleanup_handoffs(created, service)


def test_integrated_reassessment_succeeded_materializes_and_stops(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    created: list[Path] = []
    service = None
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        created.extend(_finish_roundtrip(service, episode, tmp_path))
        original_decision = (episode.folder / "04_topic_belonging_decision.json").read_bytes()
        evidence_path = tmp_path / "integrated-evidence.json"
        evidence_path.write_text(json.dumps(_reassessment_evidence("integrated")), encoding="utf-8")
        service.submit_topic_belonging_evidence(episode.episode_id, evidence_path)
        assessment = _materialized_producer_assessment(episode)
        cognitive_decision = _cognitive_decision(assessment, "APPROVE_WITH_CONDITIONS")
        cognitive_decision["pre_b5_i1_evidence"] = {"forged": "model-owned"}

        def integrated_review(*args, **kwargs):
            return cognitive_decision, ExecutionResult(
                run_id="RUN-INTEGRATED-REASSESSMENT",
                status=ExecutionStatus.SUCCEEDED,
                executor_type="provider",
                provider="agent_executor",
                model="CURRENT_OPENCODE_MODEL",
                input_manifest_checksum="manifest-integrated",
                output=cognitive_decision,
                output_checksum=canonical_checksum(cognitive_decision, "decision"),
                started_at="2026-09-15T20:00:00Z",
                completed_at="2026-09-15T20:00:01Z",
                usage={
                    "provider_kind": "REAL",
                    "execution_mode": "REAL",
                    "execution_route": "agent_harness",
                    "execution_profile": None,
                },
            )

        monkeypatch.setattr(service.workflow.boundary, "review", integrated_review)
        final = service.prepare_topic_belonging_reassessment(episode.episode_id)
        assert final["state"]["status"] == "TOPIC_BELONGING_TECHNICAL_STOP"
        assert (episode.folder / "04_topic_belonging_decision.json").read_bytes() == original_decision
        reassessments = json.loads((episode.folder / "topic_belonging_reassessments.json").read_text(encoding="utf-8"))
        reassessment = reassessments["reassessments"][-1]
        assert reassessment["status"] == "COMPLETED"
        assert reassessment["attempt_number"] == 2
        assert reassessment["prior_decision_ref"] == f"episode:{episode.episode_id}/04_topic_belonging_decision.json"
        assert reassessment["lineage"]["reviewer_run_id"] == "RUN-INTEGRATED-REASSESSMENT"
        decision_path = episode.folder / reassessment["decision_ref"].split(f"episode:{episode.episode_id}/", 1)[1]
        assert decision_path.is_file()
        assert hashlib.sha256(decision_path.read_bytes()).hexdigest() == reassessment["decision_checksum"]
    finally:
        _cleanup_handoffs(created, service)


def _reassessment_evidence(label: str) -> dict:
    return {
        "context": f"Evidencia técnica de reevaluación {label}.",
        "candidate_work_refs": [f"work:{label}"],
        "scene_refs": [f"scene:{label}:belonging-boundary"],
        "evidence": [f"La evidencia {label} permite verificar la frontera de pertenencia."],
        "question_answers": {"narrative_door": f"work:{label}"},
    }


def _complete_reassessment(
    service: EpisodeApplicationService,
    episode,
    tmp_path: Path,
    label: str,
    decision_name: str,
    created: list[Path],
) -> dict:
    evidence_path = tmp_path / f"evidence-{label}.json"
    evidence_path.write_text(json.dumps(_reassessment_evidence(label)), encoding="utf-8")
    ready = service.submit_topic_belonging_evidence(episode.episode_id, evidence_path)
    assert ready["state"]["status"] == "READY_FOR_REASSESSMENT"
    pending = service.prepare_topic_belonging_reassessment(episode.episode_id)
    package = Path(pending["state"]["handoff_package_ref"])
    created.append(package)
    assessment = _materialized_producer_assessment(episode)
    service.import_result(
        episode.episode_id,
        _result_for(
            package,
            _cognitive_decision(assessment, decision_name),
            f"RESULT-REASSESSMENT-{label}",
            tmp_path / f"reviewer-{label}.json",
        ),
    )
    final = service.resume(episode.episode_id)
    assert final["state"]["status"] == "TOPIC_BELONGING_TECHNICAL_STOP"
    return final


@pytest.mark.parametrize("decision_name", ["REJECT", "BLOCK", "APPROVE", "APPROVE_WITH_CONDITIONS"])
def test_terminal_decisions_reject_new_reassessment_evidence(tmp_path: Path, decision_name: str) -> None:
    created: list[Path] = []
    service = None
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        _finish_roundtrip(service, episode, tmp_path, decision_name)
        evidence_path = tmp_path / "terminal-evidence.json"
        evidence_path.write_text(json.dumps(_reassessment_evidence(decision_name)), encoding="utf-8")
        with pytest.raises(TopicBelongingExecutionError, match="TOPIC_BELONGING_REASSESSMENT_NOT_REQUESTED"):
            service.submit_topic_belonging_evidence(episode.episode_id, evidence_path)
    finally:
        _cleanup_handoffs(created, service)


def test_reassessment_chain_uses_latest_effective_decision(tmp_path: Path) -> None:
    created: list[Path] = []
    service = None
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        _finish_roundtrip(service, episode, tmp_path)
        _complete_reassessment(service, episode, tmp_path, "attempt-2", "REQUEST_MORE_EVIDENCE", created)
        _complete_reassessment(service, episode, tmp_path, "attempt-3", "REJECT", created)
        reassessments = json.loads((episode.folder / "topic_belonging_reassessments.json").read_text(encoding="utf-8"))["reassessments"]
        assert [item["attempt_number"] for item in reassessments] == [2, 3]
        assert reassessments[1]["prior_decision_ref"] == reassessments[0]["decision_ref"]
        assert reassessments[1]["prior_decision_checksum"] == reassessments[0]["decision_checksum"]
        decision_path = reassessments[0]["decision_ref"].split(f"episode:{episode.episode_id}/", 1)[1]
        assert hashlib.sha256((episode.folder / decision_path).read_bytes()).hexdigest() == reassessments[1]["prior_decision_checksum"]
    finally:
        _cleanup_handoffs(created, service)


def test_reassessment_rejects_stale_prior_decision_binding(tmp_path: Path) -> None:
    created: list[Path] = []
    service = None
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        _finish_roundtrip(service, episode, tmp_path)
        evidence_path = tmp_path / "stale-evidence.json"
        evidence_path.write_text(json.dumps(_reassessment_evidence("stale")), encoding="utf-8")
        service.submit_topic_belonging_evidence(episode.episode_id, evidence_path)
        reassessment_path = episode.folder / "topic_belonging_reassessments.json"
        data = json.loads(reassessment_path.read_text(encoding="utf-8"))
        data["reassessments"][0]["prior_decision_checksum"] = "0" * 64
        reassessment_path.write_text(json.dumps(data), encoding="utf-8")
        with pytest.raises(TopicBelongingExecutionError, match="TOPIC_BELONGING_PRIOR_DECISION_BINDING_INVALID"):
            service.prepare_topic_belonging_reassessment(episode.episode_id)
    finally:
        _cleanup_handoffs(created, service)


def test_reassessment_schema_rejects_whitespace_only_values(tmp_path: Path) -> None:
    created: list[Path] = []
    service = None
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        _finish_roundtrip(service, episode, tmp_path)
        evidence_path = tmp_path / "whitespace-evidence.json"
        evidence_path.write_text(json.dumps({"context": "   \n\t"}), encoding="utf-8")
        with pytest.raises(TopicBelongingExecutionError, match="REASSESSMENT_EVIDENCE_INVALID"):
            service.submit_topic_belonging_evidence(episode.episode_id, evidence_path)
    finally:
        _cleanup_handoffs(created, service)


@pytest.mark.parametrize(
    "payload",
    [
        {"context": " \t\n"},
        {"candidate_work_refs": [" \t\n"]},
        {"scene_refs": [" \t\n"]},
        {"evidence": [" \t\n"]},
        {"question_answers": {" \t\n": "valid"}},
        {"question_answers": {"valid": " \t\n"}},
    ],
)
def test_reassessment_schema_rejects_whitespace_strings_elements_and_keys(payload: dict) -> None:
    assert validate_against_schema(payload, "topic_belonging_reassessment_evidence")


def _pending_package(episode):
    workflow = json.loads((episode.folder / "workflow_state.json").read_text(encoding="utf-8"))
    return workflow["stage"], episode, Path(workflow["handoff_package_ref"])


def test_enrichment_import_materializes_software_owned_input(tmp_path: Path) -> None:
    created: list[Path] = []
    service = None
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        proposal = _cognitive_proposal()
        result_path = _result_for(package, proposal, "RESULT-ENRICHMENT-MATERIALIZED", tmp_path / "enrichment.json")
        service.import_result(episode.episode_id, result_path)

        results = json.loads((episode.folder / "roundtrip_results.json").read_text(encoding="utf-8"))
        record = results["results"][0]
        materialized = json.loads((episode.folder / record["materialized_output_path"]).read_text(encoding="utf-8"))
        assert materialized["topic"] == "T"
        assert materialized["central_question"] == "¿Qué revela esta tensión sobre vivir con otros?"
        assert materialized["topic_input_id"].startswith("TBI-")
        assert materialized["submitted_at"]
        assert materialized["profile_id"] == active_profile()["profile_id"]
        assert materialized["profile_version"] == active_profile()["profile_version"]
        assert materialized["proposed_angle"] == proposal["proposed_angle"]
        assert "topic_input_id" not in proposal
        assert "submitted_at" not in proposal
        workflow = json.loads((episode.folder / "workflow_state.json").read_text(encoding="utf-8"))
        assert workflow["status"] == "PERSISTED"
        assert workflow["next_stage"] == "PRODUCER"
    finally:
        _cleanup_handoffs(created, service)


def test_enrichment_import_rejects_missing_canonical_input(tmp_path: Path) -> None:
    created: list[Path] = []
    service = None
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        (episode.folder / "01_editorial_intake_handoff.json").unlink()
        result_path = _result_for(package, _cognitive_proposal(), "RESULT-ENRICHMENT-NO-INPUT", tmp_path / "missing-input.json")
        with pytest.raises(TopicBelongingExecutionError, match="ROUNDTRIP_INPUT_CANONICAL_MISSING"):
            service.import_result(episode.episode_id, result_path)
        workflow = json.loads((episode.folder / "workflow_state.json").read_text(encoding="utf-8"))
        assert workflow["status"] == "PENDING_EXTERNAL_RESULT"
    finally:
        _cleanup_handoffs(created, service)


def test_enrichment_import_rejects_wrong_episode_binding(tmp_path: Path) -> None:
    created: list[Path] = []
    service = None
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        result_path = _result_for(package, _cognitive_proposal(), "RESULT-ENRICHMENT-WRONG-EPISODE", tmp_path / "wrong-episode.json")
        payload = json.loads(result_path.read_text(encoding="utf-8"))
        payload["episode_id"] = "ep-other"
        result_path.write_text(json.dumps(payload), encoding="utf-8")
        with pytest.raises(TopicBelongingExecutionError, match="ROUNDTRIP_RESULT_PACKAGE_BINDING_INVALID"):
            service.import_result(episode.episode_id, result_path)
    finally:
        _cleanup_handoffs(created, service)


def test_enrichment_import_rejects_wrong_result_correlation(tmp_path: Path) -> None:
    created: list[Path] = []
    service = None
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        result_path = _result_for(package, _cognitive_proposal(), "RESULT-ENRICHMENT-CORRELATION", tmp_path / "wrong-correlation.json")
        payload = json.loads(result_path.read_text(encoding="utf-8"))
        payload["provenance"]["run_id"] = "RESULT-ENRICHMENT-CORRELATION-OTHER"
        result_path.write_text(json.dumps(payload), encoding="utf-8")
        with pytest.raises(TopicBelongingExecutionError, match="ROUNDTRIP_RESULT_PROVENANCE_BINDING_INVALID"):
            service.import_result(episode.episode_id, result_path)
    finally:
        _cleanup_handoffs(created, service)


def test_enrichment_import_rejects_software_owned_metadata_from_proposal(tmp_path: Path) -> None:
    created: list[Path] = []
    service = None
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        proposal = _cognitive_proposal()
        proposal["topic_input_id"] = "TBI-FORGED"
        result_path = _result_for(package, proposal, "RESULT-ENRICHMENT-FORGED-METADATA", tmp_path / "forged-metadata.json")
        with pytest.raises(TopicBelongingExecutionError, match="COGNITIVE_PROPOSAL_INVALID"):
            service.import_result(episode.episode_id, result_path)
        assert not (episode.folder / "roundtrip_results.json").exists()
    finally:
        _cleanup_handoffs(created, service)


def test_enrichment_import_resumes_to_producer_handoff(tmp_path: Path) -> None:
    created: list[Path] = []
    service = None
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        result_path = _result_for(package, _cognitive_proposal(), "RESULT-ENRICHMENT-NEXT-STAGE", tmp_path / "next-stage.json")
        service.import_result(episode.episode_id, result_path)
        resumed = service.resume(episode.episode_id)
        assert resumed["state"]["status"] == "PENDING_EXTERNAL_RESULT"
        workflow = json.loads((episode.folder / "workflow_state.json").read_text(encoding="utf-8"))
        assert workflow["stage"] == "PRODUCER"
        assert workflow["next_stage"] == "PRODUCER"
        assert workflow["completed_stages"] == ["ENRICHMENT"]
        producer_package = Path(workflow["handoff_package_ref"])
        created.append(producer_package)
        assert json.loads(producer_package.read_text(encoding="utf-8"))["stage"] == "PRODUCER"
    finally:
        _cleanup_handoffs(created, service)


def test_p2_reporter_marks_pending_without_inventing_pass(tmp_path: Path) -> None:
    created: list[Path] = []
    service = None
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        report = build_p2_report(episode.folder)
        rendered = render_p2_report(report)
        assert report.result == "PARTIAL"
        assert report.maximum_reached == "PENDING_EXTERNAL_RESULT"
        assert report.steps[0].status == "PASS"
        assert all(step.status == "PENDING" for step in report.steps if step.name in STAGES)
        assert "☐ ENRICHMENT: PENDING" in rendered
        assert "RESULTADO: PARTIAL" in rendered
    finally:
        _cleanup_handoffs(created, service)


def test_p2_reporter_reads_persisted_completion_and_cli_renders_it(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    created: list[Path] = []
    service = None
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        created.extend(_finish_roundtrip(service, episode, tmp_path))
        settings = tmp_path / "report-settings.json"
        settings.write_text(
            json.dumps({"vault_root": str(getattr(service, "_p2_test_vault_root")), "channel_id": "CHANNEL"}),
            encoding="utf-8",
        )
        assert cli.main(["reportar-p2", episode.episode_id, "--config", str(settings)]) == 0
        rendered = capsys.readouterr().out
        report = build_p2_report(episode.folder)
        assert report.result == "PASS"
        assert report.maximum_reached == "REVIEWER"
        assert all(step.status == "PASS" for step in report.steps if step.name in STAGES)
        assert "☑ REVIEWER: PASS" in rendered
        assert "RESULTADO: PASS" in rendered
    finally:
        _cleanup_handoffs(created, service)


def test_p2_reporter_exposes_persisted_evidence_failure(tmp_path: Path) -> None:
    created: list[Path] = []
    service = None
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        result = _result_for(package, _cognitive_proposal(), "RESULT-REPORTER-TAMPER", tmp_path / "reporter.json")
        service.import_result(episode.episode_id, result)
        indexed = json.loads((episode.folder / "roundtrip_results.json").read_text(encoding="utf-8"))["results"][0]
        (episode.folder / indexed["result_path"]).unlink()
        report = build_p2_report(episode.folder)
        assert report.result == "FAIL"
        assert report.failed_step == "ENRICHMENT"
        assert "ROUNDTRIP_PERSISTED_ENVELOPE_INVALID" in report.error
        assert "No such file or directory" in report.error
        assert report.expected == "resultado persistido compatible con su handoff"
        assert report.obtained == "evidencia incompatible"
    finally:
        _cleanup_handoffs(created, service)


def test_p2_reporter_rejects_inconsistent_terminal_state(tmp_path: Path) -> None:
    created: list[Path] = []
    service = None
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        created.extend(_finish_roundtrip(service, episode, tmp_path))
        workflow_path = episode.folder / "workflow_state.json"
        workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
        workflow["downstream_execution_started"] = True
        workflow_path.write_text(json.dumps(workflow), encoding="utf-8")
        report = build_p2_report(episode.folder)
        assert report.result == "FAIL"
        assert report.failed_step == "STATE_CONSISTENCY"
        assert report.error == "downstream_execution_started contradice el estado terminal"
        assert report.expected == "downstream_execution_started=False"
        assert report.obtained == "downstream_execution_started=True"
    finally:
        _cleanup_handoffs(created, service)


def _finish_roundtrip(service, episode, tmp_path: Path, decision_name: str = "REQUEST_MORE_EVIDENCE") -> list[Path]:
    created: list[Path] = []
    _, _, package = _pending_package(episode)
    created.append(package)
    service.import_result(
        episode.episode_id,
        _result_for(package, _cognitive_proposal(), "RESULT-FIX-ENRICHMENT", tmp_path / "fix-enrichment.json"),
    )
    service.resume(episode.episode_id)
    _, _, package = _pending_package(episode)
    created.append(package)
    topic = _materialized_topic_input(episode)
    cognitive_assessment = _cognitive_assessment(topic, "RESULT-FIX-PRODUCER")
    service.import_result(
        episode.episode_id,
        _result_for(package, cognitive_assessment, "RESULT-FIX-PRODUCER", tmp_path / "fix-producer.json"),
    )
    service.resume(episode.episode_id)
    _, _, package = _pending_package(episode)
    created.append(package)
    assessment = _materialized_producer_assessment(episode)
    decision = _cognitive_decision(assessment, decision_name)
    service.import_result(
        episode.episode_id,
        _result_for(package, decision, "RESULT-FIX-REVIEWER", tmp_path / "fix-reviewer.json"),
    )
    service.resume(episode.episode_id)
    return created


def test_roundtrip_duplicate_import_is_idempotent(tmp_path: Path) -> None:
    created: list[Path] = []
    service = None
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        result_path = _result_for(package, _cognitive_proposal(), "RESULT-DUPLICATE-P2", tmp_path / "duplicate.json")
        service.import_result(episode.episode_id, result_path)
        count_before = len(json.loads((episode.folder / "roundtrip_results.json").read_text())["results"])
        service.import_result(episode.episode_id, result_path)
        count_after = len(json.loads((episode.folder / "roundtrip_results.json").read_text())["results"])
        assert count_before == count_after == 1
    finally:
        _cleanup_handoffs(created, service)


def test_roundtrip_duplicate_without_provenance_is_blocked(tmp_path: Path) -> None:
    created: list[Path] = []
    service = None
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        original = _result_for(package, _cognitive_proposal(), "RESULT-DUPLICATE-MISSING-PROVENANCE", tmp_path / "duplicate-missing-provenance.json")
        service.import_result(episode.episode_id, original)
        altered = json.loads(original.read_text(encoding="utf-8"))
        altered.pop("provenance")
        altered_path = tmp_path / "duplicate-missing-provenance-altered.json"
        altered_path.write_text(json.dumps(altered), encoding="utf-8")
        with pytest.raises(TopicBelongingExecutionError, match="ROUNDTRIP_RESULT_BLOCKED"):
            service.import_result(episode.episode_id, altered_path)
    finally:
        _cleanup_handoffs(created, service)


def test_roundtrip_duplicate_with_provenance_run_mismatch_is_blocked(tmp_path: Path) -> None:
    created: list[Path] = []
    service = None
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        original = _result_for(package, _cognitive_proposal(), "RESULT-DUPLICATE-PROVENANCE-RUN", tmp_path / "duplicate-provenance-run.json")
        service.import_result(episode.episode_id, original)
        altered = json.loads(original.read_text(encoding="utf-8"))
        altered["provenance"]["run_id"] = "RESULT-DUPLICATE-PROVENANCE-RUN-OTHER"
        altered_path = tmp_path / "duplicate-provenance-run-altered.json"
        altered_path.write_text(json.dumps(altered), encoding="utf-8")
        with pytest.raises(TopicBelongingExecutionError, match="ROUNDTRIP_RESULT_BLOCKED"):
            service.import_result(episode.episode_id, altered_path)
    finally:
        _cleanup_handoffs(created, service)


def test_roundtrip_duplicate_with_changed_result_run_id_is_blocked(tmp_path: Path) -> None:
    created: list[Path] = []
    service = None
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        original = _result_for(package, _cognitive_proposal(), "RESULT-DUPLICATE-RUN", tmp_path / "duplicate-run.json")
        service.import_result(episode.episode_id, original)
        altered = json.loads(original.read_text(encoding="utf-8"))
        altered["result_run_id"] = "RESULT-DUPLICATE-RUN-ALTERED"
        altered["provenance"]["run_id"] = altered["result_run_id"]
        altered_path = tmp_path / "duplicate-run-altered.json"
        altered_path.write_text(json.dumps(altered), encoding="utf-8")
        with pytest.raises(TopicBelongingExecutionError, match="ROUNDTRIP_RESULT_CONFLICT"):
            service.import_result(episode.episode_id, altered_path)
    finally:
        _cleanup_handoffs(created, service)


def test_roundtrip_duplicate_with_changed_mission_is_blocked(tmp_path: Path) -> None:
    created: list[Path] = []
    service = None
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        original = _result_for(package, _cognitive_proposal(), "RESULT-DUPLICATE-MISSION", tmp_path / "duplicate-mission.json")
        service.import_result(episode.episode_id, original)
        altered = json.loads(original.read_text(encoding="utf-8"))
        altered["mission_id"] = "OTHER-MISSION"
        altered["provenance"]["mission_id"] = "OTHER-MISSION"
        altered_path = tmp_path / "duplicate-mission-altered.json"
        altered_path.write_text(json.dumps(altered), encoding="utf-8")
        with pytest.raises(TopicBelongingExecutionError, match="ROUNDTRIP_RESULT_CONFLICT"):
            service.import_result(episode.episode_id, altered_path)
    finally:
        _cleanup_handoffs(created, service)


def test_roundtrip_conflicting_duplicate_is_blocked(tmp_path: Path) -> None:
    created: list[Path] = []
    service = None
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        original = _result_for(package, _cognitive_proposal(), "RESULT-CONFLICT-P2", tmp_path / "original.json")
        service.import_result(episode.episode_id, original)
        conflicting = json.loads(original.read_text(encoding="utf-8"))
        conflicting["output"]["proposed_angle"] = "conflicto"
        conflicting["output_checksum"] = "0" * 64
        conflict_path = tmp_path / "conflict.json"
        conflict_path.write_text(json.dumps(conflicting), encoding="utf-8")
        with pytest.raises(TopicBelongingExecutionError, match="CONFLICT"):
            service.import_result(episode.episode_id, conflict_path)
    finally:
        _cleanup_handoffs(created, service)


def test_roundtrip_final_resume_returns_stop_without_new_effects(tmp_path: Path) -> None:
    created: list[Path] = []
    service = None
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        created.extend(_finish_roundtrip(service, episode, tmp_path))
        before_results = json.loads((episode.folder / "roundtrip_results.json").read_text(encoding="utf-8"))
        before_handoffs = sorted(path.name for path in (ROOT / "handoff").glob("*.json"))
        first = service.resume(episode.episode_id)
        second = service.resume(episode.episode_id)
        after_results = json.loads((episode.folder / "roundtrip_results.json").read_text(encoding="utf-8"))
        after_handoffs = sorted(path.name for path in (ROOT / "handoff").glob("*.json"))
        assert first["state"]["status"] == second["state"]["status"] == "TOPIC_BELONGING_TECHNICAL_STOP"
        assert before_results == after_results
        assert before_handoffs == after_handoffs
    finally:
        _cleanup_handoffs(created, service)


def test_roundtrip_final_resume_rejects_deleted_envelope(tmp_path: Path) -> None:
    created: list[Path] = []
    service = None
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        created.extend(_finish_roundtrip(service, episode, tmp_path))
        reviewer = json.loads((episode.folder / "roundtrip_results.json").read_text(encoding="utf-8"))["results"][2]
        (episode.folder / reviewer["result_path"]).unlink()
        with pytest.raises(TopicBelongingExecutionError, match="ROUNDTRIP_PERSISTED_ENVELOPE_INVALID"):
            service.resume(episode.episode_id)
    finally:
        _cleanup_handoffs(created, service)


def test_roundtrip_final_resume_rejects_tampered_envelope(tmp_path: Path) -> None:
    created: list[Path] = []
    service = None
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        created.extend(_finish_roundtrip(service, episode, tmp_path))
        reviewer = json.loads((episode.folder / "roundtrip_results.json").read_text(encoding="utf-8"))["results"][2]
        result_path = episode.folder / reviewer["result_path"]
        envelope = json.loads(result_path.read_text(encoding="utf-8"))
        envelope["output"]["decision"] = "APPROVE"
        result_path.write_text(json.dumps(envelope), encoding="utf-8")
        with pytest.raises(TopicBelongingExecutionError, match="ROUNDTRIP_PERSISTED_ENVELOPE_INVALID"):
            service.resume(episode.episode_id)
    finally:
        _cleanup_handoffs(created, service)


def test_roundtrip_final_resume_rejects_tampered_result_index(tmp_path: Path) -> None:
    created: list[Path] = []
    service = None
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        created.extend(_finish_roundtrip(service, episode, tmp_path))
        results_path = episode.folder / "roundtrip_results.json"
        results = json.loads(results_path.read_text(encoding="utf-8"))
        results["results"][1]["role"] = "CHANNEL_INTELLIGENCE_REVIEWER"
        results_path.write_text(json.dumps(results), encoding="utf-8")
        with pytest.raises(TopicBelongingExecutionError, match="ROUNDTRIP_PERSISTED"):
            service.resume(episode.episode_id)
    finally:
        _cleanup_handoffs(created, service)


def test_roundtrip_final_resume_rejects_tampered_execution_evidence(tmp_path: Path) -> None:
    created: list[Path] = []
    service = None
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        created.extend(_finish_roundtrip(service, episode, tmp_path))
        execution_path = episode.folder / "topic_belonging_execution.json"
        execution = json.loads(execution_path.read_text(encoding="utf-8"))
        execution["executions"][2]["artifact_checksum"] = "0" * 64
        execution_path.write_text(json.dumps(execution), encoding="utf-8")
        with pytest.raises(TopicBelongingExecutionError, match="ROUNDTRIP_PERSISTED"):
            service.resume(episode.episode_id)
    finally:
        _cleanup_handoffs(created, service)


def test_roundtrip_import_rejects_wrong_stage_binding(tmp_path: Path) -> None:
    created: list[Path] = []
    service = None
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        result_path = _result_for(package, _cognitive_proposal(), "RESULT-WRONG-STAGE-P2", tmp_path / "wrong.json")
        payload = json.loads(result_path.read_text(encoding="utf-8"))
        payload["stage"] = "REVIEWER"
        result_path.write_text(json.dumps(payload), encoding="utf-8")
        with pytest.raises(TopicBelongingExecutionError):
            service.import_result(episode.episode_id, result_path)
    finally:
        _cleanup_handoffs(created, service)


def test_roundtrip_valid_result_with_wrong_persisted_checkpoint_is_blocked(tmp_path: Path) -> None:
    created: list[Path] = []
    service = None
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        workflow_path = episode.folder / "workflow_state.json"
        workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
        workflow["handoff_id"] = "HANDOFF-WRONG-CHECKPOINT"
        workflow_path.write_text(json.dumps(workflow), encoding="utf-8")
        result_path = _result_for(package, _cognitive_proposal(), "RESULT-WRONG-CHECKPOINT-P2", tmp_path / "wrong-checkpoint.json")
        with pytest.raises(TopicBelongingExecutionError, match="CHECKPOINT_BINDING"):
            service.import_result(episode.episode_id, result_path)
    finally:
        _cleanup_handoffs(created, service)


def test_roundtrip_producer_result_provenance_mismatch_is_blocked(tmp_path: Path) -> None:
    created: list[Path] = []
    service = None
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        service.import_result(episode.episode_id, _result_for(package, _cognitive_proposal(), "RESULT-ENRICHMENT-RUN", tmp_path / "enrichment.json"))
        service.resume(episode.episode_id)
        _, _, package = _pending_package(episode)
        created.append(package)
        topic = _materialized_topic_input(episode)
        cognitive_assessment = _cognitive_assessment(topic, "RESULT-PRODUCER-DECLARED")
        result_path = _result_for(package, cognitive_assessment, "RESULT-PRODUCER-ACTUAL", tmp_path / "producer.json")
        payload = json.loads(result_path.read_text(encoding="utf-8"))
        payload["provenance"]["run_id"] = "RESULT-PRODUCER-DECLARED"
        result_path.write_text(json.dumps(payload), encoding="utf-8")
        with pytest.raises(TopicBelongingExecutionError, match="ROUNDTRIP_RESULT_PROVENANCE_BINDING_INVALID"):
            service.import_result(episode.episode_id, result_path)
    finally:
        _cleanup_handoffs(created, service)


def test_roundtrip_new_service_revalidates_tampered_persisted_envelope(tmp_path: Path) -> None:
    created: list[Path] = []
    service = None
    restarted = None
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        result_path = _result_for(package, _cognitive_proposal(), "RESULT-RESTART-P2", tmp_path / "restart.json")
        service.import_result(episode.episode_id, result_path)
        persisted = json.loads((episode.folder / "roundtrip_results.json").read_text(encoding="utf-8"))["results"][0]
        stored_result = episode.folder / persisted["result_path"]
        envelope = json.loads(stored_result.read_text(encoding="utf-8"))
        envelope["output"]["proposed_angle"] = "altered-after-import"
        stored_result.write_text(json.dumps(envelope), encoding="utf-8")
        restarted = _service(tmp_path, getattr(service, "_p2_test_vault_root"))
        with pytest.raises(TopicBelongingExecutionError, match="PERSISTED_ENVELOPE"):
            restarted.resume(episode.episode_id)
    finally:
        _cleanup_handoffs(created, restarted or service)


def test_roundtrip_new_service_continues_from_persisted_checkpoint(tmp_path: Path) -> None:
    created: list[Path] = []
    service = None
    restarted = None
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        service.import_result(episode.episode_id, _result_for(package, _cognitive_proposal(), "RESULT-RESTART-CONTINUE", tmp_path / "restart-continue.json"))
        restarted = _service(tmp_path, getattr(service, "_p2_test_vault_root"))
        resumed = restarted.resume(episode.episode_id)
        assert resumed["state"]["status"] == "PENDING_EXTERNAL_RESULT"
        workflow = json.loads((episode.folder / "workflow_state.json").read_text(encoding="utf-8"))
        assert workflow["stage"] == "PRODUCER"
        created.append(Path(workflow["handoff_package_ref"]))
    finally:
        _cleanup_handoffs(created, restarted or service)


def test_roundtrip_resume_rejects_incompatible_next_stage(tmp_path: Path) -> None:
    created: list[Path] = []
    service = None
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        service.import_result(episode.episode_id, _result_for(package, _cognitive_proposal(), "RESULT-BAD-NEXT-STAGE", tmp_path / "bad-next-stage.json"))
        workflow_path = episode.folder / "workflow_state.json"
        workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
        workflow["next_stage"] = "UNKNOWN"
        workflow_path.write_text(json.dumps(workflow), encoding="utf-8")
        with pytest.raises(TopicBelongingExecutionError, match="NEXT_STAGE_INVALID"):
            service.resume(episode.episode_id)
    finally:
        _cleanup_handoffs(created, service)


def test_roundtrip_resume_is_idempotent_while_next_handoff_is_pending(tmp_path: Path) -> None:
    created: list[Path] = []
    service = None
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        service.import_result(episode.episode_id, _result_for(package, _cognitive_proposal(), "RESULT-RESUME-IDEMPOTENT", tmp_path / "resume.json"))
        first = service.resume(episode.episode_id)
        first_package = first["state"].get("handoff_package_ref")
        second = service.resume(episode.episode_id)
        assert second["state"]["status"] == "PENDING_EXTERNAL_RESULT"
        assert second["state"].get("handoff_package_ref") == first_package
    finally:
        _cleanup_handoffs(created, service)


def test_roundtrip_handoff_has_no_completion_gate_or_model_selection(tmp_path: Path) -> None:
    created: list[Path] = []
    service = None
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        data = json.loads(package.read_text(encoding="utf-8"))
        assert "completion_gate" not in data
        assert data["execution_family"] == "AGENT_HARNESS"
        assert data["execution_route"] == "agent_harness"
        assert data["model_override"] is None
    finally:
        _cleanup_handoffs(created, service)


def test_roundtrip_convergence_callbacks_fail_closed_for_invalid_boundary() -> None:
    callbacks = TopicBelongingTechnicalWorkflow._convergence_callbacks(
        "roundtrip:test:invalid",
        stage="unknown",
        output_schema="unknown",
        inputs=[],
        mock_output={"fixture": True},
    )
    assert callbacks["implement"]()["passed"] is False
    assert callbacks["verify"]()["passed"] is False
    assert callbacks["adversarial_review"]()["passed"] is False
    assert callbacks["repair"]({"stage": "unknown"})["passed"] is False
