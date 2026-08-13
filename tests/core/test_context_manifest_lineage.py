from __future__ import annotations

import pytest

from src.core.context_resolution import ContextResolutionError, resolve_context


def test_child_manifest_records_run_lineage_and_no_conversation_inheritance(tmp_path):
    (tmp_path / "config").mkdir()
    (tmp_path / "policies").mkdir()
    (tmp_path / "config/context_resolution_policy.json").write_text('{"normative_allowed_roots":["policies"],"evidentiary_allowed_roots":[],"historical_allowed_roots":[]}', encoding="utf-8")
    source = tmp_path / "policies/rule.md"
    source.write_text("rule", encoding="utf-8")
    import hashlib
    ref = {"ref_id": "rule", "context_class": "NORMATIVE", "artifact_path": "policies/rule.md", "artifact_type": "markdown", "artifact_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "authority_domain": "TEST", "required": True}
    manifest = resolve_context([ref], root=tmp_path, capability_id="CAP", role_id="ROLE", run_id="CHILD", parent_run_id="PARENT", child_run_id="CHILD", delegation_lineage_ref="PARENT/CHILD", authorized_context_refs=["policies/rule.md"])
    assert manifest["parent_run_id"] == "PARENT"
    assert manifest["child_run_id"] == "CHILD"
    assert manifest["delegation_lineage_ref"] == "PARENT/CHILD"
    assert manifest["conversation_history_inherited"] is False


def test_equal_parent_and_child_run_blocks_context_resolution(tmp_path):
    with pytest.raises(ContextResolutionError, match="CHILD_RUN_NOT_ISOLATED"):
        resolve_context([], root=tmp_path, capability_id="CAP", role_id="ROLE", run_id="SAME", parent_run_id="SAME", child_run_id="SAME")


def test_manifest_run_must_match_child_run(tmp_path):
    with pytest.raises(ContextResolutionError, match="CHILD_RUN_MISMATCH"):
        resolve_context([], root=tmp_path, capability_id="CAP", role_id="ROLE", run_id="PARENT", parent_run_id="PARENT", child_run_id="CHILD")


def test_child_context_ref_must_be_authorized(tmp_path):
    with pytest.raises(ContextResolutionError, match="AUTHORIZED_CHILD_REFS_REQUIRED"):
        resolve_context([], root=tmp_path, capability_id="CAP", role_id="ROLE", run_id="CHILD", parent_run_id="PARENT", child_run_id="CHILD")
