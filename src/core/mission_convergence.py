"""Provider-neutral, evidence-governed convergence for reduced missions."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Callable

CONVERGED = "CONVERGED"
BLOCKED = "BLOCKED"
MAX_ITERATIONS_REACHED = "MAX_ITERATIONS_REACHED"
SELF_ONLY = "SELF_ONLY"
INDEPENDENT_REVIEW = "INDEPENDENT_REVIEW"
OWNER_REVIEW = "OWNER_REVIEW"


@dataclass(frozen=True)
class ConvergenceOutcome:
    status: str
    iterations: int
    review_stage: str
    events: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def required_review_stage(review_policy: dict[str, Any] | None, *, sensitive_change: bool = False, findings: bool = False) -> str:
    policy = review_policy or {}
    configured = str(policy.get("required_review", "")).upper()
    if configured in {SELF_ONLY, INDEPENDENT_REVIEW, OWNER_REVIEW}:
        return INDEPENDENT_REVIEW if sensitive_change and configured == SELF_ONLY else configured
    independent = str(policy.get("independent_review", "ON_FAILURE")).upper()
    if sensitive_change or independent == "REQUIRED" or (independent == "ON_FAILURE" and findings):
        return INDEPENDENT_REVIEW
    return OWNER_REVIEW if bool(policy.get("owner_review", True)) else SELF_ONLY


def _phase_result(stage: str, value: Any, *, governed: bool) -> dict[str, Any]:
    if not governed and isinstance(value, bool):
        return {"passed": value, "evidence": [{"kind": "LEGACY_TEST_HELPER", "ref": stage}], "legacy": True}
    if not isinstance(value, dict) or not isinstance(value.get("passed"), bool):
        return {"passed": False, "evidence": [], "reason": "STRUCTURED_RESULT_REQUIRED"}
    raw_evidence = value.get("evidence")
    entries = raw_evidence if isinstance(raw_evidence, list) else [raw_evidence]
    if not entries or any(not isinstance(entry, dict) or not str(entry.get("kind", "")).strip() or not str(entry.get("ref", "")).strip() for entry in entries):
        return {"passed": False, "evidence": [], "reason": "EVIDENCE_REQUIRED"}
    return {"passed": value["passed"], "evidence": [{"kind": str(entry["kind"]), "ref": str(entry["ref"])} for entry in entries], **({"reason": str(value["reason"])} if value.get("reason") else {})}


def run_convergence_loop(
    *,
    implement: Callable[[], Any],
    verify: Callable[[], Any],
    adversarial_review: Callable[[], Any],
    repair: Callable[[dict[str, Any]], Any],
    max_iterations: int = 3,
    review_policy: dict[str, Any] | None = None,
    sensitive_change: bool = False,
    governed: bool = True,
) -> ConvergenceOutcome:
    """Execute a fail-closed technical loop without performing approval.

    Governed use accepts only structured results with non-empty evidence refs.
    ``governed=False`` is retained solely for isolated legacy unit helpers.
    """
    if max_iterations < 1:
        raise ValueError("MAX_ITERATIONS_MUST_BE_POSITIVE")
    events: list[dict[str, Any]] = []

    def record(iteration: int, stage: str, raw: Any) -> dict[str, Any]:
        result = _phase_result(stage, raw, governed=governed)
        events.append({"iteration": iteration, "stage": stage, "result": result})
        return result

    implementation = record(0, "IMPLEMENT", implement())
    if not implementation["passed"]:
        repaired = record(0, "REPAIR", repair({"iteration": 0, "stage": "IMPLEMENT", "result": implementation}))
        # A repair callback is not replacement implementation evidence. A failed
        # IMPLEMENT phase must be rerun under a new mission attempt.
        return ConvergenceOutcome(BLOCKED, 0, required_review_stage(review_policy, sensitive_change=sensitive_change, findings=True), tuple(events), implementation.get("reason") or repaired.get("reason") or "IMPLEMENT_FAILED")

    for iteration in range(1, max_iterations + 1):
        verify_stage = "VERIFY" if iteration == 1 else "REVERIFY"
        verification = record(iteration, verify_stage, verify())
        if not verification["passed"]:
            repaired = record(iteration, "REPAIR", repair({"iteration": iteration, "stage": verify_stage, "result": verification}))
            if not repaired["passed"]:
                return ConvergenceOutcome(BLOCKED, iteration, required_review_stage(review_policy, sensitive_change=sensitive_change, findings=True), tuple(events), verification.get("reason") or repaired.get("reason") or "VERIFY_FAILED")
            continue

        adversarial = record(iteration, "SELF_ADVERSARIAL_REVIEW", adversarial_review())
        if not adversarial["passed"]:
            repaired = record(iteration, "REPAIR", repair({"iteration": iteration, "stage": "SELF_ADVERSARIAL_REVIEW", "result": adversarial}))
            if not repaired["passed"]:
                return ConvergenceOutcome(BLOCKED, iteration, required_review_stage(review_policy, sensitive_change=sensitive_change, findings=True), tuple(events), adversarial.get("reason") or repaired.get("reason") or "SELF_REVIEW_FAILED")
            continue
        return ConvergenceOutcome(CONVERGED, iteration, required_review_stage(review_policy, sensitive_change=sensitive_change), tuple(events))

    return ConvergenceOutcome(MAX_ITERATIONS_REACHED, max_iterations, required_review_stage(review_policy, sensitive_change=sensitive_change, findings=True), tuple(events), "MAX_ITERATIONS_REACHED")
