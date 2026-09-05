from copy import deepcopy
import json
from pathlib import Path

import pytest

from src.application.research_b2 import _checksum
from src.application.research_b4 import ResearchB4Error, ResearchB4Orchestrator, ResearchB4Persistence
from src.core.contract_validation import validate_against_schema, validate_research_ready_manifest
from src.core.gate_runtime import validate_gate_result
from src.core.gate_result import GateResult
from src.core.invalidation import InvalidationEngine
from tests.core.test_plan012_m4_b3_deep_research import _m4_context
from tests.core.test_plan012_m4_b3_deep_research import _run_m4
from tests.core.test_plan012_m3_b2_base_research import _run as _run_b2
from tests.core.test_all_schemas import VALID_FIXTURES
from tests.core.test_plan012_m5_b3_post_deep import (
    _claims,
    _comparison,
    _read,
    _run_m5,
    _thesis,
)


def _audit(request, *, decision="PASS", finding_status=None):
    input_refs = request.input_artifacts
    evidence_ref = input_refs[0]["artifact_id"]
    criteria = request.prepared_contract["input_payload"]["audit_scope"]["required_criteria"]
    findings = [
        {
            "criterion": criterion,
            "status": finding_status if finding_status and index == 0 else "SATISFIED",
            "evidence_refs": [evidence_ref],
            "limitations": ["El alcance permanece explícito."] if finding_status and index == 0 else [],
            "judgment_basis": f"El auditor revisó el criterio {criterion} contra la cadena Research recibida.",
        }
        for index, criterion in enumerate(criteria)
    ]
    return {
        "audit_id": "COGNITION-MUST-NOT-OWN-THIS",
        "audit_version": "9.9.9",
        "audited_artifacts": [{"artifact_id": "FORGED", "checksum": "0" * 64, "producer_run_id": "FORGED"}],
        "research_ready_state": "RESEARCH_READY",
        "independence_result": "PASS",
        "findings": findings,
        "evidence_refs": [evidence_ref],
        "limitations": [],
        "defects": [],
        "correction_routes": [],
        "decision": decision,
    }


def _baseline_from_b2(b2_result):
    plan = _read(b2_result["research_plan"])
    plan["target_final_works_decision"] = {
        "status": "CONFIRMED",
        "requested_count": 3,
        "decision_basis": "Resolución explícita de fixture para el formato vigente.",
        "decision_ref": "decision:fixture-target-final-works",
    }
    return {
        "research_plan": plan,
        "phenomenon_base_research": _read(b2_result["phenomenon_base_research"]),
        "work_discovery": _read(b2_result["work_discovery"]),
        "base_research_pool": _read(b2_result["base_research_pool"])["dossiers"],
        "preliminary_fidelity": _read(b2_result["preliminary_fidelity"])["dossiers"],
        "initial_sufficiency": _read(b2_result["initial_sufficiency"])["dossiers"],
        "provisional_thesis": _read(b2_result["provisional_thesis"]),
        "research_comparison": _read(b2_result["research_comparison"]),
        "deepening_targets": b2_result["deepening_targets"],
        "lifecycle": b2_result["lifecycle_projection"],
    }


