from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from src.application.handoff_archive import (
    HandoffArchiveError,
    archive_completed_handoffs,
    archive_episode_handoffs_from_vault,
    sha256_file,
)


def _payload(episode_id: str, handoff_id: str) -> dict:
    return {"episode_id": episode_id, "handoff_id": handoff_id, "marker": handoff_id}


def _write_handoff(handoff_dir: Path, name: str, payload: dict) -> Path:
    path = handoff_dir / name
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def _episode_folder(folder: Path, *, status: str, episode_id: str = "ep_0003", completed: tuple[str, ...] = ("H-1",)) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "workflow_state.json").write_text(
        json.dumps({"episode_id": episode_id, "status": status}), encoding="utf-8"
    )
    (folder / "episode_state.json").write_text(
        json.dumps({"episode_id": episode_id, "status": status}), encoding="utf-8"
    )
    (folder / "roundtrip_results.json").write_text(
        json.dumps({"results": [{"handoff_id": item} for item in completed]}), encoding="utf-8"
    )
    return folder


def test_completed_handoffs_are_archived_with_verified_checksum(tmp_path: Path) -> None:
    handoff_dir = tmp_path / "handoff"
    handoff_dir.mkdir()
    run = _write_handoff(handoff_dir, "RUN-AI-aaa.json", _payload("ep_0003", "H-1"))
    res = _write_handoff(handoff_dir, "RESULT-RUN-AI-aaa.json", _payload("ep_0003", "H-1"))
    expected = {run.name: sha256_file(run), res.name: sha256_file(res)}
    history = tmp_path / "Historial"

    report = archive_completed_handoffs(
        handoff_dir=handoff_dir,
        history_root=history,
        episode_id="ep_0003",
        completed_handoff_ids={"H-1"},
        is_terminated=True,
    )

    assert sorted(report["archived"]) == ["RESULT-RUN-AI-aaa.json", "RUN-AI-aaa.json"]
    assert report["pending"] == []
    assert report["checksums"] == expected
    assert not run.exists() and not res.exists()
    for name, checksum in expected.items():
        dest = history / "ep_0003" / "handoffs" / name
        assert dest.is_file()
        assert hashlib.sha256(dest.read_bytes()).hexdigest() == checksum


def test_pending_execution_keeps_handoffs_visible(tmp_path: Path) -> None:
    handoff_dir = tmp_path / "handoff"
    handoff_dir.mkdir()
    run = _write_handoff(handoff_dir, "RUN-AI-aaa.json", _payload("ep_0003", "H-1"))

    report = archive_completed_handoffs(
        handoff_dir=handoff_dir,
        history_root=tmp_path / "Historial",
        episode_id="ep_0003",
        completed_handoff_ids={"H-1"},
        is_terminated=False,
    )

    assert report["archived"] == []
    assert report["pending"] == ["RUN-AI-aaa.json"]
    assert run.is_file()


def test_uncompleted_handoff_id_stays_pending(tmp_path: Path) -> None:
    handoff_dir = tmp_path / "handoff"
    handoff_dir.mkdir()
    run = _write_handoff(handoff_dir, "RUN-AI-aaa.json", _payload("ep_0003", "H-9"))

    report = archive_completed_handoffs(
        handoff_dir=handoff_dir,
        history_root=tmp_path / "Historial",
        episode_id="ep_0003",
        completed_handoff_ids={"H-1"},
        is_terminated=True,
    )

    assert report["archived"] == []
    assert report["pending"] == ["RUN-AI-aaa.json"]
    assert run.is_file()


def test_unwritable_history_root_preserves_source(tmp_path: Path) -> None:
    handoff_dir = tmp_path / "handoff"
    handoff_dir.mkdir()
    run = _write_handoff(handoff_dir, "RUN-AI-aaa.json", _payload("ep_0003", "H-1"))
    blocker = tmp_path / "blocker"
    blocker.write_text("no es un directorio", encoding="utf-8")

    with pytest.raises(HandoffArchiveError):
        archive_completed_handoffs(
            handoff_dir=handoff_dir,
            history_root=blocker,
            episode_id="ep_0003",
            completed_handoff_ids={"H-1"},
            is_terminated=True,
        )
    assert run.is_file()


