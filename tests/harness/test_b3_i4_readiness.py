import copy
import os
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from src.scripts.check_b3_i4_readiness import assess_manifest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "src/scripts/check_b3_i4_readiness.py"


def sample(locator: str, checksum: str) -> dict:
    return {
        "sample_id": "PRIMARY-001",
        "locator": locator,
        "checksum": checksum,
        "authorship": "OWNER",
        "text_type": "PERSONAL_TEXT",
        "classification": "CANONICAL",
        "usage_authorization": "AUTHORIZED",
        "representativeness": "HIGH",
        "recorded_at": "2026-07-22T20:00:00Z",
        "lineage": ["OWNER_PROVIDED"],
        "inclusion_reason": "Muestra principal autorizada.",
    }


def write_manifest(tmp_path: Path, samples: list[dict]) -> Path:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"manifest_id": "test", "voice_samples": samples}), encoding="utf-8")
    return manifest


def complete_manifest(tmp_path: Path) -> Path:
    source = tmp_path / "profiles/voice/samples/primary.md"
    source.parent.mkdir(parents=True)
    source.write_text("Texto real sintético autorizado.", encoding="utf-8")
    checksum = hashlib.sha256(source.read_bytes()).hexdigest()
    return write_manifest(tmp_path, [sample("profiles/voice/samples/primary.md", checksum)])


def test_missing_primary_blocks(tmp_path):
    result = assess_manifest(write_manifest(tmp_path, []), tmp_path)
    assert result["PRIMARY_SAMPLE_AVAILABLE"] == "NO"
    assert result["CORPUS_READY_FOR_B3-I4"] == "NO"


def test_missing_authorization_checksum_or_lineage_blocks(tmp_path):
    manifest = complete_manifest(tmp_path)
    baseline = json.loads(manifest.read_text(encoding="utf-8"))["voice_samples"][0]
    for field, value in (
        ("usage_authorization", "NOT_AUTHORIZED"),
        ("checksum", ""),
        ("lineage", []),
    ):
        invalid = copy.deepcopy(baseline)
        invalid[field] = value
        result = assess_manifest(write_manifest(tmp_path, [invalid]), tmp_path)
        assert result["CORPUS_READY_FOR_B3-I4"] == "NO"
        assert result["INVALID_OR_INCOMPLETE_SAMPLES"] == 1


def test_missing_physical_file_blocks(tmp_path):
    missing = sample("profiles/voice/samples/missing.md", "a" * 64)
    result = assess_manifest(write_manifest(tmp_path, [missing]), tmp_path)
    assert result["CORPUS_READY_FOR_B3-I4"] == "NO"
    assert result["INVALID_OR_INCOMPLETE_SAMPLES"] == 1


def test_complete_synthetic_corpus_passes_without_writes(tmp_path):
    manifest = complete_manifest(tmp_path)
    before = manifest.read_bytes()
    result = assess_manifest(manifest, tmp_path)
    assert result["PRIMARY_SAMPLE_AVAILABLE"] == "YES"
    assert result["AUTHORIZED_COMPLEMENTARY_SAMPLES"] == 0
    assert result["CORPUS_READY_FOR_B3-I4"] == "YES"
    assert manifest.read_bytes() == before
    assert not (tmp_path / "config/active_editorial_profile.json").exists()
    assert not (tmp_path / "profiles/editorial/mas_alla_del_guion/1.0.0/editorial_profile.json").exists()

    command = subprocess.run(
        [sys.executable, str(SCRIPT), "--manifest", str(manifest), "--repository-root", str(tmp_path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        env={**os.environ, "PYTHONPATH": str(ROOT)},
    )
    assert command.returncode == 0
    assert "CORPUS_READY_FOR_B3-I4: YES" in command.stdout
