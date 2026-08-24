"""Storage ports and the local/mounted Vault adapter."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import threading
import unicodedata
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.application.contracts import HumanInput
from src.application.interaction import HumanDecision, HumanDecisionRequest, validate_human_decision


class StorageError(RuntimeError):
    """A persistence operation failed and must not be reported as success."""


_PROCESS_LOCKS: dict[str, threading.RLock] = {}
_PROCESS_LOCKS_GUARD = threading.Lock()


@dataclass(frozen=True)
class EpisodeHandle:
    episode_id: str
    slug: str
    folder: Path
    index_path: Path


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temp_name, path)
    except OSError as exc:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise StorageError(f"No se pudo persistir {path.name}: {exc}") from exc


def _read_json(path: Path, default: dict[str, Any] | None = None) -> dict[str, Any]:
    if not path.exists():
        return dict(default or {})
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StorageError(f"No se pudo leer {path}: {exc}") from exc


def slugify(value: str, fallback: str = "episodio") -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", normalized.lower()).strip("_")
    return (slug or fallback)[:50]


class VaultEpisodeStore:
    """Filesystem adapter compatible with a local, mounted, or synced Vault."""

    INDEX_FILENAME = "episodes_index.json"
    ADMINISTRATIVE_CLOSED_STATE = "ADMINISTRATIVELY_CLOSED"
    ADMINISTRATIVE_CLOSED_INDEX_STATUS = "administratively_cerrado"
    ADMINISTRATIVE_CLOSURE_FILENAME = "administrative_recovery.json"

    def __init__(self, vault_root: str | Path, channel_id: str):
        if not str(vault_root).strip():
            raise StorageError("vault_root es obligatorio.")
        if not str(channel_id).strip():
            raise StorageError("channel_id es obligatorio.")
        self.vault_root = Path(os.path.expandvars(str(vault_root))).expanduser()
        self.channel_id = str(channel_id).strip()
        self.channel_path = self.vault_root / self.channel_id
        self.episodes_path = self.channel_path / "episodios"
        self.index_path = self.channel_path / "index" / self.INDEX_FILENAME

    @classmethod
    def from_settings(cls, settings_path: str | Path) -> "VaultEpisodeStore":
        settings = _read_json(Path(settings_path))
        if not settings.get("vault_root") or not settings.get("channel_id"):
            raise StorageError("local_settings.json requiere vault_root y channel_id.")
        return cls(settings["vault_root"], settings["channel_id"])

    def _load_index(self) -> dict[str, Any]:
        return _read_json(self.index_path, {"episodes": [], "last_updated": None})

    def _next_number(self, episodes: list[dict[str, Any]]) -> int:
        numbers = [
            int(match.group(1))
            for item in episodes
            if (match := re.fullmatch(r"ep_(\d+)", str(item.get("ep_id", ""))))
        ]
        return max(numbers, default=0) + 1

    @contextmanager
    def _index_lock(self):
        """Serialize index allocation across CLI processes without a dependency."""
        lock_path = self.index_path.with_suffix(self.index_path.suffix + ".lock")
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        lock_key = str(lock_path.resolve())
        with _PROCESS_LOCKS_GUARD:
            process_lock = _PROCESS_LOCKS.setdefault(lock_key, threading.RLock())
        process_lock.acquire()
        try:
            fd = os.open(lock_path, os.O_RDWR | os.O_CREAT)
        except Exception:
            process_lock.release()
            raise
        operating_system_lock = False
        try:
            if os.name == "nt":
                import msvcrt

                if os.path.getsize(lock_path) == 0:
                    os.write(fd, b"0")
                os.lseek(fd, 0, os.SEEK_SET)
                msvcrt.locking(fd, msvcrt.LK_LOCK, 1)
                operating_system_lock = True
            else:
                import fcntl

                fcntl.flock(fd, fcntl.LOCK_EX)
                operating_system_lock = True
            yield
        finally:
            try:
                if operating_system_lock:
                    if os.name == "nt":
                        import msvcrt

                        os.lseek(fd, 0, os.SEEK_SET)
                        msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
                    else:
                        import fcntl

                        fcntl.flock(fd, fcntl.LOCK_UN)
            finally:
                os.close(fd)
                process_lock.release()

    def create_episode(
        self,
        human_input: HumanInput,
        *,
        handoff: dict[str, Any],
        profile: dict[str, Any],
        run_id: str,
        mission_id: str | None = None,
        episode_number: int | None = None,
        slug_override: str | None = None,
    ) -> EpisodeHandle:
        with self._index_lock():
            return self._create_episode_locked(
                human_input,
                handoff=handoff,
                profile=profile,
                run_id=run_id,
                mission_id=mission_id,
                episode_number=episode_number,
                slug_override=slug_override,
            )

    def create_legacy_episode(self, *, episode_number: int, slug: str) -> EpisodeHandle:
        """Create only the technical folder/index record used by the legacy wrapper."""
        if not self.channel_path.is_dir():
            raise StorageError(
                f"La carpeta del canal no existe: {self.channel_path}. Ejecuta Gate 0 antes del wrapper legacy."
            )
        with self._index_lock():
            return self._create_episode_locked(
                None,
                handoff=None,
                profile=None,
                run_id=f"LEGACY-RUN-{episode_number}",
                episode_number=episode_number,
                slug_override=slug,
                legacy=True,
            )

    def _create_episode_locked(
        self,
        human_input: HumanInput | None,
        *,
        handoff: dict[str, Any] | None,
        profile: dict[str, Any] | None,
        run_id: str,
        mission_id: str | None = None,
        episode_number: int | None = None,
        slug_override: str | None = None,
        legacy: bool = False,
    ) -> EpisodeHandle:
        try:
            self.episodes_path.mkdir(parents=True, exist_ok=True)
            self.index_path.parent.mkdir(parents=True, exist_ok=True)
            index = self._load_index()
            episodes = list(index.get("episodes", []))
            in_progress = [item.get("ep_id", "?") for item in episodes if item.get("estado") == "en_progreso"]
            if in_progress:
                raise StorageError(
                    "Ya existe un episodio en progreso: " + ", ".join(map(str, in_progress))
                )
            number = episode_number if episode_number is not None else self._next_number(episodes)
            if number < 1:
                raise StorageError("El número del episodio debe ser positivo.")
            episode_id = f"ep_{number:04d}"
            source_text = (
                (human_input.content or (human_input.works[0] if human_input.works else ""))
                if human_input is not None
                else slug_override or "episodio"
            )
            slug = slugify(slug_override or source_text)
            folder = self.episodes_path / f"{episode_id}_{slug}"
            if folder.exists() or any(item.get("ep_id") == episode_id for item in episodes):
                raise StorageError(f"El episodio {episode_id} ya existe; no se sobrescribe.")
            folder.mkdir(parents=False, exist_ok=False)
            try:
                now = datetime.now(timezone.utc).isoformat()
                if legacy:
                    state = {
                        "episode_id": episode_id,
                        "status": "LEGACY_TECHNICAL_INITIALIZATION",
                        "run_id": run_id,
                        "editorial_input_registered": False,
                        "provenance": {"source": "LEGACY_SCRIPT", "semantic_input": False},
                        "updated_at": now,
                    }
                    entry = {
                        "ep_id": episode_id,
                        "slug": slug,
                        "ep_folder": folder.name,
                        "ep_path": str(folder),
                        "estado": "en_progreso",
                        "application_status": "LEGACY_TECHNICAL_INITIALIZATION",
                        "entry_mode": None,
                        "human_input_id": None,
                        "input_origin": "LEGACY_SCRIPT_TECHNICAL",
                        "creado": now,
                        "cerrado": None,
                    }
                else:
                    _write_json_atomic(folder / "00_human_input.json", human_input.to_dict())
                    _write_json_atomic(folder / "01_editorial_intake_handoff.json", handoff or {})
                    state = {
                        "episode_id": episode_id,
                        "status": "READY_FOR_EDITORIAL_ENRICHMENT",
                        "run_id": run_id,
                        "profile_binding": {
                            "profile_id": profile["ACTIVE_PROFILE_ID"],
                            "profile_version": profile["ACTIVE_PROFILE_VERSION"],
                            "profile_checksum": profile["profile_checksum"],
                        },
                        "updated_at": now,
                    }
                    entry = {
                        "ep_id": episode_id,
                        "slug": slug,
                        "ep_folder": folder.name,
                        "ep_path": str(folder),
                        "estado": "en_progreso",
                        "application_status": "READY_FOR_EDITORIAL_ENRICHMENT",
                        "entry_mode": human_input.mode.value,
                        "human_input_id": human_input.interaction_id,
                        "profile_id": profile["ACTIVE_PROFILE_ID"],
                        "profile_version": profile["ACTIVE_PROFILE_VERSION"],
                        "profile_checksum": profile["profile_checksum"],
                        "creado": now,
                        "cerrado": None,
                    }
                if mission_id:
                    state["mission_id"] = str(mission_id)
                    entry["mission_id"] = str(mission_id)
                state_anchor = {
                    key: value
                    for key, value in state.items()
                    if key not in {"status", "updated_at", "administrative_closure_ref"}
                }
                index_anchor = {
                    key: value
                    for key, value in entry.items()
                    if key not in {"estado", "application_status", "cerrado", "administrative_closure_ref", "administrative_closure"}
                }
                origin = {
                    "episode_id": episode_id,
                    "origin": "LEGACY_M1" if legacy else "MODERN_M1",
                    "state_anchor_sha256": hashlib.sha256(
                        json.dumps(state_anchor, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
                    ).hexdigest(),
                    "index_anchor_sha256": hashlib.sha256(
                        json.dumps(index_anchor, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
                    ).hexdigest(),
                }
                origin["origin_checksum"] = hashlib.sha256(
                    json.dumps(origin, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
                ).hexdigest()
                _write_json_atomic(folder / "episode_origin.json", origin)
                _write_json_atomic(folder / "episode_state.json", state)
                episodes.append(entry)
                index["episodes"] = episodes
                index["last_updated"] = datetime.now(timezone.utc).isoformat()
                _write_json_atomic(self.index_path, index)
            except Exception:
                try:
                    for child in folder.iterdir():
                        child.unlink()
                    folder.rmdir()
                except OSError:
                    pass
                raise
            return EpisodeHandle(episode_id, slug, folder, self.index_path)
        except StorageError:
            raise
        except OSError as exc:
            raise StorageError(f"No se pudo crear el episodio: {exc}") from exc

    def record_topic_belonging_vertical(
        self,
        handle: EpisodeHandle,
        *,
        topic_input: dict[str, Any],
        assessment: dict[str, Any],
        decision: dict[str, Any],
        gate_result: dict[str, Any],
        lineage: dict[str, Any],
        executions: list[dict[str, Any]],
    ) -> None:
        """Persist the bounded Topic Belonging vertical as one editorial batch."""
        artifacts = {
            "02_topic_belonging_input.json": topic_input,
            "03_topic_belonging_assessment.json": assessment,
            "04_topic_belonging_decision.json": decision,
            "05_topic_belonging_gate.json": gate_result,
            "topic_belonging_lineage.json": lineage,
            "topic_belonging_execution.json": {"executions": executions},
        }
        with self._index_lock():
            paths = [handle.folder / name for name in artifacts]
            if any(path.exists() for path in paths):
                raise StorageError("La vertical Topic Belonging ya tiene artefactos persistidos.")
            written: list[Path] = []
            try:
                for path in paths:
                    _write_json_atomic(path, artifacts[path.name])
                    written.append(path)
            except Exception:
                for path in written:
                    try:
                        path.unlink(missing_ok=True)
                    except OSError:
                        pass
                raise

    def _entry(self, episode_id: str) -> dict[str, Any]:
        entry = next((item for item in self._load_index().get("episodes", []) if item.get("ep_id") == episode_id), None)
        if not entry:
            raise StorageError(f"No existe el episodio {episode_id} en el índice.")
        return entry

    def _folder_for_entry(self, entry: dict[str, Any]) -> Path:
        ep_folder = str(entry.get("ep_folder", "")).strip()
        folder = self.episodes_path / ep_folder if ep_folder else Path("")
        if not ep_folder:
            # Legacy indexes may not have ep_folder; retain their absolute path fallback.
            folder = Path(entry.get("ep_path", ""))
        if not str(folder).strip():
            return folder
        base = self.episodes_path.resolve()
        resolved = folder.resolve(strict=False)
        if resolved == base:
            raise StorageError("EPISODE_PATH_NOT_EPISODE: el destino debe ser una carpeta de episodio")
        try:
            resolved.relative_to(base)
        except ValueError as exc:
            raise StorageError("EPISODE_PATH_OUTSIDE_VAULT: no se permite recovery fuera del Vault") from exc
        if folder.is_symlink():
            raise StorageError("EPISODE_PATH_SYMLINK_UNSUPPORTED: no se modifica un destino enlazado")
        return folder

    @staticmethod
    def _file_checksum(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def _evidence_files(self, folder: Path) -> list[dict[str, str]]:
        if not folder.is_dir():
            return []
        evidence: list[dict[str, str]] = []
        for path in sorted(item for item in folder.rglob("*") if item.is_file() and item.name != self.ADMINISTRATIVE_CLOSURE_FILENAME):
            evidence.append(
                {
                    "path": path.relative_to(folder).as_posix(),
                    "sha256": self._file_checksum(path),
                }
            )
        return evidence

    def _irrecoverability_basis(self, folder: Path) -> tuple[str, list[str], dict[str, Any] | None]:
        """Prove a technical recovery gap without treating a healthy stop as abandoned."""
        if not folder.is_dir():
            return "EPISODE_FOLDER_MISSING", [], None

        state_path = folder / "episode_state.json"
        state: dict[str, Any] | None = None
        if state_path.is_file():
            try:
                state = _read_json(state_path)
            except StorageError:
                return "EPISODE_STATE_INVALID", [state_path.name], None
            if state.get("status") == "TOPIC_BELONGING_TECHNICAL_STOP":
                raise StorageError("EPISODE_RECOVERABLE_TECHNICAL_STOP: no se cierra administrativamente un episodio sano")

        missing = [
            name
            for name in ("00_human_input.json", "01_editorial_intake_handoff.json", "episode_state.json")
            if not (folder / name).is_file()
        ]
        if missing:
            return "REQUIRED_ARTIFACT_MISSING", missing, state

        try:
            _read_json(folder / "00_human_input.json")
            _read_json(folder / "01_editorial_intake_handoff.json")
        except StorageError:
            return "REQUIRED_ARTIFACT_INVALID", ["00_human_input.json", "01_editorial_intake_handoff.json"], state

        # With the intake contract intact, the application can still attempt normal resume.
        raise StorageError("EPISODE_RECOVERABILITY_NOT_PROVEN: se conserva el episodio para reanudación normal")

    def administratively_close_irrecoverable_episode(
        self,
        episode_id: str,
        *,
        reason: str,
        actor: str,
        source: str = "APPLICATION_ADMINISTRATIVE_RECOVERY",
    ) -> dict[str, Any]:
        """Record a non-editorial recovery closure without deleting episode evidence."""
        if not str(reason).strip() or not str(actor).strip() or not str(source).strip():
            raise StorageError("ADMINISTRATIVE_RECOVERY_METADATA_REQUIRED: reason, actor y source son obligatorios")
        if "PLAN010" in str(source).upper():
            raise StorageError("ADMINISTRATIVE_RECOVERY_SOURCE_MUST_BE_NEUTRAL")
        with self._index_lock():
            index = self._load_index()
            episodes = list(index.get("episodes", []))
            entry = next((item for item in episodes if item.get("ep_id") == episode_id), None)
            if entry is None:
                raise StorageError(f"No existe el episodio {episode_id} en el índice.")
            folder = self._folder_for_entry(entry)

            def materialize(closure: dict[str, Any]) -> None:
                if not folder.is_dir():
                    return
                closure_path = folder / self.ADMINISTRATIVE_CLOSURE_FILENAME
                if not closure_path.is_file():
                    _write_json_atomic(closure_path, closure)
                prior_state = closure.get("prior_episode_state")
                state_path = folder / "episode_state.json"
                if isinstance(prior_state, dict) and state_path.is_file():
                    current_state = _read_json(state_path)
                    if current_state.get("status") != self.ADMINISTRATIVE_CLOSED_STATE:
                        updated_state = dict(prior_state)
                        updated_state.update(
                            {
                                "status": self.ADMINISTRATIVE_CLOSED_STATE,
                                "administrative_closure_ref": self.ADMINISTRATIVE_CLOSURE_FILENAME,
                                "updated_at": closure["closed_at"],
                            }
                        )
                        _write_json_atomic(state_path, updated_state)

            def index_with_closure(current_index: dict[str, Any], closure: dict[str, Any]) -> dict[str, Any]:
                updated_episodes = []
                current_entries = list(current_index.get("episodes", []))
                for candidate in current_entries:
                    if candidate.get("ep_id") != episode_id:
                        updated_episodes.append(candidate)
                        continue
                    updated = dict(candidate)
                    updated.update(
                        {
                            "estado": self.ADMINISTRATIVE_CLOSED_INDEX_STATUS,
                            "application_status": self.ADMINISTRATIVE_CLOSED_STATE,
                            "cerrado": closure["closed_at"],
                            "administrative_closure_ref": (
                                self.ADMINISTRATIVE_CLOSURE_FILENAME if folder.is_dir() else "index:administrative_closure"
                            ),
                            # The index is the recovery journal. The folder record is a durable evidence copy.
                            "administrative_closure": closure,
                        }
                    )
                    updated_episodes.append(updated)
                new_index = dict(current_index)
                new_index["episodes"] = updated_episodes
                new_index["last_updated"] = closure["closed_at"]
                return new_index

            if entry.get("estado") == self.ADMINISTRATIVE_CLOSED_INDEX_STATUS:
                closure_path = folder / self.ADMINISTRATIVE_CLOSURE_FILENAME
                if closure_path.is_file():
                    closure = _read_json(closure_path)
                else:
                    closure = entry.get("administrative_closure")
                    if not isinstance(closure, dict):
                        raise StorageError("ADMINISTRATIVE_RECOVERY_RECORD_MISSING: cierre marcado sin evidencia")
                materialize(closure)
                return closure
            if entry.get("estado") != "en_progreso":
                raise StorageError(f"EPISODE_NOT_IN_PROGRESS: estado actual {entry.get('estado')}")

            closure_path = folder / self.ADMINISTRATIVE_CLOSURE_FILENAME
            if closure_path.exists():
                closure = _read_json(closure_path)
                if closure.get("operation") != "ADMINISTRATIVE_RECOVERY_CLOSE" or closure.get("episode_id") != episode_id:
                    raise StorageError("ADMINISTRATIVE_RECOVERY_RECORD_CONFLICT: evidencia de otro cierre")
                _write_json_atomic(self.index_path, index_with_closure(index, closure))
                materialize(closure)
                return closure

            basis, basis_artifacts, prior_state = self._irrecoverability_basis(folder)
            closed_at = datetime.now(timezone.utc).isoformat()
            closure = {
                "operation": "ADMINISTRATIVE_RECOVERY_CLOSE",
                "version": "1.0.0",
                "episode_id": episode_id,
                "previous_index_status": entry.get("estado"),
                "previous_application_status": entry.get("application_status"),
                "reason": str(reason).strip(),
                "actor": str(actor).strip(),
                "source": str(source).strip(),
                "closed_at": closed_at,
                "irrecoverability": {"basis": basis, "artifacts": basis_artifacts},
                "evidence_files": self._evidence_files(folder),
                "prior_index_entry": dict(entry),
                "prior_episode_state": prior_state,
            }
            # Commit the index journal first. Any interruption after this point is
            # converged by the idempotent materialization path above.
            _write_json_atomic(self.index_path, index_with_closure(index, closure))
            materialize(closure)
            return closure

    def resume(self, episode_id: str) -> dict[str, Any]:
        entry = self._entry(episode_id)
        folder = self._folder_for_entry(entry)
        if not folder.is_dir():
            if entry.get("estado") == self.ADMINISTRATIVE_CLOSED_INDEX_STATUS:
                return {
                    "entry": entry,
                    "state": entry.get("administrative_closure", {}),
                    "folder": "",
                }
            raise StorageError(f"El episodio {episode_id} no tiene una carpeta persistida.")
        state = _read_json(folder / "episode_state.json")
        return {"entry": entry, "state": state, "folder": str(folder)}

    def _episode_file(self, episode_id: str, filename: str) -> Path:
        episode = self.resume(episode_id)
        return Path(episode["folder"]) / filename

    def record_decision_request(self, episode_id: str, request: dict[str, Any]) -> dict[str, Any]:
        """Persist the immutable request before any interaction adapter sees it."""
        with self._index_lock():
            request_path = self._episode_file(episode_id, "human_decision_requests.json")
            current = _read_json(request_path, {"requests": []})
            requests = list(current.get("requests", []))
            if request.get("episode_id") not in (None, episode_id):
                raise StorageError("El request no pertenece al episodio indicado.")
            request = {**request, "episode_id": episode_id}
            import hashlib

            computed_checksum = hashlib.sha256(
                json.dumps(
                    {key: value for key, value in request.items() if key not in {"status", "request_checksum"}},
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest()
            if request.get("request_checksum") not in (None, computed_checksum):
                raise StorageError("El request no coincide con su checksum.")
            request_checksum = computed_checksum
            request["request_checksum"] = request_checksum
            existing = next((item for item in requests if item.get("request_id") == request.get("request_id")), None)
            if existing:
                if existing.get("request_checksum") != request_checksum:
                    raise StorageError("El request_id ya existe con otro contenido.")
                return existing
            request["status"] = request.get("status", "PENDING")
            requests.append(request)
            _write_json_atomic(request_path, {"requests": requests})
            return request

    def interaction_record(self, episode_id: str, request_id: str) -> dict[str, Any]:
        request_path = self._episode_file(episode_id, "human_decision_requests.json")
        requests = _read_json(request_path, {"requests": []}).get("requests", [])
        request = next((item for item in requests if item.get("request_id") == request_id), None)
        if request is None:
            raise StorageError(f"No existe el request {request_id}.")
        decision_path = self._episode_file(episode_id, "human_decisions.json")
        decisions = _read_json(decision_path, {"decisions": []}).get("decisions", [])
        decision = next((item for item in decisions if item.get("request_id") == request_id), None)
        orphaned_decision = next(
            (
                item
                for item in decisions
                if item.get("episode_id") == episode_id
                and item.get("request_checksum") == request.get("request_checksum")
                and item.get("request_id") != request_id
            ),
            None,
        )
        transition_path = self._episode_file(episode_id, "workflow_transitions.json")
        transitions = _read_json(transition_path, {"transitions": []}).get("transitions", [])
        transition = next((item for item in transitions if item.get("request_id") == request_id), None)
        return {
            "request": request,
            "decision": decision,
            "decision_error": orphaned_decision,
            "transition": transition,
        }

    def record_workflow(self, handle: EpisodeHandle, workflow: dict[str, Any]) -> None:
        with self._index_lock():
            workflow_path = handle.folder / "workflow_state.json"
            state_path = handle.folder / "episode_state.json"
            prior_workflow = _read_json(workflow_path) if workflow_path.exists() else None
            prior_state = _read_json(state_path)
            prior_index = self._load_index()
            try:
                _write_json_atomic(workflow_path, workflow)
                state = dict(prior_state)
                state.update({"status": workflow["status"], "updated_at": datetime.now(timezone.utc).isoformat()})
                _write_json_atomic(state_path, state)
                index = dict(prior_index)
                index["episodes"] = [dict(entry) for entry in prior_index.get("episodes", [])]
                for entry in index["episodes"]:
                    if entry.get("ep_id") == handle.episode_id:
                        entry["application_status"] = workflow["status"]
                        break
                index["last_updated"] = datetime.now(timezone.utc).isoformat()
                _write_json_atomic(self.index_path, index)
            except Exception:
                try:
                    if prior_workflow is None:
                        workflow_path.unlink(missing_ok=True)
                    else:
                        _write_json_atomic(workflow_path, prior_workflow)
                    _write_json_atomic(state_path, prior_state)
                    _write_json_atomic(self.index_path, prior_index)
                except Exception:
                    # The original exception remains the public failure signal.
                    pass
                raise

    def record_workflow_transition(self, episode_id: str, transition: dict[str, Any]) -> dict[str, Any]:
        """Append one logical workflow transition and make repeated consumption idempotent."""
        with self._index_lock():
            if not transition.get("transition_id") or not transition.get("request_id"):
                raise StorageError("Una transición requiere transition_id y request_id.")
            record = self.interaction_record(episode_id, transition["request_id"])
            if record["decision"] is None:
                raise StorageError("No se puede consumir un request sin respuesta persistida.")
            path = self._episode_file(episode_id, "workflow_transitions.json")
            current = _read_json(path, {"transitions": []})
            transitions = list(current.get("transitions", []))
            existing_request_transition = next(
                (item for item in transitions if item.get("request_id") == transition["request_id"]),
                None,
            )
            if existing_request_transition:
                if existing_request_transition.get("transition_id") != transition["transition_id"]:
                    raise StorageError("El request_id ya tiene una transición consumida.")
                return existing_request_transition
            existing = next((item for item in transitions if item.get("transition_id") == transition["transition_id"]), None)
            if existing:
                if existing.get("request_id") != transition["request_id"]:
                    raise StorageError("transition_id ya está ligado a otro request.")
                return existing
            transitions.append(transition)
            _write_json_atomic(path, {"transitions": transitions})
            self._set_request_status_locked(episode_id, transition["request_id"], transition.get("status", "RESOLVED"))
            return transition

    def _set_request_status_locked(self, episode_id: str, request_id: str, status: str) -> None:
        path = self._episode_file(episode_id, "human_decision_requests.json")
        current = _read_json(path, {"requests": []})
        changed = False
        for request in current.get("requests", []):
            if request.get("request_id") == request_id:
                request["status"] = status
                request["status_updated_at"] = datetime.now(timezone.utc).isoformat()
                changed = True
        if changed:
            _write_json_atomic(path, current)

    def set_request_status(self, episode_id: str, request_id: str, status: str) -> None:
        with self._index_lock():
            self._set_request_status_locked(episode_id, request_id, status)

    def record_decision(self, episode_id: str, decision: dict[str, Any]) -> None:
        with self._index_lock():
            record = self.interaction_record(episode_id, decision.get("request_id", ""))
            request = record["request"]
            request_model = HumanDecisionRequest.from_dict(request, require_contract=True)
            decision_model = HumanDecision.from_dict(decision, require_bound_metadata=True)
            validate_human_decision(request_model, decision_model, episode_id, require_bound_metadata=True)
            if request.get("request_checksum") != decision.get("request_checksum"):
                raise StorageError("La respuesta no corresponde al checksum del request persistido.")
            path = self._episode_file(episode_id, "human_decisions.json")
            current = _read_json(path, {"decisions": []})
            decisions = list(current.get("decisions", []))
            existing = next((item for item in decisions if item.get("request_id") == decision.get("request_id")), None)
            if existing:
                if existing != decision:
                    raise StorageError(f"La decisión {decision.get('request_id')} ya está registrada con otro contenido.")
                return
            decisions.append(decision)
            _write_json_atomic(path, {"decisions": decisions})
            self._set_request_status_locked(episode_id, decision["request_id"], "RESPONSE_RECORDED")
