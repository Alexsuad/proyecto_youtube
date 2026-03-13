# File: src/scripts/gate0_auditoria.py
# ──────────────────────────────────────────────────────────────────────
# Propósito: Verificación real (determinista) del entorno antes de producir.
# Rol: Gate 0 — Auditoría de sistema. Reemplaza la "simulación" previa.
# ──────────────────────────────────────────────────────────────────────

import json
import os
from datetime import datetime
from pathlib import Path

# ─── Config ────────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).parent.parent.parent
CONFIG_PATH = REPO_ROOT / "config" / "local_settings.json"
OUTPUT_PATH = REPO_ROOT / "output" / "auditoria_sistema_v1.md"

REQUIRED_REPO_DIRS = [
    ".agent/rules",
    ".agent/skills",
    ".agent/workflows",
    "templates",
    "workspace",
    "config",
]

REQUIRED_RULES = [
    "00_reglas_globales.md",
    "01_formato_outputs.md",
    "02_reglas_notebooklm.md",
]

REQUIRED_VAULT_SUBDIRS = ["episodios", "index"]
INDEX_FILE = "index/episodes_index.json"
EMPTY_INDEX = {"episodes": [], "last_updated": None}


# ─── Helpers ────────────────────────────────────────────────────────────────────
def h2(title):
    return f"\n## {title}\n"


def check(label, ok, detail=""):
    icon = "✅" if ok else "❌"
    line = f"- {icon} {label}"
    if detail:
        line += f" — {detail}"
    return line


# ─── Auditoría ──────────────────────────────────────────────────────────────────
def run():
    lines = []
    severity = "OK"  # OK | WARN | FAIL
    created = []

    lines.append("# Auditoría de Sistema V1 (Gate 0)")
    lines.append(f"**Fecha:** {datetime.now().isoformat()}\n")

    # 1. Configuración
    lines.append(h2("1. Verificación de Configuración"))
    if not CONFIG_PATH.exists():
        lines.append(check("config/local_settings.json", False, "ARCHIVO NO ENCONTRADO"))
        severity = "FAIL"
        _write(lines, severity)
        return

    with open(CONFIG_PATH, encoding="utf-8") as f:
        config = json.load(f)

    vault_root_str = config.get("vault_root")
    channel_id = config.get("channel_id")

    lines.append(check("config/local_settings.json existe", True))
    lines.append(check("vault_root presente", bool(vault_root_str), vault_root_str or "MISSING"))
    lines.append(check("channel_id presente", bool(channel_id), channel_id or "MISSING"))

    if not vault_root_str or not channel_id:
        severity = "FAIL"
        _write(lines, severity)
        return

    vault_root = Path(vault_root_str)

    # 2. Repositorio
    lines.append(h2("2. Verificación del Repositorio"))
    for d in REQUIRED_REPO_DIRS:
        exists = (REPO_ROOT / d).is_dir()
        lines.append(check(d, exists))
        if not exists:
            severity = "FAIL"

    lines.append("\n**Reglas core:**")
    rules_dir = REPO_ROOT / ".agent" / "rules"
    for rule in REQUIRED_RULES:
        exists = (rules_dir / rule).is_file()
        lines.append(check(rule, exists))
        if not exists:
            severity = "FAIL"

    # 3. Vault
    lines.append(h2("3. Verificación y Auto-Creación del Vault"))
    channel_path = vault_root / channel_id

    if not vault_root.exists():
        lines.append(check(f"VAULT_ROOT ({vault_root})", False, "NO EXISTE — crear la carpeta manualmente"))
        severity = "FAIL"
        _write(lines, severity)
        return

    lines.append(check(f"VAULT_ROOT ({vault_root})", True))

    for subdir in [channel_id] + [f"{channel_id}/{s}" for s in REQUIRED_VAULT_SUBDIRS]:
        full_path = vault_root / subdir
        existed = full_path.exists()
        if not existed:
            full_path.mkdir(parents=True, exist_ok=True)
            created.append(str(full_path))
            lines.append(check(str(full_path), True, "AUTO-CREADO"))
        else:
            lines.append(check(str(full_path), True, "ya existía"))

    # Index JSON
    index_path = channel_path / INDEX_FILE
    if not index_path.exists():
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(EMPTY_INDEX, f, indent=2)
        created.append(str(index_path))
        lines.append(check("episodes_index.json", True, "AUTO-CREADO (vacío válido)"))
    else:
        lines.append(check("episodes_index.json", True, "ya existía"))

    # 4. Resumen de creaciones
    if created:
        lines.append(h2("4. Acciones Auto-ejecutadas en el Vault"))
        for c in created:
            lines.append(f"- Creado: `{c}`")
    else:
        lines.append(h2("4. Acciones Auto-ejecutadas en el Vault"))
        lines.append("- Ninguna. Todo ya existía.")

    _write(lines, severity)


def _write(lines, severity):
    lines.append(f"\n---\nESTADO_GLOBAL: {severity}")
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[gate0_auditoria] ESTADO_GLOBAL: {severity} — output: {OUTPUT_PATH}")


if __name__ == "__main__":
    run()
