"""Gate 0 de auditoría del sistema sin falsos PASS."""
import argparse
import json
from pathlib import Path

from src.core.gate_result import GateResult
from src.core.gate_runtime import run_gate
from src.core.input_validation import InputRequirement, validate_inputs
from src.core.path_resolution import REPO_ROOT, expand_path
from src.core.status import GateStatus

REQUIRED_DIRS = [".agent/rules", ".agent/skills", ".agent/workflows", "templates", "workspace", "config"]
REQUIRED_RULES = ["00_reglas_globales.md", "01_formato_outputs.md", "02_reglas_notebooklm.md"]

def evaluate() -> GateResult:
    config_path = REPO_ROOT / "config" / "local_settings.json"
    blocked, failures, evidence = validate_inputs([InputRequirement(config_path, "config/local_settings.json")])
    if blocked: return GateResult("gate0_auditoria", "system", "1.0.0", GateStatus.BLOCKED, "Configuración requerida ausente", blocked, evidence=evidence)
    try: config = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc: return GateResult("gate0_auditoria", "system", "1.0.0", GateStatus.FAIL, "Configuración JSON inválida", [str(exc)], evidence=evidence)
    for item in REQUIRED_DIRS:
        if not (REPO_ROOT / item).is_dir(): failures.append(f"Directorio requerido ausente: {item}")
    for item in REQUIRED_RULES:
        if not (REPO_ROOT / ".agent/rules" / item).is_file(): failures.append(f"Regla requerida ausente: {item}")
    if not config.get("vault_root") or not config.get("channel_id"): failures.append("vault_root y channel_id son obligatorios")
    elif not expand_path(config["vault_root"]).is_dir(): failures.append("vault_root no existe o no es directorio")
    return GateResult("gate0_auditoria", "system", "1.0.0", GateStatus.FAIL if failures else GateStatus.PASS, "Auditoría de sistema completada", failures, evidence=evidence)

def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--output-root"); args = parser.parse_args(); return run_gate(evaluate, output_root=args.output_root)

if __name__ == "__main__":
    import sys
    sys.exit(main())