def _chain_from_runs(tmp_path, b2_result, m4_result, m5_result):
    b2_manifest_ref = b2_result["execution_manifest"]
    b2_manifest = _read(b2_manifest_ref)
    m4_manifest_ref = m4_result["execution_manifest"]
    m4_manifest = _read(m4_manifest_ref)
    source_report = deepcopy(VALID_FIXTURES["source_access_and_evidence_report"])
    source_report.update({
        "episode_id": "EP-1",
        "research_id": "RP-FIXTURE",
        "brief_version": "1.0.0",
    })
    source_path = tmp_path / "source_access_and_evidence_report.json"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(json.dumps(source_report, ensure_ascii=False), encoding="utf-8")
    source_ref = {
        "artifact_id": "RP-FIXTURE:SOURCE_ACCESS",
        "artifact_kind": "SourceAccessAndEvidenceReport",
        "artifact_version": "2.0.0",
        "path": str(source_path),
        "checksum": _checksum(source_report),
    }
    refs = [b2_manifest_ref, *b2_manifest["artifacts"], m4_manifest_ref, *m4_manifest["artifacts"], source_ref]
    m5_ref = m5_result["execution_manifest"]
    registry = deepcopy(VALID_FIXTURES["execution_provenance_registry"])
    base_run = deepcopy(registry["runs"][0])

    def provenance_run(ref, run_id, *, actor_id, role="RESEARCH_AND_CURATION", executor_id):
        run = deepcopy(base_run)
        run.update({
            "run_id": run_id,
            "episode_id": "EP-1",
            "role": role,
            "role_id": role,
            "agent_id": actor_id,
            "actual_executor": executor_id,
            "status": "SUCCEEDED",
            "output_artifact_ids": [f"{ref['artifact_kind']}:{ref['artifact_id']}"],
            "output_versions": [ref["artifact_version"]],
            "output_checksums": [ref["checksum"]],
            "outputs": [{
                "artifact_kind": "semantic_audit",
                "artifact_id": ref["artifact_id"],
                "artifact_ref": f"{ref['artifact_kind']}:{ref['artifact_id']}",
                "checksum": ref["checksum"],
            }],
        })
        return run

    all_refs = [m5_ref, *_read(m5_ref)["m5_outputs"], *refs]
    unique_refs = {
        (ref["artifact_id"], ref["artifact_kind"], ref["artifact_version"], ref["checksum"]): ref
        for ref in all_refs
    }
    producer_run = provenance_run(
        m5_ref, "M5-RUN-ACTUAL", actor_id="M5_PRODUCER_ACTUAL", executor_id="M5-EXECUTOR-ACTUAL",
    )
    upstream_runs = [
        provenance_run(
            ref,
            f"UPSTREAM-RUN-{index:03d}",
            actor_id=f"UPSTREAM-PRODUCER-{index:03d}",
            executor_id=f"UPSTREAM-EXECUTOR-{index:03d}",
        )
        for index, ref in enumerate(unique_refs.values(), start=1)
        if ref is not m5_ref and not (
            ref["artifact_id"] == m5_ref["artifact_id"]
            and ref["artifact_kind"] == m5_ref["artifact_kind"]
            and ref["checksum"] == m5_ref["checksum"]
        )
    ]
    registry["runs"] = [producer_run, *upstream_runs]
    repository_root = tmp_path / "canonical_repo"
    (repository_root / "config").mkdir(parents=True, exist_ok=True)
    (repository_root / "config" / "execution_provenance_policy.json").write_text(
        json.dumps({"schema_version": "1.0.0", "canonical_registry_path": "output/execution_provenance_registry.json"}),
        encoding="utf-8",
    )
    registry_path = repository_root / "output" / "execution_provenance_registry.json"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8")
    provenance = {
        "producer_provenance": {
            "actor_id": "M5_PRODUCER_ACTUAL",
            "run_id": "M5-RUN-ACTUAL",
            "executor_id": "M5-EXECUTOR-ACTUAL",
            "role": "RESEARCH_AND_CURATION",
            "provenance_ref": "M5-RUN-PROVENANCE",
            "artifact_ref": {key: m5_ref[key] for key in ("artifact_id", "artifact_kind", "artifact_version", "checksum")},
        },
        "repository_root": str(repository_root),
        "execution_provenance_registry_ref": "output/execution_provenance_registry.json",
    }
    provenance["producer_provenance"]["provenance_ref"] = provenance["execution_provenance_registry_ref"]
    return {"artifact_refs": refs}, provenance


def _run_full_m5(tmp_path, *, m5_cognitive=None, fidelity="APTA", m4_mutator=None):
    b2_result, _ = _run_b2(
        tmp_path / "b2",
        work_ids=("W1", "W2", "W3"),
        fidelity=fidelity,
    )
    baseline = _baseline_from_b2(b2_result)
    m4_result, _ = _run_m4(tmp_path / "m4", baseline=baseline, fidelity=fidelity)
    if m4_mutator is not None:
        m4_result = m4_mutator(m4_result)
    m5_result, _ = _run_m5(
        tmp_path / "m5", baseline=baseline, m4_result=m4_result, cognitive=m5_cognitive,
    )
    chain, provenance = _chain_from_runs(tmp_path, b2_result, m4_result, m5_result)
    return m5_result, chain, provenance


def _mutate_m4_phenomenon_stop_to_more(m4_result):
    manifest_ref = m4_result["execution_manifest"]
    manifest = _read(manifest_ref)
    stop_ref = next(
        ref for ref in manifest["artifacts"]
        if ref["artifact_kind"] == "ResearchStopDecisionCollection"
        and ":M4:" in ref["artifact_id"]
    )
    payload = _read(stop_ref)
    for decision in payload["dossiers"]:
        decision["sufficiency_status"] = "MORE_RESEARCH_REQUIRED"
        decision["pending_matters"] = ["La evidencia fenomenológica requiere investigación adicional."]
    Path(stop_ref["path"]).write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    stop_ref["checksum"] = _checksum(payload)
    for key in ("deep_phenomenon_sufficiency", "deep_work_sufficiency"):
        if m4_result[key]["artifact_id"] == stop_ref["artifact_id"]:
            m4_result[key]["checksum"] = stop_ref["checksum"]
    Path(manifest_ref["path"]).write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    manifest_ref["checksum"] = _checksum(manifest)
    return m4_result


