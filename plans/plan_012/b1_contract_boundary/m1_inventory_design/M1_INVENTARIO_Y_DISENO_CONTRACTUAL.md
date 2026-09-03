# PLAN012 B1 M1 — Inventario y diseño contractual

## 1. Baseline y alcance de esta misión

**Misión:** `PLAN012_M1_INVENTORY_CONTRACT_DESIGN`
**Naturaleza:** auditoría, inventario, reconciliación y diseño documental.
**Estado:** `CLOSED_OWNER_APPROVED`

Este informe parte del borrador preliminar existente, fue contrastado con el
repositorio real y constituye la entrega documental de M1 aprobada por el
OWNER. M2 también queda cerrada; M3 permanece no autorizada.

Esta misión no ejecuta una capability de producto, no invoca IA y no usa
`MissionAuthorization` de runtime. Se conserva deliberadamente:

```text
CURRENT_MISSION: NONE
CURRENT_MISSION_EXECUTION_BUNDLE: NONE
REAL_AI_EXECUTION: NO
AUTHORIZED_FOR_PRODUCT_USE: NO
P2_REAL_EXECUTION_NOW: NO
```

El precheck realizado antes de la auditoría encontró:

| Control | Resultado | Evidencia |
|---|---|---|
| Rama | `master` | salida de `git branch --show-current` |
| HEAD | `67a86ce09381bbc8f8229f4d42cad8f390d2eb6b` | salida de `git rev-parse HEAD` |
| Estado previo | `M plans/001_CONTROL_OPERATIVO.md`; `?? .agents/skills/tests-validacion-cierre/`; `?? plans/plan_012/` | salida de `git status --short` |
| Protección | `tests-validacion-cierre/SKILL.md` permanece sin modificación | comparación de estado y diff |
| Misión activa previa | `NONE` | `plans/001_CONTROL_OPERATIVO.md` |
| Bundle activo previo | `NONE` | `plans/001_CONTROL_OPERATIVO.md` |
| M1/M2 previo | `DEFINED_NOT_AUTHORIZED` | control operativo, PLAN012 y B1 |

Se inspeccionaron completos los documentos de gobernanza PLAN012, el contrato
de frontera B1, el control operativo, la referencia cerrada de PLAN011 M3, el
consumer real de B5-I3 y las fuentes canónicas encontradas mediante búsqueda:
schemas, validadores, storage, servicio, ejecución de roles, prompts,
registries, skills, workflows y tests del harness.

### Hallazgo de gobernanza

`schemas/mission_authorization_contract.json` exige al menos una capability y
un role. `src/core/mission_authorization.py` y
`src/application/authority.py` verifican además identidad de misión, bundle y
estado vivo. `config/capability_registry.json` solo ofrece capabilities de
producto o auditoría de producto, y `config/responsibility_registry.json` no
contiene una unidad de misión documental M1. El patrón PLAN011 M3 en
`plans/plan_011/m3_b5_i3/mission_contract.json`,
`mission-authorization.json` y `authority.json` es de ejecución de
`NARRATIVE_ARCHITECTURE`, no de inventario.

Conclusión: crear una capability, role o bundle artificial para M1 habría
deformado el modelo de autorización. M1 se materializa únicamente mediante
este informe y la actualización documental del estado permitido por el
OWNER.

## 2. Criterio de búsqueda

Se aplicó:

```text
SEARCH BEFORE CREATE
REUSE → EXTEND → MOVE_RECONCILE → CREATE_ONLY_IF_GAP
SOFTWARE → IA → SOFTWARE
```

`REUSE` significa que existe una responsabilidad y una validación que ya
pueden cumplir el objetivo sin cambiar su significado. `EXTEND` significa que
la pieza es canónica pero carece de campos, estado o binding necesario.
`MOVE_RECONCILE` significa que la pieza contiene capacidad útil, pero mezcla
investigación con una decisión narrativa o asigna autoridad al consumidor
equivocado. `LEGACY_COMPAT` conserva una superficie cerrada o histórica sin
convertirla en el contrato V2. `CREATE_ONLY_IF_GAP` queda condicionado a una
verificación de M2; no autoriza creación durante M1.

## 3. Inventario real

