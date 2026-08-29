import json, os, subprocess, sys
from uuid import uuid4
from pathlib import Path
from src.core.version_manifest import compute_checksum
from src.core.contract_validation import validate_against_schema

ROOT = Path(__file__).resolve().parents[2]
ENV = {**os.environ, "PYTHONPATH": str(ROOT)}


def run(script, *args):
    return subprocess.run([sys.executable, str(ROOT / "src/scripts" / script), *map(str, args)], cwd=ROOT, env=ENV, text=True, capture_output=True)


def payload():
    return json.loads((ROOT / "profiles/editorial/mas_alla_del_guion/1.2.2/profile_payload.json").read_text())


def approval(profile, checksum):
    return {
        "profile_id": profile["profile_id"],
        "profile_version": profile["version"],
        "profile_checksum": checksum,
        "decision": "APPROVE",
        "approval_status": "APPROVE",
        "reviewer_role": "CHANNEL_INTELLIGENCE",
        "approval_timestamp": "2026-07-27T12:00:00Z",
        "review_scope": ["identidad", "voz", "límites"],
        "functional_owner_role": "CHANNEL_INTELLIGENCE",
        "voice_evidence_level": "AUTHENTIC_CORPUS_PARTIAL",
        "evidence_summary": "Aprobación final de fixture sintético.",
        "limitations": ["Fixture de validación."],
        "approved_by": "channel_intelligence_owner",
        "approved_at": "2026-07-27T12:00:00Z",
    }


def gate(profile, checksum):
    return {
        "gate_id": "B3_TECHNICAL_PROFILE_VALIDATION",
        "artifact_id": profile["profile_id"],
        "artifact_version": profile["version"],
        "status": "PASS",
        "summary": "synthetic",
        "violations": [],
        "warnings": [],
        "evidence": {"profile_checksum": checksum},
        "checked_at": "2026-07-27T12:15:00Z",
        "checker_version": "1.2.0",
        "exit_code": 0,
    }


def test_cli_pipeline_and_rejections(tmp_path: Path):
    before = {path.name for path in ROOT.glob(".tmp_*")}
    repo_active = ROOT / "config/active_editorial_profile.json"
    repo_active_before = repo_active.read_text() if repo_active.exists() else None
    token = uuid4().hex
    source = tmp_path / f"payload_{token}.json"
    source.write_text(json.dumps(payload()))
    registry = tmp_path / f"registry_{token}.json"
    one = tmp_path / f"one_{token}.json"
    two = tmp_path / f"two_{token}.json"
    assert run("compile_editorial_profile.py", "--payload", source, "--output", one, "--registry", registry).returncode == 0
    assert run("compile_editorial_profile.py", "--payload", source, "--output", two, "--registry", registry).returncode == 0
    assert json.loads(one.read_text())["checksum"] == json.loads(two.read_text())["checksum"]
    assert run("validate_editorial_profile.py", "--profile", one).returncode == 0
    bad = tmp_path / f"bad_{token}.json"
    bad.write_text(json.dumps({}))
    assert run("validate_editorial_profile.py", "--profile", bad).returncode != 0
    profile = json.loads(one.read_text())["profile"]
    checksum = compute_checksum(profile)
    ap = tmp_path / f"approval_{token}.json"
    te = tmp_path / f"gate_{token}.json"
    ap.write_text(json.dumps(approval(profile, checksum)))
    te.write_text(json.dumps(gate(profile, checksum)))
    active = tmp_path / f"active_{token}.json"
    assert run("activate_editorial_profile.py", "--profile", one, "--approval", ap, "--technical", te, "--output", active, "--actor", "synthetic").returncode == 0
    assert validate_against_schema(json.loads(active.read_text()), "active_editorial_profile") == []
    if repo_active_before is None:
        assert not repo_active.exists()
    else:
        assert repo_active.read_text() == repo_active_before
    missing = tmp_path / f"missing_{token}.json"
    assert run("activate_editorial_profile.py", "--profile", one, "--approval", missing, "--technical", te, "--output", tmp_path / f"no_{token}.json", "--actor", "synthetic").returncode != 0
    wrong = gate(profile, "b" * 64)
    te.write_text(json.dumps(wrong))
    assert run("activate_editorial_profile.py", "--profile", one, "--approval", ap, "--technical", te, "--output", tmp_path / f"wrong_{token}.json", "--actor", "synthetic").returncode != 0

    pending_approval = {
        "profile_id": profile["profile_id"],
        "profile_version": profile["version"],
        "profile_checksum": checksum,
        "decision": "PENDING",
        "approval_status": "PENDING",
        "functional_owner_role": "CHANNEL_INTELLIGENCE",
        "voice_evidence_level": "AUTHENTIC_CORPUS_PARTIAL",
        "evidence_summary": "Pendiente de revisión funcional.",
        "limitations": ["Sin aprobación funcional todavía."],
    }
    ap.write_text(json.dumps(pending_approval))
    assert run("activate_editorial_profile.py", "--profile", one, "--approval", ap, "--technical", te, "--output", tmp_path / f"pending_{token}.json", "--actor", "synthetic").returncode != 0
    after = {path.name for path in ROOT.glob(".tmp_*")}
    assert after == before
