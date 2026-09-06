"""PLAN012 M7 canonical Research V2 E2E coordinator.

M7 owns only coordination. B2, M4, M5 and M6 remain the authorities for
their contracts, validation, persistence, lineage, provenance and gates.
"""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from src.ai.contracts import ExecutionRequest, InputArtifact
from src.ai.execution import M3_REQUIRED_INPUT_KINDS, _validate_m3_input_artifacts
from src.application.interaction import HumanDecision
from src.application.research_b2 import ResearchB2Orchestrator, ResearchB2Persistence, SoftwareAcquisitionAdapter, _checksum
from src.application.research_b3 import ResearchB3Orchestrator, ResearchB3Persistence
from src.application.research_b4 import ResearchB4Orchestrator, ResearchB4Persistence
from src.application.research_m7_fixture import SyntheticResearchExecutor, b5_i3_transversal_fixtures, research_plan, source_report
from src.application.storage import _write_json_atomic
from src.core.contract_validation import validate_against_schema, validate_research_plan, validate_research_ready_manifest
from src.core.invalidation import InvalidationEngine

M7_VERSION = "2.0.0"
STAGES = ("INTAKE", "RESEARCH_PLAN", "B2", "M4", "M5", "M6", "B5_I3_HANDOFF")
NARRATIVE_FIELDS = {"viewer_journey", "narrative_plan", "opening_design", "closing_design", "hook", "climax", "cta", "pacing", "title", "thumbnail"}


class ResearchM7Error(RuntimeError):
    """Fail-closed M7 coordination error."""


@dataclass(frozen=True)
class M7Artifact:
    stage: str
    artifact_id: str
    artifact_kind: str
    artifact_version: str
    path: str
    checksum: str

    def to_dict(self) -> dict[str, str]:
        return {"stage": self.stage, "artifact_id": self.artifact_id, "artifact_kind": self.artifact_kind, "artifact_version": self.artifact_version, "path": self.path, "checksum": self.checksum}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read(path: str | Path) -> Any:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ResearchM7Error(f"M7_STATE_UNREADABLE:{path}") from exc


def _ref_payload(ref: Mapping[str, Any]) -> dict[str, Any]:
    return {key: copy.deepcopy(ref[key]) for key in ("artifact_id", "artifact_kind", "artifact_version", "path", "checksum")}


class M7CheckpointStore:
    """Lightweight coordination state; canonical payloads stay in B2/B3/B4."""

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.checkpoint_path = self.root / "m7_checkpoint.json"

    def exists(self) -> bool:
        return self.checkpoint_path.is_file()

    def save(self, state: Mapping[str, Any]) -> None:
        _write_json_atomic(self.checkpoint_path, dict(state))

    def load(self) -> dict[str, Any]:
        if not self.exists():
            raise ResearchM7Error("M7_CHECKPOINT_MISSING")
        state = _read(self.checkpoint_path)
        if not isinstance(state, dict) or state.get("contract") != "plan012_m7_coordination":
            raise ResearchM7Error("M7_CHECKPOINT_CONTRACT_INVALID")
        self.verify(state)
        return state

    def verify(self, state: Mapping[str, Any]) -> None:
        for raw in list(state.get("artifacts", [])) + list(state.get("recovery_artifacts", [])):
            path = Path(str(raw.get("path", "")))
            if not path.is_file():
                raise ResearchM7Error(f"M7_STALE_DEPENDENCY:{raw.get('artifact_id')}:MISSING")
            raw_checksum = hashlib.sha256(path.read_bytes()).hexdigest()
            canonical_checksum = None
            try:
                canonical_checksum = _checksum(_read(path))
            except ResearchM7Error:
                pass
            if raw_checksum != raw.get("checksum") and canonical_checksum != raw.get("checksum"):
                raise ResearchM7Error(f"M7_STALE_DEPENDENCY:{raw.get('artifact_id')}:CHECKSUM_MISMATCH")


