"""Registro de decisiones materiales y vista derivada de documentación legacy.

Este módulo implementa el mecanismo mínimo del PLAN 008, Misión 1:
- representación nativa y pequeña de decisiones materiales con estado y sucesión;
- una única relación canónica de sucesión (`superseded_by`), derivando la inversa
  solo cuando se necesita (no se duplica información);
- vista per-file derivada para documentación legacy, sin constituir una segunda
  fuente de verdad (la fuente canónica es el registro JSON).

Invariantes protegidas:
- la autoridad debe pertenecer al vocabulario canónico de dominios de gobernanza
  definido por el producto (ver AUTHORITIES y su test de deriva contra
  config/runtime_contamination_policy.json);
- la evidencia es obligatoria y cada referencia local debe resolverse en el repo;
- el grafo de sucesión no admite autorreferencias, sucesores inexistentes ni ciclos;
- los archivos legacy indexados son históricos/no canónicos y nunca ejecutables.
"""

from __future__ import annotations

import json
from pathlib import Path

from src.core.contract_validation import validate_against_schema

STATES = ("VIGENTE", "HISTORICA", "SUSTITUIDA")
LEGACY_FILE_STATES = ("HISTORICA", "SUSTITUIDA")
DERIVED_VIEW_REF = "docs/legacy/LEGACY_PER_FILE_VIEW.md"

# Vocabulario canónico de autoridades de gobernanza del producto. Fuentes:
# - config/runtime_contamination_policy.json -> neutral_terms;
# - src/core/capability_governance.py -> DOMAINS.
AUTHORITIES = frozenset(
    {
        "CHANNEL_INTELLIGENCE",
        "SCRIPT_PRODUCT",
        "YOUTUBE_ADAPTATION",
        "TECHNICAL_GOVERNANCE",
        "INFRASTRUCTURE_GOVERNANCE",
    }
)

VIEW_NOTICE = (
    "> Documento generado de forma determinista por `src/scripts/check_material_decisions.py --render`.\n"
    "> NO editar manualmente. La fuente canónica es `docs/legacy/material_decision_registry.json`;\n"
    "> esta vista es una proyección derivada y no una segunda fuente de verdad.\n"
)


