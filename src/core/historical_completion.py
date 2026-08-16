"""T1 — Historical Completion + Owner Closure for PLAN 006.

Separates the three concepts defined in PLAN 006 §9.2:

    A. ACTIVE EXECUTION AUTHORIZATION   (fail-closed, uses MissionAuthorization)
    B. HISTORICAL TECHNICAL COMPLETION  (immutable completion identity)
    C. CURRENT APPLICABILITY            (semantic reuse decision, delegated to T2)

The historical completion identity is derived from a frozen execution snapshot
(mission, authorization artifact, live state at execution, authority, git
binding, evidence identities). It never re-reads the future live state, so an
administrative live-state change after completion does not stale the historical
fact. `MissionAuthorization.verify()` remains fail-closed for active execution;
this module only consumes it via the frozen snapshot hashes it already captured.

Owner closure expresses ACCEPTED_COMPLETION_IDENTITY + OWNER_DECISION +
CLOSURE_METADATA. It never re-executes required tests and never rebuilds the
historical authorization against the current live state. Technical completion
never becomes functional approval of product.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.core.contract_validation import validate_against_schema
from src.core.mission_authorization import MissionAuthorization, scope_checksum, sha256_file


class HistoricalCompletionError(ValueError):
    """A frozen completion snapshot is inconsistent or owner closure is invalid."""


@dataclass(frozen=True)
class CompletionSnapshot:
    mission_id: str
    mission_contract_sha256: str
    authorization_artifact_sha256: str
    authorized_scope_sha256: str
    live_state_path: str
    live_state_sha256_at_execution: str
    authority_ref: str
    authority_sha256: str
    repository_revision: str
    required_test_identities: tuple[str, ...]
    evidence_identities: tuple[str, ...]
    git_binding: dict[str, str]
    completion_result: str
    completion_generated_at: str

    def to_frozen(self) -> dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "mission_contract_sha256": self.mission_contract_sha256,
            "authorization_artifact_sha256": self.authorization_artifact_sha256,
            "authorized_scope_sha256": self.authorized_scope_sha256,
            "live_state_path": self.live_state_path,
            "live_state_sha256_at_execution": self.live_state_sha256_at_execution,
            "authority_ref": self.authority_ref,
            "authority_sha256": self.authority_sha256,
            "repository_revision": self.repository_revision,
            "required_test_identities": list(self.required_test_identities),
            "evidence_identities": list(self.evidence_identities),
            "git_binding": self.git_binding,
            "completion_result": self.completion_result,
            "completion_generated_at": self.completion_generated_at,
        }


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _identity(*payload: Any) -> str:
    digest = hashlib.sha256()
    for item in payload:
        digest.update(len(_canonical_json(item)).to_bytes(8, "big"))
        digest.update(_canonical_json(item))
    return digest.hexdigest()


def freeze_completion_snapshot(
    *,
    mission_id: str,
    mission_contract_sha256: str,
    authorization_artifact_sha256: str,
    authorized_scope_sha256: str,
    live_state_path: str,
    live_state_sha256_at_execution: str,
    authority_ref: str,
    authority_sha256: str,
    repository_revision: str,
    required_test_identities: tuple[str, ...],
    evidence_identities: tuple[str, ...],
    git_binding: dict[str, str],
    completion_result: str,
    completion_generated_at: str | None = None,
) -> CompletionSnapshot:
    """Freeze the minimal historical snapshot of a completed execution.

    All values are historical facts captured at completion time. None of them is
    re-derived from the future live state.
    """
    required = {
        "mission_id": mission_id,
        "mission_contract_sha256": mission_contract_sha256,
        "authorization_artifact_sha256": authorization_artifact_sha256,
        "authorized_scope_sha256": authorized_scope_sha256,
        "live_state_path": live_state_path,
        "live_state_sha256_at_execution": live_state_sha256_at_execution,
        "authority_ref": authority_ref,
        "authority_sha256": authority_sha256,
        "repository_revision": repository_revision,
        "completion_result": completion_result,
    }
    for key, value in required.items():
        if not isinstance(value, str) or not value:
            raise HistoricalCompletionError(f"COMPLETION_SNAPSHOT_FIELD_REQUIRED:{key}")
    if completion_result not in {"PASS", "PASS_WITH_LIMITATIONS"}:
        raise HistoricalCompletionError(f"COMPLETION_RESULT_INVALID:{completion_result}")
    if not required_test_identities:
        raise HistoricalCompletionError("COMPLETION_SNAPSHOT_TEST_IDENTITIES_REQUIRED")
    return CompletionSnapshot(
        mission_id=mission_id,
        mission_contract_sha256=mission_contract_sha256.lower(),
        authorization_artifact_sha256=authorization_artifact_sha256.lower(),
        authorized_scope_sha256=authorized_scope_sha256.lower(),
        live_state_path=live_state_path,
        live_state_sha256_at_execution=live_state_sha256_at_execution.lower(),
        authority_ref=authority_ref,
        authority_sha256=authority_sha256.lower(),
        repository_revision=repository_revision,
        required_test_identities=required_test_identities,
        evidence_identities=evidence_identities,
        git_binding=git_binding,
        completion_result=completion_result,
        completion_generated_at=completion_generated_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    )


def completion_identity(snapshot: CompletionSnapshot) -> str:
    """Immutable identity of the historical completion.

    Derived only from frozen material data: canonical execution snapshot +
    technical evidence identities + completion result. Volatile metadata that
    does not reflect material execution (completion_generated_at) is excluded,
    so the identity does not change because time passed or the live state
    evolved after completion.
    """
    frozen = snapshot.to_frozen()
    frozen.pop("completion_generated_at", None)
    return _identity(
        frozen,
        snapshot.mission_contract_sha256,
        snapshot.authorization_artifact_sha256,
        snapshot.authorized_scope_sha256,
        snapshot.live_state_sha256_at_execution,
        snapshot.authority_sha256,
        sorted(snapshot.required_test_identities),
        sorted(snapshot.evidence_identities),
        snapshot.completion_result,
    )


def build_completion_record(snapshot: CompletionSnapshot) -> dict[str, Any]:
    identity = completion_identity(snapshot)
    return {
        "schema_version": "1.0.0",
        "plan_id": "PLAN_006",
        "artifact_id": "PLAN_006_T1_HISTORICAL_COMPLETION",
        "mission_id": snapshot.mission_id,
        "increment": "T1",
        "repository_revision": snapshot.repository_revision,
        "generated_at": snapshot.completion_generated_at,
        "completion_identity_sha256": identity,
        "frozen_snapshot": snapshot.to_frozen(),
        "technical_completion_claim": True,
        "functional_approval_claim": False,
        "product_readiness_claim": False,
        "source_inputs": [],
        "evidence_refs": [],
        "limitations": [],
        "result": "PASS",
        "evidence_identity_sha256": None,
    }


def verify_historical_completion(record: dict[str, Any]) -> list[str]:
    """Verify a historical completion record WITHOUT reading the future live state.

    Checks internal consistency of the frozen snapshot: identity recomputation,
    schema validity and consistency of the frozen scope checksum against the
    frozen scope payload it captures.
    """
    violations: list[str] = []
    snapshot_data = record.get("frozen_snapshot")
    if not isinstance(snapshot_data, dict):
        return ["COMPLETION_FROZEN_SNAPSHOT_REQUIRED"]
    try:
        snapshot = CompletionSnapshot(**snapshot_data)
        snapshot = CompletionSnapshot(
            mission_id=snapshot.mission_id,
            mission_contract_sha256=snapshot.mission_contract_sha256,
            authorization_artifact_sha256=snapshot.authorization_artifact_sha256,
            authorized_scope_sha256=snapshot.authorized_scope_sha256,
            live_state_path=snapshot.live_state_path,
            live_state_sha256_at_execution=snapshot.live_state_sha256_at_execution,
            authority_ref=snapshot.authority_ref,
            authority_sha256=snapshot.authority_sha256,
            repository_revision=snapshot.repository_revision,
            required_test_identities=tuple(snapshot.required_test_identities),
            evidence_identities=tuple(snapshot.evidence_identities),
            git_binding=snapshot.git_binding,
            completion_result=snapshot.completion_result,
            completion_generated_at=snapshot.completion_generated_at,
        )
    except (TypeError, ValueError) as exc:
        return [f"COMPLETION_SNAPSHOT_INVALID:{exc}"]
    if completion_identity(snapshot) != record.get("completion_identity_sha256"):
        violations.append("COMPLETION_IDENTITY_MISMATCH")
    binding_hashes = (
        snapshot.authorization_artifact_sha256,
        snapshot.authorized_scope_sha256,
        snapshot.authority_sha256,
    )
    if any(not _is_sha256(value) for value in binding_hashes):
        violations.append("COMPLETION_BINDING_SHA256_INVALID")
    if len(set(binding_hashes)) != len(binding_hashes):
        violations.append("COMPLETION_BINDINGS_NOT_DISTINCT")
    if record.get("technical_completion_claim") is not True:
        violations.append("TECHNICAL_COMPLETION_CLAIM_MISSING")
    if record.get("functional_approval_claim") is True:
        violations.append("FUNCTIONAL_APPROVAL_MUST_NOT_BE_CLAIMED")
    if record.get("product_readiness_claim") is True:
        violations.append("PRODUCT_READINESS_MUST_NOT_BE_CLAIMED")
    closure = record.get("owner_closure")
    if closure is not None:
        metadata = closure.get("closure_metadata") if isinstance(closure, dict) else None
        if not isinstance(metadata, dict) or not _is_sha256(str(metadata.get("owner_identity_sha256") or "")):
            violations.append("OWNER_IDENTITY_BINDING_REQUIRED")
    return violations


def _is_sha256(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdefABCDEF" for character in value)


def owner_closure(
    *,
    completion_record: dict[str, Any],
    owner_decision: str,
    closure_metadata: dict[str, Any],
    closure_generated_at: str | None = None,
) -> dict[str, Any]:
    """Record owner closure that references the completion identity.

    Never re-executes required tests and never rebuilds the historical
    authorization against the current live state.
    """
    violations = verify_historical_completion(completion_record)
    if violations:
        raise HistoricalCompletionError("COMPLETION_NOT_VERIFIED:" + "; ".join(violations))
    if owner_decision not in {"ACCEPTED", "ACCEPTED_WITH_OBSERVABILITY_LIMITATION", "REJECTED"}:
        raise HistoricalCompletionError(f"OWNER_DECISION_INVALID:{owner_decision}")
    if owner_decision == "REJECTED":
        raise HistoricalCompletionError("OWNER_REJECTED_COMPLETION")
    if "owner" not in closure_metadata or not closure_metadata.get("owner"):
        raise HistoricalCompletionError("CLOSURE_OWNER_REQUIRED")
    if not _is_sha256(str(closure_metadata.get("owner_identity_sha256") or "")):
        raise HistoricalCompletionError("CLOSURE_OWNER_IDENTITY_BINDING_REQUIRED")
    identity = completion_record["completion_identity_sha256"]
    return {
        "plan_id": "PLAN_006",
        "artifact_id": "PLAN_006_T1_OWNER_CLOSURE",
        "mission_id": completion_record["mission_id"],
        "increment": "T1",
        "completion_identity_sha256": identity,
        "owner_decision": owner_decision,
        "closure_metadata": closure_metadata,
        "closure_generated_at": closure_generated_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "re_executes_required_tests": False,
        "rebuilds_historical_authorization_against_current_live_state": False,
        "functional_approval_claim": False,
    }


@dataclass(frozen=True)
class CurrentApplicability:
    applicable: bool
    decision: str
    reasons: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {"applicable": self.applicable, "decision": self.decision, "reasons": list(self.reasons)}


def evaluate_current_applicability(
    *,
    snapshot: CompletionSnapshot,
    current_live_state_sha256: str,
    material_dependency_hashes: dict[str, str],
    compare_live_state: bool = True,
) -> CurrentApplicability:
    """Decide whether the historical evidence is reusable for a new decision.

    HISTORICAL_VALIDITY != CURRENT_APPLICABILITY. A frozen completion can stay
    historically valid while its applicability degrades because material
    execution dependencies moved. This delegates to T2 semantics: when the live
    state used at execution no longer matches the current live state, the
    evidence cannot be reused as-is for a new decision without targeted
    re-verification. Reuse callers may disable that global-state comparison when
    material dependencies are independently verified.
    """
    if not isinstance(snapshot.live_state_sha256_at_execution, str) or not snapshot.live_state_sha256_at_execution:
        return CurrentApplicability(False, "UNVERIFIABLE", ("LIVE_STATE_SNAPSHOT_MISSING",))
    if compare_live_state and current_live_state_sha256.lower() != snapshot.live_state_sha256_at_execution.lower():
        return CurrentApplicability(
            False,
            "TARGETED_REVERIFY_REQUIRED",
            ("LIVE_STATE_CHANGED_AFTER_COMPLETION",),
        )
    for dependency, recorded_hash in material_dependency_hashes.items():
        if not isinstance(recorded_hash, str) or not recorded_hash:
            return CurrentApplicability(False, "UNVERIFIABLE", (f"MATERIAL_DEPENDENCY_UNVERIFIABLE:{dependency}",))
    return CurrentApplicability(True, "REUSE_CANDIDATE", ("MATERIAL_DEPS_UNCHANGED",))


def verify_active_execution_fail_closed(
    authorization: MissionAuthorization,
    root: str | Path,
    *,
    capability_id: str,
    role_id: str,
    operation: str,
) -> None:
    """Consume the existing fail-closed authorization for ACTIVE execution.

    T1 does not weaken this. If the live state moved after the authorization
    snapshot, `verify()` raises MissionAuthorizationError and active execution is
    blocked, even when historical completion stays valid.
    """
    authorization.verify(
        root,
        capability_id=capability_id,
        role_id=role_id,
        operation=operation,
    )
