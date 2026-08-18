# R1 — Trazabilidad IR canónica (R1-M1)

**Documento:** Matriz de trazabilidad de requisitos de investigación editorial IR-0 a IR-7.
**Fuente de requisitos (canónica):** `docs/reconciliation/p08/2026-08-05/ir0_matriz_investigacion_editorial_post_p08_v3_2026-08-05.xlsx`.
**Plan técnico:** `docs/reconciliation/p08/2026-08-05/ir0_plan_tecnico_investigacion_editorial_post_p08_v2_2026-08-05.md`.
**Roadmap:** `plans/plan_001/B0_1_roadmap_implementacion_post_p08.md`.
**Estado vivo:** `plans/001_CONTROL_OPERATIVO.md`.

```text
R1_STATUS: IN_PROGRESS
R1_M1_STATUS: COMPLETED_PENDING_REVIEW
IR_TRACEABILITY_MATRIX: CREATED
FUNCTIONAL_DECISIONS_REINTERPRETED: NO
TECHNICAL_COMPONENTS_IMPLEMENTED: R1_M2_AND_R1_M3_CONTRACT_EXTENSIONS_PARTIAL_BY_IR4_IR7_DEPENDENCIES
PRODUCT_USE_AUTHORIZED: NO (siempre durante R1)
```

## Propósito

Esta matriz es la referencia técnica única de los requisitos IR. Evita que las misiones R1-M2 a R1-M11 auditén o inventen el alcance cada vez: define requisito, owner funcional, componente existente o faltante, estado real, dependencia, gate relacionado, fase de implementación y evidencia esperada.

No implementa contratos, schemas, scripts, agentes, prompts, skills ni gates. Solo documenta.

## Convenciones

- `current_state` proviene de la matriz IR-0 aprobada: `ALREADY_IMPLEMENTED`, `PARTIAL`, `MISSING`, `OUT_OF_SCOPE_TECHNICAL`.
- `existing_component` registra la evidencia estructural encontrada en el repositorio (o `NONE`).
- `resolution_hint` (solo `PARTIAL`/`ALREADY_IMPLEMENTED`): indica si el componente futuro debe `REUSE`, `EXTEND`, `REPLACE` o `RETIRE` el existente. La decisión técnica detallada se toma en la misión correspondiente.
- `product_use_authorized` es siempre `NO` durante R1.
- Los `requirement_summary` son fieles a la matriz IR-0; no se reinterpretan.

## Matriz

