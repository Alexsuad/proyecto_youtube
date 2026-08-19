# R1-M10 - Independent Research Audits

Technical review: `PASS`.
Technical approval: `APPROVED`.
R1-M10 status: `COMPLETED`.

## Scope

R1-M10 was limited to the technical representation and controlled validation of independent research audits. It did not execute a real editorial vertical, approve research, promote a capability, open R1-M11, authorize R2, or authorize product use.

## Gap Map

- IR7-002 was partial: B5-I2 already represented and executed semantic sufficiency auditing, but no single technical contract represented the differentiated audit types required for fidelity, interpretation, claims and sources, curation, and the research package.
- IR7-003 was partial: B5-I2 contained producer/auditor lineage and audit-only write scope, but the property was not reusable as a generic research-audit contract.
- IR7-004 was partial: existing decision vocabularies were available, but no shared audit envelope preserved findings, evidence, limitations, defects, and decision for the differentiated audit types.
- IR7-005 was partial: `correction_routing_policy.json` and `InvalidationEngine` existed, but no audit consumer validated that every detected defect had an origin-preserving correction route.
- IRA-003 was already covered by the responsibility registry and coordination authority. No change was needed.
- Fidelity criteria remain owned by SCRIPT_PRODUCT. The dossier continues to represent `independent_fidelity_audit` as deferred; this mission did not invent fidelity criteria or claim a fidelity audit was functionally approved.

## Implementation

- Added `schemas/independent_research_audit.json`, a single parametrized envelope for the six IR7-002 audit types.
- Added `src/core/research_audit.py` for schema validation, distinct producer/auditor actor and run checks, audit-only write scope, defect-to-route consistency, and opaque functional criterion identifiers.
- Extended `src/core/invalidation.py` with origin-preserving correction-route resolution using the existing correction policy schema and in-memory dependency engine; no persistent registry is written by this validation path.
- Added adversarial and positive tests, including same producer/auditor rejection, one route per defect, PASS incompatibility with pending findings/defects, multiple producer runs, and defect routing without producer-output mutation.
- Reconciled the live control minimally from PLAN 007 owner review to the completed R1-M10 state and recorded this evidence path. R2, R1-M11, real execution, functional approval, and product use remain closed or unauthorized.

## Validation

- `python -m pytest tests/core/test_all_schemas.py tests/core/test_contract_validation.py tests/core/test_invalidation.py tests/core/test_research_audit.py -q`: 62 passed, 217 subtests passed.
- `python -m pytest tests/core/test_cross_registry_integrity.py tests/harness/test_plan007_p6a_vertical.py tests/harness/test_b5_i2.py -q`: 83 passed.
- `python -m compileall -q src/core/research_audit.py src/core/contract_validation.py src/core/cross_registry_integrity.py src/scripts/b5_i2_gate.py`: passed.
- `git diff --check`: passed.

## Limitations

The contract and controlled fixtures do not demonstrate real producer/auditor operation. Fidelity criteria and functional audit judgments remain pending SCRIPT_PRODUCT. This evidence supports technical review only and does not establish operational demonstration, functional approval, product readiness, or authorization for product use.

The audit envelope repeats the correction-route shape because the repository schema resolver does not currently resolve external schema references; actual route validation delegates to the existing `correction_routing_policy.json`. This is a non-material technical debt, not a second routing policy.

## Corrección posterior a auditoría

Se detectó posteriormente un gap de independencia en `MULTIPLE_PRODUCER_RUNS`. Se corrigió verificando `auditor.run_id` contra los `producer_run_id` reales de los artefactos. Se añadió regresión adversarial.

La corrección fue verificada de forma externa e independiente: `MATERIAL-1: VERIFIED_FIXED`.
