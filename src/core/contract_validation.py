"""
Módulo de Validación Determinista de Contratos y Reglas de Negocio Agénticas
Proyecto YouTube — Sistema Agéntico Editorial
"""

import os
import json
import hashlib
import re
import unicodedata
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
import jsonschema
from jsonschema import Draft7Validator, RefResolver, draft7_format_checker

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
REPOSITORY_ROOT = os.path.abspath(os.path.join(SCHEMAS_DIR, ".."))
RESPONSIBILITY_REGISTRY_PATH = os.path.join(REPOSITORY_ROOT, "config", "responsibility_registry.json")
RESPONSIBILITY_REGISTRY_REF_PREFIX = "config/responsibility_registry.json#responsibilities/"


def _load_responsibility_registry() -> Dict[str, Dict[str, Any]]:
    try:
        with open(RESPONSIBILITY_REGISTRY_PATH, encoding="utf-8") as handle:
            registry = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return {}
    return {
        item.get("role_id"): item
        for item in registry.get("responsibilities", [])
        if isinstance(item, dict) and item.get("role_id")
    }


def _validate_source_provenance(
    records: List[Dict[str, Any]],
    context: str,
    claim_evaluations: Optional[List[Dict[str, Any]]] = None,
) -> List[str]:
    """Valida provenance editorial de fuentes sin mezclarla con execution provenance."""
    violations: List[str] = []
    by_id = {
        record.get("source_id"): record
        for record in records
        if isinstance(record, dict) and isinstance(record.get("source_id"), str)
    }
    provenance_by_id = {
        source_id: record.get("provenance")
        for source_id, record in by_id.items()
        if isinstance(record.get("provenance"), dict)
    }

    for source_id, provenance in provenance_by_id.items():
        kind = provenance.get("source_kind")
        parent_id = provenance.get("derived_from_source_ref")
        original_id = provenance.get("original_source_ref")
        if kind == "SOURCE_ORIGINAL" and (parent_id is not None or original_id is not None):
            violations.append(f"{context} fuente original '{source_id}' no puede declarar lineage derivado.")
        if kind != "SOURCE_ORIGINAL":
            for field, referenced_id in (("original_source_ref", original_id), ("derived_from_source_ref", parent_id)):
                if not referenced_id:
                    violations.append(f"{context} derivado '{source_id}' requiere {field}.")
                elif referenced_id not in by_id:
                    violations.append(f"{context} derivado '{source_id}' referencia {field} inexistente: '{referenced_id}'.")
            if parent_id == source_id or original_id == source_id:
                violations.append(f"{context} derivado '{source_id}' no puede referenciarse a sí mismo.")

        if kind != "SOURCE_ORIGINAL" and parent_id in by_id:
            parent_provenance = provenance_by_id.get(parent_id)
            parent_kind = parent_provenance.get("source_kind") if isinstance(parent_provenance, dict) else None
            allowed_parent_kinds = {
                "TRANSCRIPT": {"SOURCE_ORIGINAL"},
                "TRANSLATION": {"SOURCE_ORIGINAL", "TRANSCRIPT"},
                "SUMMARY": {"SOURCE_ORIGINAL", "TRANSCRIPT", "TRANSLATION", "REVIEW", "INDIRECT_QUOTE"},
                "REVIEW": {"SOURCE_ORIGINAL", "TRANSCRIPT", "TRANSLATION"},
                "INDIRECT_QUOTE": {"SOURCE_ORIGINAL", "TRANSCRIPT", "TRANSLATION", "SUMMARY", "REVIEW"},
            }
            if parent_kind is not None and kind in allowed_parent_kinds and parent_kind not in allowed_parent_kinds[kind]:
                violations.append(
                    f"{context} lineage de '{source_id}' no permite {kind} derivado de {parent_kind}."
                )
            visited = {source_id}
            current = parent_id
            while current in provenance_by_id and current not in visited:
                visited.add(current)
                current_provenance = provenance_by_id[current]
                if current_provenance.get("source_kind") == "SOURCE_ORIGINAL":
                    if original_id and original_id != current:
                        violations.append(
                            f"{context} lineage de '{source_id}' tiene original_source_ref inconsistente: "
                            f"'{original_id}' frente a raíz '{current}'."
                        )
                    break
                current = current_provenance.get("derived_from_source_ref")
            else:
                if current in visited:
                    violations.append(f"{context} lineage de '{source_id}' contiene un ciclo.")
                elif current not in provenance_by_id:
                    violations.append(f"{context} lineage de '{source_id}' no alcanza una FUENTE_ORIGINAL.")

        uses = set(provenance.get("permitted_uses", []))
        reviewed = provenance.get("primary_verification_performed") is True or provenance.get("verification_status") == "PRIMARY_VERIFIED"
        if provenance.get("source_kind") == "TRANSCRIPT" and provenance.get("transcription_type") == "AUTOMATIC" and not reviewed and "EXACT_QUOTE" in uses:
            violations.append(
                f"{context} fuente '{source_id}' bloqueada: transcripción automática no revisada no puede sostener EXACT_QUOTE."
            )
        if provenance.get("material_transcription_error") is True and not reviewed:
            violations.append(
                f"{context} fuente '{source_id}' bloqueada: error material de transcripción requiere verificación primaria."
            )
        if provenance.get("source_kind") == "TRANSLATION" and "EXACT_QUOTE" in uses and not reviewed:
            violations.append(
                f"{context} fuente '{source_id}' bloqueada: traducción no verificada no sustituye el original para formulación exacta."
            )
        if provenance.get("source_kind") in {"SUMMARY", "REVIEW", "INDIRECT_QUOTE"} and "PROVE_WORK_CONTENT" in uses:
            violations.append(
                f"{context} fuente '{source_id}' bloqueada: {provenance.get('source_kind')} no prueba por sí sola el contenido de la obra."
            )
        if (
            "YOUTUBE_POLICY" in uses
            and (
                provenance.get("authority_domain") != "YOUTUBE_ADAPTATION"
                or provenance.get("official_primary") is not True
                or provenance.get("claim_authority") != "PRIMARY"
            )
        ):
            violations.append(
                f"{context} fuente '{source_id}' bloqueada: una fuente no primaria/oficial no puede presentarse como política oficial de YouTube."
            )

    for evaluation in claim_evaluations or []:
        if not isinstance(evaluation, dict):
            continue
        source_id = evaluation.get("source_id")
        provenance = provenance_by_id.get(source_id)
        if not isinstance(provenance, dict):
            continue
        intended_use = evaluation.get("intended_use")
        reviewed = provenance.get("primary_verification_performed") is True or provenance.get("verification_status") == "PRIMARY_VERIFIED"
        if intended_use == "EXACT_QUOTE" and (
            (provenance.get("source_kind") == "TRANSCRIPT" and provenance.get("transcription_type") == "AUTOMATIC" and not reviewed)
            or (provenance.get("source_kind") == "TRANSLATION" and not reviewed)
        ):
            violations.append(
                f"{context} evaluación del claim '{evaluation.get('claim_id')}' bloqueada: EXACT_QUOTE requiere verificación primaria del original."
            )
        if intended_use == "PROVE_WORK_CONTENT" and provenance.get("source_kind") in {"SUMMARY", "REVIEW", "INDIRECT_QUOTE"}:
            violations.append(
                f"{context} evaluación del claim '{evaluation.get('claim_id')}' bloqueada: la fuente derivada no prueba contenido de obra."
            )
        if intended_use == "YOUTUBE_POLICY" and (
            provenance.get("authority_domain") != "YOUTUBE_ADAPTATION"
            or provenance.get("official_primary") is not True
            or provenance.get("claim_authority") != "PRIMARY"
        ):
            violations.append(
                f"{context} evaluación del claim '{evaluation.get('claim_id')}' bloqueada: requiere fuente oficial primaria de YouTube."
            )
    return violations


def _validate_multilingual_research(
    decision: Any,
    context: str,
    known_source_ids: set[str],
    known_claim_ids: set[str],
) -> List[str]:
    """Valida la decisión SP-IR0-MULTILINGUAL_RESEARCH_THRESHOLD fail-closed."""
    if decision is None:
        return []
    if not isinstance(decision, dict):
        return [f"{context}.multilingual_research debe ser un objeto."]
    violations: List[str] = []
    status = decision.get("activation_status")
    triggers = decision.get("triggers", [])
    non_triggers = decision.get("non_trigger_examples", [])
    if status == "ACTIVATED":
        if not triggers:
            violations.append(f"{context}.multilingual_research ACTIVATED requiere triggers concretos.")
        if not decision.get("required_language"):
            violations.append(f"{context}.multilingual_research ACTIVATED requiere idioma requerido.")
        if not decision.get("affected_source_ids") or not decision.get("affected_claim_ids"):
            violations.append(f"{context}.multilingual_research ACTIVATED requiere fuentes y claims afectados.")
        if not decision.get("material_risk"):
            violations.append(f"{context}.multilingual_research ACTIVATED requiere riesgo material.")
        if decision.get("consultation_result") == "NOT_APPLICABLE" or decision.get("return_route") == "NOT_APPLICABLE":
            violations.append(f"{context}.multilingual_research ACTIVATED requiere resultado y ruta de retorno.")
    elif status == "NOT_ACTIVATED":
        if triggers:
            violations.append(f"{context}.multilingual_research NOT_ACTIVATED no puede declarar triggers de activación.")
        if not non_triggers:
            violations.append(f"{context}.multilingual_research NOT_ACTIVATED requiere un ejemplo explícito de NON_TRIGGER.")
        if (
            decision.get("required_language") is not None
            or decision.get("affected_source_ids")
            or decision.get("affected_claim_ids")
            or decision.get("material_risk")
        ):
            violations.append(f"{context}.multilingual_research NOT_ACTIVATED no puede conservar impactos de una activación inexistente.")
        if decision.get("consultation_result") != "NOT_APPLICABLE" or decision.get("return_route") != "NOT_APPLICABLE":
            violations.append(f"{context}.multilingual_research NOT_ACTIVATED requiere resultado y retorno NOT_APPLICABLE.")
    elif status == "REEVALUATION_REQUIRED":
        if not decision.get("invalidators"):
            violations.append(f"{context}.multilingual_research REEVALUATION_REQUIRED requiere invalidadores concretos.")
        if decision.get("return_route") == "NOT_APPLICABLE":
            violations.append(f"{context}.multilingual_research invalidada requiere ruta de retorno.")
    expected_route = {
        "ORIGINAL_CONSULTED_RISK_RESOLVED": "ORIGINAL_CONSULTED_RISK_RESOLVED",
        "LIMITED_BUT_USABLE": "LIMITED_BUT_USABLE",
        "MORE_RESEARCH_REQUIRED": "MORE_RESEARCH_REQUIRED",
        "BLOCKED_BY_EVIDENCE": "BLOCKED_BY_EVIDENCE",
        "CHANNEL_INTELLIGENCE_REVIEW_REQUIRED": "CHANNEL_INTELLIGENCE_REVIEW_REQUIRED",
        "YOUTUBE_ADAPTATION_REVIEW_REQUIRED": "YOUTUBE_ADAPTATION_REVIEW_REQUIRED",
    }.get(decision.get("consultation_result"))
    if expected_route and decision.get("return_route") != expected_route:
        violations.append(
            f"{context}.multilingual_research consultation_result y return_route deben coincidir: "
            f"se esperaba '{expected_route}'."
        )
    for field, known_ids in (("affected_source_ids", known_source_ids), ("affected_claim_ids", known_claim_ids)):
        for value in decision.get(field, []) if isinstance(decision.get(field), list) else []:
            if value not in known_ids:
                violations.append(f"{context}.multilingual_research.{field} referencia identificador desconocido: '{value}'.")
    return violations