| path | artifact/responsibility | current_producer | current_consumers | current_scope | useful_existing_capability | conflict_or_gap | decision | evidence | deferred_M2_action |
|---|---|---|---|---|---|---|---|---|---|
| `schemas/research_pack.json` | paquete de investigación | `RESEARCH_AND_CURATION` | B5-I3, gates y validators | Research/transversal | facts, interpretations, hypotheses, contradictions, coverage, source registry, limitations y provenance | `narrative_opportunities` y `editorial_uses` mezclan Research con uso narrativo; falta stage V2 explícito | EXTEND | schema; `src/core/contract_validation.py::validate_research_pack`; `src/ai/execution.py::M3_INPUT_SCHEMA_BY_KIND` | separar campos narrativos, conservar restricciones y añadir binding/versiones solo donde sea necesario |
| `schemas/claims_ledger.json` | claims trazables y su estado | Research/guion | B5-I3 y validadores | transversal | referencias de fuente, materialidad, verificación y provenance | `script_version` y `script_location` acoplan el ledger al script antes de que exista el producto final | EXTEND | schema; `src/core/contract_validation.py::validate_claims_ledger`; `tests/harness/test_plan011_m3_b5_i3.py` | hacer explícita la etapa de Research y mantener una ruta LEGACY_COMPAT para el ledger ligado a script |
| `schemas/source_access_and_evidence_report.json` | acceso, evidencia y restricciones | Research | B5-I3, gates y auditorías | Research/transversal | allowed/limited/prohibited analyses, excluded claims, disclosures, confidence y propagación | no existe en la superficie inspeccionada un binding completo request→fetch→recovery artifact→claim | EXTEND | schema; `src/core/contract_validation.py`; `.agent/skills/skill_research_tema_y_obras.md`; `src/core/research_adapter.py` | enlazar recuperación controlada por Software sin permitir que IA eleve una fuente a verified |
| `schemas/work_research_dossier.json` | investigación por obra y fidelidad | Research/curation | B5-I2/B5-I3, auditorías | Research | stages, locators, claims, analysis refs, fidelity audit y stop decision refs | `candidate_editorial_function_analysis_ref` introduce función narrativa; fidelidad, selección y suficiencia no están totalmente ortogonales | EXTEND + MOVE_RECONCILE | schema; `src/core/contract_validation.py`; `schemas/independent_research_audit.json` | separar referencias de evidencia/fidelidad de la futura función narrativa y definir sus transiciones |
| `schemas/work_lifecycle.json` | ciclo de vida de candidatas | Research/curation | workflow y decisiones | Research/transversal | transiciones con evidencia, versiones de input, authority role, lineage e invalidation | screening/final selection contienen política de producto y no deben convertirse en mega-estado de fidelidad o suficiencia | EXTEND | schema; `.agent/workflows/01_pipeline_episodio.md` | conservar lifecycle y extraer dimensiones ortogonales de selección, fidelidad y suficiencia |
| `schemas/research_stop_decision.json` | suficiencia semántica y ruta de retorno | Research | gates, workflow y consumidores posteriores | Research | `SUFFICIENT_FOR_INTENDED_USE`, limitaciones, contradicciones, invalidators y return route | no debe cargar por sí solo el contador o límite operacional de iteraciones | REUSE | schema; `src/core/contract_validation.py::validate_research_stop_decision`; workflow 01 | mantenerlo como decisión semántica y enlazarlo a un guard operacional distinto |
| `schemas/independent_research_audit.json` | auditoría independiente de Research | auditor independiente | Research/gates | Research | separación de productor y auditor, findings, defect routes y decisión fail-closed | faltan criterios V2 específicos para profundidad/fidelidad si el alcance lo exige | REUSE + EXTEND | schema; `src/core/research_audit.py`; `.agent/skills/skill_auditar_suficiencia_semantica_b5_i2.md` | reutilizar el contrato y extender criterios o referencias, sin crear agente durante M1 |
| `schemas/source_grounded_research_adapter.json` | adaptación opcional con fuentes | Research | consumidores Research | transversal | distingue `AVAILABLE/UNAVAILABLE` y declara que no es memoria canónica ni autoridad de veracidad | es opcional y no sustituye un recovery/provenance controlado | REUSE | schema; `src/core/research_adapter.py` | usarlo solo como interfaz explícita si la compatibilidad lo requiere, nunca como bypass de evidencia |
| `schemas/delegation_decision.json` | decidir inline/delegate/escalate | Software/policy | orquestación y workflow | transversal | decisión estructurada, razones, policy version y evidence refs | no expresa por sí solo el conjunto de candidatas o la etapa Research V2 | REUSE | schema; `src/core/delegation_policy.py`; `config/subagent_registry.json` | bindear alcance y versión de selección si M2 demuestra que falta |
| `schemas/human_decision.json` | decisión explícita del OWNER/usuario | Software/humano | workflow y storage | transversal | actor, opción, corrección, canal, timestamp y request checksum | no se observó un gap material para M1 | REUSE | schema; `src/core/contract_validation.py`; `src/application/storage.py` | reutilizar para decisiones de selección o desbloqueo que realmente requieran intervención humana |
| `schemas/human_decision_request.json` | solicitud pendiente a humano | Software | workflow y recuperación | transversal | pending/resolved/stale/cancelled, subject refs, checksum y workflow ref | no es una decisión cognitiva ni debe absorber estados de Research | REUSE | schema; `src/core/contract_validation.py`; `src/application/service.py` | enlazar a la dimensión que originó la solicitud, sin duplicar su estado |
| `schemas/human_episode_input.json` | entrada humana canónica | servicio de intake | episodio, Research y B5-I3 | transversal | binding de episodio, provenance, modo, contenido y estado de procesamiento | no separa de forma suficiente research role/editorial intent si V2 los necesita | EXTEND | schema; `src/application/service.py`; `src/ai/execution.py::M3_REQUIRED_INPUT_KINDS` | añadir solo el contexto contractual demostrado y preservar compatibilidad explícita |
| `schemas/episode_brief.json` | brief y pregunta inicial | servicio/usuario | Research y B5-I3 | transversal | pregunta, conflicto, hipótesis inicial revisable, alcance, materiales y restricciones | no es plan Research; puede necesitar referencias a intención y nivel de investigación | EXTEND | schema; `.agent/workflows/01_pipeline_episodio.md`; `src/ai/execution.py` | ampliar únicamente si el handoff no puede expresarse sin deformar el brief |
| `schemas/material_curation.json` | análisis comparativo y curación final | `RESEARCH_AND_CURATION` en workflow B5-I2 | B5-I3, auditoría semántica | mixto Research/Narrative | contribuciones, solapamiento, restricciones heredadas y relación entre materiales | `sequence_rationale`, `expected_order`, progression y climax son decisiones de arquitectura narrativa | MOVE_RECONCILE | schema; `.agent/skills/skill_curation_obras.md`; `skill_auditar_suficiencia_semantica_b5_i2.md`; `src/ai/role_execution.py` | conservar comparación, límites y no redundancia; mover orden/progresión/clímax al consumidor narrativo |
| `schemas/narrative_human_analysis.json` | análisis sustantivo de escenas/materiales | B5-I2 | auditoría B5-I2 y B5-I3 | mixto | sujeto, acción, tensión, evidencia, interpretación, límites y contribución | `material_function_candidate` y `potential_contribution_to_progression` anticipan arquitectura | MOVE_RECONCILE | schema; skill de auditoría B5-I2; prompt/inputs de B5-I3 | conservar hallazgos y evidencia; convertir función narrativa en observación/candidato no vinculante o moverla |
| `schemas/refined_thesis.json` | tesis refinada trazable | skill de síntesis en B5-I2 | B5-I3 read-only y auditoría | Research→Narrative | statement, soporte, contraevidencia, rivales, objeción, matiz, límites y lineage | registry actual asigna `skill_sintesis_tesis` a `NARRATIVE_ARCHITECTURE`, aunque la tesis pertenece a Research; B5-I3 no debe mutarla | MOVE_RECONCILE | schema; `.agent/skills/skill_sintesis_tesis.md`; `config/skill_catalog.json`; prompt NARRATIVE_ARCHITECTURE | reconciliar autoridad con Research y mantener entrega read-only a B5-I3 |
| `schemas/curation_decision.json` | contrato antiguo de preselección/selección | prompt `RESEARCH_AND_CURATION` | workflow/tests y compatibilidad | Legacy/mixed | permite leer decisiones históricas y campos de perspectiva | solapa `MaterialCuration` y contiene función/secuencia/clímax; no es salida V2 canónica | LEGACY_COMPAT | schema; `config/agent_prompt_registry.json`; `skill_curation_obras.md`; workflow 01 | conservar lectura/migración explícita; no producirlo como contrato V2 nuevo |
| `schemas/semantic_sufficiency_audit.json` | auditoría semántica genérica histórica | auditor/gate anterior | consumidores históricos | Legacy | decisión, criterios y referencias de checksums | no debe sustituir la auditoría Research V2 ni la auditoría cerrada B5-I2 | LEGACY_COMPAT | schema; `src/core/contract_validation.py` | mantener compatibilidad donde exista dependencia y no ampliar su semántica por conveniencia |
| `schemas/b5_i2_semantic_sufficiency_audit.json` | auditoría cerrada de B5-I2 | `B5_I2_SEMANTIC_AUDITOR` | gates B5-I2 y B5-I3 como input | B5-I2/legacy cerrado | independencia, criterios, artifact checksums y defectos | es un contrato B5-I2, no un contrato de Research V2; reusarlo como Research sería mezcla de capas | LEGACY_COMPAT | schema; `.agent/skills/skill_auditar_suficiencia_semantica_b5_i2.md`; `tests/harness/test_plan011_m3_b5_i3.py` | no modificar M3; versionar/adaptar solo desde una autorización futura y explícita |
| `src/core/contract_validation.py`, `src/core/research_audit.py` | validación estructural y auditoría | Software | Research, gates, B5-I3 | transversal | validación schema, referencias, provenance, actores independientes, defect routes | falta implementar las nuevas reglas V2, pero no falta un motor base | REUSE | funciones `validate_*`; `research_audit.py` | extender validaciones solo después de fijar contratos V2 |
| `src/core/invalidation.py` | grafo de dependencias e invalidación | Software | storage/workflows/consumidores | transversal | invalidación recursiva, visited/cycle guard, checksums y rutas de corrección | cycle guard no equivale a no-progress guard ni a suficiencia semántica | REUSE + EXTEND | `src/core/invalidation.py`; recuperación B5-I3 | reutilizar dependencias y extender señal operacional si el modelo actual no basta |
| `src/application/storage.py` | persistencia atómica, manifest y recovery | Software | B5-I3 y episodio | transversal | atomic writes, manifest, checksums, dependency snapshot y stale detection | no hay API dedicada a ResearchPlan/ResearchReadyManifest ni al recovery de búsqueda | REUSE + EXTEND | `record_b5_i3_design`, `recover_b5_i3_design`; tests B5-I3 | reutilizar primitivas atómicas y añadir persistencia V2 solo con gap demostrado |
| `src/ai/execution.py`, `src/ai/role_execution.py` | frontera Software→IA→Software | Software/orquestación | B5-I3 y roles | transversal | proyección cognitiva sin metadata, binding de runtime, validación de inputs y outputs | no hay roles/capabilities Research V2 ni adquisición real de fuentes integrada | REUSE + EXTEND | `M3_REQUIRED_INPUT_KINDS`; `_bind_m3_runtime_fields`; role execution | reutilizar el patrón, ampliar contratos/roles solo tras autorización M2 |
| `ResearchPlan` | contrato de planificación Research V2 | no existe | no existe | requisito aprobado pendiente de implementación | responsabilidad expresamente aprobada por PLAN012; no hay implementación encontrada | no existe schema, registry, productor, consumidor, persistencia ni referencias en el repo inspeccionado | CREATE_APPROVED_BY_PLAN012 | búsqueda de `ResearchPlan` sin resultados canónicos; PLAN012 §§5, 15.1 y trabajo de software | M2 debe materializar el contrato aprobado, reutilizando/extendiendo superficies internas sin reabrir su existencia |
| `ResearchReadyManifest` | handoff verificable de Research a consumers | no existe | no existe | requisito aprobado pendiente de implementación | contrato final ligero expresamente aprobado por PLAN012 | no existe contrato o runtime equivalente identificado | CREATE_APPROVED_BY_PLAN012 | búsqueda de `ResearchReadyManifest` sin resultados canónicos; PLAN012 §§15.2 y misiones B1/B4 | M2/B4 debe materializar el contrato aprobado; SEARCH BEFORE CREATE decide referencias y reutilización interna, no suprimirlo |

