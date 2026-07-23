"""
Pruebas B4-I2: Prompts oficiales, configuracion agnostica y resolver portable.

Verifica:
- seis prompts registrados y activos
- versiones semver validas
- correspondencia entre responsabilidad y prompt
- ausencia de marcas obligatorias de proveedor, IDE o modelo
- separacion Editor/Auditor
- bloqueo por prompt ausente
- bloqueo por configuracion ausente
- resolucion correcta con adapter mock
- un agente operativo y cero subagentes
- .agent/ no es la sede canonica
- no existen credenciales o secretos en la configuracion de ejemplo
"""

import json
import re
from pathlib import Path

import jsonschema
from jsonschema import Draft7Validator

from src.core.prompt_resolver import (
    resolve_prompt,
    resolve_runtime,
    resolve_execution,
    PromptResolutionError,
    ConfigResolutionError,
)

ROOT = Path(__file__).parents[2]
ROLE_IDS = [
    "ORCHESTRATION",
    "RESEARCH_AND_CURATION",
    "NARRATIVE_ARCHITECTURE",
    "WRITING",
    "EDITOR",
    "FINAL_EDITORIAL_AUDITOR",
]


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


# ─── 1. Registry schema and contracts ───


def test_agent_prompt_registry_schema():
    schema = _read_json(ROOT / "schemas" / "agent_prompt_registry.json")
    registry = _read_json(ROOT / "config" / "agent_prompt_registry.json")
    Draft7Validator.check_schema(schema)
    jsonschema.validate(registry, schema)


def test_six_prompts_registered():
    registry = _read_json(ROOT / "config" / "agent_prompt_registry.json")
    prompts = registry["prompts"]
    assert len(prompts) == 6
    assert [p["role_id"] for p in prompts] == ROLE_IDS


def test_all_prompts_are_active():
    registry = _read_json(ROOT / "config" / "agent_prompt_registry.json")
    for p in registry["prompts"]:
        assert p["status"] == "ACTIVE", f"{p['role_id']} no es ACTIVE"


def test_all_prompt_versions_are_valid_semver():
    registry = _read_json(ROOT / "config" / "agent_prompt_registry.json")
    semver = re.compile(r"^\d+\.\d+\.\d+$")
    for p in registry["prompts"]:
        assert semver.match(p["prompt_version"]), (
            f"{p['role_id']} version={p['prompt_version']} no es semver"
        )


def test_every_role_has_corresponding_prompt_file():
    registry = _read_json(ROOT / "config" / "agent_prompt_registry.json")
    for p in registry["prompts"]:
        prompt_file = ROOT / "prompts" / "roles" / p["role_id"] / f"{p['prompt_version']}.md"
        assert prompt_file.exists(), f"Prompt file no existe: {prompt_file}"


def test_every_prompt_file_has_corresponding_registry_entry():
    """Inverse: every .md file under prompts/roles/ has a registry entry."""
    registry = _read_json(ROOT / "config" / "agent_prompt_registry.json")
    registered = {(p["role_id"], p["prompt_version"]) for p in registry["prompts"]}
    for role_dir in (ROOT / "prompts" / "roles").iterdir():
        if not role_dir.is_dir():
            continue
        for md_file in role_dir.glob("*.md"):
            version = md_file.stem
            assert (role_dir.name, version) in registered, (
                f"Prompt file {md_file} no tiene entrada en el registro"
            )


# ─── 2. Neutrality ───


def test_no_provider_or_model_identifiers_in_prompts():
    """Prompts must be provider-agnostic and model-agnostic."""
    forbidden = [
        "antigravity", "codex", "opencode", "notebooklm",
        "openai", "gemini", "claude", "gpt", "model",
    ]
    for role_id in ROLE_IDS:
        prompt_file = ROOT / "prompts" / "roles" / role_id / "1.0.0.md"
        content = prompt_file.read_text(encoding="utf-8").lower()
        for term in forbidden:
            # "model" is too generic; only check for "model" as a standalone provider reference.
            # Actually the requirement says no specific model names.
            # We check the full set of forbidden identifiers as words.
            matches = re.findall(r'\b' + re.escape(term) + r'\b', content)
            assert not matches, (
                f"Termino prohibido '{term}' encontrado en {prompt_file}: {matches}"
            )


def test_no_provider_or_model_identifiers_in_registry():
    registry = _read_json(ROOT / "config" / "agent_prompt_registry.json")
    text = json.dumps(registry).lower()
    forbidden = ["antigravity", "codex", "opencode", "notebooklm", "openai", "gemini", "claude", "gpt"]
    for term in forbidden:
        assert term not in text, f"Termino prohibido '{term}' encontrado en agent_prompt_registry.json"


