"""
Módulo de Versionado, Manifiestos y Cálculo de Checksums
Proyecto YouTube — Sistema Agéntico Editorial
"""

import hashlib
import json
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone


def compute_checksum(content: Any) -> str:
    """
    Calcula el checksum SHA-256 canónico de un string, bytes o estructura dict/list.
    """
    if isinstance(content, bytes):
        raw_bytes = content
    elif isinstance(content, str):
        raw_bytes = content.encode("utf-8")
    elif isinstance(content, (dict, list)):
        raw_bytes = json.dumps(content, sort_keys=True, ensure_ascii=False).encode("utf-8")
    else:
        raw_bytes = str(content).encode("utf-8")
    
    return hashlib.sha256(raw_bytes).hexdigest()


@dataclass
class VersionEntry:
    artifact_id: str
    version: str
    checksum: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    created_by_role: str = "SYSTEM"
    parent_version: Optional[str] = None
    change_summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class VersionManifest:
    """
    Manifiesto trazable de versiones para un artefacto o conjunto de artefactos.
    Impide la sobrescritura silenciosa de una versión existente.
    """

    def __init__(self, artifact_id: str):
        self.artifact_id = artifact_id
        self.versions: Dict[str, VersionEntry] = {}

    def register_version(
        self,
        version: str,
        content_or_checksum: Any,
        created_by_role: str = "SYSTEM",
        parent_version: Optional[str] = None,
        change_summary: str = "",
    ) -> VersionEntry:
        if not version or not isinstance(version, str) or not version.strip():
            raise ValueError(f"No se permite registrar una version vacia para el artefacto '{self.artifact_id}'.")

        checksum = (
            content_or_checksum
            if isinstance(content_or_checksum, str) and len(content_or_checksum) == 64 and all(c in "0123456789abcdefABCDEF" for c in content_or_checksum)
            else compute_checksum(content_or_checksum)
        )

        # Regla: Prevenir sobrescritura silenciosa de una version
        if version in self.versions:
            existing = self.versions[version]
            if existing.checksum != checksum:
                raise ValueError(
                    f"Sobrescritura silenciosa rechazada: La version '{version}' del artefacto '{self.artifact_id}' "
                    f"ya existe con checksum '{existing.checksum}', pero se intento registrar un checksum distinto '{checksum}'."
                )
            return existing

        entry = VersionEntry(
            artifact_id=self.artifact_id,
            version=version.strip(),
            checksum=checksum,
            created_by_role=created_by_role,
            parent_version=parent_version,
            change_summary=change_summary,
        )
        self.versions[version] = entry
        return entry

    def get_version(self, version: str) -> Optional[VersionEntry]:
        return self.versions.get(version)

    def verify_version_integrity(self, version: str, content: Any) -> bool:
        entry = self.get_version(version)
        if not entry:
            return False
        return entry.checksum == compute_checksum(content)