### ResearchPlan y ResearchReadyManifest

La búsqueda no encontró todavía una implementación canónica de
`ResearchPlan` ni de `ResearchReadyManifest`. Eso demuestra una brecha de
implementación, no una duda sobre su existencia: PLAN012 ya los establece como
contratos aprobados. `EpisodeBrief`, el workflow y los manifests de storage
pueden reutilizarse o extenderse para evitar duplicación interna, pero no
eliminan el requisito. Si durante la implementación aparece una contradicción
material, debe detenerse el trabajo y elevarse al OWNER; no convertirse en una
decisión unilateral de no crear.

## 4. Estados ortogonales

La siguiente matriz evita un enum cartesiano. Cada dimensión tiene un
significado distinto y puede cambiar por un evento distinto.

| dimensión | significado | contrato actual | situación | quién puede modificarla | dependencias | invalidadores | no debe mezclarse con |
|---|---|---|---|---|---|---|---|
| `research_stage` | profundidad/fase del trabajo Research | `ResearchPack`, `WorkResearchDossier`, `WorkLifecycle` | existe parcialmente; EXTEND | Software transicional con decisión cognitiva cuando corresponda | brief, scope, inputs y run version | cambio de scope/input, evidencia invalidada, correction route | selection, fidelity, thesis o stop |
| `selection_state` | relación de una obra con la comparación y selección | `WorkLifecycle`, `CurationDecision` | existe, pero mezclada con funciones narrativas | Software tras decisión explícita de Research/OWNER | candidate set, criteria y evidence refs | cambio de criteria, nueva evidencia, decisión humana stale | deep fidelity, sufficiency o narrative order |
| `preliminary_fidelity` | fidelidad suficiente para screening/preselección | `WorkResearchDossier` y auditoría de obra | parcial; EXTEND | Research/independent audit, persistido por Software | obra, locators, access/evidence report | source/access change, audit defect, contradiction | final selection o thesis |
| `deep_fidelity` | fidelidad suficiente para uso profundo autorizado | `WorkResearchDossier`, `IndependentResearchAudit` | parcial; EXTEND | auditor independiente/Research; Software enlaza | dossier, evidence, audit and limitations | audit defect, source invalidation, scope change | preliminary fidelity y narrative readiness |
| `research_sufficiency` | suficiencia semántica para un intended use | `ResearchStopDecision`, source report | existe; REUSE | decisión de Research, validada y persistida por Software | critical claims, coverage, limitations, contradictions | claim/evidence changes, missing critical coverage, intended-use change | operational loop guard y artifact validity |
| `artifact_validity` | integridad contractual, binding y freshness | validadores, checksums, manifests, `InvalidationEngine` | existe; REUSE/EXTEND | Software | schema, IDs, checksums, dependency snapshot | mismatch, stale dependency, schema/episode/profile change | semantic truth, thesis stage o selection |
| `thesis_stage` | posición de la tesis en su evolución | `refined_thesis`, `EpisodeBrief`, contrato de tesis provisional implícito | parcial; EXTEND | Research/OWNER mediante decisión cognitiva; Software valida transición | evidence, rival, counterevidence, material refs | research correction, changed evidence, scope/intended-use change | narrative architecture or approval |
| `research_ready_state` | si el paquete puede entregarse al consumidor declarado | parcialmente en `ResearchStopDecision` y B5-I2 audit | no existe como dimensión única; EXTEND o CREATE_ONLY_IF_GAP | Software agrega checks; Research decide suficiencia | all required artifacts, restrictions, lineage, validity | any dependency invalidation or missing restriction propagation | `ResearchStopDecision` semántico y B5-I3 authorization |

