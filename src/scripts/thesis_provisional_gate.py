"""Gate para ThesisArtifact provisional B5-I1."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.core.contract_validation import (
    validate_against_schema,
    validate_thesis_artifact,
)
from src.core.gate_result import GateResult
from src.core.gate_runtime import run_gate
from src.core.input_validation import InputRequirement, validate_inputs
from src.core.status import GateStatus
from src.scripts.evidence_sufficiency_gate import evaluate as evaluate_evidence


def evaluate(
    thesis_path: Path,
    research_path: Path,
    evidence_report_path: Path,
    artifact_id: str,
    research_id: str | None = None,
    ep_id: str | None = None,
) -> GateResult:
    ev = {}

    blocked, failures, evidence = validate_inputs([
        InputRequirement(thesis_path, "ThesisArtifact"),
        InputRequirement(research_path, "ResearchPack"),
        InputRequirement(evidence_report_path, "SourceAccessAndEvidenceReport"),
    ])
    ev.update(evidence)
    if blocked:
        return GateResult(
            "thesis_provisional_gate", artifact_id, "1.0.0",
            GateStatus.BLOCKED, "Uno o más archivos requeridos ausentes o vacíos",
            blocked, evidence=ev,
        )
    if failures:
        return GateResult(
            "thesis_provisional_gate", artifact_id, "1.0.0",
            GateStatus.FAIL, "Uno o más archivos ilegibles",
            failures, evidence=ev,
        )

    try:
        thesis = json.loads(thesis_path.read_text(encoding="utf-8"))
        research = json.loads(research_path.read_text(encoding="utf-8"))
        evidence_report = json.loads(evidence_report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return GateResult(
            "thesis_provisional_gate", artifact_id, "1.0.0",
            GateStatus.FAIL, "JSON inválido en uno de los archivos",
            [str(exc)], evidence=ev,
        )

    for name, data, schema in [
        ("thesis_artifact", thesis, "thesis_artifact"),
        ("research_pack", research, "research_pack"),
        ("source_access_and_evidence_report", evidence_report, "source_access_and_evidence_report"),
    ]:
        schema_violations = validate_against_schema(data, schema)
        if schema_violations:
            return GateResult(
                "thesis_provisional_gate", artifact_id, "1.0.0",
                GateStatus.FAIL, f"Schema validation failed for {name}",
                schema_violations, evidence=ev,
            )

    evidence_result = evaluate_evidence(evidence_report_path, artifact_id)
    ev["evidence_gate_status"] = evidence_result.status.value
    if evidence_result.status not in (GateStatus.PASS, GateStatus.WARN):
        return GateResult(
            "thesis_provisional_gate", artifact_id, "1.0.0",
            GateStatus.BLOCKED,
            "Gate de evidencia no permite continuar",
            [f"evidence_sufficiency result: {evidence_result.status.value}"],
            warnings=evidence_result.warnings,
            evidence=ev,
        )

    thesis_violations = validate_thesis_artifact(thesis, research, evidence_report)
    if thesis_violations:
        return GateResult(
            "thesis_provisional_gate", artifact_id, "1.0.0",
            GateStatus.FAIL, "ThesisArtifact inválido",
            thesis_violations, evidence=ev,
        )

    thesis_ids = {
        "episode_id": thesis.get("episode_id"),
        "brief_version": thesis.get("brief_version"),
        "research_id": thesis.get("research_id"),
        "evidence_report_id": thesis.get("evidence_report_id"),
    }
    research_ids = {
        "episode_id": research.get("episode_id"),
        "brief_version": research.get("brief_version"),
        "research_id": research.get("research_id"),
    }
    report_ids = {
        "episode_id": evidence_report.get("episode_id"),
        "brief_version": evidence_report.get("brief_version"),
        "research_id": evidence_report.get("research_id"),
        "evidence_report_id": evidence_report.get("report_id"),
    }

    cross_violations = []
    for field in ("episode_id", "brief_version", "research_id"):
        values = {thesis_ids.get(field), research_ids.get(field), report_ids.get(field)}
        if len(values) > 1:
            cross_violations.append(
                f"{field} no coincide entre artefactos: thesis={thesis_ids.get(field)}, "
                f"research={research_ids.get(field)}, report={report_ids.get(field)}"
            )
    if thesis_ids.get("evidence_report_id") != report_ids.get("evidence_report_id"):
        cross_violations.append(
            f"evidence_report_id no coincide: thesis={thesis_ids.get('evidence_report_id')}, "
            f"report={report_ids.get('evidence_report_id')}"
        )

    if ep_id and ep_id != thesis_ids.get("episode_id"):
        cross_violations.append(
            f"--ep-id={ep_id} no coincide con thesis.episode_id={thesis_ids.get('episode_id')}"
        )

    if cross_violations:
        return GateResult(
            "thesis_provisional_gate", artifact_id, "1.0.0",
            GateStatus.FAIL, "IDs o versiones no coinciden entre artefactos",
            cross_violations, evidence=ev,
        )

    warnings = evidence_result.warnings[:]
    summary = "Tesis provisional válida"
    status = GateStatus.PASS
    if warnings:
        summary = "Tesis provisional válida con advertencias"
        status = GateStatus.WARN

    return GateResult(
        "thesis_provisional_gate", artifact_id, "1.0.0",
        status, summary,
        warnings=warnings, evidence=ev,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--thesis", required=True)
    parser.add_argument("--research", required=True)
    parser.add_argument("--evidence-report", required=True)
    parser.add_argument("--ep-id")
    parser.add_argument("--output-root")
    args = parser.parse_args()
    return run_gate(
        lambda: evaluate(
            Path(args.thesis),
            Path(args.research),
            Path(args.evidence_report),
            args.ep_id or Path(args.thesis).parent.name,
            ep_id=args.ep_id,
        ),
        output_root=args.output_root,
    )


if __name__ == "__main__":
    import sys
    sys.exit(main())
