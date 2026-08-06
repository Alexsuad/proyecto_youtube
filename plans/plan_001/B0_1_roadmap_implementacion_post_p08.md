# PLAN-001 — IMPLEMENTATION ROADMAP POST-P08 v3

**Ruta canónica en el repositorio:** `plans/plan_001/B0_1_roadmap_implementacion_post_p08.md`
**Proyecto:** Más Allá del Guion
**Naturaleza:** plan maestro técnico de implementación y aseguramiento; no es autorización de ejecución
**Baseline funcional:** P-08 integrada + IR-0 aprobado
**Fuente funcional de investigación:** `plan_implementacion_investigacion_editorial_post_p08_v2_2026-08-05.md`
**DOCUMENT_OWNER_APPROVAL:** `APPROVED`
**PRE_R0_GATE:** `PASS`
**R0_EXECUTION:** `NOT_STARTED`
**R1_IMPLEMENTATION:** `NOT_AUTHORIZED`
**IMPLEMENTATION_AUTHORIZED:** `NO`
**REAL_EPISODE_AUTHORIZED:** `NO`
**COMMIT_OR_PUSH_AUTHORIZED_BY_THIS_PLAN:** `NO`

---

## 1. Propósito y autoridad

Este roadmap consolida en un único orden técnico la implementación pendiente del Proyecto YouTube después de:

1. la recuperación documental y eliminación de falsos cierres;
2. la reconciliación funcional P-08;
3. la normalización IR-0 de investigación editorial;
4. la separación entre requisitos especificados, representación técnica, validación, demostración operacional, aprobación funcional y autorización de producto.

No sustituye los requisitos funcionales aprobados por `CHANNEL_INTELLIGENCE`, `SCRIPT_PRODUCT` o `YOUTUBE_ADAPTATION`. Tampoco convierte planes históricos, tests estructurales o schemas existentes en evidencia de ejecución real.

### 1.1 Estados que deben mantenerse separados

```text
SPECIFIED
IMPLEMENTED
TECHNICALLY_VALIDATED
OPERATIONALLY_DEMONSTRATED
FUNCTIONALLY_APPROVED
AUTHORIZED_FOR_PRODUCT_USE
```

Una fase solo puede avanzar al siguiente gate cuando el estado exigido por ese gate esté demostrado con evidencia verificable. En particular:

```text
schema válido
≠ capacidad semántica demostrada

test estructural aprobado
≠ producto editorial aprobado

ejecución simulada
≠ vertical real

aprobación funcional de un dominio
≠ autorización interequipos para producto
```

### 1.2 Baseline aprobado

```text
P08_REQUIREMENTS: 112

IR0_STATUS: APPROVED_AS_PLANNING_BASELINE
IR0_REQUIREMENTS: 68
IR0_ALREADY_IMPLEMENTED: 4
IR0_PARTIAL: 31
IR0_MISSING: 32
IR0_FUNCTIONAL_DECISIONS_REQUIRED: 0
IR0_OUT_OF_SCOPE_TECHNICAL: 1

IMPLEMENTATION_AUTHORIZED: NO
```

Las tres decisiones funcionales de `SCRIPT_PRODUCT` quedaron resueltas de forma definitiva e íntegra en esta versión:

- `SP-IR0-CRITICAL_WORK_DOUBT`;
- `SP-IR0-MULTILINGUAL_RESEARCH_THRESHOLD`;
- `SP-IR0-MATERIAL_CLAIM_THRESHOLD`.

Sus criterios normativos completos se conservan en la sección 4. No queda deuda de decisión funcional en IR-0. Su implementación técnica continúa pendiente y debe verificarse en los contratos y gates de R1, R2 y R3 vinculados en este roadmap.

---

## 2. Orden maestro de dependencias

```text
R0  Cierre documental y recuperación
→ R1  Investigación editorial IR-0 a IR-7
→ R2  B5-I1 — brief, investigación inicial, evidencia y tesis provisional
→ R3  B5-I2 — profundización, análisis, curación y tesis refinada
→ R4  B5-I3 — recorrido, OPENING_UNIT, cierre, arquitectura y outline
→ R5  B5.5 — prototipo editorial controlado
→ R6  B6 — redacción completa, ensamblaje, edición y verificación
→ R7  Aprobación editorial independiente
→ R8  Adaptación profesional a YouTube y production readiness
→ R9  Pilotos, aprendizaje, cierre, Lean/5S y portabilidad
```

No se permite saltar gates por existir componentes parciales en el repositorio.

---

# R0 — CIERRE DOCUMENTAL Y RECUPERACIÓN

## Objetivo

Establecer una única autoridad de estado vivo, eliminar contradicciones documentales residuales y dejar el repositorio preparado para iniciar implementación sin reactivar rutas históricas, nomenclaturas colisionadas o autorizaciones antiguas.

## Requisitos P-08 e IR aplicables

- `P08-IF14-IG-001` a `P08-IF14-IG-004`
- `P08-IF15-IG-001` a `P08-IF15-IG-006`
- `IR0-001` — separar `IMPLEMENTATION_WORKSTREAM` y `EDITORIAL_RESEARCH_WORKFLOW`
- `IR0-002` — mantener no autorización
- `IR0-003` — trazabilidad canónica IR-0
- requisitos IR-0 restantes de gobernanza y clasificación

## Estado actual

```text
CURRENT_LIVE_STATE_AUTHORITY:
plans/001_CONTROL_OPERATIVO.md

ROADMAP_STATE_SNAPSHOT:
NON_NORMATIVE_REFERENCE_ONLY
```

Este roadmap no replica ni gobierna el estado vivo. Cualquier estado actual de fases, autorizaciones, cierres, misiones o avance debe consultarse exclusivamente en `plans/001_CONTROL_OPERATIVO.md`.

Como referencia no normativa, durante la preparación de este roadmap se detectó que `plans/plan_001/README.md` conservaba declaraciones históricas capaces de competir con la autoridad canónica. R0 debe sanear esa superficie sin copiar nuevos estados vivos al roadmap.

## Componentes existentes

- `AGENTS.md`
- `plans/001_CONTROL_OPERATIVO.md`
- `plans/plan_001/B5_PRE_SCRIPT_FOUNDATION.md`
- `plans/plan_001/README.md`
- `docs/reconciliation/p08/2026-08-05/`
- `docs/reconciliation/p08/2026-08-05/ir0_matriz_investigacion_editorial_post_p08_v3_2026-08-05.xlsx`
- `docs/reconciliation/p08/2026-08-05/ir0_plan_tecnico_investigacion_editorial_post_p08_v2_2026-08-05.md`
- P-08 integrada


## Brechas

1. Consolidar la navegación y la trazabilidad de los entregables IR-0 ya incorporados en el repositorio con sus hashes aprobados.
2. Corregir el índice `plans/plan_001/README.md` para que no duplique estado vivo ni declare autorización antigua.
3. Registrar que este roadmap es el orden maestro posterior a P-08 sin convertirlo en una segunda sede de estado.
4. Conservar P-07 como dependencia técnica transversal pendiente, sin inventar propagación.

## Dependencias

- P-08 aprobada.
- IR-0 aprobado por el propietario.
- Control operativo canónico vigente.
- Ninguna dependencia funcional adicional.

## Owner funcional

- Integración y estado: `INFRASTRUCTURE_GOVERNANCE`
- Verificación de estados de dominio: owner funcional correspondiente

## Orden técnico

1. Preservar la sede documental canónica de la matriz IR-0 y del plan técnico IR-0 sin alterar su integridad aprobada.
2. Crear este roadmap en `plans/plan_001/`.
3. Sanear `plans/plan_001/README.md` por referencia al control operativo, no por copia de estado.
4. Añadir validación documental mínima que detecte sedes paralelas, estados prohibidos y colisión B5_PRE/B5.5.
5. Revalidar integridad textual y navegación.

## Misiones previstas

> Son unidades futuras de planeación; no constituyen instrucciones para Codex.

- `R0-M1 — Incorporar baseline IR-0`
- `R0-M2 — Sanear índice operativo de Plan 001`
- `R0-M3 — Registrar roadmap maestro y autoridad documental`
- `R0-M4 — Validación de coherencia documental post-P08`

## Pruebas

- búsqueda de `IMPLEMENTATION_AUTHORIZED: YES` en superficies activas;
- búsqueda de `B5_PRE_M2_STARTED: YES`;
- comprobación de una sola sede de estado vivo;
- comprobación de nomenclatura B5_PRE frente a B5.5;
- validación de enlaces y rutas documentales;
- `git diff --check`;
- prueba de integridad UTF-8 y encabezados Markdown duplicados.

## Evidencia

- diff acotado;
- inventario de documentos modificados;
- reporte de búsquedas de estados contradictorios;
- control operativo sin cambios semánticos no autorizados;
- matriz IR-0 incorporada con checksum.