| requirement_id | functional_owner | requirement_summary | current_state | existing_component | target_component_type | r1_unit | planned_mission | dependency | affected_gate | expected_evidence | product_use_authorized | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| IR0-001 | SCRIPT_PRODUCT | Distinguir IMPLEMENTATION_WORKSTREAM de EDITORIAL_RESEARCH_WORKFLOW. | PARTIAL | `plans/plan_001/B5_PRE_SCRIPT_FOUNDATION.md`; `plans/plan_001/B5_diseno_editorial.md` | registry / representación documental | R1.1 | R1-M1 | P-08 integrada | R1_GATE | Representación canónica consumible sin segunda fase viva. | NO | EXTEND. No crear una segunda autoridad de estado vivo. |
| IR0-002 | SCRIPT_PRODUCT | Mantener IMPLEMENTATION_AUTHORIZED=NO y REAL_EPISODE_AUTHORIZED=NO hasta convergencia. | ALREADY_IMPLEMENTED | `plans/001_CONTROL_OPERATIVO.md`; `docs/reconciliation/p08/2026-08-05/consolidado_funcional_aprobado_v1.2_2026-08-04.md` | registry / validación de estado | R1.1 | R1-M1 | Ninguna | NONE | Guard de estado vigente en control operativo. | NO | REUSE. Sin brecha actual; proteger mediante validación. |
| IR0-003 | SCRIPT_PRODUCT | Trazar cada requisito v2 contra P-08 y evidencia de repositorio. | MISSING | NONE | registry / matriz de trazabilidad | R1.1 | R1-M1 | P-08 integrada | R1_GATE | Este documento como artefacto canónico. | NO | Materializado por R1-M1. |
| IR1-001 | SCRIPT_PRODUCT | Representar PhenomenonResearchPack como artefacto diferenciado del ResearchPack genérico. | PARTIAL | `schemas/research_pack.json` | contrato / schema | R1.2 | R1-M2 | IR0 | R1_GATE | Contrato PhenomenonResearchPack validado sin duplicar autoridad. | NO | EXTEND. Versionar ResearchPack sin duplicar conceptos válidos. |
| IR1-002 | SCRIPT_PRODUCT | Representar alcance exacto, usos editoriales previstos y mapa de claims por criticidad. | PARTIAL | `schemas/research_pack.json`; `schemas/claims_ledger.json` | contrato / schema | R1.2 | R1-M2 | IR1-001 | R1_GATE | Tipificación central/secundario/sensible/controvertido ligada al uso. | NO | EXTEND. |
| IR1-003 | SCRIPT_PRODUCT | Separar hechos, interpretaciones e hipótesis. | ALREADY_IMPLEMENTED | `schemas/research_pack.json` | contrato / schema | R1.2 | R1-M2 | Ninguna | R1_GATE | Sin brecha estructural; demostración real en IR-7. | NO | REUSE. |
| IR1-004 | SCRIPT_PRODUCT | Representar explicaciones rivales, contraejemplos, consenso, desacuerdo e incertidumbre. | PARTIAL | `schemas/research_pack.json`; `schemas/refined_thesis.json` | contrato / schema | R1.2 | R1-M2 | IR1-001 | R1_GATE | Taxonomía de desacuerdo y cierre. | NO | EXTEND. Ampliar fields y reglas semánticas. |
| IR1-005 | SCRIPT_PRODUCT | Representar acceso, independencia entre fuentes, cobertura, vacíos y condiciones de reapertura. | PARTIAL | `schemas/research_pack.json`; `schemas/source_access_and_evidence_report.json` | contrato / schema | R1.2 | R1-M2 | IR1-001; P-07 | R1_GATE | provenance, independence_group y triggers de reapertura. | NO | EXTEND. Depende de P-07 para reapertura granular. |
| IR1-006 | SCRIPT_PRODUCT | Distinguir demostrado, plausible y especulativo y emitir suficiencia por uso previsto. | MISSING | NONE | contrato / gate semántico | R1.2 | R1-M2 | IR4 | R1_GATE | Estado semántico por afirmación/uso. | NO | Diseñar contrato y gate semántico. |
| IR1-007 | SCRIPT_PRODUCT | Crear WorkResearchDossier por obra con identificación exacta y versión consultada. | MISSING | NONE | contrato / schema | R1.2 | R1-M3 | IR0 | R1_GATE | Contrato WorkResearchDossier versionado. | NO | No existe schema; fragmentos en narrative_human_analysis y material_curation. |
| IR1-008 | SCRIPT_PRODUCT | Incluir lifecycle, decisiones observables, conflictos, consecuencias y contexto interno. | PARTIAL | `schemas/narrative_human_analysis.json` | contrato / schema | R1.2 | R1-M3 | IR1-007; IR2 | R1_GATE | Integración dentro del dossier y lifecycle explícito. | NO | EXTEND. |
| IR1-009 | SCRIPT_PRODUCT | Incluir relación con pregunta/tesis, qué demuestra/no demuestra e interpretación rival. | PARTIAL | `schemas/narrative_human_analysis.json` | contrato / schema | R1.2 | R1-M3 | IR1-007 | R1_GATE | Referencia del análisis desde el dossier. | NO | EXTEND. |
| IR1-010 | SCRIPT_PRODUCT | Incluir claims permitidos, limitados y bloqueados por obra. | PARTIAL | `schemas/source_access_and_evidence_report.json`; `schemas/claims_ledger.json` | contrato / schema | R1.2 | R1-M3 | IR1-007; IR4 | R1_GATE | Vínculo canónico claims ledger → dossier de obra. | NO | EXTEND. |
| IR1-011 | SCRIPT_PRODUCT | Incluir riesgo de sobreinterpretación, función editorial candidata, localizadores, pendientes y confianza. | PARTIAL | `schemas/narrative_human_analysis.json`; `schemas/material_curation.json` | contrato / schema | R1.2 | R1-M3 | IR1-007 | R1_GATE | Campos consolidados en dossier. | NO | EXTEND. |
| IR1-012 | SCRIPT_PRODUCT | Incluir suficiencia para uso previsto y referencia a auditoría independiente de fidelidad. | MISSING | NONE | contrato / schema + auditoría | R1.2 | R1-M3 | IR1-007; IR7 | R1_GATE | Vínculo dossier → fidelity audit y suficiencia por obra. | NO | Referencias obligatorias y estados. |
| IR1-013 | SCRIPT_PRODUCT | Evaluar fuentes por relación con objeto, autoridad del claim, acceso, independencia, vigencia y localizador. | PARTIAL | `schemas/source_access_and_evidence_report.json`; `schemas/research_pack.json` | contrato / schema | R1.2 | R1-M2 | IR1-001 | R1_GATE | Modelo claim-dependent e independence_group. | NO | EXTEND. |
| IR1-014 | SCRIPT_PRODUCT | Representar riesgo de traducción/transcripción, limitaciones y uso permitido. | PARTIAL | `schemas/source_access_and_evidence_report.json` | contrato / schema | R1.3 | R1-M4 | IR3 | R1_GATE | Provenance derivada con riesgo específico. | NO | EXTEND. |
| IR1-015 | SCRIPT_PRODUCT | Distinguir FUENTE_ORIGINAL, TRANSCRIPCIÓN, TRADUCCIÓN, RESUMEN, RESEÑA y CITA_INDIRECTA. | MISSING | NONE | schema / enum | R1.3 | R1-M4 | IR3 | R1_GATE | Enum canónico y reglas de derivación. | NO | No existe enumeración en schemas activos. |
| IR1-016 | SCRIPT_PRODUCT | Impedir que una representación derivada sustituya automáticamente la fuente original. | PARTIAL | `.agent/rules/02_reglas_notebooklm.md`; `docs/reconciliation/p08/.../consolidado...` | gate / validación | R1.3 | R1-M4 | IR1-015 | R1_GATE | Validación de provenance y bloqueo operativo. | NO | EXTEND. Regla documental sin gate. |
| IR2-001 | SCRIPT_PRODUCT | Representar estados DISCOVERED, SCREENED, FINALIST, FINAL_SELECTED, EXCLUDED e INVALIDATED. | MISSING | NONE | schema / lifecycle | R1.3 | R1-M5 | IR1-007 | R1_GATE | Lifecycle y transición versionada. | NO | material_curation usa candidates/selected/excluded sin lifecycle completo. |
| IR2-002 | SCRIPT_PRODUCT | Tratar ANCHOR_WORK como condición de entrada, no selección automática. | PARTIAL | `schemas/episode_brief.json`; documentación P-08 | schema / regla | R1.3 | R1-M5 | IR2-001 | R1_GATE | Regla y caso negativo. | NO | EXTEND. |
| IR2-003 | SCRIPT_PRODUCT | Tratar REOPENED como transición, no estado principal. | MISSING | NONE | schema / transición | R1.3 | R1-M5 | IR2-001; P-07 | R1_GATE | Transición y lineage. | NO | Depende de P-07. |
| IR2-004 | SCRIPT_PRODUCT | Aplicar profundidad progresiva distinta por estado. | MISSING | NONE | schema / validación | R1.3 | R1-M5 | IR2-001; IR1-007 | R1_GATE | Reglas de completitud por estado. | NO | No existe policy que condicione campos por lifecycle. |
| IR2-005 | SCRIPT_PRODUCT | Permitir profundización anticipada cuando una duda crítica bloquea screening. | MISSING | NONE | contrato / schema + lifecycle + gate | R1.3 | R1-M5 | SP-IR0-CRITICAL_WORK_DOUBT; IR2-001; WorkResearchDossier; lifecycle | R1.3; R1.7; R1_GATE; B5_I1_GATE; B5_I2_GATE | Criterios de activación/no activación, invalidación y rutas de retorno materializados. | NO | DECISIÓN SP-IR0-CRITICAL_WORK_DOUBT. Sin resumir ni reinterpretar. |
| IR2-006 | SCRIPT_PRODUCT | Aplicar rango normal 5–8 candidatas en screening. | PARTIAL | `.agent/skills/skill_research_tema_y_obras.md`; documentación P-08 | schema / gate | R1.3 | R1-M5 | IR2-001 | R1_GATE | Rango integrado sin rigidizar excepciones. | NO | EXTEND. |
| IR2-007 | SCRIPT_PRODUCT | Aplicar selección final de 3–5 obras sustantivas con función diferenciada. | PARTIAL | `schemas/material_curation.json`; `.agent/skills/skill_curation_obras.md` | schema / gate | R1.3 | R1-M5 | IR2-001; IR1-007 | R1_GATE | Gate de curación reforzado. | NO | EXTEND. |
| IR2-008 | SCRIPT_PRODUCT | Representar las ocho responsabilidades de investigación multilínea sin prescribir agentes. | MISSING | NONE | registry / capability mapping | R1.5 | R1-M9 | IR1; IR6 | R1_GATE | Mapa funcional→técnico neutral. | NO | No prescribir un agente por responsabilidad. |
| IR3-001 | SCRIPT_PRODUCT | Conservar vídeo original como fuente y transcripción como derivada. | PARTIAL | `.agent/rules/02_reglas_notebooklm.md`; `workspace/CONTRATO_NOTEBOOKLM.md` | contrato / provenance | R1.3 | R1-M4 | IR1-015 | R1_GATE | Lineage de fuente derivada. | NO | EXTEND. |
| IR3-002 | SCRIPT_PRODUCT | Conservar vídeo, versión, idioma, timestamps y método de obtención. | MISSING | NONE | contrato / schema | R1.3 | R1-M4 | IR1-015 | R1_GATE | Contrato de fuente audiovisual con metadata obligatoria. | NO | No existe contrato completo. |
| IR3-003 | SCRIPT_PRODUCT | Distinguir transcripción oficial, del creador, automática y manual. | MISSING | NONE | schema / enum | R1.3 | R1-M4 | IR3-002 | R1_GATE | Tipo y provenance. | NO | No existe enum técnico. |
| IR3-004 | SCRIPT_PRODUCT | Bloquear cita exacta desde transcripción automática sin revisión. | MISSING | NONE | gate / validación | R1.3 | R1-M4 | IR3-003 | R1_GATE | Regla ejecutable y caso negativo. | NO | No existe gate específico. |
| IR3-005 | SCRIPT_PRODUCT | Verificar errores materiales de transcripción contra audio o vídeo. | MISSING | NONE | workflow / gate | R1.3 | R1-M4 | IR3-002 | R1_GATE | Ruta de revisión y evidencia. | NO | No existe flujo/gate demostrado. |
| IR3-006 | SCRIPT_PRODUCT | No sustituir original por traducción cuando importa formulación exacta. | MISSING | NONE | contrato / regla | R1.3 | R1-M4 | IR1-015 | R1_GATE | Criterio de exactitud y provenance. | NO | No existe control específico. |
| IR3-007 | SCRIPT_PRODUCT | Tratar reseñas/resúmenes/comentarios como insuficientes para probar contenido de obra. | PARTIAL | `docs/reconciliation/p08/...`; reglas editoriales heredadas | schema / gate | R1.3 | R1-M4 | IR1-015 | R1_GATE | Uso permitido por tipo de fuente. | NO | EXTEND. Sin gate técnico. |
| IR3-008 | YOUTUBE_ADAPTATION | Priorizar fuentes oficiales/primarias para políticas y funcionamiento de YouTube. | PARTIAL | `config/palabras_riesgo_youtube.md`; docs y contratos YA | registry / policy | R1.3 | R1-M4 | IR1-013 | R1_GATE | Política de source authority ejecutable. | NO | EXTEND. |
| IR3-009 | SCRIPT_PRODUCT | Activar multilingüismo por necesidad, sin cuota universal. | MISSING | NONE | contrato / provenance + evaluación de fuentes + suficiencia + gate | R1.3 | R1-M4 | SP-IR0-MULTILINGUAL_RESEARCH_THRESHOLD; IR1; source provenance; ResearchStopDecision | R1.3; R1.7; R1_GATE; B5_I1_GATE; B5_I2_GATE | Criterios de activación/no activación, invalidación y rutas de retorno materializados. | NO | DECISIÓN SP-IR0-MULTILINGUAL_RESEARCH_THRESHOLD. Sin resumir ni reinterpretar. |
| IR4-001 | SCRIPT_PRODUCT | Evaluar cada fuente de forma dependiente del claim, no con ranking universal. | PARTIAL | `schemas/source_access_and_evidence_report.json`; critical_claim_assessments | contrato / gate | R1.4 | R1-M6 | IR1-013 | R1_GATE | Modelo por claim y source authority. | NO | EXTEND. |
| IR4-002 | SCRIPT_PRODUCT | Representar CLAIM_ALLOWED, CLAIM_LIMITED y CLAIM_BLOCKED. | PARTIAL | `schemas/source_access_and_evidence_report.json`; `schemas/claims_ledger.json` | schema / enums | R1.4 | R1-M6 | IR1-010 | R1_GATE | Estados normalizados por claim. | NO | EXTEND. Nombres no unificados (allowed/limited/prohibited). |
| IR4-003 | SCRIPT_PRODUCT | Crear ResearchStopDecision por fenómeno. | MISSING | NONE | contrato / schema | R1.4 | R1-M6 | IR1-001 | R1_GATE | Contrato RSD por fenómeno. | NO | No existe contrato. |
| IR4-004 | SCRIPT_PRODUCT | Crear ResearchStopDecision por obra. | MISSING | NONE | contrato / schema | R1.4 | R1-M6 | IR1-007 | R1_GATE | Contrato RSD por dossier. | NO | No existe contrato. |
| IR4-005 | SCRIPT_PRODUCT | Crear ResearchStopDecision por claim material. | MISSING | NONE | contrato / schema + ClaimsLedger + gate | R1.4 | R1-M6 | SP-IR0-MATERIAL_CLAIM_THRESHOLD; ClaimsLedger; ResearchStopDecision | R1.4; R1.7; R1_GATE; B5_I1_GATE; B5_I2_GATE | Materialidad, estados por uso, invalidación y rutas de retorno materializados. | NO | DECISIÓN SP-IR0-MATERIAL_CLAIM_THRESHOLD. Sin resumir ni reinterpretar. |
| IR4-006 | SCRIPT_PRODUCT | Crear ResearchStopDecision para paquete agregado. | MISSING | NONE | contrato / schema | R1.4 | R1-M6 | IR4-003..005 | R1_GATE | Cierre agregado. | NO | No existe contrato. |
| IR4-007 | SCRIPT_PRODUCT | Representar SUFFICIENT_FOR_INTENDED_USE, LIMITED_BUT_USABLE, MORE_RESEARCH_REQUIRED y BLOCKED_BY_EVIDENCE. | PARTIAL | `schemas/source_access_and_evidence_report.json`; consolidado define estados | schema / enums | R1.4 | R1-M6 | IR4-003..006 | R1_GATE | Enums y transiciones canónicos. | NO | EXTEND. No implementados canónicamente. |
| IR4-008 | SCRIPT_PRODUCT | Resolver contradicción como resuelta, controversia, limitada, rival, investigación adicional o bloqueo. | PARTIAL | `schemas/research_pack.json` contradictions; `schemas/refined_thesis.json` rival_interpretations | schema / disposition | R1.4 | R1-M7 | IR4-001 | R1_GATE | Disposition canónica completa. | NO | EXTEND. |
| IR4-009 | SCRIPT_PRODUCT | Impedir selección silenciosa de la fuente más conveniente. | MISSING | NONE | gate / auditoría | R1.4 | R1-M7 | IR4-008; IR7 | R1_GATE | Evidencia de comparación y justificación; caso negativo. | NO | No existe gate o auditoría específica. |
| IR5-001 | SCRIPT_PRODUCT | Consultar memoria en los cinco momentos mínimos definidos. | MISSING | NONE | workflow / puntos de consulta | R1.5 | R1-M8 | IR5-002 | R1_GATE | Integración por hitos. | NO | No hay workflow activo demostrado. |
| IR5-002 | SCRIPT_PRODUCT | Representar memoria semántica multidimensional de producto guion. | MISSING | NONE | contrato / schema + store | R1.5 | R1-M8 | P-07 | R1_GATE | Contrato y almacenamiento canónico. | NO | No existe schema/store canónico. |
| IR5-003 | SCRIPT_PRODUCT | Incluir obras, escenas, funciones, orden, combinación, claims, interpretaciones, especialistas y fuentes. | MISSING | NONE | contrato / schema | R1.5 | R1-M8 | IR5-002 | R1_GATE | Dimensiones definidas. | NO | No existe representación canónica. |
| IR5-004 | SCRIPT_PRODUCT | Emitir seis decisiones de novedad/reutilización. | MISSING | NONE | schema / enums + gate | R1.5 | R1-M8 | IR5-002 | R1_GATE | Decisión semántica y rutas. | NO | No existen enums ni gate. |
| IR5-005 | SCRIPT_PRODUCT | Usar memoria como evidencia, sin bloqueo automático. | PARTIAL | Principio presente en consolidado y plan | interfaz / contrato | R1.5 | R1-M8 | IR5-002 | R1_GATE | Interfaz no autoritativa. | NO | EXTEND. Falta separación evidencia/decisión. |
| IR5-006 | CHANNEL_INTELLIGENCE | Mantener territorios editoriales bajo CHANNEL_INTELLIGENCE. | ALREADY_IMPLEMENTED | `config/active_editorial_profile.json`; topic belonging policy; P-08 | registry / policy | R1.5 | R1-M8 | Ninguna | NONE | Sin brecha de autoridad. | NO | REUSE. Conservar. |
| IR6-001 | SCRIPT_PRODUCT | Activar responsabilidades especializadas de forma adaptativa por riesgo y naturaleza del claim. | MISSING | NONE | registry / policy | R1.5 | R1-M9 | IR1; IR4 | R1_GATE | Capability routing neutral. | NO | No existe policy/registry de activación especializada. |
| IR6-002 | SCRIPT_PRODUCT | Exigir pregunta, alcance, fuentes, método, hallazgos, rivales, límites, incertidumbre y conflictos de interés. | MISSING | NONE | contrato / schema | R1.5 | R1-M9 | IR6-001 | R1_GATE | Contrato de contribución especialista. | NO | No existe contrato. |
| IR6-003 | SCRIPT_PRODUCT | Declarar claims que el especialista puede y no puede sostener. | MISSING | NONE | contrato / schema + claims | R1.5 | R1-M9 | IR6-002; IR4 | R1_GATE | Vínculo con claims ledger. | NO | No existe contrato. |
| IR6-004 | SCRIPT_PRODUCT | Mantener lista de especialidades abierta y no prescribir agentes. | OUT_OF_SCOPE_TECHNICAL | NONE | nota / decisión técnica | R1.5 | R1-M9 | IR6-001 | R1_GATE | No catálogo cerrado; resolver en diseño técnico. | NO | Decisión funcional ya existe en el plan v2. |
| IR6-005 | SCRIPT_PRODUCT | Impedir que especialista sustituya a SCRIPT_PRODUCT o emita suficiencia final. | PARTIAL | `config/responsibility_registry.json`; consolidado define autoridad | schema / regla de autoridad | R1.5 | R1-M9 | IR6-002 | R1_GATE | Gate sobre promoción de conclusión especialista. | NO | EXTEND. |
| IR7-001 | SCRIPT_PRODUCT | Ejecutar vertical real TOPIC_FIRST hasta tesis refinada y auditorías. | MISSING | NONE | ejecución / evidencia operacional | R1.7 | R1-M11 | IR1-IR6 | R1_GATE | Vertical real ejecutada solo tras autorización expresa. | NO | Requiere autorización separada; no es suite técnica. |
| IR7-002 | SCRIPT_PRODUCT | Separar auditorías de suficiencia, fidelidad, interpretación, claims/fuentes, curación y paquete final. | PARTIAL | `schemas/semantic_sufficiency_audit.json`; `schemas/b5_i2_semantic_sufficiency_audit.json`; `schemas/final_editorial_audit.json` | auditoría / schema | R1.6 | R1-M10 | IR1-012; IR4 | R1_GATE | Auditorías diferenciadas o dimensiones explícitas. | NO | EXTEND. Faltan fidelidad y paquete de investigación. |
| IR7-003 | SCRIPT_PRODUCT | Garantizar auditor distinto del productor y sin corrección silenciosa. | PARTIAL | `schemas/b5_i2_semantic_sufficiency_audit.json` (producer/auditor actors; independence_result) | auditoría / schema | R1.6 | R1-M10 | IR7-002 | R1_GATE | Independencia en todas las auditorías. | NO | EXTEND. No demostrado en operación real. |
| IR7-004 | SCRIPT_PRODUCT | Emitir APPROVED, REQUEST_CHANGES o BLOCK con evidencia y limitaciones. | PARTIAL | `schemas/b5_i2_semantic_sufficiency_audit.json`; `schemas/semantic_sufficiency_audit.json` | auditoría / schema | R1.6 | R1-M10 | IR7-002 | R1_GATE | Enum de decisión normalizado. | NO | EXTEND. |
| IR7-005 | SCRIPT_PRODUCT | Devolver defectos al origen correcto mediante rutas de corrección. | PARTIAL | `schemas/correction_routing_policy.json`; `src/core/invalidation.py` | workflow / rutas | R1.6 | R1-M10 | P-07; IR7-002 | R1_GATE | Rutas por artefacto completadas. | NO | EXTEND. P-07 y cobertura de investigación abiertos. |
| IR7-006 | SCRIPT_PRODUCT | Cubrir casos positivos, rechazados, bloqueados y LIMITED_BUT_USABLE. | MISSING | NONE | fixture / benchmark | R1.7 | R1-M11 | IR1-IR6 | R1_GATE | Suite de casos semánticos y evaluación. | NO | No existe suite completa. |
| IR7-007 | SCRIPT_PRODUCT | Cubrir casos de fuente derivada, transcripción, traducción, lectura rival, reutilización, especialista e invalidación. | MISSING | NONE | fixture / benchmark | R1.7 | R1-M11 | IR3; IR5; IR6 | R1_GATE | Casos negativos y de borde. | NO | No existe suite integral. |
| IR7-008 | SCRIPT_PRODUCT | Demostrar productor y auditor independientes en ejecución real. | MISSING | NONE | ejecución / evidencia operacional | R1.6 | R1-M10 | IR7-001..007 | R1_GATE | Evidencia operacional con productor y auditor distintos. | NO | Requiere vertical autorizada. |
| IRA-001 | SCRIPT_PRODUCT | Mantener SOURCE_GROUNDED_RESEARCH_ADAPTER opcional, agnóstico y no autoritativo. | PARTIAL | `workspace/CONTRATO_NOTEBOOKLM.md`; reglas NotebookLM | contrato / interfaz | R1.6 | R1-M11 | IR1 | R1_GATE | Adapter contract opcional. | NO | EXTEND. Evitar que NotebookLM sea ruta obligatoria. |
| IRA-002 | SCRIPT_PRODUCT | Impedir que el adaptador sea memoria canónica, gate obligatorio o autoridad de veracidad. | PARTIAL | Plan y consolidado lo declaran | policy / gate | R1.6 | R1-M11 | IRA-001 | R1_GATE | Policy/gate de neutralidad y tests. | NO | EXTEND. No existe enforcement técnico. |
| IRA-003 | SCRIPT_PRODUCT | Mantener SCRIPT_PRODUCT como owner de suficiencia editorial. | ALREADY_IMPLEMENTED | `docs/ALCANCE_Y_COORDINACION_EQUIPOS.md`; `config/responsibility_registry.json`; P-08 | registry / policy | R1.6 | R1-M10 | Ninguna | NONE | Sin brecha de autoridad declarativa. | NO | REUSE. Conservar. |
| IRA-004 | SCRIPT_PRODUCT | Separar aprobación funcional, activación técnica y autorización interequipos de producto. | PARTIAL | `plans/001_CONTROL_OPERATIVO.md`; schemas de approvals; P-08 | registry / workflow | R1.6 | R1-M11 | IR1-IR7 | R1_GATE | Estados separados en contratos y gates. | NO | EXTEND. |

