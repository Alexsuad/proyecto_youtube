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

    # 2. Validación de negocio
    for category in ["facts", "interpretations", "hypotheses"]:
        if category in data and not isinstance(data[category], list):
            violations.append(f"El campo '{category}' en ResearchPack debe ser una lista estructurada.")

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
    """Valida el contrato de suficiencia sin introducir umbrales editoriales."""
    violations = validate_against_schema(data, "source_access_and_evidence_report")
    if not isinstance(data.get("can_proceed"), bool):
        return violations
    if data["can_proceed"] and not isinstance(data.get("limitaciones"), list):
        violations.append("can_proceed=true requiere una lista válida de limitaciones.")
    if not data["can_proceed"] and not (data.get("limitaciones") or data.get("claims_pendientes")):
        violations.append("can_proceed=false requiere declarar limitaciones o claims pendientes.")
    return violations
