"""Gate 0 de auditoría del sistema sin falsos PASS."""
import argparse
import json
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.core.gate_result import GateResult
from src.core.gate_runtime import run_gate
from src.core.input_validation import InputRequirement, validate_inputs
from src.core.path_resolution import REPO_ROOT, expand_path
from src.core.status import GateStatus

REQUIRED_DIRS = [".agent/rules", ".agent/skills", ".agent/workflows", "templates", "workspace", "config"]
REQUIRED_RULES = ["00_reglas_globales.md", "01_formato_outputs.md", "02_reglas_notebooklm.md"]

def evaluate() -> GateResult:
    config_path = REPO_ROOT / "config" / "local_settings.json"
    blocked, failures, evidence = validate_inputs([InputRequirement(config_path, "config/local_settings.json", required=False)])
    if blocked: return GateResult("gate0_auditoria", "system", "1.0.0", GateStatus.BLOCKED, "Configuración requerida ausente", blocked, evidence=evidence)
    warnings = []
    config = None
    if config_path.is_file():
        try: config = json.loads(config_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            warnings.append(f"Configuración local legacy inválida; se omite el adaptador Vault: {exc.msg}")
    else:
        warnings.append("Ruta portable: comprobaciones legacy de Vault omitidas")
    for item in REQUIRED_DIRS:
        if not (REPO_ROOT / item).is_dir(): failures.append(f"Directorio requerido ausente: {item}")
    for item in REQUIRED_RULES:
        if not (REPO_ROOT / ".agent/rules" / item).is_file(): failures.append(f"Regla requerida ausente: {item}")
    if config is not None and not isinstance(config, dict):
        warnings.append("Configuración local legacy no es un objeto; se omite el adaptador Vault")
        config = None
    if config is not None:
        if not config.get("vault_root") or not config.get("channel_id"):
            warnings.append("Configuración local legacy incompleta; se omite el adaptador Vault")
            config = None
        elif not expand_path(config["vault_root"]).is_dir():
            warnings.append("vault_root legacy no existe; se continúa por la ruta portable")
            config = None
    evidence["execution_path"] = "legacy_vault" if config is not None else "portable_checkout"
    status = GateStatus.FAIL if failures else (GateStatus.WARN if warnings else GateStatus.PASS)
    return GateResult("gate0_auditoria", "system", "1.0.0", status, "Auditoría de sistema completada", failures, warnings=warnings, evidence=evidence)

def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--output-root"); args = parser.parse_args(); return run_gate(evaluate, output_root=args.output_root)

if __name__ == "__main__":
    import sys
    sys.exit(main())
