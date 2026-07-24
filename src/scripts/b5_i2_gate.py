"""Gate determinista B5-I2: integridad, lineage y auditoría semántica propia."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from src.core.contract_validation import validate_against_schema
from src.core.gate_result import GateResult
from src.core.gate_runtime import run_gate
from src.core.input_validation import InputRequirement, validate_inputs
from src.core.status import GateStatus


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


def _audit_status(audit: dict, violations: list[str]) -> GateStatus:
    criteria = {
        "ANALYSIS_SPECIFICITY", "MATERIAL_ANALYSIS_COVERAGE",
        "RIVAL_INTERPRETATION_AND_LIMITS", "INHERITED_RESTRICTION_PROPAGATION",
        "CURATION_COMPLETENESS", "CURATION_CONTRAST_AND_PROGRESSION",
        "THESIS_REFINEMENT_SUBSTANCE", "EVIDENCE_TRACEABILITY",
        "EARLY_PACKAGING_HONESTY",
    }
    findings = audit.get("findings", [])
    seen = [item.get("criterion") for item in findings if isinstance(item, dict)]
    if set(seen) != criteria or len(seen) != len(set(seen)):
        violations.append("B5I2SemanticSufficiencyAudit debe evaluar exactamente una vez cada criterio")
    assessments = [item.get("assessment") for item in findings if isinstance(item, dict)]
    decision = audit.get("decision")
    if any(value == "NOT_SATISFIED" for value in assessments) and decision in ("PASS", "WARN"):
        violations.append("Un criterio B5-I2 NOT_SATISFIED no permite PASS ni WARN")
    if any(value == "LIMITED" for value in assessments) and not any(value == "NOT_SATISFIED" for value in assessments) and decision == "PASS":
        violations.append("Un criterio B5-I2 LIMITED exige como mínimo WARN")
    return GateStatus(decision) if decision in GateStatus._value2member_map_ else GateStatus.FAIL


def evaluate(
    b5_i1: dict[str, Path], analysis: Path | list[Path], curation: Path,
    thesis: Path, packaging: Path, b5_i2_audit: Path, artifact_id: str,
) -> GateResult:
    analysis_paths = _as_paths(analysis)
    paths = list(b5_i1.values()) + analysis_paths + [curation, thesis, packaging, b5_i2_audit]
    blocked, failures, evidence = validate_inputs([InputRequirement(path, path.name) for path in paths])
    if blocked:
        return GateResult("b5_i2_gate", artifact_id, "1.1.0", GateStatus.BLOCKED, "Faltan artefactos B5-I1/B5-I2", blocked, evidence=evidence)
    if failures:
        return GateResult("b5_i2_gate", artifact_id, "1.1.0", GateStatus.FAIL, "Artefactos ilegibles", failures, evidence=evidence)
    try:
        data = {
            "brief": load(b5_i1["brief"]), "research": load(b5_i1["research"]),
            "evidence": load(b5_i1["evidence"]), "audit": load(b5_i1["audit"]),
            "provisional": load(b5_i1["provisional"]), "analyses": [load(path) for path in analysis_paths],
            "curation": load(curation), "thesis": load(thesis), "packaging": load(packaging),
            "b5_i2_audit": load(b5_i2_audit),
        }
    except (OSError, json.JSONDecodeError) as exc:
        return GateResult("b5_i2_gate", artifact_id, "1.1.0", GateStatus.FAIL, "JSON inválido", [str(exc)], evidence=evidence)

    violations: list[str] = []
    for name, schema in {"brief": "episode_brief", "research": "research_pack", "evidence": "source_access_and_evidence_report", "audit": "semantic_sufficiency_audit", "provisional": "thesis_artifact", "curation": "material_curation", "thesis": "refined_thesis", "packaging": "early_packaging_hypothesis", "b5_i2_audit": "b5_i2_semantic_sufficiency_audit"}.items():
        violations.extend(f"{name}: {item}" for item in validate_against_schema(data[name], schema))
    for index, item in enumerate(data["analyses"]):
        violations.extend(f"analysis[{index}]: {value}" for value in validate_against_schema(item, "narrative_human_analysis"))

    audit_checksum_sources = {"brief_checksum": b5_i1["brief"], "research_checksum": b5_i1["research"], "evidence_report_checksum": b5_i1["evidence"], "thesis_checksum": b5_i1["provisional"]}
    for field, path in audit_checksum_sources.items():
        if data["audit"].get(field) != checksum(path):
            violations.append(f"audit.{field} no coincide con el checksum real de {path.name}")
    if data["audit"].get("decision") not in ("PASS", "WARN"):
        violations.append("Auditoría semántica B5-I1 no permite avanzar")

    brief, research, report, audit = data["brief"], data["research"], data["evidence"], data["audit"]
    if any(item.get("episode_id") != brief.get("episode_id") for item in [research, report, data["provisional"], data["curation"], data["thesis"], data["packaging"], data["b5_i2_audit"], *data["analyses"]]):
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

    constraints = _expected_constraints(report)
    source_ids = {item.get("source_id") for field in ("fuentes_primarias", "fuentes_secundarias") for item in report.get(field, []) if isinstance(item, dict)}
    research_ids = {item.get("item_id") for field in ("facts", "interpretations", "hypotheses", "contradictions", "alternative_views", "narrative_evidence", "external_reality_evidence", "claims_candidates") for item in research.get(field, []) if isinstance(item, dict)}
    evidence_ids = {item.get("scene_id") for field in ("escenas_verificadas", "escenas_descritas_indirectamente") for item in report.get(field, []) if isinstance(item, dict)} | {item.get("claim_id") for item in report.get("claims_sostenibles", []) if isinstance(item, dict)}
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
    analysis_finding_ids = {finding.get("finding_id") for item in data["analyses"] for finding in item.get("findings", []) if isinstance(finding, dict)}
    for item in data["analyses"]:
        if item.get("research_id") != research.get("research_id") or item.get("evidence_report_id") != report.get("report_id") or item.get("semantic_audit_id") != audit.get("audit_id"):
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
    if thesis_data.get("statement") == data["provisional"].get("statement") and not thesis_data.get("statement_unchanged_justification"):
        violations.append("Tesis refinada igual a la provisional exige justificación sustantiva")

    packaging_data = data["packaging"]
    if packaging_data.get("refined_thesis_checksum") != checksum(thesis):
        violations.append("Checksum de RefinedThesis incorrecto")
    if packaging_data.get("refined_thesis_id") != thesis_data.get("thesis_id"):
        violations.append("Packaging no referencia la tesis refinada")
    audience = packaging_data.get("audience", {})
    if (audience.get("profile_id"), audience.get("profile_version"), audience.get("profile_checksum")) != (brief.get("profile_id"), brief.get("profile_version"), brief.get("profile_checksum")) or audience.get("brief_checksum") != checksum(b5_i1["brief"]):
        violations.append("Audience de packaging no conserva lineage de EditorialProfile y EpisodeBrief")
    honesty = packaging_data.get("honesty_assessment", {})
    if honesty.get("risk_level") != packaging_data.get("overpromise_risk"):
        violations.append("Riesgo de honestidad no coincide con overpromise_risk")
    if thesis_data.get("thesis_id") not in set(honesty.get("thesis_refs", [])) or not set(honesty.get("evidence_refs", [])).issubset(traceable_ids):
        violations.append("Honesty assessment no demuestra relación con tesis y evidencia")
    if not constraints.issubset(set(honesty.get("inherited_constraint_ids", []))):
        violations.append("Packaging pierde restricciones heredadas de B5-I1")
    risk = honesty.get("risk_level")
    if risk == "LOW" and honesty.get("unsupported_elements"):
        violations.append("Packaging LOW no puede declarar elementos no sustentados")
    if risk == "MEDIUM" and not honesty.get("mitigation_or_pending"):
        violations.append("Packaging MEDIUM exige mitigación explícita")
    if risk in ("HIGH", "UNRESOLVED"):
        violations.append("Packaging temprano sobrepromete o mantiene riesgo no resuelto")

    b5_audit = data["b5_i2_audit"]
    registered_rows = [item for item in b5_audit.get("analysis_checksums", []) if isinstance(item, dict)]
    registered_ids = [item.get("analysis_id") for item in registered_rows]
    if len(registered_ids) != len(set(registered_ids)):
        violations.append("analysis_checksum debe registrarse una sola vez por analysis_id")
    registered_analyses = {item.get("analysis_id"): item.get("checksum") for item in registered_rows}
    expected_analyses = {item.get("analysis_id"): checksum(path) for item, path in zip(data["analyses"], analysis_paths)}
    if registered_analyses != expected_analyses:
        violations.append("B5I2SemanticSufficiencyAudit no coincide con checksums reales de análisis")
    for field, path in {"curation_checksum": curation, "refined_thesis_checksum": thesis, "early_packaging_checksum": packaging}.items():
        if b5_audit.get(field) != checksum(path):
            violations.append(f"b5_i2_audit.{field} no coincide con el archivo real")
    audit_gate_status = _audit_status(b5_audit, violations)
    if audit_gate_status in (GateStatus.FAIL, GateStatus.BLOCKED):
        violations.append("Auditoría semántica B5-I2 no permite avanzar")
    if violations:
        return GateResult("b5_i2_gate", artifact_id, "1.1.0", GateStatus.FAIL, "B5-I2 no puede avanzar", violations, evidence=evidence)
    status = GateStatus.WARN if audit_gate_status == GateStatus.WARN or risk == "MEDIUM" else GateStatus.PASS
    return GateResult("b5_i2_gate", artifact_id, "1.1.0", status, "B5-I2 preparado para reauditoría funcional", evidence=evidence)


def main() -> int:
    parser = argparse.ArgumentParser()
    for option in ("brief", "research", "evidence", "audit", "provisional", "curation", "thesis", "packaging", "b5-i2-audit"):
        parser.add_argument(f"--{option}", required=True)
    parser.add_argument("--analysis", required=True, action="append")
    parser.add_argument("--ep-id"); parser.add_argument("--output-root")
    args = parser.parse_args()
    b5_i1 = {"brief": Path(args.brief), "research": Path(args.research), "evidence": Path(args.evidence), "audit": Path(args.audit), "provisional": Path(args.provisional)}
    return run_gate(lambda: evaluate(b5_i1, [Path(path) for path in args.analysis], Path(args.curation), Path(args.thesis), Path(args.packaging), Path(args.b5_i2_audit), args.ep_id or Path(args.curation).parent.name), output_root=args.output_root)


if __name__ == "__main__":
    import sys
    sys.exit(main())