### Reglas de transición e invalidación

- Una transición de stage o selection no cambia automáticamente fidelity,
  sufficiency o thesis.
- `ResearchStopDecision` responde si el conocimiento es suficiente para el uso
  declarado; no responde si el sistema lleva demasiadas iteraciones.
- `artifact_validity` es mecánica: schema, binding, checksum, provenance,
  dependencia y freshness. No convierte un artefacto válido en verdadero ni
  suficiente.
- Una corrección de evidencia puede invalidar tesis, selección y readiness por
  dependencia; no debe reescribir silenciosamente el estado histórico.
- La autorización de B5-I3 permanece fuera de estas dimensiones y no se deriva
  de `research_ready_state`.

## 5. Mapa de responsabilidades cognitivas

La unidad mínima identificable es el rol/prompt/skill existente o una
extensión explícita. No se propone un agente por disciplina.

| cognitive_responsibility | current_role | current_skill | current_prompt | capability | software_before | cognitive_work | software_after | decision | gap |
|---|---|---|---|---|---|---|---|---|---|
| Research planning | `RESEARCH_AND_CURATION` | `skill_research_tema_y_obras` | `prompt_research_curation` v1.0.0 | no capability Research dedicada | EpisodeBrief, scope, question, prior state | formular preguntas, cobertura y secuencia de búsqueda | valida plan, scope, versions y persistencia | EXTEND | no existe unidad contractual de plan |
| investigación base del fenómeno | `RESEARCH_AND_CURATION` | `skill_research_tema_y_obras` | `prompt_research_curation` v1.0.0 | no dedicada | brief y preguntas | separar hechos, interpretaciones, hipótesis y fuentes | valida refs, provenance, coverage y limitations | EXTEND | prompt genérico para profundidad V2 |
| discovery | `RESEARCH_AND_CURATION` | `skill_research_tema_y_obras` | `prompt_research_curation` | no dedicada | scope y criterios | descubrir fuentes/obras candidatas sin afirmar verificación | deduplica, registra y versiona candidatos | EXTEND | acquisition loop no está formalizado end-to-end |
| investigación base de obras | `RESEARCH_AND_CURATION` | research + `skill_curation_obras` | `prompt_research_curation` | no dedicada | work candidates, access limits | identificar obra, pasajes y contexto verificable | valida locators, access y source refs | EXTEND | falta separar candidate function de evidencia |
| fidelidad preliminar | `RESEARCH_AND_CURATION` / auditoría | research skill | research prompt; auditoría B5-I2 como referencia | no dedicada | dossier y source report | decidir si una candidata es fiel para screening | registra decision, refs y restrictions | EXTEND | no hay criterio V2 específico aislado |
| comparación de candidatas | `RESEARCH_AND_CURATION` | `skill_curation_obras` | `prompt_research_curation` | no dedicada | candidate set y criteria | contraste, complementariedad, redundancia y coste | persiste comparison evidence y decision | MOVE_RECONCILE | current curation también decide orden narrativo |
| selección delegada | `RESEARCH_AND_CURATION` con Software | no específica | no específica | `DelegationDecision` reusable, no capability Research | candidate set, policy y delegation request | seleccionar o escalar según evidencia/policy | valida actor, policy, refs y decision | REUSE + EXTEND | falta binding de etapa/scope si M2 lo demuestra |
| investigación profunda del fenómeno | `RESEARCH_AND_CURATION` | research skill | research prompt | no dedicada | preliminary findings y gaps | resolver claims, rivales, contradicciones y gaps | actualiza stage, refs, provenance e invalidation | EXTEND | no hay unidad profunda separada |
| investigación profunda de obras | `RESEARCH_AND_CURATION` | research + curation skills | research prompt | no dedicada | dossiers y locators | profundizar pasajes, contexto y límites de interpretación | valida dossier, fidelity y restrictions | EXTEND | falta unidad contractual de deep work |
| fidelidad profunda | auditoría independiente | auditoría B5-I2 como patrón, no como Research skill | no hay prompt Research V2 | no dedicada | dossier, evidence report y audit request | revisar fidelidad sin depender del productor | valida independencia, findings y correction route | EXTEND | criterios y prompt V2 no existen |
| claims/evidence/rivals/gaps | `RESEARCH_AND_CURATION` | research skill | research prompt | no dedicada | request de claims y fuentes recuperadas | relacionar claim, evidencia, rival, gap y limitación | valida refs, materiality, status y provenance | EXTEND | ClaimsLedger actual acoplado a script |
| reevaluación post-deep del conjunto | `RESEARCH_AND_CURATION` | `skill_curation_obras` | research prompt | no dedicada | deep dossiers, changed evidence | revisar selección completa con nueva evidencia | reabre/invalida dependencias y persiste nueva decision | EXTEND + MOVE_RECONCILE | lifecycle no separa bien reevaluación y narrative order |
| síntesis | `NARRATIVE_ARCHITECTURE` en registry actual | `skill_sintesis_tesis` | prompt NARRATIVE_ARCHITECTURE solo como consumer | `B5_I3_NARRATIVE_ARCHITECTURE` es de producto y no aplica a M1 | evidence, claims, analysis, curation | construir síntesis investigativa defendible | valida thesis refs, stage y restrictions | MOVE_RECONCILE | ownership actual está desplazado a Narrative |
| tesis provisional | `RESEARCH_AND_CURATION` por workflow | `skill_sintesis_tesis` modo B5-I1 | no prompt dedicado | no dedicada | brief + ResearchPack + source report | confirmar, limitar o revisar hipótesis inicial | persiste thesis stage y refs | EXTEND | contrato provisional no aparece como schema V2 único |
| tesis refinada | `NARRATIVE_ARCHITECTURE` en registry actual | `skill_sintesis_tesis` modo B5-I2 | B5-I3 la recibe read-only | capability B5-I3 no puede modificarla | analysis, curation y evidence | integrar soporte, contraevidencia, rivales, objeción y límites | valida lineage, checksums e invalidation | MOVE_RECONCILE | debe pertenecer a Research, no a arquitectura |
| ResearchStop semántico | Research/independent review | research QA + contrato stop | no prompt separado | no dedicada | claims, coverage, contradictions, intended use | decidir sufficient/limited/more research/blocked | valida consistencia y route | REUSE | no debe cargar seguridad operacional |
| auditoría independiente | auditor independiente; B5-I2 auditor es patrón vecino | `skill_auditar_suficiencia_semantica_b5_i2` para B5-I2 | prompt auditor B5-I2 | `B5_I2_SEMANTIC_AUDITOR` es producto, no M1 | artifact refs y producer run | hallar defectos, severidad y corrección | valida independencia y rutas | EXTEND + RECONCILE | criterios Research V2 requieren especificación posterior |
| especialista temporal | no existe rol/prompt/capability específico | no existe | no existe | no existe | request temporal acotada y evidence policy | resolver contexto temporal solo cuando un gap material lo exige | Software recupera, versiona y limita resultado | CREATE_ONLY_IF_GAP | no crear agente; primero probar extensión de Research |