def _run_m6(tmp_path, *, audit=None, m5_result=None, research_chain=None, provenance=None, context_overrides=None):
    state_root = tmp_path / "state"
    if m5_result is None:
        m5_result, research_chain, provenance = _run_full_m5(state_root)
    assert research_chain is not None
    assert provenance is not None

    def cognitive(request):
        assert request.stage == "M6_INDEPENDENT_RESEARCH_AUDIT"
        return audit(request) if callable(audit) else _audit(request)

    context = _m4_context()
    context.update(provenance)
    if context_overrides:
        context.update(context_overrides)
    result = ResearchB4Orchestrator(
        cognitive,
        ResearchB4Persistence(state_root / "m5"),
        _test_provenance_repository_root=Path(provenance["repository_root"]),
    ).run_m6(m5_result, context=context, research_chain=research_chain)
    return result, m5_result, state_root


def _canonical_registry_path(provenance):
    return Path(provenance["repository_root"]) / "output" / "execution_provenance_registry.json"


def _run_sufficient_m5(tmp_path):
    def cognitive(request):
        if request.stage == "M5_CLAIMS_EVIDENCE_CONSOLIDATION":
            value = _claims()
            for claim in value["claims"]:
                claim["research_sufficiency"] = "SUFFICIENT_FOR_INTENDED_USE"
                claim["claim_decision"] = "CLAIM_ALLOWED"
                claim["limitations"] = ""
                claim["materiality"]["return_route_code"] = "AUTHORIZE_INTENDED_USE_ONLY"
            return value
        if request.stage == "M5_POST_DEEP_SET_REEVALUATION":
            return _comparison(["W1", "W2", "W3"])
        value = _thesis("RP-FIXTURE:THESIS:PROVISIONAL")
        return value

    return _run_full_m5(tmp_path, m5_cognitive=cognitive)


def _run_blocked_claim_m5(tmp_path):
    def cognitive(request):
        if request.stage == "M5_CLAIMS_EVIDENCE_CONSOLIDATION":
            value = _claims()
            blocked = value["claims"][0]
            blocked["research_sufficiency"] = "BLOCKED_BY_EVIDENCE"
            blocked["claim_decision"] = "CLAIM_BLOCKED"
            blocked["limitations"] = "La evidencia no permite afirmar este claim."
            blocked["return_route"] = "No afirmar el claim; retirar su uso downstream."
            blocked["materiality"]["return_route_code"] = "REMOVE_REPLACE_OR_REFORMULATE"
            for claim in value["claims"][1:]:
                claim["research_sufficiency"] = "SUFFICIENT_FOR_INTENDED_USE"
                claim["claim_decision"] = "CLAIM_ALLOWED"
                claim["limitations"] = ""
                claim["materiality"]["return_route_code"] = "AUTHORIZE_INTENDED_USE_ONLY"
            return value
        if request.stage == "M5_POST_DEEP_SET_REEVALUATION":
            return _comparison(["W1", "W2", "W3"])
        return _thesis("RP-FIXTURE:THESIS:PROVISIONAL")

    return _run_full_m5(tmp_path, m5_cognitive=cognitive)


def _run_more_research_claim_m5(tmp_path):
    def cognitive(request):
        if request.stage == "M5_CLAIMS_EVIDENCE_CONSOLIDATION":
            value = _claims()
            pending = value["claims"][0]
            pending["research_sufficiency"] = "MORE_RESEARCH_REQUIRED"
            pending["claim_decision"] = "CLAIM_LIMITED"
            pending["limitations"] = "La evidencia adicional sigue siendo necesaria."
            pending["pending_matters"] = ["EVIDENCE_REQUIRED"]
            pending["return_route"] = "RETURN_TO_RESEARCH"
            pending["materiality"]["return_route_code"] = "RETURN_TO_RESEARCH"
            for claim in value["claims"][1:]:
                claim["research_sufficiency"] = "SUFFICIENT_FOR_INTENDED_USE"
                claim["claim_decision"] = "CLAIM_ALLOWED"
                claim["limitations"] = ""
                claim["materiality"]["return_route_code"] = "AUTHORIZE_INTENDED_USE_ONLY"
            return value
        if request.stage == "M5_POST_DEEP_SET_REEVALUATION":
            return _comparison(["W1", "W2", "W3"])
        return _thesis("RP-FIXTURE:THESIS:PROVISIONAL")

    return _run_full_m5(tmp_path, m5_cognitive=cognitive)


