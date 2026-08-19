# R1-M11 - Integracion tecnica de capacidades IR

R1-M11 status: `COMPLETED`.
Technical result: controlled integration passes.
Technical validation: `PASS`.
Technical review: `PASS`.
Functional approval: not inferred.
Product use: not authorized.
Real research vertical: `NOT_DEMONSTRATED`.
R2 execution: `NOT_AUTHORIZED`.

## Gap Map

| Requirement | Current implementation and evidence | Residual state | Resolution |
|---|---|---|---|
| IR7-001 | R1 roadmap limits R1.7 to controlled integration; live vertical remains unauthorized. | `DEFERRED_TO_REAL_EXECUTION` | No real topic, works or thesis executed. |
| IR7-006 | Existing claims, sufficiency and audit contracts covered isolated states, but no composition existed. | `INTEGRATION_MISSING` | Added controlled cases for positive, `LIMITED_BUT_USABLE`, blocked and `REQUEST_CHANGES`. |
| IR7-007 | Existing provenance, lifecycle, contradiction, memory, specialist, invalidation and audit validators were reusable. | `INTEGRATION_MISSING` | Composed the existing validators in five non-redundant controlled cases. |
| IRA-001 | NotebookLM material was historical documentation only; no neutral executable adapter contract existed. | `REALLY_MISSING` | Added provider-agnostic optional adapter schema and validator. |
| IRA-002 | Optionality and non-authority were documented but not mechanically enforced. | `PARTIALLY_COVERED` | Adapter schema and tests reject canonical-memory, veracity-authority and required-gate claims; absent/unavailable adapter remains valid. |
| IRA-004 | Capability registry, maturity/availability fields and controlled-demo invariant already existed. | `STRUCTURALLY_COVERED` | Reused them and added an integration regression for invalid promotion. |

Fidelity criteria remain `FUNCTIONAL_DECISION_REQUIRED` for `SCRIPT_PRODUCT`; no fidelity threshold was invented.

## Reused Components

- `schemas/research_pack.json` and `src/core/contract_validation.py`
- `schemas/work_lifecycle.json` and `validate_work_lifecycle`
- `schemas/claims_ledger.json` and `validate_claims_ledger`
- `schemas/research_stop_decision.json` and `validate_research_stop_decision`
- `src/core/editorial_semantic_memory.py`
- `src/core/invalidation.py`
- `schemas/independent_research_audit.json`
- `src/core/research_audit.py`
- `schemas/correction_routing_policy.json`
- `src/core/plan_005_invariants.py` (`CONTROLLED_DEMO_NOT_PROMOTION`)
- Existing R1-M6, M7, M8 and M9 controlled fixture builders/tests

## Changes

- Added `schemas/source_grounded_research_adapter.json` as the missing neutral optional adapter contract.
- Added `src/core/research_adapter.py` with optional absence handling, schema validation and evidence-reference checks.
- Extended `validate_research_pack` with an optional adapter input so the neutral contract is checked at the existing research validation boundary without becoming part of the canonical pack.
- Added `tests/integration/test_r1_m11_integration.py` with seven controlled integration tests covering the M11 cases and authority boundaries.
- Added the adapter fixture to `tests/core/test_all_schemas.py` so every schema retains a valid structural fixture.
- Updated `plans/001_CONTROL_OPERATIVO.md` only for M11 authorization, mission status and current mission.

## Controlled Cases

- Positive composition: research pack, derived provenance, lifecycle, claims, aggregate sufficiency, memory consultation, specialist contribution and independent audit.
- Limited composition: `LIMITED_BUT_USABLE` remains limited through multilingual provenance, claim decision and audit finding.
- Material block: blocked claim and material contradiction fail closed through aggregate sufficiency.
- Provenance and doubt: original, transcript and translation remain distinct; critical doubt covers activated, non-activated, resolved-return and invalidated-return paths.
- Reuse, specialist and correction: semantic reuse does not auto-block, specialist authority remains contribution-only, audit defects route to origin, producer output is unchanged and invalidation preserves origin.
- Adapter neutrality and state separation: absent and unavailable adapters do not block; invalid authority/gate/memory promotion is rejected; controlled integration promotion flags fail closed.

## Validation

- `py -3 -m pytest tests/integration/test_r1_m11_integration.py -q`: `7 passed`.
- `py -3 -m pytest tests/integration/test_r1_m11_integration.py tests/core/test_all_schemas.py tests/core/test_contract_validation.py -q`: `57 passed`, `220 subtests passed`.
- `py -3 -m pytest tests/core tests/harness/test_b5_i1_editorial_input.py tests/harness/test_b5_i2.py tests/harness/test_plan007_p6a_vertical.py -q`: `700 passed`, `1 skipped`, `220 subtests passed`.
- `py -3 -m compileall -q src/core/contract_validation.py src/core/research_adapter.py tests/integration/test_r1_m11_integration.py tests/core/test_all_schemas.py`: passed.
- `git diff --check`: passed; Git reported only existing line-ending normalization warnings for modified text files.
- `git diff --no-index --check -- NUL <new-text-file>` for each new schema, adapter, integration test and report: passed without whitespace diagnostics.

## Limitations and Deferrals

- No real editorial vertical, real source calls, real episode, refined editorial thesis or product-use authorization was performed.
- `REAL_RESEARCH_VERTICAL` remains `NOT_DEMONSTRATED`.
- Fidelity criteria and operational producer/auditor independence remain pending their functional/real execution decisions.
- The adapter is a neutral optional envelope, not a source of truth, canonical memory, required gate or veracity authority.
- Existing non-material correction-route schema duplication from M10 was not reopened.
- No systemic transversal defect was reproduced; no Dirección Transversal escalation was required.

## Evidence Boundary

This report demonstrates technical composition with synthetic fixtures only. It does not approve R1, close `R1_GATE`, authorize R2, promote `TECHNICALLY_VALIDATED` to `OPERATIONALLY_DEMONSTRATED`, issue `FUNCTIONAL_APPROVAL`, or authorize product use.

## Technical Closure

R1-M11 is technically closed with `TECHNICAL_VALIDATION_STATUS: PASS`, `TECHNICAL_REVIEW: PASS`, `TECHNICAL_APPROVAL: APPROVED` and `RESULT: PASS`. The external focal audit after the R1-M10 correction was convergent. Integration M10→M11: `PASS`. Upstream `MATERIAL-1` (`MULTIPLE_PRODUCER_RUNS` independence) was corrected and independently verified as `VERIFIED_FIXED`. Real editorial vertical remains `NOT_DEMONSTRATED`; functional approval is not inferred; product use is not authorized; R2 execution is not authorized. `R1_GATE` remains a separate review.
