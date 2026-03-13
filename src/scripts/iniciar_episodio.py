# File: src/scripts/iniciar_episodio.py
# ──────────────────────────────────────────────────────────────────────
# Propósito: Crear la carpeta del episodio en el Vault y registrarlo en el índice.
# Rol: Primer paso obligatorio del pipeline. Garantiza anti-sobrescritura.
# ──────────────────────────────────────────────────────────────────────
#
# Uso:
#   python src/scripts/iniciar_episodio.py --num 1 --slug abandono_emocional
#
# Resultado:
#   - Crea: C:\YT_VAULT\MasAllaDelGuion\episodios\ep_0001_abandono_emocional\
#   - Registra el episodio en episodes_index.json con estado "en_progreso"
#   - Imprime EP_PATH en stdout (para que el pipeline lo capture)
# ──────────────────────────────────────────────────────────────────────

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

# ─── Constantes ────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).parent.parent.parent
CONFIG_PATH = REPO_ROOT / "config" / "local_settings.json"
INDEX_FILENAME = "episodes_index.json"
SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_]{0,49}$")


# ─── Helpers ────────────────────────────────────────────────────────────────────
def load_config() -> dict:
    """Carga y valida la configuración desde local_settings.json."""
    if not CONFIG_PATH.exists():
        _abort(f"No se encontró config en: {CONFIG_PATH}\n"
               "Ejecuta gate0_auditoria.py primero.")
    with open(CONFIG_PATH, encoding="utf-8") as f:
        cfg = json.load(f)
    for key in ("vault_root", "channel_id"):
        if not cfg.get(key):
            _abort(f"Clave '{key}' faltante o vacía en local_settings.json")
    return cfg


def load_index(index_path: Path) -> dict:
    """Carga el índice de episodios. Crea uno vacío si no existe."""
    if not index_path.exists():
        return {"episodes": [], "last_updated": None}
    with open(index_path, encoding="utf-8") as f:
        return json.load(f)


def save_index(index_path: Path, index: dict) -> None:
    """Guarda el índice con timestamp actualizado."""
    index["last_updated"] = datetime.now().isoformat()
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)


def _abort(msg: str) -> None:
    print(f"\n🔴 ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def _ok(msg: str) -> None:
    print(f"✅ {msg}")


# ─── Validaciones ───────────────────────────────────────────────────────────────
def validate_slug(slug: str) -> str:
    """Normaliza y valida el slug del episodio."""
    slug = slug.strip().lower().replace(" ", "_").replace("-", "_")
    if not SLUG_PATTERN.match(slug):
        _abort(
            f"Slug inválido: '{slug}'\n"
            "Solo letras minúsculas, números y guiones bajos. "
            "Mínimo 1 carácter, máximo 50."
        )
    return slug


def check_no_in_progress(episodes: list) -> None:
    """Verifica que no haya otro episodio en progreso."""
    in_progress = [e for e in episodes if e.get("estado") == "en_progreso"]
    if in_progress:
        ep_ids = ", ".join(e.get("ep_id", "?") for e in in_progress)
        _abort(
            f"Hay episodio(s) en progreso sin cerrar: {ep_ids}\n"
            "Ciérralos con cerrar_episodio.py antes de iniciar uno nuevo.\n"
            "Esto evita sobrescrituras accidentales."
        )


def check_ep_id_not_duplicate(episodes: list, ep_id: str) -> None:
    """Verifica que el ep_id no esté ya en el índice."""
    existing = [e for e in episodes if e.get("ep_id") == ep_id]
    if existing:
        _abort(
            f"El episodio '{ep_id}' ya está registrado en el índice.\n"
            "Usa un número de episodio diferente."
        )


# ─── Lógica principal ────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Iniciar un nuevo episodio en el Vault."
    )
    parser.add_argument(
        "--num", type=int, required=True,
        help="Número del episodio (ej: 1)"
    )
    parser.add_argument(
        "--slug", type=str, required=True,
        help="Slug descriptivo del episodio (ej: abandono_emocional)"
    )
    args = parser.parse_args()

    # ── Cargar config ──
    cfg = load_config()
    vault_root = Path(cfg["vault_root"])
    channel_id = cfg["channel_id"]

    # ── Construir paths ──
    slug = validate_slug(args.slug)
    ep_id = f"ep_{args.num:04d}"
    ep_folder_name = f"{ep_id}_{slug}"
    ep_path = vault_root / channel_id / "episodios" / ep_folder_name
    index_path = vault_root / channel_id / "index" / INDEX_FILENAME

    print(f"\n🎬 Iniciando episodio: {ep_folder_name}")
    print(f"   Ruta destino: {ep_path}\n")

    # ── Verificar Vault ──
    channel_path = vault_root / channel_id
    if not channel_path.exists():
        _abort(
            f"La carpeta del canal no existe: {channel_path}\n"
            "Ejecuta gate0_auditoria.py para crearla automáticamente."
        )

    # ── Cargar índice ──
    index = load_index(index_path)
    episodes = index.get("episodes", [])

    # ── Validaciones de seguridad ──
    check_no_in_progress(episodes)
    check_ep_id_not_duplicate(episodes, ep_id)

    # ── Anti-sobrescritura: verificar que la carpeta NO exista ──
    if ep_path.exists():
        _abort(
            f"La carpeta del episodio ya existe físicamente: {ep_path}\n"
            "Para evitar pérdida de datos, el sistema no sobrescribe.\n"
            "Elige un slug o número diferente, o elimina manualmente si fue un error."
        )

    # ── Crear carpeta ──
    ep_path.mkdir(parents=True, exist_ok=False)
    _ok(f"Carpeta creada: {ep_path}")

    # ── Registrar en índice ──
    entry = {
        "ep_id": ep_id,
        "slug": slug,
        "ep_folder": ep_folder_name,
        "ep_path": str(ep_path),
        "estado": "en_progreso",
        "creado": datetime.now().isoformat(),
        "cerrado": None
    }
    episodes.append(entry)
    index["episodes"] = episodes
    save_index(index_path, index)
    _ok(f"Episodio registrado en índice: {index_path}")

    # ── Imprimir EP_PATH para que el pipeline lo capture ──
    print(f"\n📁 EP_PATH={ep_path}")
    print("\n🟢 Episodio iniciado correctamente. Puedes comenzar el pipeline.")
    print(f"   Estado: en_progreso")
    print(f"   ID: {ep_id} | Slug: {slug}\n")


if __name__ == "__main__":
    main()
