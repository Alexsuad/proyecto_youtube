import hashlib
import json
from pathlib import Path

from src.core.contract_validation import validate_against_schema
from src.core.hardening_completion_review import build_hardening_completion_review


ROOT = Path(__file__).resolve().parents[2]


def test_completion_review_has_common_envelope_and_deterministic_identity():
    first = build_hardening_completion_review(ROOT, generated_at="2026-08-11T00:00:00Z")
    second = build_hardening_completion_review(ROOT, generated_at="2026-08-11T00:00:00Z")
    assert validate_against_schema(first, "hardening_completion_review") == []
    assert first == second
    assert first["repository_revision"]
    assert first["source_inputs"]
    assert first["evidence_refs"]
    assert first["evidence_identity_sha256"] == hashlib.sha256(
        json.dumps({k: v for k, v in first.items() if k not in {"generated_at", "evidence_identity_sha256"}}, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def test_completion_review_detects_stale_source(tmp_path):
    report = tmp_path / "report.json"
    source = tmp_path / "source.txt"
    source.write_text("before", encoding="utf-8")
    report.write_text(json.dumps({"schema_version":"1", "plan_id":"PLAN_004", "mission_id":"TH-X", "repository_revision":"a" * 40, "generated_at":"now", "source_inputs": [{"path": "source.txt", "sha256": hashlib.sha256(b"before").hexdigest()}], "evidence_refs":["source.txt"], "limitations":[], "result":"PASS"}), encoding="utf-8")
    source.write_text("after", encoding="utf-8")
    from src.core.evidence_freshness import check_report_freshness
    assert check_report_freshness(tmp_path, report)["status"] == "STALE"


def test_empty_or_incomplete_report_is_never_fresh(tmp_path):
    from src.core.evidence_freshness import check_report_freshness
    for name, content in (("empty.json", {}), ("missing-inputs.json", {"schema_version":"1"})):
        path = tmp_path / name
        path.write_text(json.dumps(content), encoding="utf-8")
        assert check_report_freshness(tmp_path, path)["status"] == "UNVERIFIABLE"


def test_missing_source_or_bad_checksum_is_never_fresh(tmp_path):
    from src.core.evidence_freshness import check_report_freshness
    base = {"schema_version":"1", "plan_id":"PLAN_004", "mission_id":"TH-X", "repository_revision":"a" * 40, "generated_at":"now", "evidence_refs":[], "limitations":[], "result":"PASS"}
    missing = {**base, "source_inputs":[{"path":"missing.txt", "sha256":"a" * 64}], "evidence_refs":["missing.txt"]}
    invalid = {**base, "source_inputs":[{"path":"missing.txt", "sha256":"not-a-checksum"}], "evidence_refs":["missing.txt"]}
    for name, content in (("missing.json", missing), ("invalid.json", invalid)):
        path = tmp_path / name
        path.write_text(json.dumps(content), encoding="utf-8")
        assert check_report_freshness(tmp_path, path)["status"] == "UNVERIFIABLE"


def test_completion_review_cannot_hide_failed_cross_registry_report(tmp_path):
    import shutil
    source = ROOT
    for relative in ("reports/implementation/plan_004", "config", "schemas", "src"):
        origin = source / relative
        destination = tmp_path / relative
        if origin.is_dir():
            shutil.copytree(origin, destination)
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(origin, destination)
    report_path = tmp_path / "reports/implementation/plan_004/TH05_cross_registry_integrity.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["result"] = "FAIL"
    report_path.write_text(json.dumps(report), encoding="utf-8")
    review = build_hardening_completion_review(tmp_path, generated_at="2026-08-11T00:00:00Z")
    statuses = {item["name"]: item["status"] for item in review["dimensions"]}
    assert statuses["CROSS_REGISTRY_INTEGRITY"] == "FAIL"
    assert review["result"] == "HARDENING_COMPLETED_WITH_EVIDENCE_LIMITATION"
