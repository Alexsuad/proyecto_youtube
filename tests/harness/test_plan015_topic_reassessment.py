from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.application.storage import EpisodeHandle, VaultEpisodeStore
from src.application.topic_belonging import (
    TopicBelongingExecutionError,
    TopicBelongingTechnicalWorkflow,
)


def _workflow(tmp_path: Path) -> tuple[TopicBelongingTechnicalWorkflow, EpisodeHandle]:
    root = tmp_path / "vault"
    store = VaultEpisodeStore(root, "CHANNEL")
    folder = root / "episodios" / "ep_0001_test"
    folder.mkdir(parents=True)
    handle = EpisodeHandle("ep_0001", "test", folder, store.index_path)
    return TopicBelongingTechnicalWorkflow(store, boundary=SimpleNamespace()), handle


def test_reassessment_kind_is_software_selected_from_current_bundle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workflow, handle = _workflow(tmp_path)

    monkeypatch.setattr(
        workflow,
        "_effective_topic_bundle",
        lambda _: {
            "topic_input": {"proposed_territory": "Individuo e identidad"},
            "assessment": {
                "proposed_territory": "Individuo e identidad",
                "territory_classification": "ACTIVE",
            },
        },
    )
    assert workflow._select_reassessment_kind(handle) == "REVIEWER_ONLY_REASSESSMENT"

    monkeypatch.setattr(
        workflow,
        "_effective_topic_bundle",
        lambda _: {
            "topic_input": {"proposed_territory": "Territorio no canónico"},
            "assessment": {
                "proposed_territory": "Territorio no canónico",
                "territory_classification": "UNCLASSIFIED",
            },
        },
    )
    assert workflow._select_reassessment_kind(handle) == "STRUCTURAL_REASSESSMENT"


def test_attempt_records_cannot_mix_reassessment_ids(tmp_path: Path) -> None:
    workflow, handle = _workflow(tmp_path)
    (handle.folder / "roundtrip_results.json").write_text(
        json.dumps(
            {
                "results": [
                    {"stage": "ENRICHMENT", "attempt_number": 3, "reassessment_id": "TBR-3"},
                    {"stage": "PRODUCER", "attempt_number": 3, "reassessment_id": "TBR-other"},
                ]
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(TopicBelongingExecutionError, match="ROUNDTRIP_ATTEMPT_REASSESSMENT_BINDING_MISMATCH"):
        workflow._records_for_attempt(handle, 3)