## Decisiones definitivas de SCRIPT_PRODUCT

Las tres decisiones funcionales están resueltas (`RESOLVED_FUNCTIONALLY_TECHNICAL_IMPLEMENTATION_MISSING` en la hoja 4 de la matriz IR-0). El texto íntegro se conserva en la matriz IR-0 (hojas 6, 7 y 8) y NO se reinterpreta ni se resume aquí.

| decision_id | requirement | componentes afectados | gates finales | misión prevista | full_text_location |
|---|---|---|---|---|---|
| `SP-IR0-CRITICAL_WORK_DOUBT` | `IR2-005` | WorkResearchDossier; lifecycle; profundización anticipada delimitada; evidencia; invalidación; rutas de retorno | `R1.3`; `R1.7`; `R1_GATE`; `B5_I1_GATE` (R2); `B5_I2_GATE` (R3) | R1-M5 | Hoja 6 del xlsx IR-0 (`FULL_TEXT_PRESERVED_IN_D1_CRITICAL_DOUBT`) |
| `SP-IR0-MULTILINGUAL_RESEARCH_THRESHOLD` | `IR3-009` | provenance de fuentes; original/transcripción/traducción; evaluación de fuentes; suficiencia; limitaciones | `R1.3`; `R1.7`; `R1_GATE`; `B5_I1_GATE` (R2); `B5_I2_GATE` (R3) | R1-M4 | Hoja 7 del xlsx IR-0 (`FULL_TEXT_PRESERVED_IN_D2_MULTILINGUAL`) |
| `SP-IR0-MATERIAL_CLAIM_THRESHOLD` | `IR4-005` | ClaimsLedger; ResearchStopDecision; suficiencia por uso; invalidación; revalidación | `R1.4`; `R1.7`; `R1_GATE`; `B5_I1_GATE` (R2); `B5_I2_GATE` (R3) | R1-M6 | Hoja 8 del xlsx IR-0 (`FULL_TEXT_PRESERVED_IN_D3_MATERIAL_CLAIM`) |