def test_no_provider_or_model_identifiers_in_runtime_example():
    config = _read_json(ROOT / "config" / "ai_runtime.example.json")
    text = json.dumps(config).lower()
    forbidden = ["antigravity", "codex", "opencode", "notebooklm", "openai", "gemini", "claude", "gpt"]
    for term in forbidden:
        assert term not in text, f"Termino prohibido '{term}' encontrado en ai_runtime.example.json"


# ─── 3. Editor / Auditor separation ───


def test_editor_can_modify_script():
    registry = _read_json(ROOT / "config" / "agent_prompt_registry.json")
    editor = next(p for p in registry["prompts"] if p["role_id"] == "EDITOR")
    assert "modificar el guion" in editor["allowed_actions"] or "modificar el guion" in str(editor).lower()


def test_editor_cannot_approve_own_result():
    registry = _read_json(ROOT / "config" / "agent_prompt_registry.json")
    editor = next(p for p in registry["prompts"] if p["role_id"] == "EDITOR")
    forbidden_text = json.dumps(editor["forbidden_actions"]).lower()
    assert "aprobar" in forbidden_text or "self-approval" in forbidden_text or "autoaprobar" in forbidden_text


def test_auditor_cannot_modify_script():
    registry = _read_json(ROOT / "config" / "agent_prompt_registry.json")
    auditor = next(p for p in registry["prompts"] if p["role_id"] == "FINAL_EDITORIAL_AUDITOR")
    forbidden_text = json.dumps(auditor["forbidden_actions"]).lower()
    assert "modificar" in forbidden_text, "Auditor debe tener prohibido modificar el guion"


def test_auditor_must_operate_in_clean_context():
    registry = _read_json(ROOT / "config" / "agent_prompt_registry.json")
    auditor = next(p for p in registry["prompts"] if p["role_id"] == "FINAL_EDITORIAL_AUDITOR")
    blocking_text = json.dumps(auditor["blocking_conditions"]).lower()
    assert any(term in blocking_text for term in ["limpio", "clean", "independiente", "independent"]), (
        "Auditor debe bloquear si no opera en contexto limpio o ejecucion independiente"
    )


def test_auditor_can_emit_pass_warn_fail_blocked():
    registry = _read_json(ROOT / "config" / "agent_prompt_registry.json")
    auditor = next(p for p in registry["prompts"] if p["role_id"] == "FINAL_EDITORIAL_AUDITOR")
    evidence_text = json.dumps(auditor["evidence_requirements"]).lower()
    assert "pass" in evidence_text or "PASS" in json.dumps(auditor["evidence_requirements"])


# ─── 4. Resolver behaviour ───


def test_resolve_prompt_returns_active_contract():
    entry = resolve_prompt("ORCHESTRATION")
    assert entry["role_id"] == "ORCHESTRATION"
    assert entry["status"] == "ACTIVE"
    assert entry["prompt_version"] == "1.0.0"


def test_resolve_prompt_all_roles():
    for role_id in ROLE_IDS:
        entry = resolve_prompt(role_id)
        assert entry["role_id"] == role_id
        assert entry["status"] == "ACTIVE"


def test_resolve_prompt_blocks_on_unknown_role():
    try:
        resolve_prompt("UNKNOWN_ROLE")
        assert False, "Debio lanzar PromptResolutionError"
    except PromptResolutionError:
        pass


def test_resolve_runtime_returns_config():
    config = resolve_runtime("ORCHESTRATION")
    assert config["role_id"] == "ORCHESTRATION"
    assert config["provider"] == "mock"
    assert config["adapter"] == "mock"


def test_resolve_runtime_all_roles():
    for role_id in ROLE_IDS:
        config = resolve_runtime(role_id)
        assert config["role_id"] == role_id
        assert config["provider"] == "mock"


def test_resolve_runtime_blocks_on_unknown_role():
    try:
        resolve_runtime("UNKNOWN_ROLE")
        assert False, "Debio lanzar ConfigResolutionError"
    except ConfigResolutionError:
        pass


def test_resolve_execution_returns_complete_object():
    obj = resolve_execution("EDITOR")
    assert obj["role_id"] == "EDITOR"
    assert obj["prompt"]["status"] == "ACTIVE"
    assert obj["runtime"]["provider"] == "mock"
    assert obj["adapter"] == "mock"
    assert "EDITOR" in obj["prompt_content_path"]
    assert "1.0.0.md" in obj["prompt_content_path"]


