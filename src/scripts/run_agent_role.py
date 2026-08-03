from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.ai.contracts import ExecutionRequest
from src.ai.execution import execute, persist_execution_attempt, persist_execution_result
from src.ai.manifest import file_checksum
from src.ai.role_execution import RoleExecutionContractError, build_model_prompt, resolve_role_execution_contract
from src.ai.runtime_profiles import AgentRuntimePort


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Contractual role runner for owner-selected AI execution routes.")
    parser.add_argument("--role", required=True); parser.add_argument("--profile", required=True)
    parser.add_argument("--route", choices=["local_model", "api_model", "agent_harness"]); parser.add_argument("--executor"); parser.add_argument("--provider"); parser.add_argument("--model")
    parser.add_argument("--timeout", type=int, default=30); parser.add_argument("--max-retries", type=int, default=0); parser.add_argument("--temperature", type=float); parser.add_argument("--max-tokens", type=int); parser.add_argument("--budget-limit", type=float); parser.add_argument("--approve-paid-cost", action="store_true")
    parser.add_argument("--input"); parser.add_argument("--execution-profiles-path", default="config/agent_execution_profiles.json"); parser.add_argument("--execution-registry-path", default="output/execution_provenance_registry.json"); parser.add_argument("--output", required=True); parser.add_argument("--episode-id", default="SMOKE")
    return parser


def build_run_configuration(args: argparse.Namespace) -> dict[str, object]:
    return {"role_id":args.role,"execution_route":args.route or "agent_harness","execution_profile":args.profile,"executor_override":args.executor,"provider_override":args.provider,"model_override":args.model,"timeout_seconds":args.timeout,"max_retries":args.max_retries,"temperature":args.temperature,"max_tokens":args.max_tokens,"budget_limit":args.budget_limit,"paid_cost_approved":args.approve_paid_cost}


def load_input(path: str | None) -> dict[str, object]:
    if path is None:
        return {"mode":"CONTROLLED_SMOKE","episode_id":"SMOKE","product_artifacts":[],"note":"No editorial product is produced by this smoke."}
    try:
        data=json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc: raise RoleExecutionContractError(f"INPUT_CONTRACT_INVALID: input file not found: {path}") from exc
    except json.JSONDecodeError as exc: raise RoleExecutionContractError(f"INPUT_CONTRACT_INVALID: input JSON invalid: {exc.msg}") from exc
    if not isinstance(data,dict): raise RoleExecutionContractError("INPUT_CONTRACT_INVALID: input payload must be a JSON object")
    return data


def main() -> int:
    args=build_parser().parse_args(); output_path=Path(args.output); output_path.parent.mkdir(parents=True,exist_ok=True)
    try:
        runtime=AgentRuntimePort(Path(args.execution_profiles_path)); resolved=runtime.resolve_run_configuration(build_run_configuration(args))
        runtime_values={"smoke_id":output_path.stem,"role_id":args.role,"execution_profile":resolved.execution_profile,"execution_route":resolved.execution_route,"selected_executor":resolved.executor,"selected_provider":resolved.provider,"selected_model":resolved.model,"actual_executor":resolved.executor,"actual_provider":resolved.provider,"actual_model":resolved.model,"result":"SUCCEEDED","decision":"CONTRACTUAL_SMOKE_PASS","stdout_preview":"contractual role prompt and output schema validated","stderr_preview":"","exit_code":0,"notes":["controlled R6-B smoke; no editorial product"]}
        contract=resolve_role_execution_contract(args.role,"execution_smoke_report",load_input(args.input),runtime_values)
    except (RoleExecutionContractError, ValueError) as exc:
        payload={"status":"FAILED","error":str(exc),"role_id":args.role,"execution_profile":args.profile}; output_path.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); print(json.dumps(payload,ensure_ascii=False)); return 1
    request=ExecutionRequest(capability_id=args.role,skill_id="skill_unified_execution_smoke",skill_version="1.0.0",input_artifacts=[],output_schema="execution_smoke_report",execution_mode="agent_harness" if resolved.route_type=="AGENT_HARNESS_RUNTIME" else ("api" if resolved.route_type=="API_MODEL_RUNTIME" else "local"),provider=resolved.provider_adapter,model=None if resolved.model=="UNAVAILABLE_FROM_EXECUTOR" else resolved.model,executor=resolved.executor,execution_route=resolved.execution_route,execution_profile=resolved.execution_profile,timeout=float(resolved.timeout_seconds),output_artifact_kind="execution_smoke_report",output_artifact_id=output_path.stem,output_artifact_path=output_path,output_artifact_ref=f"execution_smoke_report:{output_path.stem}",episode_id=args.episode_id,role=args.role,run_configuration=build_run_configuration(args),config={"execution_profiles_path":str(args.execution_profiles_path),"execution_registry_path":str(args.execution_registry_path),"prompt_id":contract["prompt_id"],"prompt_version":contract["prompt_version"],"prompt_checksum":contract["prompt_checksum"],"input_checksum":contract["input_checksum"],"prompt":build_model_prompt(contract),"validation_result":"PENDING","smoke_test":True,"isolated_workdir":str(output_path.parent)})
    result=execute(request)
    request.config["validation_result"]="PASS" if result.status.value=="SUCCEEDED" else "FAIL"
    payload=result.output or {"status":result.status.value,"error":result.error,"role_id":args.role,"execution_profile":args.profile}
    output_path.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); result.output_checksum=file_checksum(output_path)
    if result.status.value=="SUCCEEDED":
        persist_execution_result(Path(args.execution_registry_path),result,request,execution_mode="REAL"); print(json.dumps({"status":"SUCCESS","run_id":result.run_id,"output":str(output_path)},ensure_ascii=False)); return 0
    persist_execution_attempt(Path(args.execution_registry_path), result, request, execution_mode="REAL")
    print(json.dumps({"status":"FAILED","error":result.error,"output":str(output_path)},ensure_ascii=False)); return 1

if __name__=="__main__": raise SystemExit(main())
