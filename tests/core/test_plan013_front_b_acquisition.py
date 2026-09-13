from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from src.application.research_b2 import ResearchB2Error, SoftwareAcquisitionAdapter
from src.core.contract_validation import validate_software_acquisition_pipeline


ROOT = Path(__file__).resolve().parents[2]


def _adapter(tmp_path: Path, *, source_id: str = "S-1") -> SoftwareAcquisitionAdapter:
    recovery_path = tmp_path / f"{source_id}.json"
    recovery_path.write_text(json.dumps({"source_id": source_id, "content": "fixture"}), encoding="utf-8")
    checksum = hashlib.sha256(recovery_path.read_bytes()).hexdigest()
    recovery_ref = f"recovery:{source_id}"
    execution_ref = f"RUN:{source_id}"
    registry = json.loads((ROOT / "output" / "execution_provenance_registry.json").read_text(encoding="utf-8"))
    run = copy.deepcopy(registry["runs"][0])
    run.update({
        "run_id": execution_ref,
        "status": "SUCCEEDED",
        "outputs": [{"artifact_kind": "research", "artifact_id": recovery_ref, "artifact_ref": f"research:{recovery_ref}", "checksum": checksum}],
        "output_artifact_ids": [f"research:{recovery_ref}"],
        "output_versions": ["fixture-1"],
        "output_checksums": [checksum],
    })
    registry["runs"] = [run]
    registry_path = tmp_path / "execution_provenance_registry.json"
    registry_path.write_text(json.dumps(registry), encoding="utf-8")
    return SoftwareAcquisitionAdapter(
        {source_id: {
            "request_ref": f"request:{source_id}", "execution_ref": execution_ref,
            "recovery_artifact_ref": recovery_ref, "retrieval_status": "RECOVERED",
            "evidence_status": "VERIFIED", "software_controlled": True,
        }},
        recovery_artifacts={recovery_ref: {"artifact_id": recovery_ref, "path": str(recovery_path), "checksum": checksum}},
        execution_registry_path=registry_path,
    )


def _candidate(source_id: str = "S-1") -> dict:
    return {
        "source_id": source_id, "title": "Fuente sintética", "source_type": "TEXT",
        "access_type": "DIRECT", "locator": f"fixture://{source_id}", "confidence": "HIGH",
        "provenance": {"locator": f"fixture://{source_id}", "verification_status": "NOT_REVIEWED"},
    }


def test_front_b_materializes_search_fetch_verify_registry_neutrally(tmp_path):
    result = _adapter(tmp_path).run_pipeline(
        "Consulta sintética", candidates=[_candidate()], request_ref="request:front-b"
    )

    assert validate_software_acquisition_pipeline(result) == []
    assert result["execution_mode"] == "SYNTHETIC"
    assert result["software_controlled"] is True
    assert [stage["stage"] for stage in result["stages"]] == [
        "SEARCH_DISCOVERY", "FETCH_ACQUISITION", "VERIFY", "SOURCE_REGISTRY"
    ]
    source = result["source_registry"][0]
    assert source["retrieval_status"] == "RECOVERED"
    assert source["evidence_status"] == "VERIFIED"
    assert source["software_controlled"] is True
    assert source["provenance"]["locator"] == "fixture://S-1"
    assert source["error"] is None


def test_front_b_unavailable_is_fail_closed_without_fabricated_sources(tmp_path):
    result = _adapter(tmp_path).run_pipeline("Consulta sin capacidad")

    assert validate_software_acquisition_pipeline(result) == []
    assert result["capability_status"] == "UNAVAILABLE"
    assert result["status"] == "UNAVAILABLE"
    assert result["error"]["code"] == "CAPABILITY_UNAVAILABLE"
    assert result["source_registry"] == []
    assert all(stage["status"] == "SKIPPED" for stage in result["stages"][1:])


def test_front_b_unacquired_candidate_cannot_be_positive_evidence(tmp_path):
    result = SoftwareAcquisitionAdapter().run_pipeline(
        "Consulta con fuente no adquirida", candidates=[_candidate()], request_ref="request:unavailable"
    )

    assert result["status"] == "BLOCKED"
    source = result["source_registry"][0]
    assert source["retrieval_status"] == "NOT_RECOVERED"
    assert source["evidence_status"] == "PENDING"
    assert source["provenance"]["verification_status"] == "NOT_REVIEWED"
    assert source["error"]["code"] == "ACQUISITION_BINDING_UNAVAILABLE"
    assert not result["stages"][2]["output_refs"]


def test_front_b_positive_binding_requires_software_controlled(tmp_path):
    adapter = _adapter(tmp_path)
    adapter.bindings["S-1"]["software_controlled"] = False

    result = adapter.run_pipeline("Consulta controlada", candidates=[_candidate()])

    assert result["status"] == "BLOCKED"
    assert result["source_registry"][0]["evidence_status"] == "PENDING"
    assert result["source_registry"][0]["error"]["code"] == "SOFTWARE_CONTROL_REQUIRED"


def test_front_b_verify_failure_preserves_provenance_and_error(tmp_path):
    adapter = _adapter(tmp_path)
    adapter.bindings["S-1"]["execution_ref"] = "RUN:MISSING"

    result = adapter.run_pipeline("Consulta con verificación fallida", candidates=[_candidate()])

    source = result["source_registry"][0]
    assert result["status"] == "BLOCKED"
    assert source["retrieval_status"] == "FAILED"
    assert source["evidence_status"] == "NOT_EVIDENCE"
    assert source["provenance"]["locator"] == "fixture://S-1"
    assert source["error"]["code"] == "ACQUISITION_VERIFY_FAILED"
    assert source["error"]["source_id"] == "S-1"
