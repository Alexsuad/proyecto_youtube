"""Channel-neutral contracts for the first product interaction."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4


class EntryMode(StrEnum):
    TOPIC_FIRST = "TOPIC_FIRST"
    ANCHOR_WORK_FIRST = "ANCHOR_WORK_FIRST"
    CORPUS_FIRST = "CORPUS_FIRST"


class InputValidationError(ValueError):
    """Raised when a human intake cannot become a valid canonical input."""


PROCESSING_STATUSES = frozenset({"RECEIVED", "REGISTERED", "READY", "CANCELLED"})


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_entry_mode(value: EntryMode | str) -> EntryMode:
    aliases = {
        "tema": EntryMode.TOPIC_FIRST,
        "topic": EntryMode.TOPIC_FIRST,
        "topic_first": EntryMode.TOPIC_FIRST,
        "obra": EntryMode.ANCHOR_WORK_FIRST,
        "anchor_work_first": EntryMode.ANCHOR_WORK_FIRST,
        "corpus": EntryMode.CORPUS_FIRST,
        "corpus_first": EntryMode.CORPUS_FIRST,
    }
    if isinstance(value, EntryMode):
        return value
    normalized = str(value).strip().lower()
    try:
        if normalized in aliases:
            return aliases[normalized]
        return EntryMode(str(value).strip().upper())
    except ValueError as exc:
        raise InputValidationError(
            "Modalidad inválida. Usa tema, obra o corpus."
        ) from exc


@dataclass(frozen=True)
class HumanInput:
    """The smallest durable representation of what a user actually supplied."""

    interaction_id: str
    occurred_at: str
    channel: str
    mode: EntryMode
    content: str
    initial_question: str | None = None
    context: str | None = None
    works: tuple[str, ...] = ()
    actor_ref: str = "local-user"
    provenance: dict[str, Any] = field(default_factory=dict)
    processing_status: str = "RECEIVED"

    def __post_init__(self) -> None:
        if self.processing_status not in PROCESSING_STATUSES:
            raise InputValidationError("Estado de procesamiento inválido.")

    @classmethod
    def create(
        cls,
        *,
        mode: EntryMode | str,
        content: str = "",
        initial_question: str | None = None,
        context: str | None = None,
        works: list[str] | tuple[str, ...] | None = None,
        channel: str = "TERMINAL",
        actor_ref: str = "local-user",
        interaction_id: str | None = None,
        occurred_at: str | None = None,
        provenance: dict[str, Any] | None = None,
        processing_status: str = "RECEIVED",
    ) -> "HumanInput":
        selected_mode = normalize_entry_mode(mode)
        clean_content = str(content or "").strip()
        clean_question = str(initial_question).strip() if initial_question and str(initial_question).strip() else None
        clean_context = str(context).strip() if context and str(context).strip() else None
        if works is not None and (
            isinstance(works, str)
            or not isinstance(works, (list, tuple))
            or any(not isinstance(item, str) for item in works)
        ):
            raise InputValidationError("Cada obra debe ser texto.")
        clean_works = tuple(item.strip() for item in (works or ()) if item.strip())
        if len(clean_works) != len(set(clean_works)):
            raise InputValidationError("El corpus no puede repetir obras.")
        if selected_mode in (EntryMode.TOPIC_FIRST, EntryMode.ANCHOR_WORK_FIRST) and not clean_content:
            raise InputValidationError("El contenido principal no puede estar vacío.")
        if selected_mode is EntryMode.CORPUS_FIRST and not clean_works:
            raise InputValidationError("El corpus debe contener al menos una obra.")
        if selected_mode is EntryMode.ANCHOR_WORK_FIRST and clean_works and clean_works != (clean_content,):
            raise InputValidationError("Una entrada de obra debe tener una única obra ancla.")
        if selected_mode is EntryMode.ANCHOR_WORK_FIRST:
            clean_works = (clean_content,)
        if not str(channel).strip():
            raise InputValidationError("El canal de origen es obligatorio.")
        if not str(actor_ref).strip():
            raise InputValidationError("La referencia del usuario es obligatoria.")
        return cls(
            interaction_id=interaction_id or f"INT-{uuid4().hex}",
            occurred_at=occurred_at or utc_now(),
            channel=str(channel).strip().upper(),
            mode=selected_mode,
            content=clean_content,
            initial_question=clean_question,
            context=clean_context,
            works=clean_works,
            actor_ref=str(actor_ref).strip(),
            provenance=dict(provenance or {"capture_method": "TEXT", "source": "USER"}),
            processing_status=processing_status,
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HumanInput":
        return cls.create(
            mode=data.get("mode", ""),
            content=data.get("content", ""),
            initial_question=data.get("initial_question"),
            context=data.get("context"),
            works=data.get("works", []),
            channel=data.get("channel", ""),
            actor_ref=data.get("actor_ref", ""),
            interaction_id=data.get("interaction_id"),
            occurred_at=data.get("occurred_at"),
            provenance=data.get("provenance"),
            processing_status=data.get("processing_status", "RECEIVED"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract": "human_episode_input",
            "contract_version": "1.0.0",
            "interaction_id": self.interaction_id,
            "occurred_at": self.occurred_at,
            "channel": self.channel,
            "mode": self.mode.value,
            "content": self.content,
            "initial_question": self.initial_question,
            "context": self.context,
            "works": list(self.works),
            "actor_ref": self.actor_ref,
            "provenance": self.provenance,
            "processing_status": self.processing_status,
        }
