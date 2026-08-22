"""Legacy wrapper around the channel-neutral episode storage service.

The old technical arguments remain supported for existing operators. New users
should use ``python -m src.cli iniciar`` instead.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.application.storage import StorageError, VaultEpisodeStore


CONFIG_PATH = REPO_ROOT / "config" / "local_settings.json"


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        raise StorageError(f"No se encontró config en: {CONFIG_PATH}")
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StorageError(f"No se pudo leer la configuración: {exc}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description="Compatibilidad: iniciar un episodio en el Vault.")
    parser.add_argument("--num", type=int, required=True, help="Número del episodio")
    parser.add_argument("--slug", required=True, help="Slug descriptivo")
    args = parser.parse_args()
    try:
        raw_slug = args.slug.strip().lower().replace(" ", "_").replace("-", "_")
        if not re.fullmatch(r"[a-z0-9][a-z0-9_]{0,49}", raw_slug):
            raise StorageError(
                "Slug inválido: usa letras minúsculas, números y guiones bajos, entre 1 y 50 caracteres."
            )
        settings = load_config()
        store = VaultEpisodeStore(settings["vault_root"], settings["channel_id"])
        handle = store.create_legacy_episode(
            episode_number=args.num,
            slug=raw_slug,
        )
    except (KeyError, StorageError, ValueError) as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        return 1
    print(f"\nEpisodio iniciado: {handle.folder.name}")
    print(f"EP_PATH={handle.folder}")
    print(f"Estado: en_progreso | ID: {handle.episode_id}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
