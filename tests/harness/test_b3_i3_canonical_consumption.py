import copy
import subprocess
import sys
from pathlib import Path

import pytest

from src.core.contract_validation import validate_against_schema
from src.scripts.check_b3_canonical_consumption import CONSUMERS, find_violations


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "src/scripts/check_b3_canonical_consumption.py"
SKILLS = tuple(consumer for consumer in CONSUMERS if "/skills/" in consumer)
HISTORICAL_SOURCES = (
    "workspace/01_canal_identidad.md",
    "workspace/02_reglas_editoriales.md",
    "workspace/03_formato_longform.md",
    "workspace/05_estilo_y_voz.md",
    "workspace/05c_voice_profile.md",
)


def candidate():
    return {
        "learning_id": "learning-001",
        "target_profile_id": "mas_alla_del_guion",
        "target_profile_version": "1.0.0",
        "observed_change": "Preferir aperturas directas.",
        "scope": "VOICE",
        "lineage": ["episode-001", "human-final-script"],
        "evidence_items": [
            {
                "source_id": "episode-001",
                "locator": "06_guion_longform_FINAL.md:12",
                "checksum": "a" * 64,
                "observation": "Se eliminó una apertura genérica.",
            }
        ],
        "confidence": 0.8,
        "examples": ["Abrir con la pregunta concreta."],
        "counterexamples": ["Abrir con una frase motivacional genérica."],
        "exceptions": [],
        "functional_decision": {"status": "PENDING"},
        "status_history": [{"status": "CANDIDATE", "recorded_at": "2026-07-22T20:00:00Z"}],
    }


def candidate_errors(value):
    errors = validate_against_schema(value, "editorial_learning_candidate")
    if value.get("functional_decision", {}).get("status") != "PENDING":
        errors.append("functional_decision.status debe ser PENDING para una salida nueva.")
    return errors


def test_all_b3_i3_consumers_use_canonical_editorial_reference():
    assert len(CONSUMERS) == 8
    consumer_paths = [ROOT / consumer for consumer in CONSUMERS]
    assert find_violations(consumer_paths) == []
    for path in consumer_paths:
        text = path.read_text(encoding="utf-8")
        assert "profile_id" in text
        assert "profile_version" in text
        assert "profile_checksum" in text
        assert "BLOCKED" in text
        assert "latest" not in text.lower()
    result = subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 0
    assert result.stdout.strip() == "PASS"


@pytest.mark.parametrize(
    "reference",
    (
        "workspace/05c_voice_profile.md",
        r"workspace\05c_voice_profile.md",
        "./workspace/05c_voice_profile.md",
        "workspace/./05c_voice_profile.md",
        "workspace/temp/../05c_voice_profile.md",
        "[voz](workspace/05c_voice_profile.md)",
        chr(96) + r"workspace\05c_voice_profile.md" + chr(96),
        "WORKSPACE/05C_VOICE_PROFILE.MD",
    ),
)
def test_gate_rejects_normalized_historical_references(tmp_path, reference):
    regressed = tmp_path / "consumer.md"
    regressed.write_text(f"Referencia: {reference}", encoding="utf-8")
    assert find_violations([regressed])
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--path", str(regressed)], cwd=ROOT, text=True, capture_output=True
    )
    assert result.returncode == 1


@pytest.mark.parametrize(
    "text",
    (
        "workspace/05c_voice_profile.mdx",
        "workspace/05c_voice_profile.md.backup",
        "workspace/otro_documento.md",
        "La palabra workspace no es una referencia.",
    ),
)
def test_gate_avoids_false_positives(tmp_path, text):
    candidate_path = tmp_path / "consumer.md"
    candidate_path.write_text(text, encoding="utf-8")
    assert find_violations([candidate_path]) == []


def test_learning_candidate_contract_and_initial_decision():
    valid = candidate()
    assert valid["target_profile_id"]
    assert valid["target_profile_version"]
    assert candidate_errors(valid) == []

    missing_lineage = copy.deepcopy(valid)
    del missing_lineage["lineage"]
    assert candidate_errors(missing_lineage)

    missing_checksum = copy.deepcopy(valid)
    del missing_checksum["evidence_items"][0]["checksum"]
    assert candidate_errors(missing_checksum)

    non_pending = copy.deepcopy(valid)
    non_pending["functional_decision"]["status"] = "APPROVED"
    assert candidate_errors(non_pending) == [
        "functional_decision.status debe ser PENDING para una salida nueva."
    ]


def test_learning_skill_is_candidate_only_and_qa_cannot_approve_identity():
    learning = (ROOT / ".agent/skills/skill_extraer_voice_learnings.md").read_text(encoding="utf-8")
    qa = (ROOT / ".agent/skills/skill_qa_editorial.md").read_text(encoding="utf-8")
    for field in (
        "learning_id",
        "target_profile_id",
        "target_profile_version",
        "observed_change",
        "scope",
        "lineage",
        "evidence_items",
        "confidence",
        "examples",
        "counterexamples",
        "exceptions",
        "functional_decision",
        "status_history",
    ):
        assert field in learning
    assert "EditorialLearningCandidate" in learning
    assert "12_editorial_learning_candidate.json" in learning
    assert "nunca escribir un perfil editorial" in learning
    assert "workspace/05c_voice_profile.md" not in learning
    assert "actualizar " not in learning.lower()
    assert "IDENTITY_STABLE" in qa
    assert "no los aprueba" in qa


def test_historical_sources_remain_noncanonical_and_skills_keep_safe_gates():
    assert all((ROOT / source).is_file() for source in HISTORICAL_SOURCES)
    for skill in SKILLS:
        text = (ROOT / skill).read_text(encoding="utf-8")
        assert "## Entrada" in text
        assert "BLOCKED" in text
        assert "active_editorial_profile.json" not in text
    assert "POLICY_DETECCION_PATRONES_Y_CLICHES_V2" in (
        ROOT / ".agent/workflows/piloto-outline.md"
    ).read_text(encoding="utf-8")