def test_m6_emits_audit_manifest_and_gate_from_exact_m5_package(tmp_path):
    result, m5_result, _ = _run_m6(tmp_path)
    assert result["status"] == "RESEARCH_READY_WITH_LIMITATIONS"
    audit = _read(result["independent_research_audit"])
    manifest = _read(result["research_ready_manifest"])
    gate = _read(result["research_ready_gate"])
    assert audit["audit_type"] == "RESEARCH_PACKAGE"
    assert any(
        item["artifact_id"] == m5_result["execution_manifest"]["artifact_id"]
        for item in audit["audited_artifacts"]
    )
    assert manifest["research_ready_state"] == "RESEARCH_READY_WITH_LIMITATIONS"
    assert validate_research_ready_manifest(manifest) == []
    assert gate["status"] == "WARN"
    validate_gate_result(GateResult.from_dict(gate))


def test_m6_requires_explicit_methodological_coverage() -> None:
    from src.application.research_b4 import M6_REQUIRED_AUDIT_CRITERIA

    assert {
        "SOURCE_APPROPRIATENESS_AND_INDEPENDENCE",
        "CLAIM_STRENGTH_VS_EVIDENCE",
        "MATERIAL_PHENOMENON_DEEPENING",
        "CONFIRMATION_BIAS",
        "POST_DEEP_SET_REEVALUATION",
        "SET_DIVERSITY_MISSING_PERSPECTIVES_OVERINTERPRETATION",
        "CLAIM_BLOCKED_DEPENDENCY",
        "RESEARCH_METHOD_REASONABLENESS",
    } <= M6_REQUIRED_AUDIT_CRITERIA


def test_m6_requires_semantic_basis_for_each_finding(tmp_path):
    def audit_without_basis(request):
        value = _audit(request)
        value["findings"][0].pop("judgment_basis")
        return value

    with pytest.raises(ResearchB4Error, match="M6_AUDIT_JUDGMENT_BASIS_REQUIRED"):
        _run_m6(tmp_path, audit=audit_without_basis)


def test_m6_limited_finding_requires_explicit_limitation(tmp_path):
    def limited_without_limit(request):
        value = _audit(request, finding_status="LIMITED")
        value["findings"][0]["limitations"] = []
        return value

    with pytest.raises(ResearchB4Error, match="M6_AUDIT_LIMITATION_REQUIRED"):
        _run_m6(tmp_path, audit=limited_without_limit)


def test_m6_valid_sufficient_package_reaches_research_ready(tmp_path):
    m5_result, chain, provenance = _run_sufficient_m5(tmp_path / "m5")
    result, _, _ = _run_m6(
        tmp_path / "run", m5_result=m5_result, research_chain=chain, provenance=provenance,
    )
    assert result["status"] == "RESEARCH_READY"
    assert _read(result["research_ready_gate"])["status"] == "PASS"


def test_m6_blocked_claim_can_be_restricted_without_blocking_the_whole_package(tmp_path):
    m5_result, chain, provenance = _run_blocked_claim_m5(tmp_path / "m5")
    result, _, _ = _run_m6(
        tmp_path / "run", m5_result=m5_result, research_chain=chain, provenance=provenance,
    )
    assert result["status"] == "RESEARCH_READY_WITH_LIMITATIONS"
    manifest = _read(result["research_ready_manifest"])
    assert any(
        item["kind"] == "CLAIM_BLOCKED" and "C-EXT" in item["statement"]
        for item in manifest["downstream_restrictions"]
    )
    gate = _read(result["research_ready_gate"])
    assert gate["status"] == "WARN"
    assert not any(item.startswith("CLAIM_BLOCKED:") for item in gate["violations"])


def test_m6_necessary_blocked_claim_remains_a_global_blocker(tmp_path):
    def audit_necessary_blocked_claim(request):
        value = _audit(request, decision="REQUEST_CHANGES")
        finding = next(
            item for item in value["findings"]
            if item["criterion"] == "CLAIM_BLOCKED_DEPENDENCY"
        )
        finding["status"] = "NOT_SATISFIED"
        finding["limitations"] = [
            "La tesis y el uso previsto dependen del claim bloqueado."
        ]
        finding["judgment_basis"] = (
            "Sin este claim no queda defendible la tesis ni el uso previsto."
        )
        return value

    m5_result, chain, provenance = _run_blocked_claim_m5(tmp_path / "m5")
    result, _, _ = _run_m6(
        tmp_path / "run",
        audit=audit_necessary_blocked_claim,
        m5_result=m5_result,
        research_chain=chain,
        provenance=provenance,
    )
    assert result["status"] == "NOT_RESEARCH_READY"
    gate = _read(result["research_ready_gate"])
    assert "AUDIT_FINDING_PENDING:CLAIM_BLOCKED_DEPENDENCY" in gate["violations"]


def test_m6_material_claim_more_research_required_remains_a_global_blocker(tmp_path):
    m5_result, chain, provenance = _run_more_research_claim_m5(tmp_path / "m5")
    result, _, _ = _run_m6(
        tmp_path / "run",
        m5_result=m5_result,
        research_chain=chain,
        provenance=provenance,
    )
    assert result["status"] == "NOT_RESEARCH_READY"
    gate = _read(result["research_ready_gate"])
    assert any(
        item.startswith("RESEARCH_STOP_MORE_RESEARCH_REQUIRED:")
        for item in gate["violations"]
    )