## Gate documental previo a R0

```text
DOCUMENT_OWNER_APPROVAL:
APPROVED

PRE_R0_GATE:
PASS

CANONICAL_LIVE_STATE_AUTHORITY:
plans/001_CONTROL_OPERATIVO.md

PARALLEL_LIVE_STATE_SURFACES:
0

IR0_BASELINE_IN_REPOSITORY:
YES

R0_EXECUTION:
NOT_STARTED

R1_IMPLEMENTATION:
NOT_AUTHORIZED
```

## Criterio de autorización

La aprobación documental de este roadmap deja convergido el plan maestro y habilita únicamente un gate previo a R0. La apertura formal de R0 y cualquier autorización posterior deben registrarse por separado en `plans/001_CONTROL_OPERATIVO.md`.

---

# R1 — INVESTIGACIÓN EDITORIAL IR-0 A IR-7

## Objetivo

Materializar e integrar técnicamente la infraestructura de investigación editorial aprobada: fenómeno, obras, fuentes, lifecycle, claims, suficiencia, contradicciones, memoria antirrepetición, especialistas adaptativos, auditoría independiente y adapters opcionales.

R1 implementa y valida capacidades técnicas. No demuestra todavía la vertical editorial completa de fenómeno, obras, curación y tesis refinada; esa demostración ocurre progresivamente en R2 y R3.

## Requisitos P-08 e IR aplicables

### P-08 principales

- B5-I1: 22 requisitos
- B5-I2 relacionados con dossiers, análisis, curación y tesis
- `P08-IF03-*` — lifecycle de obras
- `P08-IF04-*` — gobierno de investigación
- `P08-IF05-*` — formato multobra
- `P08-IF10-*` — memoria semántica
- `P08-IF14-*` — invalidación
- `P08-IF15-*` — frontera B5_PRE-M2

### IR

- `IR0-001` a requisitos IR-0 de gobernanza
- `IR1-*` — representación funcional
- `IR2-*` — lifecycle y profundidad progresiva
- `IR3-*` — YouTube, transcripciones y multilingüismo
- `IR4-*` — claim, suficiencia y contradicciones
- `IR5-*` — memoria antirrepetición
- `IR6-*` — responsabilidades especializadas
- `IR7-*` — vertical real y auditoría independiente

### Decisiones definitivas de SCRIPT_PRODUCT aplicables a R1

| Decisión                                 | Requisito IR-0 vinculado | Contratos/componentes afectados                                                                                              | Gates afectados           |
| ---------------------------------------- | ------------------------ | ---------------------------------------------------------------------------------------------------------------------------- | ------------------------- |
| `SP-IR0-CRITICAL_WORK_DOUBT`             | `IR2-005`                | `WorkResearchDossier`, lifecycle de obras, autorización delimitada de profundización anticipada, evidencia y ruta de retorno | `R1.3`, `R1.7`, `R1_GATE` |
| `SP-IR0-MULTILINGUAL_RESEARCH_THRESHOLD` | `IR3-009`                | evaluación y provenance de fuentes, original/transcripción/traducción, evidencia multilingüe, suficiencia y limitaciones     | `R1.3`, `R1.7`, `R1_GATE` |
| `SP-IR0-MATERIAL_CLAIM_THRESHOLD`        | `IR4-005`                | `ClaimsLedger`, `ResearchStopDecision`, suficiencia por uso, invalidación y revalidación                                     | `R1.4`, `R1.7`, `R1_GATE` |

La validación técnica de R1 debe demostrar que estos criterios pueden representarse y evaluarse íntegramente. R1 no demuestra todavía la vertical editorial real.

## Estado actual

```text
IR0_ALREADY_IMPLEMENTED: 4
IR0_PARTIAL: 31
IR0_MISSING: 32
IR0_FUNCTIONAL_DECISIONS_REQUIRED: 0
REAL_RESEARCH_VERTICAL: NOT_DEMONSTRATED
```

La base estructural existe, pero no cubre de extremo a extremo la política v2.

## Componentes existentes

- `schemas/research_pack.json`
- `schemas/claims_ledger.json`
- `schemas/source_access_and_evidence_report.json`
- `schemas/provisional_thesis.json`
- `schemas/narrative_human_analysis.json`
- `schemas/material_curation.json`
- `schemas/refined_thesis.json`
- `src/scripts/b5_i1_flow.py`
- `src/scripts/b5_i2_flow.py`
- gates de evidencia y suficiencia existentes
- invalidación genérica
- responsabilidades y prompts parciales
- skills históricas de investigación, curación y síntesis
- `config/capability_registry.json`
- `config/responsibility_registry.json`

## Brechas

1. `PhenomenonResearchPack` diferenciado.
2. `WorkResearchDossier` progresivo por obra.
3. fuente original frente a transcripción, traducción, resumen, reseña y cita indirecta.
4. lifecycle canónico completo y transiciones justificadas.
5. claims dependientes del uso y estados `ALLOWED/LIMITED/BLOCKED`.
6. `ResearchStopDecision` por fenómeno, obra, claim material y paquete.
7. tratamiento explícito de contradicciones.
8. memoria semántica con dimensiones y momentos de consulta.
9. contribuciones especializadas adaptativas.
10. auditorías diferenciadas e independencia productor–auditor.
11. casos reales positivos, negativos, limitados y bloqueados.
12. adapter opcional agnóstico, sin autoridad canónica.

## Dependencias

- R0 cerrado.
- Las decisiones `SP-IR0-CRITICAL_WORK_DOUBT`, `SP-IR0-MULTILINGUAL_RESEARCH_THRESHOLD` y `SP-IR0-MATERIAL_CLAIM_THRESHOLD` están resueltas y deben materializarse sin reinterpretación.
- Contratos base no esperan esas decisiones.
- Gates finales de IR2, IR3 e IR4 sí deben esperar las definiciones aplicables.
- P-07 para propagación granular de invalidaciones.

## Owner funcional

- Principal: `SCRIPT_PRODUCT`
- Plataforma y fuentes oficiales de YouTube: `YOUTUBE_ADAPTATION`
- Pertenencia y territorios: `CHANNEL_INTELLIGENCE`
- Materialización: `INFRASTRUCTURE_GOVERNANCE`

## Orden técnico

### R1.1 — Gobernanza y trazabilidad IR-0

Matriz canónica, IDs, dependencias, estados y authority mapping.

### R1.2 — Contratos base

`PhenomenonResearchPack`, `WorkResearchDossier`, evaluación de fuentes y relaciones con claims.

### R1.3 — Lifecycle y provenance

Estados de obra, transiciones, versiones exactas, fuentes derivadas, transcripciones y multilingüismo.

### R1.4 — Claims, suficiencia y contradicciones

Estados de claim, decisiones de parada, cierre de controversias y gates.

### R1.5 — Memoria y especialistas

Consultas por hitos, decisiones de originalidad, contribución adaptativa y límites de autoridad.

### R1.6 — Auditoría y adapters

Auditores diferenciados, rutas de retorno, adapter opcional y activación técnica separada.

### R1.7 — Integración técnica de componentes

Integración contractual y técnica de los componentes IR, con fixtures y casos controlados por capacidad. No constituye todavía una vertical editorial real completa.

## Misiones previstas

- `R1-M1 — Trazabilidad IR canónica`
- `R1-M2 — Contratos de investigación del fenómeno`
- `R1-M3 — Dossier progresivo por obra`
- `R1-M4 — Provenance y transformaciones de fuentes`
- `R1-M5 — Lifecycle de obras`
- `R1-M6 — Claims y suficiencia`
- `R1-M7 — Contradicciones y rutas de retorno`
- `R1-M8 — Memoria semántica`
- `R1-M9 — Contribuciones especializadas`
- `R1-M10 — Auditorías independientes`
- `R1-M11 — Integración técnica de capacidades IR`

## Pruebas

- validación de schemas;
- transiciones válidas e inválidas;
- fuente derivada que no sustituye original;
- transcripción con error material;
- traducción que requiere verificación;
- claim limitado y bloqueado;
- contradicción no resuelta que bloquea;
- obra excluida por falta de función;
- obra invalidada por nueva evidencia;
- memoria con `INSUFFICIENT_HISTORY`;
- reutilización que exige justificación;
- especialista que no puede promover su conclusión a hecho;
- independencia productor–auditor;
- adapter ausente sin bloquear el flujo.

## Evidencia

- fixtures positivos y negativos;
- lineage de fuentes y transformaciones;
- decisiones de lifecycle;
- dossiers progresivos;
- reportes de suficiencia;
- auditorías independientes;
- integración técnica trazable de componentes;
- limitaciones declaradas.

## Gate de salida

