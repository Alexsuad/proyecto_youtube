"""Explicit transformation from human input to existing editorial contracts."""

from __future__ import annotations

from typing import Any

from src.application.contracts import EntryMode, HumanInput


def build_editorial_handoff(human_input: HumanInput, profile: dict[str, Any]) -> dict[str, Any]:
    """Create a pending handoff without fabricating editorial judgments.

    ``topic_belonging_input`` remains the next canonical editorial contract. The
    application layer only binds facts supplied by the user; Channel Intelligence
    must provide the missing editorial fields before that contract is consumable.
    """
    bindings: dict[str, Any] = {
        "topic": human_input.content if human_input.mode is EntryMode.TOPIC_FIRST else None,
        "narrative_work": human_input.content if human_input.mode is EntryMode.ANCHOR_WORK_FIRST else None,
        "corpus_ref": f"human-input:{human_input.interaction_id}" if human_input.mode is EntryMode.CORPUS_FIRST else None,
        "central_question": human_input.initial_question,
        "initial_question": human_input.initial_question,
        "context": human_input.context,
        "candidate_work_refs": list(human_input.works),
        "user_instructions": [item.to_dict() for item in human_input.user_instructions],
        "duration_target_minutes": human_input.duration_target_minutes,
        "target_language": human_input.target_language,
    }
    unresolved = [
        "central_question",
        "proposed_angle",
        "proposed_territory",
        "initial_evidence",
        "strategic_triggers",
    ]
    if human_input.mode is not EntryMode.TOPIC_FIRST:
        unresolved.insert(0, "topic")
    if human_input.initial_question:
        unresolved.remove("central_question")
    return {
        "contract": "editorial_intake_handoff",
        "contract_version": "1.0.0",
        "target_contract": "topic_belonging_input",
        "status": "AWAITING_EDITORIAL_ENRICHMENT",
        "source_interaction_id": human_input.interaction_id,
        "source_channel": human_input.channel,
        "entry_mode": human_input.mode.value,
        "field_bindings": bindings,
        "unresolved_fields": unresolved,
        "profile_binding": {
            "profile_id": profile["ACTIVE_PROFILE_ID"],
            "profile_version": profile["ACTIVE_PROFILE_VERSION"],
            "profile_checksum": profile["profile_checksum"],
        },
        "provenance": {
            "source_ref": f"human-input:{human_input.interaction_id}",
            "transformation": "BIND_USER_FIELDS_ONLY",
            "editorial_decisions_made": False,
        },
    }