def test_m6_rejects_same_id_m5_output_with_different_checksum(tmp_path):
    m5_result, chain, provenance = _run_full_m5(tmp_path / "m5")
    altered = deepcopy(m5_result)
    altered["claims_ledger"]["checksum"] = "0" * 64
    with pytest.raises(ResearchB4Error, match="M6_M5_CANONICAL_BINDING_INVALID:ClaimsLedger"):
        _run_m6(tmp_path / "run", m5_result=altered, research_chain=chain, provenance=provenance)


@pytest.mark.parametrize("field", ["artifact_version", "checksum"])
def test_m6_rejects_same_id_m5_output_with_different_binding_metadata(tmp_path, field):
    m5_result, chain, provenance = _run_full_m5(tmp_path / "m5")
    altered = deepcopy(m5_result)
    altered["claims_ledger"][field] = "9.9.9" if field == "artifact_version" else "1" * 64
    with pytest.raises(ResearchB4Error, match="M6_M5_CANONICAL_BINDING_INVALID:ClaimsLedger"):
        _run_m6(tmp_path / "run", m5_result=altered, research_chain=chain, provenance=provenance)


def test_m6_rejects_missing_material_m5_artifact(tmp_path):
    m5_result, chain, provenance = _run_full_m5(tmp_path / "m5")
    altered = deepcopy(m5_result)
    altered.pop("refined_thesis")
    with pytest.raises(ResearchB4Error, match="M6_M5_MATERIAL_ARTIFACT_MISSING:RefinedThesis"):
        _run_m6(tmp_path / "run", m5_result=altered, research_chain=chain, provenance=provenance)


def test_m6_fails_closed_when_dependency_is_invalidated(tmp_path):
    m5_result, chain, provenance = _run_full_m5(tmp_path / "m5")
    invalidation = InvalidationEngine()
    m4_ref = next(ref for ref in chain["artifact_refs"] if ref["artifact_kind"] == "ResearchM4ExecutionManifest")
    invalidation.invalidate_artifact(
        m4_ref["artifact_id"],
        m4_ref["artifact_version"],
        "fixture invalidation",
        "TEST",
    )
    with pytest.raises(ResearchB4Error, match="M6_DEPENDENCY_INVALIDATED"):
        ResearchB4Orchestrator(
            lambda request: _audit(request),
            ResearchB4Persistence(tmp_path / "m5"),
            _test_provenance_repository_root=Path(provenance["repository_root"]),
        ).run_m6(
            m5_result,
            context={**_m4_context(), **provenance},
            research_chain=chain,
            invalidation_engine=invalidation,
        )


def test_m6_fails_closed_when_material_payload_is_stale(tmp_path):
    m5_result, chain, provenance = _run_full_m5(tmp_path / "m5")
    claims_path = m5_result["claims_ledger"]["path"]
    claims_payload = _read(m5_result["claims_ledger"])
    claims_payload["artifact_validity"] = "STALE"
    Path(claims_path).write_text(json.dumps(claims_payload, ensure_ascii=False), encoding="utf-8")
    stale_checksum = _checksum(claims_payload)
    m5_manifest = _read(m5_result["execution_manifest"])
    for ref in m5_manifest["m5_outputs"]:
        if ref["artifact_kind"] == "ClaimsLedger":
            ref["checksum"] = stale_checksum
    Path(m5_result["execution_manifest"]["path"]).write_text(json.dumps(m5_manifest, ensure_ascii=False), encoding="utf-8")
    m5_result["claims_ledger"]["checksum"] = stale_checksum
    m5_result["execution_manifest"]["checksum"] = _checksum(m5_manifest)
    with pytest.raises(ResearchB4Error, match="M6_STALE_OR_INVALID_ARTIFACT"):
        _run_m6(tmp_path / "run", m5_result=m5_result, research_chain=chain, provenance=provenance)


def test_m6_rejects_non_independent_actor_or_run(tmp_path):
    with pytest.raises(ResearchB4Error, match="M6_AUDITOR_RUNTIME_PROVENANCE_MISMATCH"):
        _run_m6(
            tmp_path,
            context_overrides={"auditor_provenance": {
                "actor_id": "M5_PRODUCER_ACTUAL",
            }},
        )


def test_m6_rejects_caller_supplied_provenance_registry(tmp_path):
    _, _, provenance = _run_full_m5(tmp_path / "m5")
    with pytest.raises(ResearchB4Error, match="M6_EXECUTION_PROVENANCE_REGISTRY_CALLER_OVERRIDE_FORBIDDEN"):
        _run_m6(
            tmp_path / "run",
            provenance=provenance,
            context_overrides={"execution_provenance_registry": deepcopy(VALID_FIXTURES["execution_provenance_registry"])},
        )