```text
R1_GATE:
PASS

IR_CONTRACTS:
IMPLEMENTED_AND_TECHNICALLY_VALIDATED

IR_COMPONENT_INTEGRATION:
PASS

IR_REAL_VERTICAL:
NOT_YET_DEMONSTRATED

AUTHORIZED_NEXT_STAGE:
R2_CONTROLLED_EXECUTION

SCRIPT_PRODUCT_RESEARCH_REVIEW:
PASS_FOR_TECHNICAL_CAPABILITIES

AUTHORIZED_FOR_PRODUCT_USE:
NO
```

## Criterio de autorización

R1 solo habilita una ejecución controlada de B5-I1 en R2. No declara vertical real demostrada. La autorización requiere revisión funcional de `SCRIPT_PRODUCT` sobre las capacidades técnicas y verificación de que las tres decisiones definitivas se materializaron sin reinterpretación y se aplicaron en los gates finales afectados.

---

# R2 — B5-I1: BRIEF, INVESTIGACIÓN INICIAL, EVIDENCIA Y TESIS PROVISIONAL

## Objetivo

Producir un paquete B5-I1 coherente y verificable desde intención y pertenencia hasta screening inicial, dossiers abiertos, suficiencia preliminar y tesis provisional.

## Requisitos P-08 e IR aplicables

- todos los 22 requisitos P-08 de `B5-I1`;
- requisitos `PREREQUISITE` de pertenencia;
- `IF-02 ENTRY_MODES`;
- `IF-03 WORK_LIFECYCLE`;
- `IF-04 RESEARCH_GOVERNANCE`;
- `IF-05 MULTIWORK_FORMAT`;
- `IF-06 AUDIENCE`;
- IR1 a IR4 aplicables a investigación inicial;
- IR5 consulta inicial de memoria;
- IR7 requisitos de auditoría del paquete.

### Decisiones definitivas de SCRIPT_PRODUCT aplicables a R2

| Decisión                                 | Requisito vinculado | Aplicación en B5-I1                                                                                                                 | Gate afectado |
| ---------------------------------------- | ------------------- | ----------------------------------------------------------------------------------------------------------------------------------- | ------------- |
| `SP-IR0-CRITICAL_WORK_DOUBT`             | `IR2-005`           | screening, profundización anticipada delimitada, decisión de continuar, excluir, bloquear o promover a consideración como finalista | `B5_I1_GATE`  |
| `SP-IR0-MULTILINGUAL_RESEARCH_THRESHOLD` | `IR3-009`           | investigación inicial del fenómeno y de obras, verificación primaria, traducción, transcripción y suficiencia preliminar            | `B5_I1_GATE`  |
| `SP-IR0-MATERIAL_CLAIM_THRESHOLD`        | `IR4-005`           | identificación de claims materiales y `ResearchStopDecision` individual antes de tesis provisional o uso editorial                  | `B5_I1_GATE`  |

## Estado actual

```text
B5_I1_STRUCTURAL_BASE: STRONG
B5_I1_TECHNICAL_VALIDATION: PASS_PARTIAL_SCOPE
B5_I1_FUNCTIONAL_APPROVAL: PENDING
B5_I1_REAL_EXECUTION: NOT_DEMONSTRATED
```

## Componentes existentes

- topic belonging policy, schemas y flow;
- `EpisodeBrief`;
- `ResearchPack`;
- `SourceAccessAndEvidenceReport`;
- `ClaimsLedger`;
- `ProvisionalThesis`;
- scripts y tests B5-I1;
- perfil editorial activo;
- entry modes documentados parcialmente.

## Brechas

- consumo pleno de IR v2;
- soporte consistente de `TOPIC_FIRST`, `ANCHOR_WORK_FIRST`, `CORPUS_FIRST`;
- `NO_WORK_YET` válido;
- dossiers progresivos desde screening;
- memoria inicial;
- screening normal 5–8 sin automatizar selección;
- auditoría semántica real;
- prueba de bloqueo por evidencia;
- retorno a Channel Intelligence por cambio material.

## Dependencias

- R1 contratos base y vertical técnica cerrados.
- Pertenencia temática operativa.
- perfil editorial activo.
- decisiones de materialidad y multilingüismo aplicadas cuando corresponda.

## Owner funcional

- Principal: `SCRIPT_PRODUCT`
- Pertenencia: `CHANNEL_INTELLIGENCE`
- Audiencia concreta preliminar: interfaz con `YOUTUBE_ADAPTATION`
- Técnica: `INFRASTRUCTURE_GOVERNANCE`

## Orden técnico

1. Entrada y pertenencia versionadas.
2. Brief y modo de entrada.
3. memoria inicial.
4. investigación inicial del fenómeno.
5. descubrimiento y screening.
6. apertura de dossiers.
7. claims y suficiencia preliminar.
8. tesis provisional.
9. auditoría independiente B5-I1.
10. ruta de correcciones y revalidación.

## Misiones previstas

- `R2-M1 — Entrada y pertenencia B5-I1`
- `R2-M2 — Brief y modos de entrada`
- `R2-M3 — Investigación inicial y memoria`
- `R2-M4 — Screening y apertura de dossiers`
- `R2-M5 — Evidencia y tesis provisional`
- `R2-M6 — Auditoría semántica B5-I1`
- `R2-M7 — Vertical B5-I1 controlada`

## Pruebas

- tres modos de entrada;
- `TOPIC_FIRST` sin obra;
- obra ancla no promovida automáticamente;
- corpus no aprobado automáticamente;
- 5–8 como rango normal, no cuota rígida;
- evidencia insuficiente;
- claim bloqueado;
- nueva investigación que reabre pertenencia;
- auditor distinto del productor.

## Evidencia

- paquete B5-I1 versionado;
- decisiones de pertenencia y screening;
- dossiers abiertos;
- ledger de claims;
- tesis provisional con rivalidad e incertidumbre;
- auditoría funcional del Equipo 02.

## Gate de salida

```text
B5_I1_GATE:
TECHNICAL_PASS
OPERATIONAL_DEMONSTRATION_PASS
SCRIPT_PRODUCT_FUNCTIONAL_APPROVAL_PASS
CHANNEL_INTELLIGENCE_PREREQUISITE_VALID
```

## Criterio de autorización

Autoriza únicamente iniciar B5-I2 sobre el mismo episodio controlado y las mismas versiones. No autoriza B5-I3 ni escritura.

---

# R3 — B5-I2: PROFUNDIZACIÓN, ANÁLISIS, CURACIÓN Y TESIS REFINADA

## Objetivo

Profundizar fenómeno y obras finalistas, producir análisis narrativo y humano específico, realizar síntesis transversal, curar 3–5 obras sustantivas y emitir tesis refinada y promesa editorial cumplible.

## Requisitos P-08 e IR aplicables

- los 17 requisitos P-08 de `B5-I2`;
- lifecycle, dossiers y investigación de `IF-03/IF-04`;
- formato multobra;
- audiencia concreta;
- promesa temprana y packaging temprano;
- IR2 profundidad progresiva;
- IR4 suficiencia final por uso;
- IR5 memoria antes de curación y tesis;
- IR6 especialistas;
- IR7 auditorías de fidelidad, interpretación y curación.

### Decisiones definitivas de SCRIPT_PRODUCT aplicables a R3

| Decisión                                 | Requisito vinculado | Aplicación en B5-I2                                                                                                           | Gate afectado |
| ---------------------------------------- | ------------------- | ----------------------------------------------------------------------------------------------------------------------------- | ------------- |
| `SP-IR0-CRITICAL_WORK_DOUBT`             | `IR2-005`           | continuidad o reapertura de investigación focalizada cuando la duda afecte función, interpretación, claims, selección o tesis | `B5_I2_GATE`  |
| `SP-IR0-MULTILINGUAL_RESEARCH_THRESHOLD` | `IR3-009`           | profundización de finalistas, controversias lingüísticas, traducciones, contexto local y suficiencia final                    | `B5_I2_GATE`  |
| `SP-IR0-MATERIAL_CLAIM_THRESHOLD`        | `IR4-005`           | tesis refinada, curación, promesa editorial, claims sensibles, apertura/conclusión futuras y revalidación por cambio de uso   | `B5_I2_GATE`  |

## Estado actual

```text
B5_I2_CONTRACTUAL_BASE: ADVANCED
B5_I2_IMPLEMENTATION_DECLARED: PARTIAL
B5_I2_REAL_EXECUTION: NOT_DEMONSTRATED
B5_I2_FUNCTIONAL_APPROVAL: PENDING
```

## Componentes existentes

- `NarrativeHumanAnalysis`
- `MaterialCuration`
- `RefinedThesis`
- `EditorialScriptPromise`
- paquete temprano de YouTube Adaptation
- scripts, gates y tests parciales B5-I2
- prompts de productor y auditor parciales

## Brechas

