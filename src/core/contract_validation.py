"""
Módulo de Validación Determinista de Contratos y Reglas de Negocio Agénticas
Proyecto YouTube — Sistema Agéntico Editorial
"""

import os
import json
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
import jsonschema
from jsonschema import Draft7Validator, draft7_format_checker

# Registrar un validador personalizado para el formato "date-time"
@draft7_format_checker.checks("date-time")
def is_date_time(val):
    if not isinstance(val, str):
        return False
    try:
        # Python 3.11+ maneja Z de forma nativa. Para compatibilidad con versiones previas reemplazamos Z.
        cleaned = val.replace("Z", "+00:00")
        datetime.fromisoformat(cleaned)
        return True
    except ValueError:
        return False

from src.core.status import (
    is_valid_artifact_status,
    is_valid_gate_status,
    is_valid_approver_identity,
    ApprovalType,
    ApprovalDecision,
    FunctionalRole,
    DEFAULT_ROLE_PERMISSIONS,
    APPROVER_REGISTRY,
)

# Directorio de esquemas
SCHEMAS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "schemas"))


class ContractValidationError(Exception):
    """Excepción para errores de validación estructural o de negocio en contratos."""

    def __init__(self, message: str, violations: Optional[List[str]] = None):
        super().__init__(message)
        self.violations = violations or [message]


def load_schema(schema_name: str) -> Dict[str, Any]:
    """Carga un JSON Schema por nombre. Lanza FileNotFoundError si no existe."""
    if not schema_name.endswith(".json"):
        schema_name = f"{schema_name}.json"
    schema_path = os.path.join(SCHEMAS_DIR, schema_name)
    if not os.path.isfile(schema_path):
        raise FileNotFoundError(f"Schema inexistente: {schema_name}")
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_against_schema(data: Dict[str, Any], schema_name: str) -> List[str]:
    """
    Valida un contrato contra su JSON Schema respectivo y devuelve violaciones estructuradas.
    Rechaza schema inexistente lanzando FileNotFoundError.
    """
    schema = load_schema(schema_name)
    validator = Draft7Validator(schema, format_checker=draft7_format_checker)
    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
    violations = []
    for error in errors:
        path = " -> ".join([str(p) for p in error.path]) if error.path else "root"
        violations.append(f"[{path}] {error.message}")
    return violations