Requisito de integridad: la misión que materialice cada decisión debe implementarla de forma íntegra (criterios de activación, no activación, invalidación y rutas de retorno) sin resumir ni reinterpretar, y vincularla con la unidad y el gate señalados.

## Estado agregado (fuente: hoja 1 de la matriz IR-0)

```text
REQUIREMENT_COUNT: 68
IMPLEMENTED_COUNT: 4
PARTIAL_COUNT: 31
MISSING_COUNT: 32
OUT_OF_SCOPE_TECHNICAL: 1
FUNCTIONAL_DECISIONS_REQUIRED: 0
IMPLEMENTATION_AUTHORIZED: R1_M1_M2_AND_M3_CONTRACT_SCOPE_ONLY
```

## Posibles duplicaciones a evitar

1. `PhenomenonResearchPack` vs `ResearchPack` genérico (`IR1-001`): versionar/extender, no duplicar autoridad.
2. Estados de claim (`IR4-002`): `allowed/limited/prohibited` de `source_access_and_evidence_report` vs `CLAIM_ALLOWED/CLAIM_LIMITED/CLAIM_BLOCKED` — normalizar, no crear un tercer conjunto.
3. `WorkResearchDossier` vs fragmentos en `narrative_human_analysis.json` y `material_curation.json` (`IR1-007`): consolidar por referencia, no duplicar campos.
4. Memorias (`IR5-002`): no reutilizar superficies heredadas de NotebookLM como almacén canónico.
5. Adapter (`IRA-001/002`): `SOURCE_GROUNDED_RESEARCH_ADAPTER` debe ser interfaz opcional; las reglas heredadas de NotebookLM no se convierten en gate obligatorio.
6. Auditorías (`IR7-002..004`): normalizar decision enum y dimensiones sobre las auditorías existentes, no crear esquemas paralelos sin declarar `REUSE/EXTEND/REPLACE/RETIRE`.

