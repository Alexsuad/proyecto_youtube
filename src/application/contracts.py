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


class UserInstructionCategory(StrEnum):
    CONTEXT_ONLY = "CONTEXT_ONLY"
    MAY_INCLUDE = "MAY_INCLUDE"
    MUST_INCLUDE = "MUST_INCLUDE"
    MUST_INCLUDE_VERBATIM = "MUST_INCLUDE_VERBATIM"


class InputValidationError(ValueError):
    """Raised when a human intake cannot become a valid canonical input."""


PROCESSING_STATUSES = frozenset({"RECEIVED", "REGISTERED", "READY", "CANCELLED"})
RESEARCH_ROLES = frozenset({"ANCLA", "NORMAL"})
EDITORIAL_INTENTS = frozenset({"NO_DECLARADA", "PREFERIDA", "REQUERIDA"})


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


def normalize_target_language(value: str | None) -> str | None:
    if value is None:
        return None
    clean = str(value).strip()
    if not clean or clean.lower() in {"default", "predeterminado", "automatico", "automático"}:
        return None
    aliases = {
        "español": "es",
        "spanish": "es",
        "inglés": "en",
        "ingles": "en",
        "english": "en",
        "francés": "fr",
        "frances": "fr",
        "french": "fr",
        "portugués": "pt",
        "portugues": "pt",
        "portuguese": "pt",
    }
    return aliases.get(clean.lower(), clean)


@dataclass(frozen=True)
class UserInstruction:
    category: UserInstructionCategory
    text: str

    def __post_init__(self) -> None:
        try:
            category = UserInstructionCategory(str(self.category).strip().upper())
        except ValueError as exc:
            raise InputValidationError("Categoría de indicación inválida.") from exc
        if not isinstance(self.text, str) or not self.text.strip():
            raise InputValidationError("El texto de la indicación no puede estar vacío.")
        object.__setattr__(self, "category", category)

    @classmethod
    def create(cls, *, category: UserInstructionCategory | str, text: str) -> "UserInstruction":
        return cls(category=category, text=text)

    def to_dict(self) -> dict[str, str]:
        return {"category": self.category.value, "text": self.text}


def normalize_user_instructions(
    values: list[UserInstruction | dict[str, Any]] | tuple[UserInstruction | dict[str, Any], ...] | None,
) -> tuple[UserInstruction, ...]:
    if values is None:
        return ()
    if not isinstance(values, (list, tuple)):
        raise InputValidationError("Las indicaciones deben ser una lista.")
    normalized: list[UserInstruction] = []
    for item in values:
        if isinstance(item, UserInstruction):
            normalized.append(item)
        elif isinstance(item, dict):
            normalized.append(UserInstruction.create(category=item.get("category", ""), text=item.get("text", "")))
        else:
            raise InputValidationError("Cada indicación debe tener categoría y texto.")
    return tuple(normalized)


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
    user_instructions: tuple[UserInstruction, ...] = ()
    duration_target_minutes: int | None = None
    target_language: str | None = None
    research_role: str | None = None
    editorial_intent: str | None = None
    actor_ref: str = "local-user"
    provenance: dict[str, Any] = field(default_factory=dict)
    processing_status: str = "RECEIVED"

    def __post_init__(self) -> None:
        if self.processing_status not in PROCESSING_STATUSES:
            raise InputValidationError("Estado de procesamiento inválido.")
        if self.research_role is not None and self.research_role not in RESEARCH_ROLES:
            raise InputValidationError("research_role debe ser ANCLA o NORMAL.")
        if self.editorial_intent is not None and self.editorial_intent not in EDITORIAL_INTENTS:
            raise InputValidationError("editorial_intent no pertenece al vocabulario contractual.")

    @classmethod
    def create(
        cls,
        *,
        mode: EntryMode | str,
        content: str = "",
        initial_question: str | None = None,
        context: str | None = None,
        works: list[str] | tuple[str, ...] | None = None,
        user_instructions: list[UserInstruction | dict[str, Any]] | tuple[UserInstruction | dict[str, Any], ...] | None = None,
        instructions: list[UserInstruction | dict[str, Any]] | tuple[UserInstruction | dict[str, Any], ...] | None = None,
        duration_target_minutes: int | None = None,
        target_language: str | None = None,
        research_role: str | None = None,
        editorial_intent: str | None = None,
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
        if user_instructions is not None and instructions is not None and user_instructions != instructions:
            raise InputValidationError("No se pueden indicar dos listas de indicaciones distintas.")
        clean_instructions = normalize_user_instructions(
            user_instructions if user_instructions is not None else instructions
        )
        if isinstance(duration_target_minutes, bool) or (
            duration_target_minutes is not None
            and (not isinstance(duration_target_minutes, int) or duration_target_minutes <= 0)
        ):
            raise InputValidationError("La duración objetivo debe ser un número entero positivo o null.")
        clean_language = normalize_target_language(target_language)
        clean_research_role = str(research_role).strip().upper() if research_role is not None else None
        clean_editorial_intent = str(editorial_intent).strip().upper() if editorial_intent is not None else None
        if clean_research_role is not None and clean_research_role not in RESEARCH_ROLES:
            raise InputValidationError("research_role debe ser ANCLA o NORMAL.")
        if clean_editorial_intent is not None and clean_editorial_intent not in EDITORIAL_INTENTS:
            raise InputValidationError("editorial_intent no pertenece al vocabulario contractual.")
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
            user_instructions=clean_instructions,
            duration_target_minutes=duration_target_minutes,
            target_language=clean_language,
            research_role=clean_research_role,
            editorial_intent=clean_editorial_intent,
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
            user_instructions=data.get("user_instructions", data.get("instructions", [])),
            duration_target_minutes=data.get("duration_target_minutes"),
            target_language=data.get("target_language"),
            research_role=data.get("research_role"),
            editorial_intent=data.get("editorial_intent"),
            channel=data.get("channel", ""),
            actor_ref=data.get("actor_ref", ""),
            interaction_id=data.get("interaction_id"),
            occurred_at=data.get("occurred_at"),
            provenance=data.get("provenance"),
            processing_status=data.get("processing_status", "RECEIVED"),
        )

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "contract": "human_episode_input",
            "contract_version": "2.0.0" if self.research_role is not None or self.editorial_intent is not None else "1.0.0",
            "interaction_id": self.interaction_id,
            "occurred_at": self.occurred_at,
            "channel": self.channel,
            "mode": self.mode.value,
            "content": self.content,
            "initial_question": self.initial_question,
            "context": self.context,
            "works": list(self.works),
            "user_instructions": [item.to_dict() for item in self.user_instructions],
            "duration_target_minutes": self.duration_target_minutes,
            "target_language": self.target_language,
            "actor_ref": self.actor_ref,
            "provenance": self.provenance,
            "processing_status": self.processing_status,
        }
        if self.research_role is not None:
            payload["research_role"] = self.research_role
        if self.editorial_intent is not None:
            payload["editorial_intent"] = self.editorial_intent
        return payload
