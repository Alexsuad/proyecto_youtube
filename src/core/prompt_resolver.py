"""PromptResolver portatil: resuelve prompt activo y configuracion runtime para un role_id."""

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parents[2]


class PromptResolutionError(Exception):
    """Error during prompt resolution."""

class ConfigResolutionError(Exception):
    """Error during runtime configuration resolution."""


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {path}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def resolve_prompt(role_id: str) -> dict[str, Any]:
    """Return the active prompt contract for a given role_id.

    Reads the prompt registry, finds the ACTIVE entry for role_id,
    then loads the corresponding prompt markdown file.

    Blocks if:
    - role_id is not in the registry
    - no ACTIVE prompt exists for role_id
    - prompt_version is missing
    - the prompt markdown file does not exist
    """
    registry = _read_json(ROOT / "config" / "agent_prompt_registry.json")

    prompts = registry.get("prompts", [])
    matching = [p for p in prompts if p.get("role_id") == role_id]

    if not matching:
        raise PromptResolutionError(f"role_id '{role_id}' no encontrado en agent_prompt_registry")

    active = [p for p in matching if p.get("status") == "ACTIVE"]
    if not active:
        raise PromptResolutionError(
            f"No hay prompt ACTIVE para role_id '{role_id}'. "
            f"Status encontrado(s): {[p.get('status') for p in matching]}"
        )

    if len(active) > 1:
        raise PromptResolutionError(
            f"Multiples prompts ACTIVE para role_id '{role_id}'"
        )

    entry = active[0]
    version = entry.get("prompt_version")
    if not version:
        raise PromptResolutionError(f"prompt_version ausente para role_id '{role_id}'")

    prompt_path = ROOT / "prompts" / "roles" / role_id / f"{version}.md"
    if not prompt_path.exists():
        raise PromptResolutionError(
            f"Prompt file no encontrado: {prompt_path} (version={version})"
        )

    return entry


def resolve_runtime(role_id: str) -> dict[str, Any]:
    """Return the runtime configuration entry for a given role_id.

    Reads ai_runtime config and finds the matching entry.

    Blocks if:
    - config file is missing
    - role_id is not in the config
    """
    config_path = ROOT / "config" / "ai_runtime.example.json"
    try:
        if not config_path.exists():
            raise ConfigResolutionError(f"Configuracion runtime no encontrada: {config_path}")
        config = _read_json(config_path)
    except FileNotFoundError as e:
        raise ConfigResolutionError(str(e)) from e
    entries = config.get("entries", [])
    matching = [e for e in entries if e.get("role_id") == role_id]

    if not matching:
        raise ConfigResolutionError(
            f"role_id '{role_id}' no encontrado en configuracion runtime"
        )

    return matching[0]


def resolve_execution(role_id: str) -> dict[str, Any]:
    """Resolve prompt + runtime into a single execution object.

    Returns a dict with:
    - role_id
    - prompt (contract from registry)
    - prompt_content_path (str path to the .md file)
    - runtime (config entry)
    - adapter (from runtime config)

    Does NOT invoke any external API.
    """
    prompt_entry = resolve_prompt(role_id)
    runtime_entry = resolve_runtime(role_id)

    prompt_path = (
        ROOT / "prompts" / "roles" / role_id / f"{prompt_entry['prompt_version']}.md"
    )

    return {
        "role_id": role_id,
        "prompt": prompt_entry,
        "prompt_content_path": str(prompt_path),
        "runtime": runtime_entry,
        "adapter": runtime_entry.get("adapter", "unknown"),
    }
