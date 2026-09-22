# PLAN015 — Evidencia de implementación integrada

Fecha de auto-verificación y revalidación focal: `2026-09-21`  
Baseline evaluado: working tree actual; los cambios de PLAN015 todavía no forman parte de `HEAD`.  
Resultado del implementador: `IN_PROGRESS` — correcciones focales post-auditoría en autoridad/contexto  
Auditoría independiente final: `FAIL_WITH_MATERIAL_FINDINGS`  
Aceptación OWNER: `PENDING`

## Límites de la evidencia

- No se realizó ninguna llamada real a IA, API de pago, provider externo o servicio de red.
- Los tests de handoff ejercitan preparación, bindings, importación, anti-replay y materialización software-owned con resultados locales controlados.
- La evidencia demuestra que la superficie real puede preparar e importar el trabajo cognitivo; no afirma calidad editorial real ni uso productivo.
- PLAN016 permanece fuera de esta implementación y continúa sin autorización de ejecución.

## Hitos funcionales

| Hito | Resultado | Evidencia principal |
| --- | --- | --- |
| HF-01 — Continuidad y autoridad | FOCAL_REVALIDATION_PASS; cierre global pendiente | `tests/harness/test_plan015_hf01.py` (3 passed), `tests/core/test_plan015_authority_hardening.py` y consumidor CLI |
| HF-02 — Cadena editorial downstream | PASS | `tests/harness/test_plan015_hf02.py`: cadena sintética, stale Research fail-closed y ocho handoffs reales sucesivos hasta `FINAL_VALIDATIONS_COMPLETE` |
| HF-03 — Producto completo | NOT_FULLY_DEMONSTRATED | La auditoría final mantiene pendiente el E2E representativo; no se ejecuta ni se cierra en este bloque |

## Trazabilidad mínima de correcciones post-auditoría

La asignación consolidada de los 41 AUD-C se mantiene fuera de este documento. Este bloque solo registra la evidencia de implementación de los tres findings de PLAN015 trabajados en esta continuación:

| Finding | Estado actual | Baseline | Evidencia focal |
| --- | --- | --- | --- |
| `AUD-C011` | `CLOSED_IN_CURRENT_REPO` | `CLOSED_IN_WORKING_TREE_NOT_IN_HEAD` | `src/core/product_authorization.py`: normalización fail-closed, rechazo de traversal y containment físico mediante `Path.resolve()`; `tests/core/test_plan015_authority_hardening.py` cubre `./`, `\\`, traversal y symlink/junction escape en esta sesión |
| `AUD-C012A` | `CLOSED_IN_CURRENT_REPO` | `CLOSED_IN_WORKING_TREE_NOT_IN_HEAD` | `src/ai/providers/agent_handoff.py` exige identidad por modo, conserva compatibilidad MISSION cuando el resultado histórico omite solo `authorization_mode`, rechaza identity-free y mantiene PRODUCT sin `mission_id`; `src/ai/registry.py` y `schemas/execution_provenance_registry.json` persisten `authorization_id`/checksum en provenance; HF-01, M7/B5 y las pruebas focales C012A pasan |
| `AUD-C015` | `CLOSED_IN_CURRENT_REPO` | `CLOSED_IN_WORKING_TREE_NOT_IN_HEAD` | `src/ai/role_execution.py` bloquea toda referencia simbólica no resuelta; B2/M4/M5/M6 ya pasan el contexto canónico; `ResearchM7SyntheticRunner._context()` reconstruye `research_channel_context` desde el perfil activo para resume; M2–M6, M7/B5, hybrid y la matriz del registry pasan sin relajar fail-closed |

Estos cierres focales no sustituyen la auditoría final fallida, no cierran PLAN015 y no convierten HF-03 en demostrado.

### Validación focal reproducible del bloque

| Alcance | Resultado |
| --- | --- |
| `tests/core/test_plan015_authority_hardening.py`, `tests/ai/test_role_execution_contract.py`, `tests/core/test_application_intake.py` | `117 passed` |
| `tests/harness/test_plan013_synthetic_e2e.py` | `5 passed` |
| `tests/harness/test_plan015_hf01.py` | `3 passed` |
| `tests/core/test_all_schemas.py` | `6 passed, 292 subtests passed` |

La comprobación MISSION focal de `tests/harness/test_plan009_p2_roundtrip.py` no es evidencia de regresión de este bloque: sus tres casos no alcanzan el roundtrip porque la autoridad de material `MD-CI-001` vigente en el working tree no satisface el contrato de demostración controlada. No se modificó esa autoridad fuera del alcance C011/C012A/C015.

## Trazabilidad de aceptación