- dossiers finalistas suficientemente profundos;
- investigación multilínea conectada;
- análisis específico no intercambiable;
- síntesis transversal explícita;
- curación final por función diferenciada;
- consolidación de dossiers seleccionados;
- memoria antes de curación y tesis;
- fidelidad independiente;
- packaging temprano sin sobrepromesa;
- ejecución real productor–auditor.

## Dependencias

- B5-I1 aprobado.
- R1 completo.
- suficiente conjunto de finalistas.
- intervención de YouTube Adaptation.
- revalidación de pertenencia cuando haya transformación material.

## Owner funcional

- Producto editorial: `SCRIPT_PRODUCT`
- Promesa visible/packaging temprano: `YOUTUBE_ADAPTATION`
- Identidad cuando se active trigger: `CHANNEL_INTELLIGENCE`
- Técnica: `INFRASTRUCTURE_GOVERNANCE`

## Orden técnico

1. profundización del fenómeno;
2. dossiers finalistas;
3. análisis narrativo y humano;
4. contribuciones especializadas y lecturas rivales;
5. síntesis transversal;
6. curación final 3–5;
7. tesis refinada;
8. promesa editorial;
9. adaptación temprana y riesgo de sobrepromesa;
10. auditorías independientes y correcciones.

## Misiones previstas

- `R3-M1 — Profundización de finalistas`
- `R3-M2 — Análisis narrativo y humano`
- `R3-M3 — Síntesis transversal`
- `R3-M4 — Curación final 3–5`
- `R3-M5 — Tesis refinada y promesa editorial`
- `R3-M6 — Packaging temprano`
- `R3-M7 — Auditorías B5-I2`
- `R3-M8 — Vertical real B5-I2`

## Pruebas

- obra sin función diferenciada excluida;
- lectura rival legítima;
- sobreinterpretación bloqueada;
- claim que pasa a limitado;
- tesis que cambia por contradicción;
- 3–5 obras sustantivas;
- promesa no respaldada rechazada;
- productor y auditor independientes.

## Evidencia

- dossiers consolidados;
- matriz de comparación;
- decisión de curación;
- tesis refinada;
- promesa editorial y visible separadas;
- auditorías de fidelidad y suficiencia;
- aprobaciones separadas de SP y YA.

## Gate de salida

```text
B5_I2_GATE:
SCRIPT_PRODUCT_APPROVAL: PASS
YOUTUBE_ADAPTATION_EARLY_APPROVAL: PASS
OPERATIONAL_DEMONSTRATION: PASS
IDENTITY_REVALIDATION: PASS_OR_NOT_TRIGGERED
```

## Criterio de autorización

Autoriza preparar B5-I3. No autoriza redacción del episodio completo.

---

# R4 — B5-I3: RECORRIDO, OPENING_UNIT, CIERRE, ARQUITECTURA Y OUTLINE

## Objetivo

Convertir tesis y curación aprobadas en un diseño editorial completo, con recorrido del espectador, apertura prioritaria, cierre preparado, arquitectura narrativa flexible, presupuesto editorial y outline auditado.

## Requisitos P-08 e IR aplicables

- los 15 requisitos P-08 de `B5-I3`;
- `IF-07 OPENING_UNIT`;
- `IF-08 DURATION`;
- `IF-09 PROMISE_PACKAGING`;
- `IF-10 SEMANTIC_MEMORY`;
- IR5 consulta de memoria durante apertura y arquitectura;
- dependencias de dossiers y claims de IR.

## Estado actual

```text
B5_I3: DOCUMENTED_NOT_IMPLEMENTED
OPENING_READINESS: PARTIAL
OPENING_UNIT_FULL_LIFECYCLE: MISSING
OUTLINE_REAL_VERTICAL: NOT_DEMONSTRATED
```

## Componentes existentes

- planes B5;
- schemas históricos de viewer journey, opening, closing y narrative plan;
- conceptos de presupuesto editorial;
- packaging temprano;
- referencias de hook e introducción heredadas.

## Brechas

- `OPENING_UNIT` única 0:00–1:30, no rígida;
- diseño y redacción independiente;
- doble aprobación SP/YA;
- revisión condicional CI;
- memoria de aperturas;
- correspondencia título–miniatura–promesa–apertura–desarrollo–cierre;
- presupuesto basado en función, no duración fija;
- outline semánticamente auditado;
- revalidación posterior al ensamblaje.

## Dependencias

- B5-I2 aprobado.
- packaging temprano versionado.
- memoria semántica disponible.
- criterios de duración editorial y de plataforma separados.

## Owner funcional

- Arquitectura, apertura editorial y cierre: `SCRIPT_PRODUCT`
- funcionamiento YouTube: `YOUTUBE_ADAPTATION`
- voz/persona autoral por trigger: `CHANNEL_INTELLIGENCE`
- técnica: `INFRASTRUCTURE_GOVERNANCE`

## Orden técnico

1. viewer journey;
2. presupuesto editorial;
3. diseño de `OPENING_UNIT`;
4. cierre;
5. arquitectura;
6. outline;
7. correspondencia con packaging;
8. auditoría separada;
9. reescritura y revalidación.

## Misiones previstas

- `R4-M1 — Viewer journey`
- `R4-M2 — Presupuesto editorial`
- `R4-M3 — Ciclo OPENING_UNIT`
- `R4-M4 — Diseño de cierre`
- `R4-M5 — Arquitectura y outline`
- `R4-M6 — Correspondencia y auditorías`
- `R4-M7 — Vertical B5-I3`

## Pruebas

- apertura con sustancia temprana;
- apertura sin preámbulo;
- apertura que no confirma packaging;
- voz fabricada;
- duración flexible;
- outline repetitivo;
- cierre no preparado;
- invalidación por cambio de tesis o packaging.

## Evidencia

- viewer journey;
- versiones de apertura;
- auditorías SP y YA;
- revisión CI cuando aplique;
- arquitectura y outline;
- presupuesto;
- reporte de correspondencia.

## Gate de salida

```text
B5_I3_GATE:
SCRIPT_PRODUCT_DESIGN_APPROVAL: PASS
YOUTUBE_OPENING_APPROVAL: PASS
CHANNEL_IDENTITY_REVIEW: PASS_OR_NOT_TRIGGERED
OUTLINE_AUDIT: PASS
```

## Criterio de autorización

Autoriza exclusivamente B5.5. No autoriza guion completo.

---

# R5 — B5.5: PROTOTIPO EDITORIAL CONTROLADO

## Objetivo

Demostrar que el diseño aprobado puede convertirse en escritura profesional mediante `OPENING_UNIT` y uno o dos bloques representativos, sin producir todavía el episodio completo.

## Requisitos P-08 e IR aplicables

- `P08-B55-IG-003`
- `P08-B55-SP-001`
- `P08-B55-SP-002`
- requisitos aplicables de apertura, duración, voz, fuentes, memoria y claims.

## Estado actual

```text
B5_5_STATUS: PLANNED_NOT_STARTED
PROTOTYPE_EXISTS: NO
```

## Componentes existentes

- plan `B5_5_prototipo_editorial.md`;
- contratos de bloques y redacción histórica;
- opening design futuro;
- criterios editoriales y de YouTube ya definidos.

## Brechas

- prototipo real;
- selección de bloques representativos;
- contexto global suficiente;
- revisión de progresión, oralidad y especificidad;
- validación de duración;
- auditoría humana y funcional;
- decisión explícita de continuar o volver a B5-I3.

## Dependencias

- B5-I3 aprobado.
- contexto de investigación y claims congelado por versión.
- responsabilidades de productor/editor/auditor separadas.

## Owner funcional

- Principal: `SCRIPT_PRODUCT`
- Apertura YouTube: `YOUTUBE_ADAPTATION`
- Voz por trigger: `CHANNEL_INTELLIGENCE`
- Técnica: `INFRASTRUCTURE_GOVERNANCE`

## Orden técnico

1. elegir unidad y bloques;
2. construir context pack;
3. redactar apertura;
4. redactar 1–2 bloques;
5. ensamblar prototipo;
6. editar;
7. auditar;
8. decidir `PROCEED / RETURN / BLOCK`.

## Misiones previstas

- `R5-M1 — Preparar prototipo`
- `R5-M2 — Redactar OPENING_UNIT`
- `R5-M3 — Redactar bloques`
- `R5-M4 — Ensamblar y editar`
- `R5-M5 — Auditoría del prototipo`

## Pruebas

- continuidad entre apertura y bloque;
- no repetición;
- claims con evidencia;
- oralidad;
- densidad;
- correspondencia con outline;
- caso negativo que obligue a regresar.

## Evidencia

- prototipo versionado;
- reporte de edición;
- lectura oral;
- auditorías;
- decisión de avance.

## Gate de salida

