"""Consume one pending cognitive handoff through the managed OpenCode runner."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from uuid import uuid4

from src.ai.contracts import ExecutionRequest
from src.ai.manifest import canonical_json
from src.ai.providers.agent_executor import AgentExecutorProvider
from src.ai.providers.agent_handoff import AgentHandoffProvider


def _checksum(value: object) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def consume(package_path: Path, output_path: Path) -> dict[str, object]:
    package = json.loads(package_path.read_text(encoding="utf-8"))
    result_run_id = f"RESULT-{uuid4().hex}"
    request = ExecutionRequest(
        capability_id=str(package["capability_id"]),
        skill_id=str(package["skill_id"]),
        skill_version=str(package["skill_version"]),
        input_artifacts=[],
        output_schema=str(package["output_schema"]),
        execution_mode="REAL",
        model="UNAVAILABLE_FROM_EXECUTOR",
        execution_route="agent_harness",
        execution_family="AGENT_HARNESS",
        timeout=max(float(package.get("timeout_seconds") or 0), 180.0),
        config={
            "prompt": str(package["prompt"]),
            "isolated_workdir": str(Path(package["mission_repo_root"]).resolve()),
        },
        episode_id=str(package["episode_id"]),
        role=str(package["role"]),
        executor="OWNER_MANAGED",
    )
    output, usage = AgentExecutorProvider().execute(request)
    envelope = {
        "handoff_id": package["handoff_id"],
        "package_checksum": package["package_checksum"],
        "input_manifest_checksum": package["input_manifest_checksum"],
        "skill_id": package["skill_id"],
        "skill_version": package["skill_version"],
        "mission_id": package["mission_id"],
        "episode_id": package["episode_id"],
        "capability_id": package["capability_id"],
        "stage": package["stage"],
        "role": package["role"],
        "result_run_id": result_run_id,
        "output": output,
        "output_checksum": _checksum(output),
        "provenance": {
            "mission_id": package["mission_id"],
            "episode_id": package["episode_id"],
            "capability_id": package["capability_id"],
            "stage": package["stage"],
            "role": package["role"],
            "run_id": result_run_id,
            "executor_id": f"opencode:{result_run_id}",
            "executor_identity": f"opencode:{result_run_id}",
            "provider": str(usage["actual_provider"]),
            "model": str(usage["actual_model"]),
        },
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(envelope, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    AgentHandoffProvider().import_result(package_path, output_path)
    return envelope


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    envelope = consume(args.package, args.output)
    print(json.dumps({"status": "COGNITIVE_RESULT_READY", "handoff_id": envelope["handoff_id"], "stage": envelope["stage"], "result_run_id": envelope["result_run_id"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