| Criterio PLAN015 | Resultado | Implementación/evidencia |
| --- | --- | --- |
| `E2E_NORMAL_SURFACE`, `NEXT_VALID_TRANSITION_FROM_DURABLE_STATE` | PASS | `EpisodeApplicationService.resume/import_result`; CLI `iniciar`, `importar-resultado`, `reanudar`; tests HF-01/HF-02/HF-03 y test CLI de HF-03 |
| `TOPIC_TO_RESEARCH`, `TOPIC_CURRENT_GATE_TO_RESEARCH` | PASS | `src/application/service.py`; HF-01 y reassessment verifican APPROVE, condiciones durables, stop y no replay |
| `RESEARCH_TO_B5_I3`, `RESEARCH_READY_BOUND_TO_EXISTING_B5_I3_CAPABILITY` | PASS | `ResearchV2B5I3Adapter.validate_research_v2_precondition`; HF-02 positivo y stale negativo |
| `DOWNSTREAM_EDITORIAL_CHAIN` | PASS | B5-I3 → Writing → Editor → Final Editorial Audit mediante capabilities existentes; HF-02 sintético y roundtrip `AGENT_HARNESS` |
| `MANDATORY_FINAL_VALIDATIONS_CONVERGED`, `MANDATORY_VALIDATIONS_SAME_ARTIFACT_VERSION_CHECKSUM`, `FINAL_WARN_RULE_MECHANIZABLE` | PASS | `FinalEditorialAudit` y `FinalScriptReview` software-owned sobre la misma identidad; `validate_plan015_downstream` y HF-02 |
| `HUMAN_DECISION_TO_CANONICAL_APPROVAL`, `FINAL_APPROVAL_BOUND_TO_EXACT_SCRIPT`, `APPROVER_REGISTRY_REUSED` | PASS | `HumanDecisionRequest.expected_approval_role`; mapper en `EpisodeApplicationService`; `validate_editorial_script_approval`; negativos de actor y rol en HF-03 |
| `EDITORIAL_SCRIPT_APPROVED` | PASS | `record_plan013_editorial_closure` consume el artifact completo, la decisión ligada y las validaciones finales; HF-03 |
| `UNIQUE_CURRENT_POINTER`, `NO_MULTIPLE_CURRENT_DECLARATIONS`, `CURRENT_LEGACY_AMBIGUITY_FAIL_CLOSED`, `HISTORY_PRESERVED` | PASS | `approved_current.json`, estado/índice y `plan013_script_versions.json`; HF-03 cubre working/approved, preservación y duplicado ambiguo |
| `VALID_COGNITIVE_WORK_REPLAYED_UNNECESSARILY` | NO | Imports idénticos son idempotentes; handoffs cerrados se recuperan desde `roundtrip_results`; HF-01 y HF-02 |
| `PRODUCT_OPERATION_DEPENDS_EXCLUSIVELY_ON_CURRENT_MISSION` | NO | El entrypoint ordinario usa autoridad PRODUCT; regresión en `test_application_intake.py` confirma independencia de una misión temporal activa |
| `PRODUCT_AUTHORITY_MACHINE_READABLE`, `PRODUCT_AUTHORITY_EXPLICIT`, `PRODUCT_AUTHORITY_FAIL_CLOSED`, `PRODUCT_AUTHORITY_REQUEST_BINDING_AND_STALE` | PASS | Registry/schema/consumer PRODUCT y negativos de decisión sustituida, checksum, revocación y modo desconocido en `test_plan015_authority_hardening.py` |
| `PRODUCT_AUTHORITY_SCOPE_ISOLATION`, `PRODUCT_AUTHORITY_NON_TRANSITIVE`, `IMPLEMENTED_DOES_NOT_IMPLY_PRODUCT_AUTHORIZED`, `CAPABILITY_AUTHORIZATION_LIFECYCLE`, `READY_NOT_AUTHORIZED_MODE_SEMANTICS` | PASS | Resolución 0/1/>1 y scopes capability/role/family/route/interface/path; tests de hardening |
| `FUNCTIONAL_APPROVAL_NOT_CIRCULAR`, `PRODUCT_MODE_MATERIAL_DECISION_BINDING`, `MISSION_MODE_MATERIAL_DECISION_PRESERVED`, `MISSION_AUTHORIZATION_PRESERVED_FOR_CONTROLLED_USE` | PASS/YES | Separación entre autorización técnica, decisión material y aprobación humana; tests PRODUCT y controlled validation |
| `CAPABILITY_TECHNICAL_AVAILABILITY_PRESERVED`, `REAL_EXECUTION_PROFILES_RESOLVED`, `REAL_ENTRYPOINT_OPERATIONAL_REQUIRED` | YES/PASS | Capabilities permanecen `READY_NOT_AUTHORIZED`; ruta PRODUCT neutral `EXECUTOR_MANAGED`; evidencia controlada y HF-02 de handoff sin inferencia real |
| `AGENT_HARNESS_AUTHORITY_BINDINGS_PRESERVED`, `AGENT_HARNESS_ROUNDTRIP_NORMALIZED` | PASS | `AgentHandoffProvider`, workflow durable y `roundtrip_results`; episode/capability/stage/role/package/input/result/executor bindings; HF-01/HF-02 |
| `E2E_TRANSITION_MATRIX_ENFORCED` | PASS | Stops durables de Topic, Research, downstream, corrección/rechazo y cierre; tests HF-01/HF-02/HF-03 |
| `FINAL_SCRIPT_REVIEW_SOFTWARE_OWNED` | PASS | `build_final_script_review` se ejecuta en Software tras audit elegible y conserva checksum del audit |
| `NO_AMBIGUOUS_MISSION_BOUND_HANDOFFS_AT_ACTIVATION` | PASS | `Historial/ep_0001/handoffs/PLAN015_reconciliation_MVP_REAL_E2E_SCRIPT_01.json`: ambiguos `0`, pendientes de misión anterior `0`; el handoff de validación controlada está ligado a su evidencia PLAN015 |
| `ACCEPTANCE_EVIDENCE_TRACEABILITY` | PASS | Este documento enlaza cada grupo de aceptación con implementación y prueba focal |
| `SOFTWARE_IA_SOFTWARE_INVARIANT` | PASS | Los resultados externos solo aportan proyección editorial; IDs, timestamps, checksums, lineage, FinalScriptReview, aprobación y closure son software-owned |
| `PRODUCER_EDITOR_AUDITOR_INDEPENDENCE` | PASS | Roles y run IDs separados; closure vuelve a verificar independencia de runs y actores |
| `NO_SECOND_EDITORIAL_SOURCE_OF_TRUTH`, `NO_NEW_CHECKPOINT_STORE_WITHOUT_OWNER_DECISION`, `NO_PARALLEL_RESEARCH_ENGINE`, `NO_UNAUTHORIZED_SCOPE_EXPANSION` | PASS/YES | Se reutilizan `EpisodeApplicationService`, `VaultEpisodeStore`, `workflow_state`, `roundtrip_results`, Research M7, B5-I3, contratos y closure existentes; no se implementa multi-episodio ni PLAN016 |