class ContractValidationError(Exception):
    """Excepción para errores de validación estructural o de negocio en contratos."""

    def __init__(self, message: str, violations: Optional[List[str]] = None):
        super().__init__(message)
        self.violations = violations or [message]


def _reject_duplicate_json_keys(pairs: List[Tuple[str, Any]]) -> Dict[str, Any]:
    """Build a JSON object while failing closed on duplicate member names."""
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def loads_strict_json(text: str) -> Any:
    """Parse JSON without silently discarding duplicate object members."""
    return json.loads(text, object_pairs_hook=_reject_duplicate_json_keys)


def load_schema(schema_name: str) -> Dict[str, Any]:
    """Carga un JSON Schema por nombre. Lanza FileNotFoundError si no existe."""
    if not schema_name.endswith(".json"):
        schema_name = f"{schema_name}.json"
    schema_path = os.path.join(SCHEMAS_DIR, schema_name)
    if not os.path.isfile(schema_path):
        raise FileNotFoundError(f"Schema inexistente: {schema_name}")
    with open(schema_path, "r", encoding="utf-8") as f:
        return loads_strict_json(f.read())


def validate_against_schema(data: Dict[str, Any], schema_name: str) -> List[str]:
    """
    Valida un contrato contra su JSON Schema respectivo y devuelve violaciones estructuradas.
    Rechaza schema inexistente lanzando FileNotFoundError.
    """
    schema = load_schema(schema_name)
    # SourceAccessAndEvidenceReport reuses the editorial provenance definitions
    # owned by ResearchPack; the store resolves that existing schema locally.
    store = {schema.get("$id"): schema}
    if schema_name.removesuffix(".json") == "source_access_and_evidence_report":
        canonical_provenance_schema = load_schema("research_pack")
        store[canonical_provenance_schema["$id"]] = canonical_provenance_schema
    resolver = RefResolver.from_schema(schema, store=store)
    validator = Draft7Validator(schema, resolver=resolver, format_checker=draft7_format_checker)
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


_CONTRADICTION_DISPOSITION_ROUTES = {
    "RESOLVED": "AUTHORIZE_INTENDED_USE_ONLY",
    "CONTROVERSY": "RESTRICT_FORMULATION_AND_DISCLOSE",
    "LIMITED": "RESTRICT_FORMULATION_AND_DISCLOSE",
    "RIVAL": "RESTRICT_FORMULATION_AND_DISCLOSE",
    "INVESTIGATION_REQUIRED": "RETURN_TO_RESEARCH",
    "BLOCKED": "REMOVE_REPLACE_OR_REFORMULATE",
}
_CONTRADICTION_OPEN_TREATMENTS = {"OPEN", "INVESTIGATE", "BLOCKED"}


def validate_contradiction_disposition(
    contradiction: Dict[str, Any],
    known_source_ids: Optional[set[str]] = None,
    known_evidence_ids: Optional[set[str]] = None,
    known_claim_ids: Optional[set[str]] = None,
    known_subject_ids: Optional[Dict[str, set[str]]] = None,
) -> List[str]:
    """Valida IR4-008/IR4-009 sin crear una autoridad paralela de evidencia."""
    violations: List[str] = []
    required = (
        "subject_kind", "subject_ref", "affected_use", "conflicting_source_refs", "discrepancy_kind", "materiality", "disposition",
        "compared_positions", "decision_evidence_refs", "contrary_evidence_refs", "disposition_justification",
        "return_route", "return_route_code", "invalidator_codes",
    )
    missing = [field for field in required if field not in contradiction or contradiction.get(field) in (None, "", [])]
    if missing:
        violations.append(f"Contradicción requiere disposición trazable; faltan: {', '.join(missing)}.")
        return violations

    disposition = contradiction.get("disposition")
    subject_kind = contradiction.get("subject_kind")
    resolvable_subject_ids = (known_subject_ids or {}).get(subject_kind)
    if resolvable_subject_ids is not None and contradiction.get("subject_ref") not in resolvable_subject_ids:
        violations.append(
            f"Contradicción referencia subject_ref inexistente para {subject_kind}: '{contradiction.get('subject_ref')}'."
        )
    if not any(contradiction.get(field) for field in ("subject_state", "subject_version", "subject_formulation")):
        violations.append("La contradicción requiere subject_state, subject_version o subject_formulation.")
    affected_claims_value = contradiction.get("affected_claim_ids")
    if affected_claims_value is not None and not isinstance(affected_claims_value, list):
        violations.append("affected_claim_ids debe ser una lista cuando se declara.")
        affected_claims_value = []
    route = contradiction.get("return_route_code")
    expected_route = _CONTRADICTION_DISPOSITION_ROUTES.get(disposition)
    if expected_route is None:
        violations.append(f"Disposición de contradicción no canónica: {disposition}.")
    elif route != expected_route:
        violations.append(f"Disposición {disposition} requiere return_route_code={expected_route}.")

    source_ids = set(known_source_ids or set())
    evidence_ids = set(known_evidence_ids or set()) | source_ids
    claim_ids = set(known_claim_ids or set())
    conflicting = set(contradiction.get("conflicting_source_refs", []))
    declared_sources = set(contradiction.get("source_refs", []))
    if len(conflicting) < 2:
        violations.append("Una contradicción requiere al menos dos fuentes materiales en conflicto.")
    if not conflicting.issubset(declared_sources):
        violations.append("conflicting_source_refs debe estar declarado también en source_refs.")
    unknown_sources = conflicting - source_ids
    if unknown_sources:
        violations.append(f"Contradicción referencia fuentes desconocidas: {', '.join(sorted(unknown_sources))}.")
    affected_claims = set(affected_claims_value or [])
    unknown_claims = affected_claims - claim_ids
    if unknown_claims:
        violations.append(f"Contradicción referencia claims no declarados: {', '.join(sorted(unknown_claims))}.")
    if subject_kind == "MATERIAL_CLAIM":
        if not affected_claims:
            violations.append("Una contradicción con sujeto MATERIAL_CLAIM requiere affected_claim_ids.")
        elif contradiction.get("subject_ref") not in affected_claims:
            violations.append("affected_claim_ids debe incluir el subject_ref del claim material.")
    elif contradiction.get("subject_ref") in claim_ids and contradiction.get("subject_ref") not in affected_claims:
        violations.append("El claim existente identificado como sujeto debe quedar enlazado en affected_claim_ids.")

    positions = contradiction.get("compared_positions")
    if not isinstance(positions, list) or len(positions) < 2:
        violations.append("IR4-009 requiere comparación explícita de al menos dos posiciones materiales.")
        positions = []
    position_ids = [item.get("position_id") for item in positions if isinstance(item, dict)]
    if len(position_ids) != len(set(position_ids)):
        violations.append("Las posiciones comparadas deben tener position_id únicos.")
    position_sources: set[str] = set()
    treatments: set[str] = set()
    for position in positions:
        if not isinstance(position, dict):
            violations.append("Cada posición comparada debe ser estructurada.")
            continue
        position_sources.update(position.get("source_refs", []))
        treatments.add(position.get("treatment"))
        if not set(position.get("source_refs", [])).issubset(source_ids):
            violations.append(f"Posición comparada referencia fuentes desconocidas: {position.get('position_id')}.")
    if not conflicting.issubset(position_sources):
        violations.append("La comparación debe tratar explícitamente todas las fuentes en conflicto.")

    decision_refs = set(contradiction.get("decision_evidence_refs", []))
    contrary_refs = set(contradiction.get("contrary_evidence_refs", []))
    if not decision_refs.issubset(evidence_ids):
        violations.append("decision_evidence_refs contiene evidencia no declarada.")
    if not contrary_refs.issubset(evidence_ids):
        violations.append("contrary_evidence_refs contiene evidencia no declarada.")
    if not (decision_refs & conflicting):
        violations.append("La decisión debe citar al menos una fuente en conflicto.")
    if not (contrary_refs & conflicting):
        violations.append("La evidencia contraria debe citar explícitamente una fuente en conflicto.")

    materiality = contradiction.get("materiality")
    if materiality in {"MATERIAL", "CRITICAL"} and not contrary_refs:
        violations.append("Una contradicción material requiere evidencia contraria explícita.")
    if disposition in {"CONTROVERSY", "LIMITED", "RIVAL"} and not contradiction.get("remaining_limitations"):
        violations.append(f"{disposition} requiere remaining_limitations explícitas.")
    if disposition in {"INVESTIGATION_REQUIRED", "BLOCKED"} and not contradiction.get("pending_matters") and disposition == "INVESTIGATION_REQUIRED":
        violations.append("INVESTIGATION_REQUIRED requiere pending_matters concretos.")
    if disposition != "RESOLVED" and not contradiction.get("revalidation_requirements"):
        violations.append(f"{disposition} requiere revalidation_requirements explícitos.")
    if disposition == "RESOLVED" and treatments & _CONTRADICTION_OPEN_TREATMENTS:
        violations.append("Una contradicción RESOLVED no puede conservar posiciones OPEN, INVESTIGATE o BLOCKED.")
    if disposition == "CONTROVERSY" and not (treatments & {"OPEN", "RETAINED"}):
        violations.append("CONTROVERSY debe conservar explícitamente una posición rival u abierta.")
    if disposition == "RIVAL" and "OPEN" not in treatments:
        violations.append("RIVAL debe conservar explícitamente una posición rival abierta.")
    if disposition in {"CONTROVERSY", "RIVAL"}:
        active_sources = {
            source_ref
            for position in positions
            if isinstance(position, dict)
            if position.get("treatment") in {"OPEN", "RETAINED", "LIMITED", "INVESTIGATE", "BLOCKED"}
            for source_ref in position.get("source_refs", [])
        }
        if not (contrary_refs & active_sources):
            violations.append("La evidencia contraria no puede proceder únicamente de posiciones descartadas.")
    if disposition == "LIMITED" and not (treatments & {"LIMITED", "RETAINED"}):
        violations.append("LIMITED debe conservar la posición tratada y su restricción explícita.")
    if disposition == "INVESTIGATION_REQUIRED" and not (treatments & {"INVESTIGATE", "OPEN"}):
        violations.append("INVESTIGATION_REQUIRED debe conservar una posición pendiente de investigación.")
    if disposition == "BLOCKED" and not (treatments & {"BLOCKED", "OPEN"}):
        violations.append("BLOCKED debe conservar la posición que impide el uso.")
    return violations


