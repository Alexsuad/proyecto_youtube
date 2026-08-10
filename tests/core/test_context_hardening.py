from __future__ import annotations

import hashlib
import json
from pathlib import Path
import pytest

from src.core.context_hardening import validate_handoff
from src.core.context_resolution import ContextResolutionError, resolve_context

def _write(path: Path, value: str) -> str:
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(value,encoding="utf-8"); return hashlib.sha256(path.read_bytes()).hexdigest()

def _root(tmp_path: Path) -> tuple[Path,str]:
    _write(tmp_path/"config/context_resolution_policy.json",json.dumps({"normative_allowed_roots":["policies"],"evidentiary_allowed_roots":[],"historical_allowed_roots":[]}))
    digest=_write(tmp_path/"policies/rule.md","rule")
    return tmp_path,digest

def test_case_input_cannot_claim_normative_precedence(tmp_path: Path) -> None:
    root,digest=_root(tmp_path)
    with pytest.raises(ContextResolutionError,match="CONTEXT_REQUIRED_UNRESOLVED"):
        resolve_context([{"ref_id":"x","context_class":"NORMATIVE","precedence_layer":"CASE_INPUT","artifact_path":"policies/rule.md","artifact_type":"markdown","artifact_sha256":digest,"authority_domain":"D","required":True}],root=root,capability_id="C",role_id="R",run_id="RUN")

def test_manifest_binds_execution_identity(tmp_path: Path) -> None:
    root,digest=_root(tmp_path)
    manifest=resolve_context([{"ref_id":"x","context_class":"NORMATIVE","precedence_layer":"NORMATIVE_CONTEXT","artifact_path":"policies/rule.md","artifact_type":"markdown","artifact_sha256":digest,"authority_domain":"D","required":True}],root=root,capability_id="C",role_id="R",run_id="RUN",mission_id="TH-06",execution_profile_id="PROFILE",prompt_id="PROMPT",input_refs=["in"],output_refs=["out"])
    assert {key:manifest[key] for key in ("mission_id","execution_profile_id","prompt_id","input_refs","output_refs")} == {"mission_id":"TH-06","execution_profile_id":"PROFILE","prompt_id":"PROMPT","input_refs":["in"],"output_refs":["out"]}
    second=resolve_context([{"ref_id":"x","context_class":"NORMATIVE","precedence_layer":"NORMATIVE_CONTEXT","artifact_path":"policies/rule.md","artifact_type":"markdown","artifact_sha256":digest,"authority_domain":"D","required":True}],root=root,capability_id="C",role_id="R",run_id="RUN",mission_id="TH-06",execution_profile_id="PROFILE",prompt_id="PROMPT",input_refs=["in"],output_refs=["out"])
    assert manifest == second
    assert manifest["required_context_count"] == 1
    assert manifest["resolved_context_size"] == len("rule".encode())
    assert manifest["estimated_tokens"] == 1
    changed=_write(root/"policies/rule.md","changed")
    third=resolve_context([{"ref_id":"x","context_class":"NORMATIVE","precedence_layer":"NORMATIVE_CONTEXT","artifact_path":"policies/rule.md","artifact_type":"markdown","artifact_sha256":changed,"authority_domain":"D","required":True}],root=root,capability_id="C",role_id="R",run_id="RUN",mission_id="TH-06",execution_profile_id="PROFILE",prompt_id="PROMPT",input_refs=["in"],output_refs=["out"])
    assert third["manifest_id"] != manifest["manifest_id"]
    assert third["manifest_sha256"] != manifest["manifest_sha256"]

def test_self_contained_handoff_needs_real_justification() -> None:
    with pytest.raises(ValueError,match="HANDOFF_SELF_CONTAINED_NOT_JUSTIFIED"): validate_handoff("SELF_CONTAINED",consumer_can_resolve=True)
    validate_handoff("REFERENCE_ONLY",consumer_can_resolve=True)
    validate_handoff("SELF_CONTAINED",consumer_can_resolve=False,justification="consumer cannot resolve repository references")
