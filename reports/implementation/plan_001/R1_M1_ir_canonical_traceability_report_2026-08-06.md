# R1-M1 — Reporte de trazabilidad IR canónica

**Fecha:** 2026-08-06
**Misón:** R1-M1 — Trazabilidad IR canónica
**Ruta del artefacto creado:** `plans/plan_001/R1_IR_TRACEABILITY_MATRIX.md`
**Ruta del control actualizado:** `plans/001_CONTROL_OPERATIVO.md`

## Resumen

R1 quedó abierto formalmente en el estado vivo y se materializó la trazabilidad canónica de los requisitos de investigación editorial IR-0 a IR-7. No se implementó ninguna capacidad técnica.

## Requisitos procesados

- **Requisitos totales procesados:** 68, tomados de la matriz IR-0 aprobada (`ir0_matriz_investigacion_editorial_post_p08_v3_2026-08-05.xlsx`), sin reinterpretación.
- Se incorporó una fila por requisito con los campos: `requirement_id`, `functional_owner`, `requirement_summary`, `current_state`, `existing_component`, `target_component_type`, `r1_unit`, `planned_mission`, `dependency`, `affected_gate`, `expected_evidence`, `product_use_authorized`, `notes` y `resolution_hint`.

## Distribución por estado

```text
ALREADY_IMPLEMENTED: 4   (IR0-002, IR1-003, IR5-006, IRA-003)
PARTIAL:              31
MISSING:              32
OUT_OF_SCOPE_TECHNICAL: 1 (IR6-004)
FUNCTIONAL_DECISIONS_REQUIRED: 0
```

## Componentes existentes encontrados

- Schemas: `research_pack.json`, `claims_ledger.json`, `source_access_and_evidence_report.json`, `refined_thesis.json`, `narrative_human_analysis.json`, `material_curation.json`, `episode_brief.json`, `correction_routing_policy.json`, `semantic_sufficiency_audit.json`, `b5_i2_semantic_sufficiency_audit.json`, `final_editorial_audit.json`.
- `src/core/invalidation.py`. Contratos, registers y policies: `config/palabras_riesgo_youtube.md`, `config/responsibility_registry.json`, `config/active_editorial_profile.json`, `.agent/rules/02_reglas_notebooklm.md`, `.agent/skills/skill_research_tema_y_obras.md`, `.agent/skills/skill_curation_obras.md`, `workspace/CONTRATO_NOTEBOOKLM.md`.
- Autoridad: `plans/001_CONTROL_OPERATIVO.md`, `plans/plan_001/B5_PRE_SCRIPT_FOUNDATION.md`, `plans/plan_001/B5_diseno_editorial.md`, `docs/ALCANCE_Y_COORDINACION_EQUIPOS.md` y el `consolidado_funcional_aprobado_v1.2`.

## Posibles duplicaciones

Registradas en la matriz (sección "Posibles duplicaciones a evitar") para impedir crear componentes futuros que dupliquen los existentes:

1. `PhenomenonResearchPack` vs `ResearchPack` (`IR1-001`).
2. Estados de claim (`IR4-002`): `allowed/limited/prohibited` vs `CLAIM_ALLOWED/LIMITED/BLOCKED`.
3. `WorkResearchDossier` vs campos dispersos en `narrative_human_analysis`/`material_curation` (`IR1-007`).
4. Almacén de memoria (`IR5-002`) respecto de superficies heredadas de NotebookLM.
5. Adapter (`IRA-001/002`) respecto de reglas NotebookLM como ruta obligatoria.
6. Auditorías (`IR7-002..004`): normalizar sin esquemas paralelos.

Para cada requisito `PARTIAL`/`ALREADY_IMPLEMENTED` se indicó `resolution_hint` (`REUSE`/`EXTEND`/`REPLACE`/`RETIRE`); la decisión detallada se toma en la misión correspondiente.

## Dependencias no resueltas

- `IR1-005`, `IR2-003`, `IR5-002`, `IR7-005`: dependen de P-07 (propagación granular de invalidaciones), aún abierta.
- `IR7-001` (vertical real TOPIC_FIRST), `IR7-008` (independencia real productor–auditor): requieren autorización expresa separada; la suite técnica no las sustituye.
- La materialización de `IR2-005`, `IR3-009` e `IR4-005` queda bloqueada funcionalmente por los gates finales hasta implementar íntegramente las tres decisiones definitivas.

## Decisiones definitivas incorporadas

Las tres decisiones (`SP-IR0-CRITICAL_WORK_DOUBT`, `SP-IR0-MULTILINGUAL_RESEARCH_THRESHOLD`, `SP-IR0-MATERIAL_CLAIM_THRESHOLD`) fueron vinculadas con su requisito IR, componentes afectados, gates finales y misión prevista. Su texto íntegro se conserva en la matriz IR-0 (hojas 6/7/8) y no fue reinterpretado ni resumido.

## Confirmaciones

- No se implementaron contratos, schemas, scripts, agentes, prompts, skills ni gates.
- No se modificaron requisitos funcionales.
- No se alteraron los dos artefactos IR-0 aprobados.
- `product_use_authorized` se mantiene `NO`.
- No se abrió R1-M2.
- Sin create de commits ni push.

## Recomendación

**PASS_WITH_LIMITATIONS**

La misión cumple su alcance documental con fidelidad. Las limitaciones que motivan la recomendación no bloquean R1-M1: dependencias abiertas de P-07 y autorización expresa de vertical real, que se resolverán en misiones posteriores. La apertura de R1 queda registrada y la matriz es utilizable como referencia de trazabilidad.