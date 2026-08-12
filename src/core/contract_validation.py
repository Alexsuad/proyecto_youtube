"""
Módulo de Validación Determinista de Contratos y Reglas de Negocio Agénticas
Proyecto YouTube — Sistema Agéntico Editorial
"""

import os
import json
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
        if entry.get("status") == "PARTIALLY_COVERED":
            required = ("limitation_or_pending", "editorial_impact", "scope_decision", "propagated_constraint")
            if any(not entry.get(field) or entry.get(field) == "NONE" for field in required) or entry.get("editorial_impact") == "NOT_APPLICABLE":
                violations.append(f"Coverage parcial {entry.get('dimension_id')} requiere falta, impacto editorial, decisión de alcance y restricción propagada.")
    claims = data.get("critical_claims_assessment", {})
    if isinstance(claims, dict) and claims.get("status") == "IDENTIFIED" and not claims.get("claim_ids"):
        violations.append("Critical claims identificados requieren claim_ids concretos.")
    if isinstance(claims, dict) and claims.get("status") == "NONE_JUSTIFIED":
        if not claims.get("justification") or claims.get("editorial_impact") == "NONE":
            violations.append("La ausencia de claims críticos requiere justificación e impacto editorial explícitos.")

    # IR1-002: el mapa de criticidad debe referenciar claims declaradas en el pack.
    known_claim_ids = set()
    for entry in data.get("claims_candidates", []):
        if isinstance(entry, dict) and entry.get("item_id"):
            known_claim_ids.add(entry["item_id"])
    if isinstance(claims, dict):
        known_claim_ids.update(claims.get("claim_ids", []))

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
        for idx, claim in enumerate(data["claims"]):
            if not isinstance(claim, dict):
                violations.append(f"Entrada claim en indice {idx} debe ser un diccionario.")
                continue
            
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


def validate_work_research_dossier(
    data: Dict[str, Any],
    claims_ledger: Optional[Dict[str, Any]] = None,
    narrative_analyses: Optional[List[Dict[str, Any]]] = None,
) -> List[str]:
    """Valida referencias internas del WorkResearchDossier sin duplicar sus contratos fuente."""
    violations = validate_against_schema(data, "work_research_dossier")

    if claims_ledger is None or narrative_analyses is None:
        violations.append("WorkResearchDossier requiere ClaimsLedger y NarrativeHumanAnalysis para validar referencias canónicas.")
        return violations

    analyses_by_id = {
        analysis.get("analysis_id"): analysis for analysis in narrative_analyses
        if isinstance(analysis, dict) and analysis.get("analysis_id")
    }
    work = data.get("work") if isinstance(data.get("work"), dict) else {}
    declared_analysis_ids = {
        entry.get("analysis_id") for entry in data.get("analysis_references", [])
        if isinstance(entry, dict) and entry.get("analysis_id")
    }
    for reference in data.get("analysis_references", []):
        if not isinstance(reference, dict):
            continue
        analysis_id = reference.get("analysis_id")
        analysis = analyses_by_id.get(analysis_id)
        if analysis is None:
            violations.append(f"WorkResearchDossier.analysis_references referencia análisis inexistente: '{analysis_id}'.")
            continue
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