```text
B5_5_GATE:
CONTROLLED_PROTOTYPE: PASS
SCRIPT_PRODUCT_APPROVAL: PASS
YOUTUBE_OPENING_APPROVAL: PASS
```

## Criterio de autorización

Autoriza B6 para el episodio controlado exacto. No autoriza publicación ni producción audiovisual.

---

# R6 — B6: REDACCIÓN COMPLETA, ENSAMBLAJE, EDICIÓN Y VERIFICACIÓN

## Objetivo

Producir el guion completo mediante redacción por bloques con contexto global, ensamblaje controlado, edición de desarrollo, edición de línea y oralidad, verificación factual e interpretativa y control de originalidad.

## Requisitos P-08 e IR aplicables

- los 9 requisitos P-08 de `B6`;
- `IF-11 VOICE_HUMANIZATION`;
- claims, dossiers, provenance y suficiencia IR;
- memoria antes del guion final;
- invalidación transversal.

## Estado actual

```text
B6: DOCUMENTED_NOT_MATERIALIZED_END_TO_END
FULL_SCRIPT_REAL_EXECUTION: NOT_DEMONSTRATED
```

## Componentes existentes

- plan B6;
- `ScriptBlockContract`;
- redacción longform histórica;
- context packs parciales;
- schemas de edición, oralidad, fact-check y originalidad;
- skills y prompts heredados.

## Brechas

- redacción real por bloques con contexto global;
- ensamblaje determinista;
- edición separada de redacción;
- oralidad real;
- verificación conectada a dossiers y claims;
- transformación de fuentes;
- memoria semántica final;
- rutas de corrección;
- auditor independiente.

## Dependencias

- B5.5 aprobado.
- B5-I3 congelado por versión.
- investigación y claims vigentes.
- presupuesto editorial aprobado.

## Owner funcional

- `SCRIPT_PRODUCT`
- voz/identidad por trigger: `CHANNEL_INTELLIGENCE`
- técnica: `INFRASTRUCTURE_GOVERNANCE`

## Orden técnico

1. presupuesto definitivo;
2. context pack global;
3. redacción por bloques;
4. ensamblaje;
5. edición de desarrollo;
6. edición de línea;
7. oralidad;
8. fact-check y fidelidad;
9. originalidad;
10. candidato final.

## Misiones previstas

- `R6-M1 — Context pack y presupuesto`
- `R6-M2 — Redacción por bloques`
- `R6-M3 — Ensamblaje`
- `R6-M4 — Edición de desarrollo`
- `R6-M5 — Edición de línea y oralidad`
- `R6-M6 — Verificación y originalidad`
- `R6-M7 — Candidato editorial final`

## Pruebas

- pérdida de contexto entre bloques;
- repetición;
- desbalance de presupuesto;
- claim sin soporte;
- cita o escena incorrecta;
- voz genérica;
- fuente demasiado cercana;
- lectura oral con problemas;
- invalidación por cambio de evidencia.

## Evidencia

- versiones de bloques;
- manifiesto de ensamblaje;
- reportes de edición;
- read-aloud;
- fact-check;
- fidelity audit;
- originality review;
- candidato final.

## Gate de salida

```text
B6_GATE:
FULL_SCRIPT_COMPLETE
DEVELOPMENT_EDIT_PASS
LINE_AND_ORALITY_PASS
FACTUAL_AND_INTERPRETIVE_VERIFICATION_PASS
ORIGINALITY_PASS
```

## Criterio de autorización

Autoriza someter el candidato a aprobación editorial independiente. No equivale a aprobación.

---

# R7 — APROBACIÓN EDITORIAL INDEPENDIENTE

## Objetivo

Auditar el guion completo, enrutar correcciones, controlar ciclos, revalidar dependencias y emitir aprobación editorial funcional separada de la producción y de YouTube.

## Requisitos P-08 e IR aplicables

- requisitos de B6 que exigen aprobación;
- invalidación `IF-14`;
- memoria final `IF-10`;
- promesa y correspondencia `IF-09`;
- auditoría independiente IR7;
- plan B7.

## Estado actual

```text
B7: DOCUMENTED_NOT_OPERATIONALLY_DEMONSTRATED
EDITORIAL_SCRIPT_APPROVAL: NOT_DEMONSTRATED
```

## Componentes existentes

- schemas de auditoría y aprobación;
- correction routing;
- invalidación genérica;
- prompts de auditor parcial;
- plan B7.

## Brechas

- auditoría real independiente;
- rutas de corrección por origen;
- límites de ciclos;
- revalidación después de correcciones;
- aprobación exacta de versión;
- evidencia de que el auditor no corrigió silenciosamente;
- separación de aprobación editorial y product readiness.

## Dependencias

- B6 completo.
- P-07 suficientemente materializado para invalidaciones requeridas.
- todas las evidencias de investigación y edición disponibles.

## Owner funcional

- `SCRIPT_PRODUCT`
- revisiones condicionales CI/YA
- técnica: `INFRASTRUCTURE_GOVERNANCE`

## Orden técnico

1. auditorías separadas;
2. decisión consolidada sin fusionar autoridades;
3. correcciones;
4. revalidación;
5. control de ciclos;
6. aprobación de versión exacta.

## Misiones previstas

- `R7-M1 — Auditoría editorial final`
- `R7-M2 — Correcciones y revalidación`
- `R7-M3 — Control de ciclos`
- `R7-M4 — EditorialScriptApproval`

## Pruebas

- auditor igual al productor;
- corrección silenciosa;
- versión cambiada después de aprobar;
- dependencia invalidada;
- sobrepromesa;
- repetición semántica;
- gate técnico sin aprobación funcional.

## Evidencia

- informes de auditoría;
- decisiones `APPROVED/REQUEST_CHANGES/BLOCK`;
- logs de ciclos;
- approvals por versión y checksum;
- manifest de guion aprobado.

## Gate de salida

```text
R7_GATE:
EDITORIAL_SCRIPT_APPROVED
SCRIPT_PRODUCT_FUNCTIONAL_APPROVAL: PASS
VERSION_IMMUTABLE_AFTER_APPROVAL: YES
```

## Criterio de autorización

Autoriza Adaptación a YouTube final. No autoriza producción, publicación o episodio real.

---

# R8 — ADAPTACIÓN A YOUTUBE, RIESGOS Y PRODUCTION READINESS

## Objetivo

Convertir el guion editorialmente aprobado en un paquete coherente para YouTube: correspondencia total, packaging final, apertura y duración, continuidad, plataforma, monetización, copyright, reutilización y aprobación humana para producción.

## Requisitos P-08 e IR aplicables

- 7 requisitos `B7.5`;
- 8 requisitos `B8`;
- 4 requisitos `B8.5`;
- `IF-07`, `IF-08`, `IF-09`, `IF-13`;
- IR3 para fuentes oficiales de YouTube;
- provenance y derechos de fuentes.

## Estado actual

```text
EARLY_YOUTUBE_ADAPTATION: PARTIAL_CONTRACTUAL_BASE
FINAL_PACKAGING: DOCUMENTED_NOT_MATERIALIZED
PLATFORM_AND_RIGHTS: DOCUMENTED_NOT_MATERIALIZED
YOUTUBE_PRODUCTION_READY: NOT_AUTHORIZED
```

## Componentes existentes

- traceability R3;
- packaging temprano;
- schemas de correspondencia, packaging, plataforma y copyright parciales;
- QA de lenguaje heredado;
- planes B7.5, B8 y B8.5.

## Brechas

- cadena completa título–miniatura–promesa–opening–desarrollo–conclusión;
- packaging final;
- políticas versionadas;
- duración de plataforma;
- continuidad y CTA;
- riesgo contextual;
- copyright y reutilización;
- paquete audiovisual;
- aprobación humana de versión exacta;
- estado `YOUTUBE_READY` reservado sin falsa activación.

## Dependencias

- guion aprobado R7.
- fuentes oficiales vigentes para política.
- derechos y reutilización conectados a dossiers y manifest.

## Owner funcional

- `YOUTUBE_ADAPTATION`
- contenido editorial inalterable: `SCRIPT_PRODUCT`
- identidad por trigger: `CHANNEL_INTELLIGENCE`
- producción approval: humano autorizado
- técnica: `INFRASTRUCTURE_GOVERNANCE`

## Orden técnico

1. correspondencia completa;
2. packaging final;
3. apertura/duración final;
4. continuidad y CTA;
5. plataforma y monetización;
6. copyright/reutilización;
7. paquete de producción;
8. aprobación humana;
9. cierre `YOUTUBE_PRODUCTION_READY`.

## Misiones previstas

- `R8-M1 — Promise Correspondence`
- `R8-M2 — Packaging final`
- `R8-M3 — Apertura, duración y continuidad`
- `R8-M4 — Plataforma y monetización`
- `R8-M5 — Copyright y reutilización`
- `R8-M6 — Paquete de producción`
- `R8-M7 — Aprobación humana production ready`

