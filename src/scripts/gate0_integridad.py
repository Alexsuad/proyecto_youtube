"""Gate 0 de integridad con resultados estructurados."""
import argparse
import json
from pathlib import Path

from src.core.gate_result import GateResult
from src.core.gate_runtime import run_gate
from src.core.input_validation import InputRequirement, validate_inputs
from src.core.path_resolution import REPO_ROOT, expand_path
from src.core.status import GateStatus
from src.scripts.runtime_contamination_guard import scan

def evaluate() -> GateResult:
    contamination = scan(REPO_ROOT, REPO_ROOT / "config" / "runtime_contamination_policy.json")
    if contamination["exit_code"] != 0:
        status = GateStatus.BLOCKED if contamination["exit_code"] == 2 else GateStatus.FAIL
        return GateResult("gate0_integridad", "system", "1.0.0", status, "Contaminación runtime detectada", evidence={"runtime_contamination_guard": contamination})
    cfg = REPO_ROOT / "config/local_settings.json"; blocked, failures, evidence = validate_inputs([InputRequirement(cfg, cfg.name, required=False)])
    if blocked: return GateResult("gate0_integridad", "system", "1.0.0", GateStatus.BLOCKED, "Configuración ausente", blocked, evidence=evidence)
    if failures: return GateResult("gate0_integridad", "system", "1.0.0", GateStatus.FAIL, "Configuración inválida", failures, evidence=evidence)
    warnings = []
    if not cfg.is_file():
        warnings.append("Ruta portable: comprobaciones legacy de índice Vault omitidas")
        evidence["execution_path"] = "portable_checkout"
        return GateResult("gate0_integridad", "system", "1.0.0", GateStatus.WARN, "Integridad comprobada sin estado legacy", warnings=warnings, evidence=evidence)
    try: config = json.loads(cfg.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc: return GateResult("gate0_integridad", "system", "1.0.0", GateStatus.FAIL, "Configuración inválida", [str(exc)], evidence=evidence)
    if not config.get("vault_root") or not config.get("channel_id"): return GateResult("gate0_integridad", "system", "1.0.0", GateStatus.FAIL, "Configuración incompleta", ["vault_root/channel_id requeridos"], evidence=evidence)
    index = expand_path(config["vault_root"]) / config["channel_id"] / "index/episodes_index.json"
    blocked, failures, index_evidence = validate_inputs([InputRequirement(index, "episodes_index.json")]); evidence.update(index_evidence)
    if blocked: return GateResult("gate0_integridad", "system", "1.0.0", GateStatus.BLOCKED, "Índice requerido ausente", blocked, evidence=evidence)
    if failures: return GateResult("gate0_integridad", "system", "1.0.0", GateStatus.FAIL, "Índice inválido", failures, evidence=evidence)
    try: episodes = json.loads(index.read_text(encoding="utf-8")).get("episodes", [])
    except json.JSONDecodeError as exc: return GateResult("gate0_integridad", "system", "1.0.0", GateStatus.FAIL, "Índice inválido", [str(exc)], evidence=evidence)
    warnings.extend(f"Episodio en progreso: {e.get('ep_id', '?')}" for e in episodes if e.get("estado") == "en_progreso")
    evidence["execution_path"] = "legacy_vault"
    return GateResult("gate0_integridad", "system", "1.0.0", GateStatus.WARN if warnings else GateStatus.PASS, "Integridad comprobada", warnings=warnings, evidence=evidence)

def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--output-root"); args = parser.parse_args(); return run_gate(evaluate, output_root=args.output_root)

if __name__ == "__main__":
    import sys
    sys.exit(main())