class ResearchV2B5I3Adapter:
    """Versioned, read-only adapter into the existing B5-I3 input validator."""

    _MANIFEST_KIND_BY_INPUT = {
        "research_pack": "ResearchPack",
        "claims_ledger": "ClaimsLedger",
        "source_access_and_evidence_report": "SourceAccessAndEvidenceReport",
        "refined_thesis": "RefinedThesis",
    }

    @staticmethod
    def _input_binding(item: InputArtifact) -> dict[str, Any]:
        payload = _read(item.path)
        return {
            "artifact_kind": item.artifact_kind,
            "artifact_id": item.artifact_id,
            "artifact_version": str(item.artifact_version or payload.get("artifact_version") or payload.get("version") or "1.0.0"),
            "checksum": _checksum(payload),
            "path": str(item.path),
            "producer_run_id": item.producer_run_id,
        }

    @staticmethod
    def _manifest_ref(manifest_ref: Mapping[str, Any]) -> dict[str, str]:
        return {
            "artifact_id": str(manifest_ref["artifact_id"]),
            "artifact_kind": str(manifest_ref["artifact_kind"]),
            "artifact_version": str(manifest_ref["artifact_version"]),
            "path": str(manifest_ref["path"]),
            "checksum": str(manifest_ref["checksum"]),
        }

    @staticmethod
    def validate_full_preflight(episode_id: str, inputs: list[InputArtifact]) -> dict[str, Any]:
        provided = {item.artifact_kind for item in inputs}
        missing = sorted(M3_REQUIRED_INPUT_KINDS - provided)
        if missing:
            raise ResearchM7Error("B5_I3_REQUIRED_INPUTS_MISSING:" + ",".join(missing))
        request = ExecutionRequest(
            capability_id="B5_I3_NARRATIVE_ARCHITECTURE",
            skill_id="skill_mapa_eventos_y_outline",
            skill_version="1.0.0",
            input_artifacts=inputs,
            output_schema="viewer_journey",
            execution_mode="SYNTHETIC_TEST",
            episode_id=episode_id,
            role="NARRATIVE_ARCHITECTURE",
        )
        try:
            _validate_m3_input_artifacts(request)
        except Exception as exc:
            raise ResearchM7Error(f"B5_I3_CONSUMER_CONTRACT_INVALID:{exc}") from exc
        return {"provided_input_kinds": sorted(provided), "required_input_kinds": sorted(M3_REQUIRED_INPUT_KINDS), "status": "PASS", "cognition_executed": False}

    @classmethod
    def validate_research_v2_precondition(
        cls,
        *,
        episode_id: str,
        manifest_ref: Mapping[str, Any],
        manifest: Mapping[str, Any],
        handoff: Mapping[str, Any],
        inputs: list[InputArtifact],
    ) -> dict[str, Any]:
        """Validate the single Research V2 -> B5-I3 consumability boundary."""
        expected_manifest_ref = cls._manifest_ref(manifest_ref)
        manifest_errors = validate_research_ready_manifest(dict(manifest))
        if manifest_errors:
            raise ResearchM7Error("B5_I3_RESEARCH_HANDOFF_PRECONDITION:MANIFEST_INVALID:" + " | ".join(manifest_errors))
        if expected_manifest_ref["artifact_kind"] != "ResearchReadyManifest" or expected_manifest_ref["artifact_id"] != str(manifest.get("manifest_id")):
            raise ResearchM7Error("B5_I3_RESEARCH_HANDOFF_PRECONDITION:MANIFEST_REF_MISMATCH")
        if expected_manifest_ref["artifact_version"] != str(manifest.get("research_version")) or expected_manifest_ref["checksum"] != _checksum(dict(manifest)):
            raise ResearchM7Error("B5_I3_RESEARCH_HANDOFF_PRECONDITION:MANIFEST_CHECKSUM_MISMATCH")
        if not Path(expected_manifest_ref["path"]).is_file() or _read(expected_manifest_ref["path"]) != dict(manifest):
            raise ResearchM7Error("B5_I3_RESEARCH_HANDOFF_PRECONDITION:MANIFEST_PATH_MISMATCH")
        state_bindings = manifest.get("state_bindings", {})
        if manifest.get("research_ready_state") == "NOT_RESEARCH_READY" or state_bindings.get("artifact_validity") != "VALID" or state_bindings.get("research_stage") != "READY" or state_bindings.get("selection_state") != "SELECTED":
            raise ResearchM7Error("B5_I3_RESEARCH_HANDOFF_PRECONDITION:MANIFEST_NOT_CURRENT")
        if handoff.get("handoff_state") != "VALID" or handoff.get("stale_reason"):
            raise ResearchM7Error("B5_I3_RESEARCH_HANDOFF_PRECONDITION:HANDOFF_STALE")
        validation_status = handoff.get("validation", {}).get("status")
        if validation_status not in {"PENDING", "PASS"}:
            raise ResearchM7Error("B5_I3_RESEARCH_HANDOFF_PRECONDITION:HANDOFF_VALIDATION_MISSING")
        if handoff.get("research_ready_manifest_ref") != expected_manifest_ref:
            raise ResearchM7Error("B5_I3_RESEARCH_HANDOFF_PRECONDITION:HANDOFF_MANIFEST_BINDING_MISMATCH")
        if handoff.get("research_lineage") != {
            "research_artifacts": copy.deepcopy(manifest.get("research_artifacts", [])),
            "lineage": copy.deepcopy(manifest.get("lineage", {})),
        }:
            raise ResearchM7Error("B5_I3_RESEARCH_HANDOFF_PRECONDITION:LINEAGE_BINDING_MISMATCH")
        manifest_artifacts_by_id = {str(item["artifact_id"]): item for item in manifest.get("research_artifacts", [])}
        if any(str(item) not in manifest_artifacts_by_id for item in manifest.get("lineage", {}).get("source_refs", [])):
            raise ResearchM7Error("B5_I3_RESEARCH_HANDOFF_PRECONDITION:LINEAGE_UNRESOLVABLE")

        restrictions = manifest.get("downstream_restrictions")
        if not isinstance(restrictions, list):
            raise ResearchM7Error("B5_I3_RESEARCH_HANDOFF_PRECONDITION:RESTRICTIONS_MISSING")
        if handoff.get("downstream_restrictions") != restrictions:
            raise ResearchM7Error("B5_I3_RESEARCH_HANDOFF_PRECONDITION:RESTRICTIONS_BINDING_MISMATCH")
        restriction_binding = handoff.get("downstream_restriction_binding")
        expected_restriction_binding = {
            "manifest_checksum": expected_manifest_ref["checksum"],
            "restriction_ids": [str(item.get("restriction_id")) for item in restrictions],
            "restrictions_checksum": _checksum(restrictions),
        }
        if restriction_binding != expected_restriction_binding:
            raise ResearchM7Error("B5_I3_RESEARCH_HANDOFF_PRECONDITION:RESTRICTIONS_UNBOUND")
        if any("B5-I3" not in item.get("affected_consumers", []) for item in restrictions):
            raise ResearchM7Error("B5_I3_RESEARCH_HANDOFF_PRECONDITION:RESTRICTIONS_NOT_RESOLVABLE")

        expected_input_bindings = [cls._input_binding(item) for item in inputs]
        if handoff.get("b5_i3_input_bindings") != expected_input_bindings:
            raise ResearchM7Error("B5_I3_RESEARCH_HANDOFF_PRECONDITION:INPUT_BINDING_MISMATCH")
        if handoff.get("b5_i3_input_set_checksum") != _checksum(expected_input_bindings):
            raise ResearchM7Error("B5_I3_RESEARCH_HANDOFF_PRECONDITION:INPUT_SET_CHECKSUM_MISMATCH")
        manifest_artifacts = {
            (str(item["artifact_id"]), str(item["artifact_kind"]), str(item["artifact_version"]), str(item["checksum"]))
            for item in manifest.get("research_artifacts", [])
        }
        for input_kind, manifest_kind in cls._MANIFEST_KIND_BY_INPUT.items():
            binding = next((item for item in expected_input_bindings if item["artifact_kind"] == input_kind), None)
            if binding is None or (binding["artifact_id"], manifest_kind, binding["artifact_version"], binding["checksum"]) not in manifest_artifacts:
                raise ResearchM7Error(f"B5_I3_RESEARCH_HANDOFF_PRECONDITION:RESEARCH_INPUT_UNBOUND:{input_kind}")
            if handoff.get("research_owned_inputs", {}).get(input_kind) != manifest_artifacts_by_id.get(binding["artifact_id"]):
                raise ResearchM7Error(f"B5_I3_RESEARCH_HANDOFF_PRECONDITION:RESEARCH_OWNED_INPUT_BINDING:{input_kind}")
        preflight = cls.validate_full_preflight(episode_id, inputs)
        return {
            **preflight,
            "research_handoff_precondition": "PASS",
            "research_ready_manifest_current": True,
            "downstream_restrictions_count": len(restrictions),
            "downstream_restrictions_resolvable": True,
            "input_binding_checksum": _checksum(expected_input_bindings),
        }

    @classmethod
    def build(cls, manifest: Mapping[str, Any], *, manifest_ref: Mapping[str, Any], research_pack: Mapping[str, Any], claims: Mapping[str, Any], source_access: Mapping[str, Any], refined_thesis: Mapping[str, Any], refs: list[InputArtifact], selected_work_ids: list[str]) -> dict[str, Any]:
        errors = validate_research_ready_manifest(dict(manifest))
        if errors:
            raise ResearchM7Error("B5_I3_HANDOFF_MANIFEST_INVALID:" + " | ".join(errors))
        if manifest.get("research_ready_state") == "NOT_RESEARCH_READY":
            raise ResearchM7Error("B5_I3_HANDOFF_NOT_READY")
        manifest_reference = cls._manifest_ref(manifest_ref)
        input_bindings = [cls._input_binding(item) for item in refs]
        restriction_binding = {
            "manifest_checksum": manifest_reference["checksum"],
            "restriction_ids": [str(item.get("restriction_id")) for item in manifest.get("downstream_restrictions", [])],
            "restrictions_checksum": _checksum(manifest.get("downstream_restrictions", [])),
        }
        manifest_artifacts_by_id = {str(item["artifact_id"]): item for item in manifest.get("research_artifacts", [])}
        research_owned_inputs: dict[str, dict[str, Any]] = {}
        for input_kind, manifest_kind in cls._MANIFEST_KIND_BY_INPUT.items():
            binding = next((item for item in input_bindings if item["artifact_kind"] == input_kind), None)
            owned = manifest_artifacts_by_id.get(str(binding["artifact_id"])) if binding else None
            if binding is None or not owned or owned.get("artifact_kind") != manifest_kind or owned.get("artifact_version") != binding["artifact_version"] or owned.get("checksum") != binding["checksum"]:
                raise ResearchM7Error(f"B5_I3_RESEARCH_HANDOFF_PRECONDITION:RESEARCH_INPUT_UNBOUND:{input_kind}")
            research_owned_inputs[input_kind] = copy.deepcopy(owned)
        handoff = {
            "contract": "research_v2_b5_i3_handoff",
            "contract_version": M7_VERSION,
            "consumer": "B5-I3",
            "handoff_state": "VALID",
            "research_ready_manifest_ref": manifest_reference,
            "research_input_refs": [{"artifact_kind": ref.artifact_kind, "artifact_id": ref.artifact_id, "path": str(ref.path), "producer_run_id": ref.producer_run_id} if isinstance(ref, InputArtifact) else dict(ref) for ref in refs],
            "b5_i3_input_refs": copy.deepcopy(input_bindings),
            "b5_i3_input_bindings": copy.deepcopy(input_bindings),
            "b5_i3_input_set_checksum": _checksum(input_bindings),
            "required_input_kinds": sorted(M3_REQUIRED_INPUT_KINDS),
            "research_owned_inputs": research_owned_inputs,
            "selected_work_ids": list(selected_work_ids),
            "downstream_restrictions": copy.deepcopy(manifest.get("downstream_restrictions", [])),
            "downstream_restriction_binding": restriction_binding,
            "research_lineage": {"research_artifacts": copy.deepcopy(manifest.get("research_artifacts", [])), "lineage": copy.deepcopy(manifest.get("lineage", {}))},
            "narrative_decisions_not_made": True,
            "validation": {"status": "PENDING"},
        }
        preflight = cls.validate_research_v2_precondition(episode_id=str(manifest.get("episode_id")), manifest_ref=manifest_ref, manifest=manifest, handoff=handoff, inputs=refs)
        handoff["validation"] = {"consumer": "ResearchV2B5I3Adapter.validate_research_v2_precondition", **preflight}
        if any(key in handoff for key in NARRATIVE_FIELDS):
            raise ResearchM7Error("B5_I3_HANDOFF_NARRATIVE_FIELD_FORBIDDEN")
        return handoff