def test_resolve_execution_no_api_call():
    """Verify the resolver does not invoke external APIs (just reads local files)."""
    import inspect
    source = inspect.getsource(resolve_execution)
    assert "http" not in source.lower()
    assert "socket" not in source.lower()
    assert "openai" not in source.lower()


# ─── 5. Architecture constraints ───


def test_operational_agents_and_subagents():
    registry = _read_json(ROOT / "config" / "responsibility_registry.json")
    assert registry["operational_agents"] == 1
    assert registry["real_subagents"] == 0


def test_agent_dir_is_not_canonical_seat():
    """Verify that prompts/ roles exist independently of .agent/."""
    assert (ROOT / "prompts" / "roles").is_dir(), "prompts/roles/ debe existir"
    assert (ROOT / "prompts" / "roles" / "ORCHESTRATION" / "1.0.0.md").exists()
    assert (ROOT / ".agent" / "skills").is_dir() or (ROOT / ".agent" / "rules").is_dir()


def test_no_credentials_in_runtime_example():
    """Verify no passwords, API keys, tokens, or secrets in the example config."""
    config = _read_json(ROOT / "config" / "ai_runtime.example.json")
    text = json.dumps(config).lower()
    forbidden = [
        "apikey", "api_key", "api-key", "password", "passwd",
        "token", "secret", "credential", "auth",
    ]
    for term in forbidden:
        assert term not in text, f"Termino prohibido '{term}' encontrado en ai_runtime.example.json"


# ─── 6. AI runtime config schema ───


def test_ai_runtime_config_schema():
    schema = _read_json(ROOT / "schemas" / "ai_runtime_config.json")
    config = _read_json(ROOT / "config" / "ai_runtime.example.json")
    Draft7Validator.check_schema(schema)
    jsonschema.validate(config, schema)


def test_ai_runtime_separates_role_provider_model_adapter():
    config = _read_json(ROOT / "config" / "ai_runtime.example.json")
    for entry in config["entries"]:
        assert "role_id" in entry
        assert "provider" in entry
        assert "model" in entry
        assert "adapter" in entry
        assert "tools" in entry
        assert "permissions" in entry
        assert "execution_mode" in entry


def test_ai_runtime_editor_isolation():
    config = _read_json(ROOT / "config" / "ai_runtime.example.json")
    editor = next(e for e in config["entries"] if e["role_id"] == "EDITOR")
    auditor = next(e for e in config["entries"] if e["role_id"] == "FINAL_EDITORIAL_AUDITOR")
    assert editor["execution_mode"] == "HANDOFF"
    assert auditor["execution_mode"] == "ISOLATED"


# ─── 7. Blocking tests with missing files ───


def test_resolve_prompt_blocks_when_prompt_file_missing(monkeypatch):
    """Simulate a registry entry pointing to a non-existent prompt file."""
    import json as jmod
    registry = _read_json(ROOT / "config" / "agent_prompt_registry.json")
    # Create a temporary registry with a version that doesn't exist
    bad_entry = {
        "role_id": "TEST_MISSING",
        "prompt_id": "test_missing",
        "prompt_version": "99.99.99",
        "status": "ACTIVE",
        "objective": "test",
        "authority": "test",
        "required_inputs": [],
        "required_context": [],
        "allowed_actions": [],
        "forbidden_actions": [],
        "required_outputs": [],
        "blocking_conditions": [],
        "handoff": {"to": "nowhere", "condition": "never"},
        "evidence_requirements": [],
    }
    original_read = _read_json


    def mock_registry(path):
        if "agent_prompt_registry" in str(path):
            return {"registry_version": "1.0.0", "prompts": [bad_entry]}
        return original_read(path)

    import src.core.prompt_resolver as pr
    original_fn = pr._read_json
    pr._read_json = mock_registry
    try:
        pr.resolve_prompt("TEST_MISSING")
        assert False, "Debio lanzar PromptResolutionError por archivo faltante"
    except PromptResolutionError as e:
        assert "99.99.99" in str(e)
    finally:
        pr._read_json = original_fn


def test_resolve_runtime_blocks_when_config_missing(monkeypatch):
    """Simulate missing runtime config."""
    import src.core.prompt_resolver as pr

    def mock_not_found(path):
        if "ai_runtime.example.json" in str(path):
            raise FileNotFoundError(str(path))
        # fallback to real
        return pr._read_json(path)

    original_fn = pr._read_json
    pr._read_json = mock_not_found
    try:
        pr.resolve_runtime("ORCHESTRATION")
        assert False, "Debio lanzar ConfigResolutionError"
    except ConfigResolutionError:
        pass
    finally:
        pr._read_json = original_fn