def test_m6_rejects_auditor_run_that_did_not_produce_current_audit(tmp_path):
    result, _, state_root = _run_m6(tmp_path)
    audit_ref = result["independent_research_audit"]
    audit = _read(audit_ref)
    registry_path = state_root / "canonical_repo" / "output" / "execution_provenance_registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    auditor_run = next(run for run in registry["runs"] if run.get("run_id") == audit["auditor"]["run_id"])
    auditor_run["output_artifact_ids"] = ["independent_research_audit:OLD-AUDIT"]
    auditor_run["output_checksums"] = ["a" * 64]
    auditor_run["outputs"] = [{
        "artifact_kind": "independent_research_audit",
        "artifact_id": "OLD-AUDIT",
        "artifact_ref": "independent_research_audit:OLD-AUDIT",
        "checksum": "a" * 64,
    }]
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8")
    with pytest.raises(ResearchB4Error, match="M6_AUDITOR_OUTPUT_BINDING_INVALID"):
        ResearchB4Orchestrator._validate_auditor_output(
            registry_path,
            audit=audit,
            audit_ref=audit_ref,
            auditor={
                "actor_id": audit["auditor"]["actor_id"],
                "run_id": audit["auditor"]["run_id"],
                "executor_id": auditor_run["actual_executor"],
                "role": auditor_run["role"],
                "provenance_ref": "output/execution_provenance_registry.json",
            },
            episode_id=audit["episode_id"],
        )


def test_m6_rejects_when_runtime_does_not_register_current_audit_output(tmp_path, monkeypatch):
    m5_result, chain, provenance = _run_full_m5(tmp_path / "m5")
    monkeypatch.setattr(ResearchB4Orchestrator, "_persist_auditor_execution_result", staticmethod(lambda *args, **kwargs: None))
    with pytest.raises(ResearchB4Error, match="M6_AUDITOR_RUN_NOT_REGISTERED"):
        _run_m6(
            tmp_path / "run", m5_result=m5_result, research_chain=chain, provenance=provenance,
        )


def test_m6_fails_closed_when_material_upstream_provenance_is_unknown(tmp_path):
    m5_result, chain, provenance = _run_full_m5(tmp_path / "m5")
    registry_path = _canonical_registry_path(provenance)
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["runs"] = [run for run in registry["runs"] if "ResearchPlan" not in json.dumps(run)]
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8")
    with pytest.raises(ResearchB4Error, match="M6_PRODUCER_PROVENANCE_ResearchPlan_UNKNOWN"):
        _run_m6(tmp_path / "run", m5_result=m5_result, research_chain=chain, provenance=provenance)


def test_m6_rejects_m4_manifest_changed_after_m5_even_with_recalculated_checksum(tmp_path):
    m5_result, chain, provenance = _run_full_m5(tmp_path / "m5")
    m4_ref = next(ref for ref in chain["artifact_refs"] if ref["artifact_kind"] == "ResearchM4ExecutionManifest")
    m4_payload = _read(m4_ref)
    m4_payload["events"].append({"stage": "POST_M5_TAMPER", "boundary": "TEST"})
    Path(m4_ref["path"]).write_text(json.dumps(m4_payload, ensure_ascii=False), encoding="utf-8")
    m4_ref["checksum"] = _checksum(m4_payload)
    with pytest.raises(ResearchB4Error, match="M6_M4_INPUT_BINDING_INVALID"):
        _run_m6(
            tmp_path / "run", m5_result=m5_result, research_chain=chain, provenance=provenance,
        )


def test_m6_upstream_m4_more_research_required_blocks_ready(tmp_path):
    m5_result, chain, provenance = _run_full_m5(
        tmp_path / "m5", m4_mutator=_mutate_m4_phenomenon_stop_to_more,
    )
    result, _, _ = _run_m6(
        tmp_path / "run", m5_result=m5_result, research_chain=chain, provenance=provenance,
    )
    assert result["status"] == "NOT_RESEARCH_READY"
    manifest = _read(result["research_ready_manifest"])
    assert any(
        item.startswith("RESEARCH_STOP_MORE_RESEARCH_REQUIRED:")
        for item in _read(result["research_ready_gate"])["violations"]
    )
    assert manifest["state_bindings"]["research_sufficiency"] == "MORE_RESEARCH_REQUIRED"


