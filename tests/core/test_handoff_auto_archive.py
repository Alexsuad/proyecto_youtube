"""Integration: normal Topic Belonging flow auto-archives completed handoffs.

These tests never call the archive helper directly; they drive the public
service flow (start/import/resume) and observe ``handoff/`` vs ``Historial/``.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from src.application.handoff_archive import HandoffArchiveError
from src.core.p2_real_reporter import build_p2_report
from tests.harness.test_plan009_p2_roundtrip import (
    ROOT,
    EpisodeApplicationService,
    _cleanup_handoffs,
    _cognitive_assessment,
    _cognitive_decision,
    _cognitive_proposal,
    _finish_roundtrip,
    _materialized_producer_assessment,
    _materialized_topic_input,
    _pending_package,
    _result_for,
    _start,
)


def _history_handoffs(service: EpisodeApplicationService, episode_id: str) -> Path:
    return Path(service._p2_test_vault_root) / "CHANNEL" / "Historial" / episode_id / "handoffs"


def _run_full_flow_with_results_in_handoff(
    service: EpisodeApplicationService,
    episode,
    package: Path,
    tmp_path: Path,
    tag: str,
    created: list[Path] | None = None,
) -> list[Path]:
    """Drive ENRICHMENT → PRODUCER → REVIEWER writing RESULT envelopes in handoff/.

    When ``created`` is given, every generated path is appended live so a
    failing flow still leaves full cleanup information to the caller.
    """
    handoff_dir = ROOT / "handoff"
    local: list[Path] = []

    def _track(path: Path) -> Path:
        local.append(path)
        if created is not None:
            created.append(path)
        return path

    _track(package)
    service.import_result(
        episode.episode_id,
        _result_for(package, _cognitive_proposal(), f"RESULT-{tag}-ENRICHMENT", handoff_dir / f"RESULT-{package.stem}.json"),
    )
    _track(handoff_dir / f"RESULT-{package.stem}.json")
    service.resume(episode.episode_id)
    _, _, package = _pending_package(episode)
    _track(package)
    topic = _materialized_topic_input(episode)
    service.import_result(
        episode.episode_id,
        _result_for(
            package,
            _cognitive_assessment(topic, f"RESULT-{tag}-PRODUCER"),
            f"RESULT-{tag}-PRODUCER",
            handoff_dir / f"RESULT-{package.stem}.json",
        ),
    )
    _track(handoff_dir / f"RESULT-{package.stem}.json")
    service.resume(episode.episode_id)
    _, _, package = _pending_package(episode)
    _track(package)
    assessment = _materialized_producer_assessment(episode)
    service.import_result(
        episode.episode_id,
        _result_for(
            package,
            _cognitive_decision(assessment),
            f"RESULT-{tag}-REVIEWER",
            handoff_dir / f"RESULT-{package.stem}.json",
        ),
    )
    _track(handoff_dir / f"RESULT-{package.stem}.json")
    final = service.resume(episode.episode_id)
    assert final["state"]["status"] == "TOPIC_BELONGING_TECHNICAL_STOP"
    return local


def test_normal_flow_auto_archives_run_and_result_without_manual_call(tmp_path: Path) -> None:
    created: list[Path] = []
    service = None
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        tag = tmp_path.name.replace("_", "")[-8:]
        created.extend(
            _run_full_flow_with_results_in_handoff(service, episode, package, tmp_path, tag)[1:]
        )
        run_names = sorted(path.name for path in created if path.name.startswith("RUN-AI-"))
        result_names = sorted(path.name for path in created if path.name.startswith("RESULT-"))
        assert len(run_names) == 3 and len(result_names) == 3

        history = _history_handoffs(service, episode.episode_id)
        archived = sorted(path.name for path in history.iterdir())
        assert archived == sorted(run_names + result_names)

        handoff_dir = ROOT / "handoff"
        residue = [path.name for path in handoff_dir.iterdir()] if handoff_dir.is_dir() else []
        assert not any(name in residue for name in run_names + result_names)

        records = json.loads((episode.folder / "roundtrip_results.json").read_text(encoding="utf-8"))["results"]
        assert len(records) == 3
        for record in records:
            ref = Path(str(record["handoff_package_ref"]))
            assert ref.parent == history
            assert ref.is_file()
            package_data = json.loads(ref.read_text(encoding="utf-8"))
            assert package_data["package_checksum"] == record["package_checksum"]
            assert package_data["handoff_id"] == record["handoff_id"]

        report = build_p2_report(episode.folder)
        assert report.result == "PASS"
    finally:
        _cleanup_handoffs(created, service)


def test_pending_handoff_remains_visible_and_history_empty(tmp_path: Path) -> None:
    created: list[Path] = []
    service = None
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        workflow = json.loads((episode.folder / "workflow_state.json").read_text(encoding="utf-8"))
        assert workflow["status"] == "PENDING_EXTERNAL_RESULT"

        assert package.is_file()
        history_root = Path(service._p2_test_vault_root) / "CHANNEL" / "Historial"
        assert not history_root.exists()
    finally:
        _cleanup_handoffs(created, service)


def test_unwritable_history_preserves_canonical_result_and_source(tmp_path: Path) -> None:
    created: list[Path] = []
    service = None
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        tag = tmp_path.name.replace("_", "")[-8:]
        history_root = Path(service._p2_test_vault_root) / "CHANNEL" / "Historial"
        history_root.write_text("bloqueo: no es un directorio", encoding="utf-8")

        with pytest.raises(HandoffArchiveError, match="HANDOFF_ARCHIVE"):
            _run_full_flow_with_results_in_handoff(service, episode, package, tmp_path, tag, created)

        records = json.loads((episode.folder / "roundtrip_results.json").read_text(encoding="utf-8"))["results"]
        assert len(records) == 3
        assert (episode.folder / "04_topic_belonging_decision.json").is_file()
        assert json.loads((episode.folder / "workflow_state.json").read_text(encoding="utf-8"))["status"] == (
            "TOPIC_BELONGING_TECHNICAL_STOP"
        )
        handoff_names = {path.name for path in (ROOT / "handoff").iterdir()}
        for record in records:
            assert f"{record['handoff_id']}.json" in handoff_names
    finally:
        _cleanup_handoffs(created, service)


def test_existing_roundtrip_regression_still_passes_with_auto_archive(tmp_path: Path) -> None:
    created: list[Path] = []
    service = None
    try:
        service, episode, package = _start(tmp_path)
        created.append(package)
        created.extend(_finish_roundtrip(service, episode, tmp_path))
        final = service.resume(episode.episode_id)
        assert final["state"]["status"] == "TOPIC_BELONGING_TECHNICAL_STOP"
        report = build_p2_report(episode.folder)
        assert report.result == "PASS"
        checksum = hashlib.sha256(
            (episode.folder / "04_topic_belonging_decision.json").read_bytes()
        ).hexdigest()
        assert len(checksum) == 64
    finally:
        _cleanup_handoffs(created, service)
