"""Gate determinista para YOUTUBE_ADAPTATION en B5-I2."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from src.core.contract_validation import load_schema, validate_against_schema
from src.core.gate_result import GateResult
from src.core.gate_runtime import run_gate
from src.core.status import GateStatus

CAPABILITIES = [
    "YT_EARLY_AUDIENCE_FIT",
    "YT_VISIBLE_PROMISE",
    "YT_EARLY_PACKAGING_HYPOTHESIS",
    "YT_PROMISE_CONTENT_ALIGNMENT",
    "YT_OPENING_READINESS",
    "YT_DURATION_ENVELOPE",
    "YT_OVERPROMISE_REVIEW",
    "YT_TEXT_PLATFORM_RISK",
    "YT_SCRIPT_RIGHTS_REUSE_RISK",
]
PUBLICATION_LIMIT = {
    "B5_I3",
    "FINAL_PACKAGING",
    "PRODUCTION",
    "PUBLICATION",
    "MONETIZATION_GUARANTEE",
    "LEGAL_APPROVAL",
}
DECISION_MAP = {
    "APPROVAL": GateStatus.PASS,
    "APPROVAL_WITH_WARNINGS": GateStatus.WARN,
    "REQUEST_CHANGES": GateStatus.REQUEST_CHANGES,
    "BLOCK": GateStatus.BLOCKED,
}
REAL_PROVIDER_KIND = "REAL"
SYNTHETIC_PROVIDER_KIND = "SYNTHETIC"


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _provider_kind(run: dict[str, Any]) -> str:
    explicit = str(run.get("provider_kind") or "").strip().upper()
    if explicit == REAL_PROVIDER_KIND:
        return REAL_PROVIDER_KIND
    if explicit == SYNTHETIC_PROVIDER_KIND:
        return SYNTHETIC_PROVIDER_KIND
    return REAL_PROVIDER_KIND if str(run.get("execution_mode") or "").upper() == "REAL" else SYNTHETIC_PROVIDER_KIND


def _mitigation_present(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _list_has_content(values: Any) -> bool:
    return isinstance(values, list) and any(isinstance(item, str) and item.strip() for item in values)


GENERIC_GROUNDING_REFS = {"package", "review", "evidence", "claims", "risk summary", "rights summary", "platform risk", "rights reuse"}

def _grounding_violations(label: str, refs: Any, known_ids: set[str]) -> list[str]:
    if not isinstance(refs, list) or not refs:
        return [f"{label}.evidence_refs must contain at least one specific reference"]
    violations: list[str] = []
    for ref in refs:
        value = str(ref).strip() if isinstance(ref, str) else ""
        if not value:
            violations.append(f"{label}.evidence_refs contains an empty reference")
            continue
        if value.lower() in GENERIC_GROUNDING_REFS:
            violations.append(f"{label}.evidence_refs contains a generic reference: {value}")
            continue
        if value in known_ids:
            violations.append(f"{label}.evidence_refs contains an artifact-only reference: {value}")
            continue
        prefix, separator, target = value.partition(":")
        if separator and target in known_ids and prefix.lower() in {"claim", "citation", "evidence", "source"}:
            continue
        violations.append(f"{label}.evidence_refs is not resolvable: {value}")
    return violations

def _expected_review_decision(review: dict[str, Any]) -> str:
    capability_results = review.get("capability_results", {})
    decisions = [str(capability_results[key]["decision"]) for key in CAPABILITIES]
    if review.get("independence_check", {}).get("decision") != "PASS":
        return "BLOCK"
    if _list_has_content(review.get("blocking_reasons")):
        return "BLOCK"
    if "BLOCK" in decisions:
        return "BLOCK"
    if _list_has_content(review.get("required_changes")):
        return "REQUEST_CHANGES"
    if "REQUEST_CHANGES" in decisions:
        return "REQUEST_CHANGES"
    if "WARN" in decisions:
        return "APPROVAL_WITH_WARNINGS"
    return "APPROVAL"


def _artifact_ref(kind: str, artifact_id: str) -> str:
    return f"{kind}:{artifact_id}"


def _matching_output(run: dict[str, Any], artifact_kind: str, artifact_id: str) -> dict[str, Any] | None:
    for item in run.get("outputs", []):
        if isinstance(item, dict) and item.get("artifact_kind") == artifact_kind and item.get("artifact_id") == artifact_id:
            return item
    return None


def _actor_matches(run: dict[str, Any], actor_id: str) -> bool:
    candidates = {str(run.get("agent_id") or ""), str(run.get("role_id") or ""), str(run.get("role") or "")}
    return actor_id in {value for value in candidates if value}


def _check_run_identity(run: dict[str, Any], *, expected_agent: str, expected_role: str, label: str, fail_violations: list[str], blocked_reasons: list[str]) -> None:
    if run.get("agent_id") != expected_agent:
        fail_violations.append(f"{label}: agent_id incompatible with expected {expected_agent}")
    if run.get("role_id") != expected_role:
        fail_violations.append(f"{label}: role_id incompatible with expected {expected_role}")
    if run.get("validation_result") != "PASS":
        fail_violations.append(f"{label}: validation_result must be PASS")
    if run.get("status") != "SUCCEEDED":
        blocked_reasons.append(f"{label}: run not completed successfully")
    if str(run.get("execution_mode") or "").upper() != "REAL":
        blocked_reasons.append(f"{label}: execution_mode is not REAL")
    if _provider_kind(run) != REAL_PROVIDER_KIND:
        blocked_reasons.append(f"{label}: provider_kind is not REAL")


def _strategic_return_violations(value: Any, label: str) -> list[str]:
    if not isinstance(value, dict):
        return [f"{label} must be an object"]
    trigger_keys = set(load_schema("topic_belonging_input")["$defs"]["strategic_triggers"]["properties"])
    triggers = value.get("strategic_triggers")
    violations: list[str] = []
    if not isinstance(triggers, dict) or set(triggers) != trigger_keys or any(not isinstance(item, bool) for item in triggers.values()):
        violations.append(f"{label}.strategic_triggers must match CI strategic trigger taxonomy exactly")
        return violations
    active = any(triggers.values())
    if active:
        if value.get("return_required") is not True:
            violations.append(f"{label}.return_required must be true for an active strategic trigger")
        if value.get("target_domain") != "CHANNEL_INTELLIGENCE":
            violations.append(f"{label}.target_domain must be CHANNEL_INTELLIGENCE for an active strategic trigger")
        if not isinstance(value.get("reason"), str) or not value["reason"].strip():
            violations.append(f"{label}.reason is required for an active strategic trigger")
        if not isinstance(value.get("evidence_refs"), list) or not value["evidence_refs"]:
            violations.append(f"{label}.evidence_refs is required for an active strategic trigger")
    elif value.get("return_required") is not False or value.get("target_domain") is not None or value.get("reason") is not None or value.get("evidence_refs") != []:
        violations.append(f"{label} must explicitly declare no return when no strategic trigger is active")
    return violations


def evaluate(package_path: Path, review_path: Path, registry_path: Path, active_profile_path: Path | None = None, artifact_id: str = "YT-R3", claims_ledger: dict[str, Any] | None = None) -> GateResult:
    fail_violations: list[str] = []
    blocked_reasons: list[str] = []
    warnings: list[str] = []
    package = _read(package_path)
    review = _read(review_path)
    registry = _read(registry_path)
    active_profile = _read(active_profile_path) if active_profile_path else _read(Path("config/active_editorial_profile.json"))
    for name, payload, schema in [("producer_package", package, "youtube_adaptation_b5_i2_package"), ("auditor_review", review, "youtube_adaptation_review"), ("execution_registry", registry, "execution_provenance_registry")]:
        fail_violations.extend([f"{name}: {violation}" for violation in validate_against_schema(payload, schema)])
    expected_profile = {"profile_id": active_profile.get("ACTIVE_PROFILE_ID"), "profile_version": active_profile.get("ACTIVE_PROFILE_VERSION"), "profile_checksum": active_profile.get("profile_checksum")}
    if package.get("active_profile_reference") != expected_profile:
        fail_violations.append("package.active_profile_reference does not match active profile")
    if review.get("active_profile_reference") != expected_profile:
        fail_violations.append("review.active_profile_reference does not match active profile")
    fail_violations.extend(_strategic_return_violations(package.get("strategic_return"), "package.strategic_return"))
    fail_violations.extend(_strategic_return_violations(review.get("strategic_return"), "review.strategic_return"))
    capability_results = review.get("capability_results", {})
    input_refs = package.get("input_references") if isinstance(package.get("input_references"), dict) else {}
    immutable_refs = {name: input_refs.get(name) for name in ("refined_thesis", "claims_ledger", "evidence_report")}
    known_grounding_ids = {str(ref.get("artifact_id")) for ref in immutable_refs.values() if isinstance(ref, dict) and ref.get("artifact_id")}
    visible_promise = package.get("episode_youtube_positioning", {}).get("visible_promise", {})
    known_grounding_ids.update(str(value) for value in visible_promise.get("supporting_claims", []) if isinstance(value, str) and value.strip())
    if isinstance(claims_ledger, dict):
        known_grounding_ids.update(str(item.get("claim_id")) for item in claims_ledger.get("claims", []) if isinstance(item, dict) and item.get("claim_id"))
    for name, ref in immutable_refs.items():
        if not isinstance(ref, dict) or not ref.get("artifact_id") or not ref.get("checksum"):
            fail_violations.append(f"package.input_references.{name} must be an immutable artifact reference")
    for label, refs in (("package.preliminary_youtube_risk_review.platform_risk", package.get("preliminary_youtube_risk_review", {}).get("platform_risk", {}).get("evidence_refs")), ("package.preliminary_youtube_risk_review.rights_reuse_risk", package.get("preliminary_youtube_risk_review", {}).get("rights_reuse_risk", {}).get("evidence_refs")), ("review.platform_risk_summary", review.get("platform_risk_summary", {}).get("evidence_refs")), ("review.rights_reuse_summary", review.get("rights_reuse_summary", {}).get("evidence_refs")), ("review.capability_results.YT_TEXT_PLATFORM_RISK", capability_results.get("YT_TEXT_PLATFORM_RISK", {}).get("evidence_refs")), ("review.capability_results.YT_SCRIPT_RIGHTS_REUSE_RISK", capability_results.get("YT_SCRIPT_RIGHTS_REUSE_RISK", {}).get("evidence_refs"))):
        fail_violations.extend(_grounding_violations(label, refs, known_grounding_ids))
    for summary_key, capability_key in (("platform_risk_summary", "YT_TEXT_PLATFORM_RISK"), ("rights_reuse_summary", "YT_SCRIPT_RIGHTS_REUSE_RISK")):
        summary_refs = set(review.get(summary_key, {}).get("evidence_refs", []))
        capability_refs = set(capability_results.get(capability_key, {}).get("evidence_refs", []))
        if summary_refs != capability_refs:
            fail_violations.append(f"{summary_key}.evidence_refs must align with {capability_key}.evidence_refs")
    if package.get("strategic_return") != review.get("strategic_return"):
        fail_violations.append("package.strategic_return does not match review.strategic_return")
    package_checksum = _checksum(package_path)
    review_checksum = _checksum(review_path)
    package_id = str(package.get("package_id") or "")
    review_id = str(review.get("review_id") or "")
    producer_run_id = str(package.get("producer_run_id") or "")
    auditor_run_id = str(review.get("auditor_run_id") or "")
    package_ref = _artifact_ref("youtube_adaptation_b5_i2_package", package_id)
    review_ref = _artifact_ref("youtube_adaptation_review", review_id)
    if review.get("artifact_id") != package_id:
        fail_violations.append("review.artifact_id does not match package.package_id")
    if review.get("artifact_checksum") != package_checksum:
        fail_violations.append("review.artifact_checksum does not match the real package checksum")
    if review.get("producer_run_id") != producer_run_id:
        fail_violations.append("review.producer_run_id does not match package.producer_run_id")
    capability_results = review.get("capability_results", {})
    present_capabilities = set(capability_results.keys()) if isinstance(capability_results, dict) else set()
    if present_capabilities != set(CAPABILITIES):
        fail_violations.append("capability_results does not contain the exact nine required capabilities")
    indep = review.get("independence_check", {})
    if indep.get("producer_run_id") != producer_run_id or indep.get("auditor_run_id") != auditor_run_id:
        fail_violations.append("independence_check run ids do not match review/package run ids")
    if review.get("overpromise_decision", {}).get("decision") != capability_results.get("YT_OVERPROMISE_REVIEW", {}).get("decision"):
        fail_violations.append("overpromise_decision does not match capability_results.YT_OVERPROMISE_REVIEW")
    if review.get("opening_readiness", {}).get("decision") != capability_results.get("YT_OPENING_READINESS", {}).get("decision"):
        fail_violations.append("opening_readiness does not match capability_results.YT_OPENING_READINESS")
    if review.get("duration_assessment", {}).get("decision") != capability_results.get("YT_DURATION_ENVELOPE", {}).get("decision"):
        fail_violations.append("duration_assessment does not match capability_results.YT_DURATION_ENVELOPE")
    platform = review.get("platform_risk_summary", {})
    platform_decision = capability_results.get("YT_TEXT_PLATFORM_RISK", {}).get("decision")
    if platform.get("severity") == "HIGH":
        if platform_decision == "PASS":
            fail_violations.append("platform high risk cannot remain PASS")
        if not _list_has_content(platform.get("mitigations")) and platform_decision != "BLOCK":
            fail_violations.append("platform high risk without mitigation must BLOCK")
    if platform.get("severity") == "UNRESOLVED":
        if platform_decision == "PASS":
            fail_violations.append("platform unresolved risk cannot remain PASS")
        if platform_decision == "WARN" and not (_mitigation_present(capability_results.get("YT_TEXT_PLATFORM_RISK", {}).get("mitigation_or_pending")) or _list_has_content(platform.get("mitigations")) or _list_has_content(platform.get("uncertainties"))):
            fail_violations.append("platform unresolved WARN requires mitigation or pending trace")
    rights = review.get("rights_reuse_summary", {})
    rights_decision = capability_results.get("YT_SCRIPT_RIGHTS_REUSE_RISK", {}).get("decision")
    if rights.get("severity") == "HIGH":
        if rights_decision == "PASS":
            fail_violations.append("rights high risk cannot remain PASS")
        if not _list_has_content(rights.get("mitigations")) and rights_decision != "BLOCK":
            fail_violations.append("rights high risk without mitigation must BLOCK")
    if rights.get("severity") == "UNRESOLVED":
        if rights_decision == "PASS":
            fail_violations.append("rights unresolved risk cannot remain PASS")
        if rights_decision == "WARN" and not (_mitigation_present(capability_results.get("YT_SCRIPT_RIGHTS_REUSE_RISK", {}).get("mitigation_or_pending")) or _list_has_content(rights.get("mitigations")) or _list_has_content(rights.get("unresolved_items"))):
            fail_violations.append("rights unresolved WARN requires mitigation or pending trace")
    if _list_has_content(review.get("blocking_reasons")) and review.get("decision") != "BLOCK":
        fail_violations.append("blocking_reasons require global decision BLOCK")
    if _list_has_content(review.get("required_changes")) and review.get("decision") not in {"REQUEST_CHANGES", "BLOCK"}:
        fail_violations.append("required_changes require global decision REQUEST_CHANGES or BLOCK")
    expected_decision = _expected_review_decision(review) if present_capabilities == set(CAPABILITIES) else None
    if expected_decision and review.get("decision") != expected_decision:
        fail_violations.append(f"global decision inconsistent: expected {expected_decision} but received {review.get('decision')}")
    publication = set(review.get("publication_limit", {}).get("DOES_NOT_AUTHORIZE", []))
    if publication != PUBLICATION_LIMIT:
        fail_violations.append("publication_limit does not contain the exact forbidden set")
    runs = {run.get("run_id"): run for run in registry.get("runs", []) if isinstance(run, dict) and run.get("run_id")}
    producer_run = runs.get(producer_run_id)
    auditor_run = runs.get(auditor_run_id)
    if not producer_run:
        blocked_reasons.append("producer provenance run is missing")
    if not auditor_run:
        blocked_reasons.append("auditor provenance run is missing")
    if producer_run:
        _check_run_identity(producer_run, expected_agent="YOUTUBE_ADAPTATION_PRODUCER", expected_role="YOUTUBE_ADAPTATION_PRODUCER", label="producer_run", fail_violations=fail_violations, blocked_reasons=blocked_reasons)
        producer_output = _matching_output(producer_run, "youtube_adaptation_b5_i2_package", package_id)
        if not producer_output:
            fail_violations.append("producer_run outputs do not contain the exact package artifact")
        else:
            if producer_output.get("checksum") != package_checksum:
                fail_violations.append("producer_run output checksum does not match the real package checksum")
            if producer_output.get("artifact_ref") != package_ref:
                fail_violations.append("producer_run output artifact_ref does not match the package ref")
        if package_ref not in producer_run.get("output_artifact_ids", []):
            fail_violations.append("producer_run output_artifact_ids does not contain the exact package ref")
        if package_checksum not in producer_run.get("output_checksums", []):
            fail_violations.append("producer_run output_checksums does not contain the real package checksum")
    if auditor_run:
        input_ids = list(auditor_run.get("input_artifact_ids", []))
        input_checksums = list(auditor_run.get("input_checksums", []))
        input_versions = list(auditor_run.get("input_versions", []))
        if len(input_ids) != len(input_checksums):
            fail_violations.append("auditor_run input_artifact_ids and input_checksums must be positional pairs")
        if input_versions and len(input_ids) != len(input_versions):
            fail_violations.append("auditor_run input_artifact_ids and input_versions must be positional pairs")
        checksum_by_id = {str(artifact_id): str(input_checksums[index]) for index, artifact_id in enumerate(input_ids) if index < len(input_checksums)}
        version_by_id = {str(artifact_id): str(input_versions[index]) for index, artifact_id in enumerate(input_ids) if index < len(input_versions)}
        for name, ref in immutable_refs.items():
            artifact_id = str(ref.get("artifact_id") or "") if isinstance(ref, dict) else ""
            checksum = str(ref.get("checksum") or "") if isinstance(ref, dict) else ""
            version = str(ref.get("version") or "") if isinstance(ref, dict) else ""
            if artifact_id not in checksum_by_id:
                fail_violations.append(f"auditor_run must consume original {name} reference {artifact_id}")
            elif checksum_by_id[artifact_id] != checksum:
                fail_violations.append(f"auditor_run checksum does not match original {name} reference {artifact_id}")
            if artifact_id in version_by_id and version_by_id[artifact_id] != version:
                fail_violations.append(f"auditor_run version does not match original {name} reference {artifact_id}")
        _check_run_identity(auditor_run, expected_agent="YOUTUBE_ADAPTATION_AUDITOR", expected_role="YOUTUBE_ADAPTATION_AUDITOR", label="auditor_run", fail_violations=fail_violations, blocked_reasons=blocked_reasons)
        if auditor_run.get("input_checksum") != package_checksum:
            fail_violations.append("auditor_run input_checksum does not match the real package checksum")
        if package_checksum not in auditor_run.get("input_checksums", []):
            fail_violations.append("auditor_run input_checksums does not contain the real package checksum")
        if package_ref not in auditor_run.get("input_artifact_ids", []):
            fail_violations.append("auditor_run input_artifact_ids does not contain the exact package ref")
        auditor_output = _matching_output(auditor_run, "youtube_adaptation_review", review_id)
        if not auditor_output:
            fail_violations.append("auditor_run outputs do not contain the exact review artifact")
        else:
            if auditor_output.get("checksum") != review_checksum:
                fail_violations.append("auditor_run output checksum does not match the real review checksum")
            if auditor_output.get("artifact_ref") != review_ref:
                fail_violations.append("auditor_run output artifact_ref does not match the review ref")
        if review_ref not in auditor_run.get("output_artifact_ids", []):
            fail_violations.append("auditor_run output_artifact_ids does not contain the exact review ref")
        if review_checksum not in auditor_run.get("output_checksums", []):
            fail_violations.append("auditor_run output_checksums does not contain the real review checksum")
    if producer_run and auditor_run:
        producer_actor = str(indep.get("producer_actor_id") or "")
        auditor_actor = str(indep.get("auditor_actor_id") or "")
        if producer_run_id == auditor_run_id:
            blocked_reasons.append("producer and auditor share the same run id")
        if producer_actor == auditor_actor:
            blocked_reasons.append("independence actors are identical")
        if indep.get("decision") != "PASS":
            blocked_reasons.append("independence_check is not PASS")
        if not _actor_matches(producer_run, producer_actor):
            blocked_reasons.append("producer independence actor is not demonstrated by provenance")
        if not _actor_matches(auditor_run, auditor_actor):
            blocked_reasons.append("auditor independence actor is not demonstrated by provenance")
    if fail_violations:
        status = GateStatus.FAIL
    elif blocked_reasons or review.get("decision") == "BLOCK":
        status = GateStatus.BLOCKED
    else:
        status = DECISION_MAP.get(review.get("decision"), GateStatus.FAIL)
    if status is GateStatus.WARN:
        warnings.append("La revisión consolidada contiene WARN mitigados y trazados.")
    evidence = {
        "PROVENANCE_ARTIFACT_BINDING": "PASS" if not any(any(token in item for token in ["artifact", "checksum", "output_artifact_ids", "output_checksums", "review.artifact_"]) for item in fail_violations) else "FAIL",
        "PROVENANCE_ROLE_BINDING": "PASS" if not any(any(token in item for token in ["agent_id", "role_id"]) for item in fail_violations) else "FAIL",
        "AUDITOR_INPUT_BINDING": "PASS" if not any(any(token in item for token in ["input_checksum", "input_checksums", "input_artifact_ids"]) for item in fail_violations) else "FAIL",
        "REVIEW_INTERNAL_CONSISTENCY": "PASS" if not any(any(token in item for token in ["overpromise_decision", "opening_readiness", "duration_assessment", "global decision inconsistent", "platform", "rights", "blocking_reasons", "required_changes"]) for item in fail_violations) else "FAIL",
        "REAL_EXECUTION_REQUIRED_BY_GATE": "PASS",
        "blocked_reasons": blocked_reasons,
        "review_decision": review.get("decision"),
        "expected_review_decision": expected_decision,
    }
    summary = "Gate determinista de YOUTUBE_ADAPTATION B5-I2 evaluado."
    if status is GateStatus.FAIL:
        summary = "Gate falló por inconsistencias contractuales o de provenance."
    elif status is GateStatus.BLOCKED:
        summary = "Gate bloqueado por falta de evidencia real o independencia no demostrada."
    elif status is GateStatus.REQUEST_CHANGES:
        summary = "Gate coherente: el review exige una nueva versión corregida."
    elif status is GateStatus.WARN:
        summary = "Gate coherente con warnings mitigados y trazados."
    elif status is GateStatus.PASS:
        summary = "Gate coherente: contratos, artefactos y provenance exactos coinciden."
    return GateResult("youtube_adaptation_b5_i2_gate", artifact_id, "1.0.0", status, summary, violations=fail_violations, warnings=warnings, evidence=evidence)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", required=True)
    parser.add_argument("--review", required=True)
    parser.add_argument("--execution-registry", required=True)
    parser.add_argument("--active-profile", default="config/active_editorial_profile.json")
    parser.add_argument("--ep-id", default="YT-R3")
    parser.add_argument("--output-root")
    args = parser.parse_args()
    return run_gate(lambda: evaluate(Path(args.package), Path(args.review), Path(args.execution_registry), Path(args.active_profile), args.ep_id), output_root=args.output_root)


if __name__ == "__main__":
    import sys
    sys.exit(main())
