"""Gate determinista para una auditoría semántica B5-I1 producida por IA."""
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


def _checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evaluate(brief: Path, research: Path, evidence: Path, thesis: Path, audit: Path, artifact_id: str) -> GateResult:
    requirements = [
        InputRequirement(brief, "EpisodeBrief"), InputRequirement(research, "ResearchPack"),
        InputRequirement(evidence, "SourceAccessAndEvidenceReport"), InputRequirement(thesis, "ThesisArtifact"),
        InputRequirement(audit, "SemanticSufficiencyAudit"),
    ]
    blocked, failures, details = validate_inputs(requirements)
    if blocked:
        return GateResult("semantic_sufficiency", artifact_id, "1.0.0", GateStatus.BLOCKED, "Auditoría semántica inexistente o incompleta", blocked, evidence=details)
    if failures:
        return GateResult("semantic_sufficiency", artifact_id, "1.0.0", GateStatus.FAIL, "Entradas de auditoría ilegibles", failures, evidence=details)
    try:
        audit_data = json.loads(audit.read_text(encoding="utf-8"))
        brief_data = json.loads(brief.read_text(encoding="utf-8"))
        research_data = json.loads(research.read_text(encoding="utf-8"))
        evidence_data = json.loads(evidence.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return GateResult("semantic_sufficiency", artifact_id, "1.0.0", GateStatus.FAIL, "JSON inválido", [str(exc)], evidence=details)
    violations = validate_against_schema(audit_data, "semantic_sufficiency_audit")
    expected = {"brief_checksum": _checksum(brief), "research_checksum": _checksum(research), "evidence_report_checksum": _checksum(evidence), "thesis_checksum": _checksum(thesis)}
    violations.extend(f"{field} no corresponde al artefacto auditado" for field, value in expected.items() if audit_data.get(field) != value)
    if audit_data.get("episode_id") != brief_data.get("episode_id"):
        violations.append("episode_id de la auditoría no coincide con EpisodeBrief")
    required_criteria = {"CENTRAL_QUESTION_SPECIFICITY", "RESEARCH_RELEVANCE", "DEPTH_FIT", "RIVAL_PERSPECTIVE_SUBSTANCE", "NARRATIVE_UTILITY", "CRITICAL_CLAIMS_QUALITY", "THESIS_SUBSTANCE", "READINESS_FOR_B5_I2"}
    criteria = [finding.get("criterion") for finding in audit_data.get("findings", []) if isinstance(finding, dict)]
    if set(criteria) != required_criteria or len(criteria) != len(set(criteria)):
        violations.append("SemanticSufficiencyAudit debe contener exactamente una evaluación de cada criterio obligatorio")
    research_claims = research_data.get("critical_claims_assessment", {})
    propagation = evidence_data.get("critical_claims_propagation", {})
    research_ids = set(research_claims.get("claim_ids", []))
    propagated_ids = set(propagation.get("claim_ids", []))
    assessed_ids = {item.get("claim_id") for item in evidence_data.get("critical_claim_assessments", []) if isinstance(item, dict)}
    if research_claims.get("status") != propagation.get("status"):
        violations.append("Estado de claims críticos no propagado entre ResearchPack y EvidenceReport")
    if research_claims.get("status") == "IDENTIFIED" and (research_ids != propagated_ids or research_ids != assessed_ids):
        violations.append("Claims críticos identificados deben aparecer exactamente en propagation y assessments")
    if research_claims.get("status") == "NONE_JUSTIFIED" and (propagation.get("justification") != research_claims.get("justification") or propagation.get("editorial_impact") != research_claims.get("editorial_impact")):
        violations.append("NONE_JUSTIFIED requiere justificación e impacto propagados sin reinterpretación")
    findings = audit_data.get("findings", [])
    critical = {"CENTRAL_QUESTION_SPECIFICITY", "RESEARCH_RELEVANCE", "CRITICAL_CLAIMS_QUALITY", "THESIS_SUBSTANCE", "READINESS_FOR_B5_I2"}
    assessments = [finding.get("assessment") for finding in findings]
    if any(finding.get("assessment") == "NOT_SATISFIED" and finding.get("criterion") in critical for finding in findings) and audit_data.get("decision") != "FAIL":
        violations.append("Un criterio crítico no satisfecho exige decision=FAIL")
    if any(value == "NOT_SATISFIED" for value in assessments) and audit_data.get("decision") in ("PASS", "WARN"):
        violations.append("Findings NOT_SATISFIED no permiten PASS ni WARN")
    if any(value == "LIMITED" for value in assessments) and not any(value == "NOT_SATISFIED" for value in assessments) and audit_data.get("decision") == "PASS":
        violations.append("Findings LIMITED exigen como mínimo decision=WARN")
    if all(value == "SATISFIED" for value in assessments) and audit_data.get("decision") not in ("PASS", "WARN"):
        violations.append("Todos los findings satisfechos no son compatibles con decision bloqueante")
    if violations:
        return GateResult("semantic_sufficiency", artifact_id, "1.0.0", GateStatus.FAIL, "Auditoría semántica inválida o sin lineage exacto", violations, evidence=details)
    decision = audit_data["decision"]
    status = GateStatus(decision)
    summary = "Auditoría semántica permite reauditoría" if status in (GateStatus.PASS, GateStatus.WARN) else "Auditoría semántica no permite avanzar"
    return GateResult("semantic_sufficiency", artifact_id, "1.0.0", status, summary, evidence=details)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--brief", required=True); parser.add_argument("--research", required=True)
    parser.add_argument("--evidence-report", required=True); parser.add_argument("--thesis", required=True)
    parser.add_argument("--audit", required=True); parser.add_argument("--ep-id"); parser.add_argument("--output-root")
    args = parser.parse_args()
    return run_gate(lambda: evaluate(Path(args.brief), Path(args.research), Path(args.evidence_report), Path(args.thesis), Path(args.audit), args.ep_id or Path(args.audit).parent.name), output_root=args.output_root)


if __name__ == "__main__":
    import sys
    sys.exit(main())
