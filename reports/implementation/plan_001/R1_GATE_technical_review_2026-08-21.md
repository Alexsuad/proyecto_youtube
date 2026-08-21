# R1_GATE — Revisión técnica integrada

**Fecha:** 2026-08-21
**Alcance:** R1-M1 a R1-M11; preparación técnica de una ejecución controlada de B5-I1 en R2.
**No ejecutado:** investigación editorial real, episodio real, B5-I1 real, B5-I2 real, producto, publicación o promoción de madurez.

## Dictamen

La infraestructura técnica R1 queda `PASS` para revisión funcional: contratos, validadores, lineage, checksums, provenance, lifecycle, claims, contradicciones, memoria, contribuciones especializadas, auditoría independiente y adapter opcional se validan de forma integrada y fail-closed.

`R1_GATE` no puede declararse `PASS` todavía. No existe una evidencia vigente de `SCRIPT_PRODUCT_RESEARCH_REVIEW: PASS_FOR_TECHNICAL_CAPABILITIES`; por tanto, `R2_EXECUTION` permanece `NOT_AUTHORIZED`, `REAL_RESEARCH_VERTICAL` permanece `NOT_DEMONSTRATED` y `AUTHORIZED_FOR_PRODUCT_USE` permanece `NO`.

## Preflight y autoridad

- `master` y `origin/master` coincidían en `6305375ce345686d4ef0423eeb9d0c6235c04ae6`; el worktree estaba limpio antes de la revisión.
- `plans/001_CONTROL_OPERATIVO.md` confirma `CURRENT_MISSION: NONE`, `NEXT_ALLOWED_ACTION: R1_GATE_REVIEW_REQUIRED` y `R2_EXECUTION: NOT_AUTHORIZED`.
- La búsqueda de `SCRIPT_PRODUCT_RESEARCH_REVIEW` y `PASS_FOR_TECHNICAL_CAPABILITIES` fuera del requisito del roadmap no encontró una decisión funcional vigente. Esta ausencia se conserva como bloqueo funcional, no se sustituye por una conclusión técnica.

## Corrección de integración R1

Se encontraron dos defectos técnicos materiales: `IndependentResearchAudit` solo tenía consumidores de prueba y el CLI de `src/scripts/b5_i2_gate.py` no recibía la colección de artefactos R1 que su evaluación ya podía relacionar (`WorkLifecycle` y los `WorkResearchDossier` requeridos).

La corrección no añade contratos ni capacidades nuevas:

- el gate B5-I2 existente exige ahora por su CLI `ClaimsLedger`, `WorkLifecycle`, la colección repetible de `WorkResearchDossier` e `IndependentResearchAudit` cuando solicita cierre de investigación;
- resuelve cada `dossier_ref` del lifecycle contra su dossier, construye el contexto canónico `ClaimsLedger` + `NarrativeHumanAnalysis` por obra y reutiliza `validate_work_lifecycle(..., dossier_artifacts=...)`;
- vincula cada fila de `IndependentResearchAudit` a un artefacto R1 real, checksum exacto y output/provenance del `ExecutionProvenanceRegistry`; una ausencia, checksum obsoleto, artefacto ajeno o auditoría no independiente bloquea;
- la semántica usa el checksum físico del output que registra `src/ai/registry.py`; se añadieron los `artifact_kind` R1 faltantes al schema y a la compatibilidad del productor canónico, mientras NarrativeHumanAnalysis conserva el kind existente `analysis`;
- el caso positivo integrado de tres obras, tres dossiers y auditoría exacta ya no acepta `FAIL`: queda `BLOCKED` solo por `FUNCTIONAL_DECISION_REQUIRED`, sin violaciones técnicas R1;
- los tests cubren colección incompleta, identidad incorrecta, checksum incorrecto, artefacto ajeno, auditoría no independiente y coexistencia segura de una salida histórica con una salida actual exacta.

