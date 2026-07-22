"""QA del brief y research con contrato GateResult."""
import argparse
import re
from pathlib import Path

from src.core.gate_result import GateResult
from src.core.gate_runtime import run_gate
from src.core.input_validation import InputRequirement, validate_inputs
from src.core.status import GateStatus


def evaluate(ep_path: Path, episode_id: str | None = None) -> GateResult:
    artifact_id = episode_id or ep_path.name
    brief, research = ep_path / "00_brief_episodio.md", ep_path / "01_research_bruto.md"
    blocked, failures, evidence = validate_inputs([InputRequirement(brief, brief.name), InputRequirement(research, research.name)])
    if blocked: return GateResult("qa_brief_research", artifact_id, "1.0.0", GateStatus.BLOCKED, "Faltan entradas", blocked, evidence=evidence)
    if failures: return GateResult("qa_brief_research", artifact_id, "1.0.0", GateStatus.FAIL, "Entradas inválidas", failures, evidence=evidence)
    b, r = brief.read_text(encoding="utf-8"), research.read_text(encoding="utf-8")
    checks = [
        (r"- FECHA:\s*\d{4}-\d{2}-\d{2}", "FECHA válida"),
        (r"- TESIS_CENTRAL \(\d+ frase[s]?\):\s*(?!\[PENDIENTE\])\S+", "TESIS_CENTRAL válida"),
        (r"- SPOILERS/SENSIBILIDADES:\s*(?!\[PENDIENTE\])\S+", "SPOILERS/SENSIBILIDADES válida"),
    ]
    violations = [label for pattern, label in checks if not re.search(pattern, b)]
    if len(set(re.findall(r"https?://[^\s\)]+", r))) < 8: violations.append("Research requiere al menos 8 URLs")
    if len(re.findall(r"por qu[eé] sirve", r, re.IGNORECASE)) < 8: violations.append("Research requiere 'Por qué sirve' para 8 fuentes")
    evidence["inputs_reviewed"] = [brief.name, research.name]
    return GateResult("qa_brief_research", artifact_id, "1.0.0", GateStatus.FAIL if violations else GateStatus.PASS, "QA Brief/Research completado" if not violations else "QA Brief/Research no superado", violations, evidence=evidence)


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--ep_path", required=True); parser.add_argument("--ep-id"); parser.add_argument("--output-root")
    args = parser.parse_args(); return run_gate(lambda: evaluate(Path(args.ep_path), args.ep_id), output_root=args.output_root)

if __name__ == "__main__":
    import sys
    sys.exit(main())