def load_registry(path: str | Path) -> dict:
    """Carga el registro canónico desde disco."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _superseded_by(decision: dict) -> str | None:
    return decision.get("superseded_by")


def validate_registry(data: dict) -> list[str]:
    """Valida el registro contra su schema y sus reglas de integridad."""
    violations = []
    for entry in data.get("legacy_files", []) if isinstance(data, dict) else []:
        if isinstance(entry, dict) and entry.get("estado") == "VIGENTE":
            violations.append(
                f"{entry.get('file_path', '<sin ruta>')}: un archivo legacy no puede tener estado VIGENTE"
            )
    schema_violations = validate_against_schema(data, "material_decision_registry")
    if schema_violations:
        return violations + schema_violations

    decisions = {d["decision_id"]: d for d in data["decisions"]}
    if len(decisions) != len(data["decisions"]):
        violations.append("decision_id duplicados en decisions")

    for decision in data["decisions"]:
        decision_id = decision["decision_id"]
        if decision["state"] not in STATES:
            violations.append(f"{decision_id}: estado inválido {decision['state']!r}")
        if decision.get("authority") not in AUTHORITIES:
            violations.append(f"{decision_id}: autoridad no canónica {decision.get('authority')!r}")
        if not decision.get("evidence_refs"):
            violations.append(f"{decision_id}: evidence_refs vacío o ausente")
        for ref in decision.get("evidence_refs", []):
            if _is_derived_view_ref(ref):
                violations.append(
                    f"{decision_id}: evidencia derivada no puede utilizarse como evidencia primaria: {ref}"
                )

        successor = _superseded_by(decision)
        if successor is not None:
            if successor == decision_id:
                violations.append(f"{decision_id}: referencia a sí mismo en superseded_by")
            elif successor not in decisions:
                violations.append(f"{decision_id}: superseded_by refiere a id inexistente {successor!r}")
            elif decisions[successor]["state"] == "HISTORICA":
                violations.append(f"{decision_id}: superseded_by refiere a decisión HISTORICA {successor!r}")
        if decision["state"] == "VIGENTE" and successor is not None:
            violations.append(f"{decision_id}: VIGENTE no puede tener superseded_by")
        if decision["state"] == "SUSTITUIDA" and successor is None:
            violations.append(f"{decision_id}: SUSTITUIDA requiere superseded_by")
        if decision["state"] == "HISTORICA" and successor is not None:
            violations.append(f"{decision_id}: HISTORICA no puede tener sucesión")

    _check_cycles(data["decisions"], violations)

    vigentes = {}
    for decision in data["decisions"]:
        if decision["state"] == "VIGENTE":
            vigentes.setdefault(decision["subject_ref"], []).append(decision["decision_id"])
    for subject_ref, ids in vigentes.items():
        if len(ids) > 1:
            violations.append(f"más de una decisión VIGENTE para subject_ref {subject_ref!r}: {ids}")

    file_paths = [entry["file_path"] for entry in data["legacy_files"]]
    if len(file_paths) != len(set(file_paths)):
        violations.append("file_path duplicados en legacy_files")
    for entry in data["legacy_files"]:
        if entry["decision_id"] not in decisions:
            violations.append(f"{entry['file_path']}: decision_id inexistente {entry['decision_id']!r}")
        if entry["estado"] not in LEGACY_FILE_STATES:
            violations.append(f"{entry['file_path']}: estado inválido {entry['estado']!r}")
        if entry.get("ejecutable") is not False:
            violations.append(f"{entry['file_path']}: archivo legacy no puede ser ejecutable")

    return violations


def _check_cycles(decisions: list[dict], violations: list[str]) -> None:
    by_id = {d["decision_id"]: d for d in decisions}
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {decision_id: WHITE for decision_id in by_id}

    def visit(decision_id: str) -> None:
        color[decision_id] = GRAY
        successor = _superseded_by(by_id[decision_id])
        if successor is not None and successor in by_id:
            if color[successor] == GRAY:
                violations.append(f"ciclo de sucesión detectado en {successor}")
                return
            if color[successor] == WHITE:
                visit(successor)
        color[decision_id] = BLACK

    for decision_id in by_id:
        if color[decision_id] == WHITE:
            visit(decision_id)


def _resolve(root: Path, ref: str) -> Path:
    root = root.resolve()
    candidate = Path(ref)
    return (candidate if candidate.is_absolute() else root / candidate).resolve()


def _is_within_root(root: Path, target: Path) -> bool:
    """Indica si target permanece dentro de root después de resolver symlinks."""
    root = root.resolve()
    target = target.resolve()
    return target == root or root in target.parents


def _is_derived_view_ref(ref: str) -> bool:
    """Detecta la vista canónica derivada aunque se exprese con separadores Windows."""
    normalized = str(ref).replace("\\", "/").rstrip("/")
    return normalized == DERIVED_VIEW_REF or normalized.endswith(f"/{DERIVED_VIEW_REF}")


def validate_local_refs(data: dict, root: str | Path) -> list[str]:
    """Verifica que las referencias locales del registro existan físicamente.

    Cubre: archivos legacy indexados, referencias de evidencia, consumidores
    activos y autoridades/sucesores documentales declarados como rutas locales.
    Las rutas son relativas a la raíz del repositorio.
    """
    violations = []
    root_path = Path(root).resolve()

    for entry in data["legacy_files"]:
        target = _resolve(root_path, entry["file_path"])
        if not _is_within_root(root_path, target):
            violations.append(f"archivo legacy fuera de REPO_ROOT: {entry['file_path']}")
        elif not target.is_file():
            violations.append(f"archivo legacy inexistente: {entry['file_path']}")

    for decision in data["decisions"]:
        for ref in decision.get("evidence_refs", []):
            target = _resolve(root_path, ref)
            if not _is_within_root(root_path, target):
                violations.append(f"{decision['decision_id']}: evidencia fuera de REPO_ROOT: {ref}")
            elif not target.is_file():
                violations.append(f"{decision['decision_id']}: evidencia inexistente: {ref}")

    for entry in data["legacy_files"]:
        consumer = entry.get("consumer_activo")
        if consumer is not None:
            target = _resolve(root_path, consumer)
            if not _is_within_root(root_path, target):
                violations.append(f"{entry['file_path']}: consumer activo fuera de REPO_ROOT: {consumer}")
            elif not target.is_file():
                violations.append(f"{entry['file_path']}: consumer activo inexistente: {consumer}")
        successor = entry.get("autoridad_sucesor")
        if successor is not None:
            target = _resolve(root_path, successor)
            if not _is_within_root(root_path, target):
                violations.append(f"{entry['file_path']}: autoridad/sucesor fuera de REPO_ROOT: {successor}")
            elif not target.is_file() and not target.is_dir():
                violations.append(f"{entry['file_path']}: autoridad/sucesor inexistente: {successor}")

    return violations


def render_view(data: dict) -> str:
    """Renderiza la vista per-file derivada a partir del registro canónico."""
    lines: list[str] = [
        "# Vista per-file de documentación legacy (derivada)",
        "",
        VIEW_NOTICE.rstrip(),
        "",
        "## Decisiones materiales",
        "",
        "| Id | Estado | Autoridad | Sujeto |",
        "|---|---|---|---|",
    ]
    for decision in data["decisions"]:
        lines.append(
            f"| {decision['decision_id']} | {decision['state']} | {decision['authority']} "
            f"| {decision['subject_ref']} |"
        )
    lines += ["", "## Sucesión de decisiones", ""]
    lines.append("| Id | Sustituido por |")
    lines.append("|---|---|")
    for decision in data["decisions"]:
        lines.append(f"| {decision['decision_id']} | {_superseded_by(decision) or '—'} |")
    lines += ["", "## Vista per-file", ""]
    lines.append(
        "| Archivo | Estado | Disposición | Sucesor | Consumidor activo | Duplicación material | Ejecutable |"
    )
    lines.append("|---|---|---|---|---|---|---|")
    for entry in data["legacy_files"]:
        lines.append(
            f"| {entry['file_path']} | {entry['estado']} | {entry['disposicion']} "
            f"| {entry['autoridad_sucesor'] or '—'} | {entry['consumer_activo'] or '—'} "
            f"| {entry['duplicacion_material'] or '—'} | {'sí' if entry['ejecutable'] else 'no'} |"
        )
    lines.append("")
    return "\n".join(lines)


def expected_view_path() -> Path:
    """Ruta de la vista derivada comprometida en el repositorio."""
    return Path(__file__).resolve().parents[2] / "docs" / "legacy" / "LEGACY_PER_FILE_VIEW.md"


def registry_path() -> Path:
    """Ruta del registro canónico de decisiones materiales."""
    return Path(__file__).resolve().parents[2] / "docs" / "legacy" / "material_decision_registry.json"
