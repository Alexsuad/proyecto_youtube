"""Validation for the episode-owned narration speed authority."""

from __future__ import annotations

from typing import Any


WPM_PROVENANCES = frozenset({"EPISODE_EXPLICIT", "SUGGESTED_ACCEPTED"})


def normalize_episode_wpm(
    wpm_target: Any,
    wpm_provenance: Any,
) -> tuple[int | None, str | None]:
    """Return a complete episode WPM binding without supplying a fallback."""
    if wpm_target is None and wpm_provenance is None:
        return None, None
    if isinstance(wpm_target, bool) or not isinstance(wpm_target, int) or wpm_target <= 0:
        raise ValueError("wpm_target debe ser un entero positivo o null.")
    if wpm_provenance not in WPM_PROVENANCES:
        raise ValueError("wpm_provenance debe ser EPISODE_EXPLICIT o SUGGESTED_ACCEPTED.")
    return wpm_target, str(wpm_provenance)
