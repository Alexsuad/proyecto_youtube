from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from src.ai.contracts import InputArtifact
from src.core.contract_validation import validate_against_schema, validate_claims_ledger, validate_work_lifecycle, validate_work_research_dossier
from src.core.status import GateStatus
from src.scripts.b5_i2_gate import evaluate as evaluate_b5_i2
from src.scripts.channel_intelligence import canonical_checksum, evaluate_topic_belonging_gate, validate_assessment, validate_topic_input
from src.scripts.topic_belonging_flow import bind_episode_brief_to_topic_decision
from src.scripts.evidence_sufficiency_gate import evaluate as evaluate_evidence
from src.scripts.qa_brief_research import evaluate as evaluate_brief_research
from src.scripts.run_b5_i2_semantic_audit import execute_b5_i2_audit
from src.scripts.thesis_provisional_gate import evaluate as evaluate_thesis
from tests.core.test_channel_intelligence import assessment, decision, topic_input
from tests.core.test_plan007_p2_contracts import _claim
from tests.core.test_work_lifecycle import _exception, _final_pack
from tests.harness.test_b5_i2 import _refresh_b5_i2_audit, _refresh_execution_registry, _write_case

ROOT = Path(__file__).resolve().parents[2]
EP = "EP-001"


def _write(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def _dossier(stage: str) -> dict:
    data = {"dossier_id": "D-W1", "dossier_version": "1.0.0", "episode_id": EP, "research_id": "RP-001", "evidence_report_id": "ER-001", "work": {"material_id": "M1", "title": "Obra sintetica M1", "creator": "Autor sintetico", "consulted_representations": [{"representation_kind": "ORIGINAL_WORK", "edition_or_version": "fixture-1", "consulted_locator": "fixture://M1"}]}, "dossier_stage": stage, "pending_items": ["Completar investigacion"] if stage == "IDENTIFIED" else [], "confidence": "LOW" if stage == "IDENTIFIED" else "HIGH", "created_at": "2026-08-18T10:00:00Z"}
    if stage == "RESEARCH_REVIEW_PENDING":
        data.update({"analysis_references": [{"analysis_id": "A-1", "material_id": "M1"}], "question_and_thesis_relation": {"central_question_ref": "question:EP", "provisional_thesis_ref": "thesis:TH-001", "demonstrates_analysis_ref": "A-1", "does_not_establish_analysis_ref": "A-1", "main_interpretation_analysis_ref": "A-1", "rival_interpretation_analysis_refs": ["A-1"]}, "claim_dispositions": {"claims_ledger_id": "CL-P6A-001", "authority_status": "REPRESENTATION_ONLY_IR4_PENDING", "candidate_allowed_claim_ids": ["C-1"], "candidate_limited_claim_ids": [], "candidate_blocked_claim_ids": []}, "overinterpretation_risk": {"level": "LOW", "rationale": "Fixture acotada."}, "candidate_editorial_function_analysis_ref": "A-1", "locators": [{"analysis_id": "A-1", "locator": "fixture://W1/scene"}], "work_use_sufficiency": {"intended_use": "B5_I2_CONTROLLED_HARNESS", "status": "IR7_FIDELITY_AUDIT_REQUIRED"}, "research_stop_decision_ref": "RSD-W1", "independent_fidelity_audit": {"audit_reference": None, "dependency": "FUNCTIONAL_DECISION_REQUIRED"}})
    return data


def test_p6a_topic_first_vertical_reaches_canonical_b5_i2_route(tmp_path: Path) -> None:
    entry = topic_input(entry_mode="TOPIC_FIRST"); entry.pop("narrative_work")
    assert validate_topic_input(entry) == []
    assessed = assessment(topic_input(entry_mode="TOPIC_FIRST", narrative_work="NO_WORK_YET"))
    candidate_ids = ["M1", "M2", "M3", "M4", "M5"]
    enriched = {**entry, "narrative_work": "Obra consolidada durante investigacion", "research_ref": "RP-001", "narrative_door_evidence_refs": ["ER-001"], "candidate_work_refs": candidate_ids}
    assert validate_assessment(assessed, enriched) == []
    reviewed = decision(assessed, pre_b5_i1_evidence={"topic_input_checksum": canonical_checksum(enriched, "input"), "research_ref": enriched["research_ref"], "narrative_door_evidence_refs": enriched["narrative_door_evidence_refs"], "candidate_work_refs": enriched["candidate_work_refs"]})
    paths = _write_case(tmp_path)
    brief = json.loads(paths["brief"].read_text(encoding="utf-8")); brief.update({"episode_id": EP, "profile_version": "1.2.2", "profile_checksum": "2c373b88860a2d17e3f625adfac267a173b5f7f586a6c87bed2c14c0d254cd2b"}); brief = bind_episode_brief_to_topic_decision(brief, reviewed); _write(paths["brief"], brief)
    for name in ("research", "evidence", "audit", "provisional"):
        value = json.loads(paths[name].read_text(encoding="utf-8")); value["episode_id"] = EP; _write(paths[name], value)
    analysis_value = json.loads(paths["analysis"].read_text(encoding="utf-8")); analysis_value["episode_id"] = EP; analysis_value["artifact_version"] = "1.0.0"; _write(paths["analysis"], analysis_value)
    assert validate_against_schema(brief, "episode_brief") == []
    _write(paths["brief"].parent / "episode_brief.json", brief); _write(paths["brief"].parent / "research_pack.json", json.loads(paths["research"].read_text(encoding="utf-8")))
    brief_gate = evaluate_brief_research(paths["brief"].parent, active_profile_path=ROOT / "config/active_editorial_profile.json")
    assert brief_gate.status is GateStatus.PASS, brief_gate.violations
    assert evaluate_evidence(paths["evidence"], EP).status in {GateStatus.PASS, GateStatus.WARN}
    assert evaluate_thesis(paths["provisional"], paths["research"], paths["evidence"], "TH-001").status in {GateStatus.PASS, GateStatus.WARN}
    curation = json.loads(paths["curation"].read_text(encoding="utf-8"))
    curation["selection_stage"] = "FINAL"
    _write(paths["curation"], curation)
    audit = json.loads(paths["audit"].read_text(encoding="utf-8"))
    for field, key in (("brief_checksum", "brief"), ("research_checksum", "research"), ("evidence_report_checksum", "evidence"), ("thesis_checksum", "provisional")):
        audit[field] = hashlib.sha256(paths[key].read_bytes()).hexdigest()
    _write(paths["audit"], audit)
    _refresh_b5_i2_audit(paths); _refresh_execution_registry(paths); _refresh_b5_i2_audit(paths)

    lifecycle, _ = _final_pack(); lifecycle["episode_id"] = EP; lifecycle["research_id"] = "RP-001"
    def remap_work_ids(value):
        if isinstance(value, dict):
            return {key: remap_work_ids(item) for key, item in value.items()}
        if isinstance(value, list):
            return [remap_work_ids(item) for item in value]
        if isinstance(value, str) and value.startswith("W") and value[1:].isdigit():
            return "M" + value[1:]
        return value
    lifecycle = remap_work_ids(lifecycle)
    lifecycle["final_selection"] = {"selected_work_ids": ["M1"], "format_policy_ref": "policies/script_product/main_episode_format_policy.md", "range_status": "EXCEPTION", "curation_ref": "C-1", "exception": _exception()}
    early, final = _dossier("RESEARCH_IN_PROGRESS"), _dossier("RESEARCH_REVIEW_PENDING")
    early["evidence_report_id"] = "ER-001"
    ledger = {"ledger_id": "CL-P6A-001", "script_version": "1.0.0", "claims": [_claim("C-1")]}
    analysis_value = json.loads(paths["analysis"].read_text(encoding="utf-8"))
    analysis_checksum = hashlib.sha256(json.dumps(analysis_value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    ledger_checksum = hashlib.sha256(json.dumps(ledger, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    final["analysis_references"][0].update({"material_id": "M1", "artifact_version": "1.0.0", "artifact_checksum": analysis_checksum})
    final["claim_dispositions"].update({"claims_ledger_version": "1.0.0", "claims_ledger_checksum": ledger_checksum})
    assert validate_work_research_dossier(early) == []
    assert validate_against_schema(final, "work_research_dossier") == []
    assert validate_work_research_dossier(final, ledger, [analysis_value]) == []
    assert validate_claims_ledger(ledger) == []
    lifecycle_dossiers = [final]
    for material_id in ("M2", "M3"):
        dossier = json.loads(json.dumps(final))
        dossier["dossier_id"] = f"D-W{material_id[1:]}"
        dossier["work"]["material_id"] = material_id
        dossier["work"]["title"] = f"Obra sintetica {material_id}"
        dossier["analysis_references"][0]["material_id"] = material_id
        lifecycle_dossiers.append(dossier)
    assert any("FUNCTIONAL_DECISION_REQUIRED" in item for item in validate_work_lifecycle(lifecycle, dossiers=lifecycle_dossiers))
    candidate_ids = lifecycle["screening"]["candidate_work_ids"]
    assert len(candidate_ids) == 5 and lifecycle["entry_mode"] == "TOPIC_FIRST" and lifecycle["anchor_work_id"] is None
    assert reviewed["pre_b5_i1_evidence"]["candidate_work_refs"] == ["M1", "M2", "M3", "M4", "M5"]
    assert reviewed["pre_b5_i1_evidence"]["research_ref"] == final["research_id"] == "RP-001"
    boundary_result = evaluate_topic_belonging_gate(reviewed, assessed, enriched, work_lifecycle=lifecycle, research_dossier=early)
    assert boundary_result["status"] == "PASS"
    _write(tmp_path / "topic_input.json", enriched); _write(tmp_path / "assessment.json", assessed); _write(tmp_path / "decision.json", reviewed)
    _write(tmp_path / "lifecycle.json", lifecycle); _write(tmp_path / "dossier.json", early)
    flow = subprocess.run([sys.executable, "-m", "src.scripts.topic_belonging_flow", "--input", str(tmp_path / "topic_input.json"), "--assessment", str(tmp_path / "assessment.json"), "--decision", str(tmp_path / "decision.json"), "--work-lifecycle", str(tmp_path / "lifecycle.json"), "--research-dossier", str(tmp_path / "dossier.json")], cwd=ROOT, capture_output=True, text=True)
    assert flow.returncode == 0, flow.stdout + flow.stderr
    flow_result = json.loads(flow.stdout)
    assert flow_result["status"] == "PASS"
    assert flow_result["decision"] == reviewed["decision"]
    assert brief["topic_belonging_decision_ref"] == reviewed["decision_id"]
    assert brief["topic_belonging_decision_checksum"] == reviewed["provenance"]["output_checksum"]
    assert final["claim_dispositions"]["claims_ledger_id"] == ledger["ledger_id"]

    files = {"research": paths["research"], "evidence_report": paths["evidence"], "provisional_thesis": paths["provisional"], "analysis": paths["analysis"], "curation": paths["curation"], "refined_thesis": paths["thesis"], "script_promise": paths["script_promise"]}
    ids = {"research": "research_id", "evidence_report": "report_id", "provisional_thesis": "thesis_id", "analysis": "analysis_id", "curation": "curation_id", "refined_thesis": "thesis_id", "script_promise": "promise_id"}
    artifacts = [InputArtifact(kind, json.loads(path.read_text(encoding="utf-8"))[ids[kind]], path, "RUN-" + kind.upper()) for kind, path in files.items()]
    b5_gate = evaluate_b5_i2({key: paths[key] for key in ("brief", "research", "evidence", "audit", "provisional")}, [paths["analysis"]], paths["curation"], paths["thesis"], paths["script_promise"], paths["b5_i2_audit"], paths["execution_registry"], EP, topic_belonging_decision=reviewed, work_lifecycle=lifecycle, topic_belonging_input=enriched, topic_belonging_assessment=assessed, research_dossier=early)
    assert b5_gate.status is GateStatus.BLOCKED
    assert b5_gate.violations == []
    semantic = b5_gate.evidence["semantic_audit"]
    assert semantic["TECHNICAL_INTEGRITY"] == "PASS"
    assert semantic["producer_output_schema"] == "PASS"
    assert semantic["producer_output_closed"] == "PASS"
    assert semantic["auditor_output_schema"] == "PASS"
    assert semantic["auditor_independence"] == "PASS"
    assert semantic["artifact_checksum_match"] == "PASS"
    assert semantic["provenance_complete"] == "PASS"
    assert semantic["SEMANTIC_EDITORIAL_DECISION"] == "NOT_EVALUATED"
    assert semantic["OPERATIONAL_READINESS"] == "BLOCKED"
    omitted_lineage_gate = evaluate_b5_i2({key: paths[key] for key in ("brief", "research", "evidence", "audit", "provisional")}, [paths["analysis"]], paths["curation"], paths["thesis"], paths["script_promise"], paths["b5_i2_audit"], paths["execution_registry"], EP)
    assert any("declara TopicBelongingDecision" in violation for violation in omitted_lineage_gate.violations)
    auditor = execute_b5_i2_audit(artifacts=artifacts, output_path=tmp_path / "canonical_b5_i2_audit.json", registry_path=paths["execution_registry"], episode_id=EP, provider="mock", execution_mode="mock", model="synthetic-fixture", mock_output=json.loads(paths["b5_i2_audit"].read_text(encoding="utf-8")))
    assert auditor.status.value == "BLOCKED_BY_SEMANTIC_EVALUATOR"
    assert auditor.run_id and auditor.input_manifest_checksum
    assert not (tmp_path / "canonical_b5_i2_audit.json").exists()
    forged = json.loads(json.dumps(reviewed))
    forged["pre_b5_i1_evidence"]["research_ref"] = "FORGED-RESEARCH"
    forged["provenance"]["output_checksum"] = canonical_checksum(forged, "decision")
    forged_gate = evaluate_b5_i2({key: paths[key] for key in ("brief", "research", "evidence", "audit", "provisional")}, [paths["analysis"]], paths["curation"], paths["thesis"], paths["script_promise"], paths["b5_i2_audit"], paths["execution_registry"], EP, topic_belonging_decision=forged, work_lifecycle=lifecycle, topic_belonging_input=enriched, topic_belonging_assessment=assessed, research_dossier=early)
    assert any("PRE_B5_I1_EVIDENCE_RESEARCH_REF_MISMATCH" in violation or "EVIDENCE_RESEARCH_NOT_BOUND" in violation for violation in forged_gate.violations)
    # The synthetic auditor is terminal evidence only; it cannot authorize production.
