"""Deterministic, provider-neutral INLINE/DELEGATE/ESCALATE policy."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from src.core.contract_validation import validate_against_schema
from src.core.plan_005_invariants import verify_invariants
from src.core.mission_authorization import MissionAuthorization


DECISIONS = {"INLINE", "DELEGATE", "ESCALATE"}


def _authorization_root(authorization: MissionAuthorization, task: dict[str, Any]) -> Path | None:
    explicit = task.get("authorization_root")
    if explicit:
        return Path(str(explicit)).resolve()
    if not authorization.contract_path:
        return None
    contract = Path(authorization.contract_path).resolve()
    for candidate in (contract.parent, *contract.parents):
        if (candidate / authorization.live_state_path).is_file():
            return candidate
    return None


@dataclass(frozen=True)
class DelegationDecision:
    decision: str
    reasons: tuple[str, ...]
    policy_version: str
    evidence_refs: tuple[str, ...] = ()
    candidate_capability_id: str | None = None
    delegation_depth: int = 0
    authorized_candidate_set: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["reasons"] = list(self.reasons)
        data["evidence_refs"] = list(self.evidence_refs)
        data["authorized_candidate_set"] = list(self.authorized_candidate_set)
        return {key: value for key, value in data.items() if value is not None}


def load_delegation_policy(path: str | Path | None = None) -> dict[str, Any]:
    policy_path = Path(path) if path else Path("config/delegation_policy.json")
    data = json.loads(policy_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not data.get("policy_version"):
        raise ValueError("DELEGATION_POLICY_INVALID")
    return data


def _choose_delegation(task: dict[str, Any], *, policy_path: str | Path | None = None) -> DelegationDecision:
    """Choose one deterministic decision without granting authority."""
    policy = load_delegation_policy(policy_path)
    candidate_set = tuple(str(item) for item in task.get("authorized_candidate_set", []) if str(item))
    evidence_refs = tuple(str(item) for item in task.get("evidence_refs", []) if str(item))
    depth = int(task.get("delegation_depth", 0))
    max_depth = int(task.get("max_delegation_depth", policy.get("max_delegation_depth", 1)))
    reasons: list[str] = []

    if bool(task.get("authority_conflict")) or bool(task.get("owner_review_required")):
        reasons.append("AUTHORITY_REQUIRES_ESCALATION")
        return DelegationDecision("ESCALATE", tuple(reasons), str(policy["policy_version"]), evidence_refs, authorized_candidate_set=candidate_set)
    authorization = task.get("mission_authorization")
    if isinstance(authorization, MissionAuthorization):
        requested_capability = str(task.get("candidate_capability_id") or "")
        requested_role = str(task.get("role_id") or (authorization.role_ids[0] if authorization.role_ids else ""))
        repository_root = _authorization_root(authorization, task)
        if repository_root is None:
            raise PermissionError("CANONICAL_MISSION_AUTHORIZATION_ROOT_REQUIRED")
        operation = "DELEGATE" if "DELEGATE" in authorization.allowed_operations else "EXECUTE_CAPABILITY"
        try:
            authorization.verify(
                repository_root,
                capability_id=requested_capability,
                role_id=requested_role,
                operation=operation,
                path=task.get("requested_path"),
                execution_mode=task.get("execution_mode"),
                execution_route=task.get("execution_route"),
                execution_profile_id=task.get("execution_profile_id"),
                execution_interface=task.get("execution_interface"),
            )
        except Exception as exc:
            raise PermissionError("MISSION_AUTHORIZATION_UNVERIFIED") from exc
        scope_authorized = True
        delegation_authorized = True
    else:
        # Caller booleans are observations only; they never authorize delegation.
        scope_authorized = task.get("scope_authorized") is True
        delegation_authorized = task.get("delegation_authorized") is True
    if depth >= max_depth and bool(task.get("delegation_requested")):
        reasons.append("DEPTH_EXCEEDED")
        return DelegationDecision("ESCALATE", tuple(reasons), str(policy["policy_version"]), evidence_refs, delegation_depth=depth, authorized_candidate_set=candidate_set)
    if bool(task.get("trivial", False)) or (bool(task.get("deterministic", False)) and not bool(task.get("separable", False))):
        reasons.append("INLINE_LOW_RISK_OR_DETERMINISTIC")
        return DelegationDecision("INLINE", tuple(reasons), str(policy["policy_version"]), evidence_refs, delegation_depth=depth, authorized_candidate_set=candidate_set)
    if bool(task.get("separable")) and not delegation_authorized:
        reasons.append("DELEGATION_AUTHORIZATION_REQUIRED")
        return DelegationDecision("ESCALATE", tuple(reasons), str(policy["policy_version"]), evidence_refs, delegation_depth=depth, authorized_candidate_set=candidate_set)
    if bool(task.get("separable")) and not isinstance(authorization, MissionAuthorization):
        reasons.append("CANONICAL_MISSION_AUTHORIZATION_REQUIRED")
        return DelegationDecision("ESCALATE", tuple(reasons), str(policy["policy_version"]), evidence_refs, authorized_candidate_set=candidate_set)
    if bool(task.get("separable")) and not scope_authorized:
        reasons.append("SCOPE_UNAUTHORIZED")
        return DelegationDecision("ESCALATE", tuple(reasons), str(policy["policy_version"]), evidence_refs, authorized_candidate_set=candidate_set)
    if bool(task.get("separable")) and not candidate_set:
        reasons.append("AUTHORIZED_CANDIDATE_SET_REQUIRED")
        return DelegationDecision("ESCALATE", tuple(reasons), str(policy["policy_version"]), evidence_refs, delegation_depth=depth, authorized_candidate_set=candidate_set)
    if bool(task.get("separable")) and bool(task.get("capability_available")) and delegation_authorized:
        reasons.append("DELEGATION_REDUCES_CONTEXT_OR_SPECIALIZES_WORK")
        capability_id = str(task.get("candidate_capability_id")) if task.get("candidate_capability_id") else None
        if not capability_id or capability_id not in candidate_set:
            reasons.append("CAPABILITY_OUTSIDE_AUTHORIZED_CANDIDATE_SET")
            return DelegationDecision("ESCALATE", tuple(reasons), str(policy["policy_version"]), evidence_refs, delegation_depth=depth, authorized_candidate_set=candidate_set)
        return DelegationDecision("DELEGATE", tuple(reasons), str(policy["policy_version"]), evidence_refs, capability_id, depth + 1, candidate_set)
    if not bool(task.get("capability_available", True)):
        reasons.append("CAPABILITY_UNAVAILABLE")
        return DelegationDecision("ESCALATE", tuple(reasons), str(policy["policy_version"]), evidence_refs, delegation_depth=depth, authorized_candidate_set=candidate_set)
    reasons.append("INLINE_SUFFICIENT_AND_DELEGATION_NOT_JUSTIFIED")
    return DelegationDecision("INLINE", tuple(reasons), str(policy["policy_version"]), evidence_refs, delegation_depth=depth, authorized_candidate_set=candidate_set)


def choose_delegation(task: dict[str, Any], *, policy_path: str | Path | None = None) -> DelegationDecision:
    decision = _choose_delegation(task, policy_path=policy_path)
    observation = dict(task)
    observation.update({"decision": decision.decision, "authorized_candidate_set": list(decision.authorized_candidate_set)})
    if isinstance(task.get("mission_authorization"), MissionAuthorization):
        observation["delegation_authorized"] = True
        observation["scope_authorized"] = True
    violations = verify_invariants(["NO_DELEGATION_WITHOUT_AUTHORIZATION"], observation)
    if violations:
        raise PermissionError("DELEGATION_INVARIANT_VIOLATION:" + ",".join(violations))
    return decision


def validate_decision(decision: DelegationDecision) -> list[str]:
    return validate_against_schema(decision.to_dict(), "delegation_decision")