La ausencia de una capability Research no autoriza crearla en M1. La unidad
actual `RESEARCH_AND_CURATION` sí puede ser reutilizada como agrupación
funcional, pero no debe seguir significando “todo”: M2 debe distinguir cada
responsabilidad por contrato, prompt/versión, skill o mecanismo temporal.

## 6. Consumer contract real: Research V2 → B5-I3

### 6.1 Inputs que B5-I3 exige hoy

Las superficies no son idénticas y deben auditarse separadamente:

1. `src/ai/execution.py::M3_REQUIRED_INPUT_KINDS` representa los kinds de
   artefacto que valida y orquesta el execution layer. Incluye literalmente
   `human_input`.
2. `src/ai/role_execution.py::NARRATIVE_ARCHITECTURE_REQUIRED_INPUTS` representa
   los inputs efectivos del role. Incluye `user_instructions`,
   `target_duration` y `target_language`, y no incluye literalmente
   `human_input`.
3. El prompt `prompts/roles/NARRATIVE_ARCHITECTURE/1.0.0.md` define la
   proyección cognitiva, mientras `tests/harness/test_plan011_m3_b5_i3.py`
   prueba el conjunto de integración.

La matriz correcta, por tanto, es una relación de binding entre capas, no una
afirmación de igualdad entre listas:

```text
human_input
active_editorial_profile_reference
episode_brief
research_pack
claims_ledger
source_access_and_evidence_report
narrative_human_analysis
material_curation
refined_thesis
editorial_script_promise
early_packaging_hypothesis
b5_i2_semantic_audit
youtube_adaptation_review
```

