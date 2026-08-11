"""Provider-neutral route selection bounded by mission authorization."""
from __future__ import annotations

from typing import Any

from src.core.contract_validation import validate_against_schema


def choose_authorized_route(*, candidate_set: list[str], requested_profile: str | None = None, owner_selection_authority: bool = True, external_cost: bool = False, paid_cost_approved: bool = False) -> dict[str, Any]:
    candidates = list(dict.fromkeys(str(item) for item in candidate_set if str(item)))
    if not candidates:
        decision = {"status": "BLOCKED", "reasons": ["AUTHORIZED_CANDIDATE_SET_EMPTY"], "candidate_set": [], "selected_profile": None, "external_cost_authorized": False}
    elif external_cost and not paid_cost_approved:
        decision = {"status": "BLOCKED", "reasons": ["PAID_EXTERNAL_ROUTE_NOT_AUTHORIZED"], "candidate_set": candidates, "selected_profile": None, "external_cost_authorized": False}
    elif requested_profile and requested_profile not in candidates:
        decision = {"status": "BLOCKED", "reasons": ["PROFILE_OUTSIDE_AUTHORIZED_CANDIDATE_SET"], "candidate_set": candidates, "selected_profile": None, "external_cost_authorized": bool(paid_cost_approved)}
    elif owner_selection_authority:
        decision = {"status": "RECOMMEND_ONLY", "reasons": ["OWNER_RETAINS_ROUTE_SELECTION_AUTHORITY"], "candidate_set": candidates, "selected_profile": requested_profile if requested_profile in candidates else None, "external_cost_authorized": bool(paid_cost_approved)}
    else:
        decision = {"status": "SELECTED", "reasons": ["SELECTED_WITHIN_AUTHORIZED_CANDIDATE_SET"], "candidate_set": candidates, "selected_profile": requested_profile or candidates[0], "external_cost_authorized": bool(paid_cost_approved)}
    violations = validate_against_schema(decision, "routing_decision")
    if violations:
        raise ValueError("ROUTING_DECISION_INVALID: " + "; ".join(violations))
    return decision


def assert_resolved_route_authorized(authorization: Any, *, root: str, capability_id: str, role_id: str, operation: str, profile: str, route: str, execution_interface: str) -> None:
    """Re-check the resolved route after defaults are materialized."""
    authorization.verify(
        root,
        capability_id=capability_id,
        role_id=role_id,
        operation=operation,
        execution_profile_id=profile,
        execution_route=route,
        execution_interface=execution_interface,
    )


def assert_route_resolution_authorized(*, resolved_provider: str, provider_to_route: dict[str, str], authorized_candidate_set: list[str], requested_profile: str | None = None) -> str:
    """Reconcile runtime provider resolution with the authorized candidate set.

    This is the single reconciliation point between the provider-neutral router
    (``src.ai.router.resolve_provider``) and the mission-bounded routing policy.
    A provider that cannot be mapped to an authorized route is fail-closed.
    """
    if not authorized_candidate_set:
        raise PermissionError("ROUTE_RESOLUTION_UNVERIFIABLE_WITHOUT_AUTHORIZED_CANDIDATE_SET")
    if requested_profile and requested_profile not in authorized_candidate_set:
        raise PermissionError("ROUTE_RESOLUTION_OUTSIDE_AUTHORIZED_CANDIDATE_SET")
    route = provider_to_route.get(str(resolved_provider))
    if not route:
        raise PermissionError(f"ROUTE_RESOLUTION_UNKNOWN_PROVIDER_ROUTE:{resolved_provider}")
    if route not in authorized_candidate_set:
        raise PermissionError("ROUTE_RESOLUTION_OUTSIDE_AUTHORIZED_CANDIDATE_SET")
    return route
