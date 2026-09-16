from __future__ import annotations

import copy

import pytest

from src.application.research_planning import ResearchPlanningError, ResearchPlanningService


def _proposal() -> dict:
    return {
        "contract": "research_plan_proposal",
        "contract_version": "1.0.0",
        "central_question": "Pregunta",
        "intended_use": "Uso de investigación",
        "scope": "Alcance",
        "dimensions": ["Dimensión"],
        "subquestions": ["Subpregunta"],
        "evidence_requirements": ["Evidencia"],
        "source_strategy": "Material local",
        "critical_claims": ["Afirmación"],
        "rival_refutation": ["Explicación alternativa"],
        "gaps_risks": [],
        "potential_specialists": [],
        "sufficiency_criteria": ["Criterio"],
        "target_final_works_decision": {},
        "supplied_works": [],
        "selection_policy": {},
        "planned_stages": ["PLANNING"],
    }


def _bind(proposal: dict) -> dict:
    return ResearchPlanningService().bind_research_plan(
        proposal,
        episode_id="ep_r4",
        brief_version="1.0.0",
        research_role="NORMAL",
        editorial_intent="NO_DECLARADA",
        origin_ref="proposal:r4",
    )


def test_r4_absent_fields_keep_contractual_defaults() -> None:
    proposal = _proposal()
    del proposal["planned_stages"]
    plan = _bind(proposal)
    assert plan["selection_policy"]["mode"] == "OWNER_OR_DELEGATED"
    assert plan["target_final_works_decision"]["status"] == "NOT_DECLARED"
    assert plan["planned_stages"] == ["PLANNING", "DISCOVERY"]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("selection_policy", {"mode": ""}),
        ("selection_policy", {"mode": "INVALID"}),
        ("selection_policy", {"mode": None}),
        ("target_final_works_decision", {"status": ""}),
        ("target_final_works_decision", {"status": "INVALID"}),
        ("target_final_works_decision", {"status": None}),
        ("planned_stages", []),
        ("planned_stages", ["INVALID"]),
        ("planned_stages", None),
    ],
)
def test_r4_present_invalid_values_fail_closed(field: str, value: object) -> None:
    proposal = _proposal()
    if field == "selection_policy":
        proposal[field] = value
    elif field == "target_final_works_decision":
        proposal[field] = value
    else:
        proposal[field] = value
    with pytest.raises(ResearchPlanningError, match=r"^RESEARCH_PLAN_INVALID:"):
        _bind(proposal)


def test_r4_historical_valid_values_pass_unchanged() -> None:
    proposal = _proposal()
    proposal["selection_policy"] = {"mode": "USER_SELECTION"}
    proposal["target_final_works_decision"] = {"status": "RECOMMENDED", "requested_count": 3}
    proposal["planned_stages"] = ["PLANNING", "DISCOVERY", "BASE_RESEARCH"]
    plan = _bind(copy.deepcopy(proposal))
    assert plan["selection_policy"]["mode"] == "USER_SELECTION"
    assert plan["target_final_works_decision"]["status"] == "RECOMMENDED"
    assert plan["planned_stages"] == ["PLANNING", "DISCOVERY", "BASE_RESEARCH"]
