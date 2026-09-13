from __future__ import annotations

import pytest

from src.core.final_script_review import FinalScriptReviewError, build_final_script_review
from src.core.editorial_profile_registry import load_active_profile_authority


PROFILE = {"profile_id": "mas_alla_del_guion", "profile_version": "1.2.2", "profile_checksum": load_active_profile_authority()["profile_checksum"]}
RUNS = {"producer_run_id": "RUN-PRODUCER", "editor_run_id": "RUN-EDITOR", "auditor_run_id": "RUN-AUDITOR", "review_actor_id": "YOUTUBE_ADAPTATION_AUDITOR", "producer_actor_id": "WRITING", "editor_actor_id": "EDITOR", "auditor_actor_id": "FINAL_EDITORIAL_AUDITOR"}


def test_final_script_review_binds_exact_script_and_keeps_sensors_non_normative() -> None:
    review = build_final_script_review(
        review_id="FSR-1", episode_id="EP-1", artifact_id="SCRIPT-EDITED-1", script_version="1.1.0",
        script_checksum="a" * 64, profile_reference=PROFILE,
        visible_promise_ref="editorial_script_promise:SP-1@1.0.0", final_audit_ref="final_editorial_audit:A-1@1.1.0",
        final_audit_checksum="c" * 64, review_run_id="RUN-YT-REVIEW-1",
        **RUNS,
        lexical_findings=["término contextual"], estimated_minutes=18.5, target_range=(18, 22),
        created_at="2026-09-01T00:00:00Z",
    )
    assert review["decision"] == "WARN"
    assert review["lexical_sensor"]["normative"] is False
    assert review["duration_telemetry"]["normative"] is False
    assert review["script_checksum"] == "a" * 64


def test_final_script_review_requires_exact_identity() -> None:
    with pytest.raises(FinalScriptReviewError, match="exact script identity"):
        build_final_script_review(
            review_id="FSR-1", episode_id="EP-1", artifact_id="", script_version="1.1.0",
            script_checksum="a" * 64, profile_reference=PROFILE,
            visible_promise_ref="editorial_script_promise:SP-1@1.0.0", final_audit_ref="final_editorial_audit:A-1@1.1.0",
            final_audit_checksum="c" * 64, review_run_id="RUN-YT-REVIEW-1", **RUNS,
        )


def test_final_script_review_rejects_stale_profile_and_incompatible_actor() -> None:
    with pytest.raises(FinalScriptReviewError, match="profile"):
        build_final_script_review(
            review_id="FSR-1", episode_id="EP-1", artifact_id="SCRIPT-EDITED-1", script_version="1.1.0",
            script_checksum="a" * 64, profile_reference={**PROFILE, "profile_checksum": "b" * 64},
            visible_promise_ref="editorial_script_promise:SP-1@1.0.0", final_audit_ref="final_editorial_audit:A-1@1.1.0",
            final_audit_checksum="c" * 64, review_run_id="RUN-YT-REVIEW-1", **RUNS,
        )
