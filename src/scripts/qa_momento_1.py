"""Alias contractual del QA de Momento 1."""
import argparse
from pathlib import Path

from qa_brief_research import evaluate as brief_evaluate
from src.core.gate_runtime import run_gate


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--ep_path", required=True); parser.add_argument("--output-root")
    args = parser.parse_args()
    def evaluate():
        result = brief_evaluate(Path(args.ep_path)); result.gate_id = "qa_momento_1"; return result
    return run_gate(evaluate, output_root=args.output_root)

if __name__ == "__main__":
    import sys
    sys.exit(main())
