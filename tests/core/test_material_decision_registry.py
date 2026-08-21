"""Pruebas del mecanismo de decisiones materiales y vista legacy derivada (PLAN 008, Misión 1).

Cubre las invariantes protegidas tras la revisión correctiva:
- sucesión canónica única (superseded_by) sin ciclos ni relaciones incoherentes;
- autoridad dentro del vocabulario canónico de gobernanza;
- evidencia obligatoria y referencias locales resolubles;
- consumer/sucesor local inexistente rechazado;
- ejecutabilidad incompatible con documentación legacy;
- vista per-file derivada con duplicación material.
"""

import json
import subprocess
import sys
from pathlib import Path

from src.core.material_decision_registry import (
    AUTHORITIES,
    expected_view_path,
    registry_path,
    render_view,
    validate_local_refs,
    validate_registry,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
VALID = json.loads(Path(registry_path()).read_text(encoding="utf-8"))

REAL_LEGACY_FILE = "README.md"
REAL_EVIDENCE = "README.md"


def _copy() -> dict:
    return json.loads(json.dumps(VALID))


def _decision(
    decision_id: str,
    *,
    state: str,
    subject: str,
    superseded_by=None,
    authority: str = "TECHNICAL_GOVERNANCE",
    evidence=None,
) -> dict:
    return {
        "decision_id": decision_id,
        "subject_ref": subject,
        "decision": "Decisión de prueba.",
        "reason": "Razón de prueba.",
        "authority": authority,
        "state": state,
        "evidence_refs": evidence if evidence is not None else [REAL_EVIDENCE],
        "superseded_by": superseded_by,
        "recorded_at": "2026-08-20T00:00:00Z",
    }


def _entry(file_path: str, decision_id: str, **overrides) -> dict:
    entry = {
        "file_path": file_path,
        "decision_id": decision_id,
        "estado": "SUSTITUIDA",
        "autoridad_sucesor": None,
        "consumer_activo": None,
        "duplicacion_material": "Duplicación de prueba.",
        "disposicion": "MIGRATION_SOURCE",
        "ejecutable": False,
    }
    entry.update(overrides)
    return entry


def _registry(decisions, legacy_files) -> dict:
    return {
        "registry_version": "1.0.0",
        "decisions": decisions,
        "legacy_files": legacy_files,
    }


def _valid_registry() -> dict:
    return _registry(
        [
            _decision("MD-A", state="VIGENTE", subject="subject-A"),
            _decision("MD-B", state="SUSTITUIDA", subject="subject-B", superseded_by="MD-A"),
        ],
        [_entry(REAL_LEGACY_FILE, "MD-B")],
    )


def _path_registry(*, file_path="legacy.md", evidence_refs=None, consumer=None, successor=None):
    return _registry(
        [_decision("MD-PATH", state="VIGENTE", subject="path-subject", evidence=evidence_refs or ["docs/evidence.md"])],
        [_entry(file_path, "MD-PATH", consumer_activo=consumer, autoridad_sucesor=successor)],
    )


def _prepare_path_root(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "repo"
    outside = tmp_path / "outside"
    (root / "docs").mkdir(parents=True)
    (root / "workspace").mkdir()
    (root / "plans").mkdir()
    (outside / "nested").mkdir(parents=True)
    for path in (root / "docs/evidence.md", root / "workspace/legacy.md", root / "plans/consumer.md", outside / "nested/outside.md"):
        path.write_text("fixture", encoding="utf-8")
    return root, outside


def _violations(data) -> list[str]:
    return validate_registry(data) + validate_local_refs(data, REPO_ROOT)


def test_real_registry_is_valid():
    assert validate_registry(VALID) == []
    assert validate_local_refs(VALID, REPO_ROOT) == []


def test_real_legacy_file_refs_resolve():
    assert validate_local_refs(VALID, REPO_ROOT) == []


def test_view_is_derived_from_registry():
    committed = expected_view_path().read_text(encoding="utf-8")
    assert committed == render_view(VALID)


def test_gate_script_passes_on_real_registry():
    result = subprocess.run(
        [sys.executable, "src/scripts/check_material_decisions.py"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "PASS" in result.stdout


def test_valid_minimal_registry_is_valid():
    assert _violations(_valid_registry()) == []


def test_valid_succession_chain_is_accepted():
    data = _registry(
        [
            _decision("MD-A", state="VIGENTE", subject="a"),
            _decision("MD-B", state="SUSTITUIDA", subject="b", superseded_by="MD-C"),
            _decision("MD-C", state="SUSTITUIDA", subject="c", superseded_by="MD-A"),
        ],
        [_entry(REAL_LEGACY_FILE, "MD-C")],
    )
    assert _violations(data) == []


def test_duplicate_decision_id_is_violation():
    data = _copy()
    data["decisions"].append(dict(data["decisions"][0]))
    assert any("duplicados" in v for v in validate_registry(data))


def test_successor_to_missing_id_is_violation():
    data = _valid_registry()
    data["decisions"][0]["superseded_by"] = "MD-UNKNOWN"
    assert any("MD-UNKNOWN" in v for v in _violations(data))


def test_self_reference_is_violation():
    data = _valid_registry()
    data["decisions"][0]["superseded_by"] = data["decisions"][0]["decision_id"]
    assert any("sí mismo" in v for v in _violations(data))


def test_two_cycle_is_violation():
    data = _registry(
        [
            _decision("MD-A", state="SUSTITUIDA", subject="a", superseded_by="MD-B"),
            _decision("MD-B", state="SUSTITUIDA", subject="b", superseded_by="MD-A"),
        ],
        [_entry(REAL_LEGACY_FILE, "MD-A")],
    )
    assert any("ciclo de sucesión" in v for v in validate_registry(data))


def test_three_cycle_is_violation():
    data = _registry(
        [
            _decision("MD-A", state="SUSTITUIDA", subject="a", superseded_by="MD-B"),
            _decision("MD-B", state="SUSTITUIDA", subject="b", superseded_by="MD-C"),
            _decision("MD-C", state="SUSTITUIDA", subject="c", superseded_by="MD-A"),
        ],
        [_entry(REAL_LEGACY_FILE, "MD-A")],
    )
    assert any("ciclo de sucesión" in v for v in validate_registry(data))


def test_successor_historica_is_contradictory():
    data = _registry(
        [
            _decision("MD-A", state="HISTORICA", subject="a"),
            _decision("MD-B", state="SUSTITUIDA", subject="b", superseded_by="MD-A"),
        ],
        [_entry(REAL_LEGACY_FILE, "MD-B")],
    )
    assert any("HISTORICA" in v for v in validate_registry(data))


def test_vigente_with_superseded_by_is_violation():
    data = _valid_registry()
    data["decisions"][0]["superseded_by"] = data["decisions"][1]["decision_id"]
    assert any("VIGENTE no puede tener superseded_by" in v for v in _violations(data))


def test_sustituida_without_superseded_by_is_violation():
    data = _valid_registry()
    data["decisions"][1]["superseded_by"] = None
    assert any("SUSTITUIDA requiere superseded_by" in v for v in _violations(data))


def test_historica_with_succession_is_violation():
    data = _valid_registry()
    data["decisions"][1]["state"] = "HISTORICA"
    data["decisions"][1]["superseded_by"] = data["decisions"][0]["decision_id"]
    assert any("HISTORICA no puede tener sucesión" in v for v in _violations(data))


def test_invented_authority_is_rejected():
    data = _valid_registry()
    data["decisions"][0]["authority"] = "BANANA"
    assert any("BANANA" in v for v in _violations(data))


def test_authority_vocabulary_matches_canonical_config():
    with open(Path(REPO_ROOT) / "config" / "runtime_contamination_policy.json", encoding="utf-8") as fh:
        neutral_terms = set(json.load(fh)["neutral_terms"])
    assert AUTHORITIES == neutral_terms


def test_missing_reason_is_violation():
    data = _copy()
    del data["decisions"][0]["reason"]
    assert any("reason" in v for v in validate_registry(data))


def test_missing_authority_is_violation():
    data = _copy()
    del data["decisions"][0]["authority"]
    assert any("authority" in v for v in validate_registry(data))


def test_missing_state_is_violation():
    data = _copy()
    del data["decisions"][0]["state"]
    assert any("state" in v for v in validate_registry(data))


def test_empty_evidence_is_rejected():
    data = _valid_registry()
    data["decisions"][0]["evidence_refs"] = []
    assert any("evidence" in v.lower() for v in _violations(data))


def test_nonexistent_evidence_path_is_rejected():
    data = _valid_registry()
    data["decisions"][0]["evidence_refs"] = ["ruta/inexistente.md"]
    assert any("inexistente" in v for v in _violations(data))


def test_nonexistent_consumer_is_rejected():
    data = _valid_registry()
    data["legacy_files"][0]["consumer_activo"] = "no/existe/workflow.md"
    assert any("consumer activo inexistente" in v for v in _violations(data))


def test_nonexistent_authority_successor_is_rejected():
    data = _valid_registry()
    data["legacy_files"][0]["autoridad_sucesor"] = "does/not/exist.md"
    assert any("autoridad/sucesor inexistente" in v for v in _violations(data))


def test_absolute_external_reference_is_rejected(tmp_path):
    root, outside = _prepare_path_root(tmp_path)
    data = _path_registry(file_path=str(outside / "nested/outside.md"))
    violations = validate_local_refs(data, root)
    assert any("archivo legacy fuera de REPO_ROOT" in v for v in violations)


def test_absolute_external_evidence_is_rejected(tmp_path):
    root, outside = _prepare_path_root(tmp_path)
    data = _path_registry(
        file_path="workspace/legacy.md",
        evidence_refs=[str(outside / "nested/outside.md")],
    )
    assert any("evidencia fuera de REPO_ROOT" in v for v in validate_local_refs(data, root))


def test_traversal_external_reference_is_rejected(tmp_path):
    root, outside = _prepare_path_root(tmp_path)
    data = _path_registry(file_path="../outside/nested/outside.md")
    violations = validate_local_refs(data, root)
    assert any("archivo legacy fuera de REPO_ROOT" in v for v in violations)


def test_valid_internal_paths_remain_accepted(tmp_path):
    root, _ = _prepare_path_root(tmp_path)
    data = _path_registry(
        file_path="workspace/legacy.md",
        evidence_refs=["docs/evidence.md"],
        consumer="plans/consumer.md",
        successor="plans/",
    )
    assert validate_local_refs(data, root) == []


def test_external_consumer_is_rejected(tmp_path):
    root, outside = _prepare_path_root(tmp_path)
    data = _path_registry(file_path="workspace/legacy.md", consumer=str(outside / "nested/outside.md"))
    assert any("consumer activo fuera de REPO_ROOT" in v for v in validate_local_refs(data, root))


def test_external_legacy_file_is_rejected(tmp_path):
    root, outside = _prepare_path_root(tmp_path)
    data = _path_registry(file_path=str(outside / "nested/outside.md"))
    assert any("archivo legacy fuera de REPO_ROOT" in v for v in validate_local_refs(data, root))


def test_external_authority_successor_is_rejected(tmp_path):
    root, outside = _prepare_path_root(tmp_path)
    data = _path_registry(file_path="workspace/legacy.md", successor=str(outside / "nested"))
    assert any("autoridad/sucesor fuera de REPO_ROOT" in v for v in validate_local_refs(data, root))


def test_legacy_file_cannot_be_vigente():
    data = _valid_registry()
    data["legacy_files"][0]["estado"] = "VIGENTE"
    violations = validate_registry(data)
    assert any("archivo legacy no puede tener estado VIGENTE" in v for v in violations)


def test_derived_view_cannot_be_evidence():
    data = _valid_registry()
    data["decisions"][0]["evidence_refs"] = ["docs/legacy/LEGACY_PER_FILE_VIEW.md"]
    assert any("evidencia derivada" in v for v in validate_registry(data))


def test_real_registry_has_no_derived_view_evidence():
    assert all(
        "docs/legacy/LEGACY_PER_FILE_VIEW.md" not in decision["evidence_refs"]
        for decision in VALID["decisions"]
    )


def test_external_symlink_is_rejected_when_supported(tmp_path):
    root, outside = _prepare_path_root(tmp_path)
    link = root / "workspace" / "linked.md"
    try:
        link.symlink_to(outside / "nested/outside.md")
    except (OSError, NotImplementedError):
        import pytest

        pytest.skip("el entorno no permite crear symlinks")
    data = _path_registry(file_path="workspace/linked.md")
    assert any("archivo legacy fuera de REPO_ROOT" in v for v in validate_local_refs(data, root))


def test_executable_legacy_is_rejected():
    data = _valid_registry()
    data["legacy_files"][0]["ejecutable"] = True
    assert any("no puede ser ejecutable" in v for v in _violations(data))


def test_duplicate_file_path_is_violation():
    data = _copy()
    data["legacy_files"].append(dict(data["legacy_files"][0]))
    assert any("file_path duplicados" in v for v in validate_registry(data))


def test_legacy_file_with_missing_decision_is_violation():
    data = _copy()
    data["legacy_files"][0]["decision_id"] = "MD-UNKNOWN"
    assert any("MD-UNKNOWN" in v for v in validate_registry(data))


def test_duplicate_vigente_for_subject_is_violation():
    data = _copy()
    data["decisions"][1]["subject_ref"] = data["decisions"][0]["subject_ref"]
    assert any("más de una decisión VIGENTE" in v for v in validate_registry(data))


def test_view_includes_duplicacion_material():
    view = render_view(VALID)
    assert "Duplicación material" in view
    policy_entry = next(e for e in VALID["legacy_files"] if e["file_path"].endswith("POLICY_DETECCION_PATRONES_Y_CLICHES_V2.md"))
    assert policy_entry["duplicacion_material"] in view
    assert "templates/evento_template_v2.md" in view
    assert "Consumidor activo" in view
    assert ".agent/workflows/piloto-outline.md" not in view


def test_view_divergence_is_detected():
    data = _copy()
    data["legacy_files"][0]["duplicacion_material"] = "Cambio no derivado"
    assert render_view(data) != expected_view_path().read_text(encoding="utf-8")


def test_supersedes_field_is_no_longer_used():
    for decision in VALID["decisions"]:
        assert "supersedes" not in decision