def test_m6_rejects_source_report_from_other_episode_or_research(tmp_path):
    m5_result, chain, provenance = _run_full_m5(tmp_path / "m5")
    source_ref = next(ref for ref in chain["artifact_refs"] if ref["artifact_kind"] == "SourceAccessAndEvidenceReport")
    source_payload = _read(source_ref)
    source_payload.update({"episode_id": "EP-OTHER", "research_id": "RP-OTHER"})
    Path(source_ref["path"]).write_text(json.dumps(source_payload, ensure_ascii=False), encoding="utf-8")
    source_ref["checksum"] = _checksum(source_payload)
    with pytest.raises(ResearchB4Error, match="M6_SOURCE_ACCESS_BINDING_INVALID"):
        _run_m6(
            tmp_path / "run", m5_result=m5_result, research_chain=chain, provenance=provenance,
        )


def test_m6_rejects_same_real_executor_even_when_declared_provenance_differs(tmp_path):
    m5_result, chain, provenance = _run_full_m5(tmp_path / "m5")
    altered = deepcopy(provenance)
    altered["auditor_provenance"] = {"executor_id": "M5-EXECUTOR-ACTUAL"}
    with pytest.raises(ResearchB4Error, match="M6_AUDITOR_RUNTIME_PROVENANCE_MISMATCH"):
        _run_m6(
            tmp_path / "run", m5_result=m5_result, research_chain=chain,
            provenance=altered,
        )


def test_m6_rejects_same_real_executor_from_runtime_even_when_labels_differ(tmp_path):
    m5_result, chain, provenance = _run_full_m5(tmp_path / "m5")
    registry_path = _canonical_registry_path(provenance)
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    producer_run = next(run for run in registry["runs"] if run.get("run_id") == "M5-RUN-ACTUAL")
    producer_run["actual_executor"] = "native_provider"
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8")
    provenance["producer_provenance"]["executor_id"] = "native_provider"
    with pytest.raises(ResearchB4Error, match="M6_AUDITOR_EXECUTOR_NOT_INDEPENDENT"):
        _run_m6(
            tmp_path / "run", m5_result=m5_result, research_chain=chain,
            provenance=provenance,
            context_overrides={"auditor_provenance": {
                "executor_id": "native_provider",
            }},
        )


def test_m6_context_repository_root_cannot_redirect_canonical_registry(tmp_path):
    caller_root = tmp_path / "caller-selected-root"
    caller_root.mkdir()
    result, _, _ = _run_m6(
        tmp_path / "run",
        context_overrides={"repository_root": str(caller_root)},
    )
    assert result["status"] == "RESEARCH_READY_WITH_LIMITATIONS"


def test_m6_registry_run_binds_exact_audit_execution_output(tmp_path):
    result, _, state_root = _run_m6(tmp_path)
    audit = _read(result["independent_research_audit"])
    registry_path = state_root / "canonical_repo" / "output" / "execution_provenance_registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    run = next(item for item in registry["runs"] if item.get("run_id") == audit["auditor"]["run_id"])
    assert run["role"] == "INDEPENDENT_RESEARCH_AUDITOR"
    assert run["agent_id"] == audit["auditor"]["actor_id"]
    assert any(
        output.get("artifact_id") == audit["audit_id"]
        and output.get("checksum") == _checksum(audit)
        for output in run["outputs"]
    )


def test_m6_rejects_same_real_executor_under_changed_labels(tmp_path):
    with pytest.raises(ResearchB4Error, match="M6_AUDITOR_RUNTIME_PROVENANCE_MISMATCH"):
        _run_m6(
            tmp_path,
            context_overrides={"auditor_provenance": {
                "actor_id": "DIFFERENT_AUDITOR_LABEL",
                "role": "RESEARCH_AND_CURATION",
            }},
        )


def test_m6_empty_audit_cannot_produce_research_ready(tmp_path):
    empty_audit = {
        "independence_result": "PASS",
        "findings": [],
        "evidence_refs": [],
        "limitations": [],
        "defects": [],
        "correction_routes": [],
        "decision": "PASS",
    }
    with pytest.raises(ResearchB4Error, match="M6_AUDIT_COVERAGE_EMPTY"):
        _run_m6(tmp_path, audit=lambda request: empty_audit)


def test_m6_preserves_approved_with_limits_deep_fidelity_restrictions(tmp_path):
    m5_result, chain, provenance = _run_full_m5(
        tmp_path / "m5", fidelity="APTA_CON_RIESGOS",
    )
    result, _, _ = _run_m6(
        tmp_path / "run", m5_result=m5_result, research_chain=chain, provenance=provenance,
    )
    manifest = _read(result["research_ready_manifest"])
    assert manifest["state_bindings"]["deep_fidelity"] == "APROBADA_CON_LIMITES"
    assert any(item["restriction_id"].endswith(":deep") for item in manifest["downstream_restrictions"])


