import json

import pytest

from src.core.duration_envelope import load_duration_envelope
from src.core.status import GateStatus
from src.scripts.qa_duracion_guion import evaluate, resolve_duration_parameters
from tests.harness.test_youtube_adaptation_b5_i2 import _paths


def _episode(tmp_path, words=1800):
    episode = tmp_path / "ep-1"
    episode.mkdir()
    (episode / "06_guion_longform.md").write_text("palabra " * words, encoding="utf-8")
    return episode


def test_ephemeral_duration_envelope_precedes_historical_fallback(tmp_path):
    result = evaluate(
        _episode(tmp_path),
        wpm=144,
        minimum=18,
        maximum=22,
        duration_envelope={"duration_assessment": {"recommended_range": "17-19 minutos", "wpm": 100}},
    )
    assert result.status is GateStatus.PASS
    assert result.evidence["duration_policy_source"] == "EPISODIC_YT_DURATION_ENVELOPE"
    assert result.evidence["target"] == [17, 19]
    assert result.evidence["wpm"] == 100


def test_duration_uses_explicit_technical_fallback_without_envelope(tmp_path):
    result = evaluate(_episode(tmp_path), wpm=100, minimum=17, maximum=19)
    assert result.status is GateStatus.PASS
    assert result.evidence["duration_policy_source"] == "TECHNICAL_FALLBACK"


def test_invalid_duration_envelope_does_not_silently_fallback(tmp_path):
    result = evaluate(
        _episode(tmp_path),
        wpm=100,
        minimum=17,
        maximum=19,
        duration_envelope={"duration_assessment": {"recommended_range": "pendiente"}},
    )
    assert result.status is GateStatus.FAIL
    assert any("recommended_range" in item for item in result.violations)


def test_duration_parameter_resolver_marks_fallback_as_technical():
    assert resolve_duration_parameters(None, 144, 18, 22) == (144, 18, 22, "TECHNICAL_FALLBACK")


def test_duration_envelope_loader_requires_existing_canonical_package_and_episode(tmp_path):
    _, _, envelope_path, review_path, registry_path = _paths(tmp_path)
    _, metadata = load_duration_envelope(
        envelope_path,
        "EP-1",
        review_path=review_path,
        registry_path=registry_path,
    )
    assert metadata["duration_envelope_schema"] == "youtube_adaptation_b5_i2_package"
    assert metadata["duration_envelope_episode_id"] == "EP-1"
    with pytest.raises(ValueError, match="otro episodio"):
        load_duration_envelope(
            envelope_path,
            "EP-2",
            review_path=review_path,
            registry_path=registry_path,
        )


def test_duration_envelope_loader_rejects_unverified_provenance(tmp_path):
    _, _, envelope_path, review_path, registry_path = _paths(tmp_path)
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["runs"][0]["producer_run_id"] = "RUN-UNVERIFIED"
    registry_path.write_text(json.dumps(registry), encoding="utf-8")
    with pytest.raises(ValueError, match="autoridad aprobada|provenance"):
        load_duration_envelope(
            envelope_path,
            "EP-1",
            review_path=review_path,
            registry_path=registry_path,
        )


def test_duration_envelope_loader_rejects_blocked_review(tmp_path):
    _, review, envelope_path, review_path, registry_path = _paths(tmp_path)
    review["decision"] = "BLOCK"
    review["duration_assessment"]["decision"] = "BLOCK"
    review["capability_results"]["YT_DURATION_ENVELOPE"]["decision"] = "BLOCK"
    review["blocking_reasons"] = ["No se puede cerrar el envelope."]
    review_path.write_text(json.dumps(review), encoding="utf-8")
    from tests.harness.test_youtube_adaptation_b5_i2 import _sync_review_registry_checksum

    _sync_review_registry_checksum(registry_path, review_path)
    with pytest.raises(ValueError, match="autoridad aprobada|review"):
        load_duration_envelope(
            envelope_path,
            "EP-1",
            review_path=review_path,
            registry_path=registry_path,
        )