def _validate_specialist_research(
    entries: Any,
    source_records: Any,
    known_sources: set[str],
    known_claim_ids: set[str],
) -> List[str]:
    """Valida IR6-001..IR6-005 dentro del ResearchPack canónico.

    La especialidad es una dimensión de investigación, no una identidad de
    agente. Los hallazgos permanecen como contribución limitada y no pueden
    promoverse aquí a hechos, autorización de claims, suficiencia o tesis.
    """
    violations: List[str] = []
    if not isinstance(entries, list):
        if entries is not None:
            violations.append("ResearchPack.specialist_research debe ser una lista.")
        return violations
    sources_by_id = {
        item.get("source_id"): item
        for item in source_records
        if isinstance(item, dict) and isinstance(item.get("source_id"), str)
    }
    seen_ids: dict[str, set[str]] = {
        "specialist_research_id": set(),
        "activation_id": set(),
        "contribution_id": set(),
        "finding_id": set(),
        "position_id": set(),
        "limit_id": set(),
    }

    def check_unique_id(kind: str, value: Any, context: str) -> None:
        if not isinstance(value, str) or not value:
            return
        if value in seen_ids[kind]:
            violations.append(f"{context} {kind} duplicado en ResearchPack: '{value}'.")
        seen_ids[kind].add(value)

    for index, entry in enumerate(entries):
        prefix = f"ResearchPack.specialist_research[{index}]"
        if not isinstance(entry, dict):
            continue
        check_unique_id("specialist_research_id", entry.get("specialist_research_id"), prefix)
        activation = entry.get("activation")
        if isinstance(activation, dict):
            check_unique_id("activation_id", activation.get("activation_id"), f"{prefix}.activation")
            activation_claims = set(activation.get("affected_claim_ids", []))
            unknown_activation_claims = activation_claims - known_claim_ids
            if unknown_activation_claims:
                violations.append(
                    f"{prefix}.activation referencia claims no declarados: {', '.join(sorted(unknown_activation_claims))}."
                )
        else:
            activation_claims = set()
        contribution = entry.get("contribution")
        if not isinstance(contribution, dict):
            continue
        check_unique_id("contribution_id", contribution.get("contribution_id"), f"{prefix}.contribution")
        specialty_changed = isinstance(activation, dict) and contribution.get("specialty") != activation.get("specialty")
        if specialty_changed:
            if contribution.get("activation_relation") != "MATERIAL_MISSION_CHANGE":
                violations.append(f"{prefix}.contribution no puede cambiar especialidad dentro de la misión original.")
            if "SPECIALTY" not in set(contribution.get("activation_change_dimensions", [])):
                violations.append(f"{prefix}.contribution cambio de especialidad requiere dimensión SPECIALTY explícita.")
            if contribution.get("activation_reassessment_status") != "REQUIRED":
                violations.append(f"{prefix}.contribution cambio de especialidad requiere ACTIVATION_REASSESSMENT_REQUIRED=YES.")
            if not contribution.get("activation_reassessment_reason"):
                violations.append(f"{prefix}.contribution cambio de especialidad requiere motivo de reevaluación.")
        contribution_sources = set(contribution.get("source_refs", []))
        unknown_sources = contribution_sources - known_sources
        if unknown_sources:
            violations.append(f"{prefix}.contribution referencia fuentes desconocidas: {', '.join(sorted(unknown_sources))}.")

        contribution_claims = set(contribution.get("affected_claim_ids", []))
        unknown_claims = contribution_claims - known_claim_ids
        if unknown_claims:
            violations.append(f"{prefix}.contribution referencia claims no declarados: {', '.join(sorted(unknown_claims))}.")

        def check_evidence(refs: Any, context: str) -> set[str]:
            values = set(refs or []) if isinstance(refs, list) else set()
            unknown = values - known_sources
            if unknown:
                violations.append(f"{prefix}.contribution.{context} contiene evidencia no declarada: {', '.join(sorted(unknown))}.")
            undeclared = values - contribution_sources
            if undeclared:
                violations.append(f"{prefix}.contribution.{context} usa fuentes fuera de contribution.source_refs: {', '.join(sorted(undeclared))}.")
            return values

        for finding in contribution.get("findings", []):
            if isinstance(finding, dict):
                check_unique_id("finding_id", finding.get("finding_id"), f"{prefix}.contribution.findings")
                check_evidence(finding.get("evidence_refs"), "findings")
        for rival in contribution.get("rival_positions", []):
            if isinstance(rival, dict):
                check_unique_id("position_id", rival.get("position_id"), f"{prefix}.contribution.rival_positions")
                check_evidence(rival.get("evidence_refs"), "rival_positions")

        assessments_by_claim: dict[str, list[dict[str, Any]]] = {}
        assessment_levels: dict[str, str] = {}
        for assessment in contribution.get("claim_assessments", []):
            if not isinstance(assessment, dict):
                continue
            claim_id = assessment.get("claim_id")
            if claim_id not in known_claim_ids:
                violations.append(f"{prefix}.contribution.claim_assessments referencia claim no declarado: '{claim_id}'.")
            if claim_id not in contribution_claims:
                violations.append(f"{prefix}.contribution.claim_assessments debe declarar '{claim_id}' en affected_claim_ids.")
            evidence_refs = check_evidence(assessment.get("evidence_refs"), "claim_assessments")
            level = assessment.get("support_level")
            assessments_by_claim.setdefault(claim_id, []).append(assessment)
            if claim_id in assessment_levels and assessment_levels[claim_id] != level:
                violations.append(f"{prefix}.contribution declara niveles de soporte incompatibles para claim '{claim_id}'.")
            assessment_levels[claim_id] = level
            if level in {"LIMITED", "NOT_SUPPORTED"} and not assessment.get("limitations"):
                violations.append(f"{prefix}.contribution claim '{claim_id}' requiere limitaciones explícitas para {level}.")
            if level == "SUPPORTED":
                authorities = {
                    (sources_by_id.get(ref, {}).get("provenance") or {}).get("claim_authority")
                    for ref in evidence_refs
                    if ref in sources_by_id
                }
                if not authorities or authorities == {"NONE"}:
                    violations.append(f"{prefix}.contribution claim '{claim_id}' no tiene evidencia con autoridad suficiente para SUPPORT.")

        dispositions_by_claim: dict[str, list[dict[str, Any]]] = {}
        for disposition in contribution.get("claim_dispositions", []):
            if not isinstance(disposition, dict):
                continue
            claim_id = disposition.get("claim_id")
            dispositions_by_claim.setdefault(claim_id, []).append(disposition)
            if claim_id not in known_claim_ids:
                violations.append(f"{prefix}.contribution.claim_dispositions referencia claim no declarado: '{claim_id}'.")
            if claim_id not in activation_claims:
                violations.append(f"{prefix}.contribution.claim_dispositions solo puede disponer claims de la activación original: '{claim_id}'.")
            check_evidence(disposition.get("evidence_refs"), "claim_dispositions")
            reason = disposition.get("reason")
            disposition_kind = disposition.get("disposition")
            if disposition_kind == "ASSESSED" and reason != "ASSESSMENT_COMPLETED":
                violations.append(f"{prefix}.claim_dispositions ASSESSED requiere reason=ASSESSMENT_COMPLETED para '{claim_id}'.")
            if disposition_kind == "NOT_ASSESSED" and reason == "ASSESSMENT_COMPLETED":
                violations.append(f"{prefix}.claim_dispositions NOT_ASSESSED no puede usar reason=ASSESSMENT_COMPLETED para '{claim_id}'.")

        for claim_id in contribution_claims:
            count = len(assessments_by_claim.get(claim_id, []))
            if count != 1:
                violations.append(f"{prefix}.affected_claim_ids requiere exactamente un assessment para '{claim_id}' (encontrados: {count}).")

        for claim_id, assessments in assessments_by_claim.items():
            if len(assessments) > 1:
                violations.append(f"{prefix}.claim_assessments no puede duplicar el claim '{claim_id}'.")

        for claim_id in activation_claims:
            dispositions = dispositions_by_claim.get(claim_id, [])
            assessments = assessments_by_claim.get(claim_id, [])
            if len(dispositions) != 1:
                violations.append(f"{prefix} debe conservar exactamente una disposición final para el claim inicial '{claim_id}'.")
                continue
            disposition = dispositions[0]
            kind = disposition.get("disposition")
            if kind == "ASSESSED":
                if claim_id not in contribution_claims or len(assessments) != 1:
                    violations.append(f"{prefix} claim inicial '{claim_id}' marcado ASSESSED debe estar afectado y tener un assessment.")
            elif kind == "NOT_ASSESSED":
                if claim_id in contribution_claims or assessments:
                    violations.append(f"{prefix} claim inicial '{claim_id}' no puede ser NOT_ASSESSED y conservar assessment/afectación final.")

        discovery_by_claim: dict[str, list[dict[str, Any]]] = {}
        reassessment_discoveries = 0
        for discovery in contribution.get("claim_discoveries", []):
            if not isinstance(discovery, dict):
                continue
            claim_id = discovery.get("claim_id")
            discovery_by_claim.setdefault(claim_id, []).append(discovery)
            if claim_id not in known_claim_ids:
                violations.append(f"{prefix}.claim_discoveries referencia claim no declarado: '{claim_id}'.")
            if claim_id in activation_claims:
                violations.append(f"{prefix}.claim_discoveries no puede volver a declarar como nuevo el claim inicial '{claim_id}'.")
            activation_id = activation.get("activation_id") if isinstance(activation, dict) else None
            if discovery.get("activation_ref") != activation_id:
                violations.append(f"{prefix}.claim_discoveries debe conservar activation_ref={activation_id!r}.")
            check_evidence(discovery.get("evidence_refs"), "claim_discoveries")
            relation = discovery.get("scope_relation")
            if relation == "ACTIVATION_REASSESSMENT_REQUIRED":
                reassessment_discoveries += 1
            if claim_id in contribution_claims and len(assessments_by_claim.get(claim_id, [])) != 1:
                violations.append(f"{prefix} claim descubierto '{claim_id}' afectado finalmente requiere exactamente un assessment.")

        for claim_id, discoveries in discovery_by_claim.items():
            if len(discoveries) > 1:
                violations.append(f"{prefix}.claim_discoveries no puede duplicar el claim descubierto '{claim_id}'.")

        for limit in contribution.get("operational_limits", []):
            if isinstance(limit, dict):
                check_unique_id("limit_id", limit.get("limit_id"), f"{prefix}.contribution.operational_limits")

        for claim_id in contribution_claims - activation_claims:
            if len(discovery_by_claim.get(claim_id, [])) != 1:
                violations.append(f"{prefix} claim nuevo afectado '{claim_id}' requiere un descubrimiento trazable único.")

        reassessment_status = contribution.get("activation_reassessment_status")
        if reassessment_discoveries and reassessment_status != "REQUIRED":
            violations.append(f"{prefix} declara un cambio material de misión sin ACTIVATION_REASSESSMENT_REQUIRED.")
        if reassessment_status == "REQUIRED" and not reassessment_discoveries:
            if contribution.get("activation_relation") != "MATERIAL_MISSION_CHANGE":
                violations.append(f"{prefix} no puede exigir reevaluación sin cambio material de misión u otra causa válida.")
        activation_relation = contribution.get("activation_relation")
        if activation_relation == "MATERIAL_MISSION_CHANGE":
            if reassessment_status != "REQUIRED":
                violations.append(f"{prefix} declara cambio material de misión pero mantiene ACTIVATION_REASSESSMENT_REQUIRED=NO.")
        elif activation_relation == "WITHIN_ORIGINAL_MISSION":
            if reassessment_discoveries:
                violations.append(f"{prefix} no puede declarar WITHIN_ORIGINAL_MISSION para un descubrimiento que exige reevaluación.")
            if reassessment_status == "REQUIRED":
                violations.append(f"{prefix} declara REQUIRED sin cambio material de misión declarado.")

        if entry.get("authority_status") != "SPECIALIST_CONTRIBUTION_ONLY":
            violations.append(f"{prefix} no puede declarar autoridad distinta de SPECIALIST_CONTRIBUTION_ONLY.")
        forbidden_authority = {"FACT", "CLAIM_AUTHORIZATION", "RESEARCH_SUFFICIENCY", "THESIS_APPROVAL"}
        declared_limits = set(entry.get("does_not_establish", []))
        if not forbidden_authority.issubset(declared_limits):
            violations.append(f"{prefix} debe conservar límites explícitos frente a hecho, claim, suficiencia y tesis.")
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
    known_research_ids = {
        item.get("item_id")
        for category in (
            "facts", "interpretations", "hypotheses", "contradictions", "alternative_views",
            "narrative_evidence", "external_reality_evidence", "claims_candidates", "narrative_opportunities",
        )
        for item in data.get(category, [])
        if isinstance(item, dict) and item.get("item_id")
    }
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
    known_claim_ids = set()
    claims = data.get("critical_claims_assessment", {})
    for entry in data.get("claims_candidates", []):
        if isinstance(entry, dict) and entry.get("item_id"):
            known_claim_ids.add(entry["item_id"])
    if isinstance(claims, dict):
        known_claim_ids.update(claims.get("claim_ids", []))
    known_subject_ids = {
        "WORK_INTERPRETATION": {
            item.get("item_id")
            for item in data.get("interpretations", [])
            if isinstance(item, dict) and item.get("item_id")
        },
        "MATERIAL_CLAIM": known_claim_ids,
    }
    for index, contradiction in enumerate(data.get("contradictions", [])):
        if isinstance(contradiction, dict):
            violations.extend(
                f"ResearchPack.contradictions[{index}]: {item}"
                for item in validate_contradiction_disposition(
                    contradiction,
                    known_sources,
                    known_research_ids,
                    known_claim_ids,
                    known_subject_ids,
                )
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
        if entry.get("status") == "PARTIALLY_COVERED":
            required = ("limitation_or_pending", "editorial_impact", "scope_decision", "propagated_constraint")
            if any(not entry.get(field) or entry.get(field) == "NONE" for field in required) or entry.get("editorial_impact") == "NOT_APPLICABLE":
                violations.append(f"Coverage parcial {entry.get('dimension_id')} requiere falta, impacto editorial, decisión de alcance y restricción propagada.")
    if isinstance(claims, dict) and claims.get("status") == "IDENTIFIED" and not claims.get("claim_ids"):
        violations.append("Critical claims identificados requieren claim_ids concretos.")
    if isinstance(claims, dict) and claims.get("status") == "NONE_JUSTIFIED":
        if not claims.get("justification") or claims.get("editorial_impact") == "NONE":
            violations.append("La ausencia de claims críticos requiere justificación e impacto editorial explícitos.")

    # IR1-002: el mapa de criticidad debe referenciar claims declaradas en el pack.
    editorial_uses = data.get("editorial_uses")
    if isinstance(editorial_uses, dict):
        criticality_map = editorial_uses.get("criticality_map", {})
        for entry in criticality_map.get("claims", []):
            if isinstance(entry, dict) and entry.get("claim_id") and entry["claim_id"] not in known_claim_ids:
                violations.append(
                    f"ResearchPack.editorial_uses.criticality_map referencia claim no declarada: '{entry['claim_id']}'."
                )
    # IR1-006: la representación y su dependencia se controlan por JSON Schema.
    semantic_status = data.get("semantic_status")
    if isinstance(semantic_status, dict):
        for status_entry in semantic_status.get("status_per_claim", []):
            if isinstance(status_entry, dict) and status_entry.get("claim_id") and status_entry["claim_id"] not in known_claim_ids:
                violations.append(
                    f"ResearchPack.semantic_status referencia claim no declarada: '{status_entry['claim_id']}'."
                )
    violations.extend(_validate_source_provenance(data.get("source_registry", []), "ResearchPack"))
    violations.extend(
        _validate_specialist_research(
            data.get("specialist_research", []),
            data.get("source_registry", []),
            known_sources,
            known_claim_ids,
        )
    )
    violations.extend(
        _validate_multilingual_research(
            data.get("multilingual_research"),
            "ResearchPack",
            known_sources,
            known_claim_ids,
        )
    )
    return violations


def validate_claims_ledger(data: Dict[str, Any]) -> List[str]:
    """
    Valida las entradas de ClaimsLedger (B1-C21).
    """
    # 1. Validación estructural con JSON Schema
    violations = validate_against_schema(data, "claims_ledger")

    # 2. Validación de negocio
    if "claims" in data and isinstance(data["claims"], list):
        claim_ids = [claim.get("claim_id") for claim in data["claims"] if isinstance(claim, dict)]
        if len(claim_ids) != len(set(claim_ids)):
            violations.append("ClaimsLedger no puede duplicar claim_id.")
        for idx, claim in enumerate(data["claims"]):
            if not isinstance(claim, dict):
                violations.append(f"Entrada claim en indice {idx} debe ser un diccionario.")
                continue
            
            if not isinstance(claim.get("claim_id"), str) or not claim.get("claim_id", "").strip():
                violations.append(f"Claim en indice {idx} requiere claim_id no vacío.")
            if not isinstance(claim.get("claim_text"), str) or not claim.get("claim_text", "").strip():
                violations.append(f"Claim en indice {idx} requiere claim_text no vacío.")
            # Verificar que source_refs no este vacio
            if "source_refs" in claim and isinstance(claim["source_refs"], list) and len(claim["source_refs"]) == 0:
                violations.append(f"Claim '{claim.get('claim_id')}' rechazada: No se permiten claims sin fuente ni estado de verificacion.")
            intended_use = claim.get("intended_use")
            if intended_use in {"EXACT_QUOTE", "PROVE_WORK_CONTENT", "YOUTUBE_POLICY"}:
                if not claim.get("provenance_evidence_refs"):
                    violations.append(
                        f"Claim '{claim.get('claim_id')}' con uso {intended_use} requiere provenance_evidence_refs."
                    )
                elif not set(claim["provenance_evidence_refs"]).issubset(set(claim.get("source_refs", []))):
                    violations.append(
                        f"Claim '{claim.get('claim_id')}' con uso {intended_use} requiere provenance_evidence_refs incluidas en source_refs."
                    )
                if claim.get("provenance_status") != "PRIMARY_VERIFIED":
                    violations.append(
                        f"Claim '{claim.get('claim_id')}' con uso {intended_use} requiere provenance_status=PRIMARY_VERIFIED."
                    )
                required_authority = "YOUTUBE_OFFICIAL_PRIMARY" if intended_use == "YOUTUBE_POLICY" else "PRIMARY_SOURCE"
                if claim.get("authority_basis") != required_authority:
                    violations.append(
                        f"Claim '{claim.get('claim_id')}' con uso {intended_use} requiere authority_basis={required_authority}."
                    )
            materiality = claim.get("materiality")
            requires_materiality = claim.get("criticality") in {"CENTRAL", "SENSITIVE", "CONTROVERSIAL"} or claim.get("intended_use") in {
                "CENTRAL_CLAIM_SUPPORT", "SENSITIVE_HANDLING", "CONTROVERSIAL_BALANCE", "EXACT_QUOTE", "PROVE_WORK_CONTENT", "YOUTUBE_POLICY"
            }
            if requires_materiality and not isinstance(materiality, dict):
                violations.append(f"Claim '{claim.get('claim_id')}' requiere assessment de materialidad explícito.")
            if isinstance(materiality, dict) and not materiality.get("is_material") and (
                materiality.get("activation_criteria") or materiality.get("decision_ref")
            ):
                violations.append(f"Claim '{claim.get('claim_id')}' no puede declarar criterios o decisión material con is_material=false.")
            if isinstance(materiality, dict) and materiality.get("is_material"):
                if not materiality.get("activation_criteria"):
                    violations.append(f"Claim material '{claim.get('claim_id')}' requiere activation_criteria explícitos.")
                if not materiality.get("decision_ref"):
                    violations.append(f"Claim material '{claim.get('claim_id')}' requiere ResearchStopDecision explícita.")
                if not materiality.get("invalidator_codes") or not materiality.get("return_route_code"):
                    violations.append(f"Claim material '{claim.get('claim_id')}' requiere invalidadores y ruta de retorno canónicos.")
            sufficiency = claim.get("research_sufficiency")
            decision = claim.get("claim_decision")
            if sufficiency == "BLOCKED_BY_EVIDENCE" and decision != "CLAIM_BLOCKED":
                violations.append(f"Claim '{claim.get('claim_id')}' bloqueado por evidencia requiere CLAIM_BLOCKED.")
            if decision == "CLAIM_BLOCKED" and sufficiency != "BLOCKED_BY_EVIDENCE":
                violations.append(f"Claim '{claim.get('claim_id')}' CLAIM_BLOCKED no puede presentarse con suficiencia no bloqueada.")
            if sufficiency == "LIMITED_BUT_USABLE" and not claim.get("limitations"):
                violations.append(f"Claim '{claim.get('claim_id')}' LIMITED_BUT_USABLE requiere limitaciones explícitas.")

    return violations


def validate_research_stop_decision(
    data: Dict[str, Any],
    component_decisions: Optional[List[Dict[str, Any]]] = None,
) -> List[str]:
    """Valida suficiencia por uso sin resolver contradicciones de R1-M7."""
    violations = validate_against_schema(data, "research_stop_decision")
    status = data.get("sufficiency_status")
    subject_kind = data.get("subject_kind")
    claim_decision = data.get("claim_decision")
    if subject_kind == "MATERIAL_CLAIM" and claim_decision is None:
        violations.append("ResearchStopDecision de claim material requiere claim_decision explícita.")
    if subject_kind == "MATERIAL_CLAIM" and (not data.get("invalidator_codes") or not data.get("return_route_code")):
        violations.append("ResearchStopDecision de claim material requiere invalidator_codes y return_route_code canónicos.")
    if status == "BLOCKED_BY_EVIDENCE" and claim_decision not in {None, "CLAIM_BLOCKED"}:
        violations.append("BLOCKED_BY_EVIDENCE no puede autorizar un claim.")
    if subject_kind == "MATERIAL_CLAIM":
        expected = {
            "CLAIM_ALLOWED": {"SUFFICIENT_FOR_INTENDED_USE", "LIMITED_BUT_USABLE"},
            "CLAIM_LIMITED": {"LIMITED_BUT_USABLE", "MORE_RESEARCH_REQUIRED"},
            "CLAIM_BLOCKED": {"BLOCKED_BY_EVIDENCE"},
        }
        if claim_decision in expected and status not in expected[claim_decision]:
            violations.append(f"{claim_decision} es incompatible con sufficiency_status={status}.")
    expected_routes = {
        "SUFFICIENT_FOR_INTENDED_USE": "AUTHORIZE_INTENDED_USE_ONLY",
        "LIMITED_BUT_USABLE": "RESTRICT_FORMULATION_AND_DISCLOSE",
        "MORE_RESEARCH_REQUIRED": "RETURN_TO_RESEARCH",
        "BLOCKED_BY_EVIDENCE": "REMOVE_REPLACE_OR_REFORMULATE",
    }
    route_code = data.get("return_route_code")
    if subject_kind == "MATERIAL_CLAIM" and status in expected_routes and route_code != expected_routes[status]:
        violations.append(f"sufficiency_status={status} requiere return_route_code={expected_routes[status]}.")
    if status == "LIMITED_BUT_USABLE" and not data.get("limitations"):
        violations.append("LIMITED_BUT_USABLE requiere limitaciones explícitas.")
    if status == "MORE_RESEARCH_REQUIRED" and (not data.get("pending_matters") or not data.get("return_route")):
        violations.append("MORE_RESEARCH_REQUIRED requiere pendientes y ruta de investigación.")
    if status in {"SUFFICIENT_FOR_INTENDED_USE", "LIMITED_BUT_USABLE"} and data.get("unresolved_material_contradiction_refs"):
        violations.append("Una contradicción material abierta impide suficiencia positiva en R1-M6.")
    if subject_kind == "AGGREGATE_RESEARCH_PACK":
        refs = data.get("component_decision_refs") or []
        required_refs = data.get("required_component_decision_refs") or []
        components = component_decisions or []
        if not components:
            violations.append("AGGREGATE_RESEARCH_PACK requiere decisiones de componentes verificables; no puede validar en modo fail-open.")
        component_ids = {item.get("decision_id") for item in components if isinstance(item, dict)}
        if status in {"SUFFICIENT_FOR_INTENDED_USE", "LIMITED_BUT_USABLE"} and not required_refs:
            violations.append("AGGREGATE_RESEARCH_PACK positivo requiere required_component_decision_refs completos.")
        if required_refs and set(required_refs) != set(refs):
            violations.append("required_component_decision_refs debe coincidir exactamente con component_decision_refs.")
        if refs and component_ids != set(refs):
            violations.append("AGGREGATE_RESEARCH_PACK debe materializar exactamente todas las decisiones referenciadas.")
        if refs and component_ids and not set(refs).issubset(component_ids):
            violations.append("AGGREGATE_RESEARCH_PACK contiene component_decision_refs sin decisión materializada.")
        for component in components:
            component_violations = validate_research_stop_decision(component)
            violations.extend(f"Componente {component.get('decision_id')}: {item}" for item in component_violations)
            if status == "SUFFICIENT_FOR_INTENDED_USE" and component.get("sufficiency_status") == "LIMITED_BUT_USABLE":
                violations.append("AGGREGATE_RESEARCH_PACK SUFFICIENT_FOR_INTENDED_USE no puede ocultar un componente LIMITED_BUT_USABLE.")
            if status in {"SUFFICIENT_FOR_INTENDED_USE", "LIMITED_BUT_USABLE"} and component.get("sufficiency_status") == "MORE_RESEARCH_REQUIRED":
                violations.append("AGGREGATE_RESEARCH_PACK positivo no puede avanzar con componente MORE_RESEARCH_REQUIRED.")
            if component.get("sufficiency_status") == "BLOCKED_BY_EVIDENCE":
                violations.append("AGGREGATE_RESEARCH_PACK no puede avanzar con componente material bloqueado.")
                break
    return violations



_CANONICAL_FUNCTIONAL_SOURCES = {
    "CHANNEL_INTELLIGENCE": {"policies/channel_intelligence/topic_belonging_policy.md"},
    "SCRIPT_PRODUCT": {
        "policies/script_product/main_episode_format_policy.md",
        "policies/script_product/episode_discovery_and_material_curation_policy.md",
    },
    "YOUTUBE_ADAPTATION": {"config/youtube_adaptation_r3_traceability.json"},
}


def _source_dimension_universe(owner: str, source_paths: List[Path]) -> Optional[set]:
    """Derive explicit source dimensions; unavailable universes fail closed.

    CI and SP are Markdown without independently versioned ID catalogs: CI
    uses its explicit evaluation bullets and SP its uppercase contract labels.
    Markdown versions are therefore presence-checked only; JSON registry
    versions are compared exactly.
    """
    if owner == "YOUTUBE_ADAPTATION":
        capabilities = set()
        for source_path in source_paths:
            payload = json.loads(source_path.read_text(encoding="utf-8"))
            capabilities.update(item.get("capability_id") for item in payload.get("capabilities", []) if isinstance(item, dict) and isinstance(item.get("capability_id"), str))
        return capabilities or None
    if owner == "SCRIPT_PRODUCT":
        dimensions = set()
        for source_path in source_paths:
            for line in source_path.read_text(encoding="utf-8").splitlines():
                marker = "FUNCTIONAL_DIMENSION:"
                if line.strip().startswith(marker):
                    value = line.strip()[len(marker):].strip()
                    if value:
                        dimensions.add(value)
        return dimensions or None
    if owner == "CHANNEL_INTELLIGENCE":
        source_text = source_paths[0].read_text(encoding="utf-8")
        section = source_text.split("## 2. Criterio funcional completo de evaluación", 1)
        if len(section) != 2:
            return None
        dimensions = set()
        for line in section[1].split("## ", 1)[0].splitlines():
            match = re.match(r"\s*-\s+(.+?)\.?\s*$", line)
            if match:
                value = unicodedata.normalize("NFKD", match.group(1))
                value = "".join(char for char in value if not unicodedata.combining(char))
                value = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_").lower()
                if value:
                    dimensions.add(value)
        return dimensions or None
    return None

def validate_semantic_assurance(data: Dict[str, Any]) -> List[str]:
    """Require source-derived coverage; producer-declared dimensions are not authority."""
    violations: List[str] = []
    bindings = data.get("functional_dimension_sources", {})
    assurance = data.get("semantic_assurance", {})
    evaluated = assurance.get("evaluated_dimensions", {})
    for owner, canonical_refs in _CANONICAL_FUNCTIONAL_SOURCES.items():
        binding = bindings.get(owner)
        if not isinstance(binding, dict):
            violations.append(f"SEMANTIC_SOURCE_MISSING:{owner}")
            continue
        bound_refs = set()
        source_paths = []
        for source in binding.get("sources", []):
            artifact_ref = source.get("artifact_ref") if isinstance(source, dict) else None
            if artifact_ref not in canonical_refs:
                violations.append(f"SEMANTIC_SOURCE_NON_CANONICAL:{owner}:{artifact_ref}")
                continue
            bound_refs.add(artifact_ref)
            if not source.get("version"):
                violations.append(f"SEMANTIC_SOURCE_VERSION_MISSING:{owner}:{artifact_ref}")
            source_path = Path(__file__).resolve().parents[2] / artifact_ref
            source_paths.append(source_path)
            if source_path.suffix == ".json" and source_path.is_file():
                try:
                    canonical_version = json.loads(source_path.read_text(encoding="utf-8")).get("registry_version")
                except (OSError, ValueError, json.JSONDecodeError):
                    canonical_version = None
                if canonical_version and source.get("version") != canonical_version:
                    violations.append(f"SEMANTIC_SOURCE_VERSION_MISMATCH:{owner}:{artifact_ref}")
            declared_checksum = str(source.get("checksum") or "").lower()
            if not source_path.is_file() or hashlib.sha256(source_path.read_bytes()).hexdigest() != declared_checksum:
                violations.append(f"SEMANTIC_SOURCE_CHECKSUM_MISMATCH:{owner}:{artifact_ref}")
        for artifact_ref in sorted(canonical_refs - bound_refs):
            violations.append(f"SEMANTIC_SOURCE_INCOMPLETE:{owner}:{artifact_ref}")
        expected = None
        if canonical_refs == bound_refs and all(path.is_file() for path in source_paths):
            try:
                expected = _source_dimension_universe(owner, source_paths)
            except (OSError, ValueError, json.JSONDecodeError):
                expected = None
        if not expected:
            violations.append(f"SEMANTIC_DIMENSION_UNIVERSE_UNAVAILABLE:{owner}")
            continue
        actual_items = evaluated.get(owner, []) if isinstance(evaluated, dict) else []
        actual = {item.get("dimension") for item in actual_items if isinstance(item, dict)}
        for dimension in sorted(actual - expected):
            violations.append(f"SEMANTIC_DIMENSION_NOT_CANONICAL:{owner}:{dimension}")
        for dimension in sorted(expected - actual):
            violations.append(f"SEMANTIC_DIMENSION_NOT_EVALUATED:{owner}:{dimension}")
        for item in actual_items:
            if isinstance(item, dict) and item.get("dimension") in expected:
                if item.get("status") != "EVALUATED":
                    violations.append(f"SEMANTIC_DIMENSION_INCOMPLETE:{owner}:{item.get('dimension')}")
                if item.get("status") == "EVALUATED" and not item.get("evidence_refs"):
                    violations.append(f"SEMANTIC_DIMENSION_WITHOUT_EVIDENCE:{owner}:{item.get('dimension')}")
    if assurance.get("status") == "PASS" and violations:
        violations.append("SEMANTIC_PASS_REQUIRES_COMPLETE_CANONICAL_COVERAGE")
    return violations
def validate_editorial_semantic_memory(data: Dict[str, Any]) -> List[str]:
    """Valida que la memoria sea evidencia gobernada y no autoridad editorial autónoma."""
    violations = validate_against_schema(data, "editorial_semantic_memory")
    violations.extend(validate_semantic_assurance(data))
    points = set(data.get("consultation_points", []))
    required_points = {"PROPOSAL", "PRE_FINAL_CURATION", "PRE_THESIS_OR_ARCHITECTURE", "OPENING_UNIT_REVIEW", "PRE_FINAL_SCRIPT"}
    if not required_points.issubset(points):
        violations.append("EditorialSemanticMemory no cubre todos los momentos obligatorios de consulta.")
    for decision in data.get("comparison_decisions", []):
        if not isinstance(decision, dict):
            continue
        kind = decision.get("decision")
        action = decision.get("recommended_action")
        reuse = decision.get("continuation_or_reuse")
        if kind == "TOO_SIMILAR" and action != "REVIEW_REQUIRED":
            violations.append("TOO_SIMILAR exige revisión funcional; no es una decisión editorial autónoma.")
        if kind == "INSUFFICIENT_HISTORY" and action != "REVIEW_REQUIRED":
            violations.append("INSUFFICIENT_HISTORY no puede ser PASS ni NO_ACTION.")
        if kind in {"INTENTIONAL_CONTINUATION", "REUSE_REQUIRES_JUSTIFICATION"} and not isinstance(reuse, dict):
            violations.append(f"{kind} requiere continuidad o reutilización explícitamente referenciada.")
        if kind == "REUSE_REQUIRES_JUSTIFICATION" and action not in {"JUSTIFICATION_REQUIRED", "REVIEW_REQUIRED"}:
            violations.append("REUSE_REQUIRES_JUSTIFICATION requiere justificación o revisión.")
        if kind != "INSUFFICIENT_HISTORY" and not decision.get("compared_episode_refs"):
            violations.append(f"{kind} requiere episodios previos concretos, no similitud abstracta.")
        if decision.get("candidate_episode_ref") in decision.get("compared_episode_refs", []):
            violations.append(f"{kind} no puede compararse consigo mismo.")
        evidence_refs = [str(ref).lower() for ref in decision.get("evidence_refs", [])]
        machine_only = ("keyword", "keywords", "score:", "embedding", "cosine", "similarity")
        if evidence_refs and all(any(token in ref for token in machine_only) for ref in evidence_refs):
            violations.append(f"{kind} no puede aprobarse con evidencia basada solo en keywords, scores o similitud matemática.")
        if kind == "INSUFFICIENT_HISTORY" and decision.get("compared_episode_refs"):
            violations.append("INSUFFICIENT_HISTORY no puede declarar episodios comparados como si existiera historial suficiente.")
        entries = data.get("episode_entries", [])
        if kind != "INSUFFICIENT_HISTORY":
            known = {
                (ref.get("artifact_ref"), ref.get("version"), ref.get("checksum"))
                for entry in entries if isinstance(entry, dict)
                for ref in entry.get("artifact_refs", []) if isinstance(ref, dict)
            }
            for ref in [decision.get("candidate_episode_ref"), *decision.get("compared_episode_refs", [])]:
                if isinstance(ref, dict) and (ref.get("artifact_ref"), ref.get("version"), ref.get("checksum")) not in known:
                    violations.append(f"{kind} referencia un episodio cuya versión/checksum no está en la memoria canónica.")
            reuse_ref = (reuse or {}).get("prior_artifact_ref") if isinstance(reuse, dict) else None
            if kind in {"INTENTIONAL_CONTINUATION", "REUSE_REQUIRES_JUSTIFICATION"} and reuse_ref not in {r.get("artifact_ref") for r in decision.get("compared_episode_refs", []) if isinstance(r, dict)}:
                violations.append(f"{kind} debe referenciar explícitamente uno de los episodios comparados.")
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

    # IR1-013: modelo claim-dependent; cada evaluación debe referenciar una claim declarada.
    declared_claim_ids = set()
    for field in ("claims_sostenibles", "claims_pendientes", "excluded_claims"):
        for item in data.get(field, []):
            if isinstance(item, dict) and item.get("claim_id"):
                declared_claim_ids.add(item["claim_id"])
            elif isinstance(item, str):
                declared_claim_ids.add(item)
    for item in data.get("critical_claim_assessments", []):
        if isinstance(item, dict) and item.get("claim_id"):
            declared_claim_ids.add(item["claim_id"])

    for index, evaluation in enumerate(data.get("claim_dependent_source_evaluations", [])):
        if not isinstance(evaluation, dict):
            continue
        claim_id = evaluation.get("claim_id")
        if claim_id and claim_id not in declared_claim_ids:
            violations.append(
                f"claim_dependent_source_evaluations[{index}] referencia claim no declarada: '{claim_id}'."
            )
        if evaluation.get("source_id") not in known_sources:
            violations.append(
                f"claim_dependent_source_evaluations[{index}] referencia fuente no declarada: '{evaluation.get('source_id')}'."
            )
    # IR1-005: independencia entre fuentes declarada.
    for group in data.get("independence_groups", []):
        if not isinstance(group, dict):
            continue
        for source_id in group.get("source_ids", []):
            if source_id not in known_sources:
                violations.append(f"independence_groups referencia fuente desconocida: '{source_id}'.")

    violations.extend(
        _validate_source_provenance(
            [
                item
                for field in ("fuentes_primarias", "fuentes_secundarias")
                for item in data.get(field, [])
                if isinstance(item, dict)
            ],
            "SourceAccessAndEvidenceReport",
            data.get("claim_dependent_source_evaluations", []),
        )
    )
    violations.extend(
        _validate_multilingual_research(
            data.get("multilingual_research"),
            "SourceAccessAndEvidenceReport",
            known_sources,
            declared_claim_ids,
        )
    )

    return violations


def _canonical_artifact_checksum(value: Dict[str, Any]) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate_work_research_dossier(
    data: Dict[str, Any],
    claims_ledger: Optional[Dict[str, Any]] = None,
    narrative_analyses: Optional[List[Dict[str, Any]]] = None,
) -> List[str]:
    """Valida el dossier por madurez y resuelve referencias contra artefactos canonicos."""
    violations = validate_against_schema(data, "work_research_dossier")
    stage = data.get("dossier_stage")
    mature_fields = {
        "analysis_references", "question_and_thesis_relation", "claim_dispositions",
        "overinterpretation_risk", "candidate_editorial_function_analysis_ref", "locators",
        "work_use_sufficiency", "research_stop_decision_ref", "independent_fidelity_audit",
    }
    if stage == "IDENTIFIED":
        for field in sorted(mature_fields.intersection(data)):
            violations.append(f"WorkResearchDossier IDENTIFIED no puede declarar artefacto maduro: '{field}'.")
        return violations
    mature_declared = bool(mature_fields.intersection(data))
    if claims_ledger is None or narrative_analyses is None:
        if stage == "RESEARCH_REVIEW_PENDING" or (stage == "RESEARCH_IN_PROGRESS" and mature_declared):
            violations.append("WorkResearchDossier requiere artefactos canonicos para resolver referencias en la fase declarada.")
        return violations
    violations.extend(validate_against_schema(claims_ledger, "claims_ledger"))
    analyses_by_id = {
        analysis.get("analysis_id"): analysis for analysis in narrative_analyses
        if isinstance(analysis, dict) and analysis.get("analysis_id")
    }
    work = data.get("work") if isinstance(data.get("work"), dict) else {}
    declared_analysis_ids = {
        entry.get("analysis_id") for entry in data.get("analysis_references", [])
        if isinstance(entry, dict) and entry.get("analysis_id")
    }
    if stage == "RESEARCH_REVIEW_PENDING":
        for reference in data.get("analysis_references", []):
            if not reference.get("artifact_version") or not reference.get("artifact_checksum"):
                violations.append("WorkResearchDossier RESEARCH_REVIEW_PENDING requiere version y checksum de cada NarrativeHumanAnalysis.")
        dispositions = data.get("claim_dispositions") if isinstance(data.get("claim_dispositions"), dict) else {}
        if not dispositions.get("claims_ledger_version") or not dispositions.get("claims_ledger_checksum"):
            violations.append("WorkResearchDossier RESEARCH_REVIEW_PENDING requiere version y checksum del ClaimsLedger.")
    for reference in data.get("analysis_references", []):
        if not isinstance(reference, dict):
            continue
        analysis_id = reference.get("analysis_id")
        analysis = analyses_by_id.get(analysis_id)
        if analysis is None:
            violations.append(f"WorkResearchDossier.analysis_references referencia análisis inexistente: '{analysis_id}'.")
            continue
        if reference.get("artifact_version") is not None and reference.get("artifact_version") != analysis.get("artifact_version"):
            violations.append(f"WorkResearchDossier.analysis_references version no coincide para '{analysis_id}'.")
        if reference.get("artifact_checksum") is not None and reference.get("artifact_checksum") != _canonical_artifact_checksum(analysis):
            violations.append(f"WorkResearchDossier.analysis_references checksum no coincide para '{analysis_id}'.")
        for field in ("episode_id", "research_id", "evidence_report_id"):
            if data.get(field) != analysis.get(field):
                violations.append(f"WorkResearchDossier y análisis '{analysis_id}' difieren en '{field}'.")
        if reference.get("material_id") != analysis.get("material_id"):
            violations.append(f"WorkResearchDossier.analysis_references no conserva material_id de '{analysis_id}'.")
        if reference.get("material_id") != work.get("material_id"):
            violations.append(f"WorkResearchDossier.analysis_references no pertenece a la obra del dossier: '{analysis_id}'.")
        analysis_violations = validate_against_schema(analysis, "narrative_human_analysis")
        violations.extend(f"NarrativeHumanAnalysis '{analysis_id}': {violation}" for violation in analysis_violations)
    relation = data.get("question_and_thesis_relation", {})
    if isinstance(relation, dict):
        for field in (
            "demonstrates_analysis_ref",
            "does_not_establish_analysis_ref",
            "main_interpretation_analysis_ref",
        ):
            if relation.get(field) and relation[field] not in declared_analysis_ids:
                violations.append(f"WorkResearchDossier.{field} referencia análisis no declarado: '{relation[field]}'.")
        for analysis_id in relation.get("rival_interpretation_analysis_refs", []):
            if analysis_id not in declared_analysis_ids:
                violations.append(
                    f"WorkResearchDossier.rival_interpretation_analysis_refs referencia análisis no declarado: '{analysis_id}'."
                )
    function_ref = data.get("candidate_editorial_function_analysis_ref")
    if function_ref not in declared_analysis_ids:
        violations.append(f"WorkResearchDossier.candidate_editorial_function_analysis_ref referencia análisis no declarado: '{function_ref}'.")
    for entry in data.get("locators", []):
        if isinstance(entry, dict) and entry.get("analysis_id") not in declared_analysis_ids:
            violations.append(f"WorkResearchDossier.locators referencia análisis no declarado: '{entry.get('analysis_id')}'.")

    dispositions = data.get("claim_dispositions", {})
    if not isinstance(dispositions, dict):
        return violations
    disposition_sets = {
        name: set(dispositions.get(name, []))
        for name in ("candidate_allowed_claim_ids", "candidate_limited_claim_ids", "candidate_blocked_claim_ids")
    }
    names = list(disposition_sets)
    for index, name in enumerate(names):
        for other in names[index + 1:]:
            overlap = disposition_sets[name] & disposition_sets[other]
            if overlap:
                violations.append(
                    f"WorkResearchDossier.claim_dispositions no permite claims en {name} y {other}: {', '.join(sorted(overlap))}."
                )

    if dispositions.get("claims_ledger_id") != claims_ledger.get("ledger_id"):
        violations.append("WorkResearchDossier referencia un claims_ledger_id distinto del ledger suministrado.")
    if dispositions.get("claims_ledger_version") is not None and dispositions.get("claims_ledger_version") != claims_ledger.get("script_version"):
        violations.append("WorkResearchDossier referencia una version de ClaimsLedger distinta del ledger suministrado.")
    if dispositions.get("claims_ledger_checksum") is not None and dispositions.get("claims_ledger_checksum") != _canonical_artifact_checksum(claims_ledger):
        violations.append("WorkResearchDossier referencia un checksum de ClaimsLedger distinto del ledger suministrado.")
    known_claim_ids = {
        claim.get("claim_id") for claim in claims_ledger.get("claims", [])
        if isinstance(claim, dict) and claim.get("claim_id")
    }
    for claim_id in set().union(*disposition_sets.values()):
        if claim_id not in known_claim_ids:
            violations.append(f"WorkResearchDossier referencia claim inexistente en ledger: '{claim_id}'.")

    return violations



def validate_work_lifecycle(
    data: Dict[str, Any],
    dossiers: Optional[List[Dict[str, Any]]] = None,
    material_curation: Optional[Dict[str, Any]] = None,
) -> List[str]:
    """Valida el lifecycle de obras sin duplicar dossier ni curación."""
    violations = validate_against_schema(data, "work_lifecycle")
    works = [item for item in data.get("works", []) if isinstance(item, dict)]
    works_by_id = {item.get("work_id"): item for item in works if item.get("work_id")}
    if len(works_by_id) != len(works):
        violations.append("WorkLifecycle no permite work_id duplicados o ausentes.")

    entry_mode = data.get("entry_mode")
    anchor_id = data.get("anchor_work_id")
    if entry_mode == "ANCHOR_WORK_FIRST":
        if not anchor_id or anchor_id not in works_by_id:
            violations.append("ANCHOR_WORK_FIRST requiere anchor_work_id declarado en works.")
        elif works_by_id[anchor_id].get("is_anchor") is not True:
            violations.append("La obra ancla declarada debe conservar is_anchor=true.")
    elif anchor_id is not None:
        violations.append("anchor_work_id solo puede existir con entrada ANCHOR_WORK_FIRST.")

    states = {"DISCOVERED_WORK", "SCREENED_WORK", "FINALIST_WORK", "FINAL_SELECTED_WORK", "EXCLUDED_WORK", "INVALIDATED_WORK"}
    promotion_targets = {
        "DISCOVERED_WORK": "SCREENED_WORK",
        "SCREENED_WORK": "FINALIST_WORK",
        "FINALIST_WORK": "FINAL_SELECTED_WORK",
    }
    transitions_by_work: Dict[str, List[Dict[str, Any]]] = {}
    transitions_by_id: Dict[str, Dict[str, Any]] = {}
    transition_indexes: Dict[str, int] = {}
    registry = _load_responsibility_registry()
    for transition_index, transition in enumerate(data.get("transitions", [])):
        if not isinstance(transition, dict):
            continue
        work_id = transition.get("work_id")
        transition_id = transition.get("transition_id")
        if transition_id in transitions_by_id:
            violations.append(f"WorkLifecycle no permite transition_id duplicado: '{transition_id}'.")
        else:
            transitions_by_id[transition_id] = transition
            transition_indexes[transition_id] = transition_index
        transitions_by_work.setdefault(work_id, []).append(transition)
        if work_id not in works_by_id:
            violations.append(f"WorkLifecycle.transition referencia obra desconocida: '{work_id}'.")
        previous = transition.get("previous_state")
        target = transition.get("target_state")
        transition_type = transition.get("transition_type")
        authority_role = transition.get("authority_role")
        authority_ref = transition.get("transition_authority_ref")
        authority = registry.get(authority_role)
        expected_authority_ref = f"{RESPONSIBILITY_REGISTRY_REF_PREFIX}{authority_role}" if authority_role else None
        if authority is None:
            violations.append(f"Transición '{transition_id}' referencia una authority_role inexistente: '{authority_role}'.")
        elif authority.get("functional_owner") != "SCRIPT_PRODUCT":
            violations.append(f"Transición '{transition_id}' referencia una autoridad fuera de SCRIPT_PRODUCT.")
        elif authority_role != "RESEARCH_AND_CURATION":
            violations.append(f"Transición '{transition_id}' usa una responsabilidad no válida para lifecycle de obras.")
        if expected_authority_ref != authority_ref:
            violations.append(f"Transición '{transition_id}' debe referenciar canónicamente la autoridad declarada.")
        if previous not in states or target not in states or previous == target:
            violations.append(f"Transición '{transition.get('transition_id')}' tiene estados inválidos o iguales.")
        if transition_type == "PROMOTION":
            if promotion_targets.get(previous) != target:
                violations.append(
                    f"Transición promocional '{transition.get('transition_id')}' no respeta la progresión ordenada."
                )
        elif transition_type == "EXCLUSION" and target != "EXCLUDED_WORK":
            violations.append(f"La transición de exclusión '{transition.get('transition_id')}' debe terminar en EXCLUDED_WORK.")
        elif transition_type == "INVALIDATION" and target != "INVALIDATED_WORK":
            violations.append(f"La transición de invalidación '{transition.get('transition_id')}' debe terminar en INVALIDATED_WORK.")
        elif target in {"FINALIST_WORK", "FINAL_SELECTED_WORK"}:
            violations.append(f"La promoción a '{target}' debe usar transition_type=PROMOTION.")
        if transition_type == "REOPENED":
            if not transition.get("previous_transition_ref") or not transition.get("authorized_return_state"):
                violations.append(f"Reapertura '{transition.get('transition_id')}' requiere lineage y estado de retorno.")
            previous_transition_ref = transition.get("previous_transition_ref")
            previous_transition = transitions_by_id.get(previous_transition_ref)
            if previous_transition is None:
                violations.append(f"Reapertura '{transition_id}' referencia una transición inexistente.")
            else:
                if previous_transition.get("work_id") != work_id:
                    violations.append(f"Reapertura '{transition_id}' referencia una transición de otra obra.")
                if transition_indexes.get(previous_transition_ref, transition_index) >= transition_index:
                    violations.append(f"Reapertura '{transition_id}' debe referenciar una transición anterior.")
                if previous_transition.get("target_state") != previous:
                    violations.append(f"Reapertura '{transition_id}' no enlaza su estado previo con la transición referenciada.")
            if transition.get("authorized_return_state") != target:
                violations.append(f"Reapertura '{transition.get('transition_id')}' debe coincidir con su estado de retorno.")
            if previous in {"EXCLUDED_WORK", "INVALIDATED_WORK"} and target == "FINAL_SELECTED_WORK":
                violations.append("Una obra excluida o invalidada no puede reabrirse directamente como final seleccionada.")
        if transition_type in {"PROMOTION", "EXCLUSION", "INVALIDATION", "REOPENED"} and not transition.get("decision", {}).get("status") == "EXPLICIT":
            violations.append(f"Transición '{transition.get('transition_id')}' requiere una decisión explícita.")

    for work_id, work in works_by_id.items():
        history = transitions_by_work.get(work_id, [])
        if work.get("state") != "DISCOVERED_WORK" and not history:
            violations.append(f"'{work_id}' en estado derivado requiere una transición explícita.")
        if history and history[0].get("previous_state") != "DISCOVERED_WORK":
            violations.append(f"El lineage de '{work_id}' no reconstruye su origen DISCOVERED_WORK.")
        for history_index, (previous_transition, next_transition) in enumerate(zip(history, history[1:]), start=1):
            if next_transition.get("previous_state") != previous_transition.get("target_state"):
                violations.append(f"El lineage de transiciones de '{work_id}' no conserva continuidad de estado.")
            if next_transition.get("transition_type") == "REOPENED" and next_transition.get("previous_transition_ref") != previous_transition.get("transition_id"):
                violations.append(f"Reapertura '{next_transition.get('transition_id')}' debe referenciar la transición inmediata anterior de '{work_id}'.")
        if history and history[-1].get("target_state") != work.get("state"):
            violations.append(f"El estado actual de '{work_id}' no coincide con la última transición registrada.")
        state = work.get("state")
        if state == "SCREENED_WORK" and not work.get("screening_ref"):
            violations.append(f"SCREENED_WORK '{work_id}' requiere referencia de screening.")
        if state == "FINALIST_WORK" and not work.get("dossier_ref"):
            violations.append(f"FINALIST_WORK '{work_id}' requiere referencia a WorkResearchDossier.")
        if state == "FINAL_SELECTED_WORK":
            for field in ("dossier_ref", "differentiated_function_ref", "comparative_decision_ref"):
                if not work.get(field):
                    violations.append(f"FINAL_SELECTED_WORK '{work_id}' requiere {field}.")
        if state in {"FINALIST_WORK", "FINAL_SELECTED_WORK"} and not history:
            violations.append(f"'{work_id}' no puede aparecer promocionada sin transición explícita.")

    screening = data.get("screening", {})
    candidate_ids = set(screening.get("candidate_work_ids", [])) if isinstance(screening, dict) else set()
    if not candidate_ids.issubset(works_by_id):
        violations.append("Screening referencia obras no declaradas en WorkLifecycle.")
    screening_status = screening.get("range_status") if isinstance(screening, dict) else None
    screening_exception = screening.get("exception") if isinstance(screening, dict) else None
    if candidate_ids:
        if screening_status == "NOT_APPLICABLE":
            violations.append("Un screening con candidatas declaradas no puede ser NOT_APPLICABLE.")
        if screening_status == "NORMAL" and not 5 <= len(candidate_ids) <= 8:
            violations.append("El screening NORMAL requiere entre 5 y 8 candidatas.")
        if screening_status == "EXCEPTION" and not screening_exception:
            violations.append("El screening EXCEPTION requiere referencia explícita de excepción aprobada.")
        if len(candidate_ids) not in range(5, 9) and screening_status not in {"EXCEPTION"}:
            violations.append("Un screening fuera del rango 5–8 requiere excepción explícita.")
        if screening_exception and screening_status != "EXCEPTION":
            violations.append("Una excepción de screening debe declararse como EXCEPTION.")
    elif screening_status == "NORMAL":
        violations.append("Un screening NORMAL requiere candidatas declaradas.")

    final_selection = data.get("final_selection", {})
    selected_ids = set(final_selection.get("selected_work_ids", [])) if isinstance(final_selection, dict) else set()
    if not selected_ids.issubset(works_by_id):
        violations.append("Final selection referencia obras no declaradas en WorkLifecycle.")
    final_status = final_selection.get("range_status") if isinstance(final_selection, dict) else None
    final_exception = final_selection.get("exception") if isinstance(final_selection, dict) else None
    if selected_ids:
        if final_status == "NOT_APPLICABLE":
            violations.append("Una selección final con obras declaradas no puede ser NOT_APPLICABLE.")
        if final_status == "NORMAL" and not 3 <= len(selected_ids) <= 5:
            violations.append("La selección final NORMAL requiere entre 3 y 5 obras sustantivas.")
        if final_status == "EXCEPTION" and not final_exception:
            violations.append("La selección final EXCEPTION requiere referencia explícita de excepción aprobada.")
        if len(selected_ids) not in range(3, 6) and final_status != "EXCEPTION":
            violations.append("Una selección final fuera del rango 3–5 requiere excepción explícita.")
        if final_exception and final_status != "EXCEPTION":
            violations.append("Una excepción de selección final debe declararse como EXCEPTION.")
    if selected_ids:
        for work_id in selected_ids:
            if works_by_id[work_id].get("state") != "FINAL_SELECTED_WORK":
                violations.append(f"La obra '{work_id}' seleccionada debe estar en FINAL_SELECTED_WORK.")
        if not final_selection.get("curation_ref"):
            violations.append("La selección final requiere referencia a MaterialCuration.")
        if material_curation is not None:
            curation_id = material_curation.get("curation_id")
            if curation_id != final_selection.get("curation_ref"):
                violations.append("La selección final referencia una MaterialCuration distinta de la suministrada.")
            curation_selected = set(material_curation.get("selected_material_ids", [])) | set(material_curation.get("selected_materials", []))
            if selected_ids != curation_selected:
                violations.append("Las obras seleccionadas no coinciden con MaterialCuration.")
            selected_materials = {
                item.get("material_id"): item
                for item in material_curation.get("candidates", [])
                if isinstance(item, dict) and item.get("material_id")
            }
            contributions = {item.get("material_id") for item in material_curation.get("function_of_each_selected_material", []) if isinstance(item, dict)}
            progression = {item.get("material_id") for item in material_curation.get("progression_evidence", []) if isinstance(item, dict)}
            for work_id in selected_ids:
                material = selected_materials.get(work_id)
                if not material or material.get("selection_status") != "SELECTED" or work_id not in contributions or work_id not in progression:
                    violations.append(f"La obra '{work_id}' no demuestra función y progresión sustantivas en MaterialCuration.")
    elif final_status == "NORMAL":
        violations.append("Una selección final NORMAL requiere obras declaradas.")

    dossier_by_id = {item.get("dossier_id"): item for item in (dossiers or []) if isinstance(item, dict) and item.get("dossier_id")}
    for work in works:
        dossier_ref = work.get("dossier_ref")
        if dossier_ref and dossiers is not None:
            dossier = dossier_by_id.get(dossier_ref)
            if dossier is None:
                violations.append(f"WorkLifecycle referencia WorkResearchDossier inexistente: '{dossier_ref}'.")
            elif dossier.get("work", {}).get("material_id") != work.get("work_id"):
                violations.append(f"WorkLifecycle y WorkResearchDossier difieren para la obra '{work.get('work_id')}'.")

    for doubt in data.get("critical_doubts", []):
        if not isinstance(doubt, dict):
            continue
        work_id = doubt.get("work_id")
        if work_id not in works_by_id:
            violations.append(f"CriticalWorkDoubt referencia obra desconocida: '{work_id}'.")
            continue
        status = doubt.get("authorization_status")
        return_trigger = doubt.get("return_trigger")
        return_route = doubt.get("return_route")
        external_routes = {"CHANNEL_INTELLIGENCE_REVIEW_REQUIRED", "YOUTUBE_ADAPTATION_REVIEW_REQUIRED"}
        trigger_routes = {
            "MATERIAL_QUESTION_INTENT_TERRITORY_CHANGE": "CHANNEL_INTELLIGENCE_REVIEW_REQUIRED",
            "VISIBLE_PROMISE_OR_EARLY_PACKAGING_IMPACT": "YOUTUBE_ADAPTATION_REVIEW_REQUIRED",
        }
        expected_external_route = trigger_routes.get(return_trigger)
        if return_route in external_routes and expected_external_route != return_route:
            violations.append("Una ruta externa de duda crítica requiere su trigger externo correspondiente.")
        if return_trigger is not None and return_route != expected_external_route:
            violations.append("El trigger externo de duda crítica debe corresponder exactamente a su ruta.")
        if return_route not in external_routes and return_trigger is not None:
            violations.append("Un trigger externo de duda crítica no puede retornar silenciosamente a una ruta interna.")
        if status in {"ACTIVE", "RESOLVED"}:
            if works_by_id[work_id].get("state") in {"FINALIST_WORK", "FINAL_SELECTED_WORK"}:
                violations.append("Una duda crítica activa o resuelta solo puede afectar una obra no finalista.")
            if status == "ACTIVE":
                if not doubt.get("activation_criteria") or not doubt.get("evidence_refs") or not doubt.get("authorized_actions") or not doubt.get("authorization_ref"):
                    violations.append("Una duda crítica activa requiere criterio, evidencia, acciones y autorización.")
                if doubt.get("outcome") not in doubt.get("authorized_actions", []):
                    violations.append("El resultado de una duda crítica activa debe estar entre sus acciones autorizadas.")
            else:
                if not doubt.get("activation_criteria") or not doubt.get("authorization_ref") or not doubt.get("evidence_refs") or not doubt.get("authorized_actions") or not doubt.get("scope") or doubt.get("outcome") == "NOT_APPLICABLE":
                    violations.append("Una duda crítica RESOLVED requiere conservar activación, autorización, evidencia, alcance, acciones y resultado.")
                if doubt.get("outcome") not in doubt.get("authorized_actions", []):
                    violations.append("El resultado de una duda crítica RESOLVED debe estar entre las acciones autorizadas.")
            expected_route = {
                "CONTINUE_SCREENING": "RETURN_TO_SCREENING",
                "PROMOTE_TO_FINALIST_CONSIDERATION": "RETURN_TO_SCREENING",
                "EXCLUDE_FOR_CURRENT_EPISODE": "EXCLUDED_WORK",
                "REQUIRE_MORE_TARGETED_RESEARCH": "MORE_TARGETED_RESEARCH_REQUIRED",
                "BLOCK_BY_EVIDENCE": "BLOCKED_BY_EVIDENCE",
            }.get(doubt.get("outcome"))
            if expected_route and doubt.get("return_route") != expected_route and doubt.get("return_route") not in external_routes:
                violations.append("La duda crítica activa debe conservar una ruta de retorno coherente con su resultado.")
        elif status == "NOT_ACTIVATED":
            if not doubt.get("non_trigger_examples") or doubt.get("activation_criteria") or doubt.get("authorized_actions") or doubt.get("authorization_ref") or doubt.get("outcome") != "NOT_APPLICABLE":
                violations.append("Una duda NOT_ACTIVATED solo puede conservar NON_TRIGGER y no autoriza profundización.")
        elif status == "INVALIDATED":
            if not doubt.get("invalidators") or doubt.get("authorization_ref") or doubt.get("authorized_actions") or doubt.get("outcome") != "NOT_APPLICABLE":
                violations.append("Una duda INVALIDATED debe conservar invalidadores y cortar la autorización.")

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