## Pruebas

- título y miniatura incompatibles;
- apertura que no confirma clic;
- promesa incumplida por conclusión;
- política desactualizada;
- riesgo contextual;
- copyright insuficiente;
- contenido sintético/alterado;
- versión distinta de la aprobada;
- aprobación de producción sin aprobación editorial.

## Evidencia

- packaging decision;
- correspondence report;
- risk reports;
- rights report;
- production package;
- human production approval;
- checksums de todas las piezas.

## Gate de salida

```text
R8_GATE:
EDITORIAL_SCRIPT_APPROVED
YOUTUBE_ADAPTATION_APPROVED
PLATFORM_AND_RIGHTS_PASS
HUMAN_PRODUCTION_APPROVAL_PASS
YOUTUBE_PRODUCTION_READY
```

## Criterio de autorización

Solo el gate completo autoriza producción audiovisual del episodio exacto. La publicación continúa separada si el sistema conserva esa etapa.

---

# R9 — PILOTOS, APRENDIZAJE, CIERRE Y PORTABILIDAD

## Objetivo

Validar el sistema con episodios controlados, convertir observaciones en aprendizaje gobernado, limpiar el repositorio, demostrar portabilidad y cerrar el MVP sin dependencias a chats, equipos numerados, proveedores o IDE concretos.

## Requisitos P-08 e IR aplicables

- `P08-B9-YA-001`;
- 13 requisitos P-08 de `B9.5`;
- `IF-10 SEMANTIC_MEMORY`;
- `IF-12 PLATFORM_LEARNING`;
- invalidación transversal;
- IR5 memoria y originalidad;
- IR7 vertical real;
- planes B9, B9.5 y B10.

## Estado actual

```text
B9: PLANNED_NOT_STARTED
B9_5: PARTIAL_CONTRACTUAL_BASE_DEFERRED
B10: PARTIAL_HISTORICAL_PASS_NOT_REVALIDATED_POST_P08
PORTABILITY_END_TO_END: NOT_DEMONSTRATED
```

## Componentes existentes

- plan de tres episodios;
- schemas de aprendizaje candidato;
- perfil editorial y activación;
- registros, manifests, gates y configuración agnóstica parciales;
- plan Lean/5S;
- políticas de contaminación y portabilidad.

## Brechas

- tres pilotos reales;
- métricas y evaluación humanas;
- aprendizaje editorial y de plataforma separados;
- evidencia acumulada antes de promover reglas;
- actualización gobernada de perfiles/memoria;
- limpieza de legado;
- eliminación de superficies paralelas;
- documentación instalable;
- prueba multi-proveedor;
- independencia de ChatGPT/Antigravity/Codex;
- cierre y versión.

## Dependencias

- R8 production ready.
- autorización explícita de pilotos.
- publicación y datos reales cuando correspondan.
- owner review de aprendizajes.

## Owner funcional

- Producto: `SCRIPT_PRODUCT`
- Identidad/aprendizaje de voz: `CHANNEL_INTELLIGENCE`
- YouTube learning: `YOUTUBE_ADAPTATION`
- Técnica/portabilidad: `INFRASTRUCTURE_GOVERNANCE`
- autorización final: propietario

## Orden técnico

1. pilotos controlados;
2. evaluación por caso;
3. observaciones;
4. aprendizaje candidato;
5. revisión funcional;
6. promoción o rechazo;
7. invalidación y actualización;
8. Lean/5S;
9. portabilidad;
10. cierre y versión.

## Misiones previstas

- `R9-M1 — Piloto episodio representativo`
- `R9-M2 — Piloto estructura alternativa`
- `R9-M3 — Piloto sensible/factual`
- `R9-M4 — Evaluación transversal`
- `R9-M5 — Aprendizaje editorial`
- `R9-M6 — Aprendizaje YouTube`
- `R9-M7 — Lean/5S y descontaminación`
- `R9-M8 — Portabilidad`
- `R9-M9 — Cierre y versión`

## Pruebas

- tres verticales completas;
- tema sensible;
- estructura distinta;
- aprendizaje no promovido por un solo dato;
- separación de owners;
- reproducción desde checkout limpio;
- proveedor alternativo;
- ausencia de secretos;
- ausencia de dependencia a chat;
- documentación reproducible;
- suite final y benchmarks editoriales.

## Evidencia

- tres paquetes completos;
- resultados de evaluación;
- decisiones de aprendizaje;
- actualización versionada;
- reporte Lean/5S;
- instalación limpia;
- prueba de portabilidad;
- manifest de release;
- aprobaciones finales.

## Gate de salida

```text
R9_GATE:
THREE_CONTROLLED_EPISODES: PASS
LEARNING_GOVERNANCE: PASS
LEAN_5S: PASS
PORTABILITY: PASS
FINAL_OWNER_APPROVAL: PASS
```

## Criterio de autorización

El propietario autoriza el cierre del MVP y el uso controlado del sistema. Ningún aprendizaje modifica automáticamente identidad, voz, criterio editorial o política de plataforma.

---

## 3. Gates globales no negociables

### G-01 — Autoridad

Ninguna fase puede declarar aprobación de un dominio sin la decisión del owner correspondiente.

### G-02 — Evidencia

Todo `PASS` debe incluir artefactos, versión, checksum, ejecución, limitaciones y responsable.

### G-03 — Independencia

Productor, editor y auditor deben mantener separación cuando la decisión lo requiera.

### G-04 — Invalidación

Todo cambio material debe determinar qué decisiones quedan vigentes, qué se reabre y a qué owner retorna.

### G-05 — No autorización implícita

La existencia de este roadmap no cambia:

```text
IMPLEMENTATION_AUTHORIZED: NO
REAL_EPISODE_AUTHORIZED: NO
PRODUCT_USE_AUTHORIZED: NO
```

### G-06 — Cambios proporcionales

Cada misión futura debe ser acotada, con mínimo contexto suficiente, archivos autorizados, pruebas y evidencia clara. No se permite usar este roadmap como excusa para una misión monolítica.

---

## 4. Decisiones funcionales definitivas de SCRIPT_PRODUCT

```text
IR0_FUNCTIONAL_DECISIONS_REQUIRED: 0
```

Las siguientes decisiones forman parte normativa del baseline IR-0. Sus criterios se conservan íntegros y no deben resumirse, reinterpretarse ni sustituirse durante la materialización técnica.

### 4.1 Vinculación consolidada

| Decisión                                 | Requisito IR-0 | Contratos/componentes afectados                                                                              | R1                        | R2                                      | R3                                             |
| ---------------------------------------- | -------------- | ------------------------------------------------------------------------------------------------------------ | ------------------------- | --------------------------------------- | ---------------------------------------------- |
| `SP-IR0-CRITICAL_WORK_DOUBT`             | `IR2-005`      | `WorkResearchDossier`, lifecycle, profundización focalizada, evidencia, invalidación y rutas de retorno      | `R1.3`, `R1.7`, `R1_GATE` | screening y `B5_I1_GATE`                | profundización/curación y `B5_I2_GATE`         |
| `SP-IR0-MULTILINGUAL_RESEARCH_THRESHOLD` | `IR3-009`      | provenance, fuente original, transcripción, traducción, evaluación de fuentes, suficiencia y contradicciones | `R1.3`, `R1.7`, `R1_GATE` | investigación inicial y `B5_I1_GATE`    | profundización/fidelidad y `B5_I2_GATE`        |
| `SP-IR0-MATERIAL_CLAIM_THRESHOLD`        | `IR4-005`      | `ClaimsLedger`, `ResearchStopDecision`, suficiencia por uso, limitaciones, invalidación y revalidación       | `R1.4`, `R1.7`, `R1_GATE` | claims/tesis provisional y `B5_I1_GATE` | tesis refinada/curación/promesa y `B5_I2_GATE` |

### 4.2 `SP-IR0-CRITICAL_WORK_DOUBT`

