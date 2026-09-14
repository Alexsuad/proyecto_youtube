"""Lifecycle operativo de handoffs: bandeja temporal + archivo histórico.

``handoff/`` es una bandeja operativa temporal. Cuando la ejecución de un
episodio ya terminó (STOP técnico) y su evidencia canónica ya está persistida
en el Vault, los paquetes brutos ``RUN-AI-*.json`` / ``RESULT-*.json`` se
mueven a ``Historial/<episode_id>/handoffs/`` con verificación de checksum.

Reglas (fail-closed):
- Ejecución pendiente -> no se mueve nada.
- Vault/destino inaccesible o checksum distinto -> no se borra el origen.
- Destino con mismo nombre y mismo checksum -> idempotente.
- Destino con mismo nombre y distinto checksum -> rechazo sin sobrescribir.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


class HandoffArchiveError(ValueError):
    """El archivado no puede completarse de forma segura."""


STOP_STATUS = "TOPIC_BELONGING_TECHNICAL_STOP"
_EPISODE_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HandoffArchiveError(f"HANDOFF_ARCHIVE_UNREADABLE:{label}:{exc}") from exc
    if not isinstance(data, dict):
        raise HandoffArchiveError(f"HANDOFF_ARCHIVE_INVALID:{label}: se esperaba un objeto JSON")
    return data


def _validated_episode_id(value: Any) -> str:
    if not isinstance(value, str) or not value.strip() or not _EPISODE_ID_PATTERN.match(value.strip()):
        raise HandoffArchiveError("HANDOFF_ARCHIVE_EPISODE_INVALID: episode_id ausente o inválido")
    return value.strip()


def _move_verified(src: Path, dst: Path) -> str:
    """Copia con verificación y solo entonces elimina el origen."""
    try:
        checksum_src = sha256_file(src)
    except OSError as exc:
        raise HandoffArchiveError(f"HANDOFF_ARCHIVE_UNREADABLE:{src.name}:{exc}") from exc
    if dst.exists():
        try:
            checksum_dst = sha256_file(dst)
        except OSError as exc:
            raise HandoffArchiveError(f"HANDOFF_ARCHIVE_DESTINATION_UNREADABLE:{dst.name}:{exc}") from exc
        if checksum_dst == checksum_src:
            # Ya archivado antes: idempotente, se puede retirar el origen.
            try:
                src.unlink()
            except OSError as exc:
                raise HandoffArchiveError(f"HANDOFF_ARCHIVE_CLEANUP_FAILED:{src.name}:{exc}") from exc
            return checksum_src
        raise HandoffArchiveError(
            f"HANDOFF_ARCHIVE_CONFLICT:{dst.name}: mismo nombre con distinto checksum"
        )
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise HandoffArchiveError(f"HANDOFF_ARCHIVE_DESTINATION_UNWRITABLE:{dst.parent}:{exc}") from exc
    try:
        dst.write_bytes(src.read_bytes())
    except OSError as exc:
        raise HandoffArchiveError(f"HANDOFF_ARCHIVE_COPY_FAILED:{src.name}:{exc}") from exc
    try:
        checksum_dst = sha256_file(dst)
    except OSError as exc:
        raise HandoffArchiveError(f"HANDOFF_ARCHIVE_VERIFY_FAILED:{dst.name}:{exc}") from exc
    if checksum_dst != checksum_src:
        raise HandoffArchiveError(f"HANDOFF_ARCHIVE_CHECKSUM_MISMATCH:{src.name}")
    try:
        src.unlink()
    except OSError as exc:
        raise HandoffArchiveError(f"HANDOFF_ARCHIVE_CLEANUP_FAILED:{src.name}:{exc}") from exc
    return checksum_src


def archive_completed_handoffs(
    *,
    handoff_dir: str | Path,
    history_root: str | Path,
    episode_id: str,
    completed_handoff_ids: set[str],
    is_terminated: bool,
) -> dict[str, Any]:
    """Archiva handoffs completados; pendientes e inválidos permanecen."""
    episode = _validated_episode_id(episode_id)
    handoff_path = Path(handoff_dir)
    history_path = Path(history_root)
    if not handoff_path.is_dir():
        raise HandoffArchiveError(f"HANDOFF_ARCHIVE_HANDOFF_DIR_MISSING:{handoff_path}")
    if history_path.exists() and not history_path.is_dir():
        raise HandoffArchiveError(f"HANDOFF_ARCHIVE_HISTORY_ROOT_UNWRITABLE:{history_path}")

    candidates = sorted(
        [path for path in handoff_path.iterdir() if path.is_file() and (path.name.startswith("RUN-AI-") or path.name.startswith("RESULT-")) and path.suffix == ".json"],
        key=lambda item: item.name,
    )
    report: dict[str, Any] = {
        "episode_id": episode,
        "history_dir": str(history_path / episode / "handoffs"),
        "archived": [],
        "pending": [],
        "skipped": [],
        "checksums": {},
    }
    if not is_terminated:
        report["pending"] = [path.name for path in candidates]
        return report
    completed = {str(item) for item in completed_handoff_ids if str(item).strip()}
    for path in candidates:
        try:
            payload = _read_json_object(path, path.name)
        except HandoffArchiveError:
            report["skipped"].append({"file": path.name, "reason": "UNREADABLE"})
            continue
        payload_episode = payload.get("episode_id")
        if not isinstance(payload_episode, str) or payload_episode.strip() != episode:
            report["skipped"].append({"file": path.name, "reason": "EPISODE_MISMATCH"})
            continue
        handoff_id = payload.get("handoff_id")
        if not isinstance(handoff_id, str) or not handoff_id.strip():
            report["skipped"].append({"file": path.name, "reason": "HANDOFF_ID_MISSING"})
            continue
        if handoff_id.strip() not in completed:
            report["pending"].append(path.name)
            continue
        checksum = _move_verified(path, history_path / episode / "handoffs" / path.name)
        report["archived"].append(path.name)
        report["checksums"][path.name] = checksum
    return report


def archive_episode_handoffs_from_vault(
    *,
    handoff_dir: str | Path,
    history_root: str | Path,
    episode_folder: str | Path,
) -> dict[str, Any]:
    """Deriva el estado canónico desde la carpeta del episodio y archiva."""
    folder = Path(episode_folder)
    workflow = _read_json_object(folder / "workflow_state.json", "workflow_state.json")
    episode_state = _read_json_object(folder / "episode_state.json", "episode_state.json")
    episode_id = _validated_episode_id(workflow.get("episode_id") or episode_state.get("episode_id"))
    if str(episode_state.get("episode_id") or episode_id) != episode_id or str(workflow.get("episode_id") or episode_id) != episode_id:
        raise HandoffArchiveError("HANDOFF_ARCHIVE_EPISODE_MISMATCH: estados del episodio inconsistentes")
    results = _read_json_object(folder / "roundtrip_results.json", "roundtrip_results.json").get("results", [])
    if not isinstance(results, list) or not results:
        raise HandoffArchiveError("HANDOFF_ARCHIVE_NO_RESULTS: sin evidencia canónica persistida")
    completed = {str(item.get("handoff_id")) for item in results if isinstance(item, dict) and str(item.get("handoff_id") or "").strip()}
    if not completed:
        raise HandoffArchiveError("HANDOFF_ARCHIVE_NO_RESULTS: sin handoff_ids persistidos")
    return archive_completed_handoffs(
        handoff_dir=handoff_dir,
        history_root=history_root,
        episode_id=episode_id,
        completed_handoff_ids=completed,
        is_terminated=str(workflow.get("status") or "") == STOP_STATUS,
    )