class ResearchM7SyntheticRunner:
    """Coordinate a canonical B2→M4→M5→M6 run with synthetic cognition."""

    def __init__(self, root: str | Path, *, selection_mode: str = "MANUAL", delegated_scope: list[str] | None = None):
        if selection_mode not in {"MANUAL", "DELEGATED"}:
            raise ResearchM7Error("M7_SELECTION_MODE_INVALID")
        self.root = Path(root)
        self.store = M7CheckpointStore(self.root)
        self.selection_mode = selection_mode
        self.delegated_scope = sorted(set(str(item) for item in (delegated_scope or [])))
        self.invalidation = InvalidationEngine()

    def _new_state(self, human_input: Mapping[str, Any]) -> dict[str, Any]:
        return {"contract": "plan012_m7_coordination", "contract_version": M7_VERSION, "run_id": f"M7-{human_input['episode_id']}", "generation": 1, "status": "IN_PROGRESS", "next_stage": "INTAKE", "completed_stages": [], "invalidated_stages": [], "artifacts": [], "recovery_artifacts": [], "canonical_refs": {}, "events": [], "human_input": copy.deepcopy(dict(human_input)), "selection_mode": self.selection_mode, "delegated_scope": list(self.delegated_scope), "real_ai_execution": False, "product_use_authorized": False, "p2_real_execution": False, "research_quality": "NOT_DEMONSTRATED", "created_at": _now(), "updated_at": _now()}

    @staticmethod
    def _validate_input(value: Mapping[str, Any]) -> None:
        works = value.get("works")
        if not isinstance(works, list) or not works or not all(isinstance(item, str) and item.strip() for item in works):
            raise ResearchM7Error("M7_HUMAN_WORK_INPUT_REQUIRED")
        if len(set(works)) != len(works):
            raise ResearchM7Error("M7_HUMAN_WORK_INPUT_DUPLICATE")
        target = value.get("target_final_works")
        count = target.get("requested_count") if isinstance(target, Mapping) else target
        if not isinstance(count, int) or count < 3 or count > 5:
            raise ResearchM7Error("M7_TARGET_FINAL_WORKS_EXPLICIT_AND_VALID_REQUIRED")
        if count > len(works):
            raise ResearchM7Error("M7_TARGET_FINAL_WORKS_EXCEEDS_INPUT")
        selected = value.get("selected_work_ids")
        if not isinstance(selected, list) or not selected or not set(selected).issubset(set(works)):
            raise ResearchM7Error("M7_SELECTION_INPUT_REQUIRED")
        if len(selected) != count:
            raise ResearchM7Error("M7_SELECTION_COUNT_MISMATCH")
        if value.get("episode_id") is None or value.get("topic") is None:
            raise ResearchM7Error("M7_HUMAN_INPUT_REQUIRED")

    def _state(self, human_input: Mapping[str, Any] | None, resume: bool) -> dict[str, Any]:
        if self.store.exists():
            state = self.store.load()
            if human_input is not None and dict(human_input) != state.get("human_input"):
                raise ResearchM7Error("M7_RESUME_INPUT_MISMATCH")
            return state
        if resume:
            raise ResearchM7Error("M7_RESUME_CHECKPOINT_MISSING")
        if not isinstance(human_input, Mapping):
            raise ResearchM7Error("M7_HUMAN_INPUT_REQUIRED")
        self._validate_input(human_input)
        state = self._new_state(human_input)
        self.store.save(state)
        return state

    @staticmethod
    def _event(state: dict[str, Any], boundary: str, stage: str, **extra: Any) -> None:
        state.setdefault("events", []).append({"boundary": boundary, "stage": stage, "at": _now(), **extra})

    def _materialize_recovery(self, state: dict[str, Any]) -> None:
        recovery_dir = self.root / f"recovery_g{state.get('generation', 1)}"
        recovery_dir.mkdir(parents=True, exist_ok=True)
        inp = state["human_input"]
        values = [("S1", {"source_id": "S1", "content": "Fixture controlado materializado por Software.", "locator": "fixture://S1", "synthetic": True})]
        values.extend((str(work_id), {"work_id": str(work_id), "content": f"Fixture de obra {work_id}.", "locator": f"fixture://{work_id}", "synthetic": True}) for work_id in inp["works"])
        state["recovery_artifacts"] = []
        for identifier, payload in values:
            path = recovery_dir / f"{identifier}.json"
            _write_json_atomic(path, payload)
            state["recovery_artifacts"].append({"artifact_id": f"recovery:{identifier}", "artifact_kind": "RecoveredSourceFixture" if identifier == "S1" else "RecoveredWorkFixture", "artifact_version": "1.0.0", "path": str(path), "checksum": hashlib.sha256(path.read_bytes()).hexdigest()})

    def _adapter(self, state: Mapping[str, Any]) -> SoftwareAcquisitionAdapter:
        bindings = {"S1": {"request_ref": "request:S1", "execution_ref": "execution:S1", "recovery_artifact_ref": "recovery:S1", "retrieval_status": "RECOVERED", "evidence_status": "VERIFIED", "software_controlled": True}}
        work_bindings = {str(work_id): {"request_ref": f"request:{work_id}", "execution_ref": f"execution:{work_id}", "recovery_artifact_ref": f"recovery:{work_id}", "retrieval_status": "RECOVERED", "evidence_status": "VERIFIED", "software_controlled": True, "representation_kind": "ORIGINAL_WORK", "edition_or_version": "fixture-1", "consulted_locator": f"fixture://{work_id}"} for work_id in state["human_input"]["works"]}
        return SoftwareAcquisitionAdapter(bindings, work_bindings=work_bindings)

    def _context(self, state: Mapping[str, Any]) -> dict[str, Any]:
        inp = state["human_input"]
        return {"topic": str(inp["topic"]), "source_access": source_report(str(inp["episode_id"]), f"RP-M7-{inp['episode_id']}"), "brief": {"brief_id": f"BRIEF-{inp['episode_id']}"}, "channel_context": {"channel_id": "CHANNEL-M7"}}

    def _store_coord(self, state: dict[str, Any], stage: str, ref: Mapping[str, Any], *, kind: str | None = None) -> None:
        item = {"stage": stage, **_ref_payload(ref)}
        state["artifacts"] = [old for old in state.get("artifacts", []) if old.get("stage") != stage]
        state["artifacts"].append(item)
        if kind:
            state.setdefault("canonical_refs", {}).setdefault(kind, []).append(_ref_payload(ref))

    def _baseline(self, b2_result: Mapping[str, Any]) -> dict[str, Any]:
        manifest = _read(b2_result["execution_manifest"]["path"])
        by_kind = {str(ref["artifact_kind"]): ref for ref in manifest["artifacts"]}
        def payload(kind: str) -> Any:
            return _read(by_kind[kind]["path"])
        return {"research_plan": _read(b2_result["research_plan"]["path"]), "phenomenon_base_research": payload("ResearchPack"), "work_discovery": payload("WorkLifecycle"), "base_research_pool": payload("WorkResearchDossierCollection")["dossiers"], "preliminary_fidelity": _read(b2_result["preliminary_fidelity"]["path"])["dossiers"], "initial_sufficiency": _read(b2_result["initial_sufficiency"]["path"])["dossiers"], "provisional_thesis": payload("ThesisArtifact"), "research_comparison": payload("ResearchComparison"), "deepening_targets": b2_result["deepening_targets"], "lifecycle": b2_result["lifecycle_projection"]}

    def _m4_result(self, ref: Mapping[str, Any]) -> dict[str, Any]:
        manifest = _read(ref["path"])
        result = {"execution_manifest": dict(ref)}
        for item in manifest["artifacts"]:
            kind = str(item["artifact_kind"])
            if kind == "ResearchPack": result["deep_phenomenon_research"] = item
            elif kind in {"ResearchStopDecision", "ResearchStopDecisionCollection"}: result["deep_phenomenon_sufficiency" if ":PHENOMENON" in str(item["artifact_id"]) else "deep_work_sufficiency"] = item
            elif kind == "WorkResearchDossierCollection":
                payload = _read(item["path"])
                result["deep_fidelity" if payload.get("dossiers", [{}])[0].get("research_stage") == "DEEP_FIDELITY" else "deep_work_research"] = item
        return result

    def _provenance(self, state: Mapping[str, Any], b2: Mapping[str, Any], m4: Mapping[str, Any], m5: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        repo_root = self.root / "canonical_repo"
        registry = _read(Path(__file__).resolve().parents[2] / "output" / "execution_provenance_registry.json")
        base = copy.deepcopy(registry["runs"][0])
        b2_manifest = _read(b2["execution_manifest"]["path"])
        m4_manifest = _read(m4["execution_manifest"]["path"])
        m5_manifest = _read(m5["execution_manifest"]["path"])
        refs = [b2["execution_manifest"], *b2_manifest["artifacts"], m4["execution_manifest"], *m4_manifest["artifacts"], m5["execution_manifest"], *m5_manifest["m5_outputs"], state["source_ref"]]
        unique = {(r["artifact_id"], r["artifact_kind"], r["checksum"]): r for r in refs}
        def run_for(ref: Mapping[str, Any], run_id: str) -> dict[str, Any]:
            run = copy.deepcopy(base)
            run.update({"run_id": run_id, "episode_id": state["human_input"]["episode_id"], "role": "RESEARCH_AND_CURATION", "role_id": "RESEARCH_AND_CURATION", "agent_id": run_id, "actual_executor": "synthetic-fixture", "status": "SUCCEEDED", "output_artifact_ids": [f"{ref['artifact_kind']}:{ref['artifact_id']}"], "output_versions": [ref["artifact_version"]], "output_checksums": [ref["checksum"]], "outputs": [{"artifact_kind": "semantic_audit", "artifact_id": ref["artifact_id"], "artifact_ref": f"{ref['artifact_kind']}:{ref['artifact_id']}", "checksum": ref["checksum"]}]})
            return run
        producer = run_for(m5["execution_manifest"], "M7-M5-PRODUCER")
        upstream = [run_for(ref, f"M7-UPSTREAM-{index:03d}") for index, ref in enumerate(unique.values(), start=1) if ref is not m5["execution_manifest"]]
        registry["runs"] = [producer, *upstream]
        _write_json_atomic(repo_root / "config" / "execution_provenance_policy.json", {"schema_version": "1.0.0", "canonical_registry_path": "output/execution_provenance_registry.json"})
        _write_json_atomic(repo_root / "output" / "execution_provenance_registry.json", registry)
        provenance = {"producer_provenance": {"actor_id": "M7-M5-PRODUCER", "run_id": "M7-M5-PRODUCER", "executor_id": "synthetic-fixture", "role": "RESEARCH_AND_CURATION", "provenance_ref": "output/execution_provenance_registry.json", "artifact_ref": {key: m5["execution_manifest"][key] for key in ("artifact_id", "artifact_kind", "artifact_version", "checksum")}}, "repository_root": str(repo_root), "execution_provenance_registry_ref": "output/execution_provenance_registry.json"}
        return {"artifact_refs": [b2["execution_manifest"], *b2_manifest["artifacts"], m4["execution_manifest"], *m4_manifest["artifacts"], state["source_ref"]]}, provenance

    def _materialize_b5_i3_inputs(self, state: dict[str, Any], baseline: Mapping[str, Any], m5: Mapping[str, Any]) -> list[InputArtifact]:
        source = self._context(state)["source_access"]
        claims = _read(m5["claims_ledger"]["path"])
        thesis = _read(m5["refined_thesis"]["path"])
        profile = _read(Path(__file__).resolve().parents[2] / "config" / "active_editorial_profile.json")
        fixtures = b5_i3_transversal_fixtures(
            episode_id=str(state["human_input"]["episode_id"]),
            topic=str(state["human_input"]["topic"]),
            works=[str(item) for item in state["human_input"]["works"]],
            profile=profile,
            research_pack=baseline["phenomenon_base_research"],
            source_report_payload=source,
            claims_ledger=claims,
            refined_thesis_payload=thesis,
            refined_thesis_checksum=hashlib.sha256(Path(m5["refined_thesis"]["path"]).read_bytes()).hexdigest(),
        )
        b2_manifest_ref = next(item for item in state["artifacts"] if item["stage"] == "B2")
        b2_manifest = _read(b2_manifest_ref["path"])
        research_ref = next(ref for ref in b2_manifest["artifacts"] if ref["artifact_kind"] == "ResearchPack" and ref["artifact_id"] == baseline["phenomenon_base_research"]["research_id"])
        refs: list[InputArtifact] = [
            InputArtifact("human_input", str(fixtures["human_input"]["interaction_id"]), self.root / "b5_i3_inputs" / f"g{state.get('generation', 1)}" / "human_input.json", "M7-TRANSVERSAL-FIXTURE"),
            InputArtifact("active_editorial_profile_reference", "ACTIVE_PROFILE_REFERENCE", self.root / "b5_i3_inputs" / f"g{state.get('generation', 1)}" / "active_editorial_profile_reference.json", "M7-PROFILE"),
            InputArtifact("episode_brief", str(fixtures["episode_brief"]["episode_id"]), self.root / "b5_i3_inputs" / f"g{state.get('generation', 1)}" / "episode_brief.json", "M7-TRANSVERSAL-FIXTURE"),
            InputArtifact("research_pack", str(baseline["phenomenon_base_research"]["research_id"]), Path(research_ref["path"]), "M7-B2", str(research_ref["artifact_version"])),
            InputArtifact("claims_ledger", str(claims["ledger_id"]), Path(m5["claims_ledger"]["path"]), "M7-M5", str(m5["claims_ledger"]["artifact_version"])),
            InputArtifact("source_access_and_evidence_report", str(source["report_id"]), Path(state["source_ref"]["path"]), "M7-SOURCE", str(state["source_ref"]["artifact_version"])),
            InputArtifact("narrative_human_analysis", str(fixtures["narrative_human_analysis"]["analysis_id"]), self.root / "b5_i3_inputs" / f"g{state.get('generation', 1)}" / "narrative_human_analysis.json", "M7-TRANSVERSAL-FIXTURE"),
            InputArtifact("material_curation", str(fixtures["material_curation"]["curation_id"]), self.root / "b5_i3_inputs" / f"g{state.get('generation', 1)}" / "material_curation.json", "M7-TRANSVERSAL-FIXTURE"),
            InputArtifact("refined_thesis", str(thesis["thesis_id"]), Path(m5["refined_thesis"]["path"]), "M7-M5", str(m5["refined_thesis"]["artifact_version"])),
            InputArtifact("editorial_script_promise", str(fixtures["editorial_script_promise"]["promise_id"]), self.root / "b5_i3_inputs" / f"g{state.get('generation', 1)}" / "editorial_script_promise.json", "M7-TRANSVERSAL-FIXTURE"),
            InputArtifact("early_packaging_hypothesis", str(fixtures["early_packaging_hypothesis"]["packaging_id"]), self.root / "b5_i3_inputs" / f"g{state.get('generation', 1)}" / "early_packaging_hypothesis.json", "M7-TRANSVERSAL-FIXTURE"),
            InputArtifact("b5_i2_semantic_audit", str(fixtures["b5_i2_semantic_audit"]["audit_id"]), self.root / "b5_i3_inputs" / f"g{state.get('generation', 1)}" / "b5_i2_semantic_audit.json", "M7-TRANSVERSAL-FIXTURE"),
            InputArtifact("youtube_adaptation_review", str(fixtures["youtube_adaptation_review"]["review_id"]), self.root / "b5_i3_inputs" / f"g{state.get('generation', 1)}" / "youtube_adaptation_review.json", "M7-TRANSVERSAL-FIXTURE"),
        ]
        directory = self.root / "b5_i3_inputs" / f"g{state.get('generation', 1)}"
        directory.mkdir(parents=True, exist_ok=True)
        for item in refs:
            if item.artifact_kind in {"research_pack", "claims_ledger", "source_access_and_evidence_report", "refined_thesis"}:
                continue
            payload = fixtures[item.artifact_kind]
            schema_by_kind = {
                "human_input": "human_episode_input",
                "active_editorial_profile_reference": "active_editorial_profile",
                "b5_i2_semantic_audit": "b5_i2_semantic_sufficiency_audit",
            }
            errors = validate_against_schema(payload, schema_by_kind.get(item.artifact_kind, item.artifact_kind))
            if errors:
                raise ResearchM7Error(f"B5_I3_TRANSVERSAL_FIXTURE_INVALID:{item.artifact_kind}:" + " | ".join(errors))
            _write_json_atomic(item.path, payload)
        return refs

    def _validate_consumer(self, state: dict[str, Any], manifest: Mapping[str, Any], baseline: Mapping[str, Any], m5: Mapping[str, Any]) -> dict[str, Any]:
        source = self._context(state)["source_access"]
        claims = _read(m5["claims_ledger"]["path"])
        thesis = _read(m5["refined_thesis"]["path"])
        inputs = self._materialize_b5_i3_inputs(state, baseline, m5)
        manifest_ref = next(item for item in state["artifacts"] if item["stage"] == "M6")
        comparison = _read(m5["post_deep_comparison"]["path"])
        return ResearchV2B5I3Adapter.build(manifest, manifest_ref=manifest_ref, research_pack=baseline["phenomenon_base_research"], claims=claims, source_access=source, refined_thesis=thesis, refs=inputs, selected_work_ids=[str(item) for item in comparison["selected_work_ids"]])

    def _b2_result_from_state(self, state: Mapping[str, Any]) -> dict[str, Any]:
        manifest_ref = next(item for item in state["artifacts"] if item["stage"] == "B2")
        plan_ref = next(item for item in state["artifacts"] if item["stage"] == "RESEARCH_PLAN")
        manifest = _read(manifest_ref["path"])
        by_kind = {str(ref["artifact_kind"]): ref for ref in manifest["artifacts"]}
        return {"research_plan": plan_ref, "phenomenon_base_research": by_kind["ResearchPack"], "work_discovery": by_kind["WorkLifecycle"], "base_research_pool": next(ref for ref in manifest["artifacts"] if ref["artifact_id"].endswith(":BASE_RESEARCH_POOL")), "preliminary_fidelity": next(ref for ref in manifest["artifacts"] if ref["artifact_id"].endswith(":PRELIMINARY_FIDELITY")), "initial_sufficiency": next(ref for ref in manifest["artifacts"] if ref["artifact_id"].endswith(":INITIAL_SUFFICIENCY")), "provisional_thesis": by_kind["ThesisArtifact"], "research_comparison": by_kind["ResearchComparison"], "deepening_targets": manifest["deepening_targets"], "lifecycle_projection": manifest["lifecycle_projection"], "execution_manifest": manifest_ref}

    def _m5_result_from_state(self, state: Mapping[str, Any]) -> dict[str, Any]:
        m5_ref = next(item for item in state["artifacts"] if item["stage"] == "M5")
        manifest = _read(m5_ref["path"])
        result = {"execution_manifest": m5_ref}
        for item in manifest["m5_outputs"]:
            result[{"ClaimsLedger": "claims_ledger", "ResearchStopDecisionCollection": "claim_sufficiency", "ResearchComparison": "post_deep_comparison", "RefinedThesis": "refined_thesis"}[item["artifact_kind"]]] = item
        return result

    def _mark_handoff_stale(self, state: dict[str, Any], reason: str) -> None:
        ref = next((item for item in state.get("artifacts", []) if item.get("stage") == "B5_I3_HANDOFF"), None)
        if ref is None:
            return
        payload = _read(ref["path"])
        payload.update({"handoff_state": "STALE", "stale_reason": reason, "validation": {**payload.get("validation", {}), "status": "STALE", "cognition_executed": False}})
        _write_json_atomic(Path(ref["path"]), payload)
        ref["checksum"] = hashlib.sha256(Path(ref["path"]).read_bytes()).hexdigest()

    def assert_handoff_consumable(self, state: Mapping[str, Any] | None = None) -> None:
        current = dict(state) if state is not None else self.store.load()
        if current.get("stale_handoff") or current.get("invalidated_stages"):
            raise ResearchM7Error("B5_I3_HANDOFF_STALE_OR_INVALIDATED")
        ref = next((item for item in current.get("artifacts", []) if item.get("stage") == "B5_I3_HANDOFF"), None)
        if ref is None:
            raise ResearchM7Error("B5_I3_HANDOFF_MISSING")
        payload = _read(ref["path"])
        if payload.get("handoff_state") != "VALID" or payload.get("validation", {}).get("status") != "PASS":
            raise ResearchM7Error("B5_I3_HANDOFF_NOT_CONSUMABLE")

    def _resume_m6_and_handoff(self, state: dict[str, Any]) -> dict[str, Any]:
        b2 = self._b2_result_from_state(state)
        baseline = self._baseline(b2)
        m4_ref = next(item for item in state["artifacts"] if item["stage"] == "M4")
        m5_ref = next(item for item in state["artifacts"] if item["stage"] == "M5")
        m4 = self._m4_result(m4_ref)
        m5 = self._m5_result_from_state(state)
        executor = SyntheticResearchExecutor(state["human_input"])
        chain, provenance = self._provenance(state, b2, m4, m5)
        context = self._context(state)
        context.update(provenance)
        execution_root = self.root / f"canonical_g{state.get('generation', 1)}"
        m6 = ResearchB4Orchestrator(executor, ResearchB4Persistence(execution_root / "b3"), _test_provenance_repository_root=Path(provenance["repository_root"])).run_m6(m5, context=context, research_chain=chain, invalidation_engine=self.invalidation)
        manifest = _read(m6["research_ready_manifest"]["path"])
        self._store_coord(state, "M6", m6["research_ready_manifest"], kind="ResearchReadyManifest")
        state["canonical_refs"]["M6Gate"] = [m6["research_ready_gate"]]
        state["canonical_invocations"] = {**state.get("canonical_invocations", {}), "M6": "ResearchB4Orchestrator.run_m6"}
        state["completed_stages"] = ["INTAKE", "RESEARCH_PLAN", "B2", "M4", "M5", "M6"]
        self.store.save(state)
        handoff = self._validate_consumer(state, manifest, baseline, m5)
        handoff_path = execution_root / "b5_i3_handoff.json"
        _write_json_atomic(handoff_path, handoff)
        self._store_coord(state, "B5_I3_HANDOFF", {"artifact_id": f"{manifest['manifest_id']}:B5_I3", "artifact_kind": "ResearchV2B5I3Handoff", "artifact_version": M7_VERSION, "path": str(handoff_path), "checksum": hashlib.sha256(handoff_path.read_bytes()).hexdigest()}, kind="ResearchV2B5I3Handoff")
        state["completed_stages"] = list(STAGES)
        state.update({"status": "COMPLETED", "next_stage": None, "m7_status": "READY_FOR_OWNER_REVIEW", "research_vertical_e2e": "PASS", "invalidated_stages": [], "stale_handoff": False, "updated_at": _now()})
        self._bind_dependencies(state)
        self.store.save(state)
        return state

    def _bind_dependencies(self, state: dict[str, Any]) -> None:
        by_stage = {item["stage"]: item for item in state.get("artifacts", [])}
        for parent, children in (("B2", ["M4", "M5", "M6", "B5_I3_HANDOFF"]), ("M4", ["M5", "M6", "B5_I3_HANDOFF"]), ("M5", ["M6", "B5_I3_HANDOFF"]), ("M6", ["B5_I3_HANDOFF"])):
            if parent not in by_stage:
                continue
            for child in children:
                if child in by_stage:
                    self.invalidation.register_dependency(by_stage[parent]["artifact_id"], by_stage[child]["artifact_id"])
        state["dependency_graph"] = {key: sorted(value) for key, value in self.invalidation.dependencies.items()}

    def _execute_from_stage(self, state: dict[str, Any], start_stage: str) -> dict[str, Any]:
        """Reopen one invalidated stage and only its downstream dependents."""
        if start_stage not in {"M4", "M5", "M6"}:
            raise ResearchM7Error("M7_FOCAL_START_STAGE_INVALID")
        inp = state["human_input"]
        execution_root = self.root / f"canonical_g{state.get('generation', 1)}"
        executor = SyntheticResearchExecutor(copy.deepcopy(inp))
        adapter = self._adapter(state)
        context = self._context(state)
        b2 = self._b2_result_from_state(state)
        baseline = self._baseline(b2)
        plan = _read(b2["research_plan"]["path"])
        m4 = self._m4_result(next(item for item in state["artifacts"] if item["stage"] == "M4"))
        if start_stage == "M4":
            selected = list(inp["selected_work_ids"])
            if self.selection_mode == "DELEGATED" and inp.get("replace_work_id") and inp.get("substitute_work_id"):
                selected = [work_id for work_id in selected if work_id != inp["replace_work_id"]] + [str(inp["substitute_work_id"])]
            if self.selection_mode == "DELEGATED" and not set(selected).issubset(set(self.delegated_scope)):
                raise ResearchM7Error("M7_DELEGATED_SELECTION_SCOPE_INVALID")
            executor.input["_effective_selected_work_ids"] = list(selected)
            executor.input["selection_mode"] = self.selection_mode
            selection_mode = "DELEGATED_SELECTION" if self.selection_mode == "DELEGATED" else "USER_SELECTION"
            human = HumanDecision(request_id=f"{plan['research_plan_id']}:M4:SELECTION_REQUEST", action="APPROVE", actor_ref="OWNER", channel="TERMINAL") if selection_mode == "USER_SELECTION" else None
            delegation = {"decision": "DELEGATE", "reasons": ["scope explícito"], "policy_version": "1.0.0", "evidence_refs": [f"D-{work_id}" for work_id in selected], "authorized_candidate_set": selected} if selection_mode == "DELEGATED_SELECTION" else None
            m4 = ResearchB3Orchestrator(executor, ResearchB3Persistence(execution_root / "b3"), acquisition_adapter=adapter).run(baseline, context=context, selection_mode=selection_mode, human_decision=human, delegation_decision=delegation, selection_options=[selected])
            state.setdefault("canonical_invocations", {}).update({"M4": "ResearchB3Orchestrator.run"})
            self._store_coord(state, "M4", m4["execution_manifest"], kind="ResearchM4ExecutionManifest")
            state["completed_stages"] = ["INTAKE", "RESEARCH_PLAN", "B2", "M4"]
            self.store.save(state)
        m5 = self._m5_result_from_state(state) if start_stage == "M6" else None
        if start_stage in {"M4", "M5"}:
            executor.input["_effective_selected_work_ids"] = list(_read(m4["execution_manifest"]["path"])["selection"]["selected_work_ids"])
            executor.input["selection_mode"] = self.selection_mode
            m5 = ResearchB3Orchestrator(executor, ResearchB3Persistence(execution_root / "b3"), acquisition_adapter=adapter).run_m5(baseline, m4, context=context)
            state.setdefault("canonical_invocations", {}).update({"M5": "ResearchB3Orchestrator.run_m5"})
            self._store_coord(state, "M5", m5["execution_manifest"], kind="ResearchM5ExecutionManifest")
            state["completed_stages"] = ["INTAKE", "RESEARCH_PLAN", "B2", "M4", "M5"]
            self.store.save(state)
        assert m5 is not None
        chain, provenance = self._provenance(state, b2, m4, m5)
        context.update(provenance)
        m6 = ResearchB4Orchestrator(executor, ResearchB4Persistence(execution_root / "b3"), _test_provenance_repository_root=Path(provenance["repository_root"])).run_m6(m5, context=context, research_chain=chain, invalidation_engine=self.invalidation)
        state.setdefault("canonical_invocations", {}).update({"M6": "ResearchB4Orchestrator.run_m6"})
        manifest = _read(m6["research_ready_manifest"]["path"])
        self._store_coord(state, "M6", m6["research_ready_manifest"], kind="ResearchReadyManifest")
        state["canonical_refs"]["M6Gate"] = [m6["research_ready_gate"]]
        state["completed_stages"] = ["INTAKE", "RESEARCH_PLAN", "B2", "M4", "M5", "M6"]
        self.store.save(state)
        handoff = self._validate_consumer(state, manifest, baseline, m5)
        handoff_path = execution_root / "b5_i3_handoff.json"
        _write_json_atomic(handoff_path, handoff)
        self._store_coord(state, "B5_I3_HANDOFF", {"artifact_id": f"{manifest['manifest_id']}:B5_I3", "artifact_kind": "ResearchV2B5I3Handoff", "artifact_version": M7_VERSION, "path": str(handoff_path), "checksum": hashlib.sha256(handoff_path.read_bytes()).hexdigest()}, kind="ResearchV2B5I3Handoff")
        state["completed_stages"] = list(STAGES)
        state.update({"status": "COMPLETED", "next_stage": None, "m7_status": "READY_FOR_OWNER_REVIEW", "research_vertical_e2e": "PASS", "invalidated_stages": [], "stale_handoff": False, "updated_at": _now()})
        self._bind_dependencies(state)
        self.store.save(state)
        return state

    def _execute(self, state: dict[str, Any], *, stop_after_stage: str | None = None, simulate_no_progress: bool = False) -> dict[str, Any]:
        self._materialize_recovery(state)
        inp = state["human_input"]
        execution_root = self.root / f"canonical_g{state.get('generation', 1)}"
        executor = SyntheticResearchExecutor(copy.deepcopy(inp))
        adapter = self._adapter(state)
        context = self._context(state)
        if simulate_no_progress:
            from src.application.research_b2 import ResearchB2NoProgressGuard
            guard = ResearchB2NoProgressGuard(max_iterations=2)
            guard.observe(gap="M7:synthetic-iteration", evidence_refs=["recovery:S1"], state="OPEN", result={"status": "UNCHANGED"})
            observation = guard.observe(gap="M7:synthetic-iteration", evidence_refs=["recovery:S1"], state="OPEN", result={"status": "UNCHANGED"})
            state["iteration_guard"] = guard.to_dict()
            if observation.status != "NO_PROGRESS":
                raise ResearchM7Error("M7_NO_PROGRESS_PROBE_DID_NOT_STOP")
            state.update({"status": "BLOCKED_NO_PROGRESS", "no_progress_terminal": "NO_PROGRESS / ITERATION_GUARD", "updated_at": _now()})
            self.store.save(state)
            raise ResearchM7Error("NO_PROGRESS / ITERATION_GUARD")
        intake_path = execution_root / "editorial_intake.json"
        intake = {
            "contract": "plan012_m7_synthetic_intake",
            "contract_version": "1.0.0",
            "episode_id": str(inp["episode_id"]),
            "topic": str(inp["topic"]),
            "question": str(inp["initial_question"]),
            "works": list(inp["works"]),
            "profile_binding": {"profile_id": "M7-SYNTHETIC", "profile_version": "1.0.0", "profile_checksum": "synthetic"},
            "editorial_decisions_made": False,
        }
        _write_json_atomic(intake_path, intake)
        self._store_coord(state, "INTAKE", {"artifact_id": f"intake:{inp['episode_id']}", "artifact_kind": "EditorialIntakeHandoff", "artifact_version": "1.0.0", "path": str(intake_path), "checksum": hashlib.sha256(intake_path.read_bytes()).hexdigest()}, kind="EditorialIntakeHandoff")
        state["completed_stages"] = ["INTAKE"]
        self.store.save(state)
        plan = research_plan(inp)
        if validate_research_plan(plan):
            raise ResearchM7Error("M7_RESEARCH_PLAN_INVALID")
        b2 = ResearchB2Orchestrator(executor, ResearchB2Persistence(execution_root / "b2"), acquisition_adapter=adapter).run(plan, context=context)
        state["canonical_invocations"] = {"B2": "ResearchB2Orchestrator.run"}
        source_path = execution_root / "source_access_and_evidence_report.json"
        _write_json_atomic(source_path, context["source_access"])
        state["source_ref"] = {"artifact_id": f"{plan['research_plan_id']}:SOURCE_ACCESS", "artifact_kind": "SourceAccessAndEvidenceReport", "artifact_version": "2.0.0", "path": str(source_path), "checksum": _checksum(context["source_access"])}
        b2_manifest = _read(b2["execution_manifest"]["path"])
        self._store_coord(state, "RESEARCH_PLAN", b2["research_plan"], kind="ResearchPlan")
        self._store_coord(state, "B2", b2["execution_manifest"], kind="ResearchB2ExecutionManifest")
        state["canonical_refs"]["ResearchPack"] = [ref for ref in b2_manifest["artifacts"] if ref["artifact_kind"] == "ResearchPack"]
        state["canonical_refs"]["SourceAccessAndEvidenceReport"] = [state["source_ref"]]
        state["completed_stages"] = ["INTAKE", "RESEARCH_PLAN", "B2"]
        self.store.save(state)
        if stop_after_stage == "B2":
            state.update({"status": "INTERRUPTED", "next_stage": "M4", "updated_at": _now()})
            self.store.save(state)
            return state
        selected = list(inp["selected_work_ids"])
        if self.selection_mode == "DELEGATED" and inp.get("replace_work_id") and inp.get("substitute_work_id"):
            selected = [work_id for work_id in selected if work_id != inp["replace_work_id"]] + [str(inp["substitute_work_id"])]
        if self.selection_mode == "DELEGATED" and not set(selected).issubset(set(self.delegated_scope)):
            raise ResearchM7Error("M7_DELEGATED_SELECTION_SCOPE_INVALID")
        executor.input["_effective_selected_work_ids"] = list(selected)
        executor.input["selection_mode"] = self.selection_mode
        selection_mode = "DELEGATED_SELECTION" if self.selection_mode == "DELEGATED" else "USER_SELECTION"
        human = HumanDecision(request_id=f"{plan['research_plan_id']}:M4:SELECTION_REQUEST", action="APPROVE", actor_ref="OWNER", channel="TERMINAL") if selection_mode == "USER_SELECTION" else None
        delegation = {"decision": "DELEGATE", "reasons": ["scope explícito"], "policy_version": "1.0.0", "evidence_refs": [f"D-{work_id}" for work_id in selected], "authorized_candidate_set": selected} if selection_mode == "DELEGATED_SELECTION" else None
        baseline = self._baseline(b2)
        m4 = ResearchB3Orchestrator(executor, ResearchB3Persistence(execution_root / "b3"), acquisition_adapter=adapter).run(baseline, context=context, selection_mode=selection_mode, human_decision=human, delegation_decision=delegation, selection_options=[selected])
        state.setdefault("canonical_invocations", {}).update({"M4": "ResearchB3Orchestrator.run"})
        self._store_coord(state, "M4", m4["execution_manifest"], kind="ResearchM4ExecutionManifest")
        state["completed_stages"] = ["INTAKE", "RESEARCH_PLAN", "B2", "M4"]
        self.store.save(state)
        if stop_after_stage == "M4":
            state.update({"status": "INTERRUPTED", "next_stage": "M5", "updated_at": _now()})
            self.store.save(state)
            return state
        if inp.get("deep_stop_status") == "MORE_RESEARCH_REQUIRED" and not inp.get("_research_stop_reopened"):
            state.update({"status": "INTERRUPTED", "next_stage": "M4", "research_stop_route": "REOPEN_FOCAL", "updated_at": _now()})
            self.store.save(state)
            return state
        m5 = ResearchB3Orchestrator(executor, ResearchB3Persistence(execution_root / "b3"), acquisition_adapter=adapter).run_m5(baseline, m4, context=context)
        state.setdefault("canonical_invocations", {}).update({"M5": "ResearchB3Orchestrator.run_m5"})
        self._store_coord(state, "M5", m5["execution_manifest"], kind="ResearchM5ExecutionManifest")
        state["completed_stages"] = ["INTAKE", "RESEARCH_PLAN", "B2", "M4", "M5"]
        self.store.save(state)
        if stop_after_stage == "M5":
            state.update({"status": "INTERRUPTED", "next_stage": "M6", "updated_at": _now()})
            self.store.save(state)
            return state
        chain, provenance = self._provenance(state, b2, m4, m5)
        context.update(provenance)
        m6 = ResearchB4Orchestrator(executor, ResearchB4Persistence(execution_root / "b3"), _test_provenance_repository_root=Path(provenance["repository_root"])).run_m6(m5, context=context, research_chain=chain, invalidation_engine=self.invalidation)
        state.setdefault("canonical_invocations", {}).update({"M6": "ResearchB4Orchestrator.run_m6"})
        manifest = _read(m6["research_ready_manifest"]["path"])
        self._store_coord(state, "M6", m6["research_ready_manifest"], kind="ResearchReadyManifest")
        state["canonical_refs"]["M6Gate"] = [m6["research_ready_gate"]]
        state["completed_stages"] = ["INTAKE", "RESEARCH_PLAN", "B2", "M4", "M5", "M6"]
        self.store.save(state)
        handoff = self._validate_consumer(state, manifest, baseline, m5)
        handoff_path = execution_root / "b5_i3_handoff.json"
        _write_json_atomic(handoff_path, handoff)
        self._store_coord(state, "B5_I3_HANDOFF", {"artifact_id": f"{manifest['manifest_id']}:B5_I3", "artifact_kind": "ResearchV2B5I3Handoff", "artifact_version": M7_VERSION, "path": str(handoff_path), "checksum": hashlib.sha256(handoff_path.read_bytes()).hexdigest()}, kind="ResearchV2B5I3Handoff")
        state["completed_stages"] = list(STAGES)
        state.update({"status": "COMPLETED", "next_stage": None, "m7_status": "READY_FOR_OWNER_REVIEW", "research_vertical_e2e": "PASS", "invalidated_stages": [], "stale_handoff": False, "updated_at": _now()})
        self._bind_dependencies(state)
        self.store.save(state)
        return state

    def run(self, human_input: Mapping[str, Any] | None = None, *, resume: bool = False, stop_after_stage: str | None = None, simulate_no_progress: bool = False) -> dict[str, Any]:
        state = self._state(human_input, resume)
        if state.get("status") == "COMPLETED":
            return state
        if stop_after_stage not in {None, "INTAKE", "RESEARCH_PLAN", "B2", "M4", "M5"}:
            raise ResearchM7Error("M7_STOP_STAGE_INVALID")
        if stop_after_stage in {"INTAKE", "RESEARCH_PLAN"}:
            raise ResearchM7Error("M7_STOP_STAGE_NOT_IMPLEMENTED_AT_CANONICAL_BOUNDARY")
        return self._execute(state, stop_after_stage=stop_after_stage, simulate_no_progress=simulate_no_progress)

    def resume(self) -> dict[str, Any]:
        state = self._state(None, True)
        if state.get("status") == "COMPLETED":
            return state
        if state.get("completed_stages", [])[-1:] == ["M5"]:
            return self._resume_m6_and_handoff(state)
        if state.get("invalidated_stages"):
            start_stage = next((stage for stage in STAGES if stage in set(state["invalidated_stages"])), None)
            if start_stage == "B2":
                return self._execute(state)
            if start_stage in {"M4", "M5", "M6"}:
                return self._execute_from_stage(state, start_stage)
            raise ResearchM7Error("M7_FOCAL_RESUME_STAGE_UNKNOWN")
        raise ResearchM7Error("M7_RESUME_REQUIRES_LAST_CANONICAL_STAGE")

    def invalidate(self, stage: str) -> dict[str, Any]:
        state = self.store.load()
        if stage not in STAGES[2:]:
            raise ResearchM7Error("M7_INVALIDATION_STAGE_INVALID")
        self._bind_dependencies(state)
        target = next(item for item in state["artifacts"] if item["stage"] == stage)
        self.invalidation.invalidate_artifact(target["artifact_id"], target["artifact_version"], f"M7 focal invalidation {stage}", "PLAN012_M7")
        affected = {entry.target_artifact_id for entry in self.invalidation.invalidation_log}
        state["invalidated_stages"] = [item["stage"] for item in state["artifacts"] if item["artifact_id"] in affected]
        state["generation"] = int(state.get("generation", 1)) + 1
        self._mark_handoff_stale(state, f"M7 focal invalidation {stage}")
        state.update({"status": "IN_PROGRESS", "next_stage": stage, "research_vertical_e2e": "NOT_DEMONSTRATED", "stale_handoff": "B5_I3_HANDOFF" in state["invalidated_stages"], "updated_at": _now()})
        self.store.save(state)
        return state

    def reopen_focal(self, dependency_artifact_id: str) -> dict[str, Any]:
        state = self.store.load()
        stages = {item["artifact_id"]: item["stage"] for item in state["artifacts"]}
        if dependency_artifact_id not in stages:
            raise ResearchM7Error("M7_REOPEN_DEPENDENCY_UNKNOWN")
        result = self.invalidate(stages[dependency_artifact_id])
        if result.get("human_input", {}).get("deep_stop_status") == "MORE_RESEARCH_REQUIRED":
            result["human_input"]["deep_stop_status"] = "SUFFICIENT_FOR_INTENDED_USE"
            result["human_input"]["_research_stop_reopened"] = True
            result["research_stop_route"] = "REOPENED_AND_RESOLVED"
            self.store.save(result)
        return result

    def assert_software_boundaries(self, state: Mapping[str, Any]) -> None:
        if state.get("real_ai_execution") is not False or state.get("product_use_authorized") is not False or state.get("p2_real_execution") is not False:
            raise ResearchM7Error("M7_PROHIBITED_EXECUTION_STATE")
        handoff = next((item for item in state.get("artifacts", []) if item.get("stage") == "B5_I3_HANDOFF"), None)
        if handoff and any(key in _read(handoff["path"]) for key in NARRATIVE_FIELDS):
            raise ResearchM7Error("M7_NARRATIVE_OUTPUT_PRESENT")
