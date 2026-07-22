"""Resolución portable de rutas para el runtime de gates."""

from pathlib import Path
import os


REPO_ROOT = Path(__file__).resolve().parents[2]


def expand_path(value: str | Path, *, base: Path | None = None) -> Path:
    """Expande entorno y ``~``; las rutas relativas se anclan de forma explícita."""
    expanded = Path(os.path.expandvars(os.path.expanduser(str(value))))
    return expanded if expanded.is_absolute() else (base or REPO_ROOT) / expanded


def output_root(value: str | Path | None = None) -> Path:
    return expand_path(value, base=REPO_ROOT) if value else REPO_ROOT / "output"


def gate_output_paths(gate_id: str, artifact_id: str, root: str | Path | None = None) -> tuple[Path, Path]:
    scope = "system" if artifact_id == "system" else artifact_id
    destination = output_root(root) / "gates" / scope
    return destination / f"{gate_id}.json", destination / f"{gate_id}.md"
