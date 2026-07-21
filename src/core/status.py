"""
Módulo técnico de Estados Canónicos y Roles Funcionales
Proyecto YouTube — Sistema Agéntico Editorial
"""

from enum import Enum
from typing import Set, Dict, Any, Optional

class ArtifactStatus(str, Enum):
    DRAFT = "DRAFT"
    IN_REVIEW = "IN_REVIEW"
    EDITORIAL_SCRIPT_APPROVED = "EDITORIAL_SCRIPT_APPROVED"
    YOUTUBE_PRODUCTION_READY = "YOUTUBE_PRODUCTION_READY"
    YOUTUBE_READY = "YOUTUBE_READY"
    PUBLISHED = "PUBLISHED"
    DEPRECATED = "DEPRECATED"
    INVALIDATED = "INVALIDATED"


class GateStatus(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"


class ApprovalType(str, Enum):
    EDITORIAL_SCRIPT_APPROVAL = "EDITORIAL_SCRIPT_APPROVAL"
    HUMAN_PRODUCTION_APPROVAL = "HUMAN_PRODUCTION_APPROVAL"
    HUMAN_PUBLICATION_APPROVAL = "HUMAN_PUBLICATION_APPROVAL"
    TECHNICAL_VALIDATION = "TECHNICAL_VALIDATION"


class ApprovalDecision(str, Enum):
    APPROVED = "APPROVED"
    APPROVED_FOR_PRODUCTION = "APPROVED_FOR_PRODUCTION"
    APPROVED_FOR_PUBLICATION = "APPROVED_FOR_PUBLICATION"
    REQUEST_CHANGES = "REQUEST_CHANGES"
    REJECT = "REJECT"


class FunctionalRole(str, Enum):
    EDITORIAL_LEAD = "EDITORIAL_LEAD"
    EDITORIAL_REVIEWER = "EDITORIAL_REVIEWER"
    PRODUCTION_LEAD = "PRODUCTION_LEAD"
    PUBLICATION_LEAD = "PUBLICATION_LEAD"
    TECHNICAL_AUDITOR = "TECHNICAL_AUDITOR"
    SYSTEM_AUTOMATION = "SYSTEM_AUTOMATION"


# Mapeo de tipo de aprobación a roles autorizados por defecto
DEFAULT_ROLE_PERMISSIONS: Dict[ApprovalType, Set[FunctionalRole]] = {
    ApprovalType.EDITORIAL_SCRIPT_APPROVAL: {
        FunctionalRole.EDITORIAL_LEAD,
        FunctionalRole.EDITORIAL_REVIEWER,
    },
    ApprovalType.HUMAN_PRODUCTION_APPROVAL: {
        FunctionalRole.PRODUCTION_LEAD,
    },
    ApprovalType.HUMAN_PUBLICATION_APPROVAL: {
        FunctionalRole.PUBLICATION_LEAD,
    },
    ApprovalType.TECHNICAL_VALIDATION: {
        FunctionalRole.TECHNICAL_AUDITOR,
        FunctionalRole.SYSTEM_AUTOMATION,
    },
}

# Registro configurable de aprobadores autorizados
class ApproverRegistry:
    def __init__(self):
        self._registry = {} # dict of identity -> {"roles": set, "active": bool}

    def register_approver(self, identity: str, roles: Set[str], active: bool = True):
        self._registry[identity.strip()] = {
            "roles": {r.upper() for r in roles},
            "active": active
        }

    def is_valid_approver(self, identity: Optional[str], required_role: Optional[str] = None) -> bool:
        if not identity or not isinstance(identity, str):
            return False
        info = self._registry.get(identity.strip())
        if not info or not info["active"]:
            return False
        if required_role:
            return required_role.upper() in info["roles"]
        return True

    def clear(self):
        self._registry.clear()

APPROVER_REGISTRY = ApproverRegistry()

# Registrar aprobadores por defecto (utilizados en fixtures de pruebas y operaciones)
APPROVER_REGISTRY.register_approver("editor_jefe_01", {"EDITORIAL_LEAD", "EDITORIAL_REVIEWER"})
APPROVER_REGISTRY.register_approver("editor_jefe_editorial_01", {"EDITORIAL_LEAD"})
APPROVER_REGISTRY.register_approver("lead_produccion_01", {"PRODUCTION_LEAD"})
APPROVER_REGISTRY.register_approver("lead_produccion_nalex", {"PRODUCTION_LEAD"})
APPROVER_REGISTRY.register_approver("lead_publicacion_01", {"PUBLICATION_LEAD"})
APPROVER_REGISTRY.register_approver("technical_auditor_user", {"TECHNICAL_AUDITOR", "SYSTEM_AUTOMATION"})


def is_valid_artifact_status(status: str) -> bool:
    try:
        ArtifactStatus(status)
        return True
    except ValueError:
        return False


def is_valid_gate_status(status: str) -> bool:
    try:
        GateStatus(status)
        return True
    except ValueError:
        return False


def is_valid_approver_identity(approver: Optional[str]) -> bool:
    """
    Valida que la identidad del aprobador este registrada y activa en el registro.
    """
    return APPROVER_REGISTRY.is_valid_approver(approver)


# Matriz explícita de transiciones permitidas (curr -> targ)
ALLOWED_TRANSITIONS = {
    # Transiciones desde DRAFT
    (ArtifactStatus.DRAFT, ArtifactStatus.IN_REVIEW),
    (ArtifactStatus.DRAFT, ArtifactStatus.EDITORIAL_SCRIPT_APPROVED),

    # Transiciones desde IN_REVIEW
    (ArtifactStatus.IN_REVIEW, ArtifactStatus.DRAFT),
    (ArtifactStatus.IN_REVIEW, ArtifactStatus.EDITORIAL_SCRIPT_APPROVED),
    (ArtifactStatus.IN_REVIEW, ArtifactStatus.YOUTUBE_PRODUCTION_READY),
    (ArtifactStatus.IN_REVIEW, ArtifactStatus.YOUTUBE_READY),

    # Transiciones desde EDITORIAL_SCRIPT_APPROVED
    (ArtifactStatus.EDITORIAL_SCRIPT_APPROVED, ArtifactStatus.IN_REVIEW),
    (ArtifactStatus.EDITORIAL_SCRIPT_APPROVED, ArtifactStatus.DRAFT),
    (ArtifactStatus.EDITORIAL_SCRIPT_APPROVED, ArtifactStatus.YOUTUBE_PRODUCTION_READY),

    # Transiciones desde YOUTUBE_PRODUCTION_READY
    (ArtifactStatus.YOUTUBE_PRODUCTION_READY, ArtifactStatus.IN_REVIEW),
    (ArtifactStatus.YOUTUBE_PRODUCTION_READY, ArtifactStatus.DRAFT),
    (ArtifactStatus.YOUTUBE_PRODUCTION_READY, ArtifactStatus.YOUTUBE_READY),

    # Transiciones desde YOUTUBE_READY
    (ArtifactStatus.YOUTUBE_READY, ArtifactStatus.IN_REVIEW),
    (ArtifactStatus.YOUTUBE_READY, ArtifactStatus.DRAFT),
    (ArtifactStatus.YOUTUBE_READY, ArtifactStatus.PUBLISHED),
}

# Permitir transiciones a INVALIDATED, DEPRECATED y DRAFT desde cualquier estado
for status in ArtifactStatus:
    ALLOWED_TRANSITIONS.add((status, ArtifactStatus.INVALIDATED))
    ALLOWED_TRANSITIONS.add((status, ArtifactStatus.DEPRECATED))
    ALLOWED_TRANSITIONS.add((status, ArtifactStatus.DRAFT))


def validate_status_transition(
    current_status: Any,
    target_status: Any,
    approval_type: Optional[Any] = None,
    approval_decision: Optional[Any] = None,
    has_final_audiovisual_assets: bool = False,
) -> bool:
    """
    Valida si una transición de estado de artefacto es permitida por la matriz y las reglas del sistema.
    """
    try:
        curr = ArtifactStatus(current_status)
        targ = ArtifactStatus(target_status)
    except ValueError:
        return False

    if curr == targ:
        return True

    # 1. Matriz explícita de transiciones permitidas (rechazar por defecto)
    if (curr, targ) not in ALLOWED_TRANSITIONS:
        return False

    # 2. Comprobar reglas de decisión específicas por tipo de aprobación
    if approval_type is not None:
        try:
            app_type = ApprovalType(approval_type)
        except ValueError:
            return False

        # EditorialScriptApproval solo puede usar decision=APPROVED
        if app_type == ApprovalType.EDITORIAL_SCRIPT_APPROVAL:
            if approval_decision != ApprovalDecision.APPROVED:
                return False
            if targ != ArtifactStatus.EDITORIAL_SCRIPT_APPROVED:
                return False

        # ProductionApproval solo puede alcanzar YOUTUBE_PRODUCTION_READY
        if app_type == ApprovalType.HUMAN_PRODUCTION_APPROVAL:
            if approval_decision != ApprovalDecision.APPROVED_FOR_PRODUCTION:
                return False
            if targ != ArtifactStatus.YOUTUBE_PRODUCTION_READY:
                return False

        # PublicationApproval solo puede alcanzar YOUTUBE_READY
        if app_type == ApprovalType.HUMAN_PUBLICATION_APPROVAL:
            if approval_decision != ApprovalDecision.APPROVED_FOR_PUBLICATION:
                return False
            if targ != ArtifactStatus.YOUTUBE_READY:
                return False

    # 3. YOUTUBE_READY requiere HumanPublicationApproval y activos audiovisuales finales
    if targ == ArtifactStatus.YOUTUBE_READY:
        if (
            approval_type != ApprovalType.HUMAN_PUBLICATION_APPROVAL
            or approval_decision != ApprovalDecision.APPROVED_FOR_PUBLICATION
            or not has_final_audiovisual_assets
        ):
            return False

    # 4. YOUTUBE_PRODUCTION_READY requiere HumanProductionApproval
    if targ == ArtifactStatus.YOUTUBE_PRODUCTION_READY:
        if (
            approval_type != ApprovalType.HUMAN_PRODUCTION_APPROVAL
            or approval_decision != ApprovalDecision.APPROVED_FOR_PRODUCTION
        ):
            return False

    # 5. EDITORIAL_SCRIPT_APPROVED requiere EditorialScriptApproval
    if targ == ArtifactStatus.EDITORIAL_SCRIPT_APPROVED:
        if (
            approval_type != ApprovalType.EDITORIAL_SCRIPT_APPROVAL
            or approval_decision != ApprovalDecision.APPROVED
        ):
            return False

    # 6. PUBLISHED solo puede partir de YOUTUBE_READY
    if targ == ArtifactStatus.PUBLISHED:
        if curr != ArtifactStatus.YOUTUBE_READY:
            return False

    return True