```text
DECISION_ID:
SP-IR0-CRITICAL_WORK_DOUBT

DEFINITION:
Una duda crítica es una incertidumbre sobre una obra todavía no clasificada como "FINALIST_WORK" cuya resolución puede cambiar materialmente:

- su viabilidad para el episodio;
- su estado dentro del lifecycle;
- la interpretación autorizable;
- los claims que podrían utilizarse;
- su relación con la pregunta o la tesis provisional;
- su posible función diferenciada;
- la seguridad editorial de continuar invirtiendo investigación en ella.

La profundización anticipada se autoriza únicamente para resolver esa duda concreta. No equivale a promover la obra a "FINALIST_WORK", completar anticipadamente todo su dossier ni asumir que será seleccionada.

ACTIVATION_CRITERIA:

Se activa cuando existe al menos uno de estos supuestos:

1. "VERSION_OR_ADAPTATION_UNCERTAINTY"

No está claro qué edición, corte, temporada, traducción o adaptación contiene el material relevante.

2. "PRIMARY_ACCESS_UNCERTAINTY"

La obra parece potencialmente útil, pero falta confirmar acceso suficiente a la fuente primaria o a una representación fiable para los claims previstos.

3. "SCENE_OR_PASSAGE_EXISTENCE_UNCERTAINTY"

Una escena, pasaje, decisión, diálogo o consecuencia es central para evaluar la obra, pero su existencia, localización o contexto no está suficientemente verificado.

4. "FUNCTION_DIFFERENTIATION_UNCERTAINTY"

La obra parece relevante, pero no puede determinarse mediante screening ligero si aporta una función distinta de las demás candidatas.

5. "THESIS_IMPACT_UNCERTAINTY"

La obra podría apoyar, tensionar, refutar o transformar materialmente la tesis provisional.

6. "RIVAL_READING_UNCERTAINTY"

Existe una lectura rival plausible que podría volver inadecuada, incompleta o sobreinterpretada la lectura inicial.

7. "SENSITIVITY_OR_HARM_RISK"

La obra se utilizaría para sostener afirmaciones sensibles sobre psicología, violencia, grupos sociales, historia, política, salud, derecho u otros asuntos de riesgo.

8. "ANCHOR_WORK_VIABILITY"

En "ANCHOR_WORK_FIRST", existe una duda que podría demostrar que la obra ancla no puede cumplir la función requerida, aunque deba conservarse como obligación de entrada.

9. "SCREENING_DECISION_BLOCKED"

No es posible emitir responsablemente una decisión de "SCREENED_WORK", "EXCLUDED_WORK" o investigación posterior sin una comprobación adicional delimitada.

10. "CONTRADICTION_WITH_AVAILABLE_EVIDENCE"

La información preliminar sobre la obra presenta contradicciones materiales entre la obra, transcripciones, resúmenes, críticas u otras fuentes.

La profundización debe limitarse a la información necesaria para decidir:

CONTINUE_SCREENING
PROMOTE_TO_FINALIST_CONSIDERATION
EXCLUDE_FOR_CURRENT_EPISODE
REQUIRE_MORE_TARGETED_RESEARCH
BLOCK_BY_EVIDENCE

NON_TRIGGER_EXAMPLES:

- curiosidad general por conocer mejor una obra;
- popularidad de la obra;
- disponibilidad abundante de análisis externos;
- familiaridad previa del equipo con la obra;
- deseo de adelantar trabajo por si la obra termina seleccionada;
- intención de completar el dossier antes de comparar candidatas;
- existencia de una escena interesante sin relación material con la pregunta;
- ausencia de detalles menores que no afectan estado, claims, interpretación o función;
- preferencia subjetiva por la obra;
- posibilidad abstracta de que aparezca una lectura diferente sin evidencia concreta;
- investigar profundamente todas las candidatas “para estar seguros”.

INVALIDATORS:

La autorización de profundización anticipada queda invalidada cuando:

- la pregunta crítica ya fue resuelta;
- la obra fue excluida y no apareció nueva evidencia material;
- cambió la pregunta central y la duda dejó de ser relevante;
- cambió la versión o adaptación que se estaba evaluando;
- la profundización comenzó a cubrir asuntos no relacionados con la duda declarada;
- se usa la investigación anticipada como promoción implícita a "FINALIST_WORK";
- la evidencia disponible demuestra que el claim o uso previsto no puede sostenerse;
- otra obra ya cubre la función y la candidata no conserva una contribución diferenciada;
- la obra dejó de pertenecer al corpus o intención aprobados;
- la investigación reveló un cambio identitario o de alcance que requiere revisión externa.

RETURN_ROUTE:

Duda resuelta y obra viable
→ volver a SCREENING
→ decidir SCREENED_WORK o promoción a consideración como FINALIST_WORK

Duda resuelta y obra no viable
→ EXCLUDED_WORK
→ conservar motivo y evidencia

Duda no resuelta pero corregible
→ MORE_TARGETED_RESEARCH_REQUIRED
→ regresar a investigación por obra

Evidencia incompatible con el uso
→ BLOCKED_BY_EVIDENCE
→ retirar claim, función o candidatura

Cambio material de pregunta, intención o territorio
→ CHANNEL_INTELLIGENCE_REVIEW_REQUIRED

Impacto sobre promesa visible o packaging temprano
→ YOUTUBE_ADAPTATION_REVIEW_REQUIRED
```

### 4.3 `SP-IR0-MULTILINGUAL_RESEARCH_THRESHOLD`

```text
DECISION_ID:
SP-IR0-MULTILINGUAL_RESEARCH_THRESHOLD

DEFINITION:
La investigación multilingüe se activa cuando limitar la investigación al español produce un riesgo material de cobertura incompleta, dependencia de fuentes derivadas, pérdida de significado o representación sesgada de una controversia.

No se activa por una cuota fija de idiomas ni porque exista material extranjero disponible. Se activa cuando consultar la lengua original o una fuente en otro idioma puede cambiar la suficiencia, interpretación, exactitud o equilibrio de la investigación.

ACTIVATION_CRITERIA:

Se activa cuando existe al menos uno de estos supuestos:

1. "ORIGINAL_SOURCE_NOT_IN_SPANISH"

Una obra, documento, entrevista, declaración, estudio o fuente primaria relevante fue producido en otro idioma y el uso editorial depende de su formulación o contenido exacto.

2. "SPANISH_COVERAGE_DEPENDS_ON_DERIVATIVES"

La cobertura disponible en español proviene principalmente de traducciones, resúmenes, reseñas, vídeos secundarios o reproducciones de una misma fuente original.

3. "MATERIAL_SOURCE_GAP"

No existe en español evidencia suficiente para uno o más claims materiales.

4. "TRANSLATION_SEMANTIC_RISK"

Una palabra, expresión, concepto, diálogo, categoría técnica o matiz cultural puede alterar la interpretación o el claim al traducirse.

5. "CONFLICTING_TRANSLATIONS"

Existen traducciones materially distintas de una misma fuente.

6. "LINGUISTICALLY_SPLIT_CONTROVERSY"

La controversia, recepción o interpretación presenta diferencias relevantes entre comunidades lingüísticas.

7. "LOCAL_CONTEXT_REQUIRED"

El fenómeno o la obra pertenece a un contexto cultural, histórico o institucional cuya información más autorizada se encuentra principalmente en el idioma local.

8. "AUTHORIAL_OR_CREATOR_STATEMENT"

Se pretende utilizar una declaración del autor, director, creador, especialista o protagonista y solo está disponible de forma fiable en otro idioma.

9. "PRIMARY_VERIFICATION_REQUIRED"

Una fuente en español cita, resume o interpreta una fuente extranjera y el claim requiere comprobar el original.

10. "EVIDENCE_SUFFICIENCY_BLOCKED_BY_LANGUAGE"

La decisión de suficiencia está en "MORE_RESEARCH_REQUIRED" o "BLOCKED_BY_EVIDENCE" porque la evidencia relevante no ha sido consultada en su idioma original o en una traducción fiable.

Umbral funcional:

MULTILINGUAL_RESEARCH_REQUIRED
cuando la ausencia de consulta en otro idioma pueda cambiar al menos uno de estos elementos:

- validez de un claim material;
- interpretación de una obra;
- resolución de una contradicción;
- evaluación de suficiencia;
- selección o exclusión de una obra;
- tesis provisional o refinada;
- disclosure o limitación obligatoria.

NON_TRIGGER_EXAMPLES:

- imponer al menos una fuente extranjera en todos los episodios;
- consultar otros idiomas únicamente para aumentar el volumen de fuentes;
- existencia de una traducción oficial suficiente para un claim no sensible;
- disponibilidad de artículos extranjeros que repiten información ya cubierta de forma independiente;
- buscar perspectivas internacionales sin relación con la pregunta central;
- traducir automáticamente todas las fuentes aunque no sean relevantes;
- usar otro idioma como señal automática de mayor autoridad;
- consultar la obra original cuando el uso previsto no depende de una diferencia lingüística y existe una versión autorizada suficiente;
- incluir una fuente extranjera solo para demostrar capacidad técnica.

INVALIDATORS:

La necesidad de investigación multilingüe debe reevaluarse cuando:

- cambia el claim o uso previsto;
- se recupera una fuente primaria suficiente en español;
- aparece una traducción autorizada que resuelve el riesgo material;
- se descubre que varias fuentes multilingües derivan de la misma fuente original;
- la traducción utilizada no conserva original, localizador o método;
- la fuente extranjera no posee autoridad para el claim concreto;
- el episodio cambia de versión, adaptación o contexto cultural;
- la investigación multilingüe introduce una controversia nueva que no ha sido evaluada;
- el contenido traducido no puede verificarse con suficiente confianza;
- la consulta en otro idioma se usa para ocultar que la cobertura general sigue siendo insuficiente.

RETURN_ROUTE:

Original consultado y riesgo resuelto
→ actualizar claim, evidencia, traducción y limitaciones
→ regresar a revisión de suficiencia

Traducción utilizable con reservas
→ LIMITED_BUT_USABLE
→ restringir el claim y declarar limitaciones

Contradicción lingüística no resuelta
→ MORE_RESEARCH_REQUIRED
→ ampliar contraste o solicitar revisión especializada

Significado material no verificable
→ BLOCKED_BY_EVIDENCE
→ retirar claim o uso interpretativo

Hallazgo que transforma pregunta, territorio o límites
→ CHANNEL_INTELLIGENCE_REVIEW_REQUIRED

Hallazgo sobre políticas o funcionamiento de YouTube
→ YOUTUBE_ADAPTATION_REVIEW_REQUIRED
```