La decisión `REUSE/EXTEND/REPLACE/RETIRE` detallada se toma en cada misión R1 correspondiente; esta matriz solo la anticipa en `resolution_hint`.

## Cierre de R1-M2

R1-M2 fue ejecutada con autorización explícita para IR1-001, IR1-002, IR1-003, IR1-004, IR1-005, IR1-006 e IR1-013.

- IR1-001, IR1-002, IR1-004, IR1-005 e IR1-013: contratos extendidos en los schemas existentes, sin crear una autoridad paralela.
- IR1-003: REUSE; `research_pack.json` ya separa `facts`, `interpretations` e `hypotheses`.
- IR1-004: `research_pack.json` incorpora análisis rival con consenso, desacuerdo, contraejemplo e incertidumbre; `refined_thesis.json` permanece REUSE.
- IR1-006: se materializa el estado semántico por claim y la dependencia `DEFERRED_TO_R1_M6`; no se valida suficiencia funcional ni se abre R1-M6.
- `src/core/contract_validation.py` solo se extendió para referencias cruzadas que JSON Schema no puede resolver por sí solo.
- Evidencia de validación: `18 passed`, `162 subtests passed` en los tests dirigidos de schemas y contratos.

## Límites

- No se implementaron scripts, agentes, prompts ni skills; R1-M2 solo extendió contratos, schemas y validación estructural/cruzada.
- Los artefactos IR-0 aprobados no se alteraron.
- R1-M2 queda `COMPLETED` con revisión del OWNER `APPROVED` y resultado `PASS`; IR4/R1-M6 conserva la responsabilidad de suficiencia funcional.
- R1-M6 no fue abierta.

