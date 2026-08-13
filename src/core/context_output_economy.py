"""T2-D — Context/output economy + Product Impact protection for PLAN 006.

Implements §10D:
- 10D.1 Context economy: start minimal, expand only on bounded triggers
  (contradiction, missing dependency, insufficient evidence, unresolved
  reference, material test failure).
- 10D.2 Delegated context: reviewer inherits only diff/invariant/affected
  files/tests/evidence, never the full implementer conversation.
- 10D.3 Output economy: parent receives SUMMARY/structured findings; raw logs
  only by reference or on demand.
- 10D.4 Product impact check: touched technical surface -> known consumers ->
  functional responsibilities affected -> targeted product regression. Fails
  closed when the consumer map is missing or incomplete; never becomes a
  complete audit or a parallel documentary system.

Consumes existing surfaces (ResolvedContextManifest semantics, evidence
validation) as data; it does not edit product modules.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

EXPANSION_TRIGGERS = (
    "CONTRADICTION",
    "MISSING_DEPENDENCY",
    "INSUFFICIENT_EVIDENCE",
    "UNRESOLVED_REFERENCE",
    "MATERIAL_TEST_FAILURE",
)

VALID_EXPANSION_TRIGGERS = set(EXPANSION_TRIGGERS)

CONSUMER_RESOLUTION = ("CONSUMERS_KNOWN", "CONSUMERS_UNKNOWN")

MINIMAL_CONTEXT_KIND = "MINIMAL_CONTEXT"
EXPANDED_CONTEXT_KIND = "EXPANDED_CONTEXT"
DELEGATED_CONTEXT_KIND = "DELEGATED_CONTEXT"
FULL_CONTEXT_KIND = "FULL_CONTEXT"


@dataclass(frozen=True)
class ContextPlan:
    context_kind: str
    base_surface: tuple[str, ...]
    expansion_triggers: tuple[str, ...] = ()
    justification: str = ""

    @property
    def minimal(self) -> bool:
        return self.context_kind == MINIMAL_CONTEXT_KIND and not self.expansion_triggers

    def expand(self, trigger: str, justification: str) -> "ContextPlan":
        if trigger not in VALID_EXPANSION_TRIGGERS:
            raise ValueError(f"UNKNOWN_EXPANSION_TRIGGER:{trigger}")
        return ContextPlan(
            context_kind=EXPANDED_CONTEXT_KIND,
            base_surface=self.base_surface,
            expansion_triggers=self.expansion_triggers + (trigger,),
            justification=justification,
        )


def plan_minimal_context(surface: list[str], *, expand_on: list[str] | None = None) -> ContextPlan:
    plan = ContextPlan(
        context_kind=EXPANDED_CONTEXT_KIND if expand_on else MINIMAL_CONTEXT_KIND,
        base_surface=tuple(surface),
        expansion_triggers=tuple(expand_on or ()),
    )
    if expand_on:
        invalid = [t for t in expand_on if t not in VALID_EXPANSION_TRIGGERS]
        if invalid:
            raise ValueError(f"UNKNOWN_EXPANSION_TRIGGER:{invalid[0]}")
    return plan


@dataclass(frozen=True)
class ReviewerDelegation:
    context_kind: str
    mission_ref: str
    authority_ref: str
    diff_ref: str
    invariant_ids: tuple[str, ...]
    affected_files: tuple[str, ...]
    relevant_test_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    inherited_conversation: bool = False

    @property
    def contaminated(self) -> bool:
        return self.inherited_conversation


def build_reviewer_delegation(
    *,
    mission_ref: str,
    authority_ref: str,
    diff_ref: str,
    invariant_ids: list[str],
    affected_files: list[str],
    relevant_test_refs: list[str],
    evidence_refs: list[str],
) -> ReviewerDelegation:
    return ReviewerDelegation(
        context_kind=DELEGATED_CONTEXT_KIND,
        mission_ref=mission_ref,
        authority_ref=authority_ref,
        diff_ref=diff_ref,
        invariant_ids=tuple(invariant_ids),
        affected_files=tuple(affected_files),
        relevant_test_refs=tuple(relevant_test_refs),
        evidence_refs=tuple(evidence_refs),
        inherited_conversation=False,
    )


@dataclass(frozen=True)
class CompactOutput:
    outcome: str
    exit_code: int | None
    test_counts: dict[str, int]
    failing_nodes: tuple[str, ...]
    evidence_ref: str | None
    finding: str
    raw_log_ref: str | None = None

    def as_summary(self) -> dict[str, Any]:
        payload = {
            "outcome": self.outcome,
            "exit_code": self.exit_code,
            "test_counts": self.test_counts,
            "failing_nodes": list(self.failing_nodes),
            "evidence_ref": self.evidence_ref,
            "finding": self.finding,
            "raw_log_ref": self.raw_log_ref,
        }
        return payload


def compress_parent_output(
    *,
    outcome: str,
    exit_code: int | None,
    test_counts: dict[str, int],
    failing_nodes: list[str],
    evidence_ref: str | None,
    finding: str,
    raw_log_ref: str | None = None,
) -> CompactOutput:
    return CompactOutput(
        outcome=outcome,
        exit_code=exit_code,
        test_counts=test_counts,
        failing_nodes=tuple(failing_nodes),
        evidence_ref=evidence_ref,
        finding=finding,
        raw_log_ref=raw_log_ref,
    )


# --- Product Impact Check (10D.4) ---


@dataclass(frozen=True)
class ConsumerRegistration:
    surface: str
    consumer: str
    functional_responsibility: str
    regression_ref: str


@dataclass(frozen=True)
class ProductImpactCheck:
    checked: bool
    surfaces_touched: tuple[str, ...]
    consumers_known: tuple[ConsumerRegistration, ...]
    responsibilities_affected: tuple[str, ...]
    targeted_regression_refs: tuple[str, ...]
    fails_closed: bool
    reason: str | None = None


def _lookup_consumers(
    surface: str,
    registrations: list[ConsumerRegistration],
) -> list[ConsumerRegistration]:
    return [r for r in registrations if r.surface == surface]


def run_product_impact_check(
    *,
    touched_surfaces: list[str],
    registrations: list[ConsumerRegistration],
    resolution: str = "CONSUMERS_KNOWN",
) -> ProductImpactCheck:
    """Every touched transversal surface must resolve to known consumers and a
    targeted regression. Unknown resolution fails closed; an untouched surface
    with no registrations is not a defect (check only guards what is touched)."""
    if resolution not in CONSUMER_RESOLUTION:
        return ProductImpactCheck(
            checked=False,
            surfaces_touched=tuple(touched_surfaces),
            consumers_known=(),
            responsibilities_affected=(),
            targeted_regression_refs=(),
            fails_closed=True,
            reason=f"UNKNOWN_RESOLUTION:{resolution}",
        )
    all_consumers: list[ConsumerRegistration] = []
    responsibilities: set[str] = set()
    regressions: set[str] = set()
    for surface in touched_surfaces:
        consumers = _lookup_consumers(surface, registrations)
        if not consumers:
            return ProductImpactCheck(
                checked=False,
                surfaces_touched=tuple(touched_surfaces),
                consumers_known=(),
                responsibilities_affected=(),
                targeted_regression_refs=(),
                fails_closed=True,
                reason=f"NO_KNOWN_CONSUMERS:{surface}",
            )
        for consumer in consumers:
            all_consumers.append(consumer)
            responsibilities.add(consumer.functional_responsibility)
            regressions.add(consumer.regression_ref)
    return ProductImpactCheck(
        checked=True,
        surfaces_touched=tuple(touched_surfaces),
        consumers_known=tuple(all_consumers),
        responsibilities_affected=tuple(sorted(responsibilities)),
        targeted_regression_refs=tuple(sorted(regressions)),
        fails_closed=False,
        reason=None,
    )


def product_impact_guard(
    *,
    touched_surfaces: list[str],
    registrations: list[ConsumerRegistration],
    resolution: str = "CONSUMERS_KNOWN",
) -> ProductImpactCheck:
    """Fail-closed wrapper: a touched surface without targeted regression blocks
    the mission checkpoint."""
    return run_product_impact_check(
        touched_surfaces=touched_surfaces,
        registrations=registrations,
        resolution=resolution,
    )
