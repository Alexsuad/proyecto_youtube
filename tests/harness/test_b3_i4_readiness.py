import copy
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from src.scripts.check_b3_i4_readiness import assess_manifest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "src/scripts/check_b3_i4_readiness.py"
PAYLOAD = ROOT / "profiles/editorial/mas_alla_del_guion/1.0.0/profile_payload.json"


def sample(locator: str, checksum: str) -> dict:
    return {
        "sample_id": "WRITING-001",
        "locator": locator,
        "checksum": checksum,
        "authorship": "OWNER",
        "text_type": "PERSONAL_TEXT",
        "classification": "AUTHENTIC",
        "usage_authorization": "AUTHORIZED",
        "representativeness": "HIGH",
        "recorded_at": "2026-07-22T20:00:00Z",
        "lineage": ["OWNER_PROVIDED"],
        "inclusion_reason": "Evidencia editorial escrita autorizada.",
    }


def write_manifest(tmp_path: Path, samples: list[dict]) -> Path:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"manifest_id": "test", "voice_samples": samples}), encoding="utf-8")
    return manifest


def write_profile(tmp_path: Path, corpus_status: str, approved_sample_ids: list[str] | None = None) -> Path:
    profile = json.loads(PAYLOAD.read_text(encoding="utf-8"))
    profile["voice_profile"]["corpus_status"] = corpus_status
    profile["voice_profile"]["approved_sample_ids"] = approved_sample_ids or []
    path = tmp_path / "profile.json"
    path.write_text(json.dumps(profile), encoding="utf-8")
    return path


def complete_manifest(tmp_path: Path) -> Path:
    source = tmp_path / "profiles/voice/samples/writing.md"
    source.parent.mkdir(parents=True)
    source.write_text("Texto editorial sintético autorizado.", encoding="utf-8")
    checksum = hashlib.sha256(source.read_bytes()).hexdigest()
    return write_manifest(tmp_path, [sample("profiles/voice/samples/writing.md", checksum)])


def test_empty_specification_based_corpus_passes_without_audio_or_transcription(tmp_path):
    manifest = write_manifest(tmp_path, [])
    profile = write_profile(tmp_path, "SPECIFICATION_BASED")
    result = assess_manifest(manifest, profile, tmp_path)
    assert result["VOICE_EVIDENCE_LEVEL"] == "SPECIFICATION_BASED"
    assert result["AUTHENTIC_EDITORIAL_WRITING_SAMPLE_STATUS"] == "NOT_AVAILABLE"
    assert result["CORPUS_READY_FOR_B3-I4"] == "YES"


def test_validated_authentic_corpus_cannot_be_empty(tmp_path):
    result = assess_manifest(
        write_manifest(tmp_path, []),
        write_profile(tmp_path, "AUTHENTIC_CORPUS_VALIDATED"),
        tmp_path,
    )
    assert result["CORPUS_READY_FOR_B3-I4"] == "NO"


def test_authentic_sample_passes_without_primary_semantics(tmp_path):
    manifest = complete_manifest(tmp_path)
    profile = write_profile(tmp_path, "AUTHENTIC_CORPUS_PARTIAL")
    result = assess_manifest(manifest, profile, tmp_path)
    assert result["AUTHENTIC_EDITORIAL_WRITING_SAMPLE_STATUS"] == "AVAILABLE"
    assert "PRIMARY_SAMPLE_AVAILABLE" not in result
    assert result["CORPUS_READY_FOR_B3-I4"] == "YES"


def test_future_incomplete_writing_sample_fails(tmp_path):
    manifest = complete_manifest(tmp_path)
    invalid = json.loads(manifest.read_text(encoding="utf-8"))["voice_samples"][0]
    del invalid["lineage"]
    result = assess_manifest(write_manifest(tmp_path, [invalid]), write_profile(tmp_path, "SPECIFICATION_BASED"), tmp_path)
    assert result["INVALID_OR_INCOMPLETE_SAMPLES"] == 1
    assert result["CORPUS_READY_FOR_B3-I4"] == "NO"


def test_missing_positive_or_negative_examples_fails(tmp_path):
    manifest = write_manifest(tmp_path, [])
    for field in ("approved_positive_examples", "approved_negative_examples"):
        profile = json.loads(PAYLOAD.read_text(encoding="utf-8"))
        del profile["voice_profile"][field]
        path = tmp_path / f"{field}.json"
        path.write_text(json.dumps(profile), encoding="utf-8")
        assert assess_manifest(manifest, path, tmp_path)["CORPUS_READY_FOR_B3-I4"] == "NO"


def test_preflight_is_read_only_and_never_activates(tmp_path):
    manifest = write_manifest(tmp_path, [])
    profile = write_profile(tmp_path, "SPECIFICATION_BASED")
    before = manifest.read_bytes()
    command = subprocess.run(
        [sys.executable, str(SCRIPT), "--manifest", str(manifest), "--profile", str(profile), "--repository-root", str(tmp_path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        env={**os.environ, "PYTHONPATH": str(ROOT)},
    )
    assert command.returncode == 0
    assert manifest.read_bytes() == before
    assert not (tmp_path / "config/active_editorial_profile.json").exists()
    assert not (tmp_path / "profiles/editorial/mas_alla_del_guion/1.0.0/editorial_profile.json").exists()
