"""Gate de duración con entradas y salida canónicas."""
import argparse
import re
from pathlib import Path

from src.core.gate_result import GateResult
from src.core.gate_runtime import run_gate
from src.core.input_validation import InputRequirement, validate_inputs
from src.core.status import GateStatus


def count_words(text: str) -> int:
    return len(re.findall(r"\b\w+\b", re.sub(r"#+\s+|\*+", "", text)))


def evaluate(ep_path: Path, wpm: int, minimum: int, maximum: int, episode_id: str | None = None) -> GateResult:
    artifact_id = episode_id or ep_path.name
    script = ep_path / "06_guion_longform.md"
    blocked, failures, evidence = validate_inputs([InputRequirement(script, "06_guion_longform.md")])
    if blocked:
        return GateResult("qa_duracion_guion", artifact_id, "1.0.0", GateStatus.BLOCKED, "No se puede medir la duración", blocked, evidence=evidence)
    if failures:
        return GateResult("qa_duracion_guion", artifact_id, "1.0.0", GateStatus.FAIL, "Entrada inválida", failures, evidence=evidence)
    words = count_words(script.read_text(encoding="utf-8"))
    minutes = words / wpm
    evidence.update({"words": words, "wpm": wpm, "estimated_minutes": minutes, "target": [minimum, maximum]})
    if minimum <= minutes <= maximum:
        return GateResult("qa_duracion_guion", artifact_id, "1.0.0", GateStatus.PASS, "Duración dentro del objetivo", evidence=evidence)
    return GateResult("qa_duracion_guion", artifact_id, "1.0.0", GateStatus.FAIL, "Duración fuera del objetivo", [f"Duración estimada {minutes:.2f} min; objetivo {minimum}-{maximum}"], evidence=evidence)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ep_path", required=True)
    parser.add_argument("--wpm", type=int, default=144)
    parser.add_argument("--min_target", type=int, default=18)
    parser.add_argument("--max_target", type=int, default=22)
    parser.add_argument("--ep-id")
    parser.add_argument("--output-root")
    args = parser.parse_args()
    return run_gate(lambda: evaluate(Path(args.ep_path), args.wpm, args.min_target, args.max_target, args.ep_id), output_root=args.output_root)


if __name__ == "__main__":
    import sys
    sys.exit(main())