Los seis artefactos Research o Research→Narrative que B5-I3 consume
realmente son `ResearchPack`, `ClaimsLedger`,
`SourceAccessAndEvidenceReport`, `NarrativeHumanAnalysis`, `MaterialCuration`
y `RefinedThesis`. `EpisodeBrief`, `human_input` y el perfil son contexto
canónico transversal. `EditorialScriptPromise`, `EarlyPackagingHypothesis`,
`B5I2SemanticAudit` y `YouTubeAdaptationReview` son outputs/reviews de B5-I2 o
YouTube, no productos de Research V2.

### 6.2 Matriz de consumo

| Research artifact/campo actual | Consumidor B5-I3 | Necesario en V2 | Problema | Acción futura |
|---|---|---|---|---|
| `ResearchPack.facts`, `interpretations`, `hypotheses`, `contradictions`, `alternative_views`, `coverage` | prompt NARRATIVE_ARCHITECTURE y projection de `src/ai/execution.py` | sí, como conocimiento investigado claramente tipado | `narrative_opportunities` puede convertir hallazgo en instrucción narrativa | conservar contenido epistemológico; mover/reformular oportunidades como restricciones/observaciones no vinculantes |
| `ResearchPack.source_registry`, `limitations`, `external_reality_evidence`, `narrative_evidence` | validación de Research y B5-I3 | sí | riesgo de perder distinción obra/fenómeno o de propagar fuentes no verificadas | preservar separación y bindings de provenance |
| `ClaimsLedger.claims` | B5-I3 y tests de inputs | sí | `script_version`/`script_location` hacen que Research dependa del script | extender a ledger de etapa; ruta versionada/adapter explícita para consumidor legacy |
| `SourceAccessAndEvidenceReport` completo | B5-I3 prompt, validadores y restricciones | sí, especialmente allowed/limited/prohibited, excluded claims, disclosures | no hay vínculo completo con recuperación real controlada por Software | extender acquisition provenance y conservar restricciones downstream |
| `NarrativeHumanAnalysis` evidencia, interpretación, límites, hallazgos | B5-I3 y auditoría B5-I2 | sí como análisis de material | campos de función/progresión anticipan arquitectura | mantener hallazgo y evidencia; sacar orden/progresión del contrato Research |
| `MaterialCuration` contribuciones, complementariedad, redundancia, restricciones | B5-I3, auditoría B5-I2 | sí como decisión comparativa | secuencia, `expected_order`, progression y climax son decisiones narrativas | conservar comparación y limits; mover decisiones de orden a B5-I3 |
| `RefinedThesis.statement`, soporte, contraevidencia, rivales, objeción, matiz, limits | B5-I3 read-only | sí, como tesis investigativa cerrada para el uso | owner registry actual es Narrative; riesgo de que B5-I3 la modifique por confusión | ownership Research; B5-I3 solo lee y referencia |
| `EpisodeBrief`/`human_input`/profile | B5-I3 full input set | sí como contexto inmutable | no son Research y no deben ser absorbidos por el handoff | conservar como contratos transversales separados |
| `editorial_script_promise`, `early_packaging_hypothesis`, `b5_i2_semantic_audit`, `youtube_adaptation_review` | B5-I3 actual | sí para M3 cerrada | no son Research V2; convertirlos en Research produciría mezcla de capas | mantenerlos en B5-I2/Youtube; no cambiarlos silenciosamente |

### 6.3 Qué recibe B5-I3 y qué decide

B5-I3 recibe hechos/interpretaciones/hipótesis, evidencia, claims, fidelidad,
contradicciones, rivales, tesis, limitaciones y restricciones. Software ya
controla `episode_id`, IDs, versiones, checksums, lineage, input checksums,
timestamps, duración, idioma y persistencia. La IA decide viewer journey,
opening, closing, progresión, arquitectura argumental, secuencia y outline;
no inventa provenance ni modifica la tesis refinada.

En consecuencia, estos elementos deben salir de la responsabilidad Research
activa, aunque puedan seguir llegando como compatibilidad histórica:

- orden final de materiales;
- progresión narrativa y clímax;
- hook, apertura, cierre y bloques;
- asignación narrativa obligatoria de una obra;
- cualquier instrucción que trate una hipótesis Research como decisión de
  arquitectura.

La compatibilidad correcta no puede decidirse por comodidad. M2 debe probar,
para cada cambio, si basta una extensión compatible, si requiere una nueva
versión contractual, un adapter explícito o una migración. En ningún caso se
modificarán silenciosamente los schemas cerrados de PLAN011 M3.

## 7. Frontera Software → IA → Software

El patrón existente de B5-I3 es reutilizable:

```text
Software prepara input validado y versionado
        ↓
IA recibe proyección cognitiva sin metadata técnica
        ↓
IA produce decisión estructurada limitada por schema/prompt
        ↓
Software bindea IDs, versiones, checksums, lineage y provenance
        ↓
Software valida, persiste, versiona, invalida y enruta
        ↓
siguiente cognición explícita, si corresponde
```

La evidencia es `src/ai/execution.py` (proyección y
`_bind_m3_runtime_fields`), `src/ai/role_execution.py`,
`prompts/roles/NARRATIVE_ARCHITECTURE/1.0.0.md`,
`src/application/storage.py` (`record_b5_i3_design`/`recover_b5_i3_design`) y
los tests del harness B5-I3. El punto de riesgo no está en B5-I3 cerrado,
sino en el futuro handoff Research V2: no debe permitir output libre de una IA
como input confiado de otra IA.

M2 debe establecer una vuelta a Software después de cada responsabilidad
material: validación, binding, persistencia, invalidación y route. Un output
cognitivo que no pase por ese retorno no puede ser fuente de autoridad para la
siguiente cognición.