def validate_contract_required_fields(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
    """
    Verifica que todos los campos obligatorios esten presentes y no sean None/vacios si son strings.
    """
    violations = []
    for field in required_fields:
        if field not in data or data[field] is None:
            violations.append(f"Campo obligatorio ausente o nulo: '{field}'.")
        elif isinstance(data[field], str) and not data[field].strip():
            violations.append(f"Campo obligatorio vacio: '{field}'.")
    return violations


def validate_approver_and_role(
    approver: Optional[str],
    role: Optional[str],
    approval_type: ApprovalType,
) -> List[str]:
    """
    Valida la identidad del aprobador y que su rol este autorizado para el tipo de aprobacion.
    """
    violations = []
    
    # 1. Identidad verificable
    if not is_valid_approver_identity(approver):
        violations.append(
            f"Identidad del aprobador invalida o ambigua: '{approver}'."
        )
        return violations

    # 2. Rol autorizado
    if not role or not isinstance(role, str):
        violations.append(f"Rol del aprobador ausente o invalido: '{role}'.")
        return violations
    
    role_clean = role.strip().upper()
    if not APPROVER_REGISTRY.is_valid_approver(approver, role_clean):
        violations.append(
            f"El aprobador '{approver}' no esta registrado con el rol '{role_clean}'."
        )
        return violations

    allowed_roles = DEFAULT_ROLE_PERMISSIONS.get(approval_type, set())
    allowed_role_names = {r.value if hasattr(r, "value") else str(r) for r in allowed_roles}
    if role_clean not in allowed_role_names:
        violations.append(
            f"Rol '{role}' no esta autorizado para emitir '{approval_type.value}'. "
            f"Roles autorizados: {sorted(list(allowed_role_names))}."
        )

    return violations


def validate_editorial_script_approval(data: Dict[str, Any]) -> List[str]:
    """
    Valida el contrato EditorialScriptApproval (B1-C23).
    """
    # 1. Validación estructural con JSON Schema
    violations = validate_against_schema(data, "editorial_script_approval")

    # 2. Validación de negocio y aprobador
    if "approved_by" in data and "approved_role" in data:
        violations.extend(
            validate_approver_and_role(
                data.get("approved_by"),
                data.get("approved_role"),
                ApprovalType.EDITORIAL_SCRIPT_APPROVAL,
            )
        )

    checksum = data.get("checksum")
    if not checksum or len(str(checksum).strip()) == 0:
        violations.append("Checksum obligatorio ausente en la aprobacion editorial del guion.")

    return violations


def validate_human_production_approval(data: Dict[str, Any]) -> List[str]:
    """
    Valida el contrato HumanProductionApproval (B1-C24).
    """
    # 1. Validación estructural con JSON Schema
    violations = validate_against_schema(data, "human_production_approval")

    # 2. Validación de negocio y aprobador
    if "approved_by" in data and "approved_role" in data:
        violations.extend(
            validate_approver_and_role(
                data.get("approved_by"),
                data.get("approved_role"),
                ApprovalType.HUMAN_PRODUCTION_APPROVAL,
            )
        )

    decision = data.get("decision")
    if decision == "DECLARAR_YOUTUBE_READY" or data.get("target_status") == "YOUTUBE_READY":
        violations.append(
            "Regla violada: HumanProductionApproval NO puede declarar el estado YOUTUBE_READY. "
            "Solo puede declarar YOUTUBE_PRODUCTION_READY."
        )

    return violations


def validate_human_publication_approval(data: Dict[str, Any]) -> List[str]:
    """
    Valida el contrato HumanPublicationApproval (B1-C24A).
    """
    # 1. Validación estructural con JSON Schema
    violations = validate_against_schema(data, "human_publication_approval")

    # 2. Validación de negocio y aprobador
    if "approved_by" in data and "approved_role" in data:
        violations.extend(
            validate_approver_and_role(
                data.get("approved_by"),
                data.get("approved_role"),
                ApprovalType.HUMAN_PUBLICATION_APPROVAL,
            )
        )

    if not data.get("has_final_audiovisual_assets", False):
        violations.append(
            "HumanPublicationApproval rechazada: No se pueden emitir aprobaciones de publicacion ni declarar YOUTUBE_READY "
            "sin la existencia y verificacion previa de los activos audiovisuales finales."
        )

    return violations


def validate_research_pack(data: Dict[str, Any]) -> List[str]:
    """
    Valida el contrato ResearchPack (B1-C17).
    Debe separar hechos, interpretaciones e hipótesis.
    """
    # 1. Validación estructural con JSON Schema
    violations = validate_against_schema(data, "research_pack")

    # 2. Validación de negocio y trazabilidad cruzada.
    categories = [
        "facts", "interpretations", "hypotheses", "contradictions",
        "alternative_views", "narrative_evidence", "external_reality_evidence", "claims_candidates",
        "narrative_opportunities",
    ]
    source_ids = [item.get("source_id") for item in data.get("source_registry", []) if isinstance(item, dict)]
    if len(source_ids) != len(set(source_ids)):
        violations.append("ResearchPack contiene source_id duplicados.")
    known_sources = set(source_ids)
    for category in categories:
        entries = data.get(category, [])
        if not isinstance(entries, list):
            violations.append(f"El campo '{category}' en ResearchPack debe ser una lista estructurada.")
            continue
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                continue
            for source_ref in entry.get("source_refs", []):
                if source_ref not in known_sources:
                    violations.append(
                        f"ResearchPack.{category}[{index}] referencia una fuente desconocida: '{source_ref}'."
                    )

    required_dimensions = {
        "CENTRAL_QUESTION", "CONFLICT", "INITIAL_HYPOTHESIS",
        "HUMAN_SOCIAL_HISTORICAL_OR_CULTURAL_PHENOMENON", "PRIMARY_NARRATIVE_MATERIAL",
        "CRITICAL_CLAIMS", "ALTERNATIVE_PERSPECTIVES",
    }
    coverage = data.get("coverage", [])
    coverage_ids = {entry.get("dimension_id") for entry in coverage if isinstance(entry, dict)}
    missing = required_dimensions - coverage_ids
    if missing:
        violations.append(f"ResearchPack.coverage no cubre dimensiones críticas: {', '.join(sorted(missing))}.")
    for entry in coverage:
        if not isinstance(entry, dict):
            continue
        if entry.get("status") in ("PENDING", "NOT_VERIFIABLE"):
            if not entry.get("limitation_or_pending") or entry.get("scope_decision") == "NONE":
                violations.append(f"Coverage {entry.get('dimension_id')} pendiente o no verificable requiere limitación y decisión de bloqueo o reducción.")
    return violations


def validate_claims_ledger(data: Dict[str, Any]) -> List[str]:
    """
    Valida las entradas de ClaimsLedger (B1-C21).
    """
    # 1. Validación estructural con JSON Schema
    violations = validate_against_schema(data, "claims_ledger")

    # 2. Validación de negocio
    if "claims" in data and isinstance(data["claims"], list):
        for idx, claim in enumerate(data["claims"]):
            if not isinstance(claim, dict):
                violations.append(f"Entrada claim en indice {idx} debe ser un diccionario.")
                continue
            
            # Verificar que source_refs no este vacio
            if "source_refs" in claim and isinstance(claim["source_refs"], list) and len(claim["source_refs"]) == 0:
                violations.append(f"Claim '{claim.get('claim_id')}' rechazada: No se permiten claims sin fuente ni estado de verificacion.")

    return violations


def validate_source_access_and_evidence_report(data: Dict[str, Any]) -> List[str]:
    """Valida suficiencia estructural y referencias internas sin fijar umbrales editoriales."""
    violations = validate_against_schema(data, "source_access_and_evidence_report")
    if not isinstance(data.get("can_proceed"), bool):
        return violations
    if data["can_proceed"] and not isinstance(data.get("limitaciones"), list):
        violations.append("can_proceed=true requiere una lista válida de limitaciones.")
    if not data["can_proceed"] and not (data.get("limitaciones") or data.get("claims_pendientes")):
        violations.append("can_proceed=false requiere declarar limitaciones o claims pendientes.")

    sources = []
    for field in ("fuentes_primarias", "fuentes_secundarias"):
        sources.extend(item.get("source_id") for item in data.get(field, []) if isinstance(item, dict))
    if len(sources) != len(set(sources)):
        violations.append("SourceAccessAndEvidenceReport contiene source_id duplicados.")
    known_sources = set(sources)
    if known_sources:
        for field in ("escenas_verificadas", "escenas_descritas_indirectamente"):
            for index, item in enumerate(data.get(field, [])):
                if isinstance(item, dict) and item.get("source_id") not in known_sources:
                    violations.append(f"{field}[{index}] referencia una fuente desconocida.")
        for index, claim in enumerate(data.get("claims_sostenibles", [])):
            if not isinstance(claim, dict):
                continue
            for source_ref in claim.get("source_refs", []):
                if source_ref not in known_sources:
                    violations.append(f"claims_sostenibles[{index}] referencia una fuente desconocida: '{source_ref}'.")

    tipo = data.get("tipo_de_acceso")
    material = data.get("material_principal_disponible")
    if material is True and tipo == "UNAVAILABLE":
        violations.append("material_principal_disponible=true es incoherente con tipo_de_acceso=UNAVAILABLE.")
    if material is False and tipo == "DIRECT":
        violations.append("material_principal_disponible=false es incoherente con tipo_de_acceso=DIRECT.")

    for index, item in enumerate(data.get("escenas_verificadas", [])):
        if isinstance(item, dict) and item.get("verification_mode") != "DIRECT":
            violations.append(
                f"escenas_verificadas[{index}] tiene verification_mode='{item.get('verification_mode')}', "
                f"se esperaba DIRECT."
            )

    for index, item in enumerate(data.get("escenas_descritas_indirectamente", [])):
        if isinstance(item, dict) and item.get("verification_mode") != "INDIRECT":
            violations.append(
                f"escenas_descritas_indirectamente[{index}] tiene verification_mode='{item.get('verification_mode')}', "
                f"se esperaba INDIRECT."
            )

    required_scope_fields = ("allowed_analyses", "limited_analyses", "prohibited_analyses", "excluded_claims", "required_disclosures", "propagated_constraints")
    for field in required_scope_fields:
        if field not in data or not isinstance(data.get(field), list):
            violations.append(f"SourceAccessAndEvidenceReport requiere '{field}' como lista explícita.")
    for claim in data.get("critical_claim_assessments", []):
        if not isinstance(claim, dict):
            continue
        if claim.get("support_status") in ("SUPPORTED", "LIMITED") and claim.get("confidence") == "LOW":
            violations.append(f"Claim crítico '{claim.get('claim_id')}' con confianza LOW debe excluirse o bloquearse.")
        if claim.get("support_status") in ("EXCLUDED", "INSUFFICIENT") and claim.get("claim_id") not in data.get("excluded_claims", []):
            violations.append(f"Claim crítico '{claim.get('claim_id')}' no sostenible debe figurar en excluded_claims.")

    if tipo == "INDIRECT":
        prohibited = set(data.get("prohibited_analyses", []))
        required_prohibitions = {"CLOSE_SCENE_ANALYSIS", "UNSUPPORTED_AUTHORIAL_INTENT", "PRIMARY_EVIDENCE_FOR_DEEP_READING"}
        missing = required_prohibitions - prohibited
        if missing:
            violations.append(f"Acceso INDIRECT requiere prohibir: {', '.join(sorted(missing))}.")
        if not data.get("required_disclosures"):
            violations.append("Acceso INDIRECT requiere disclosures obligatorios.")

    return violations


def validate_thesis_artifact(data: Dict[str, Any], research: Dict[str, Any], evidence_report: Dict[str, Any]) -> List[str]:
    violations = validate_against_schema(data, "thesis_artifact")

    stage = data.get("stage")
    if stage != "THESIS_PROVISIONAL":
        violations.append(
            f"stage debe ser THESIS_PROVISIONAL, recibido: '{stage}'."
        )

    research_sources = {
        s["source_id"] for s in research.get("source_registry", [])
        if isinstance(s, dict) and "source_id" in s
    }
    evidence_sources = set()
    for field in ("fuentes_primarias", "fuentes_secundarias"):
        for s in evidence_report.get(field, []):
            if isinstance(s, dict) and "source_id" in s:
                evidence_sources.add(s["source_id"])

    findings = {}
    for category in ("facts", "interpretations", "hypotheses", "contradictions", "alternative_views", "narrative_evidence", "external_reality_evidence", "claims_candidates"):
        for item in research.get(category, []):
            if isinstance(item, dict) and item.get("item_id"):
                findings[item["item_id"]] = set(item.get("source_refs", []))
    for premise in data.get("premises", []):
        if not isinstance(premise, dict):
            continue
        premise_sources = set(premise.get("source_refs", []))
        for finding_id in premise.get("finding_ids", []):
            if finding_id not in findings:
                violations.append(f"Premisa '{premise.get('premise_id')}' referencia hallazgo inexistente: '{finding_id}'.")
            elif not findings[finding_id].intersection(premise_sources):
                violations.append(f"Premisa '{premise.get('premise_id')}' no conserva trazabilidad hallazgo → fuente para '{finding_id}'.")
        for source_ref in premise_sources:
            if source_ref not in research_sources or source_ref not in evidence_sources:
                violations.append(f"Premisa '{premise.get('premise_id')}' referencia fuente no admitida: '{source_ref}'.")
    for relation in data.get("tensioning_evidence", []):
        if isinstance(relation, dict) and relation.get("finding_id") not in findings:
            violations.append(f"La contraevidencia referencia hallazgo inexistente: '{relation.get('finding_id')}'.")
    expected_constraints = set(evidence_report.get("limitaciones", [])) | set(evidence_report.get("excluded_claims", [])) | set(evidence_report.get("required_disclosures", [])) | set(evidence_report.get("prohibited_analyses", [])) | set(evidence_report.get("propagated_constraints", []))
    inherited = set(data.get("inherited_constraints", []))
    missing_constraints = expected_constraints - inherited
    if missing_constraints:
        violations.append(f"ThesisArtifact no hereda restricciones del reporte: {', '.join(sorted(missing_constraints))}.")

    return violations
