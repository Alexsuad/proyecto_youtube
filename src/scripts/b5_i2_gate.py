"""Gate determinista B5-I2: integridad, lineage y adjudicación semántica independiente."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from src.ai.manifest import canonical_json, manifest_checksum as _shared_manifest_checksum

from src.core.contract_validation import validate_against_schema, validate_research_pack, validate_research_stop_decision
from src.scripts.channel_intelligence import evaluate_topic_belonging_gate, validate_assessment, validate_decision, validate_topic_input
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
AUDITOR_ROLE = "SCRIPT_PRODUCT_AUDITOR"
REAL_PROVIDER_KIND = "REAL"
SYNTHETIC_PROVIDER_KIND = "SYNTHETIC"
READINESS_BY_DECISION = {"REQUEST_CHANGES": "NOT_READY_FOR_EDITORIAL_FUNCTIONAL_REVIEW", "FAIL": "NOT_READY_FOR_EDITORIAL_FUNCTIONAL_REVIEW", "BLOCKED": "BLOCKED", "NOT_EVALUATED": "BLOCKED"}


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


def _research_material_entries(research: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    entries: dict[str, list[dict[str, Any]]] = {}
    for category in (
        "facts", "interpretations", "hypotheses", "contradictions",
        "alternative_views", "narrative_evidence", "external_reality_evidence", "claims_candidates",
    ):
        for item in research.get(category, []):
            if isinstance(item, dict) and item.get("material_id"):
                entries.setdefault(item["material_id"], []).append({"category": category, "artifact": item})
    return entries


def _material_checksum(entry: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(entry)).hexdigest()


def _provider_kind(run: dict[str, Any]) -> str:
    explicit = _normalize_token(run.get("provider_kind", ""))
    if explicit == "real":
        return REAL_PROVIDER_KIND
    if explicit == "synthetic":
        return SYNTHETIC_PROVIDER_KIND
    return REAL_PROVIDER_KIND if run.get("execution_mode") == "REAL" else SYNTHETIC_PROVIDER_KIND


def _semantic_editorial_decision(audit: dict[str, Any], auditor_run: dict[str, Any] | None) -> str:
    if not auditor_run:
        return "BLOCKED"
    if auditor_run.get("status") == "BLOCKED_BY_SEMANTIC_EVALUATOR":
        return "BLOCKED"
    if auditor_run.get("status") != "SUCCEEDED":
        return "BLOCKED"
    if auditor_run.get("execution_mode") != "REAL" or _provider_kind(auditor_run) != REAL_PROVIDER_KIND:
        return "NOT_EVALUATED"
    return str(audit.get("decision") or "BLOCKED")


def _operational_readiness(technical_integrity: str, semantic_decision: str, auditor_run: dict[str, Any] | None) -> str:
    if technical_integrity != "PASS":
        return "BLOCKED"
    if semantic_decision in {"REQUEST_CHANGES", "FAIL"}:
        return "NOT_READY_FOR_EDITORIAL_FUNCTIONAL_REVIEW"
    if semantic_decision in {"BLOCKED", "NOT_EVALUATED"}:
        return "BLOCKED"
    if not auditor_run:
        return "BLOCKED"
    if auditor_run.get("status") != "SUCCEEDED":
        return "BLOCKED"
    if auditor_run.get("execution_mode") != "REAL":
        return "BLOCKED"
    if _provider_kind(auditor_run) != REAL_PROVIDER_KIND:
        return "BLOCKED"
    return "READY_FOR_EDITORIAL_FUNCTIONAL_REVIEW"


def _canonical_manifest_checksum(episode_id: str, artifacts: list[dict[str, Any]]) -> str:
    return _shared_manifest_checksum(episode_id, artifacts)


def _looks_generic(text: Any) -> bool:
    if not isinstance(text, str):
        return True
    normalized = _normalize_token(text)
    generic_markers = {"tema", "tesis", "analisis", "lectura", "reflexion", "cambio", "relacion", "material", "profundo", "importante", "relevante", "general", "universal"}
    if len(normalized.split()) < 5:
        return True
    return any(marker == normalized or f" {marker} " in f" {normalized} " for marker in generic_markers)


def _append_functional_defects(violations: list[str], analyses: list[dict[str, Any]], curation: dict[str, Any], thesis: dict[str, Any], provisional: dict[str, Any]) -> None:
    if _looks_generic(thesis.get("refined_position")) or _looks_generic(thesis.get("statement")):
        violations.append("TRIVIAL_THESIS: la tesis refinada sigue siendo genérica o evidente")
    if thesis.get("statement") == provisional.get("statement"):
        violations.append("REPHRASED_NOT_REFINED_THESIS: la tesis final mantiene la misma proposición de la tesis provisional")
    if not thesis.get("what_was_changed") or not thesis.get("what_was_rejected") or not thesis.get("what_was_limited"):
        violations.append("REPHRASED_NOT_REFINED_THESIS: faltan cambios, rechazos o límites explícitos de la tesis refinada")
    if _looks_generic(thesis.get("strongest_objection")) or _looks_generic(thesis.get("alternative_explanation")):
        violations.append("DECORATIVE_OBJECTION: la objeción o la explicación alternativa no es sustantiva")
    for analysis in analyses:
        if any(_looks_generic(analysis.get(field)) for field in ("specific_scene_or_passage", "observable_decision_or_action", "conflict", "consequence", "main_interpretation")):
            violations.append(f"INTERCHANGEABLE_ANALYSIS: el análisis {analysis.get('analysis_id')} sigue siendo genérico o intercambiable")
        if not analysis.get("supporting_evidence"):
            violations.append(f"UNSUPPORTED_INFERENCE: el análisis {analysis.get('analysis_id')} no declara supporting_evidence")
        if _looks_generic(analysis.get("interpretive_limit")) or _looks_generic(analysis.get("does_not_establish")):
            violations.append(f"MISSING_INTERPRETIVE_LIMIT: el análisis {analysis.get('analysis_id')} no declara límites interpretativos suficientes")
        if _looks_generic(analysis.get("specific_scene_or_passage")) and _looks_generic(analysis.get("observable_decision_or_action")):
            violations.append(f"SUMMARY_INSTEAD_OF_ANALYSIS: el análisis {analysis.get('analysis_id')} parece resumir en lugar de interpretar")
        if _looks_generic(analysis.get("main_interpretation")) and _looks_generic(analysis.get("causal_relation")):
            violations.append(f"FALSE_DEPTH: el análisis {analysis.get('analysis_id')} usa abstracción sin mecanismo verificable")
    selected_functions = [item.get("contribution") for item in curation.get("function_of_each_selected_material", []) if isinstance(item, dict)]
    if len(selected_functions) != len(set(selected_functions)):
        violations.append("REDUNDANT_CURATION: hay funciones editoriales repetidas entre materiales seleccionados")
    if len(curation.get("progression_map", [])) < len(curation.get("selected_material_ids", [])):
        violations.append("NO_ARGUMENTATIVE_PROGRESSION: la progresión argumentativa no cubre todos los materiales seleccionados")
    if not curation.get("contrast_map"):
        violations.append("NO_ARGUMENTATIVE_PROGRESSION: falta contrast_map en la curación final")


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
    if any(value in ("NOT_SATISFIED", "UNRESOLVED") for value in critical_statuses.values()) and decision not in ("FAIL", "BLOCKED"):
        violations.append("Un criterio crítico NOT_SATISFIED o UNRESOLVED exige decision=FAIL o decision=BLOCKED")
    if any(value == "LIMITED" for value in critical_statuses.values()) and decision == "PASS":
        violations.append("Un criterio crítico LIMITED no permite decision=PASS")
    if any(value == "UNRESOLVED" for value in statuses) and decision in ("PASS", "REQUEST_CHANGES"):
        violations.append("Un criterio UNRESOLVED no permite PASS ni REQUEST_CHANGES")
    if any(value == "NOT_SATISFIED" for value in statuses) and decision in ("PASS", "REQUEST_CHANGES"):
        violations.append("Un criterio NOT_SATISFIED no permite PASS ni REQUEST_CHANGES")
    if any(value == "LIMITED" for value in statuses) and not any(value in ("NOT_SATISFIED", "UNRESOLVED") for value in statuses) and decision == "PASS":
        violations.append("Un criterio LIMITED exige como mínimo decision=REQUEST_CHANGES")
    if all(value == "SATISFIED" for value in statuses) and decision == "FAIL":
        violations.append("Todos los criterios satisfechos no son compatibles con decision=FAIL")
    return GateStatus(decision) if decision in GateStatus._value2member_map_ else GateStatus.FAIL


def _outputs_by_ref(run: dict) -> dict[str, dict]:
    outputs = [item for item in run.get("outputs", []) if isinstance(item, dict)]
    refs = [_artifact_ref(item.get("artifact_kind", ""), item.get("artifact_id", "")) for item in outputs]
    return {ref: item for ref, item in zip(refs, outputs)}


def evaluate(
    b5_i1: dict[str, Path], analysis: Path | list[Path], curation: Path,
    thesis: Path, script_promise: Path, b5_i2_audit: Path, execution_registry: Path, artifact_id: str,
    aggregate_decisions: list[dict[str, Any]] | None = None,
    require_research_closure: bool = False,
    topic_belonging_decision: dict[str, Any] | None = None,
    work_lifecycle: dict[str, Any] | None = None,
    topic_belonging_input: dict[str, Any] | None = None,
    topic_belonging_assessment: dict[str, Any] | None = None,
    research_dossier: dict[str, Any] | None = None,
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
    blocking_violations: list[str] = []
    memory_warning = False
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
    if topic_belonging_decision is None and data["brief"].get("topic_belonging_decision_ref"):
        violations.append("brief declara TopicBelongingDecision pero el gate no recibio la decision canonica para resolver su lineage.")
    if topic_belonging_decision is not None:
        if topic_belonging_input is None or topic_belonging_assessment is None:
            violations.append("TopicBelongingDecision requiere input y assessment canonicos para validar lineage independiente.")
        else:
            violations.extend(f"topic_input: {item}" for item in validate_topic_input(topic_belonging_input))
            violations.extend(f"topic_assessment: {item}" for item in validate_assessment(topic_belonging_assessment, topic_belonging_input))
            violations.extend(f"topic_decision: {item}" for item in validate_decision(topic_belonging_decision, topic_belonging_assessment))
            topic_gate = evaluate_topic_belonging_gate(topic_belonging_decision, topic_belonging_assessment, topic_belonging_input, work_lifecycle=work_lifecycle, research_dossier=research_dossier)
            violations.extend(f"topic_belonging: {item}" for item in topic_gate.get("violations", []))
        expected_ref = str(topic_belonging_decision.get("decision_id") or "")
        expected_checksum = str(topic_belonging_decision.get("provenance", {}).get("output_checksum") or "")
        if data["brief"].get("topic_belonging_decision_ref") != expected_ref:
            violations.append("brief no conserva el TopicBelongingDecision que lo habilit?")
        if data["brief"].get("topic_belonging_decision_checksum") != expected_checksum:
            violations.append("brief no conserva el checksum del TopicBelongingDecision")
    for index, item in enumerate(data["analyses"]):
        violations.extend(f"analysis[{index}]: {value}" for value in validate_against_schema(item, "narrative_human_analysis"))
    violations.extend(f"research: {item}" for item in validate_research_pack(data["research"]))

    audit_checksum_sources = {
        "brief_checksum": b5_i1["brief"],
        "research_checksum": b5_i1["research"],
        "evidence_report_checksum": b5_i1["evidence"],
        "thesis_checksum": b5_i1["provisional"],
    }
    for field, path in audit_checksum_sources.items():
        if data["audit"].get(field) != checksum(path):
            violations.append(f"audit.{field} no coincide con el checksum real de {path.name}")
    if data["audit"].get("decision") not in ("PASS", "REQUEST_CHANGES"):
        violations.append("Auditoría semántica B5-I1 no permite avanzar")

    brief, research, report, audit = data["brief"], data["research"], data["evidence"], data["audit"]
    if require_research_closure:
        stage = research.get("research_pack_stage")
        if stage not in {"RESEARCH_REVIEW_PENDING", "RESEARCH_COMPLETE"}:
            blocking_violations.append("B5-I2 closure requires research_pack_stage=RESEARCH_REVIEW_PENDING o RESEARCH_COMPLETE.")
        aggregate_ref = research.get("aggregate_research_stop_decision_ref")
        if not aggregate_ref:
            blocking_violations.append("B5-I2 closure requires aggregate_research_stop_decision_ref.")
        required_refs = research.get("required_component_decision_refs") or []
        if not required_refs:
            blocking_violations.append("B5-I2 closure requires required_component_decision_refs.")
        supplied_decisions = [item for item in (aggregate_decisions or []) if isinstance(item, dict)]
        aggregate = next((item for item in supplied_decisions if item.get("decision_id") == aggregate_ref), None)
        if aggregate is None:
            blocking_violations.append("B5-I2 closure requires the canonical aggregate ResearchStopDecision resolved by aggregate_research_stop_decision_ref.")
        else:
            if aggregate.get("subject_kind") != "AGGREGATE_RESEARCH_PACK":
                blocking_violations.append("aggregate_research_stop_decision_ref must resolve to subject_kind=AGGREGATE_RESEARCH_PACK.")
            if aggregate.get("subject_ref") != research.get("research_id"):
                blocking_violations.append("La RSD agregada resuelta debe referir exactamente al ResearchPack actual.")
            component_by_id = {
                item.get("decision_id"): item
                for item in supplied_decisions
                if item.get("decision_id") != aggregate_ref
            }
            missing_components = [ref for ref in required_refs if ref not in component_by_id]
            if missing_components:
                blocking_violations.append(f"Faltan RSD componentes canónicas requeridas: {', '.join(missing_components)}.")
            components = [component_by_id[ref] for ref in required_refs if ref in component_by_id]
            violations.extend(validate_research_stop_decision(aggregate, components))
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
    research_materials = _research_material_entries(research)

    curation_data = data["curation"]
    candidate_rows = curation_data.get("candidates", [])
    selected_ids = list(curation_data.get("selected_material_ids", []))
    selected_materials = list(curation_data.get("selected_materials", []))
    if set(selected_materials) != set(selected_ids):
        violations.append("selected_materials y selected_material_ids deben representar la misma seleccion")
    selected_final_materials = selected_ids
    if curation_data.get("selection_stage") == "FINAL":
        selected_rows = [item for item in candidate_rows if item.get("material_id") in set(selected_ids)]
        substantive = [item for item in selected_rows if item.get("narrative_evidence_strength") in {"MEDIUM", "HIGH"} and item.get("function") and item.get("thesis_contribution") and item.get("new_perspective") and item.get("narrative_use")]
        final_selection = work_lifecycle.get("final_selection", {}) if isinstance(work_lifecycle, dict) else {}
        final_exception = final_selection.get("exception") if isinstance(final_selection, dict) else None
        exception_valid = isinstance(final_selection, dict) and final_selection.get("range_status") == "EXCEPTION" and isinstance(final_exception, dict) and final_exception.get("functional_owner") == "SCRIPT_PRODUCT" and bool(final_exception.get("owner_approval_ref"))
        if isinstance(work_lifecycle, dict) and isinstance(final_selection, dict):
            if set(final_selection.get("selected_work_ids", [])) != set(selected_final_materials):
                violations.append("WorkLifecycle.final_selection no coincide con MaterialCuration.selected_material_ids")
            if final_selection.get("curation_ref") != curation_data.get("curation_id"):
                violations.append("WorkLifecycle.final_selection.curation_ref no coincide con la curation actual")
        if not 3 <= len(selected_final_materials) <= 5 and not exception_valid:
            violations.append("FINAL curation requires 3 to 5 substantive selected materials or an approved format exception")
        elif len(substantive) != len(selected_rows):
            violations.append("FINAL curation includes material without substantive analysis, evidence, differentiated function, or progression use")
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
    for item in data["analyses"]:
        material_id = item.get("material_id")
        matches = research_materials.get(material_id, [])
        if not matches:
            blocking_violations.append(f"No existe referencia canónica suficiente para verificar material_checksum de {material_id}")
            continue
        if len(matches) != 1:
            blocking_violations.append(f"La referencia canónica de material_id={material_id} es ambigua en ResearchPack")
            continue
        if material_id in excluded:
            violations.append(f"material_id {material_id} está excluido y no puede validarse como análisis autorizado")
        if material_id not in candidate_id_set:
            violations.append(f"material_id {material_id} no está autorizado por MaterialCuration")
        canonical_entry = matches[0]["artifact"]
        if item.get("material_checksum") != _material_checksum(canonical_entry):
            violations.append(f"material_checksum no coincide con el material canónico real para {material_id}")

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
    if b5_audit.get("auditor_run_reference") != auditor_run_id:
        violations.append("B5I2SemanticSufficiencyAudit no alinea auditor_run_reference con auditor_run_id")
    if b5_audit.get("auditor_write_scope") != "AUDIT_ONLY":
        violations.append("B5I2SemanticSufficiencyAudit exige auditor_write_scope=AUDIT_ONLY")

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
    integrity_status = "BLOCKED" if blocking_violations else ("FAIL" if violations else "PASS")
    semantic_editorial_decision = _semantic_editorial_decision(b5_audit, auditor_run)
    operational_readiness = _operational_readiness(integrity_status, semantic_editorial_decision, auditor_run)
    expected_readiness = READINESS_BY_DECISION.get(semantic_editorial_decision, "READY_FOR_EDITORIAL_FUNCTIONAL_REVIEW")
    if operational_readiness == "READY_FOR_EDITORIAL_FUNCTIONAL_REVIEW" and expected_readiness != "READY_FOR_EDITORIAL_FUNCTIONAL_REVIEW":
        violations.append(f"SEMANTIC_EDITORIAL_DECISION={semantic_editorial_decision} no puede autorizar readiness operativo READY_FOR_EDITORIAL_FUNCTIONAL_REVIEW")
    if b5_audit.get("readiness") != operational_readiness:
        violations.append(f"readiness operativo incoherente: se esperaba {operational_readiness} y se recibió {b5_audit.get('readiness')}")
    evidence["semantic_audit"] = {
        "TECHNICAL_INTEGRITY": integrity_status,
        "SEMANTIC_EDITORIAL_DECISION": semantic_editorial_decision,
        "OPERATIONAL_READINESS": operational_readiness,
        "producer_output_schema": "PASS" if not any(item.startswith("analysis[") or item.startswith("curation:") or item.startswith("thesis:") or item.startswith("script_promise:") for item in violations) else "FAIL",
        "producer_output_closed": "PASS" if not any("artefactos del productor" in item.lower() for item in violations) else "FAIL",
        "auditor_output_schema": "PASS" if not any(item.startswith("b5_i2_audit:") for item in violations) else "FAIL",
        "auditor_independence": "PASS" if b5_audit.get("independence_result") == "PASS" else "FAIL",
        "artifact_checksum_match": "PASS" if not any("checksum" in item.lower() for item in violations) else "FAIL",
        "provenance_complete": "PASS" if auditor_run else "FAIL",
        "AUDITOR_EXECUTION_MODE": auditor_run.get("execution_mode") if auditor_run else "",
        "AUDITOR_STATUS": auditor_run.get("status") if auditor_run else "",
        "AUDITOR_PROVIDER_KIND": _provider_kind(auditor_run) if auditor_run else "",
        "auditor_run_id": b5_audit.get("auditor_run_id"),
        "raw_audit_decision": b5_audit.get("decision"),
        "raw_audit_readiness": b5_audit.get("readiness"),
        "input_manifest_checksum": b5_audit.get("input_manifest_checksum"),
    }
    if blocking_violations:
        return GateResult("b5_i2_gate", artifact_id, "1.2.0", GateStatus.BLOCKED, "B5-I2 bloqueada por falta de referencia técnica suficiente", blocking_violations + violations, evidence=evidence)
    if violations:
        return GateResult("b5_i2_gate", artifact_id, "1.2.0", GateStatus.FAIL, "B5-I2 no puede avanzar", violations, evidence=evidence)

    critical_statuses = {
        item.get("criterion"): item.get("status")
        for item in b5_audit.get("findings", [])
        if isinstance(item, dict) and item.get("criterion") in CRITICAL_CRITERIA
    }
    if operational_readiness == "BLOCKED":
        return GateResult("b5_i2_gate", artifact_id, "1.2.0", GateStatus.BLOCKED, "La auditoría no tiene autorización operativa para pasar a SCRIPT_PRODUCT", evidence=evidence)
    if any(value in ("NOT_SATISFIED", "UNRESOLVED") for value in critical_statuses.values()) or semantic_editorial_decision == "FAIL":
        return GateResult("b5_i2_gate", artifact_id, "1.2.0", GateStatus.FAIL, "La adjudicación editorial independiente no autoriza avanzar", evidence=evidence)
    if memory_warning or any(value == "LIMITED" for value in critical_statuses.values()) or editorial_gate_status == GateStatus.REQUEST_CHANGES or risk == "MEDIUM" or semantic_editorial_decision == "REQUEST_CHANGES":
        return GateResult("b5_i2_gate", artifact_id, "1.2.0", GateStatus.REQUEST_CHANGES, "La auditoría editorial exige correcciones antes de avanzar", evidence=evidence)
    return GateResult("b5_i2_gate", artifact_id, "1.2.0", GateStatus.PASS, "B5-I2 preparado para reauditoría funcional", evidence=evidence)


def main() -> int:
    parser = argparse.ArgumentParser()
    for option in ("brief", "research", "evidence", "audit", "provisional", "curation", "thesis", "script-promise", "b5-i2-audit"):
        parser.add_argument(f"--{option}", required=True)
    parser.add_argument("--execution-registry", required=True)
    parser.add_argument("--analysis", required=True, action="append")
    parser.add_argument("--ep-id")
    parser.add_argument("--output-root")
    parser.add_argument("--research-stop-decision", action="append", default=[])
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
            aggregate_decisions=[load(Path(path)) for path in args.research_stop_decision],
            require_research_closure=True,
        ),
        output_root=args.output_root,
    )


if __name__ == "__main__":
    import sys

    sys.exit(main())
