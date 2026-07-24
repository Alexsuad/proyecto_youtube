"""Gate determinista de B5-I2: lineage, trazabilidad y límites de packaging temprano."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from src.core.contract_validation import validate_against_schema
from src.core.gate_result import GateResult
from src.core.gate_runtime import run_gate
from src.core.input_validation import InputRequirement, validate_inputs
from src.core.status import GateStatus

def checksum(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path: Path): return json.loads(path.read_text(encoding="utf-8"))

def evaluate(b5_i1: dict[str, Path], analysis: Path, curation: Path, thesis: Path, packaging: Path, artifact_id: str) -> GateResult:
    paths = list(b5_i1.values()) + [analysis, curation, thesis, packaging]
    blocked, failures, evidence = validate_inputs([InputRequirement(path, path.name) for path in paths])
    if blocked: return GateResult("b5_i2_gate", artifact_id, "1.0.0", GateStatus.BLOCKED, "Faltan artefactos B5-I1/B5-I2", blocked, evidence=evidence)
    if failures: return GateResult("b5_i2_gate", artifact_id, "1.0.0", GateStatus.FAIL, "Artefactos ilegibles", failures, evidence=evidence)
    try:
        data = {name: load(path) for name, path in [("brief", b5_i1["brief"]), ("research", b5_i1["research"]), ("evidence", b5_i1["evidence"]), ("audit", b5_i1["audit"]), ("provisional", b5_i1["provisional"]), ("analysis", analysis), ("curation", curation), ("thesis", thesis), ("packaging", packaging)]}
    except (OSError, json.JSONDecodeError) as exc: return GateResult("b5_i2_gate", artifact_id, "1.0.0", GateStatus.FAIL, "JSON inválido", [str(exc)], evidence=evidence)
    schemas = {"brief":"episode_brief", "research":"research_pack", "evidence":"source_access_and_evidence_report", "audit":"semantic_sufficiency_audit", "provisional":"thesis_artifact", "analysis":"narrative_human_analysis", "curation":"material_curation", "thesis":"refined_thesis", "packaging":"early_packaging_hypothesis"}
    violations = []
    for name, schema in schemas.items(): violations.extend(f"{name}: {v}" for v in validate_against_schema(data[name], schema))
    if data["audit"].get("decision") not in ("PASS", "WARN"): violations.append("Auditoría semántica B5-I1 no permite avanzar")
    if data["research"].get("episode_id") != data["brief"].get("episode_id") or data["evidence"].get("episode_id") != data["brief"].get("episode_id") or data["provisional"].get("episode_id") != data["brief"].get("episode_id"): violations.append("Los artefactos B5-I1 no comparten episode_id")
    if data["analysis"].get("episode_id") != data["brief"].get("episode_id"): violations.append("Analysis episode_id no coincide")
    if data["curation"].get("episode_id") != data["brief"].get("episode_id"): violations.append("Curation episode_id no coincide")
    if data["thesis"].get("episode_id") != data["brief"].get("episode_id"): violations.append("RefinedThesis episode_id no coincide")
    if data["packaging"].get("episode_id") != data["brief"].get("episode_id"): violations.append("Packaging episode_id no coincide")
    if data["thesis"].get("analysis_ids") != data["curation"].get("analysis_ids"): violations.append("RefinedThesis no deriva de la misma selección de análisis")
    if data["analysis"].get("research_id") != data["research"].get("research_id"): violations.append("analysis.research_id no coincide con ResearchPack")
    if data["analysis"].get("evidence_report_id") != data["evidence"].get("report_id"): violations.append("analysis.evidence_report_id no coincide con EvidenceReport")
    if data["analysis"].get("semantic_audit_id") != data["audit"].get("audit_id"): violations.append("analysis.semantic_audit_id no coincide con SemanticSufficiencyAudit")
    if data["thesis"].get("provisional_thesis_id") != data["provisional"].get("thesis_id"): violations.append("provisional_thesis_id no coincide con tesis provisional")
    if data["thesis"].get("curation_id") != data["curation"].get("curation_id"): violations.append("curation_id no coincide con MaterialCuration")
    candidate_ids = {item.get("material_id") for item in data["curation"].get("candidates", [])}
    selected = set(data["curation"].get("selected_material_ids", []))
    if not selected.issubset(candidate_ids): violations.append("Curation selecciona materiales no presentes en candidatos")
    candidates = {item.get("material_id"): item for item in data["curation"].get("candidates", [])}
    excluded = {item.get("material_id") for item in data["curation"].get("exclusions", [])}
    contribution_ids = {item.get("material_id") for item in data["thesis"].get("material_contributions", [])}
    if selected & excluded: violations.append("Material EXCLUDED aparece en selected_material_ids")
    if any(candidates[mid].get("selection_status") != "SELECTED" for mid in selected if mid in candidates): violations.append("Material seleccionado no tiene estado SELECTED")
    if excluded != {mid for mid, item in candidates.items() if item.get("selection_status") == "EXCLUDED"}: violations.append("Todo material EXCLUDED debe aparecer en exclusions")
    if contribution_ids != selected: violations.append("Material contributions deben corresponder exactamente a materiales seleccionados")
    for mid, item in candidates.items():
        for redundant in item.get("redundancy_with_selected", []):
            if redundant not in candidate_ids or redundant == mid: violations.append("Redundancia referencia material inexistente o a sí mismo")
    if any(mid not in candidate_ids for mid in contribution_ids): violations.append("Contribución referencia material inexistente")
    analysis_ids = {item.get("analysis_id") for item in data["analysis"].get("findings", [])}
    if not set(data["curation"].get("analysis_ids", [])).issubset({data["analysis"].get("analysis_id")}): violations.append("Curation referencia analysis_id inexistente")
    research_items = {item.get("item_id") for category in ("facts","interpretations","hypotheses","contradictions","alternative_views","narrative_evidence","external_reality_evidence","claims_candidates") for item in data["research"].get(category, []) if isinstance(item, dict)}
    evidence_ids = {item.get("scene_id") for field in ("escenas_verificadas","escenas_descritas_indirectamente") for item in data["evidence"].get(field, []) if isinstance(item, dict)} | {item.get("claim_id") for item in data["evidence"].get("claims_sostenibles", []) if isinstance(item, dict)}
    for finding in data["analysis"].get("findings", []):
        if not set(finding.get("narrative_evidence_refs", [])).issubset(research_items | evidence_ids): violations.append("Análisis referencia evidencia narrativa inexistente")
        if not set(finding.get("source_refs", [])).issubset({item.get("source_id") for field in ("fuentes_primarias","fuentes_secundarias") for item in data["evidence"].get(field, []) if isinstance(item, dict)}): violations.append("Análisis referencia fuente inexistente")
    if data["packaging"].get("refined_thesis_checksum") != checksum(thesis): violations.append("Checksum de RefinedThesis incorrecto")
    if data["packaging"].get("refined_thesis_id") != data["thesis"].get("thesis_id"): violations.append("Packaging no referencia la tesis refinada")
    if data["packaging"].get("overpromise_risk") in ("HIGH", "UNRESOLVED") or not data["packaging"].get("honesty_check"): violations.append("Packaging temprano sobrepromete o no supera comprobación de honestidad")
    if violations: return GateResult("b5_i2_gate", artifact_id, "1.0.0", GateStatus.FAIL, "B5-I2 no puede avanzar", violations, evidence=evidence)
    return GateResult("b5_i2_gate", artifact_id, "1.0.0", GateStatus.PASS, "B5-I2 preparado para auditoría funcional", evidence=evidence)

def main() -> int:
    p=argparse.ArgumentParser(); p.add_argument("--brief",required=True); p.add_argument("--research",required=True); p.add_argument("--evidence",required=True); p.add_argument("--audit",required=True); p.add_argument("--provisional",required=True); p.add_argument("--analysis",required=True); p.add_argument("--curation",required=True); p.add_argument("--thesis",required=True); p.add_argument("--packaging",required=True); p.add_argument("--ep-id"); p.add_argument("--output-root"); a=p.parse_args()
    b={"brief":Path(a.brief),"research":Path(a.research),"evidence":Path(a.evidence),"audit":Path(a.audit),"provisional":Path(a.provisional)}
    return run_gate(lambda:evaluate(b,Path(a.analysis),Path(a.curation),Path(a.thesis),Path(a.packaging),a.ep_id or Path(a.analysis).parent.name),output_root=a.output_root)
if __name__ == "__main__":
    import sys; sys.exit(main())