def test_archive_is_idempotent(tmp_path: Path) -> None:
    handoff_dir = tmp_path / "handoff"
    handoff_dir.mkdir()
    _write_handoff(handoff_dir, "RUN-AI-aaa.json", _payload("ep_0003", "H-1"))
    history = tmp_path / "Historial"
    kwargs = {
        "handoff_dir": handoff_dir,
        "history_root": history,
        "episode_id": "ep_0003",
        "completed_handoff_ids": {"H-1"},
        "is_terminated": True,
    }
    first = archive_completed_handoffs(**kwargs)
    second = archive_completed_handoffs(**kwargs)

    assert first["archived"] == ["RUN-AI-aaa.json"]
    assert second["archived"] == []
    assert (history / "ep_0003" / "handoffs" / "RUN-AI-aaa.json").is_file()


def test_conflicting_destination_fails_closed(tmp_path: Path) -> None:
    handoff_dir = tmp_path / "handoff"
    handoff_dir.mkdir()
    run = _write_handoff(handoff_dir, "RUN-AI-aaa.json", _payload("ep_0003", "H-1"))
    history = tmp_path / "Historial"
    dest = history / "ep_0003" / "handoffs" / "RUN-AI-aaa.json"
    dest.parent.mkdir(parents=True)
    dest.write_text(json.dumps(_payload("ep_0003", "OTRO")), encoding="utf-8")

    with pytest.raises(HandoffArchiveError, match="HANDOFF_ARCHIVE_CONFLICT"):
        archive_completed_handoffs(
            handoff_dir=handoff_dir,
            history_root=history,
            episode_id="ep_0003",
            completed_handoff_ids={"H-1"},
            is_terminated=True,
        )
    assert run.is_file()


def test_invalid_episode_id_moves_nothing(tmp_path: Path) -> None:
    handoff_dir = tmp_path / "handoff"
    handoff_dir.mkdir()
    run = _write_handoff(handoff_dir, "RUN-AI-aaa.json", _payload("ep_0003", "H-1"))

    with pytest.raises(HandoffArchiveError, match="HANDOFF_ARCHIVE_EPISODE_INVALID"):
        archive_completed_handoffs(
            handoff_dir=handoff_dir,
            history_root=tmp_path / "Historial",
            episode_id="  ",
            completed_handoff_ids={"H-1"},
            is_terminated=True,
        )
    assert run.is_file()


def test_completed_execution_leaves_no_handoff_residue(tmp_path: Path) -> None:
    handoff_dir = tmp_path / "handoff"
    handoff_dir.mkdir()
    _write_handoff(handoff_dir, "RUN-AI-aaa.json", _payload("ep_0003", "H-1"))
    _write_handoff(handoff_dir, "RESULT-RUN-AI-aaa.json", _payload("ep_0003", "H-1"))

    archive_completed_handoffs(
        handoff_dir=handoff_dir,
        history_root=tmp_path / "Historial",
        episode_id="ep_0003",
        completed_handoff_ids={"H-1"},
        is_terminated=True,
    )

    residue = [path.name for path in handoff_dir.iterdir() if path.name.startswith(("RUN-AI-", "RESULT-"))]
    assert residue == []


def test_vault_driven_archive_respects_stop_and_results(tmp_path: Path) -> None:
    handoff_dir = tmp_path / "handoff"
    handoff_dir.mkdir()
    _write_handoff(handoff_dir, "RUN-AI-aaa.json", _payload("ep_0003", "H-1"))
    episode = _episode_folder(tmp_path / "ep", status="TOPIC_BELONGING_TECHNICAL_STOP")

    report = archive_episode_handoffs_from_vault(
        handoff_dir=handoff_dir,
        history_root=tmp_path / "Historial",
        episode_folder=episode,
    )

    assert report["archived"] == ["RUN-AI-aaa.json"]
    assert (tmp_path / "Historial" / "ep_0003" / "handoffs" / "RUN-AI-aaa.json").is_file()


def test_vault_driven_archive_keeps_pending_visible(tmp_path: Path) -> None:
    handoff_dir = tmp_path / "handoff"
    handoff_dir.mkdir()
    run = _write_handoff(handoff_dir, "RUN-AI-aaa.json", _payload("ep_0003", "H-1"))
    episode = _episode_folder(tmp_path / "ep", status="PENDING_EXTERNAL_RESULT")

    report = archive_episode_handoffs_from_vault(
        handoff_dir=handoff_dir,
        history_root=tmp_path / "Historial",
        episode_folder=episode,
    )

    assert report["archived"] == []
    assert run.is_file()
