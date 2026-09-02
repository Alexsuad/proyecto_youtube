"""Generic role prompt, context, and output-contract assembly for real runs."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from src.core.contract_validation import load_schema
from src.core.editorial_profile_registry import load_active_profile_authority
from src.core.prompt_resolver import PromptResolutionError, resolve_prompt
from src.core.version_manifest import compute_checksum

ROOT = Path(__file__).resolve().parents[2]

SCRIPT_PRODUCT_PRODUCER_REQUIRED_INPUTS = (
    "active_editorial_profile_reference",
    "episode_brief",
    "research_pack",
    "source_access_and_evidence_report",
    "provisional_thesis",
    "semantic_sufficiency_audit",
    "claims_ledger",
    "approved_material_candidates",
    "excluded_claims",
    "limited_claims",
    "mandatory_disclosures",
)
SCRIPT_PRODUCT_AUDITOR_REQUIRED_INPUTS = (
    "b5_i1_package",
    "narrative_human_analyses",
    "material_curation",
    "refined_thesis",
    "editorial_script_promise",
    "producer_run_reference",
    "artifact_checksums",
)

YOUTUBE_ADAPTATION_PRODUCER_REQUIRED_INPUTS = (
    "active_editorial_profile_reference",
    "episode_brief",
    "refined_thesis",
    "editorial_script_promise",
    "evidence_or_claims_reference",
    "claims_ledger",
    "evidence_report",
)
YOUTUBE_ADAPTATION_AUDITOR_REQUIRED_INPUTS = (
    "youtube_adaptation_b5_i2_package",
    "producer_run_reference",
    "active_editorial_profile_reference",
    "refined_thesis",
    "claims_ledger",
    "evidence_report",
)
CHANNEL_INTELLIGENCE_ENRICHMENT_REQUIRED_INPUTS = (
    "EditorialIntakeHandoff",
    "active_editorial_profile",
    "initial_evidence",
)
CHANNEL_INTELLIGENCE_PRODUCER_REQUIRED_INPUTS = (
    "TopicBelongingInput",
    "active_editorial_profile",
    "initial_evidence",
)
CHANNEL_INTELLIGENCE_REVIEWER_REQUIRED_INPUTS = (
    "TopicBelongingInput",
    "TopicBelongingAssessment",
    "active_editorial_profile",
)
ROLE_REQUIRED_INPUTS = {
    "SCRIPT_PRODUCT_PRODUCER": SCRIPT_PRODUCT_PRODUCER_REQUIRED_INPUTS,
    "SCRIPT_PRODUCT_AUDITOR": SCRIPT_PRODUCT_AUDITOR_REQUIRED_INPUTS,
    "YOUTUBE_ADAPTATION_PRODUCER": YOUTUBE_ADAPTATION_PRODUCER_REQUIRED_INPUTS,
    "YOUTUBE_ADAPTATION_AUDITOR": YOUTUBE_ADAPTATION_AUDITOR_REQUIRED_INPUTS,
    "CHANNEL_INTELLIGENCE_PRODUCER": CHANNEL_INTELLIGENCE_PRODUCER_REQUIRED_INPUTS,
    "CHANNEL_INTELLIGENCE_REVIEWER": CHANNEL_INTELLIGENCE_REVIEWER_REQUIRED_INPUTS,
}
ROLE_ALLOWED_OUTPUT_SCHEMAS = {
    "SCRIPT_PRODUCT_PRODUCER": {
        "execution_smoke_report",
        "narrative_human_analysis",
        "material_curation",
        "refined_thesis",
        "editorial_script_promise",
    },
    "SCRIPT_PRODUCT_AUDITOR": {
        "execution_smoke_report",
        "b5_i2_semantic_sufficiency_audit",
    },
    "YOUTUBE_ADAPTATION_PRODUCER": {
        "execution_smoke_report",
        "youtube_adaptation_b5_i2_package",
        "early_packaging_hypothesis",
    },
    "YOUTUBE_ADAPTATION_AUDITOR": {
        "execution_smoke_report",
        "youtube_adaptation_review",
    },
    "CHANNEL_INTELLIGENCE_PRODUCER": {
        "execution_smoke_report",
        "topic_belonging_cognitive_proposal",
        "topic_belonging_input",
        "topic_belonging_assessment",
    },
    "CHANNEL_INTELLIGENCE_REVIEWER": {
        "execution_smoke_report",
        "topic_belonging_decision",
    },
}


class RoleExecutionContractError(ValueError):
    """A deterministic pre-invocation failure for a role execution."""


def _canonical_checksum(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _active_compiled_profile() -> dict[str, Any] | None:
    pointer_path = ROOT / "config" / "active_editorial_profile.json"
    registry_path = ROOT / "config" / "editorial_profile_registry.json"
    if not pointer_path.is_file() or not registry_path.is_file():
        raise RoleExecutionContractError("INPUT_CONTRACT_INVALID: active editorial profile authority missing")
    try:
        pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        load_active_profile_authority()
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise RoleExecutionContractError("INPUT_CONTRACT_INVALID: active editorial profile authority invalid") from exc
    key = registry.get("active_profile_key")
    entry = registry.get("profiles", {}).get(key, {})
    profile_path = entry.get("compiled_profile_path")
    if not profile_path:
        raise RoleExecutionContractError("INPUT_CONTRACT_INVALID: compiled active profile path missing")
    resolved = ROOT / profile_path
    try:
        compiled_text = resolved.read_text(encoding="utf-8")
        compiled_profile = json.loads(compiled_text)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RoleExecutionContractError("INPUT_CONTRACT_INVALID: compiled active profile invalid") from exc
    if not compiled_text.strip() or not isinstance(compiled_profile, dict):
        raise RoleExecutionContractError("INPUT_CONTRACT_INVALID: compiled active profile missing")
    active_checksum = str(pointer.get("profile_checksum") or "")
    if (
        compiled_profile.get("checksum") != active_checksum
        or not isinstance(compiled_profile.get("profile"), dict)
        or compute_checksum(compiled_profile["profile"]) != active_checksum
    ):
        raise RoleExecutionContractError("INPUT_CONTRACT_INVALID: compiled active profile checksum mismatch")
    return {
        "profile_id": pointer.get("ACTIVE_PROFILE_ID"),
        "profile_version": pointer.get("ACTIVE_PROFILE_VERSION"),
        "profile_checksum": pointer.get("profile_checksum"),
        "compiled_profile_path": profile_path,
        "compiled_profile": compiled_profile,
    }


def _validate_role_payload(
    role_id: str,
    input_payload: dict[str, Any],
    output_schema: str,
    runtime_values: dict[str, Any] | None = None,
) -> None:
    required = ROLE_REQUIRED_INPUTS.get(role_id, ())
    if role_id == "CHANNEL_INTELLIGENCE_PRODUCER":
        stage = str((runtime_values or {}).get("stage") or "").upper()
        required = (
            CHANNEL_INTELLIGENCE_ENRICHMENT_REQUIRED_INPUTS
            if stage == "ENRICHMENT" or output_schema in {"topic_belonging_input", "topic_belonging_cognitive_proposal"}
            else CHANNEL_INTELLIGENCE_PRODUCER_REQUIRED_INPUTS
        )
    missing = [key for key in required if key not in input_payload]
    if missing:
        raise RoleExecutionContractError(
            f"INPUT_CONTRACT_INVALID: {role_id} missing required inputs: {', '.join(missing)}"
        )
    allowed_schemas = ROLE_ALLOWED_OUTPUT_SCHEMAS.get(role_id)
    if allowed_schemas and output_schema not in allowed_schemas:
        raise RoleExecutionContractError(
            f"OUTPUT_CONTRACT_INVALID: {role_id} cannot emit schema {output_schema}"
        )
    if role_id == "SCRIPT_PRODUCT_AUDITOR":
        artifact_checksums = input_payload.get("artifact_checksums")
        analyses = input_payload.get("narrative_human_analyses")
        if not isinstance(artifact_checksums, list) or not artifact_checksums:
            raise RoleExecutionContractError("INPUT_CONTRACT_INVALID: SCRIPT_PRODUCT_AUDITOR requires non-empty artifact_checksums")
        if not isinstance(analyses, list) or not analyses:
            raise RoleExecutionContractError("INPUT_CONTRACT_INVALID: SCRIPT_PRODUCT_AUDITOR requires non-empty narrative_human_analyses")


def existing_producer_run_compatibility(path: Path) -> str:
    if not path.exists():
        return "NOT_EVALUATED"
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("smoke_id") and payload.get("role_id") == "SCRIPT_PRODUCT_PRODUCER":
        return "INVALIDATED_BY_CONTRACT_CHANGE"
    return "PASS"


def _applicable_policies(prompt_contract: dict[str, Any]) -> list[dict[str, str]]:
    policies: list[dict[str, str]] = []
    for ref in prompt_contract.get("required_context", []):
        if not isinstance(ref, str) or not ref.endswith((".md", ".json")):
            continue
        path = ROOT / ref
        if not path.is_file():
            raise RoleExecutionContractError(f"INPUT_CONTRACT_INVALID: required context missing: {ref}")
        content = path.read_text(encoding="utf-8")
        if not content.strip():
            raise RoleExecutionContractError(f"INPUT_CONTRACT_INVALID: required context empty: {ref}")
        policies.append({"path": ref, "content": content})
    return policies


def resolve_role_execution_contract(role_id: str, output_schema: str, input_payload: Any, runtime_values: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(input_payload, dict):
        raise RoleExecutionContractError("INPUT_CONTRACT_INVALID: input payload must be a JSON object")
    _validate_role_payload(role_id, input_payload, output_schema, runtime_values)
    try:
        prompt_contract = resolve_prompt(role_id)
    except PromptResolutionError as exc:
        message = str(exc)
        category = "PROMPT_NOT_FOUND" if "Prompt file" in message or "prompt_version" in message else "ROLE_NOT_REGISTERED"
        raise RoleExecutionContractError(f"{category}: {message}") from exc
    prompt_path = ROOT / "prompts" / "roles" / role_id / f"{prompt_contract['prompt_version']}.md"
    try:
        prompt_content = prompt_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise RoleExecutionContractError(f"PROMPT_NOT_FOUND: {prompt_path}") from exc
    profile = _active_compiled_profile() if ("active_editorial_profile" in prompt_contract.get("required_inputs", []) or any("profile" in str(item).lower() for item in prompt_contract.get("required_context", []))) else None
    if "active_editorial_profile" in prompt_contract.get("required_inputs", []) and not isinstance(profile, dict):
        raise RoleExecutionContractError("INPUT_CONTRACT_INVALID: active editorial profile is required")
    schema = load_schema(output_schema)
    if output_schema in {
        "narrative_human_analysis",
        "material_curation",
        "refined_thesis",
        "editorial_script_promise",
        "b5_i2_semantic_sufficiency_audit",
        "early_packaging_hypothesis",
        "youtube_adaptation_b5_i2_package",
        "youtube_adaptation_review",
    }:
        # Reuse the runtime's canonical projection so the model receives only
        # the cognitive contract.  Software binds the omitted system fields
        # after the provider returns.
        from src.ai.execution import editorial_projection_schema

        schema = editorial_projection_schema(output_schema)
    return {
        "role_id": role_id,
        "prompt_id": prompt_contract["prompt_id"],
        "prompt_version": prompt_contract["prompt_version"],
        "prompt_checksum": hashlib.sha256(prompt_content.encode("utf-8")).hexdigest(),
        "input_payload": input_payload,
        "input_checksum": _canonical_checksum(input_payload),
        "prompt_content": prompt_content,
        "compiled_profile": profile,
        "applicable_policies": _applicable_policies(prompt_contract),
        "output_schema_name": output_schema,
        "output_schema": schema,
        "runtime_values": runtime_values,
    }


def build_model_prompt(contract: dict[str, Any]) -> str:
    payload = {
        "role_identity": {"role_id": contract["role_id"], "prompt_id": contract["prompt_id"], "prompt_version": contract["prompt_version"]},
        "functional_instructions": contract["prompt_content"],
        "input_payload": contract["input_payload"],
        "compiled_editorial_profile": contract["compiled_profile"],
        "applicable_policies": contract["applicable_policies"],
        "output_contract": {"schema_name": contract["output_schema_name"], "json_schema": contract["output_schema"]},
        "runtime_values": contract["runtime_values"],
    }
    return (
        "Return exactly one JSON object and no prose, markdown, or code fence. "
        "The object must validate against output_contract.json_schema. Use runtime_values exactly where relevant.\n"
        + json.dumps(payload, ensure_ascii=False, sort_keys=True)
    )