def test_m6_research_ready_manifest_binds_full_material_chain(tmp_path):
    m5_result, chain, provenance = _run_full_m5(tmp_path / "source")
    result, _, _ = _run_m6(
        tmp_path / "run", m5_result=m5_result, research_chain=chain, provenance=provenance,
    )
    manifest = _read(result["research_ready_manifest"])
    kinds = {item["artifact_kind"] for item in manifest["research_artifacts"]}
    assert {
        "ResearchPlan",
        "ResearchPack",
        "SourceAccessAndEvidenceReport",
        "ResearchB2ExecutionManifest",
        "ResearchM4ExecutionManifest",
        "ThesisArtifact",
        "WorkResearchDossierCollection",
    } <= kinds
    assert all(
        all(field in item for field in ("artifact_id", "artifact_kind", "artifact_version", "checksum"))
        for item in manifest["research_artifacts"]
    )
    for expected in chain["artifact_refs"]:
        assert any(
            all(item[field] == expected[field] for field in (
                "artifact_id", "artifact_kind", "artifact_version", "checksum",
            ))
            for item in manifest["research_artifacts"]
        )
    audit = _read(result["independent_research_audit"])
    producer_by_artifact = {
        item["artifact_id"]: item["producer_run_id"]
        for item in audit["audited_artifacts"]
    }
    assert len(set(producer_by_artifact.values())) > 1
    assert producer_by_artifact[m5_result["execution_manifest"]["artifact_id"]] == "M5-RUN-ACTUAL"
    assert any(run_id.startswith("UPSTREAM-RUN-") for run_id in producer_by_artifact.values())


def test_m6_auditor_receives_research_plan_fidelity_and_source_chain(tmp_path):
    observed = {}

    def audit(request):
        observed["input_kinds"] = {item["artifact_kind"] for item in request.input_artifacts}
        observed["chain"] = request.prepared_contract["input_payload"]["research_chain"]
        return _audit(request)

    _run_m6(tmp_path, audit=audit)
    assert {
        "ResearchPlan",
        "SourceAccessAndEvidenceReport",
        "ResearchM4ExecutionManifest",
    } <= observed["input_kinds"]
    assert any("DEEP_FIDELITY" in key for key in observed["chain"])
    assert any("DEEP_WORK_RESEARCH" in key for key in observed["chain"])


def test_m6_blocked_audit_produces_not_ready_manifest_and_blocked_gate(tmp_path):
    result, _, _ = _run_m6(
        tmp_path,
        audit=lambda request: _audit(request, decision="REQUEST_CHANGES", finding_status="NOT_SATISFIED"),
    )
    assert result["status"] == "NOT_RESEARCH_READY"
    manifest = _read(result["research_ready_manifest"])
    gate = _read(result["research_ready_gate"])
    assert manifest["state_bindings"]["research_sufficiency"] == "BLOCKED_BY_EVIDENCE"
    assert gate["status"] == "BLOCKED"
    assert gate["violations"]


def test_m6_cognitive_output_cannot_set_technical_identity_or_readiness(tmp_path):
    result, _, _ = _run_m6(tmp_path)
    audit = _read(result["independent_research_audit"])
    manifest = _read(result["research_ready_manifest"])
    assert audit["audit_id"] != "COGNITION-MUST-NOT-OWN-THIS"
    assert audit["audit_version"] == "2.0.0"
    assert manifest["manifest_id"] != "COGNITION-MUST-NOT-OWN-THIS"
    assert "research_ready_state" in manifest


def test_m6_preserves_limitations_and_has_no_narrative_or_b5_outputs(tmp_path):
    result, _, _ = _run_m6(
        tmp_path,
        audit=lambda request: _audit(request, finding_status="LIMITED"),
    )
    manifest = _read(result["research_ready_manifest"])
    assert manifest["downstream_restrictions"]
    assert any(
        item["kind"] == "CLAIM_LIMITED" and "C-EXT" in item["statement"]
        for item in manifest["downstream_restrictions"]
    )
    assert any(
        item["statement"].startswith("RefinedThesis limitation:")
        for item in manifest["downstream_restrictions"]
    )
    forbidden = {"hook", "viewer_journey", "narrative_plan", "pacing", "climax", "cta", "title", "thumbnail"}
    assert not forbidden.intersection(manifest)
    assert not any(key.startswith("b5") or key.startswith("narrative") for key in result)


def test_m6_keeps_human_selection_lineage_in_read_only_handoff(tmp_path):
    result, _, _ = _run_m6(tmp_path)
    manifest = _read(result["research_ready_manifest"])
    kinds = {item["artifact_kind"] for item in manifest["research_artifacts"]}
    assert "HumanDecisionRequest" in kinds
    assert "ResearchM5ExecutionManifest" in kinds


def test_m6_gate_and_manifest_contracts_reject_invalid_shapes():
    assert validate_against_schema({"research_ready_state": "RESEARCH_READY"}, "research_ready_manifest")
    assert validate_against_schema({"status": "PASS"}, "gate_result")
