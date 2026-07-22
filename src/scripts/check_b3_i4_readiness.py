"""Preflight de solo lectura para la evidencia editorial escrita de B3-I4."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.contract_validation import validate_against_schema


DEFAULT_MANIFEST = ROOT / "profiles/voice/corpus_manifest.json"
DEFAULT_PROFILE = ROOT / "profiles/editorial/mas_alla_del_guion/1.0.0/profile_payload.json"


def _safe_sample_path(locator: str, repository_root: Path) -> Path | None:
    candidate = Path(locator)
    if candidate.is_absolute() or any(part == ".." for part in candidate.parts):
        return None
    return repository_root / candidate


def _file_checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assess_manifest(manifest_path: Path, profile_path: Path, repository_root: Path) -> dict[str, Any]:
    """Assess optional authentic samples without compiling or activating a profile."""
    result = {
        "VOICE_EVIDENCE_LEVEL": "UNKNOWN",
        "AUTHENTIC_EDITORIAL_WRITING_SAMPLE_STATUS": "NOT_AVAILABLE",
        "AUTHORIZED_COMPLEMENTARY_SAMPLES": 0,
        "INVALID_OR_INCOMPLETE_SAMPLES": 0,
        "CORPUS_READY_FOR_B3-I4": "NO",
        "violations": [],
    }
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        result["violations"].append(f"Artefacto inválido: {error}")
        return result

    profile_errors = validate_against_schema(profile, "editorial_profile")
    if profile_errors:
        result["violations"].extend(f"Perfil: {error}" for error in profile_errors)
        return result

    corpus_status = profile["voice_profile"]["corpus_status"]
    result["VOICE_EVIDENCE_LEVEL"] = corpus_status
    samples = manifest.get("voice_samples")
    if not isinstance(samples, list):
        result["violations"].append("voice_samples debe ser una lista.")
        return result

    valid_sample_ids: set[str] = set()
    for sample in samples:
        sample_id = sample.get("sample_id", "UNKNOWN") if isinstance(sample, dict) else "UNKNOWN"
        errors = validate_against_schema(sample, "voice_sample") if isinstance(sample, dict) else ["Muestra no es objeto."]
        if not errors:
            file_path = _safe_sample_path(sample["locator"], repository_root)
            if file_path is None or not file_path.is_file():
                errors.append("Archivo físico ausente o fuera del repositorio.")
            elif _file_checksum(file_path).casefold() != sample["checksum"].casefold():
                errors.append("Checksum no verificable contra el archivo físico.")
            if sample["usage_authorization"] != "AUTHORIZED":
                errors.append("Autorización de uso ausente o no autorizada.")

        if errors:
            result["INVALID_OR_INCOMPLETE_SAMPLES"] += 1
            result["violations"].append(f"{sample_id}: {'; '.join(errors)}")
            continue
        if sample["classification"] != "EXCLUDED":
            valid_sample_ids.add(sample["sample_id"])
            result["AUTHENTIC_EDITORIAL_WRITING_SAMPLE_STATUS"] = "AVAILABLE"
        if sample["classification"] == "COMPLEMENTARY":
            result["AUTHORIZED_COMPLEMENTARY_SAMPLES"] += 1

    if corpus_status == "AUTHENTIC_CORPUS_VALIDATED":
        approved = set(profile["voice_profile"]["approved_sample_ids"])
        if not valid_sample_ids:
            result["violations"].append("AUTHENTIC_CORPUS_VALIDATED requiere evidencia auténtica válida.")
        elif not approved or not approved.issubset(valid_sample_ids):
            result["violations"].append("Las muestras aprobadas no coinciden con el corpus auténtico válido.")

    result["CORPUS_READY_FOR_B3-I4"] = "YES" if not result["violations"] else "NO"
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    parser.add_argument("--repository-root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    result = assess_manifest(args.manifest, args.profile, args.repository_root)
    for key in (
        "VOICE_EVIDENCE_LEVEL",
        "AUTHENTIC_EDITORIAL_WRITING_SAMPLE_STATUS",
        "AUTHORIZED_COMPLEMENTARY_SAMPLES",
        "INVALID_OR_INCOMPLETE_SAMPLES",
        "CORPUS_READY_FOR_B3-I4",
    ):
        print(f"{key}: {result[key]}")
    for violation in result["violations"]:
        print(f"BLOCKED: {violation}", file=sys.stderr)
    return 0 if result["CORPUS_READY_FOR_B3-I4"] == "YES" else 2


if __name__ == "__main__":
    raise SystemExit(main())