## Cierre de R1-M3

R1-M3 fue ejecutada con autorización explícita para IR1-007, IR1-008, IR1-009, IR1-010, IR1-011 e IR1-012.

- NEW justificado: `schemas/work_research_dossier.json`; no existía contrato que consolidara la identificación/versionado por obra y sus referencias sin crear una segunda autoridad.
- REUSE: `narrative_human_analysis.json`, `material_curation.json`, `claims_ledger.json` y `source_access_and_evidence_report.json` se conservan como fuentes; el dossier los referencia y no copia su contenido.
- IR1-008, IR1-009 e IR1-011 se resuelven mediante referencias validadas a `NarrativeHumanAnalysis` del mismo episodio, investigación, evidencia y obra.
- IR1-010 conserva los claims en `ClaimsLedger`; las listas del dossier son candidatas con `REPRESENTATION_ONLY_IR4_PENDING`, sin emitir una decisión IR4.
- IR1-012 solo representa suficiencia no funcional y una auditoría de fidelidad nula con dependencia `DEFERRED_TO_R1_M10_R1_M11`; no declara auditoría independiente implementada ni aprobada.
- Evidencia de validación: `29 passed`, `166 subtests passed` en los tests dirigidos de schemas y contratos.

R1-M3 queda `COMPLETED_PENDING_REVIEW`. R1-M4, R1-M5 y R1-M6 permanecen sin abrir.


