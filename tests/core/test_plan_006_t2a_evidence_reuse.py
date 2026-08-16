"""T2-A tests — evidence reuse + semantic applicability (PLAN 006)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from src.core.evidence_reuse import (
    REUSE,
    RERUN_REQUIRED,
    TARGETED_REVERIFY,
    UNVERIFIABLE,
    IntendedUse,
    MaterialDependency,
    evaluate_evidence_reuse,
)
from src.core.historical_completion import freeze_completion_snapshot


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _report(
    repo: Path,
    name: str,
    source: str,
    content: str,
    *,
    scope: str = "src/core/x.py",
    coverage_required: str = "module",
    intended_assurance: str = "smoke",
    environment: str = "ANY",
    repository_revision: str = "REV-1",
) -> str:
    (repo / "reports/implementation/plan_006").mkdir(parents=True, exist_ok=True)
    (repo / source).parent.mkdir(parents=True, exist_ok=True)
    source_path = repo / source
    source_path.write_text(content, encoding="utf-8")
    payload = {
        "schema_version": "1.0.0",
        "plan_id": "PLAN_006",
        "artifact_id": "PLAN_006_T2A",
        "mission_id": "T2A_TEST",
        "increment": "T2-A",
        "repository_revision": repository_revision,
        "generated_at": "2026-08-13T00:00:00Z",
        "source_inputs": [{"path": source, "sha256": _sha(content.encode())}],
        "evidence_refs": [source],
        "semantic_applicability": {
            "scope": scope,
            "coverage_required": coverage_required,
            "intended_assurance": intended_assurance,
            "environment": environment,
            "repository_revision": repository_revision,
        },
        "limitations": [],
        "result": "PASS",
        "evidence_identity_sha256": "a" * 64,
    }
    report_path = repo / "reports/implementation/plan_006" / name
    report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    identity = dict(payload)
    identity.pop("evidence_identity_sha256", None)
    identity.pop("generated_at", None)
    payload["evidence_identity_sha256"] = _sha(json.dumps(identity, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode())
    report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return f"reports/implementation/plan_006/{name}"


def _snapshot(live_sha: str):
    return freeze_completion_snapshot(
        mission_id="T2A_TEST",
        mission_contract_sha256="a" * 64,
        authorization_artifact_sha256="b" * 64,
        authorized_scope_sha256="c" * 64,
        live_state_path="plans/001_CONTROL_OPERATIVO.md",
        live_state_sha256_at_execution=live_sha,
        authority_ref="config/authority.json",
        authority_sha256="e" * 64,
        repository_revision="REV-1",
        required_test_identities=("t",),
        evidence_identities=("e",),
        git_binding={"head": "abc"},
        completion_result="PASS",
    )


def test_fresh_evidence_with_unchanged_deps_reuses(tmp_path):
    repo = tmp_path / "repo"
    (repo / "plans").mkdir(parents=True)
    state = repo / "plans/001_CONTROL_OPERATIVO.md"
    state.write_text("state", encoding="utf-8")
    ref = _report(repo, "evidence.json", "src/core/x.py", "def x(): pass")
    decision = evaluate_evidence_reuse(
        repo,
        ref,
        intended_use=IntendedUse(scope="src/core/x.py", coverage_required="module", intended_assurance="smoke"),
        material_dependencies=[],
        snapshot=_snapshot(_sha(state.read_bytes())),
    )
    assert decision.decision == REUSE


def test_fresh_is_not_enough_when_coverage_not_contained(tmp_path):
    repo = tmp_path / "repo"
    ref = _report(repo, "evidence.json", "src/core/x.py", "def x(): pass")
    decision = evaluate_evidence_reuse(
        repo,
        ref,
        intended_use=IntendedUse(scope="src/core/y.py", coverage_required="module", intended_assurance="smoke"),
        material_dependencies=[],
    )
    assert decision.decision == TARGETED_REVERIFY
    assert "SEMANTIC_SCOPE_MISMATCH" in decision.reasons


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("coverage_required", "different", "SEMANTIC_COVERAGE_REQUIRED_MISMATCH"),
        ("intended_assurance", "high", "SEMANTIC_INTENDED_ASSURANCE_MISMATCH"),
        ("environment", "OTHER_ENV", "SEMANTIC_ENVIRONMENT_MISMATCH"),
        ("repository_revision", "REV-2", "SEMANTIC_REPOSITORY_REVISION_MISMATCH"),
    ],
)
def test_semantically_incompatible_evidence_requires_targeted_reverify(tmp_path, field, value, reason):
    repo = tmp_path / "repo"
    ref = _report(repo, "evidence.json", "src/core/x.py", "def x(): pass")
    intended = {
        "scope": "src/core/x.py",
        "coverage_required": "module",
        "intended_assurance": "smoke",
        "environment": "ANY",
        "repository_revision": "REV-1",
    }
    intended[field] = value
    decision = evaluate_evidence_reuse(repo, ref, intended_use=IntendedUse(**intended), material_dependencies=[])
    assert decision.decision == TARGETED_REVERIFY
    assert reason in decision.reasons


def test_missing_semantic_declaration_requires_targeted_reverify(tmp_path):
    repo = tmp_path / "repo"
    ref = _report(repo, "evidence.json", "src/core/x.py", "def x(): pass")
    report = repo / ref
    payload = json.loads(report.read_text(encoding="utf-8"))
    payload.pop("semantic_applicability")
    identity = dict(payload)
    identity.pop("evidence_identity_sha256", None)
    identity.pop("generated_at", None)
    payload["evidence_identity_sha256"] = _sha(json.dumps(identity, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode())
    report.write_text(json.dumps(payload), encoding="utf-8")
    decision = evaluate_evidence_reuse(
        repo,
        ref,
        intended_use=IntendedUse(scope="src/core/x.py", coverage_required="module", intended_assurance="smoke", repository_revision="REV-1"),
        material_dependencies=[],
    )
    assert decision.decision == TARGETED_REVERIFY
    assert "SEMANTIC_DECLARATION_MISSING" in decision.reasons


def test_material_dependency_change_degrades_to_targeted_reverify(tmp_path):
    repo = tmp_path / "repo"
    (repo / "src").mkdir(parents=True)
    ref = _report(repo, "evidence.json", "src/core/x.py", "def x(): pass")
    dep_path = repo / "src/core/dep.py"
    dep_path.write_text("def dep(): pass", encoding="utf-8")
    original = _sha(dep_path.read_bytes())
    decision = evaluate_evidence_reuse(
        repo,
        ref,
        intended_use=IntendedUse(scope="src/core/x.py", coverage_required="module", intended_assurance="smoke"),
        material_dependencies=[MaterialDependency(path="src/core/dep.py", sha256=original)],
    )
    assert decision.decision == REUSE
    # Mutate a material dependency distinct from the evidence source: the
    # evidence stays fresh but reuse must degrade (targeted reverify).
    dep_path.write_text("def dep(): return 1", encoding="utf-8")
    decision = evaluate_evidence_reuse(
        repo,
        ref,
        intended_use=IntendedUse(scope="src/core/x.py", coverage_required="module", intended_assurance="smoke"),
        material_dependencies=[MaterialDependency(path="src/core/dep.py", sha256=original)],
    )
    assert decision.decision == TARGETED_REVERIFY


def test_stale_evidence_requires_rerun(tmp_path):
    repo = tmp_path / "repo"
    (repo / "src").mkdir(parents=True)
    ref = _report(repo, "evidence.json", "src/core/x.py", "def x(): pass")
    # Stale: mutate the source_input after the report was written.
    (repo / "src/core/x.py").write_text("def x(): return 2", encoding="utf-8")
    decision = evaluate_evidence_reuse(
        repo,
        ref,
        intended_use=IntendedUse(scope="src/core/x.py", coverage_required="module", intended_assurance="smoke"),
        material_dependencies=[],
    )
    assert decision.decision == RERUN_REQUIRED


def test_missing_dependency_is_unverifiable(tmp_path):
    repo = tmp_path / "repo"
    ref = _report(repo, "evidence.json", "src/core/x.py", "def x(): pass")
    decision = evaluate_evidence_reuse(
        repo,
        ref,
        intended_use=IntendedUse(scope="src/core/x.py", coverage_required="module", intended_assurance="smoke"),
        material_dependencies=[MaterialDependency(path="src/core/missing.py", sha256="a" * 64)],
    )
    assert decision.decision == UNVERIFIABLE


def test_missing_evidence_ref_is_unverifiable(tmp_path):
    repo = tmp_path / "repo"
    decision = evaluate_evidence_reuse(
        repo,
        "reports/implementation/plan_006/nope.json",
        intended_use=IntendedUse(scope="x", coverage_required="m", intended_assurance="s"),
        material_dependencies=[],
    )
    assert decision.decision == UNVERIFIABLE
    assert "EVIDENCE_REF_UNRESOLVED" in decision.reasons


def _bind_live_state(repo: Path, ref: str) -> None:
    state = repo / "plans/001_CONTROL_OPERATIVO.md"
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text("state-1", encoding="utf-8")
    report = repo / ref
    payload = json.loads(report.read_text(encoding="utf-8"))
    payload["authority"] = {"live_state_path": "plans/001_CONTROL_OPERATIVO.md"}
    payload["source_inputs"].insert(0, {"path": "plans/001_CONTROL_OPERATIVO.md", "sha256": _sha(state.read_bytes())})
    identity = dict(payload)
    identity.pop("evidence_identity_sha256", None)
    identity.pop("generated_at", None)
    payload["evidence_identity_sha256"] = _sha(
        json.dumps(identity, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    )
    report.write_text(json.dumps(payload), encoding="utf-8")


def test_live_state_change_does_not_stale_historical_evidence(tmp_path):
    repo = tmp_path / "repo"
    ref = _report(repo, "evidence.json", "src/core/x.py", "def x(): pass")
    _bind_live_state(repo, ref)
    (repo / "plans/001_CONTROL_OPERATIVO.md").write_text("state-2", encoding="utf-8")

    from src.core.evidence_reuse import check_plan_006_report_freshness

    freshness = check_plan_006_report_freshness(repo, ref)
    assert freshness["status"] == "FRESH"
    assert freshness["live_state_changes"] == ["plans/001_CONTROL_OPERATIVO.md"]


def test_full_reuse_ignores_only_live_state_drift(tmp_path):
    repo = tmp_path / "repo"
    ref = _report(repo, "evidence.json", "src/core/x.py", "def x(): pass")
    _bind_live_state(repo, ref)
    state = repo / "plans/001_CONTROL_OPERATIVO.md"
    historical_live_state = _sha(b"state-1")
    dependency = repo / "src/core/dep.py"
    dependency.write_text("def dep(): pass", encoding="utf-8")
    dependency_sha = _sha(dependency.read_bytes())
    state.write_text("state-2", encoding="utf-8")

    decision = evaluate_evidence_reuse(
        repo,
        ref,
        intended_use=IntendedUse(
            scope="src/core/x.py",
            coverage_required="module",
            intended_assurance="smoke",
            repository_revision="REV-1",
        ),
        material_dependencies=[MaterialDependency(path="src/core/dep.py", sha256=dependency_sha)],
        snapshot=_snapshot(historical_live_state),
    )
    assert decision.decision == REUSE


def test_crlf_only_material_dependency_change_is_not_reported(tmp_path):
    repo = tmp_path / "repo"
    ref = _report(repo, "evidence.json", "src/core/x.py", "def x(): pass")
    dependency = repo / "src/core/dep.py"
    dependency.write_bytes(b"def dep(): pass\n")
    expected = _sha(dependency.read_bytes())
    dependency.write_bytes(b"def dep(): pass\r\n")

    decision = evaluate_evidence_reuse(
        repo,
        ref,
        intended_use=IntendedUse(scope="src/core/x.py", coverage_required="module", intended_assurance="smoke"),
        material_dependencies=[MaterialDependency(path="src/core/dep.py", sha256=expected)],
    )
    assert decision.decision == REUSE


def test_material_source_change_still_stales_evidence(tmp_path):
    repo = tmp_path / "repo"
    ref = _report(repo, "evidence.json", "src/core/x.py", "def x(): pass")
    _bind_live_state(repo, ref)
    (repo / "src/core/x.py").write_text("def x(): return 1", encoding="utf-8")

    from src.core.evidence_reuse import check_plan_006_report_freshness

    freshness = check_plan_006_report_freshness(repo, ref)
    assert freshness["status"] == "STALE"
    assert "src/core/x.py" in freshness["mismatches"]


def test_missing_declared_live_state_fails_closed(tmp_path):
    repo = tmp_path / "repo"
    ref = _report(repo, "evidence.json", "src/core/x.py", "def x(): pass")
    report = repo / ref
    payload = json.loads(report.read_text(encoding="utf-8"))
    payload["authority"] = {"live_state_path": "plans/001_CONTROL_OPERATIVO.md"}
    payload["source_inputs"].insert(0, {"path": "plans/001_CONTROL_OPERATIVO.md", "sha256": "a" * 64})
    identity = dict(payload)
    identity.pop("evidence_identity_sha256", None)
    identity.pop("generated_at", None)
    payload["evidence_identity_sha256"] = _sha(
        json.dumps(identity, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    )
    report.write_text(json.dumps(payload), encoding="utf-8")

    from src.core.evidence_reuse import check_plan_006_report_freshness

    freshness = check_plan_006_report_freshness(repo, ref)
    assert freshness["status"] == "UNVERIFIABLE"
