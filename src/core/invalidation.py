"""
Módulo del Motor de Invalidación en Cascada y Trazabilidad
Proyecto YouTube — Sistema Agéntico Editorial
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timezone


@dataclass
class InvalidationRecord:
    invalidation_id: str
    target_artifact_id: str
    target_version: str
    reason: str
    invalidated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    invalidated_by_role: str = "SYSTEM_AUTOMATION"
    trigger_artifact_id: Optional[str] = None
    trigger_version: Optional[str] = None
    affected_dependent_artifacts: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class InvalidationEngine:
    """
    Motor de invalidación que rastrea dependencias y propaga la invalidación
    de aprobaciones y artefactos derivados cuando un insumo aguas arriba cambia.
    """

    def __init__(self, registry=None):
        self.invalidation_log: List[InvalidationRecord] = []
        self.registry = registry
        self.dependencies: Dict[str, Set[str]] = {} if registry is None else {key: set(value) for key, value in registry.data.get("dependencies", {}).items()}

    def register_dependency(self, parent_id: str, child_id: str):
        """
        Registra que child_id depende de parent_id. Si parent_id se invalida,
        child_id también debe invalidarse.
        """
        if parent_id not in self.dependencies:
            self.dependencies[parent_id] = set()
        self.dependencies[parent_id].add(child_id)
        if self.registry:
            self.registry.add_dependency(parent_id, child_id)

    def classify_profile_change(self, change_type: str) -> str:
        mapping = {"NO_IMPACT": "NO_IMPACT", "PARTIAL_INVALIDATION": "PARTIAL_INVALIDATION", "FULL_INVALIDATION": "FULL_INVALIDATION"}
        if change_type not in mapping: raise ValueError("Clasificación de cambio inválida")
        return mapping[change_type]

    def invalidate_profile_change(self, profile_id: str, version: str, classification: str, by_role: str, affected=None):
        classification = self.classify_profile_change(classification)
        if classification == "NO_IMPACT": return []
        if classification == "PARTIAL_INVALIDATION":
            allowed = set(self.dependencies.get(profile_id, set()))
            return [self.invalidate_artifact(item, version, "Cambio parcial de perfil", by_role) for item in (affected or []) if item in allowed]
        self.invalidate_artifact(profile_id, version, "Cambio completo de perfil", by_role)
        return list(self.invalidation_log)

    def check_approval_validity(
        self,
        approval_checksum: str,
        current_artifact_content_or_checksum: Any,
    ) -> bool:
        """
        Una aprobación queda estrictamente ligada al checksum del artefacto.
        Cualquier cambio posterior en el artefacto invalida la aprobación.
        """
        from src.core.version_manifest import compute_checksum

        current_checksum = (
            current_artifact_content_or_checksum
            if isinstance(current_artifact_content_or_checksum, str)
            and len(current_artifact_content_or_checksum) == 64
            else compute_checksum(current_artifact_content_or_checksum)
        )
        return approval_checksum == current_checksum

    def can_candidate_learning_modify_profile(self, learning_status: str) -> bool:
        """
        Regla: Un aprendizaje en estado CANDIDATE NO puede modificar el perfil activo.
        Solo aprendizajes en estado APPROVED por un rol editorial autorizado pueden modificar el perfil.
        """
        if not learning_status:
            return False
        status_clean = learning_status.strip().upper()
        if status_clean == "CANDIDATE":
            return False
        return status_clean in {"APPROVED", "INTEGRATED"}

    def invalidate_artifact(
        self,
        artifact_id: str,
        version: str,
        reason: str,
        by_role: str,
        trigger_artifact_id: Optional[str] = None,
        trigger_version: Optional[str] = None,
        dependents: Optional[List[str]] = None,
        visited: Optional[Set[str]] = None,
    ) -> InvalidationRecord:
        if visited is None:
            visited = set()

        if artifact_id in visited:
            # Para evitar loops en ciclos, retornamos un record de aviso o skip
            # En la recursión esto corta el ciclo. Devolvemos el record ya existente.
            existing = [r for r in self.invalidation_log if r.target_artifact_id == artifact_id]
            if existing:
                return existing[0]

        visited.add(artifact_id)

        # Si se pasan dependientes directamente, los registramos
        if dependents:
            for dep in dependents:
                self.register_dependency(artifact_id, dep)

        # Calculamos dependientes afectados
        all_deps = list(self.dependencies.get(artifact_id, set()))

        record = InvalidationRecord(
            invalidation_id=f"INV-{artifact_id}-{version}-{len(self.invalidation_log) + 1}",
            target_artifact_id=artifact_id,
            target_version=version,
            reason=reason,
            invalidated_by_role=by_role,
            trigger_artifact_id=trigger_artifact_id,
            trigger_version=trigger_version,
            affected_dependent_artifacts=all_deps,
        )
        self.invalidation_log.append(record)

        # Propagar recursivamente a todos los dependientes
        for dep_id in all_deps:
            if dep_id not in visited:
                self.invalidate_artifact(
                    artifact_id=dep_id,
                    version=version,
                    reason=f"Invalidacion en cascada debido a la invalidacion de {artifact_id}",
                    by_role=by_role,
                    trigger_artifact_id=artifact_id,
                    trigger_version=version,
                    visited=visited,
                )

        return record
