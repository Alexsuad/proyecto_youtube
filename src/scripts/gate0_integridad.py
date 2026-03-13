# File: src/scripts/gate0_integridad.py
# ──────────────────────────────────────────────────────────────────────
# Propósito: Verificar si hay episodios anteriores incompletos en el Vault.
# Rol: Gate 0 — Control de integridad del pipeline.
# ──────────────────────────────────────────────────────────────────────

import json
import os
from datetime import datetime
from pathlib import Path

# ─── Config ────────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).parent.parent.parent
CONFIG_PATH = REPO_ROOT / "config" / "local_settings.json"
OUTPUT_PATH = REPO_ROOT / "output" / "control_integridad_pipeline.md"

ENTREGABLES_FINALES = [
    "06_guion_longform.md",
    "08_shorts.md",
    "09_packaging.md",
    "10_seo.md",
]


def run():
    lines = []
    severity = "OK"

    lines.append("# Control de Integridad del Pipeline (Gate 0)")
    lines.append(f"**Fecha:** {datetime.now().isoformat()}\n")

    if not CONFIG_PATH.exists():
        lines.append("❌ config/local_settings.json no encontrado — ejecutar gate0_auditoria primero.")
        _write(lines, "FAIL")
        return

    with open(CONFIG_PATH, encoding="utf-8") as f:
        config = json.load(f)

    vault_root = Path(config.get("vault_root", ""))
    channel_id = config.get("channel_id", "")
    episodes_path = vault_root / channel_id / "episodios"
    index_path = vault_root / channel_id / "index" / "episodes_index.json"

    # ── Leer índice ──
    lines.append("## 1. Índice de Episodios")
    if not index_path.exists():
        lines.append("- ⚠️ episodes_index.json no encontrado.")
        severity = "WARN"
    else:
        with open(index_path, encoding="utf-8") as f:
            index = json.load(f)
        episodes = index.get("episodes", [])
        lines.append(f"- Episodios registrados: {len(episodes)}")

        in_progress = [e for e in episodes if e.get("estado") == "en_progreso"]
        if in_progress:
            lines.append(f"\n⚠️ Episodios con estado 'en_progreso': {len(in_progress)}")
            severity = "WARN"
            for ep in in_progress:
                lines.append(f"  - `{ep.get('ep_id')}` — ruta: `{ep.get('ep_path', 'desconocida')}`")

    # ── Escanear carpetas físicas ──
    lines.append("\n## 2. Escaneo de Carpetas de Episodios en Vault")
    if not episodes_path.exists():
        lines.append("- Carpeta episodios/ no existe aún. (Normal en primer uso)")
        _write(lines, severity)
        return

    ep_dirs = [d for d in episodes_path.iterdir() if d.is_dir()]
    if not ep_dirs:
        lines.append("- No hay episodios en el Vault. Pipeline limpio. ✅")
    else:
        for ep_dir in sorted(ep_dirs):
            present = [f for f in ENTREGABLES_FINALES if (ep_dir / f).exists()]
            missing = [f for f in ENTREGABLES_FINALES if f not in present]
            complete = len(missing) == 0
            icon = "✅" if complete else "⚠️"
            lines.append(f"\n{icon} **{ep_dir.name}** — {len(present)}/{len(ENTREGABLES_FINALES)} entregables")
            if missing:
                severity = "WARN"
                for m in missing:
                    lines.append(f"  - ❌ Falta: `{m}`")

    _write(lines, severity)


def _write(lines, severity):
    lines.append(f"\n---\nESTADO_GLOBAL: {severity}")
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[gate0_integridad] ESTADO_GLOBAL: {severity} — output: {OUTPUT_PATH}")


if __name__ == "__main__":
    run()
