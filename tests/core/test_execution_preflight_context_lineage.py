from types import SimpleNamespace

from src.core import execution_preflight


class _Authorization:
    mission_id = "MISSION-1"
    contract_sha256 = "a" * 64
    single_use = False

    def verify(self, *args, **kwargs):
        return None


def test_preflight_binds_reduced_mission_lineage_into_context_manifest(monkeypatch, tmp_path):
    captured = {}

    monkeypatch.setattr(execution_preflight, "load_mission_authorization", lambda _path: _Authorization())
    monkeypatch.setattr(execution_preflight, "_registry_capability", lambda *args: {"assigned_role": ["ROLE-1"]})

    def resolve(_references, **kwargs):
        captured.update(kwargs)
        return {"manifest_id": "CTX-1"}

    monkeypatch.setattr(execution_preflight, "resolve_context", resolve)
    request = SimpleNamespace(
        capability_id="CAP-1",
        role="ROLE-1",
        execution_route="route-1",
        execution_profile="profile-1",
        execution_mode="SYNTHETIC",
        output_artifact_path="output/result.json",
        config={
            "mission_authorization_path": "authorization.json",
            "context_references": [],
            "mission_id": "MISSION-1",
            "prompt_id": "prompt-1",
            "input_refs": ["input-1"],
            "output_refs": ["output-1"],
        },
    )

    result = execution_preflight.preflight_controlled_execution(request, root=tmp_path)

    assert result["context_manifest"] == {"manifest_id": "CTX-1"}
    assert captured["mission_id"] == "MISSION-1"
    assert captured["execution_profile_id"] == "profile-1"
    assert captured["prompt_id"] == "prompt-1"
    assert captured["input_refs"] == ["input-1"]
    assert captured["output_refs"] == ["output-1"]


def test_preflight_loads_only_matching_reduced_mission_contract(monkeypatch, tmp_path):
    captured = {}
    contract = SimpleNamespace(mission_mode="REDUCED", mission_id="MISSION-1")
    monkeypatch.setattr(execution_preflight, "load_mission_authorization", lambda _path: _Authorization())
    def load_contract(path):
        captured["contract_path"] = path
        return contract
    monkeypatch.setattr(execution_preflight, "load_mission_contract", load_contract)
    monkeypatch.setattr(execution_preflight, "_registry_capability", lambda *args: {"assigned_role": ["ROLE-1"]})
    monkeypatch.setattr(execution_preflight, "resolve_context", lambda *args, **kwargs: {"manifest_id": "CTX-1"})
    request = SimpleNamespace(capability_id="CAP-1", role="ROLE-1", execution_route="route-1", execution_profile="profile-1", execution_mode="SYNTHETIC", output_artifact_path="output/result.json", config={"mission_authorization_path":"authorization.json", "mission_contract_path":"contract.json", "context_references":[]})
    result = execution_preflight.preflight_controlled_execution(request, root=tmp_path)
    assert result["mission_contract"] is contract
