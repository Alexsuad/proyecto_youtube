from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.ai.contracts import ExecutionRequest
from src.ai.manifest import file_checksum
from src.ai.execution import execute, persist_execution_result
from src.ai.runtime_profiles import AgentRuntimePort


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Owner-selected smoke runner for unified AI execution routes.")
    parser.add_argument("--role", required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--route", choices=["local_model", "api_model", "agent_harness"])
    parser.add_argument("--executor")
    parser.add_argument("--provider")
    parser.add_argument("--model")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--max-retries", type=int, default=0)
    parser.add_argument("--temperature", type=float)
    parser.add_argument("--max-tokens", type=int)
    parser.add_argument("--budget-limit", type=float)
    parser.add_argument("--approve-paid-cost", action="store_true")
    parser.add_argument("--probe-arg", action="append", default=[])
    parser.add_argument("--execution-profiles-path", default="config/agent_execution_profiles.json")
    parser.add_argument("--execution-registry-path", default="output/execution_provenance_registry.json")
    parser.add_argument("--output", required=True)
    parser.add_argument("--episode-id", default="SMOKE")
    return parser


def build_run_configuration(args: argparse.Namespace) -> dict[str, object]:
    return {
        "role_id": args.role,
        "execution_route": args.route or "agent_harness",
        "execution_profile": args.profile,
        "executor_override": args.executor,
        "provider_override": args.provider,
        "model_override": args.model,
        "timeout_seconds": args.timeout,
        "max_retries": args.max_retries,
        "temperature": args.temperature,
        "max_tokens": args.max_tokens,
        "budget_limit": args.budget_limit,
        "paid_cost_approved": args.approve_paid_cost,
    }


def main() -> int:
    args = build_parser().parse_args()
    profiles_path = Path(args.execution_profiles_path)
    runtime = AgentRuntimePort(profiles_path)
    run_configuration = build_run_configuration(args)
    resolved = runtime.resolve_run_configuration(run_configuration)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path = Path(args.execution_registry_path)
    probe_args = args.probe_arg or ["--help"]

    request = ExecutionRequest(
        capability_id=args.role,
        skill_id="skill_unified_execution_smoke",
        skill_version="1.0.0",
        input_artifacts=[],
        output_schema="execution_smoke_report",
        execution_mode="agent_harness" if resolved.route_type == "AGENT_HARNESS_RUNTIME" else ("api" if resolved.route_type == "API_MODEL_RUNTIME" else "local"),
        provider=resolved.provider_adapter,
        model=None if resolved.model == "UNAVAILABLE_FROM_EXECUTOR" else resolved.model,
        executor=resolved.executor,
        execution_route=resolved.execution_route,
        execution_profile=resolved.execution_profile,
        timeout=float(resolved.timeout_seconds),
        output_artifact_kind="execution_smoke_report",
        output_artifact_id=output_path.stem,
        output_artifact_path=output_path,
        output_artifact_ref=f"execution_smoke_report:{output_path.stem}",
        episode_id=args.episode_id,
        role=args.role,
        run_configuration=run_configuration,
        config={
            "execution_profiles_path": str(profiles_path),
            "execution_registry_path": str(registry_path),
            "prompt_version": "smoke-1.0.0",
            "smoke_test": True,
            "probe_args": probe_args,
            "isolated_workdir": str(output_path.parent),
        },
    )

    result = execute(request)
    payload = result.output or {
        "status": result.status.value,
        "error": result.error,
        "role_id": args.role,
        "execution_profile": args.profile,
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result.output_checksum = file_checksum(output_path)
    if result.status.value == "SUCCEEDED":
        persist_execution_result(registry_path, result, request, execution_mode="REAL")
        print(json.dumps({"status": result.status.value, "run_id": result.run_id, "output": str(output_path)}, ensure_ascii=False))
        return 0
    print(json.dumps({"status": result.status.value, "error": result.error, "output": str(output_path)}, ensure_ascii=False))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
