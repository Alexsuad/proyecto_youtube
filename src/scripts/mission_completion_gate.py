"""CLI for the provider-neutral deterministic mission completion gate."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.core.gate_runtime import run_gate
from src.core.mission_completion_gate import load_mission_contract, run_mission_completion_gate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", required=True, help="Path to a structured MissionContract JSON file")
    parser.add_argument("--repo-root", default=".", help="Repository root to inspect")
    parser.add_argument("--output-root", default=None, help="Optional gate evidence output root")
    args = parser.parse_args(argv)
    contract = load_mission_contract(args.contract)
    return run_gate(
        lambda: run_mission_completion_gate(contract, Path(args.repo_root)),
        output_root=args.output_root,
    )


if __name__ == "__main__":
    raise SystemExit(main())