## 8. Adquisición controlada de evidencia

La frontera requerida es:

```text
IA produce Research/Search Request
        ↓
Software valida alcance y ejecuta search/fetch real autorizado
        ↓
Software guarda recovery artifact + provenance + checksum + locator
        ↓
IA recibe solo la evidencia recuperada y sus restricciones
```

El repositorio ya ofrece piezas parciales: source registry y provenance en
`ResearchPack`, validación de refs en `src/core/contract_validation.py`,
`SourceAccessAndEvidenceReport`, `src/core/research_adapter.py` y la regla de
las skills de que la IA no inventa fuentes. No se encontró, sin embargo, un
contrato único que enlace request, ejecución de Software, artefacto recuperado,
provenance y uso cognitivo extremo a extremo.

Gap de M2: extender esas piezas o demostrar que el manifest/storage existente
puede bindear el flujo. La IA no puede convertir una URL mencionada en
`CONSULTED`, `VERIFIED` o `EVIDENCE` sin recuperación real controlada por
Software.

## 9. Estrategia no-progress / loop guard

Debe mantenerse la separación:

```text
ResearchStopDecision = suficiencia semántica para un intended use
Iteration/NoProgressGuard = seguridad operacional del proceso
```

Se puede reutilizar:

- el grafo, `visited` y cycle guard de `src/core/invalidation.py` para evitar
  recursión de invalidaciones;
- checksums, dependency snapshots y manifests de
  `src/application/storage.py` para comparar ejecuciones;
- `DelegationDecision`, `HumanDecisionRequest` y la política de
  `config/subagent_registry.json` como precedentes de route y límites.

No se encontró un guard Research V2 que registre de forma determinista gap,
evidence fingerprint, estado, resultado cognitivo, arista de transición,
contador y límite operativo. El `max_cycles` del registry de subagentes es una
política de agentes existentes, no un control integrado del loop Research.

M2 debe intentar primero extender run state/provenance/storage con:

1. fingerprint de scope, gap, evidencia, estado y decisión;
2. detección de repetición del mismo resultado o de ciclo A→B→A;
3. límite de iteraciones/acciones/tiempo;
4. route explícita a `ResearchStopDecision`, revisión humana o `STOP_LOCAL`;
5. idempotencia y persistencia antes de volver a IA.

Solo si esas superficies no pueden alojarlo habrá un contrato separado, y
seguiría siendo `CREATE_ONLY_IF_GAP`. El guard nunca puede inferir suficiencia
semántica ni autoautorizar B5-I3.

## 10. Paralelismo

PLAN012 no exige concurrencia. La lectura de `.agent/workflows/01_pipeline_episodio.md`,
`piloto-outline.md`, storage y el runtime no mostró una obligación material de
concurrencia para Research V2: el flujo documentado es secuencial y B5-I3
usa un conjunto validado, unido por checksum y dependency snapshot.

Diseño M1: **secuencial es válido y preferido por defecto**. No se propone
concurrencia, join ni merge. Si M2 descubre paralelismo ya existente, deberá
documentar input versions, join, stale detection, merge, invalidation, race
conditions e idempotencia antes de modificar el runtime.

## 11. Gaps y puntos pendientes de implementación

1. `ResearchPlan` está aprobado por PLAN012 pero todavía no está materializado;
   `EpisodeBrief`, el workflow y storage deben reutilizarse internamente sin
   cuestionar la existencia del contrato.
2. `ResearchReadyManifest` está aprobado por PLAN012 pero todavía no está
   materializado; su forma debe reutilizar referencias y manifests existentes
   sin suprimir el handoff requerido.
3. No existe binding extremo a extremo de Search Request a evidencia recuperada
   por Software.
4. No existe guard Research V2 de no progreso; el cycle guard de invalidación
   no cubre esa responsabilidad.
5. El ledger de claims actual está acoplado a `script_version` y
   `script_location`.
6. MaterialCuration, NarrativeHumanAnalysis y algunos campos de ResearchPack
   contienen decisiones de uso narrativo que deben reconciliarse antes del
   contrato V2.
7. La ownership de síntesis/tesis en registries está desplazada a
   `NARRATIVE_ARCHITECTURE`, aunque B5-I3 la recibe como lectura. Debe
   reconciliarse sin crear otro agente.
8. No hay una unidad Research V2 específica para deep fidelity ni temporal;
   es un gap de contrato/prompt/capacidad solo si un caso material lo exige,
   no una razón para crear agentes disciplinares.

## 12. Riesgos de compatibilidad

- Cambiar un schema B5-I3 cerrado rompería el contrato M3 y sus tests.
- Hacer obligatorio en Research un campo de arquitectura desplaza decisiones a
  la IA equivocada y crea dependencia silenciosa.
- Eliminar sin versión `script_version`/`script_location` puede romper ledger
  histórico; se requiere extensión, versión, adapter o migración explícita.
- Usar `ResearchStopDecision` como loop guard puede detener investigación
  suficiente o declarar suficiencia por agotamiento operativo.
- Tratar disponibilidad de `source_grounded_research_adapter` como veracidad
  convertiría un adapter opcional en autoridad epistemológica.
- Propagar restricciones solo por ID, sin comprobar aplicación operativa,
  permitiría a B5-I3 usar claims excluidos o análisis prohibidos.
- Entregar un objeto cognitivo directamente a otra IA sin Software entre ambas
  rompería provenance, invalidación y control de estado.
- Promover `research_ready_state` a autorización B5-I3 mezclaría readiness
  contractual con autorización de producto.

## 13. Alcance exacto propuesto para M2

M2, solo después de autorización específica del OWNER, debería:

1. congelar una tabla de compatibilidad por campo entre contratos actuales y
   Research V2;
2. extender primero los schemas y validadores existentes;
3. separar campos de evidencia/conocimiento de campos de función narrativa;
4. reconciliar ownership de síntesis y tesis sin reabrir ni modificar en
   silencio B5-I3;
