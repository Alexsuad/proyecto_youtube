"""T4.0 — Orchestration gap analysis for PLAN 006.

Deterministically classifies each T4 decision need (PLAN 006 §12.0/§12.1) against
existing repository capabilities as ALREADY_COVERED / PARTIALLY_COVERED /
REAL_GAP, before any T4 implementation. It probes the live surfaces (policy
files + core modules) and never grants authority or creates new functional
authority. Only REAL_GAP needs may later be implemented with the minimum change.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ALREADY_COVERED = "ALREADY_COVERED"
PARTIALLY_COVERED = "PARTIALLY_COVERED"
REAL_GAP = "REAL_GAP"

COVERAGE_VALUES = (ALREADY_COVERED, PARTIALLY_COVERED, REAL_GAP)

# Decision needs from PLAN 006 §12.0 that must not be reimplemented without a
# demonstrated gap.
NOT_REIMPLEMENT = (
    "DECISION_INLINE_DELEGATE_ESCALATE",
    "DELEGATION_BOUNDED_BY_AUTHORIZATION",
    "REVIEW_FLOOR",
    "ROUTING_WITHIN_AUTHORIZED_CANDIDATE_SET",
)

EXISTING_CAPABILITIES = (
    "delegation_policy",
    "routing_policy",
    "review_workload",
    "agent_execution_profiles",
    "mission_authorization",
    "context_resolution",
)


@dataclass(frozen=True)
class GapFinding:
    need: str
    classification: str
    existing_capability: str
    evidence_path: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "need": self.need,
            "classification": self.classification,
            "existing_capability": self.existing_capability,
            "evidence_path": self.evidence_path,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class GapAnalysisResult:
    findings: tuple[GapFinding, ...]
    real_gaps: tuple[str, ...]
    partially_covered: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "findings": [finding.to_dict() for finding in self.findings],
            "real_gaps": list(self.real_gaps),
            "partially_covered": list(self.partially_covered),
        }


def _probe_file(path: Path) -> bool:
    return path.is_file()


def _semantic_surface_present(paths: list[Path], required_markers: tuple[str, ...]) -> bool:
    try:
        text = "\n".join(path.read_text(encoding="utf-8") for path in paths)
    except OSError:
        return False
    return all(marker in text for marker in required_markers)


def analyze_gaps(
    root: str | Path,
    *,
    decision_need: str,
    existing_capability: str,
) -> GapFinding:
    repository_root = Path(root).resolve()
    evidence_paths = {
        "delegation_policy": ("config/delegation_policy.json", "src/core/delegation_policy.py"),
        "routing_policy": ("src/core/routing_policy.py",),
        "review_workload": ("src/core/review_workload.py",),
        "agent_execution_profiles": ("config/agent_execution_profiles.json",),
        "mission_authorization": ("src/core/mission_authorization.py",),
        "context_resolution": ("src/core/context_resolution.py",),
    }
    semantic_markers = {
        "delegation_policy": ("def choose_delegation", "INLINE", "DELEGATE", "ESCALATE"),
        "routing_policy": ("def choose_authorized_route", "authorized_candidate_set"),
        "review_workload": ("def choose_review_workload",),
        "agent_execution_profiles": ("execution_profiles", "execution_route_selection_authority"),
        "mission_authorization": ("def verify", "authorized_scope_sha256"),
        "context_resolution": ("def resolve_context", "resolved_context_size"),
    }
    if existing_capability not in evidence_paths:
        raise ValueError(f"UNKNOWN_EXISTING_CAPABILITY:{existing_capability}")

    paths = [repository_root / relative for relative in evidence_paths[existing_capability]]
    present = all(_probe_file(path) for path in paths)
    if not present:
        return GapFinding(
            need=decision_need,
            classification=REAL_GAP,
            existing_capability=existing_capability,
            evidence_path=evidence_paths[existing_capability][0],
            reason="MISSING_CAPABILITY_SURFACE",
        )
    if not _semantic_surface_present(paths, semantic_markers[existing_capability]):
        return GapFinding(
            need=decision_need,
            classification=PARTIALLY_COVERED,
            existing_capability=existing_capability,
            evidence_path=evidence_paths[existing_capability][0],
            reason="SURFACE_PRESENT_SEMANTIC_PROBE_FAILED",
        )

    # Default mapping of T4 needs to their canonical existing capability.
    coverage_map = {
        "DECISION_INLINE_DELEGATE_ESCALATE": ("delegation_policy", ALREADY_COVERED),
        "DELEGATION_BOUNDED_BY_AUTHORIZATION": ("mission_authorization", ALREADY_COVERED),
        "REVIEW_FLOOR": ("review_workload", ALREADY_COVERED),
        "ROUTING_WITHIN_AUTHORIZED_CANDIDATE_SET": ("routing_policy", ALREADY_COVERED),
    }
    expected, default_classification = coverage_map.get(
        decision_need, (existing_capability, PARTIALLY_COVERED)
    )
    if existing_capability != expected:
        # The caller probed a non-canonical capability: keep the probe result but
        # classify as PARTIALLY_COVERED since a canonical owner exists.
        return GapFinding(
            need=decision_need,
            classification=PARTIALLY_COVERED,
            existing_capability=existing_capability,
            evidence_path=evidence_paths[existing_capability][0],
            reason=f"CANONICAL_CAPABILITY_IS_{expected};probed={existing_capability}",
        )
    return GapFinding(
        need=decision_need,
        classification=default_classification,
        existing_capability=existing_capability,
        evidence_path=evidence_paths[existing_capability][0],
        reason="SEMANTIC_SURFACE_PRESENT_AND_CANONICAL",
    )


def run_gap_analysis(
    root: str | Path,
    *,
    probe: dict[str, str] | None = None,
) -> GapAnalysisResult:
    """Analyze the canonical T4 needs against the canonical capabilities.

    ``probe`` optionally overrides need->capability for scenario probing; the
    canonical default is the documented coverage mapping.
    """
    root_path = Path(root).resolve()
    defaults = {
        "DECISION_INLINE_DELEGATE_ESCALATE": "delegation_policy",
        "DELEGATION_BOUNDED_BY_AUTHORIZATION": "mission_authorization",
        "REVIEW_FLOOR": "review_workload",
        "ROUTING_WITHIN_AUTHORIZED_CANDIDATE_SET": "routing_policy",
        "LOWEST_SUFFICIENT_ROUTE": "agent_execution_profiles",
        "CONTEXT_BUDGET": "context_resolution",
        "VERIFICATION_BUDGET": "routing_policy",
    }
    probes = dict(defaults)
    if probe:
        for need, capability in probe.items():
            if capability not in EXISTING_CAPABILITIES:
                raise ValueError(f"UNKNOWN_EXISTING_CAPABILITY:{capability}")
            probes[need] = capability
    findings = tuple(
        analyze_gaps(root_path, decision_need=need, existing_capability=capability)
        for need, capability in probes.items()
    )
    real_gaps = tuple(sorted({f.need for f in findings if f.classification == REAL_GAP}))
    partially = tuple(sorted({f.need for f in findings if f.classification == PARTIALLY_COVERED}))
    return GapAnalysisResult(findings=findings, real_gaps=real_gaps, partially_covered=partially)


def assert_no_gap_without_evidence(result: GapAnalysisResult, *, allowed_real_gaps: tuple[str, ...] = ()) -> None:
    """Fail-closed guard: REAL_GAP is only admissible when explicitly authorized
    and justified by missing surface evidence."""
    unexpected = tuple(gap for gap in result.real_gaps if gap not in allowed_real_gaps)
    if unexpected:
        raise AssertionError("UNEXPECTED_REAL_GAP:" + ",".join(unexpected))
