"""Gate determinista contra consumo disperso de identidad editorial B3-I3."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable, Sequence


ROOT = Path(__file__).resolve().parents[2]
CONSUMERS = (
    ".agent/rules/00_reglas_globales.md",
    ".agent/skills/skill_crear_brief_episodio.md",
    ".agent/skills/skill_guion_longform.md",
    ".agent/skills/skill_qa_editorial.md",
    ".agent/skills/skill_extraer_voice_learnings.md",
    ".agent/skills/skill_mapa_eventos_y_outline.md",
    ".agent/workflows/piloto-outline.md",
    ".agent/workflows/01_pipeline_episodio.md",
)
FORBIDDEN_HISTORICAL_PATHS = frozenset(
    {
        "workspace/01_canal_identidad.md",
        "workspace/02_reglas_editoriales.md",
        "workspace/03_formato_longform.md",
        "workspace/04_politica_spoilers.md",
        "workspace/05_estilo_y_voz.md",
        "workspace/05c_voice_profile.md",
    }
)
REFERENCE = re.compile(
    r"(?<![A-Za-z0-9_.-])(?P<reference>(?:(?:[A-Za-z0-9_.-]+)[\\/])+(?:[A-Za-z0-9_.-]+))",
    re.IGNORECASE,
)


def normalize_reference(reference: str) -> str | None:
    """Normalize a textual repository-relative reference without filesystem access."""
    parts: list[str] = []
    for segment in reference.replace("\\", "/").split("/"):
        if segment in ("", "."):
            continue
        if segment == "..":
            if not parts:
                return None
            parts.pop()
            continue
        parts.append(segment.casefold())
    return "/".join(parts)


def find_violations(paths: Iterable[Path]) -> list[str]:
    """Return deterministic violations for normalized historic editorial references."""
    violations: list[str] = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for match in REFERENCE.finditer(text):
            reference = match.group("reference")
            normalized = normalize_reference(reference)
            if normalized in FORBIDDEN_HISTORICAL_PATHS:
                violations.append(f"{path}: consumo histórico prohibido: {reference} -> {normalized}")
    return violations


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", action="append", help="consumer path to check; repeatable")
    args = parser.parse_args(argv)
    paths = [Path(value).resolve() for value in args.path] if args.path else [ROOT / item for item in CONSUMERS]
    violations = find_violations(paths)
    if violations:
        print("FAIL")
        print("\n".join(violations))
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
