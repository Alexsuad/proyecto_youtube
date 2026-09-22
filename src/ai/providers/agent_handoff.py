"""Paquetes verificables para ejecución humana/agéntica fuera del proceso local."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from src.ai.contracts import ExecutionRequest
from src.ai.manifest import build_input_manifest, canonical_json, file_checksum
from src.ai.registry import skill_checksum
from src.core.mission_completion_gate import (
    load_mission_contract,
    validate_verified_completion_gate,
    verify_completion_gate_for_repository,
)
from src.core.mission_authorization import load_mission_authorization
from src.core.contract_validation import validate_against_schema


VALID_AUTHORIZATION_MODES = frozenset({"MISSION", "PRODUCT"})


def _validated_authorization_mode(value: Any) -> str:
    mode = str(value or "MISSION").upper()
    if mode not in VALID_AUTHORIZATION_MODES:
        raise PermissionError("AUTHORIZATION_MODE_INVALID:" + mode)
    return mode


def load_verified_completion_gate_from_payload(data: dict[str, Any] | None):
    if not isinstance(data, dict):
        raise PermissionError("MISSION_COMPLETION_GATE_REQUIRED: package lacks completion gate")
    try:
        from src.core.gate_result import GateResult

        result = GateResult.from_dict(data)
    except (ValueError, TypeError) as exc:
        raise PermissionError(f"MISSION_COMPLETION_GATE_REQUIRED: {exc}") from exc
    return validate_verified_completion_gate(result)


def checksum(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


class AgentHandoffProvider:
    name = "agent_handoff"

    @staticmethod
    def _require_preparation_authority(request: ExecutionRequest) -> str:
        """Require a complete, unambiguous authority before serializing a package."""
        raw_mode = request.config.get("authorization_mode")
        if not str(raw_mode or "").strip():
            raise PermissionError("AUTHORIZATION_MODE_REQUIRED_FOR_HANDOFF")
        authorization_mode = _validated_authorization_mode(raw_mode)
        mission_id = request.config.get("mission_id")
        authorization_id = request.config.get("authorization_id")
        authorization_checksum = request.config.get("authorization_checksum")
        mission_binding_present = any(
            request.config.get(key)
            for key in ("mission_authorization_path", "mission_contract_path", "_mission_authorization_token")
        )
        product_binding_present = bool(authorization_id or authorization_checksum)
        if authorization_mode == "PRODUCT":
            if mission_id is not None or mission_binding_present:
                raise PermissionError("AUTHORIZATION_MODE_CONFLICT:PRODUCT_WITH_MISSION_BINDING")
            if not str(authorization_id or "").strip() or not str(authorization_checksum or "").strip():
                raise PermissionError("PRODUCT_AUTHORIZATION_REQUIRED_FOR_HANDOFF")
            return authorization_mode
        if product_binding_present:
            raise PermissionError("AUTHORIZATION_MODE_CONFLICT:MISSION_WITH_PRODUCT_BINDING")
        if not str(mission_id or "").strip():
            raise PermissionError("MISSION_ID_REQUIRED_FOR_HANDOFF")
        return authorization_mode

    @staticmethod
    def _resolve_directory(request: ExecutionRequest, repo_root: Path) -> Path:
        directory = request.handoff_directory or Path("handoff")
        if not directory.is_absolute():
            directory = repo_root / directory
        return directory

    @staticmethod
    def _write_package(
        request: ExecutionRequest,
        manifest_checksum: str,
        run_id: str,
        directory: Path,
        completion_gate: Any | None = None,
    ) -> Path:
        authorization_mode = AgentHandoffProvider._require_preparation_authority(request)
        if authorization_mode == "PRODUCT" and request.config.get("mission_id") is not None:
            raise PermissionError("PRODUCT_AUTHORIZATION_MUST_NOT_HAVE_MISSION_ID")
        directory.mkdir(parents=True, exist_ok=True)
        artifacts = [
            {
                "artifact_kind": item.artifact_kind,
                "artifact_id": item.artifact_id,
                "artifact_checksum": file_checksum(item.path),
                "content": item.path.read_text(encoding="utf-8"),
            }
            for item in request.input_artifacts
        ]
        package = {
            "handoff_id": run_id,
            "capability_id": request.capability_id,
            "episode_id": request.episode_id,
            "skill_id": request.skill_id,
            "skill_version": request.skill_version,
            "skill_checksum": skill_checksum(),
            "input_manifest_checksum": manifest_checksum,
            "input_manifest": build_input_manifest(request.episode_id, artifacts),
            "output_schema": request.output_schema,
            "prompt": request.config.get("prompt", ""),
            "expected_provider_or_agent": request.config.get("expected_provider_or_agent"),
            "execution_family": request.execution_family or request.config.get("execution_family"),
            "execution_profile": request.execution_profile,
            "selection_mode": request.config.get("selection_mode") or ("EXECUTOR_MANAGED" if (request.execution_family or request.config.get("execution_family")) == "AGENT_HARNESS" else None),
            "profile_binding": request.config.get("profile_binding") or ("EXECUTOR_MANAGED" if (request.execution_family or request.config.get("execution_family")) == "AGENT_HARNESS" else request.execution_profile),
            "execution_route": request.execution_route,
            "execution_interface": request.config.get("execution_interface"),
            "execution_mode": request.execution_mode,
            **({"authorization_mode": authorization_mode} if request.config.get("authorization_mode") else {}),
            **(
                {
                    "authorization_id": request.config["authorization_id"],
                    "authorization_checksum": request.config["authorization_checksum"],
                }
                if authorization_mode == "PRODUCT" and request.config.get("authorization_id") and request.config.get("authorization_checksum")
                else {}
            ),
            "model_override": None
            if (request.execution_family or request.config.get("execution_family")) == "AGENT_HARNESS"
            else request.model,
            "reasoning_effort": request.reasoning_effort,
            "artifacts": artifacts,
            **({"completion_gate": completion_gate.to_dict()} if completion_gate is not None else {}),
            **({"mission_id": request.config["mission_id"]} if authorization_mode == "MISSION" and request.config.get("mission_id") else {}),
            **({"mission_authorization_path": request.config["mission_authorization_path"]} if request.config.get("mission_authorization_path") else {}),
            **({"mission_contract_path": request.config["mission_contract_path"]} if request.config.get("mission_contract_path") else {}),
            **({"mission_repo_root": str(Path(request.config["mission_repo_root"]).resolve())} if request.config.get("mission_repo_root") else {}),
            **({"stage": request.config["stage"]} if request.config.get("stage") else {}),
            **({"role": request.role} if request.role else {}),
            **({"expected_return": request.config["expected_return"]} if request.config.get("expected_return") else {}),
            **({"prompt_id": request.config["prompt_id"]} if request.config.get("prompt_id") else {}),
            **({"prompt_version": request.config["prompt_version"]} if request.config.get("prompt_version") else {}),
            **({"prompt_checksum": request.config["prompt_checksum"]} if request.config.get("prompt_checksum") else {}),
            **({"prompt_input_checksum": request.config["prompt_input_checksum"]} if request.config.get("prompt_input_checksum") else {}),
            **({"mission_convergence": request.config["_mission_convergence"]} if request.config.get("_mission_convergence") else {}),
            **({"strategic_return": request.config["strategic_return"]} if "strategic_return" in request.config else {}),
        }
        controls = request.config.get("execution_controls")
        if controls is not None:
            if not isinstance(controls, dict):
                raise ValueError("execution_controls inválidos")
            package["execution_controls"] = json.loads(json.dumps(controls, ensure_ascii=False))
            package["execution_controls_checksum"] = checksum(canonical_json(package["execution_controls"]))
        for key in ("budget_limit", "max_iterations", "max_retries", "timeout_seconds"):
            if key in request.config:
                package[key] = request.config[key]
        package["package_checksum"] = checksum(canonical_json(package))
        path = directory / f"{run_id}.json"
        path.write_text(json.dumps(package, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return path

    @staticmethod
    def _verify_pre_handoff_authorization(request: ExecutionRequest, repo_root: Path, directory: Path) -> None:
        """Verify execution authority without requiring final mission evidence.

        A completion gate is evidence produced after a mission.  The first
        handoff instead relies on the already verified execution preflight and
        the same mission/route bindings that preflight checked.
        """
        from src.ai.registry import _VERIFIED_AUTHORIZATION_TOKEN
        from src.core.execution_preflight import _load_registered_capability

        authorization_mode = _validated_authorization_mode(request.config.get("authorization_mode"))
        if (
            request.config.get("_mission_authorization_token") is not _VERIFIED_AUTHORIZATION_TOKEN
            and authorization_mode != "PRODUCT"
        ):
            raise PermissionError("MISSION_AUTHORIZATION_REQUIRED_FOR_HANDOFF")
        if authorization_mode == "PRODUCT":
            from src.core.product_authorization import resolve_product_authorization

            try:
                relative_directory = directory.resolve().relative_to(repo_root).as_posix()
            except ValueError as exc:
                raise PermissionError("HANDOFF_PATH_OUTSIDE_REPOSITORY") from exc
            authorization, _ = resolve_product_authorization(
                repo_root,
                capability_id=str(request.capability_id),
                role_id=str(request.role),
                execution_family=str(request.execution_family or request.config.get("execution_family") or ""),
                execution_route=str(request.execution_route or ""),
                execution_profile_id=request.execution_profile,
                execution_interface=str(request.config.get("execution_interface") or ""),
                path=relative_directory + "/",
            )
            if request.config.get("authorization_id") != authorization.authorization_id or request.config.get("authorization_checksum") != authorization.authorization_checksum:
                raise PermissionError("PRODUCT_AUTHORIZATION_REQUEST_STALE")
            return
        authorization_path = request.config.get("mission_authorization_path")
        contract_path = request.config.get("mission_contract_path")
        if not authorization_path or not contract_path:
            raise PermissionError("MISSION_AUTHORIZATION_REQUIRED: handoff bindings are incomplete")
        authorization_file = Path(str(authorization_path))
        contract_file = Path(str(contract_path))
        if authorization_file.is_absolute() or ".." in authorization_file.parts:
            raise PermissionError("MISSION_AUTHORIZATION_PATH_OUTSIDE_REPOSITORY")
        if contract_file.is_absolute() or ".." in contract_file.parts:
            raise PermissionError("MISSION_CONTRACT_PATH_OUTSIDE_REPOSITORY")
        authorization_file = (repo_root / authorization_file).resolve(strict=True)
        contract_file = (repo_root / contract_file).resolve(strict=True)
        authorization_file.relative_to(repo_root)
        contract_file.relative_to(repo_root)
        contract = load_mission_contract(contract_file)
        authorization = load_mission_authorization(authorization_file)
        if contract.mission_id != authorization.mission_id:
            raise PermissionError("MISSION_CONTRACT_AUTHORIZATION_MISMATCH")
        authorization.verify_controlled_validation_contract(contract)
        expected_authorization_ref = authorization_file.relative_to(repo_root).as_posix()
        if contract.mission_authorization_path != expected_authorization_ref:
            raise PermissionError("MISSION_CONTRACT_AUTHORIZATION_PATH_MISMATCH")
        capability = _load_registered_capability(repo_root, request.capability_id)
        authorization.verify(
            repo_root,
            capability_id=str(request.capability_id),
            role_id=str(request.role),
            operation=str(request.config.get("mission_operation") or "EXECUTE_CAPABILITY"),
            execution_mode=str(request.execution_mode),
            execution_route=str(request.execution_route or "") or None,
            execution_family=str(request.execution_family or request.config.get("execution_family") or "") or None,
            execution_interface=str(request.config.get("execution_interface") or "") or None,
            required_material_decision_ref=capability.get("material_decision_ref") if capability else None,
        )

    @staticmethod
    def _verify_external_preparation_authorization(request: ExecutionRequest, repo_root: Path, directory: Path) -> None:
        """Verify a B4 handoff scope without pretending execution was resolved.

        This path is deliberately narrower than ``prepare``: it accepts only
        the neutral AGENT_HARNESS transport and never resolves a provider,
        model, runtime, or execution profile.  The mission authorization and
        the package directory are still checked against the live repository.
        """
        from src.core.execution_preflight import _load_registered_capability

        authorization_mode = _validated_authorization_mode(request.config.get("authorization_mode"))
        if (
            request.execution_mode != "REAL"
            or request.execution_family != "AGENT_HARNESS"
            or request.execution_route != "agent_harness"
            or any((request.provider if request.provider not in (None, "agent_handoff") else None, request.model, request.executor, request.execution_profile, request.run_configuration))
        ):
            raise PermissionError("EXTERNAL_HANDOFF_REQUIRES_NEUTRAL_AGENT_HARNESS_BOUNDARY")
        if authorization_mode == "PRODUCT":
            from src.core.product_authorization import resolve_product_authorization

            try:
                relative_directory = directory.resolve().relative_to(repo_root).as_posix()
            except ValueError as exc:
                raise PermissionError("HANDOFF_PATH_OUTSIDE_REPOSITORY") from exc
            authorization, _ = resolve_product_authorization(
                repo_root,
                capability_id=str(request.capability_id),
                role_id=str(request.role),
                execution_family=str(request.execution_family),
                execution_route=str(request.execution_route),
                execution_profile_id=request.execution_profile,
                execution_interface=str(request.config.get("execution_interface") or ""),
                path=relative_directory + "/",
            )
            if request.config.get("authorization_id") != authorization.authorization_id or request.config.get("authorization_checksum") != authorization.authorization_checksum:
                raise PermissionError("PRODUCT_AUTHORIZATION_REQUEST_STALE")
            return
        authorization_path = request.config.get("mission_authorization_path")
        contract_path = request.config.get("mission_contract_path")
        if not authorization_path or not contract_path:
            raise PermissionError("MISSION_AUTHORIZATION_REQUIRED: handoff bindings are incomplete")
        authorization_file = Path(str(authorization_path))
        contract_file = Path(str(contract_path))
        if authorization_file.is_absolute() or ".." in authorization_file.parts:
            raise PermissionError("MISSION_AUTHORIZATION_PATH_OUTSIDE_REPOSITORY")
        if contract_file.is_absolute() or ".." in contract_file.parts:
            raise PermissionError("MISSION_CONTRACT_PATH_OUTSIDE_REPOSITORY")
        authorization_file = (repo_root / authorization_file).resolve(strict=True)
        contract_file = (repo_root / contract_file).resolve(strict=True)
        authorization_file.relative_to(repo_root)
        contract_file.relative_to(repo_root)
        contract = load_mission_contract(contract_file)
        authorization = load_mission_authorization(authorization_file)
        if contract.mission_id != authorization.mission_id:
            raise PermissionError("MISSION_CONTRACT_AUTHORIZATION_MISMATCH")
        authorization.verify_controlled_validation_contract(contract)
        capability = _load_registered_capability(repo_root, request.capability_id)
        if capability is None:
            raise PermissionError("CAPABILITY_UNREGISTERED:" + str(request.capability_id))
        authorization.verify(
            repo_root,
            capability_id=str(request.capability_id),
            role_id=str(request.role),
            operation=str(request.config.get("mission_operation") or "EXECUTE_CAPABILITY"),
            execution_mode=str(request.execution_mode),
            execution_route=str(request.execution_route),
            execution_family=str(request.execution_family),
            execution_interface=str(request.config.get("execution_interface") or "") or None,
            required_material_decision_ref=capability.get("material_decision_ref") if capability else None,
        )
        try:
            relative_directory = directory.resolve().relative_to(repo_root).as_posix()
        except ValueError as exc:
            raise PermissionError("HANDOFF_PATH_OUTSIDE_REPOSITORY") from exc
        authorization.verify(
            repo_root,
            capability_id=str(request.capability_id),
            role_id=str(request.role),
            operation=str(request.config.get("mission_operation") or "EXECUTE_CAPABILITY"),
            path=relative_directory.rstrip("/") + "/",
            execution_mode=str(request.execution_mode),
            execution_route=str(request.execution_route),
            execution_family=str(request.execution_family),
            execution_interface=str(request.config.get("execution_interface") or "") or None,
            required_material_decision_ref=capability.get("material_decision_ref") if capability else None,
        )
    def prepare(self, request: ExecutionRequest, manifest_checksum: str, run_id: str) -> Path:
        # Explicit runtime selections must arrive with the
        # resolver-owned route object.  A mutable request flag is diagnostic
        # only and cannot authorize preparation by itself.
        if request.execution_profile or request.execution_family or request.run_configuration is not None:
            from src.ai.runtime_profiles import READY, ResolvedExecutionRoute, _VERIFIED_ROUTE_TOKEN

            route = request.resolved_route
            if (
                not isinstance(route, ResolvedExecutionRoute)
                or route.status != READY
                or request.resolved_route_token is not _VERIFIED_ROUTE_TOKEN
            ):
                raise PermissionError("RUNTIME_CONFIGURATION_NOT_RESOLVED_BEFORE_HANDOFF")
            if (
                route.execution_profile != request.execution_profile
                or route.execution_family != (request.execution_family or request.config.get("execution_family"))
                or route.execution_route != request.execution_route
                or route.model != (request.model or "")
                or route.executor != (request.executor or "")
            ):
                raise PermissionError("RUNTIME_CONFIGURATION_RESOLUTION_BINDING_MISMATCH")
        gate_path = request.config.get("completion_gate_result_path")
        contract_path = request.config.get("mission_contract_path")
        repo_root = request.config.get("mission_repo_root")
        if not contract_path or not repo_root:
            raise PermissionError(
                "MISSION_COMPLETION_GATE_REQUIRED: handoff requires gate result, mission contract and repository root"
            )
        directory = self._resolve_directory(request, Path(repo_root).resolve())
        if gate_path:
            contract_file = Path(str(contract_path))
            if not contract_file.is_absolute():
                contract_file = Path(repo_root).resolve() / contract_file
            completion_gate = verify_completion_gate_for_repository(gate_path, contract_file, repo_root)
        else:
            self._verify_pre_handoff_authorization(request, Path(repo_root).resolve(), directory)
            completion_gate = None
        return self._write_package(request, manifest_checksum, run_id, directory, completion_gate)

    def prepare_external(self, request: ExecutionRequest, manifest_checksum: str, run_id: str) -> Path:
        """Prepare one neutral external cognitive task before runtime resolution."""
        repo_root = Path(str(request.config.get("mission_repo_root") or request.config.get("repository_root") or Path.cwd())).resolve()
        directory = self._resolve_directory(request, repo_root)
        self._verify_external_preparation_authorization(request, repo_root, directory)
        return self._write_package(request, manifest_checksum, run_id, directory)

    def import_result(
        self,
        package_path: Path,
        result_path: Path,
        *,
        historical_checkpoint: bool = False,
    ) -> dict[str, Any]:
        """Import a result, optionally as an already-committed checkpoint.

        ``historical_checkpoint`` skips only authorization of a new
        execution. Package, result, schema, checksum, and binding validation
        remain mandatory; the caller must establish durable checkpoint
        evidence before using this mode.
        """
        package = json.loads(package_path.read_text(encoding="utf-8"))
        payload = json.loads(result_path.read_text(encoding="utf-8"))
        content = payload.get("output")
        expected_checksum = package.get("package_checksum")
        package_without_checksum = {key: value for key, value in package.items() if key != "package_checksum"}
        if expected_checksum != checksum(canonical_json(package_without_checksum)):
            raise ValueError("checksum incorrecto en paquete de handoff")
        if package.get("output_schema") in {
            "topic_belonging_cognitive_proposal",
            "topic_belonging_cognitive_assessment",
            "topic_belonging_cognitive_decision",
        }:
            if historical_checkpoint:
                if not isinstance(content, dict):
                    raise ValueError("TOPIC_BELONGING_OUTPUT_INVALID: expected object")
            else:
                envelope_errors = validate_against_schema(payload, "external_result_envelope")
                if envelope_errors:
                    raise ValueError("EXTERNAL_RESULT_ENVELOPE_INVALID: " + " | ".join(envelope_errors))
        try:
            if package.get("completion_gate") is not None:
                load_verified_completion_gate_from_payload(package.get("completion_gate"))
        except PermissionError as exc:
            raise PermissionError(str(exc)) from exc
        authorization_mode = _validated_authorization_mode(package.get("authorization_mode"))
        authority_identity_field = "authorization_id" if authorization_mode == "PRODUCT" else "mission_id"
        authority_identity = package.get(authority_identity_field)
        if not str(authority_identity or "").strip():
            raise ValueError(f"resultado importado requiere {authority_identity_field}")
        if authority_identity is not None:
            if not historical_checkpoint:
                self._verify_import_authorization(package, package_path)
            # Research V2 stages are coordinator-owned.  The package role and
            # stage are validated against the pending coordinator checkpoint
            # by the application boundary; this transport provider must not
            # maintain a parallel stage-to-role workflow table.
            is_research_v2 = package.get("capability_id") == "EXTEND_01_RESEARCH_V2_REAL_E2E"
            declared_stage = str(package.get("stage") or "").strip()
            if not is_research_v2 and declared_stage:
                expected_role = {
                    "ENRICHMENT": "CHANNEL_INTELLIGENCE_PRODUCER",
                    "PRODUCER": "CHANNEL_INTELLIGENCE_PRODUCER",
                    "REVIEWER": "CHANNEL_INTELLIGENCE_REVIEWER",
                    "PLAN015_VIEWER_JOURNEY": "NARRATIVE_ARCHITECTURE",
                    "PLAN015_OPENING_DESIGN": "NARRATIVE_ARCHITECTURE",
                    "PLAN015_CLOSING_DESIGN": "NARRATIVE_ARCHITECTURE",
                    "PLAN015_NARRATIVE_PLAN": "NARRATIVE_ARCHITECTURE",
                    "PLAN015_SCRIPT_DRAFT": "WRITING",
                    "PLAN015_EDITED_SCRIPT": "EDITOR",
                    "PLAN015_EDITORIAL_EDIT_REPORT": "EDITOR",
                    "PLAN015_FINAL_EDITORIAL_AUDIT": "FINAL_EDITORIAL_AUDITOR",
                }.get(declared_stage)
                if expected_role is None:
                    raise ValueError("stage de handoff desconocida")
                if package.get("role") != expected_role:
                    raise ValueError("role no coincide con la stage esperada")
            if is_research_v2:
                controls = package.get("execution_controls")
                if not isinstance(controls, dict):
                    raise ValueError("execution_controls ausentes en handoff Research")
                if package.get("execution_controls_checksum") != checksum(canonical_json(controls)):
                    raise ValueError("checksum incorrecto en execution_controls")
                if any(package.get(key) != controls.get(key) for key in ("budget_limit", "max_iterations", "max_retries", "timeout_seconds")):
                    raise ValueError("execution_controls no coinciden con el paquete")
                for key, minimum, inclusive in (("budget_limit", 0, False), ("max_iterations", 1, True), ("max_retries", 0, True), ("timeout_seconds", 1, False)):
                    value = controls.get(key)
                    invalid_limit = (
                        not isinstance(value, (int, float))
                        or isinstance(value, bool)
                        or ((value < minimum) if inclusive else (value <= minimum))
                    )
                    if invalid_limit:
                        raise ValueError(f"execution_controls inválidos en {key}")
                if controls.get("unbounded_execution") is not False:
                    raise ValueError("execution_controls permiten ejecución indefinida")
                if not isinstance(content, (dict, list)) or (isinstance(content, list) and not content):
                    raise ValueError("RESEARCH_EXTERNAL_COGNITIVE_OUTPUT_INVALID: expected non-empty object or list")
                # ResearchPlanProposal is itself the cognitive contract.  The
                # other Research V2 responses are projected by Software before
                # their canonical artifact schemas are evaluated; validating
                # those final schemas here would require the external side to
                # fabricate Software-owned IDs, timestamps and provenance.
                if package.get("output_schema") == "research_plan_proposal":
                    output_errors = validate_against_schema(content, "research_plan_proposal")
                    if output_errors:
                        raise ValueError("RESEARCH_PLAN_PROPOSAL_INVALID: " + " | ".join(output_errors))
            elif package.get("capability_id") == "TOPIC_BELONGING_ASSESSMENT":
                output_schema = str(package.get("output_schema") or "")
                if historical_checkpoint:
                    if not isinstance(content, dict):
                        raise ValueError("TOPIC_BELONGING_OUTPUT_INVALID: expected object")
                else:
                    output_errors = validate_against_schema(content, output_schema)
                    if output_errors:
                        raise ValueError("TOPIC_BELONGING_OUTPUT_INVALID: " + " | ".join(output_errors))
            binding_fields = [authority_identity_field, "episode_id", "capability_id", "stage", "role"]
            if "authorization_mode" in package:
                binding_fields.insert(1, "authorization_mode")
            for field in binding_fields:
                # Older MISSION results were valid without echoing the now
                # explicit mode.  Preserve that compatibility only for the
                # implicit MISSION default; PRODUCT remains explicit.
                if (
                    field == "authorization_mode"
                    and package.get("authorization_mode") == "MISSION"
                    and field not in payload
                ):
                    continue
                if payload.get(field) != package.get(field):
                    raise ValueError(f"resultado importado no corresponde en {field}")
            if not payload.get("result_run_id"):
                raise ValueError("resultado importado requiere result_run_id")
            provenance = payload.get("provenance")
            if provenance is not None and not isinstance(provenance, dict):
                raise ValueError("provenance inválida en resultado importado")
            if str(package.get("stage") or "").startswith("PLAN015_") and (
                not isinstance(provenance, dict)
                or not str(provenance.get("executor_identity") or "").strip()
            ):
                raise ValueError("resultado PLAN015 requiere executor_identity real")
            if isinstance(provenance, dict):
                for field in (authority_identity_field, "episode_id", "capability_id", "stage", "role"):
                    if field in provenance and provenance[field] != package.get(field):
                        raise ValueError(f"provenance no corresponde en {field}")
                if (
                    not historical_checkpoint
                    and package.get("output_schema") in {
                        "topic_belonging_cognitive_proposal",
                        "topic_belonging_cognitive_assessment",
                        "topic_belonging_cognitive_decision",
                    }
                    and not str(provenance.get("executor_identity") or "").strip()
                ):
                    raise ValueError("resultado importado requiere executor_identity real")
        if (payload.get("handoff_id") != package["handoff_id"] or payload.get("package_checksum") != expected_checksum
                or payload.get("input_manifest_checksum") != package["input_manifest_checksum"]
                or payload.get("skill_id") != package["skill_id"] or payload.get("skill_version") != package["skill_version"]):
            raise ValueError("resultado importado no corresponde al paquete de handoff")
        declared_return = package.get("strategic_return")
        if declared_return is not None and (not isinstance(content, dict) or content.get("strategic_return") != declared_return):
            raise ValueError("strategic_return no coincide con el handoff canónico")
        encoded = json.dumps(content, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
        if payload.get("output_checksum") != checksum(encoded):
            raise ValueError("checksum incorrecto en resultado importado")
        return content

    @staticmethod
    def _verify_import_authorization(package: dict[str, Any], package_path: Path | None = None) -> None:
        from src.core.execution_preflight import _load_registered_capability

        repo_root = Path(str(package.get("mission_repo_root") or ".")).resolve()
        authorization_mode = _validated_authorization_mode(package.get("authorization_mode"))
        if authorization_mode == "PRODUCT":
            from src.core.product_authorization import resolve_product_authorization

            if package_path is None:
                raise PermissionError("PRODUCT_AUTHORIZATION_IMPORT_PACKAGE_PATH_REQUIRED")
            try:
                handoff_directory = package_path.resolve().parent.relative_to(repo_root).as_posix()
            except ValueError as exc:
                raise PermissionError("PRODUCT_AUTHORIZATION_HANDOFF_PATH_OUTSIDE_REPOSITORY") from exc
            authorization, _ = resolve_product_authorization(
                repo_root,
                capability_id=str(package.get("capability_id") or ""),
                role_id=str(package.get("role") or ""),
                execution_family=str(package.get("execution_family") or ""),
                execution_route=str(package.get("execution_route") or ""),
                execution_profile_id=package.get("execution_profile"),
                execution_interface=str(package.get("execution_interface") or ""),
                path=handoff_directory + "/",
            )
            if (
                package.get("authorization_id") != authorization.authorization_id
                or package.get("authorization_checksum") != authorization.authorization_checksum
                or package.get("mission_id") is not None
            ):
                raise PermissionError("PRODUCT_AUTHORIZATION_REQUEST_STALE")
            return
        authorization_ref = str(package.get("mission_authorization_path") or "")
        contract_ref = str(package.get("mission_contract_path") or "")
        if not authorization_ref or not contract_ref:
            raise PermissionError("MISSION_AUTHORIZATION_REQUIRED: imported handoff lacks mission bindings")
        authorization_path = (repo_root / authorization_ref).resolve(strict=True)
        contract_path = (repo_root / contract_ref).resolve(strict=True)
        authorization_path.relative_to(repo_root)
        contract_path.relative_to(repo_root)
        authorization = load_mission_authorization(authorization_path)
        contract = load_mission_contract(contract_path)
        if authorization.mission_id != package.get("mission_id") or contract.mission_id != package.get("mission_id"):
            raise PermissionError("MISSION_SCOPE_AUTHORIZATION_MISMATCH: imported result")
        authorization.verify_controlled_validation_contract(contract)
        capability = _load_registered_capability(repo_root, str(package.get("capability_id")))
        authorization.verify(
            repo_root,
            capability_id=str(package.get("capability_id")),
            role_id=str(package.get("role")),
            operation="EXECUTE_CAPABILITY",
            execution_mode=str(package.get("execution_mode") or "REAL"),
            execution_route=str(package.get("execution_route") or "") or None,
            execution_family=str(package.get("execution_family") or "") or None,
            execution_interface=str(package.get("execution_interface") or "TOPIC_BELONGING_TERMINAL"),
            required_material_decision_ref=capability.get("material_decision_ref") if capability else None,
        )