## Ejecuciones de validación

### Revalidación de compatibilidad C012A/C015

| Grupo | Antes de la corrección | Después de la corrección | Clasificación de los fallos restantes |
| --- | --- | --- | --- |
| Hybrid runtime/handoff | `24 passed, 1 failed` (`C015`) | `25 passed` | Ninguno |
| PLAN012 M2–M6 | `35 passed, 131 failed` (`130 C015`, `1 preexistente`) | `165 passed, 1 failed` | El mismo fallo preexistente de disponibilidad del capability registry |
| PLAN012 M7/B5 y resume/recovery | `45 passed, 14 failed` (`10 C015`, `4 C012A`) | `59 passed` | Ninguno |
| Contratos de roles | `20 passed` | `20 passed` | Ninguno |
| HF-01 | `3 passed` | `3 passed` | Ninguno |
| Pruebas nuevas C012A | No aplicaba | `3 passed` | Ninguno |

La comparación confirma que ningún PASS del baseline se convirtió en FAIL. El único fallo restante del grupo M2–M6 es el mismo fallo preexistente de `availability_status` y no pertenece a esta misión.

| Comando focal | Resultado |
| --- | --- |
| `pytest` de autoridad, reassessment y HF-01/HF-02/HF-03 | `30 passed` |
| `pytest` de HF-02/HF-03 e interacción de aplicación | `86 passed` |
| schemas críticos, fixture de autoridad PRODUCT y cierre PLAN013 | `8 passed, 190 subtests passed` |

Advertencias observadas: deprecaciones de `jsonschema.RefResolver` y `draft7_format_checker`; no son fallos funcionales de PLAN015.

## Dictamen del implementador

`PLAN015_IMPLEMENTATION_SELF_VERIFICATION: PASS`

`PLAN015_STATUS: IN_PROGRESS`

`PLAN015_FINAL_INDEPENDENT_AUDIT: FAIL_WITH_MATERIAL_FINDINGS`

`PLAN015_HF03: NOT_FULLY_DEMONSTRATED`

Este dictamen no sustituye la auditoría independiente final ni la aceptación del OWNER.
