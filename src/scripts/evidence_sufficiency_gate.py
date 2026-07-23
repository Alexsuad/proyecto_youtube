"""Gate de suficiencia para SourceAccessAndEvidenceReport de B5-I1."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from src.core.contract_validation import validate_source_access_and_evidence_report
from src.core.gate_result import GateResult
from src.core.gate_runtime import run_gate
from src.core.input_validation import InputRequirement, validate_inputs
from src.core.status import GateStatus


def _substantive(item: Any) -> bool:
    if isinstance(item, dict):
        return any(_substantive(value) for value in item.values())
    if isinstance(item, list):
        return any(_substantive(value) for value in item)
    if isinstance(item, str):
        return bool(item.strip())
    return bool(item)


def _count(items: Any) -> int:
    return sum(1 for item in items if _substantive(item)) if isinstance(items, list) else 0


def evaluate(report_path: Path, artifact_id: str) -> GateResult:
    blocked, failures, evidence = validate_inputs(
        [InputRequirement(report_path, "SourceAccessAndEvidenceReport")]
    )
    if blocked:
        return GateResult(
            "evidence_sufficiency",
            artifact_id,
            "2.0.0",
            GateStatus.BLOCKED,
            "Reporte de evidencia ausente o vacío",
            blocked,
            evidence=evidence,
        )
    if failures:
        return GateResult(
            "evidence_sufficiency",
            artifact_id,
            "2.0.0",
            GateStatus.FAIL,
            "Reporte de evidencia ilegible",
            failures,
            evidence=evidence,
        )
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return GateResult(
            "evidence_sufficiency",
            artifact_id,
            "2.0.0",
            GateStatus.FAIL,
            "Reporte JSON inválido",
            [str(exc)],
            evidence=evidence,
        )

    violations = validate_source_access_and_evidence_report(report)
    evidence.update(
        {
            "report": report_path.name,
            "report_id": report.get("report_id"),
            "research_id": report.get("research_id"),
        }
    )
    if violations:
        return GateResult(
            "evidence_sufficiency",
            artifact_id,
            "2.0.0",
            GateStatus.FAIL,
            "Contrato de evidencia inválido",
            violations,
            evidence=evidence,
        )

    source_count = _count(report.get("fuentes_primarias")) + _count(report.get("fuentes_secundarias"))
    evidence_count = (
        _count(report.get("escenas_verificadas"))
        + _count(report.get("escenas_descritas_indirectamente"))
        + _count(report.get("claims_sostenibles"))
    )
    evidence["substantive_source_count"] = source_count
    evidence["substantive_evidence_count"] = evidence_count

    if not report.get("material_principal_disponible") and source_count == 0:
        return GateResult(
            "evidence_sufficiency",
            artifact_id,
            "2.0.0",
            GateStatus.BLOCKED,
            "No hay material principal ni evidencia alternativa sustantiva",
            ["Evidencia alternativa sustantiva ausente"],
            evidence=evidence,
        )

    if not report.get("can_proceed"):
        return GateResult(
            "evidence_sufficiency",
            artifact_id,
            "2.0.0",
            GateStatus.BLOCKED,
            "La evidencia no permite continuar",
            ["can_proceed=false"],
            evidence=evidence,
        )
    if source_count == 0 or evidence_count == 0:
        return GateResult(
            "evidence_sufficiency",
            artifact_id,
            "2.0.0",
            GateStatus.FAIL,
            "Evidencia formal sin soporte sustantivo",
            ["can_proceed=true requiere fuentes y escenas o claims sostenibles"],
            evidence=evidence,
        )

    warnings = list(report.get("limitaciones", [])) + list(report.get("required_disclosures", []))
    if report.get("claims_pendientes"):
        warnings.append("Existen claims pendientes declarados")
    if report.get("tipo_de_acceso") in {"INDIRECT", "SECONDARY_ONLY", "MIXED"}:
        warnings.append(f"Acceso no totalmente directo: {report.get('tipo_de_acceso')}")
    status = GateStatus.WARN if warnings else GateStatus.PASS
    return GateResult(
        "evidence_sufficiency",
        artifact_id,
        "2.0.0",
        status,
        "Evidencia suficiente" if not warnings else "Se puede continuar con limitaciones explícitas",
        warnings=warnings,
        evidence=evidence,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True)
    parser.add_argument("--ep-id")
    parser.add_argument("--output-root")
    args = parser.parse_args()
    report = Path(args.report)
    return run_gate(
        lambda: evaluate(report, args.ep_id or report.parent.name),
        output_root=args.output_root,
    )


if __name__ == "__main__":
    import sys

    sys.exit(main())