## Trazabilidad de las decisiones IR-0

| Decisión | Representación y consumidor | Evidencia adversarial |
|---|---|---|
| `SP-IR0-CRITICAL_WORK_DOUBT` | `schemas/work_lifecycle.json`, `validate_work_lifecycle`, cierre B5-I2 | `tests/core/test_work_lifecycle.py` y `tests/harness/test_plan007_p6a_vertical.py` cubren activación, no activación, retorno e invalidación. |
| `SP-IR0-MULTILINGUAL_RESEARCH_THRESHOLD` | provenance en `schemas/research_pack.json`, `validate_research_pack`, QA/gates B5-I1 | `tests/core/test_r1_m6_m8.py` e integración R1-M11 cubren fuente derivada, riesgo material, limitación y bloqueo. |
| `SP-IR0-MATERIAL_CLAIM_THRESHOLD` | `schemas/claims_ledger.json`, `schemas/research_stop_decision.json`, validadores y cierre B5-I2 | `tests/core/test_r1_m6_m8.py`, `tests/core/test_r1_m7.py` e integración R1-M11 cubren suficiencia, invalidadores, retorno y bloqueos. |

## Integración y límites demostrados

- `ResearchPack` es consumido por `qa_brief_research.py`, `evidence_sufficiency_gate.py`, `thesis_provisional_gate.py` y `b5_i2_gate.py`.
- `EditorialSemanticMemory` se consulta desde los checkpoints B5-I1; ausencia de memoria es una ruta opcional y memoria inválida no se convierte en `PASS`.
- El cierre B5-I2 recibe ahora los artefactos R1 de lifecycle, claims, colección de dossiers y auditoría independiente; no permite sustituir la colección por un dossier único al invocar el CLI.
- La auditoría independiente rechaza actor o run del auditor iguales al productor, findings/defectos incompatibles con `PASS` y rutas de corrección ausentes.
- La evidencia es técnica y sintética. No prueba una vertical editorial real ni convierte la revisión funcional pendiente en aprobación.

## Validaciones ejecutadas

- `py -3 -m pytest tests/harness/test_b5_i2.py -q`: `80 passed`.
- `py -3 -m pytest tests/ai/test_hybrid_runtime.py -q`: `42 passed`; incluye productores R1 y regresión de checksum ante distinta indentación JSON física.
- `py -3 -m pytest tests/core/test_work_lifecycle.py tests/core/test_research_audit.py tests/integration/test_r1_m11_integration.py -q`: `53 passed`.
- Regresión R1 dirigida combinada —schemas, contract validation, lifecycle, dossiers, research audit, R1-M6/M7/M9, R1-M11, B5-I2 y provenance—: `327 passed`, `223 subtests passed`.
- `python src/scripts/check_material_decisions.py`: `PASS`.
- `python src/scripts/check_b3_canonical_consumption.py`: `PASS`.
- `python src/scripts/runtime_contamination_guard.py`: `ACTIVE_PRODUCT_CONTAMINATION=0`, `blocked=[]`.
- `git diff --check`: PASS.

## Estado resultante

```text
IR_CONTRACTS: IMPLEMENTED_AND_TECHNICALLY_VALIDATED
IR_COMPONENT_INTEGRATION: PASS
IR_REAL_VERTICAL: NOT_YET_DEMONSTRATED
SCRIPT_PRODUCT_RESEARCH_REVIEW: PENDING
R1_GATE: NOT_PASS
BLOCKING_CONDITION: SCRIPT_PRODUCT_RESEARCH_REVIEW
R2_EXECUTION: NOT_AUTHORIZED
AUTHORIZED_FOR_PRODUCT_USE: NO
```

El único paso necesario para resolver este gate es una revisión funcional explícita de `SCRIPT_PRODUCT` sobre las capacidades técnicas. Esta revisión no puede ser emitida por infraestructura, tests ni este reporte.
