"""
Módulo del Contrato Canónico GateResult y Mapeo Estricto de Exit Codes
Proyecto YouTube — Sistema Agéntico Editorial
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from src.core.status import GateStatus, is_valid_gate_status

# Mapeo determinista e inmutable de GateStatus a Exit Code
EXIT_CODE_MAP: Dict[GateStatus, int] = {
    GateStatus.PASS: 0,
    GateStatus.WARN: 0,
    GateStatus.FAIL: 1,
    GateStatus.BLOCKED: 2,
}

EXIT_CODE_ERROR = 3


@dataclass
class GateResult:
    gate_id: str
    artifact_id: str
    artifact_version: str
    status: GateStatus
    summary: str
    violations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    evidence: Dict[str, Any] = field(default_factory=dict)
    checked_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    checker_version: str = "1.0.0"
    exit_code: int = 0

    def __post_init__(self):
        # Convertir string a GateStatus si es necesario
        if isinstance(self.status, str):
            if not is_valid_gate_status(self.status):
                raise ValueError(f"Estado de gate invalido: '{self.status}'. Debe ser PASS, WARN, FAIL o BLOCKED.")
            self.status = GateStatus(self.status)

        # Regla estricta: exit_code debe corresponder exactamente al status
        expected_exit_code = EXIT_CODE_MAP.get(self.status, EXIT_CODE_ERROR)
        self.exit_code = expected_exit_code

        # Regla: Si hay violaciones y el estado se habia marcado como PASS o WARN, se fuerza a FAIL/BLOCKED
        if self.violations and self.status in {GateStatus.PASS, GateStatus.WARN}:
            raise ValueError(
                f"Contradiccion detectada: Gate '{self.gate_id}' contiene {len(self.violations)} violaciones "
                f"pero el estado declarado es {self.status.value}. No se permiten falsos PASS/WARN."
            )

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GateResult":
        # Prohibido decidir estado usando busqueda por substring en summary o texto libre
        status_raw = data.get("status")
        if not status_raw:
            raise ValueError("Campo 'status' es obligatorio en GateResult y no puede inferirse por texto libre.")
        
        return cls(
            gate_id=data["gate_id"],
            artifact_id=data["artifact_id"],
            artifact_version=data["artifact_version"],
            status=GateStatus(status_raw),
            summary=data.get("summary", ""),
            violations=data.get("violations", []),
            warnings=data.get("warnings", []),
            evidence=data.get("evidence", {}),
            checked_at=data.get("checked_at", datetime.now(timezone.utc).isoformat()),
            checker_version=data.get("checker_version", "1.0.0"),
            exit_code=data.get("exit_code", EXIT_CODE_MAP.get(GateStatus(status_raw), EXIT_CODE_ERROR)),
        )
