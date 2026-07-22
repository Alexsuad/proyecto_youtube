"""Gate determinista de lenguaje YouTube."""
import argparse
import re
from pathlib import Path

from src.core.gate_result import GateResult
from src.core.gate_runtime import run_gate
from src.core.input_validation import InputRequirement, validate_inputs
from src.core.path_resolution import REPO_ROOT
from src.core.status import GateStatus


def parse_policy(path: Path) -> dict[str, list[str]]:
    groups = {"lista_roja": [], "lista_amarilla": []}; current = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.endswith(":"):
            current = line[:-1]
        elif current in groups and line.startswith("-"):
            groups[current].append(line[1:].strip().strip("\"'"))
    return groups


def evaluate(ep_path: Path, phase: str, gate_id: str = "qa_lenguaje_youtube", episode_id: str | None = None) -> GateResult:
    artifact_id = episode_id or ep_path.name
    names = ["00_brief_episodio.md", "04_analisis_patrones.md", "05_sintesis_tesis.md"] if phase == "pre-guion" else ["06_guion_longform.md", "09_packaging.md", "10_seo.md"]
    requirements = [InputRequirement(ep_path / name, name) for name in names]
    blocked, failures, evidence = validate_inputs(requirements)
    if blocked:
        return GateResult(gate_id, artifact_id, "1.0.0", GateStatus.BLOCKED, "Faltan entradas declaradas", blocked, evidence=evidence)
    if failures:
        return GateResult(gate_id, artifact_id, "1.0.0", GateStatus.FAIL, "Entradas inválidas", failures, evidence=evidence)
    policy_path = REPO_ROOT / "config" / "qa_youtube_lenguaje.yml"
    if not policy_path.is_file() or not policy_path.read_text(encoding="utf-8").strip():
        return GateResult(gate_id, artifact_id, "1.0.0", GateStatus.BLOCKED, "Política de lenguaje no disponible", ["Configuración qa_youtube_lenguaje.yml ausente o vacía"], evidence=evidence)
    policy = parse_policy(policy_path); red, yellow = [], []
    for name in names:
        for number, line in enumerate((ep_path / name).read_text(encoding="utf-8").splitlines(), 1):
            for word in policy["lista_roja"]:
                if re.search(r"\b" + re.escape(word.lower()) + r"\b", line.lower()): red.append(f"{name}:L{number}: término rojo {word}")
            for word in policy["lista_amarilla"]:
                if re.search(r"\b" + re.escape(word.lower()) + r"\b", line.lower()): yellow.append(f"{name}:L{number}: término amarillo {word}")
    evidence["phase"] = phase
    if red: return GateResult(gate_id, artifact_id, "1.0.0", GateStatus.FAIL, "Se detectaron términos rojos", red, yellow, evidence)
    if yellow: return GateResult(gate_id, artifact_id, "1.0.0", GateStatus.WARN, "Se detectaron términos amarillos", warnings=yellow, evidence=evidence)
    return GateResult(gate_id, artifact_id, "1.0.0", GateStatus.PASS, "Sin hallazgos", evidence=evidence)


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--ep_path", required=True); parser.add_argument("--fase", required=True, choices=["pre-guion", "post-guion"]); parser.add_argument("--ep-id"); parser.add_argument("--output-root"); parser.add_argument("--gate-id", default="qa_lenguaje_youtube")
    args = parser.parse_args(); return run_gate(lambda: evaluate(Path(args.ep_path), args.fase, args.gate_id, args.ep_id), output_root=args.output_root)

if __name__ == "__main__":
    import sys
    sys.exit(main())
