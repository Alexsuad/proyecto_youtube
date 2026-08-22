"""Human interaction port and the Terminal adapter."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Protocol


class UserCancelled(Exception):
    """The user explicitly cancelled an interaction."""


@dataclass(frozen=True)
class HumanDecisionRequest:
    request_id: str
    prompt: str
    options: tuple[dict[str, str], ...] = ()
    recommendation: str | None = None
    episode_id: str | None = None
    subject_ref: str | None = None
    subject_version: str | None = None
    subject_checksum: str | None = None
    workflow_ref: str | None = None
    expected_actor_ref: str | None = None
    expected_channel: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: str = "PENDING"

    def _payload(self) -> dict[str, Any]:
        return {
            "contract": "human_decision_request",
            "contract_version": "1.0.0",
            "request_id": self.request_id,
            "episode_id": self.episode_id,
            "prompt": self.prompt,
            "options": [dict(option) for option in self.options],
            "recommendation": self.recommendation,
            "subject_ref": self.subject_ref,
            "subject_version": self.subject_version,
            "subject_checksum": self.subject_checksum,
            "workflow_ref": self.workflow_ref,
            "expected_actor_ref": self.expected_actor_ref,
            "expected_channel": self.expected_channel,
            "created_at": self.created_at,
            "status": self.status,
        }

    def checksum(self) -> str:
        payload = {key: value for key, value in self._payload().items() if key not in {"status"}}
        return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        payload = self._payload()
        payload["request_checksum"] = self.checksum()
        return payload

    @classmethod
    def from_dict(cls, data: dict[str, Any], *, require_contract: bool = False) -> "HumanDecisionRequest":
        if require_contract and (
            data.get("contract") != "human_decision_request" or data.get("contract_version") != "1.0.0"
        ):
            raise ValueError("La solicitud persistida no tiene un contrato reconocido.")
        return cls(
            request_id=data["request_id"],
            prompt=data["prompt"],
            options=tuple(data.get("options", [])),
            recommendation=data.get("recommendation"),
            episode_id=data.get("episode_id"),
            subject_ref=data.get("subject_ref"),
            subject_version=data.get("subject_version"),
            subject_checksum=data.get("subject_checksum"),
            workflow_ref=data.get("workflow_ref"),
            expected_actor_ref=data.get("expected_actor_ref"),
            expected_channel=data.get("expected_channel"),
            created_at=data.get("created_at") or datetime.now(timezone.utc).isoformat(),
            status=data.get("status", "PENDING"),
        )


DecisionRequest = HumanDecisionRequest


@dataclass(frozen=True)
class HumanDecision:
    request_id: str
    action: str
    selected_option: str | None = None
    correction: str | None = None
    actor_ref: str = "local-user"
    channel: str = "TERMINAL"
    request_snapshot: dict[str, Any] | None = None
    episode_id: str | None = None
    occurred_at: str | None = None
    request_checksum: str | None = None

    def __post_init__(self) -> None:
        if self.action not in {"APPROVE", "SELECT_ALTERNATIVE", "CORRECT", "REJECT", "CANCEL"}:
            raise ValueError(f"Acción de decisión inválida: {self.action}")
        if self.action == "SELECT_ALTERNATIVE" and (
            not isinstance(self.selected_option, str) or not self.selected_option.strip()
        ):
            raise ValueError("Elegir una alternativa requiere selected_option.")
        if self.action == "CORRECT" and (
            not isinstance(self.correction, str) or not self.correction.strip()
        ):
            raise ValueError("Corregir requiere un comentario no vacío.")
        if self.action in {"APPROVE", "REJECT", "CANCEL"} and (
            self.selected_option is not None or self.correction is not None
        ):
            raise ValueError(f"{self.action} no puede incluir selección ni corrección.")
        if self.action == "SELECT_ALTERNATIVE" and self.correction is not None:
            raise ValueError("SELECT_ALTERNATIVE no puede incluir corrección.")
        if self.action == "CORRECT" and self.selected_option is not None:
            raise ValueError("CORRECT no puede incluir selección.")

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "contract": "human_decision",
            "contract_version": "1.0.0",
            "request_id": self.request_id,
            "action": self.action,
            "selected_option": self.selected_option,
            "correction": self.correction,
            "actor_ref": self.actor_ref,
            "channel": self.channel,
            "episode_id": self.episode_id,
            "occurred_at": self.occurred_at,
            "request_checksum": self.request_checksum,
        }
        return payload

    def bind_request(self, request: HumanDecisionRequest) -> "HumanDecision":
        return HumanDecision(
            request_id=self.request_id,
            action=self.action,
            selected_option=self.selected_option,
            correction=self.correction,
            actor_ref=self.actor_ref,
            channel=self.channel,
            request_snapshot=None,
            episode_id=request.episode_id,
            occurred_at=datetime.now(timezone.utc).isoformat(),
            request_checksum=request.checksum(),
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any], *, require_bound_metadata: bool = False) -> "HumanDecision":
        if data.get("contract") != "human_decision" or data.get("contract_version") != "1.0.0":
            raise ValueError("La decisión persistida no tiene un contrato reconocido.")
        if require_bound_metadata:
            allowed = {
                "contract", "contract_version", "request_id", "action", "selected_option",
                "correction", "actor_ref", "channel", "episode_id", "occurred_at",
                "request_checksum",
            }
            if set(data) - allowed:
                raise ValueError("La decisión persistida contiene campos desconocidos.")
            required = {
                "request_id", "action", "selected_option", "correction", "actor_ref",
                "channel", "episode_id", "occurred_at", "request_checksum",
            }
            if not required.issubset(data):
                raise ValueError("La decisión persistida no contiene todos sus campos obligatorios.")
        return cls(
            request_id=data["request_id"],
            action=data["action"],
            selected_option=data.get("selected_option"),
            correction=data.get("correction"),
            actor_ref=data.get("actor_ref", "unknown"),
            channel=data.get("channel", "UNKNOWN"),
            episode_id=data.get("episode_id"),
            occurred_at=data.get("occurred_at"),
            request_checksum=data.get("request_checksum"),
        )


def validate_human_decision(
    request: HumanDecisionRequest,
    decision: HumanDecision,
    episode_id: str,
    *,
    require_bound_metadata: bool = False,
) -> None:
    """Apply the same technical request/response invariants at every boundary."""
    if request.episode_id != episode_id or decision.episode_id not in (None, episode_id):
        raise ValueError("La decisión no corresponde al episodio indicado.")
    if decision.request_id != request.request_id:
        raise ValueError("La decisión no corresponde al request indicado.")
    if require_bound_metadata and decision.episode_id is None:
        raise ValueError("La decisión persistida no tiene episode_id.")
    if require_bound_metadata and decision.request_checksum is None:
        raise ValueError("La decisión persistida no tiene request_checksum.")
    if require_bound_metadata:
        if not isinstance(decision.occurred_at, str) or not decision.occurred_at:
            raise ValueError("La decisión persistida no tiene occurred_at.")
        try:
            occurred_at = datetime.fromisoformat(decision.occurred_at.replace("Z", "+00:00"))
        except (AttributeError, ValueError) as exc:
            raise ValueError("La decisión persistida tiene occurred_at inválido.") from exc
        if "T" not in decision.occurred_at or occurred_at.tzinfo is None:
            raise ValueError("La decisión persistida tiene occurred_at inválido.")
    if decision.request_checksum not in (None, request.checksum()):
        raise ValueError("La decisión no corresponde al checksum del request.")
    if not isinstance(decision.actor_ref, str) or not decision.actor_ref.strip():
        raise ValueError("La decisión requiere actor_ref.")
    if not isinstance(decision.channel, str) or not decision.channel.strip():
        raise ValueError("La decisión requiere channel.")
    if request.expected_actor_ref is not None and decision.actor_ref != request.expected_actor_ref:
        raise PermissionError("El actor de la decisión no coincide con el actor esperado.")
    if request.expected_channel is not None and decision.channel != request.expected_channel:
        raise PermissionError("El canal de la decisión no coincide con el canal esperado.")
    if decision.action in {"APPROVE", "REJECT", "CANCEL"} and (
        decision.selected_option is not None or decision.correction is not None
    ):
        raise ValueError("La respuesta contiene campos incompatibles con su acción.")
    if decision.action == "CORRECT" and not isinstance(decision.correction, str):
        raise ValueError("La corrección debe ser texto.")
    if decision.action == "SELECT_ALTERNATIVE" and not isinstance(decision.selected_option, str):
        raise ValueError("La alternativa elegida debe ser texto.")
    if decision.action == "SELECT_ALTERNATIVE" and decision.correction is not None:
        raise ValueError("SELECT_ALTERNATIVE no puede incluir corrección.")
    if decision.action == "CORRECT" and decision.selected_option is not None:
        raise ValueError("CORRECT no puede incluir selección.")
    option_ids = {option.get("id") for option in request.options}
    if decision.action == "SELECT_ALTERNATIVE" and decision.selected_option not in option_ids:
        raise ValueError("La alternativa elegida no pertenece al request.")


class HumanInteraction(Protocol):
    channel: str

    def present(self, message: str) -> None: ...
    def free_text(self, prompt: str, *, optional: bool = False) -> str | None: ...
    def choose(self, prompt: str, options: list[tuple[str, str]]) -> str: ...
    def confirm(self, prompt: str) -> bool: ...
    def decide(self, request: HumanDecisionRequest) -> HumanDecision: ...


class TerminalInteraction:
    channel = "TERMINAL"

    def present(self, message: str) -> None:
        print(message)

    def free_text(self, prompt: str, *, optional: bool = False) -> str | None:
        suffix = " [opcional]" if optional else ""
        try:
            value = input(f"{prompt}{suffix}\n> ").strip()
        except (EOFError, KeyboardInterrupt) as exc:
            raise UserCancelled from exc
        if not value and optional:
            return None
        if not value:
            raise ValueError("La respuesta no puede estar vacía.")
        return value

    def choose(self, prompt: str, options: list[tuple[str, str]]) -> str:
        self.present(prompt)
        for index, (_, label) in enumerate(options, start=1):
            print(f"{index}. {label}")
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt) as exc:
            raise UserCancelled from exc
        try:
            selected = options[int(raw) - 1][0]
        except (ValueError, IndexError) as exc:
            raise ValueError("Selecciona una opción válida usando su número.") from exc
        return selected

    def confirm(self, prompt: str) -> bool:
        while True:
            try:
                raw = input(f"{prompt} [S/n]\n> ").strip().lower()
            except (EOFError, KeyboardInterrupt) as exc:
                raise UserCancelled from exc
            if raw in {"", "s", "si", "sí", "y", "yes"}:
                return True
            if raw in {"n", "no"}:
                return False
            self.present("Respuesta inválida. Escribe S o N.")

    def decide(self, request: HumanDecisionRequest) -> HumanDecision:
        self.present(request.prompt)
        for index, option in enumerate(request.options, start=1):
            print(f"{index}. {option['label']}")
        if request.recommendation:
            print(f"Recomendación: {request.recommendation}")
        print("\n¿Qué deseas hacer?\n[A] Aprobar\n[E] Elegir otra opción\n[C] Corregir / añadir instrucciones\n[R] Rechazar")
        try:
            raw = input("> ").strip().upper()
        except (EOFError, KeyboardInterrupt) as exc:
            raise UserCancelled from exc
        if raw == "A":
            return HumanDecision(request.request_id, "APPROVE", actor_ref="local-user")
        if raw == "E":
            selected = self.choose("Elige una alternativa:", [(item["id"], item["label"]) for item in request.options])
            return HumanDecision(request.request_id, "SELECT_ALTERNATIVE", selected_option=selected)
        if raw == "C":
            correction = self.free_text("Escribe la corrección o instrucción:")
            return HumanDecision(request.request_id, "CORRECT", correction=correction)
        if raw == "R":
            return HumanDecision(request.request_id, "REJECT")
        raise ValueError("Respuesta inválida. Usa A, E, C o R.")
