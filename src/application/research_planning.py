"""Deterministic PRE_RESEARCH context and ResearchPlan binding helpers."""

from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from src.core.contract_validation import validate_against_schema, validate_research_plan
from src.core.editorial_profile_registry import load_active_profile_authority
from src.core.path_resolution import REPO_ROOT


class ResearchPlanningError(ValueError):
    """A PRE_RESEARCH contract or binding cannot be accepted."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _checksum(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _pick(value: Mapping[str, Any], fields: tuple[str, ...]) -> dict[str, Any]:
    return {field: copy.deepcopy(value[field]) for field in fields if field in value}


def _bound_claim(value: Any, index: int, evidence_ref: str) -> dict[str, Any]:
    if isinstance(value, Mapping):
        result = _pick(value, ("claim_id", "statement", "intended_use", "strength", "evidence_requirement_refs", "material_if_false", "claim_dimensions"))
        result.setdefault("claim_id", f"C-{index}")
        result.setdefault("statement", str(value.get("statement") or value.get("claim_text") or f"Claim {index}."))
        result.setdefault("intended_use", "RESEARCH")
        result.setdefault("strength", "LIMITED")
        result.setdefault("evidence_requirement_refs", [evidence_ref])
        result.setdefault("material_if_false", True)
        return result
    return {"claim_id": f"C-{index}", "statement": str(value), "intended_use": "RESEARCH", "strength": "LIMITED", "evidence_requirement_refs": [evidence_ref], "material_if_false": True}


def _bound_rival(value: Any, index: int, evidence_ref: str) -> dict[str, Any]:
    if isinstance(value, Mapping):
        result = _pick(value, ("rival_id", "explanation", "refutation_signals", "evidence_requirement_refs"))
        result.setdefault("rival_id", f"R-{index}")
        result.setdefault("explanation", str(value.get("explanation") or value.get("statement") or f"Explicación rival {index}."))
        result.setdefault("refutation_signals", ["Evidencia contradictoria"])
        result.setdefault("evidence_requirement_refs", [evidence_ref])
        return result
    return {"rival_id": f"R-{index}", "explanation": str(value), "refutation_signals": ["Evidencia contradictoria"], "evidence_requirement_refs": [evidence_ref]}


def _bound_gap(value: Any, index: int) -> dict[str, Any]:
    if isinstance(value, Mapping):
        result = _pick(value, ("gap_id", "kind", "description", "material_impact", "mitigation"))
        result.setdefault("gap_id", f"G-{index}")
        result.setdefault("kind", "EVIDENCE")
        result.setdefault("description", str(value.get("description") or f"Brecha {index}."))
        result.setdefault("material_impact", "PENDING")
        result.setdefault("mitigation", "Revisar antes de declarar suficiencia.")
        return result
    return {"gap_id": f"G-{index}", "kind": "EVIDENCE", "description": str(value), "material_impact": "PENDING", "mitigation": "Revisar antes de declarar suficiencia."}


def _bound_specialist(value: Any, index: int) -> dict[str, Any]:
    if isinstance(value, Mapping):
        result = _pick(value, ("specialist_id", "field", "activation_condition", "expected_contribution"))
        result.setdefault("specialist_id", f"SP-{index}")
        result.setdefault("field", str(value.get("field") or "GENERAL"))
        result.setdefault("activation_condition", "Si aparece una brecha material.")
        result.setdefault("expected_contribution", "Aportar contraste especializado.")
        return result
    return {"specialist_id": f"SP-{index}", "field": str(value), "activation_condition": "Si aparece una brecha material.", "expected_contribution": "Aportar contraste especializado."}


class ResearchPlanningService:
    """Build the software-owned research context and bind a cognitive proposal."""

    STANDARD_INTENDED_USE = "RESEARCH_AND_THESIS"

    @classmethod
    def resolve_intended_use(
        cls,
        *,
        explicit: Any = None,
        topic: Any = None,
        question: Any = None,
        reference: str = "human_episode_input",
    ) -> dict[str, str]:
        """Resolve purpose once, preserving whether it was supplied or derived.

        A normal topic/question is sufficient for the standard Research V2
        route.  Explicit purpose always wins; an empty explicit value is not
        treated as a negative assertion and therefore does not create a false
        ambiguity block.
        """
        value = str(explicit or "").strip()
        if value:
            return {"value": value, "origin": "OWNER_EXPLICIT", "reference": reference}
        if str(topic or "").strip() or str(question or "").strip():
            return {"value": cls.STANDARD_INTENDED_USE, "origin": "DERIVED_STANDARD", "reference": reference}
        raise ResearchPlanningError("RESEARCH_INTENDED_USE_AMBIGUOUS")

    def build_episode_brief(
        self,
        *,
        episode_id: str,
        topic: str,
        question: str | None,
        intended_use: str | None,
        profile: Mapping[str, Any],
        work_intents: list[Mapping[str, Any]] | None = None,
        selection_authority: str = "NOT_DECLARED",
        material_refs: list[str] | None = None,
        owner_restrictions: list[str] | None = None,
        brief_version: str = "2.0.0",
        origin_ref: str = "human_episode_input",
    ) -> dict[str, Any]:
        """Create the minimal PRE_RESEARCH brief from already supplied input.

        This is a deterministic preparation step: it records only information
        available before research and never invents a thesis or evidence.
        """
        if not str(episode_id).strip() or not str(topic).strip():
            raise ResearchPlanningError("PRE_RESEARCH_BRIEF_INPUT_REQUIRED")
        intended_use_resolution = self.resolve_intended_use(
            explicit=intended_use, topic=topic, question=question, reference=origin_ref,
        )
        if not isinstance(profile, Mapping):
            raise ResearchPlanningError("EDITORIAL_PROFILE_REQUIRED")
        profile_data = dict(profile.get("profile", profile)) if isinstance(profile.get("profile", profile), Mapping) else {}
        identity = profile_data.get("identity_stable", {})
        profile_id = str(profile_data.get("profile_id") or profile.get("ACTIVE_PROFILE_ID") or "")
        profile_version = str(profile_data.get("version") or profile.get("ACTIVE_PROFILE_VERSION") or "")
        profile_checksum = str(profile_data.get("checksum") or profile.get("profile_checksum") or "")
        if not profile_id or not profile_version or len(profile_checksum) != 64:
            raise ResearchPlanningError("EDITORIAL_PROFILE_BINDING_INVALID")
        intents = [dict(item) for item in (work_intents or [])]
        refs = [str(item) for item in (material_refs or [])]
        authority = str(selection_authority or "NOT_DECLARED").strip().upper()
        if authority not in {"NOT_DECLARED", "OWNER_DECIDES", "DELEGATED_TO_RESEARCH"}:
            raise ResearchPlanningError("SELECTION_AUTHORITY_INVALID")
        brief = {
            "episode_id": str(episode_id), "brief_version": brief_version, "brief_stage": "PRE_RESEARCH",
            "profile_id": profile_id, "profile_version": profile_version, "profile_checksum": profile_checksum,
            "tema": str(topic).strip(), "initial_question": str(question).strip() if question else None,
            "objetivo": intended_use_resolution["value"],
            "intended_use_resolution": intended_use_resolution,
            "narrative_materials": [str(item.get("work_ref")) for item in intents if item.get("work_ref")],
            "work_intents": intents, "selection_authority": authority,
            "owner_material_refs": refs, "owner_restrictions": [str(item) for item in (owner_restrictions or [])],
            "created_at": _now(),
        }
        errors = validate_against_schema(brief, "episode_brief")
        if errors:
            raise ResearchPlanningError("PRE_RESEARCH_BRIEF_INVALID: " + " | ".join(errors))
        return brief

    def build_channel_context(self, *, episode_id: str, profile: Mapping[str, Any], origin_ref: str) -> dict[str, Any]:
        profile_data = dict(profile)
        pointer_fields = (
            profile_data.get("ACTIVE_PROFILE_ID"),
            profile_data.get("ACTIVE_PROFILE_VERSION"),
            profile_data.get("profile_checksum"),
        )
        if any(pointer_fields):
            try:
                canonical = load_active_profile_authority()
            except (OSError, ValueError) as exc:
                raise ResearchPlanningError("EDITORIAL_PROFILE_AUTHORITY_INVALID") from exc
            if pointer_fields != (
                canonical.get("ACTIVE_PROFILE_ID"),
                canonical.get("ACTIVE_PROFILE_VERSION"),
                canonical.get("profile_checksum"),
            ):
                raise ResearchPlanningError("EDITORIAL_PROFILE_BINDING_MISMATCH")
        if isinstance(profile_data.get("profile"), Mapping):
            nested = dict(profile_data["profile"])
            nested.setdefault("checksum", profile_data.get("checksum"))
            profile_data = nested
        elif profile_data.get("ACTIVE_PROFILE_ID"):
            registry_path = REPO_ROOT / "config" / "editorial_profile_registry.json"
            try:
                registry = json.loads(registry_path.read_text(encoding="utf-8"))
                key = f"{profile_data['ACTIVE_PROFILE_ID']}@{profile_data['ACTIVE_PROFILE_VERSION']}"
                entry = registry.get("profiles", {}).get(key, {})
                profile_data = dict(entry.get("profile", {}))
                profile_data.setdefault("checksum", profile.get("profile_checksum"))
                profile_data.setdefault("profile_id", profile.get("ACTIVE_PROFILE_ID"))
                profile_data.setdefault("version", profile.get("ACTIVE_PROFILE_VERSION"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError, AttributeError):
                raise ResearchPlanningError("EDITORIAL_PROFILE_REGISTRY_UNAVAILABLE")
        identity = profile_data.get("identity_stable", {})
        audience_hypotheses = profile_data.get("audience_hypotheses") or identity.get("audience_hypotheses") or []
        territories = profile_data.get("territories") or identity.get("territories") or []
        context = {
            "contract": "research_channel_context",
            "contract_version": "1.0.0",
            "context_id": f"{episode_id}:CHANNEL_CONTEXT",
            "episode_id": episode_id,
            "profile_id": str(profile_data.get("profile_id") or ""),
            "profile_version": str(profile_data.get("version") or ""),
            "profile_checksum": str(profile_data.get("checksum") or ""),
            "editorial_identity": str(identity.get("identity") or ""),
            "editorial_purpose": str(profile_data.get("editorial_purpose") or identity.get("editorial_purpose") or ""),
            "primary_promise": str(profile_data.get("primary_promise") or identity.get("primary_promise") or ""),
            "audience_context": json.dumps(audience_hypotheses, ensure_ascii=False),
            "territories": [str(item.get("name")) for item in territories if isinstance(item, Mapping) and item.get("classification") == "ACTIVE"],
            "research_relevant_limits": [str(item) for item in (profile_data.get("permanent_limits") or identity.get("permanent_limits") or [])],
            "origin_ref": origin_ref,
            "created_at": _now(),
        }
        errors = validate_against_schema(context, "research_channel_context")
        if errors:
            raise ResearchPlanningError("RESEARCH_CHANNEL_CONTEXT_INVALID: " + " | ".join(errors))
        return context

    def build_source_access(self, *, episode_id: str, brief_version: str, materials: list[Mapping[str, Any]], origin_refs: list[str]) -> dict[str, Any]:
        access = {
            "contract": "research_source_access",
            "contract_version": "1.0.0",
            "access_id": f"{episode_id}:SOURCE_ACCESS",
            "episode_id": episode_id,
            "brief_version": brief_version,
            "capabilities": {"owner_material_ingestion": "AVAILABLE", "web_search": "UNAVAILABLE", "http_fetch": "UNAVAILABLE"},
            "materials": [dict(item) for item in materials],
            "unavailable_source_types": ["WEB_SEARCH", "HTTP_FETCH"],
            "limitations": ["Solo se aceptan materiales locales previamente verificados."],
            "origin_artifact_refs": list(origin_refs),
            "created_at": _now(),
        }
        errors = validate_against_schema(access, "research_source_access")
        if errors:
            raise ResearchPlanningError("RESEARCH_SOURCE_ACCESS_INVALID: " + " | ".join(errors))
        return access

    def bind_research_plan(self, proposal: Mapping[str, Any], *, episode_id: str, brief_version: str, research_role: str, editorial_intent: str, origin_ref: str) -> dict[str, Any]:
        if not isinstance(proposal, Mapping):
            raise ResearchPlanningError("RESEARCH_PLAN_PROPOSAL_REQUIRED")
        proposal_errors = validate_against_schema(dict(proposal), "research_plan_proposal")
        if proposal_errors:
            raise ResearchPlanningError("RESEARCH_PLAN_PROPOSAL_INVALID: " + " | ".join(proposal_errors))
        raw = copy.deepcopy(dict(proposal))
        # The cognitive proposal is intentionally lightweight; Software owns
        # the canonical ResearchPlan 2.0.0 shape and adds stable identifiers.
        dimension_items = raw.get("dimensions") or ["primary"]
        dimensions = [copy.deepcopy(dict(item)) if isinstance(item, Mapping) else {"dimension_id": f"D-{index}", "label": str(item), "research_question": str(item)} for index, item in enumerate(dimension_items, 1)]
        for index, item in enumerate(dimensions, 1):
            item.setdefault("dimension_id", f"D-{index}"); item.setdefault("label", str(item.get("dimension_id"))); item.setdefault("research_question", str(item.get("label")))
        sub_items = raw.get("subquestions") or ["Delimitar el fenómeno."]
        subquestions = [copy.deepcopy(dict(item)) if isinstance(item, Mapping) else {"subquestion_id": f"SQ-{index}", "dimension_id": dimensions[0]["dimension_id"], "question": str(item)} for index, item in enumerate(sub_items, 1)]
        evidence_items = raw.get("evidence_requirements") or ["Evidencia verificable."]
        evidence = [copy.deepcopy(dict(item)) if isinstance(item, Mapping) else {"evidence_requirement_id": f"E-{index}", "subquestion_refs": [subquestions[0]["subquestion_id"]], "evidence_kind": "BOTH", "minimum_strength": str(item), "preferred_source_types": ["OWNER_MATERIAL"]} for index, item in enumerate(evidence_items, 1)]
        for index, item in enumerate(subquestions, 1):
            item.setdefault("subquestion_id", f"SQ-{index}"); item.setdefault("dimension_id", dimensions[0]["dimension_id"]); item.setdefault("question", f"Subpregunta {index}.")
        for index, item in enumerate(evidence, 1):
            item.setdefault("evidence_requirement_id", f"E-{index}"); item.setdefault("subquestion_refs", [subquestions[0]["subquestion_id"]]); item.setdefault("evidence_kind", "BOTH"); item.setdefault("minimum_strength", "Evidencia verificable."); item.setdefault("preferred_source_types", ["OWNER_MATERIAL"])
        supplied_works = []
        for item in (raw.get("supplied_works") or []):
            if isinstance(item, Mapping):
                supplied_works.append({
                    "work_ref": str(item.get("work_ref") or item.get("work_id") or ""),
                    "research_role": str(item.get("research_role") or "NORMAL"),
                    "editorial_intent": str(item.get("editorial_intent") or "NO_DECLARADA"),
                    "origin_ref": str(item.get("origin_ref") or origin_ref),
                })
        raw_policy = raw.get("selection_policy") if isinstance(raw.get("selection_policy"), Mapping) else {}
        selection_policy = {
            "mode": str(raw_policy.get("mode") or "OWNER_OR_DELEGATED"),
            "decision_rule": str(raw_policy.get("decision_rule") or "Decisión explícita"),
            "reconsideration_rule": str(raw_policy.get("reconsideration_rule") or "Revisar si cambia el alcance"),
        }
        if raw_policy.get("decision_ref") is not None:
            selection_policy["decision_ref"] = raw_policy["decision_ref"]
        raw_target = raw.get("target_final_works_decision") if isinstance(raw.get("target_final_works_decision"), Mapping) else {}
        target_final_works_decision = {
            "status": str(raw_target.get("status") or "NOT_DECLARED"),
            "requested_count": raw_target.get("requested_count"),
            "decision_basis": str(raw_target.get("decision_basis") or "No se decide selección de obras en la planificación inicial."),
        }
        if raw_target.get("decision_ref") is not None:
            target_final_works_decision["decision_ref"] = raw_target["decision_ref"]
        plan = {
            "contract": "research_plan", "contract_version": "2.0.0", "research_plan_id": f"{episode_id}:RESEARCH_PLAN", "episode_id": episode_id, "brief_version": brief_version,
            "research_role": research_role, "editorial_intent": editorial_intent,
            "editorial_intent_provenance": {"source": "USER_INTAKE", "reference": origin_ref},
            "origin": {"input_ref": origin_ref, "source_kind": "EPISODE_BRIEF", "question_ref": f"{episode_id}:initial_question"},
            "central_question": {"question": str(raw.get("central_question") or "Pregunta de investigación."), "decision_relevance": "Delimita el alcance investigativo."},
            "intended_use": {"uses": [str(raw.get("intended_use") or "Research V2")], "required_outputs": ["evidence_report"]},
            "scope": {"included": [str(raw.get("scope") or "Tema y materiales suministrados")], "excluded": ["Producción editorial final"]},
            "dimensions": dimensions, "subquestions": subquestions, "evidence_requirements": evidence,
            "source_strategy": [copy.deepcopy(dict(raw["source_strategy"]))] if isinstance(raw.get("source_strategy"), Mapping) else [{"strategy_id": "S-1", "source_types": ["OWNER_MATERIAL"], "purpose": str(raw.get("source_strategy") or "Material local"), "limitations": ["Sin búsqueda web"]}],
            "critical_claims": [_bound_claim(item, index, evidence[0]["evidence_requirement_id"]) for index, item in enumerate(raw.get("critical_claims") or ["No exceder la evidencia."], 1)],
            "rival_refutation": [_bound_rival(item, index, evidence[0]["evidence_requirement_id"]) for index, item in enumerate(raw.get("rival_refutation") or ["Considerar explicaciones alternativas."], 1)],
            "gaps_risks": [_bound_gap(item, index) for index, item in enumerate(raw.get("gaps_risks") or [], 1)],
            "potential_specialists": [_bound_specialist(item, index) for index, item in enumerate(raw.get("potential_specialists") or [], 1)],
            "sufficiency_criteria": [{"criterion_id": "SC-1", "dimension_id": dimensions[0]["dimension_id"], "condition": str(item), "pass_route": "CONTINUE_WITH_LIMITATIONS"} for item in (raw.get("sufficiency_criteria") or ["Evidencia suficiente para el uso declarado."])],
            "target_final_works_decision": target_final_works_decision,
            "supplied_works": supplied_works, "selection_policy": selection_policy,
            "planned_stages": list(raw.get("planned_stages") or ["PLANNING", "DISCOVERY"]), "created_at": _now(),
        }
        plan["origin_artifact_refs"] = [{
                "artifact_ref": origin_ref,
                "artifact_kind": "research_plan_proposal",
                "artifact_version": "1.0.0",
                "checksum": None,
            }]
        errors = validate_research_plan(plan)
        if errors:
            raise ResearchPlanningError("RESEARCH_PLAN_INVALID: " + " | ".join(errors))
        return plan

    def produce_research_plan(
        self,
        *,
        episode_brief: Mapping[str, Any],
        channel_context: Mapping[str, Any],
        source_access: Mapping[str, Any],
        cognitive_executor: Any,
        persistence: Any,
        research_role: str,
        editorial_intent: str,
        persist_plan: bool = True,
    ) -> dict[str, Any]:
        """Run the existing planning contract, then bind and persist its plan.

        The injected executor is intentionally the only cognitive seam.  This
        method neither selects a provider nor treats a proposal as evidence;
        Software validates and owns all durable identifiers and references.
        """
        if not callable(cognitive_executor) or not hasattr(persistence, "persist"):
            raise ResearchPlanningError("RESEARCH_PLAN_PRODUCER_DEPENDENCIES_REQUIRED")
        brief = copy.deepcopy(dict(episode_brief)) if isinstance(episode_brief, Mapping) else None
        context = copy.deepcopy(dict(channel_context)) if isinstance(channel_context, Mapping) else None
        access = copy.deepcopy(dict(source_access)) if isinstance(source_access, Mapping) else None
        if not isinstance(brief, dict) or not isinstance(context, dict) or not isinstance(access, dict):
            raise ResearchPlanningError("RESEARCH_PLAN_PRE_RESEARCH_INPUTS_REQUIRED")
        for payload, schema, label in (
            (brief, "episode_brief", "EPISODE_BRIEF"),
            (context, "research_channel_context", "CHANNEL_CONTEXT"),
            (access, "research_source_access", "SOURCE_ACCESS"),
        ):
            errors = validate_against_schema(payload, schema)
            if errors:
                raise ResearchPlanningError(f"RESEARCH_PLAN_{label}_INVALID: " + " | ".join(errors))
        episode_id = str(brief.get("episode_id") or "")
        topic = str(brief.get("tema") or "")
        brief_version = str(brief.get("brief_version") or "")
        if not episode_id or not topic or not brief_version:
            raise ResearchPlanningError("RESEARCH_PLAN_BRIEF_BINDING_REQUIRED")

        from src.ai.role_execution import RoleExecutionContractError, resolve_role_execution_contract
        from src.application.research_b2 import B2CognitiveRequest

        payload = {
            "topic": topic,
            "source_access": access,
            "brief": brief,
            "channel_context": context,
        }
        try:
            prepared = resolve_role_execution_contract(
                "RESEARCH_AND_CURATION", "research_plan_proposal", payload,
                {"stage": "RESEARCH_PLANNING"},
            )
        except RoleExecutionContractError as exc:
            raise ResearchPlanningError("RESEARCH_PLAN_CONTRACT_INVALID") from exc
        proposal = cognitive_executor(B2CognitiveRequest(
            stage="RESEARCH_PLANNING",
            output_schema="research_plan_proposal",
            input_artifacts=(),
            prepared_contract=prepared,
        ))
        if not isinstance(proposal, Mapping):
            raise ResearchPlanningError("RESEARCH_PLAN_PROPOSAL_REQUIRED")
        proposal_payload = copy.deepcopy(dict(proposal))
        proposal_errors = validate_against_schema(proposal_payload, "research_plan_proposal")
        if proposal_errors:
            raise ResearchPlanningError("RESEARCH_PLAN_PROPOSAL_INVALID: " + " | ".join(proposal_errors))
        proposal_ref = persistence.persist(
            "RESEARCH_PLAN_PROPOSAL", proposal_payload,
            artifact_id=f"{episode_id}:RESEARCH_PLAN_PROPOSAL",
            artifact_kind="ResearchPlanProposal",
        )
        plan = self.bind_research_plan(
            proposal_payload,
            episode_id=episode_id,
            brief_version=brief_version,
            research_role=research_role,
            editorial_intent=editorial_intent,
            origin_ref=str(proposal_ref["artifact_id"]),
        )
        plan["origin_artifact_refs"][0]["checksum"] = str(proposal_ref["checksum"])
        plan_errors = validate_research_plan(plan)
        if plan_errors:
            raise ResearchPlanningError("RESEARCH_PLAN_INVALID: " + " | ".join(plan_errors))
        plan_ref = None
        if persist_plan:
            plan_ref = persistence.persist(
                "RESEARCH_PLAN", plan,
                artifact_id=str(plan["research_plan_id"]),
                artifact_kind="ResearchPlan",
            )
        return {
            "research_plan_proposal": proposal_ref,
            "research_plan": plan_ref,
            "research_plan_payload": plan,
            "prepared_contract": prepared,
        }
