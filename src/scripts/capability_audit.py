"""Generate deterministic TH-04 capability inventory evidence."""
from __future__ import annotations

import argparse
from pathlib import Path

from src.core.capability_audit import write_th04_artifacts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output-root", default="reports/implementation/plan_004")
    parser.add_argument("--generated-at", default=None, help="ISO-8601 timestamp; supply it for byte-reproducible evidence.")
    args = parser.parse_args(argv)
    artifacts = write_th04_artifacts(Path(args.output_root), root=Path(args.repo_root), generated_at=args.generated_at)
    for name, path in artifacts.items():
        print(f"{name}={path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
