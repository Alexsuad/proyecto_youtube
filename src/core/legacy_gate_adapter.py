"""Adaptador estricto para el reporte textual heredado del Gate V."""

import re
from pathlib import Path

from src.core.status import GateStatus


_STATUS_LINE = re.compile(r"^\s*ESTADO_GLOBAL\s*:\s*(OK|WARN|FAIL)\s*$", re.IGNORECASE)


def parse_legacy_gate_v(path: Path) -> tuple[GateStatus | None, str | None]:
    if not path.exists():
        return None, "Reporte Gate V ausente"
    if not path.is_file() or not path.read_text(encoding="utf-8").strip():
        return None, "Reporte Gate V vacío o no regular"
    declarations = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = _STATUS_LINE.match(line)
        if match:
            declarations.append(match.group(1).upper())
    if len(declarations) != 1:
        return None, "Reporte Gate V ambiguo: debe contener exactamente una línea ESTADO_GLOBAL válida"
    return {"OK": GateStatus.PASS, "WARN": GateStatus.WARN, "FAIL": GateStatus.FAIL}[declarations[0]], None
