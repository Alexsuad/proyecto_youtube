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
    except json.JSONDecodeError as exc:
        return GateResult("semantic_sufficiency", artifact_id, "1.0.0", GateStatus.FAIL, "JSON inválido", [str(exc)], evidence=details)
    violations = validate_against_schema(audit_data, "semantic_sufficiency_audit")
    expected = {"brief_checksum": _checksum(brief), "research_checksum": _checksum(research), "evidence_report_checksum": _checksum(evidence), "thesis_checksum": _checksum(thesis)}
    violations.extend(f"{field} no corresponde al artefacto auditado" for field, value in expected.items() if audit_data.get(field) != value)
    if audit_data.get("episode_id") != brief_data.get("episode_id"):
        violations.append("episode_id de la auditoría no coincide con EpisodeBrief")
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