### 4.4 `SP-IR0-MATERIAL_CLAIM_THRESHOLD`

```text
DECISION_ID:
SP-IR0-MATERIAL_CLAIM_THRESHOLD

DEFINITION:
Un claim material es una afirmación cuya aceptación, rechazo o formulación puede modificar de manera significativa:

- la comprensión del fenómeno;
- la representación de una obra;
- la selección o función de una obra;
- la tesis;
- la progresión argumental;
- la promesa editorial;
- una conclusión;
- la seguridad ética, factual o interpretativa del episodio.

Todo claim material requiere una "ResearchStopDecision" propia. No puede quedar oculto dentro de una decisión agregada de suficiencia.

La materialidad depende del uso previsto y de sus consecuencias, no únicamente de si la afirmación parece importante en abstracto.

ACTIVATION_CRITERIA:

Un claim es material cuando cumple al menos uno de estos criterios:

1. "THESIS_DEPENDENCY"

La tesis provisional o refinada depende del claim.

2. "CENTRAL_ARGUMENT_DEPENDENCY"

El claim sostiene una premisa, mecanismo causal, contraste, giro o conclusión central.

3. "WORK_SELECTION_DEPENDENCY"

El claim influye en promover, excluir, seleccionar o asignar una función a una obra.

4. "WORK_FIDELITY"

Afirma qué ocurre en una obra, qué decide un personaje, qué se dice, qué consecuencia aparece o qué versión contiene el material relevante.

5. "CAUSAL_OR_PSYCHOLOGICAL_EXPLANATION"

Atribuye causas psicológicas, sociales, históricas, económicas, políticas o culturales.

6. "AUTHORIAL_INTENT"

Atribuye intención, significado deliberado o postura a un autor, director, creador o institución.

7. "SENSITIVE_OR_HARMFUL_ASSERTION"

Puede afectar la representación de personas, grupos, condiciones psicológicas, enfermedades, violencia, abuso, historia, política, derecho, ciencia, religión u otros asuntos sensibles.

8. "NUMERICAL_OR_HISTORICAL_ASSERTION"

Incluye cifras, fechas, estadísticas, cronologías o hechos históricos necesarios para el argumento.

9. "CONTROVERSIAL_OR_DISPUTED_ASSERTION"

Existe desacuerdo relevante entre fuentes o especialistas.

10. "VISIBLE_PROMISE_DEPENDENCY"

El claim es necesario para cumplir la promesa editorial o sostener honestamente una expectativa visible.

11. "OPENING_OR_CONCLUSION_DEPENDENCY"

El claim se utiliza en la apertura, clímax, síntesis o conclusión, donde adquiere mayor peso interpretativo.

12. "REPUTATIONAL_OR_ETHICAL_RISK"

Una formulación incorrecta podría producir daño, desinformación, acusación injustificada o sobreinterpretación.

13. "TRANSLATION_OR_TRANSCRIPTION_DEPENDENCY"

Depende de una traducción, transcripción, cita o formulación cuya exactitud puede cambiar el significado.

14. "RIVAL_READING_IMPACT"

Aceptar o rechazar el claim modifica cuál lectura de una obra o fenómeno es defendible.

15. "REUSE_ORIGINALITY_DEPENDENCY"

El claim es utilizado para justificar que un episodio constituye una continuación válida, una reutilización necesaria o una propuesta suficientemente distinta.

Cada claim material debe recibir uno de estos estados para su uso exacto:

SUFFICIENT_FOR_INTENDED_USE
LIMITED_BUT_USABLE
MORE_RESEARCH_REQUIRED
BLOCKED_BY_EVIDENCE

NON_TRIGGER_EXAMPLES:

- detalles ambientales sin función argumentativa;
- información descriptiva ampliamente conocida y no controvertida que no afecta tesis ni interpretación;
- transiciones retóricas;
- metáforas claramente presentadas como metáforas;
- opiniones autorales declaradas explícitamente como opinión y que no pretenden describir hechos externos;
- ejemplos ilustrativos sustituibles que no sostienen una conclusión;
- datos de producción irrelevantes para la lectura;
- formulaciones estilísticas que no cambian el significado;
- observaciones menores cuya eliminación no altera argumento, obra seleccionada, promesa ni conclusión;
- afirmaciones ya cubiertas por otro claim material equivalente, siempre que no oculten un uso distinto.

INVALIDATORS:

La "ResearchStopDecision" de un claim material deja de ser válida cuando:

- cambia su formulación o alcance;
- cambia el uso previsto;
- pasa de un bloque secundario a apertura o conclusión;
- se incorpora a packaging o promesa visible;
- cambia la tesis;
- cambia la versión o adaptación de la obra;
- aparece nueva evidencia material;
- una fuente es retirada, corregida o pierde vigencia;
- se detecta derivación no declarada entre fuentes;
- aparece una contradicción relevante;
- cambia una traducción o transcripción;
- aumenta la sensibilidad o el riesgo del claim;
- el claim empieza a sostener una causalidad más fuerte;
- se elimina el disclosure o la limitación que permitía "LIMITED_BUT_USABLE";
- cambia el contexto editorial de forma que la misma frase adquiera una implicación diferente.

RETURN_ROUTE:

SUFFICIENT_FOR_INTENDED_USE
→ autorizar únicamente el uso evaluado
→ continuar hacia tesis, análisis o redacción correspondiente

LIMITED_BUT_USABLE
→ restringir formulación
→ incorporar matiz, disclosure o límite
→ revalidar si cambia el uso

MORE_RESEARCH_REQUIRED
→ regresar a investigación del fenómeno,
   investigación por obra,
   investigación multilingüe
   o revisión especializada según el origen

BLOCKED_BY_EVIDENCE
→ retirar el claim
→ sustituirlo
→ reformular la tesis
→ excluir o cambiar la función de la obra si dependía de él

Claim con impacto identitario
→ CHANNEL_INTELLIGENCE_REVIEW_REQUIRED

Claim necesario para promesa visible, packaging o política de plataforma
→ YOUTUBE_ADAPTATION_REVIEW_REQUIRED

Defecto detectado después del ensamblaje
→ regresar al artefacto donde se originó
→ no corregir silenciosamente en edición final
```

---

## 5. Resumen ejecutivo del estado y siguiente decisión

```text
ROADMAP_STATUS:
APPROVED

P08_BASELINE:
APPROVED

IR0_BASELINE:
APPROVED_WITH_FUNCTIONAL_DECISIONS_RESOLVED

IR0_FUNCTIONAL_DECISIONS_REQUIRED:
0

IMPLEMENTATION_SEQUENCE:
DEFINED

CODE_MODIFIED:
NO

CODEX_MISSIONS_PREPARED:
NO

R0_EXECUTION:
NOT_STARTED

IMPLEMENTATION_AUTHORIZED:
NO

NEXT_ACTION:
SEPARATE_OPENING_OF_R0_IN_LIVE_STATE
```

Este roadmap ya fue aprobado por el propietario. La siguiente acción permitida es abrir formalmente R0 en la autoridad única de estado vivo y ejecutar únicamente la misión documental correspondiente.

---

## Efecto de la aprobación del propietario

La aprobación de este roadmap valida su estructura de planeación y autoriza únicamente el bloque documental inicial R0. No constituye autorización general de implementación ni habilita automáticamente fases posteriores.

```text
OWNER_APPROVAL_EFFECT:
AUTHORIZE_R0_ONLY

R1_IMPLEMENTATION:
REQUIRES_SEPARATE_OWNER_AUTHORIZATION

R2_TO_R9:
NOT_AUTHORIZED

IMPLEMENTATION_AUTHORIZED:
NO
```

Después de cerrar R0, el propietario debe revisar su evidencia y emitir una autorización independiente antes de iniciar R1. Cada bloque posterior conserva su propio gate y criterio de autorización.