## Addendum P7 ? Reconciliacion contra evidencia actual

Este addendum no reescribe los estados historicos de la matriz IR-0 ni convierte evidencia tecnica en aprobacion funcional. Distingue el baseline historico de los hitos tecnicos demostrados en PLAN 007 y del estado vivo actual.

| capa | estado reconciliado | evidencia | limite |
|---|---|---|---|
| Historico de la matriz | Se conserva sin reescritura | filas IR-0 a IR-7 existentes | No representa por si solo el estado vivo posterior |
| Completado tecnicamente | P2/P3/P4/P5/P6 controlados por PLAN 007 | suite amplia, P6-A, P6-B, cross-registry y semantic assurance | No equivale a aprobacion funcional ni uso productivo |
| Estado vivo | `R1_IN_PROGRESS`; `PLAN_007_FUNCTIONAL_APPROVAL: NO` | `plans/001_CONTROL_OPERATIVO.md` | Requiere revision del OWNER para cualquier siguiente autorizacion |
| Siguiente accion | `OWNER_REVIEW_OF_PLAN_007_P7_EVIDENCE` | control operativo reconciliado en P7 | R2 y ejecucion real siguen sin autorizacion |

Los artefactos y pruebas de la implementacion permanecen en el worktree sin commit ni push por instruccion de la mision.
