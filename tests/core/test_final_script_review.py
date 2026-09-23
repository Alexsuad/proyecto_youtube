from __future__ import annotations

import hashlib

import pytest

from src.ai.manifest import canonical_json
from src.core.final_script_review import (
    FinalScriptReviewError,
    build_final_script_review,
    measure_duration_telemetry,
)
from src.core.editorial_profile_registry import load_active_profile_authority


PROFILE = {"profile_id": "mas_alla_del_guion", "profile_version": "1.2.2", "profile_checksum": load_active_profile_authority()["profile_checksum"]}
RUNS = {"producer_run_id": "RUN-PRODUCER", "editor_run_id": "RUN-EDITOR", "auditor_run_id": "RUN-AUDITOR", "review_actor_id": "YOUTUBE_ADAPTATION_AUDITOR", "producer_actor_id": "WRITING", "editor_actor_id": "EDITOR", "auditor_actor_id": "FINAL_EDITORIAL_AUDITOR"}


def _script(*, checksum: str | None = None, narrated_content: str | None = "uno dos tres cuatro") -> dict:
    script = {
        "episode_id": "EP-1",
        "source_script_version": "1.0.0",
        "content": "Texto completo del EditedScript.",
        "narrated_content": narrated_content,
    }
    script["checksum"] = checksum or hashlib.sha256(canonical_json(script)).hexdigest()
    return script


def _script_draft() -> dict:
    return {"episode_id": "EP-1", "narrative_plan_ref": "PLAN-1", "artifact_version": "1.0.0"}


def _plan(*, wpm_target: int | None = 100, wpm_provenance: str | None = "EPISODE_EXPLICIT", duration_target_minutes: int | None = 18) -> dict:
    return {
        "episode_id": "EP-1",
        "script_plan_id": "PLAN-1",
        "wpm_target": wpm_target,
        "wpm_provenance": wpm_provenance,
        "duration_target_minutes": duration_target_minutes,
    }


def _review(duration_telemetry: dict, *, script_checksum: str | None = None, lexical_findings: list[str] | None = None) -> dict:
    script_checksum = script_checksum or duration_telemetry.get("measured_script_checksum") or "a" * 64
    return build_final_script_review(
        review_id="FSR-1", episode_id="EP-1", artifact_id="SCRIPT-EDITED-1", script_version="1.1.0",
        script_checksum=script_checksum, profile_reference=PROFILE,
        visible_promise_ref="editorial_script_promise:SP-1@1.0.0", final_audit_ref="final_editorial_audit:A-1@1.1.0",
        final_audit_checksum="c" * 64, review_run_id="RUN-YT-REVIEW-1", duration_telemetry=duration_telemetry,
        lexical_findings=lexical_findings, created_at="2026-09-01T00:00:00Z", **RUNS,
    )


def test_final_script_review_binds_exact_script_and_keeps_sensors_non_normative() -> None:
    telemetry = measure_duration_telemetry(_script(), _plan(), script_draft=_script_draft())
    review = _review(telemetry, lexical_findings=["término contextual"])
    assert review["decision"] == "WARN"
    assert review["lexical_sensor"]["normative"] is False
    assert review["duration_telemetry"]["normative"] is False
    assert review["script_checksum"] == telemetry["measured_script_checksum"]


def test_duration_measurement_does_not_copy_human_target() -> None:
    telemetry = measure_duration_telemetry(_script(narrated_content="uno dos tres cuatro"), _plan(wpm_target=2), script_draft=_script_draft())

    assert telemetry["status"] == "MEASURED"
    assert telemetry["estimated_minutes"] == 2.0
    assert telemetry["duration_target_minutes"] == 18.0
    assert telemetry["estimated_minutes"] != telemetry["duration_target_minutes"]


def test_duration_measurement_persists_reproducible_provenance() -> None:
    script = _script()
    telemetry = measure_duration_telemetry(script, _plan(), script_draft=_script_draft())

    assert telemetry["measurement_method"]
    assert telemetry["word_count"] == 4
    assert telemetry["wpm_applied"] == 100
    assert telemetry["measured_script_checksum"] == script["checksum"]
    assert telemetry["wpm_provenance"] == "EPISODE_EXPLICIT"


def test_duration_measurement_is_unresolved_without_valid_wpm() -> None:
    telemetry = measure_duration_telemetry(_script(), _plan(wpm_target=None), script_draft=_script_draft())

    assert telemetry["status"] == "UNRESOLVED"
    assert telemetry["estimated_minutes"] is None


def test_duration_measurement_is_unresolved_without_wpm_provenance() -> None:
    telemetry = measure_duration_telemetry(
        _script(), _plan(wpm_provenance=None), script_draft=_script_draft()
    )

    assert telemetry["status"] == "UNRESOLVED"
    assert telemetry["wpm_applied"] is None


def test_duration_measurement_is_unresolved_without_explicit_narrated_text() -> None:
    telemetry = measure_duration_telemetry(_script(narrated_content=None), _plan(), script_draft=_script_draft())

    assert telemetry["status"] == "UNRESOLVED"
    assert telemetry["estimated_minutes"] is None


def test_duration_measurement_is_unresolved_without_script_checksum() -> None:
    script = _script()
    del script["checksum"]

    telemetry = measure_duration_telemetry(script, _plan(), script_draft=_script_draft())

    assert telemetry["status"] == "UNRESOLVED"
    assert telemetry["measured_script_checksum"] is None


def test_stale_duration_measurement_is_not_reused_for_a_new_script() -> None:
    old_telemetry = measure_duration_telemetry(_script(), _plan(), script_draft=_script_draft())

    review = _review(old_telemetry, script_checksum="b" * 64)

    assert review["duration_telemetry"]["status"] == "UNRESOLVED"
    assert review["duration_telemetry"]["measured_script_checksum"] is None


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
