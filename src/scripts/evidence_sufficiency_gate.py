"""Gate de suficiencia de evidencia para SourceAccessAndEvidenceReport."""
import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from src.core.contract_validation import validate_source_access_and_evidence_report
from src.core.gate_result import GateResult
from src.core.gate_runtime import run_gate
from src.core.input_validation import InputRequirement, validate_inputs
from src.core.status import GateStatus


def is_substantive_item(item: Any) -> bool:
    """Comprueba si un elemento de evidencia contiene información sustantiva no vacía."""
    if isinstance(item, dict):
        if not item:
            return False
        for val in item.values():
            if isinstance(val, str) and val.strip():
                return True
            if isinstance(val, (list, dict)) and val:
                return True
            if isinstance(val, (int, float)) and val != 0:
                return True
            if isinstance(val, bool) and val is True:
                return True
        return False
    if isinstance(item, str):
        return bool(item.strip())
    if item is not None:
        return bool(item)
    return False


def count_substantive_items(items_list: Any) -> int:
    """Cuenta los elementos sustantivos en una lista de evidencias."""
    if not isinstance(items_list, list):
        return 0
    return sum(1 for item in items_list if is_substantive_item(item))


def evaluate(report_path: Path, artifact_id: str) -> GateResult:
    blocked, failures, evidence = validate_inputs([InputRequirement(report_path, "SourceAccessAndEvidenceReport")])
    if blocked:
        return GateResult("evidence_sufficiency", artifact_id, "1.0.0", GateStatus.BLOCKED, "Reporte de evidencia ausente o vacío", blocked, evidence=evidence)
    if failures:
        return GateResult("evidence_sufficiency", artifact_id, "1.0.0", GateStatus.FAIL, "Reporte de evidencia inválido", failures, evidence=evidence)
    
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return GateResult("evidence_sufficiency", artifact_id, "1.0.0", GateStatus.FAIL, "Reporte JSON inválido", [str(exc)], evidence=evidence)
    
    violations = validate_source_access_and_evidence_report(report)
    evidence["report"] = report_path.name
    if violations:
        return GateResult("evidence_sufficiency", artifact_id, "1.0.0", GateStatus.FAIL, "Contrato de evidencia inválido", violations, evidence=evidence)

    sub_primarias = count_substantive_items(report.get("fuentes_primarias", []))
    sub_secundarias = count_substantive_items(report.get("fuentes_secundarias", []))
    sub_escenas = count_substantive_items(report.get("escenas_verificadas", []))
    sub_claims = count_substantive_items(report.get("claims_sostenibles", []))
    total_substantive = sub_primarias + sub_secundarias + sub_escenas + sub_claims

    # Sin material principal ni evidencia alternativa sustantiva -> BLOCKED
    if not report.get("material_principal_disponible") and (sub_primarias + sub_secundarias == 0):
        return GateResult(
            "evidence_sufficiency",
            artifact_id,
            "1.0.0",
            GateStatus.BLOCKED,
            "No hay material principal ni evidencia alternativa sustantiva",
            ["Evidencia alternativa sustantiva ausente"],
            evidence=evidence,
        )

    # can_proceed=true pero sin evidencia sustantiva o solo objetos vacíos -> FAIL
    if report.get("can_proceed"):
        if total_substantive == 0:
            return GateResult(
                "evidence_sufficiency",
                artifact_id,
                "1.0.0",
                GateStatus.FAIL,
                "Evidencia afirmada sin soporte sustantivo",
                ["can_proceed=true requiere fuentes, escenas verificadas o claims sostenibles sustantivos"],
                evidence=evidence,
            )

    if not report.get("can_proceed"):
        return GateResult(
            "evidence_sufficiency",
            artifact_id,
            "1.0.0",
            GateStatus.BLOCKED,
            "La evidencia no permite continuar",
            ["can_proceed=false"],
            evidence=evidence,
        )

    limitations = report.get("limitaciones", []) + report.get("required_disclosures", [])
    if limitations or report.get("claims_pendientes"):
        return GateResult(
            "evidence_sufficiency",
            artifact_id,
            "1.0.0",
            GateStatus.WARN,
            "Se puede continuar con limitaciones explícitas",
            warnings=limitations + ["Claims pendientes declarados"] if report.get("claims_pendientes") else limitations,
            evidence=evidence,
        )
    return GateResult("evidence_sufficiency", artifact_id, "1.0.0", GateStatus.PASS, "Evidencia suficiente", evidence=evidence)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True)
    parser.add_argument("--ep-id")
    parser.add_argument("--output-root")
    args = parser.parse_args()
    report = Path(args.report)
    return run_gate(lambda: evaluate(report, args.ep_id or report.parent.name), output_root=args.output_root)


if __name__ == "__main__":
    import sys
    sys.exit(main())
