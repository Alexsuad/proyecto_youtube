"""Neutral optional source-grounded research adapter contract."""
from __future__ import annotations

from typing import Any

from src.core.contract_validation import validate_against_schema


def validate_optional_research_adapter(
    data: dict[str, Any] | None,
    known_source_refs: set[str] | None = None,
) -> list[str]:
    """Validate an adapter when present; absence is a valid non-blocking path."""
    if data is None:
        return []

    violations = [
        f"SCHEMA_INVALID:{item}"
        for item in validate_against_schema(data, "source_grounded_research_adapter")
    ]
    if violations:
        return violations

    source_refs = set(data["source_refs"])
    if known_source_refs is not None:
        unknown_refs = source_refs - known_source_refs
        if unknown_refs:
            violations.append(f"ADAPTER_SOURCE_UNKNOWN:{','.join(sorted(unknown_refs))}")
    finding_ids = [finding["finding_id"] for finding in data["findings"]]
    if len(finding_ids) != len(set(finding_ids)):
        violations.append("ADAPTER_FINDING_ID_DUPLICATE")
    for finding in data["findings"]:
        unknown_refs = set(finding["evidence_refs"]) - source_refs
        if unknown_refs:
            violations.append(
                f"ADAPTER_EVIDENCE_SOURCE_UNKNOWN:{finding['finding_id']}:{','.join(sorted(unknown_refs))}"
            )
    return sorted(set(violations))