5. formalizar bindings de provenance, lineage, versions y restrictions;
6. materializar `ResearchPlan` y `ResearchReadyManifest`, reutilizando o
   extendiendo `EpisodeBrief`, lifecycle y storage internamente sin reabrir la
   decisión aprobada de que ambos contratos deben existir;
7. formalizar el flujo Search Request→Software fetch→recovery artifact→IA;
8. implementar, solo si procede, el no-progress guard como control operacional
   independiente de ResearchStop;
9. mantener flujo secuencial salvo evidencia contraria;
10. añadir validación y pruebas únicamente como parte de la autorización M2,
    no durante esta misión.

### Archivos que M2 probablemente deberá modificar

La lista es previsional, no autorización de escritura:

```text
schemas/research_pack.json
schemas/claims_ledger.json
schemas/source_access_and_evidence_report.json
schemas/work_research_dossier.json
schemas/work_lifecycle.json
schemas/material_curation.json
schemas/narrative_human_analysis.json
schemas/refined_thesis.json
schemas/human_episode_input.json
schemas/episode_brief.json        (solo si se demuestra necesario)
src/core/contract_validation.py
src/core/research_audit.py         (solo criterios V2 demostrados)
src/core/invalidation.py
src/application/storage.py
src/application/service.py
src/ai/execution.py
src/ai/role_execution.py
```

`src/cli.py` queda fuera del alcance normal de M2 y debe permanecer read-only.
La CLI pertenece a la misión posterior de B5/M7. Solo una dependencia técnica
real, documentada y autorizada explícitamente por el OWNER podría ampliar ese
alcance.

También podrían requerirse ajustes coordinados en prompts, skills,
registries, workflows, gates y tests; no forman parte de M1 y no se prescriben
como cambios automáticos.

### Archivos que M2 probablemente deberá crear

Los siguientes schemas son requisitos aprobados de PLAN012; su forma interna y
sus referencias deben seguir SEARCH BEFORE CREATE:

```text
schemas/research_plan.json
schemas/research_ready_manifest.json
```

Un adapter o contrato específico de adquisición/no-progress queda condicionado
a gap probado. No se crea ninguno en M1; cualquier creación queda condicionada
a un gap demostrado durante M2.

### Elementos que M2 no debe crear

- una segunda autoridad de estado, runtime, ledger, dossier, provenance,
  storage o lifecycle;
- `authority.json`, `mission-authorization.json` o `mission_contract.json`
  para una auditoría documental;
- capability, role o agente ficticio para representar M1;
- `agent_psychologist`, `agent_historian`, `agent_sociologist` u otros agentes
  disciplinares como sustituto de contratos;
- mega-enums que combinen stage, selección, aprobación, fidelidad y suficiencia;
- un ResearchPack que decida hook, orden, bloques, ritmo o clímax;
- un loop guard que se comporte como ResearchStop;
- compatibilidad silenciosa, reescritura de M3 o reapertura de PLAN011 M3;
- IA real, PRODUCT_USE, P2 real, B5.5, B6, B7 o infraestructura de publicación.

## 14. Blockers y decisiones pendientes

M1 no se auto-cierra y queda lista para revisión del OWNER. Quedan
decisiones de M2/OWNER:

- aceptar o corregir la ownership Research de síntesis y tesis;
- definir la forma exacta de `ResearchPlan` y `ResearchReadyManifest`,
  reutilizando referencias existentes sin cuestionar su existencia aprobada;
- escoger por campo extensión, versión, adapter o migración;
- definir el contrato de adquisición controlada y el no-progress guard;
- confirmar los criterios de deep fidelity y el tratamiento de una necesidad
  temporal concreta.

Estas decisiones no se implementan ni autorizan con este informe.

### Conteo de decisiones de inventario

Para evitar doble conteo, cada fila recibe una clasificación primaria según la
acción dominante de M2; las combinaciones documentadas en la tabla se
conservan como riesgo o dependencia secundaria.

```text
REUSE_COUNT = 5
EXTEND_COUNT = 12
MOVE_RECONCILE_COUNT = 3
CREATE_ONLY_IF_GAP_COUNT = 0
# CREATE_REQUIRED aquí significa requisito aprobado por PLAN012, no gap descubierto por M1.
CREATE_REQUIRED_APPROVED_COUNT = 2
CREATE_APPROVED_BY_PLAN012_COUNT = 2
LEGACY_COMPAT_COUNT = 3
NEW_AGENTS_PROPOSED = 0
NEW_CAPABILITIES_PROPOSED = 0
NEW_SKILLS_PROPOSED = 0
```

## 15. Estado de M1

```text
M1_DESIGN = CLOSED_OWNER_APPROVED
M1_CLOSED = YES
M2_STATUS = CLOSED_OWNER_APPROVED
M2_CLOSED = YES
PLAN_012_CURRENT_BLOCK = B1
PLAN_012_CURRENT_MISSION = M1
PLAN_012_B1_STATUS = CLOSED
PLAN_012_B1_M1_STATUS = CLOSED_OWNER_APPROVED
PLAN_012_B1_M2_STATUS = CLOSED_OWNER_APPROVED
PLAN_012_M3_STATUS = NOT_AUTHORIZED
PLAN_012_IMPLEMENTATION_AUTHORIZED = NO
CURRENT_MISSION = NONE
CURRENT_MISSION_EXECUTION_BUNDLE = NONE
REAL_AI_EXECUTION = NO
AUTHORIZED_FOR_PRODUCT_USE = NO
P2_REAL_EXECUTION_NOW = NO
COMMIT = NO
PUSH = NO
```

El informe queda cerrado con aprobación del OWNER. El cierre no autoriza M3,
no activa IA real, no autoriza uso productivo y no cambia la autorización viva
de runtime.
