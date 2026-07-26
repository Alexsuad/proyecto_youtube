"""Gate determinista B5-I2: integridad, lineage y adjudicación semántica independiente."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from src.ai.manifest import manifest_checksum as _shared_manifest_checksum

from src.core.contract_validation import validate_against_schema
from src.core.gate_result import GateResult
from src.core.gate_runtime import run_gate
from src.core.input_validation import InputRequirement, validate_inputs
from src.core.status import GateStatus


CRITERIA = {
    "ANALYSIS_SPECIFICITY",
    "EVIDENCE_TRACEABILITY",
    "EPISTEMIC_SEPARATION",
    "EDITORIAL_DEPTH_AND_UTILITY",
    "MATERIAL_COVERAGE",
    "CURATION_FUNCTION",
    "CURATION_CONTRAST_AND_PROGRESSION",
    "REDUNDANCY_AND_CONTEXT_COST",
    "THESIS_REFINEMENT_SUBSTANCE",
    "THESIS_ARGUMENTATIVE_QUALITY",
    "MATERIAL_THESIS_CONTRIBUTION",
    "INHERITED_RESTRICTIONS",
    "SCRIPT_PROMISE_HONESTY",
    "EARLY_PACKAGING_HONESTY",
    "B5_I3_READINESS",
}
CRITICAL_CRITERIA = {
    "ANALYSIS_SPECIFICITY",
    "EVIDENCE_TRACEABILITY",
    "EPISTEMIC_SEPARATION",
    "MATERIAL_COVERAGE",
    "CURATION_FUNCTION",
    "CURATION_CONTRAST_AND_PROGRESSION",
    "THESIS_REFINEMENT_SUBSTANCE",
    "THESIS_ARGUMENTATIVE_QUALITY",
    "MATERIAL_THESIS_CONTRIBUTION",
    "INHERITED_RESTRICTIONS",
    "B5_I3_READINESS",
}
INVALID_PROVENANCE = {"manual", "unknown", "unverified"}
AUDITOR_ROLE = "INDEPENDENT_EDITORIAL_AUDITOR"
READINESS_BY_DECISION = {
    "PASS": "READY_FOR_TEAM_02_REAUDIT",
    "WARN": "READY_FOR_TEAM_02_REAUDIT",
    "FAIL": "NOT_READY_FOR_TEAM_02_REAUDIT",
    "BLOCKED": "BLOCKED_BY_MISSING_INPUT",
}


def checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _as_paths(analysis: Path | list[Path]) -> list[Path]:
    return [analysis] if isinstance(analysis, Path) else analysis


def _expected_constraints(evidence: dict) -> set[str]:
    return set().union(
        evidence.get("limitaciones", []), evidence.get("excluded_claims", []),
        evidence.get("required_disclosures", []), evidence.get("prohibited_analyses", []),
        evidence.get("propagated_constraints", []),
    )


def _constraint_details(evidence: dict) -> dict[str, set[str]]:
    required_disclosures = {value for value in evidence.get("required_disclosures", []) if isinstance(value, str) and value}
    unsupported_claims = {
        value
        for field in ("excluded_claims", "prohibited_analyses")
        for value in evidence.get(field, [])
        if isinstance(value, str) and value
    }
    return {
        "all": _expected_constraints(evidence),
        "required_disclosures": required_disclosures,
        "unsupported_claims": unsupported_claims,
    }


def _artifact_ref(artifact_kind: str, artifact_id: str) -> str:
    return f"{artifact_kind}:{artifact_id}"


def _normalize_token(value: Any) -> str:
    return str(value).strip().lower()


def _collect_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        items: list[str] = []
        for item in value:
            items.extend(_collect_strings(item))
        return items
    if isinstance(value, dict):
        items: list[str] = []
        for item in value.values():
            items.extend(_collect_strings(item))
        return items
    return []


def _field_tokens(path: str) -> list[str | int]:
    tokens: list[str | int] = []
    for name, index in re.findall(r"([A-Za-z0-9_]+)|\[([0-9]+)\]", path):
        tokens.append(name if name else int(index))
    return tokens


def _resolve_field(data: Any, field_path: str) -> Any:
    current = data
    for token in _field_tokens(field_path):
        if isinstance(token, int):
            if not isinstance(current, list) or token >= len(current):
                raise KeyError(field_path)
            current = current[token]
        else:
            if not isinstance(current, dict) or token not in current:
                raise KeyError(field_path)
            current = current[token]
    return current


def _build_actual_artifacts(data: dict[str, Any], b5_i1: dict[str, Path], analysis_paths: list[Path], curation: Path, thesis: Path, script_promise: Path) -> list[dict[str, Any]]:
    artifacts = [
        {
            "artifact_kind": "research",
            "artifact_id": data["research"].get("research_id"),
            "artifact_ref": _artifact_ref("research", data["research"].get("research_id")),
            "checksum": checksum(b5_i1["research"]),
            "data": data["research"],
        },
        {
            "artifact_kind": "evidence_report",
            "artifact_id": data["evidence"].get("report_id"),
            "artifact_ref": _artifact_ref("evidence_report", data["evidence"].get("report_id")),
            "checksum": checksum(b5_i1["evidence"]),
            "data": data["evidence"],
        },
        {
            "artifact_kind": "provisional_thesis",
            "artifact_id": data["provisional"].get("thesis_id"),
            "artifact_ref": _artifact_ref("provisional_thesis", data["provisional"].get("thesis_id")),
            "checksum": checksum(b5_i1["provisional"]),
            "data": data["provisional"],
        },
    ]
    artifacts.extend(
        {
            "artifact_kind": "analysis",
            "artifact_id": item.get("analysis_id"),
            "artifact_ref": _artifact_ref("analysis", item.get("analysis_id")),
            "checksum": checksum(path),
            "data": item,
        }
        for item, path in zip(data["analyses"], analysis_paths)
    )
    artifacts.extend(
        [
            {
                "artifact_kind": "curation",
                "artifact_id": data["curation"].get("curation_id"),
                "artifact_ref": _artifact_ref("curation", data["curation"].get("curation_id")),
                "checksum": checksum(curation),
                "data": data["curation"],
            },
            {
                "artifact_kind": "refined_thesis",
                "artifact_id": data["thesis"].get("thesis_id"),
                "artifact_ref": _artifact_ref("refined_thesis", data["thesis"].get("thesis_id")),
                "checksum": checksum(thesis),
                "data": data["thesis"],
            },
            {
                "artifact_kind": "script_promise",
                "artifact_id": data["script_promise"].get("promise_id"),
                "artifact_ref": _artifact_ref("script_promise", data["script_promise"].get("promise_id")),
                "checksum": checksum(script_promise),
                "data": data["script_promise"],
            },
        ]
    )
    return artifacts


def _canonical_manifest_checksum(episode_id: str, artifacts: list[dict[str, Any]]) -> str:
    return _shared_manifest_checksum(episode_id, artifacts)


def _build_evidence_texts(research: dict, report: dict, constraints: set[str]) -> dict[str, list[str]]:
    evidence_texts: dict[str, list[str]] = {}
    for field in (
        "facts", "interpretations", "hypotheses", "contradictions",
        "alternative_views", "narrative_evidence", "external_reality_evidence",
        "claims_candidates",
    ):
        for item in research.get(field, []):
            if isinstance(item, dict) and item.get("item_id"):
                evidence_texts[item["item_id"]] = _collect_strings(item)
    for field in ("escenas_verificadas", "escenas_descritas_indirectamente"):
        for item in report.get(field, []):
            if isinstance(item, dict) and item.get("scene_id"):
                evidence_texts[item["scene_id"]] = _collect_strings(item)
    for item in report.get("claims_sostenibles", []):
        if isinstance(item, dict) and item.get("claim_id"):
            evidence_texts[item["claim_id"]] = _collect_strings(item)
    for constraint in constraints:
        evidence_texts[constraint] = [constraint]
    return evidence_texts


def _editorial_status(audit: dict, violations: list[str]) -> GateStatus:
    findings = [item for item in audit.get("findings", []) if isinstance(item, dict)]
    seen = [item.get("criterion") for item in findings]
    if set(seen) != CRITERIA or len(seen) != len(set(seen)):
        violations.append("B5I2SemanticSufficiencyAudit debe evaluar exactamente una vez cada criterio")

    statuses = [item.get("status") for item in findings]
    critical_statuses = {item.get("criterion"): item.get("status") for item in findings if item.get("criterion") in CRITICAL_CRITERIA}
    decision = audit.get("decision")
    if any(value in ("NOT_SATISFIED", "UNRESOLVED") for value in critical_statuses.values()) and decision != "FAIL":
        violations.append("Un criterio crítico NOT_SATISFIED o UNRESOLVED exige decision=FAIL")
    if any(value == "LIMITED" for value in critical_statuses.values()) and decision == "PASS":
        violations.append("Un criterio crítico LIMITED no permite decision=PASS")
    if any(value == "UNRESOLVED" for value in statuses) and decision in ("PASS", "WARN"):
        violations.append("Un criterio UNRESOLVED no permite PASS ni WARN")
    if any(value == "NOT_SATISFIED" for value in statuses) and decision in ("PASS", "WARN"):
        violations.append("Un criterio NOT_SATISFIED no permite PASS ni WARN")
    if any(value == "LIMITED" for value in statuses) and not any(value in ("NOT_SATISFIED", "UNRESOLVED") for value in statuses) and decision == "PASS":
        violations.append("Un criterio LIMITED exige como mínimo decision=WARN")
    if all(value == "SATISFIED" for value in statuses) and decision not in ("PASS", "WARN"):
        violations.append("Todos los criterios satisfechos no son compatibles con una decisión bloqueante")
    expected_readiness = READINESS_BY_DECISION.get(decision)
    if expected_readiness and audit.get("readiness") != expected_readiness:
        violations.append(f"decision={decision} exige readiness={expected_readiness}")
    return GateStatus(decision) if decision in GateStatus._value2member_map_ else GateStatus.FAIL


def _outputs_by_ref(run: dict) -> dict[str, dict]:
    outputs = [item for item in run.get("outputs", []) if isinstance(item, dict)]
    refs = [_artifact_ref(item.get("artifact_kind", ""), item.get("artifact_id", "")) for item in outputs]
    return {ref: item for ref, item in zip(refs, outputs)}


def evaluate(
    b5_i1: dict[str, Path], analysis: Path | list[Path], curation: Path,
    thesis: Path, script_promise: Path, b5_i2_audit: Path, execution_registry: Path, artifact_id: str,
) -> GateResult:
    analysis_paths = _as_paths(analysis)
    paths = list(b5_i1.values()) + analysis_paths + [curation, thesis, script_promise, b5_i2_audit, execution_registry]
    blocked, failures, evidence = validate_inputs([InputRequirement(path, path.name) for path in paths])
    if blocked:
        return GateResult("b5_i2_gate", artifact_id, "1.2.0", GateStatus.BLOCKED, "Faltan artefactos B5-I1/B5-I2", blocked, evidence=evidence)
    if failures:
        return GateResult("b5_i2_gate", artifact_id, "1.2.0", GateStatus.FAIL, "Artefactos ilegibles", failures, evidence=evidence)
    try:
        data = {
            "brief": load(b5_i1["brief"]), "research": load(b5_i1["research"]),
            "evidence": load(b5_i1["evidence"]), "audit": load(b5_i1["audit"]),
            "provisional": load(b5_i1["provisional"]), "analyses": [load(path) for path in analysis_paths],
            "curation": load(curation), "thesis": load(thesis), "script_promise": load(script_promise),
            "b5_i2_audit": load(b5_i2_audit), "execution_registry": load(execution_registry),
        }
    except (OSError, json.JSONDecodeError) as exc:
        return GateResult("b5_i2_gate", artifact_id, "1.2.0", GateStatus.FAIL, "JSON inválido", [str(exc)], evidence=evidence)

    violations: list[str] = []
    for name, schema in {
        "brief": "episode_brief",
        "research": "research_pack",
        "evidence": "source_access_and_evidence_report",
        "audit": "semantic_sufficiency_audit",
        "provisional": "thesis_artifact",
        "curation": "material_curation",
        "thesis": "refined_thesis",
        "script_promise": "editorial_script_promise",
        "b5_i2_audit": "b5_i2_semantic_sufficiency_audit",
        "execution_registry": "execution_provenance_registry",
    }.items():
        violations.extend(f"{name}: {item}" for item in validate_against_schema(data[name], schema))
    for index, item in enumerate(data["analyses"]):
        violations.extend(f"analysis[{index}]: {value}" for value in validate_against_schema(item, "narrative_human_analysis"))

    audit_checksum_sources = {
        "brief_checksum": b5_i1["brief"],
        "research_checksum": b5_i1["research"],
        "evidence_report_checksum": b5_i1["evidence"],
        "thesis_checksum": b5_i1["provisional"],
    }
    for field, path in audit_checksum_sources.items():
        if data["audit"].get(field) != checksum(path):
            violations.append(f"audit.{field} no coincide con el checksum real de {path.name}")
    if data["audit"].get("decision") not in ("PASS", "WARN"):
        violations.append("Auditoría semántica B5-I1 no permite avanzar")

    brief, research, report, audit = data["brief"], data["research"], data["evidence"], data["audit"]
    if any(
        item.get("episode_id") != brief.get("episode_id")
        for item in [research, report, data["provisional"], data["curation"], data["thesis"], data["script_promise"], data["b5_i2_audit"], *data["analyses"]]
    ):
        violations.append("Los artefactos B5-I1/B5-I2 no comparten episode_id")
    if data["curation"].get("research_id") != research.get("research_id"):
        violations.append("curation.research_id no coincide con ResearchPack")
    if data["thesis"].get("research_id") != research.get("research_id"):
        violations.append("thesis.research_id no coincide con ResearchPack")
    if data["thesis"].get("evidence_report_id") != report.get("report_id"):
        violations.append("thesis.evidence_report_id no coincide con EvidenceReport")
    if data["thesis"].get("semantic_audit_id") != audit.get("audit_id"):
        violations.append("thesis.semantic_audit_id no coincide con SemanticSufficiencyAudit")
    if data["thesis"].get("provisional_thesis_id") != data["provisional"].get("thesis_id"):
        violations.append("provisional_thesis_id no coincide con tesis provisional")
    if data["thesis"].get("curation_id") != data["curation"].get("curation_id"):
        violations.append("curation_id no coincide con MaterialCuration")

    constraint_details = _constraint_details(report)
    constraints = constraint_details["all"]
    source_ids = {
        item.get("source_id")
        for field in ("fuentes_primarias", "fuentes_secundarias")
        for item in report.get(field, [])
        if isinstance(item, dict)
    }
    research_ids = {
        item.get("item_id")
        for field in (
            "facts", "interpretations", "hypotheses", "contradictions",
            "alternative_views", "narrative_evidence", "external_reality_evidence",
            "claims_candidates",
        )
        for item in research.get(field, [])
        if isinstance(item, dict)
    }
    evidence_ids = {
        item.get("scene_id")
        for field in ("escenas_verificadas", "escenas_descritas_indirectamente")
        for item in report.get(field, [])
        if isinstance(item, dict)
    } | {
        item.get("claim_id")
        for item in report.get("claims_sostenibles", [])
        if isinstance(item, dict)
    }
    analysis_ids = [item.get("analysis_id") for item in data["analyses"]]
    if len(analysis_ids) != len(set(analysis_ids)):
        violations.append("analysis_id debe ser único entre todos los análisis")
    analysis_by_id = {item.get("analysis_id"): item for item in data["analyses"]}
    analyses_by_material: dict[str, list[dict]] = {}
    for item in data["analyses"]:
        analyses_by_material.setdefault(item.get("material_id"), []).append(item)
    if any(len(items) > 1 for items in analyses_by_material.values()):
        violations.append("Debe existir un solo análisis canónico por material_id")
    analysis_materials = set(analyses_by_material)
    analysis_finding_ids = {
        finding.get("finding_id")
        for item in data["analyses"]
        for finding in item.get("findings", [])
        if isinstance(finding, dict)
    }
    for item in data["analyses"]:
        if (
            item.get("research_id") != research.get("research_id")
            or item.get("evidence_report_id") != report.get("report_id")
            or item.get("semantic_audit_id") != audit.get("audit_id")
        ):
            violations.append("NarrativeHumanAnalysis no conserva IDs B5-I1")
        if not constraints.issubset(set(item.get("inherited_constraint_ids", []))):
            violations.append("NarrativeHumanAnalysis pierde restricciones heredadas de B5-I1")
        if item.get("rival_interpretation_status") == "PRESENT" and not item.get("rival_interpretations"):
            violations.append("NarrativeHumanAnalysis declara rival PRESENT sin interpretación rival")
        if item.get("rival_interpretation_status") == "NOT_APPLICABLE" and not item.get("rival_interpretation_justification"):
            violations.append("NarrativeHumanAnalysis exige justificación de rival no aplicable")
        if item.get("limits_status") == "PRESENT" and not item.get("limitations"):
            violations.append("NarrativeHumanAnalysis declara límites PRESENT sin límites")
        if item.get("limits_status") == "NOT_APPLICABLE" and not item.get("limits_justification"):
            violations.append("NarrativeHumanAnalysis exige justificación de límites no aplicables")
        for finding in item.get("findings", []):
            if not set(finding.get("narrative_evidence_refs", [])).issubset(research_ids | evidence_ids):
                violations.append("Análisis referencia evidencia narrativa inexistente")
            if not set(finding.get("source_refs", [])).issubset(source_ids):
                violations.append("Análisis referencia fuente inexistente")

    curation_data = data["curation"]
    candidate_rows = curation_data.get("candidates", [])
    candidate_ids = [item.get("material_id") for item in candidate_rows]
    if len(candidate_ids) != len(set(candidate_ids)):
        violations.append("material_id debe ser único entre candidatos")
    candidates = {item.get("material_id"): item for item in candidate_rows}
    selected = set(curation_data.get("selected_material_ids", []))
    exclusion_ids = [item.get("material_id") for item in curation_data.get("exclusions", [])]
    if len(exclusion_ids) != len(set(exclusion_ids)):
        violations.append("material_id debe ser único entre exclusiones")
    excluded = set(exclusion_ids)
    if curation_data.get("selection_stage") == "FINAL" and any(item.get("selection_status") == "CANDIDATE" for item in candidates.values()):
        violations.append("Curación FINAL no puede conservar candidatos sin resolver")
    if selected - set(candidates):
        violations.append("Curation selecciona materiales no presentes en candidatos")
    if any(candidates[mid].get("selection_status") != "SELECTED" for mid in selected if mid in candidates):
        violations.append("Material seleccionado no tiene estado SELECTED")
    if excluded != {mid for mid, item in candidates.items() if item.get("selection_status") == "EXCLUDED"}:
        violations.append("Todo material EXCLUDED debe aparecer en exclusions")
    candidate_id_set = set(candidate_ids)
    for material_id, item in candidates.items():
        for redundant_id in item.get("redundancy_with_selected", []):
            if redundant_id not in candidate_id_set or redundant_id == material_id:
                violations.append("Redundancia referencia material inexistente o a sí mismo")
    if any(item.get("selection_status") != "EXCLUDED" and mid not in analysis_materials for mid, item in candidates.items()):
        violations.append("Material no analizado solo puede continuar si queda EXCLUDED")
    if not selected.issubset(analysis_materials):
        violations.append("Material seleccionado sin NarrativeHumanAnalysis")
    if not set(curation_data.get("analysis_ids", [])).issubset(analysis_by_id):
        violations.append("Curation referencia analysis_id inexistente")
    for analysis_id in curation_data.get("analysis_ids", []):
        if analysis_by_id.get(analysis_id, {}).get("material_id") not in candidates:
            violations.append("Curation referencia un análisis cuyo material no existe")
    for material_id in selected:
        material_analyses = analyses_by_material.get(material_id, [])
        if len(material_analyses) != 1:
            violations.append("Cada material seleccionado debe tener exactamente un análisis")
        elif material_analyses[0].get("analysis_id") not in curation_data.get("analysis_ids", []):
            violations.append("El análisis del material seleccionado falta en curation.analysis_ids")
    curation_contributions = [item.get("material_id") for item in curation_data.get("unique_contributions", [])]
    if set(curation_contributions) != selected or len(curation_contributions) != len(set(curation_contributions)):
        violations.append("Curación debe registrar una contribución única por material seleccionado")
    functions = [candidates[mid].get("function") for mid in selected if mid in candidates]
    if len(functions) != len(set(functions)) and not curation_data.get("function_overlap_justification"):
        violations.append("Funciones repetidas exigen justificación de solapamiento")
    curation_restrictions = [item for item in curation_data.get("inherited_restrictions", []) if isinstance(item, dict)]
    curation_constraints = {item.get("constraint_id") for item in curation_restrictions}
    if not constraints.issubset(curation_constraints):
        violations.append("MaterialCuration pierde restricciones heredadas de B5-I1")
    for item in curation_restrictions:
        constraint_id = item.get("constraint_id")
        affected_material_ids = item.get("affected_material_ids", [])
        required_disclosures = item.get("required_disclosures", [])
        unsupported_claims = item.get("unsupported_claims", [])
        if constraint_id not in constraints:
            violations.append("MaterialCuration declara una restricción heredada inexistente en B5-I1")
        if len(affected_material_ids) != len(set(affected_material_ids)):
            violations.append("MaterialCuration no puede duplicar affected_material_ids en una restricción heredada")
        if not set(affected_material_ids).issubset(candidate_id_set):
            violations.append("MaterialCuration referencia affected_material_ids inexistentes")
        if constraint_id in constraint_details["required_disclosures"] and constraint_id not in required_disclosures:
            violations.append("MaterialCuration pierde un required_disclosure heredado de B5-I1")
        if constraint_id in constraint_details["unsupported_claims"] and constraint_id not in unsupported_claims:
            violations.append("MaterialCuration pierde un excluded_claim o análisis prohibido heredado de B5-I1")
        if not affected_material_ids and not required_disclosures and not unsupported_claims:
            violations.append("MaterialCuration no puede conservar una restricción heredada solo como constraint_id")
    progression = {item.get("material_id"): item for item in curation_data.get("progression_evidence", []) if isinstance(item, dict)}
    if not selected.issubset(progression):
        violations.append("Curación no demuestra contraste y progresión para cada material seleccionado")
    for item in progression.values():
        if not set(item.get("evidence_refs", [])).issubset(research_ids | evidence_ids | analysis_finding_ids):
            violations.append("Curación referencia evidencia de progresión inexistente")

    thesis_data = data["thesis"]
    if thesis_data.get("analysis_ids") != curation_data.get("analysis_ids"):
        violations.append("RefinedThesis no deriva de la misma selección de análisis")
    thesis_contributions = [item.get("material_id") for item in thesis_data.get("material_contributions", [])]
    if set(thesis_contributions) != selected or len(thesis_contributions) != len(set(thesis_contributions)):
        violations.append("Material contributions deben corresponder exactamente y sin duplicados a materiales seleccionados")
    traceable_ids = research_ids | evidence_ids | analysis_finding_ids
    if not set(thesis_data.get("supporting_evidence_refs", [])).issubset(traceable_ids):
        violations.append("RefinedThesis referencia evidencia favorable inexistente")
    if not set(thesis_data.get("counterevidence_refs", [])).issubset(traceable_ids):
        violations.append("RefinedThesis referencia contraevidencia inexistente")
    if not constraints.issubset(set(thesis_data.get("inherited_constraint_ids", []))):
        violations.append("RefinedThesis pierde restricciones heredadas de B5-I1")
    for dimension in thesis_data.get("refinement_dimensions", []):
        if not set(dimension.get("evidence_refs", [])).issubset(traceable_ids):
            violations.append("RefinedThesis referencia evidencia inexistente en refinement_dimensions")
    if thesis_data.get("statement") == data["provisional"].get("statement") and not thesis_data.get("statement_unchanged_justification"):
        violations.append("Tesis refinada igual a la provisional exige justificación sustantiva")

    script_promise_data = data["script_promise"]
    if script_promise_data.get("refined_thesis_checksum") != checksum(thesis):
        violations.append("Checksum de RefinedThesis incorrecto")
    if script_promise_data.get("refined_thesis_id") != thesis_data.get("thesis_id"):
        violations.append("La promesa editorial no referencia la tesis refinada")
    if not constraints.issubset(set(script_promise_data.get("inherited_constraint_ids", []))):
        violations.append("La promesa editorial pierde restricciones heredadas de B5-I1")
    risk = script_promise_data.get("textual_overpromise_risk", {}).get("level")
    if risk == "MEDIUM" and not script_promise_data.get("textual_overpromise_risk", {}).get("mitigation_or_pending"):
        violations.append("Riesgo textual MEDIUM exige mitigación explícita")
    if risk in ("HIGH", "UNRESOLVED"):
        violations.append("La promesa editorial sobrepromete o mantiene riesgo no resuelto")

    b5_audit = data["b5_i2_audit"]
    registry_runs = [item for item in data["execution_registry"].get("runs", []) if isinstance(item, dict)]
    run_ids = [item.get("run_id") for item in registry_runs]
    if len(run_ids) != len(set(run_ids)):
        violations.append("ExecutionProvenanceRegistry no puede duplicar run_id")
    runs_by_id = {item.get("run_id"): item for item in registry_runs}
    actual_artifacts = _build_actual_artifacts(data, b5_i1, analysis_paths, curation, thesis, script_promise)
    actual_by_ref = {item["artifact_ref"]: item for item in actual_artifacts}
    expected_manifest_checksum = _canonical_manifest_checksum(brief.get("episode_id"), actual_artifacts)
    if b5_audit.get("input_manifest_checksum") != expected_manifest_checksum:
        violations.append("B5I2SemanticSufficiencyAudit no corresponde al manifiesto exacto de artefactos evaluados")

    auditor_run_id = b5_audit.get("auditor_run_id", "")
    for field in ("auditor_role", "auditor_run_id", "auditor_skill_id", "auditor_skill_version", "provider_or_adapter", "model_or_evaluator"):
        if _normalize_token(b5_audit.get(field, "")) in INVALID_PROVENANCE:
            violations.append(f"B5I2SemanticSufficiencyAudit declara procedencia no verificable en {field}")
    if b5_audit.get("auditor_role") != AUDITOR_ROLE:
        violations.append(f"B5I2SemanticSufficiencyAudit exige auditor_role={AUDITOR_ROLE}")

    artifact_rows = [item for item in b5_audit.get("artifact_checksums", []) if isinstance(item, dict)]
    artifact_refs = [
        _artifact_ref(item.get("artifact_kind", ""), item.get("artifact_id", ""))
        for item in artifact_rows
    ]
    if len(artifact_refs) != len(set(artifact_refs)):
        violations.append("artifact_checksums debe registrar una sola vez cada artefacto auditado")
    declared_by_ref = {ref: item for ref, item in zip(artifact_refs, artifact_rows)}
    if set(declared_by_ref) != set(actual_by_ref):
        violations.append("B5I2SemanticSufficiencyAudit no cubre exactamente todos los artefactos relevantes")
    for artifact_ref, actual in actual_by_ref.items():
        declared = declared_by_ref.get(artifact_ref)
        if not declared:
            continue
        if declared.get("checksum") != actual.get("checksum"):
            violations.append(f"B5I2SemanticSufficiencyAudit reutiliza checksums obsoletos para {artifact_ref}")
        if _normalize_token(declared.get("producer_run_id", "")) in INVALID_PROVENANCE:
            violations.append(f"B5I2SemanticSufficiencyAudit no registra producer_run_id verificable para {artifact_ref}")
        producer_run_id = declared.get("producer_run_id")
        producer_run = runs_by_id.get(producer_run_id)
        if not producer_run:
            violations.append(f"producer_run_id inexistente para {artifact_ref}")
        else:
            if producer_run.get("role") == AUDITOR_ROLE:
                violations.append(f"El run {producer_run_id} no puede reutilizar el rol auditor para {artifact_ref}")
            producer_outputs = _outputs_by_ref(producer_run)
            registered_output = producer_outputs.get(artifact_ref)
            if not registered_output:
                violations.append(f"El run {producer_run_id} no produjo realmente {artifact_ref}")
            elif registered_output.get("checksum") != actual.get("checksum"):
                violations.append(f"El run {producer_run_id} registró un checksum distinto para {artifact_ref}")
        if declared.get("artifact_kind") in {"analysis", "curation", "refined_thesis"} and producer_run_id == auditor_run_id:
            violations.append("B5I2SemanticSufficiencyAudit fue producida por la misma ejecución que creó análisis, curación o tesis")

    auditor_run = runs_by_id.get(auditor_run_id)
    if not auditor_run:
        violations.append("auditor_run_id inexistente en ExecutionProvenanceRegistry")
    else:
        for audit_field, run_field in (
            ("auditor_role", "role"),
            ("auditor_skill_id", "skill_id"),
            ("auditor_skill_version", "skill_version"),
            ("provider_or_adapter", "provider_or_adapter"),
            ("model_or_evaluator", "model_or_evaluator"),
        ):
            if b5_audit.get(audit_field) != auditor_run.get(run_field):
                violations.append(f"B5I2SemanticSufficiencyAudit no coincide con ExecutionProvenanceRegistry en {audit_field}")
        if auditor_run.get("role") != AUDITOR_ROLE:
            violations.append(f"El auditor registrado debe usar role={AUDITOR_ROLE}")
        if auditor_run.get("input_manifest_checksum") != expected_manifest_checksum:
            violations.append("El run auditor no evaluó el manifiesto de entrada exacto de B5-I2")
        audit_output_ref = _artifact_ref("semantic_audit", b5_audit.get("audit_id"))
        audit_outputs = _outputs_by_ref(auditor_run)
        audit_output = audit_outputs.get(audit_output_ref)
        if not audit_output:
            violations.append("El run auditor no produjo realmente la auditoría semántica declarada")
        elif audit_output.get("checksum") != checksum(b5_i2_audit):
            violations.append("El run auditor registró un checksum distinto para la auditoría semántica")
        if any(item.get("artifact_kind") in {"analysis", "curation", "refined_thesis"} for item in audit_outputs.values()):
            violations.append("El run auditor también produjo análisis, curación o tesis")

    evidence_texts = _build_evidence_texts(research, report, constraints)
    criterion_coverage = {
        "ANALYSIS_SPECIFICITY": {
            _artifact_ref("analysis", analysis_id) for analysis_id in analysis_by_id
        },
        "CURATION_CONTRAST_AND_PROGRESSION": {_artifact_ref("curation", curation_data.get("curation_id"))},
        "THESIS_REFINEMENT_SUBSTANCE": {_artifact_ref("refined_thesis", thesis_data.get("thesis_id"))},
    }
    for finding in b5_audit.get("findings", []):
        if not isinstance(finding, dict):
            continue
        criterion = finding.get("criterion")
        anchored = [item for item in finding.get("anchored_findings", []) if isinstance(item, dict)]
        if criterion in CRITICAL_CRITERIA and not anchored:
            violations.append(f"{criterion} exige al menos un hallazgo anclado")
        covered_refs: set[str] = set()
        for anchored_finding in anchored:
            artifact_kind = anchored_finding.get("artifact_kind")
            artifact_obj_id = anchored_finding.get("artifact_id")
            artifact_ref = _artifact_ref(artifact_kind, artifact_obj_id)
            covered_refs.add(artifact_ref)
            actual_artifact = actual_by_ref.get(artifact_ref)
            if not actual_artifact:
                violations.append("Auditoría semántica referencia artefactos inexistentes")
                continue
            try:
                field_value = _resolve_field(actual_artifact["data"], anchored_finding.get("artifact_field", ""))
            except KeyError:
                violations.append("Auditoría semántica referencia un campo inexistente del artefacto evaluado")
                continue
            if not isinstance(field_value, str):
                violations.append("Auditoría semántica debe anclarse a un campo textual existente")
                continue
            if anchored_finding.get("evaluated_excerpt") not in field_value:
                violations.append("Auditoría semántica declara un evaluated_excerpt que no existe en el campo auditado")
            evidence_refs = anchored_finding.get("evidence_refs", [])
            evidence_excerpt_rows = [item for item in anchored_finding.get("evidence_excerpts", []) if isinstance(item, dict)]
            if set(evidence_refs) != {item.get("evidence_ref") for item in evidence_excerpt_rows}:
                violations.append("Auditoría semántica no alinea evidence_refs con evidence_excerpts")
            for evidence_excerpt in evidence_excerpt_rows:
                evidence_ref = evidence_excerpt.get("evidence_ref")
                if evidence_ref not in evidence_texts:
                    violations.append("Auditoría semántica referencia evidencia inexistente")
                    continue
                excerpt = evidence_excerpt.get("excerpt", "")
                if not any(excerpt in candidate for candidate in evidence_texts[evidence_ref]):
                    violations.append("Auditoría semántica cita un fragmento que no aparece en la evidencia referenciada")
        if criterion in criterion_coverage and not criterion_coverage[criterion].issubset(covered_refs):
            violations.append(f"{criterion} no cubre todos los artefactos relevantes auditados")

    editorial_gate_status = _editorial_status(b5_audit, violations)
    integrity_status = "FAIL" if violations else "PASS"
    semantic_editorial_decision = editorial_gate_status.value
    if auditor_run and auditor_run.get("execution_mode") == "REAL" and auditor_run.get("status") == "BLOCKED_BY_SEMANTIC_EVALUATOR":
        semantic_editorial_decision = "BLOCKED_BY_SEMANTIC_EVALUATOR"
    evidence["semantic_audit"] = {
        "SEMANTIC_AUDIT_INTEGRITY": integrity_status,
        "SEMANTIC_EDITORIAL_DECISION": semantic_editorial_decision,
        "auditor_run_id": b5_audit.get("auditor_run_id"),
        "input_manifest_checksum": b5_audit.get("input_manifest_checksum"),
    }
    if violations:
        return GateResult("b5_i2_gate", artifact_id, "1.2.0", GateStatus.FAIL, "B5-I2 no puede avanzar", violations, evidence=evidence)
    if semantic_editorial_decision == "BLOCKED_BY_SEMANTIC_EVALUATOR":
        return GateResult("b5_i2_gate", artifact_id, "1.2.0", GateStatus.BLOCKED, "El evaluador semántico operativo no está disponible para una adjudicación editorial real", evidence=evidence)

    critical_statuses = {
        item.get("criterion"): item.get("status")
        for item in b5_audit.get("findings", [])
        if isinstance(item, dict) and item.get("criterion") in CRITICAL_CRITERIA
    }
    if any(value in ("NOT_SATISFIED", "UNRESOLVED") for value in critical_statuses.values()):
        return GateResult("b5_i2_gate", artifact_id, "1.2.0", GateStatus.FAIL, "La adjudicación editorial independiente no autoriza avanzar", evidence=evidence)
    if any(value == "LIMITED" for value in critical_statuses.values()) or editorial_gate_status == GateStatus.WARN or risk == "MEDIUM":
        return GateResult("b5_i2_gate", artifact_id, "1.2.0", GateStatus.WARN, "La auditoría editorial es trazable pero mantiene limitaciones no bloqueantes", evidence=evidence)
    return GateResult("b5_i2_gate", artifact_id, "1.2.0", GateStatus.PASS, "B5-I2 preparado para reauditoría funcional", evidence=evidence)


def main() -> int:
    parser = argparse.ArgumentParser()
    for option in ("brief", "research", "evidence", "audit", "provisional", "curation", "thesis", "script-promise", "b5-i2-audit"):
        parser.add_argument(f"--{option}", required=True)
    parser.add_argument("--execution-registry", required=True)
    parser.add_argument("--analysis", required=True, action="append")
    parser.add_argument("--ep-id")
    parser.add_argument("--output-root")
    args = parser.parse_args()
    b5_i1 = {
        "brief": Path(args.brief),
        "research": Path(args.research),
        "evidence": Path(args.evidence),
        "audit": Path(args.audit),
        "provisional": Path(args.provisional),
    }
    return run_gate(
        lambda: evaluate(
            b5_i1,
            [Path(path) for path in args.analysis],
            Path(args.curation),
            Path(args.thesis),
            Path(args.script_promise),
            Path(args.b5_i2_audit),
            Path(args.execution_registry),
            args.ep_id or Path(args.curation).parent.name,
        ),
        output_root=args.output_root,
    )


if __name__ == "__main__":
    import sys

    sys.exit(main())
