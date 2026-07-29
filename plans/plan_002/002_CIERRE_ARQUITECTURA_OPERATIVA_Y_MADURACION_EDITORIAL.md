# PLAN 002 — Cierre de arquitectura operativa y maduración del núcleo editorial

**Proyecto:** Más Allá del Guion / Proyecto YouTube
**Versión:** 1.0.0
**Estado:** `SUPERSEDED_BY_APPROVED_ARCHITECTURE`
**Fecha:** 2026-07-27
**Propietario funcional:** OWNER
**Responsable técnico:** TECHNICAL_GOVERNANCE
**Plan precedente:** PLAN 001 — Reestructuración del motor agéntico, editorial y harness
**Fuente principal:** `auditoria_planeacion_proyecto_youtube_2026-07-27.md`

```text
PLAN_002_DOCUMENT_STATUS = SUPERSEDED_BY_APPROVED_ARCHITECTURE
PLAN_002_OPERATIONAL_AUTHORITY = NOT_GRANTED
PLAN_002_AGENT_ARCHITECTURE = APPROVED_REPLACEMENT_MODEL
PLAN_002_FINAL_DECISION = SUPERSEDED_BY_APPROVED_ARCHITECTURE
OWNER_AGENT_ARCHITECTURE_APPROVAL = APPROVED
R4_STATUS = PASS
R4_CURRENT_PHASE = CLOSED
R4_EXECUTION = NOT_AUTHORIZED
```

---

## 1. Propósito

Este plan cierra la transición entre el sistema heredado de documentos y agente único y el producto editorial versionado, portable, auditable y con verificación independiente.

No reemplaza el Plan 001 ni reinicia sus bloques. Mientras el Plan 003 permanezca activo en R0, este documento conserva valor de propuesta y no puede gobernar el estado vivo ni autorizar implementación operativa. Organiza las correcciones transversales detectadas por la auditoría y las integra con una secuencia propuesta:

```text
MISIONES 1–3 DE B5-I2
→ cerradas y commiteadas

SUBAGENT_FOUNDATION
→ hipótesis de fase intermedia; pendiente de R3, R4 y decisión posterior del propietario

S5 / ejecución real de B5-I2
→ auditoría funcional de SCRIPT_PRODUCT
→ autorización del propietario
→ B5-I3
```

El objetivo final sigue siendo producir un guion profesional, trazable y editorialmente aprobado. La infraestructura, los agentes y los controles son medios para alcanzar ese producto.`r`n`r`nLos nombres de agentes, subagentes, fases y responsabilidades definidos aquí son hipótesis de arquitectura. No son autoridad operativa vigente, no demuestran runtime real y no pueden activarse antes de R3 y R4 del Plan 003 y una decisión posterior del propietario.

---

## 2. Decisiones rectoras

1. Identidad, investigación, diseño editorial, guion y gobernanza permanecen en el mismo repositorio como dominios internos.
2. Audio y Video permanecen en repositorios separados.
3. El MVP activo termina en `EDITORIAL_SCRIPT_APPROVED`.
4. Packaging, miniaturas, Shorts, SEO, publicación y analítica permanecen diferidos salvo controles textuales indispensables de seguridad de plataforma.
5. `EditorialProfile` versionado es la autoridad productiva de identidad y voz.
6. `plans/001_CONTROL_OPERATIVO.md` es la autoridad del estado operativo vigente.
7. Los documentos de `workspace/` no pueden operar como fuente de verdad ejecutable cuando han sido sustituidos.
8. Los nombres Equipo 01–04 pueden conservarse en coordinación humana e historia, pero no como identificadores durables del runtime.
9. Los subagentes se crean por independencia, contexto, permisos o conflicto de interés, no por cantidad decorativa.
10. Un test técnico aprobado no equivale a calidad editorial ni a autorización operativa.
11. Ninguna ejecución sintética puede autorizar una transición funcional real.
12. Las herramientas externas son adaptadores; no son la fuente canónica del producto.

---

## 3. Estado de partida

### 3.1 Cerrado y no debe repetirse

- B5-I2 Misión 1: alineación de alcance y contratos de evidencia.
- B5-I2 Misión 2: provenance de productores y separación del auditor.
- B5-I2 Misión 3: bloqueo de aprobación sintética, separación de resultados, checksum material y transacción atómica.
- Perfil editorial 1.1.0 activo y versionado.
- Runtime híbrido con mock, Ollama, proveedor OpenAI-compatible y handoff externo.
- Contratos, schemas, checksums, invalidación y provenance base.

### 3.2 Pendiente inmediato

- `SUBAGENT_FOUNDATION`.
- Saneamiento de autoridad canónica.
- Suite canónica reproducible y terminante.
- Instalación y empaquetado reproducibles.
- S5 real de B5-I2.
- Auditoría funcional de `SCRIPT_PRODUCT`.
- Autorización del propietario para B5-I3.

### 3.3 Prohibido iniciar todavía

- B5-I3 antes de cerrar B5-I2.
- B6/B7 antes de aprobar B5-I3 y B5.5.
- Stage 2 sin autorización expresa.
- Implementación de NotebookLM, Obsidian, Audio o Video.
- Migración física masiva de carpetas.

---

## 4. Principios de ejecución

### 4.1 Contexto mínimo suficiente

Cada misión deberá contener:

- objetivo;
- archivos iniciales imprescindibles;
- cambios esperados;
- límites;
- validación;
- condición de parada;
- entrega proporcional.

No se pedirá al agente reauditar lo ya diagnosticado.

### 4.2 Cierre dual

Todo bloque relevante exige:

```text
TECHNICAL_GOVERNANCE
→ implementación y auditoría técnica

DOMINIO FUNCIONAL RESPONSABLE
→ auditoría funcional

OWNER
→ autorización cuando corresponda
```

### 4.3 Evidencia real

Un bloque no se cierra solo por:

- schema válido;
- exit code 0;
- fixtures verdes;
- respuesta plausible del modelo.

Debe existir evidencia del comportamiento real requerido por el producto.

---

## 5. Arquitectura canónica multiagente

Estado de esta sección durante R0:

```text
ARCHITECTURE_SECTION_STATUS = PROPOSAL_ONLY
RUNTIME_AUTHORITY = NOT_GRANTED
AGENT_NAMES_AND_RESPONSIBILITIES = HYPOTHESIS_SUBJECT_TO_R3_R4
```

El runtime activo no debe depender de nombres de coordinación humana, chats concretos ni superficies de ChatGPT. La traducción canónica es:

```text
equipo funcional humano
→ dominio del producto
→ responsabilidades
→ agentes productores
→ revisores
→ auditores independientes
→ skills
→ gates
→ componentes deterministas
→ decisiones reservadas al humano
```

### 5.1 Mapa funcional

| Estructura humana de desarrollo | Dominio runtime canónico | Responsabilidades principales | Agentes productores | Revisores | Auditores independientes | Skills / gates / componentes | Decisión reservada al humano |
|---|---|---|---|---|---|---|---|
| Identidad e inteligencia editorial | `CHANNEL_INTELLIGENCE` | identidad, voz, promesa, restricciones del canal | `CHANNEL_INTELLIGENCE_PRODUCER` cuando proceda | `CHANNEL_INTELLIGENCE_REVIEWER` | `CHANNEL_INTELLIGENCE_AUDITOR` | `EditorialProfile`, lineage, gates de perfil | aprobar cambios de identidad, voz y alcance |
| Producto editorial del guion | `SCRIPT_PRODUCT` | brief, investigación útil al episodio, tesis, diseño, guion, edición, dictamen editorial | `EDITORIAL_DESIGN_PRODUCER`, `WRITER`, `EDITOR` | `SCRIPT_PRODUCT_REVIEWER` | `INDEPENDENT_SEMANTIC_VERIFIER`, `FINAL_EDITORIAL_AUDITOR` | skills B5/B6/B7, `b5_i2_gate.py`, auditorías editoriales | aprobar cierre funcional del guion |
| Adaptación textual a YouTube | `YOUTUBE_ADAPTATION` | packaging temprano, adaptación textual, riesgo de plataforma | `YOUTUBE_ADAPTATION_PRODUCER` | `YOUTUBE_ADAPTATION_REVIEWER` | `YOUTUBE_ADAPTATION_AUDITOR` | `EarlyPackagingHypothesis`, checks de riesgo textual | aprobar decisiones visibles de adaptación |
| Infraestructura y gobernanza | `INFRASTRUCTURE_GOVERNANCE` | contratos, runtime, schemas, pruebas, empaquetado, permisos, observabilidad | `ORCHESTRATOR` y componentes deterministas | `TECHNICAL_REVIEWER` | `TECHNICAL_AUDITOR` | registries, schemas, harness, gates, tests, empaquetado | aprobar cambios técnicos estructurales |

Los equipos humanos pueden aparecer como contexto histórico o estructura de trabajo, pero el runtime, los contratos, los estados, los owners y los enums activos deben usar dominios neutrales y roles funcionales.

### 5.2 Matriz de producción y auditoría

| Salida relevante | Productor | Revisor | Auditor independiente | Gate | Máximo de ciclos | Condición de bloqueo | Escalamiento humano |
|---|---|---|---|---|---|---|---|
| inteligencia e identidad del canal | `CHANNEL_INTELLIGENCE_PRODUCER` | `CHANNEL_INTELLIGENCE_REVIEWER` | `CHANNEL_INTELLIGENCE_AUDITOR` | lineage + perfil activo | 2 | checksum, aprobación o lineage incoherente | `OWNER_APPROVER` |
| investigación y fuentes | `RESEARCH_AND_CURATION_PRODUCER` | `SCRIPT_PRODUCT_REVIEWER` | `FINAL_EDITORIAL_AUDITOR` | evidence sufficiency | 2 | evidencia insuficiente o fuente no verificable | `SCRIPT_PRODUCT` |
| diseño editorial | `EDITORIAL_DESIGN_PRODUCER` | `SCRIPT_PRODUCT_REVIEWER` | `INDEPENDENT_SEMANTIC_VERIFIER` | `b5_i2_gate.py` | 2 | hallazgos críticos sin resolver | `SCRIPT_PRODUCT` |
| arquitectura narrativa | `NARRATIVE_ARCHITECTURE_PRODUCER` | `SCRIPT_PRODUCT_REVIEWER` | `FINAL_EDITORIAL_AUDITOR` | gate narrativo futuro | 2 | tensión/outline sin soporte | `SCRIPT_PRODUCT` |
| escritura del guion | `WRITER` | `EDITOR` | `FINAL_EDITORIAL_AUDITOR` | validación estructural y editorial | 3 | incumplimiento crítico repetido | `SCRIPT_PRODUCT` |
| revisión de oralidad y estilo | `EDITOR` | `SCRIPT_PRODUCT_REVIEWER` | `FINAL_EDITORIAL_AUDITOR` | QA editorial | 2 | identidad/voz inestables | `CHANNEL_INTELLIGENCE` |
| verificación factual | `FACTUAL_REVIEWER` | `SCRIPT_PRODUCT_REVIEWER` | `FINAL_EDITORIAL_AUDITOR` | fact check report | 2 | claim crítico sin trazabilidad | `SCRIPT_PRODUCT` |
| adaptación a YouTube | `YOUTUBE_ADAPTATION_PRODUCER` | `YOUTUBE_ADAPTATION_REVIEWER` | `YOUTUBE_ADAPTATION_AUDITOR` | gate de adaptación textual | 2 | promesa visible deshonesta o riesgo alto | `YOUTUBE_ADAPTATION` |
| packaging | `YOUTUBE_ADAPTATION_PRODUCER` | `YOUTUBE_ADAPTATION_REVIEWER` | `YOUTUBE_ADAPTATION_AUDITOR` | hypothesis / package gate | 2 | desalineación con tesis o plataforma | `YOUTUBE_ADAPTATION` |
| riesgo de plataforma | `YOUTUBE_ADAPTATION_REVIEWER` | `SCRIPT_PRODUCT_REVIEWER` | `YOUTUBE_ADAPTATION_AUDITOR` | risk gate | 2 | riesgo `HIGH` o `UNRESOLVED` | `OWNER_APPROVER` |
| auditoría editorial final | ninguno; solo dictamen | `SCRIPT_PRODUCT_REVIEWER` recibe defectos | `FINAL_EDITORIAL_AUDITOR` | final editorial audit | 2 | persistencia de defectos críticos | `OWNER_APPROVER` |

### 5.3 Revisión humana

```text
DESARROLLO DEL SISTEMA
→ revisión humana del repositorio al terminar una misión o una fase significativa

PRODUCCIÓN EDITORIAL
→ los agentes producen, revisan, auditan y corrigen antes de entregar
```

La intervención humana ordinaria en producción debe ser una aprobación final o una decisión estratégica. Revisiones humanas adicionales solo proceden por `BLOCKED`, riesgo no resuelto, baja confianza, cambio de alcance o decisión de producto.

### 5.4 Independencia operativa

1. Un productor no puede aprobar su propia salida.
2. Productor, revisor y auditor deben ejecutar runs distintos cuando su separación sea requerida por el contrato.
3. El auditor debe revisar una versión exacta y un checksum exacto.
4. La independencia mínima exigible en B5-I2 es `producer_run_id` distinto de `auditor_run_id`, skill/version verificables y manifiesto de entrada con checksum exacto.
5. Los ciclos automáticos deben ser limitados por contrato; exceder el límite produce `BLOCKED`.
6. Los estados activos no pueden depender de `TEAM_*`, de nombres de chat ni de “esperar a ChatGPT”.
7. `SUBAGENT_FOUNDATION` debe declarar capacidad, integración y demostración solo con evidencia real observada.

### 5.5 Inventario breve de saneamiento para esta misión

| Superficie | Decisión |
|---|---|
| `AGENTS.md`, `README.md`, `plans/002...` | `CORREGIR` |
| `.agent/skills`, `.agent/workflows`, `config/skill_catalog.json` | `CORREGIR` |
| `schemas/b5_i2_semantic_sufficiency_audit.json`, `schemas/early_packaging_hypothesis.json`, `config/subagent_registry.json`, `schemas/subagent_registry.json`, `src/ai/subagents.py`, `src/scripts/b5_i2_gate.py`, `src/scripts/run_b5_i2_semantic_audit.py` | `CORREGIR` |
| tests dirigidos de B5-I1, B5-I2 y foundation | `CORREGIR` |
| perfiles aprobados y documentación histórica clasificada | `CONSERVAR` o `HISTÓRICO`; no neutralizar en sitio |
| referencias heredadas solo útiles para migración futura | `MIGRAR` o `DEPRECAR` según inventario posterior |

---

# 6. Fases de implementación

## FASE 0 — Reconciliación del estado y congelación de base

**Objetivo:** establecer un punto de partida verificable sin modificar funcionalidad.

### Trabajo

1. Confirmar los hashes completos de los commits de las Misiones 1–3.
2. Verificar que el working tree no contenga cambios de esas misiones sin commit.
3. Registrar en `plans/001_CONTROL_OPERATIVO.md`:
   - Misiones 1–3 cerradas;
   - `SUBAGENT_FOUNDATION` como siguiente fase obligatoria;
   - S5 bloqueado hasta su cierre;
   - B5-I3 no autorizado.
4. Capturar baseline de pruebas dirigidas y estado Git.
5. No corregir todavía otras deudas.

### Gate de salida

```text
BASELINE_RECONCILED=PASS
MISSION_1_3_COMMITS_CONFIRMED=PASS
CURRENT_STATE_CANONICAL=PASS
```

---

## FASE 1 — SUBAGENT_FOUNDATION

**Objetivo:** crear la base neutral, portable y verificable para ejecutar responsabilidades independientes sin reconstruir el runtime.

### Alcance funcional mínimo

Crear un contrato de ejecución de agentes que distinga:

```yaml
execution_role: root | subagent
functional_role: orchestrator | researcher | producer | writer | editor | verifier
```

Cada definición debe incluir:

- identidad y versión;
- propósito;
- inputs y outputs;
- contexto permitido;
- memoria permitida;
- skills permitidas;
- tools y permisos;
- proveedor/modelo configurable;
- presupuesto;
- retries y timeout;
- handoff;
- provenance;
- evidencia;
- estado de madurez.

### Capacidades obligatorias

1. Registro neutral de agentes/subagentes.
2. Contexto aislado por run.
3. Handoff versionado.
4. Provenance independiente.
5. Compatibilidad rol–artefacto.
6. Prohibición de autoaprobación.
7. Permisos de lectura/escritura por rol.
8. Estado de madurez:

```text
AGENT_DESIGNED
→ AGENT_IMPLEMENTED
→ AGENT_TESTED_IN_ISOLATION
→ AGENT_INTEGRATED
→ AGENT_DEMONSTRATED
```

9. Ejecución sintética para pruebas sin readiness real.
10. Política de máximo 2–3 ciclos en loops futuros.

### Subagentes mínimos a demostrar

Para B5-I2:

```text
EDITORIAL_DESIGN_PRODUCER
INDEPENDENT_SEMANTIC_VERIFIER
```

No crear todavía escritor, editor o auditor final completos; solo dejar la foundation reutilizable.

### Pruebas

- aislamiento de contexto;
- permisos denegados;
- productor no puede aprobar;
- verificador no puede modificar el artefacto;
- provenance distinta;
- handoff alterado rechazado;
- rol desconocido rechazado;
- ejecución sintética bloqueada para readiness;
- subagente no ejecutable no puede activarse;
- compatibilidad con proveedor mock y ruta real simulada.

### Gates de salida

```text
AGENT_DEPENDENCY_GATE=PASS
SUBAGENT_CONTEXT_ISOLATION=PASS
SUBAGENT_PERMISSION_BOUNDARIES=PASS
SUBAGENT_PROVENANCE_INDEPENDENT=PASS
B5_SEMANTIC_AUDITOR_INDEPENDENT=PASS
```

---

## FASE 2 — S5: ejecución real de B5-I2

**Objetivo:** demostrar la vertical real multiagente de B5-I2.

### Secuencia

```text
EDITORIAL_DESIGN_PRODUCER
→ gates deterministas
→ INDEPENDENT_SEMANTIC_VERIFIER
→ dictamen estructurado
→ corrección limitada
→ reauditoría
```

### Casos mínimos

1. Un caso editorialmente suficiente.
2. Un caso deliberadamente defectuoso.
3. Un caso con evidencia insuficiente que debe bloquear.

### Requisitos

- runs separados;
- contexto curado;
- proveedor real autorizado o modelo local suficiente;
- provenance independiente;
- material checksum real;
- handoff atómico;
- auditor sin permiso de escritura sobre artefactos;
- máximo 2 ciclos de corrección;
- costes y tiempos registrados aunque sea de forma provisional.

### Cierre

1. Auditoría técnica de `TECHNICAL_GOVERNANCE`.
2. Auditoría funcional de `SCRIPT_PRODUCT`.
3. Correcciones necesarias.
4. Autorización expresa del propietario.

### Gate técnico de salida

```text
B5_REAL_VERTICAL_EXECUTED=PASS
B5_SEMANTIC_AUDITOR_INDEPENDENT=PASS
B5_TECHNICAL_AUDIT=PASS
```

---

## FASE 3 — Auditoría funcional y decisión sobre B5-I2

**Objetivo:** decidir si la ejecución real de B5-I2 sirve editorialmente antes de cualquier autorización para B5-I3.

### Trabajo

1. Entregar al dominio `SCRIPT_PRODUCT`:
   - artefactos reales;
   - auditoría semántica independiente;
   - evidencia y provenance;
   - correcciones aplicadas;
   - resultado de reauditoría.
2. Ejecutar auditoría funcional de `SCRIPT_PRODUCT`.
3. Corregir únicamente defectos funcionales confirmados.
4. Repetir la auditoría funcional cuando proceda.
5. Preparar la decisión del propietario.
6. No autorizar B5-I3 mientras existan defectos bloqueantes.

### Gate funcional de salida

```text
B5_FUNCTIONAL_REAUDIT=PASS
B5_I2_FINAL_STATUS=PASS
```

La autorización del propietario se emitirá después de completar también las Fases 4 y 5, porque los hallazgos P0 de autoridad, pruebas, lineage e instalación deben quedar cerrados antes de B5-I3.

---

## FASE 4 — Autoridad canónica y saneamiento documental

**Objetivo:** eliminar la convivencia de dos arquitecturas ejecutables sin realizar una migración física masiva.

### Trabajo

1. Crear `AGENTS.md` raíz, corto y neutral.
2. Crear mapa canónico de autoridad.
3. Clasificar cada documento de `workspace/` como:
   - `ACTIVE_REFERENCE`;
   - `HISTORICAL`;
   - `SUPERSEDED`;
   - `NON_EXECUTABLE`.
4. Marcar `workspace/00_sistema_agentes_v1.md` como superado y no ejecutable.
5. Corregir README para que no reconstruya identidad desde `workspace/`.
6. Establecer de forma inequívoca:
   - `EditorialProfile` → identidad y voz;
   - `001_CONTROL_OPERATIVO.md` → estado;
   - contratos/schemas → estructuras ejecutables;
   - `AGENTS.md` → entrada operativa.
7. Corregir `prompt_version: PENDING_B4_I2` en el registro de responsabilidades.
8. Sustituir nombres Equipo 01–04 en runtime, schemas, configuración y catálogos ejecutables por dominios neutrales.
9. Conservar nombres de equipos en documentación humana e histórica cuando aporten trazabilidad.
10. Definir mapa lógico de dominios sin mover carpetas todavía.

### Gates de salida

```text
CANONICAL_AUTHORITY_SINGLE=PASS
LEGACY_DOCUMENTS_CLASSIFIED=PASS
ROOT_AGENT_ENTRYPOINT=PASS
FUNCTIONAL_DOMAINS_NEUTRAL=PASS
```

---

## FASE 5 — Estabilización de calidad, instalación y empaquetado

**Objetivo:** garantizar que el repositorio pueda instalarse, probarse y entregarse de forma repetible.

### 3.1 Suite canónica

1. Corregir los tres fallos B4-I1:
   - conteo 21 → 22;
   - segunda aserción equivalente;
   - referencia ejecutable a `YOUTUBE_ADAPTATION`.
2. Ejecutar pruebas por archivo con timeout y reporte de duración.
3. Aislar el test o proceso que impide terminar la suite completa.
4. Definir un único comando canónico de pruebas.
5. Añadir reporte de test lento/timeout.
6. Actualizar APIs de `jsonschema` obsoletas cuando sea seguro.

### 3.2 Instalación reproducible

Adoptar:

```text
pyproject.toml
uv.lock
```

Incluir:

- versión de Python;
- dependencias runtime;
- dependencias dev;
- comandos de instalación;
- smoke test desde entorno limpio;
- CI mínima en Linux.

### 3.3 Empaquetado por allowlist

Crear un script canónico que:

- incluya solo rutas permitidas;
- excluya `config/local_settings.json`;
- excluya `.runtime-tmp/`, caches, outputs históricos y ZIPs anteriores;
- genere manifiesto y checksum;
- ejecute scanner básico de secretos;
- pruebe instalación y tests desde el ZIP generado.

### 3.4 Lineage del perfil

1. Reparar o sustituir referencias faltantes sin inventar evidencia.
2. Definir semántica única de:
   - `DRAFT`;
   - `APPROVED`;
   - `ACTIVE`;
   - `SUPERSEDED`.
3. Validar puntero, payload, aprobación y checksum.
4. Añadir test de integridad de lineage.

### Gates de salida

```text
SKILL_REGISTRY_CONSISTENT=PASS
FULL_TEST_SUITE_TERMINATES=PASS
FRESH_INSTALL_REPRODUCIBLE=PASS
PACKAGING_HYGIENE=PASS
EDITORIAL_PROFILE_LINEAGE_INTEGRITY=PASS
```

---

## FASE 6 — B5-I3 y B5.5: arquitectura narrativa y prototipo editorial

**Objetivo:** completar el diseño narrativo antes de redactar el guion completo.

### B5-I3

Implementar:

- recorrido del espectador;
- `OPENING_UNIT`;
- cierre;
- arquitectura narrativa;
- presupuesto de palabras;
- outline completo;
- variedad estructural;
- memoria global;
- relación entre bloques;
- promesa editorial interna.

### B5.5

Crear prototipo controlado de:

- apertura;
- uno o dos bloques;
- transiciones;
- lectura oral;
- comparación contra baseline.

Separar:

```text
TEST TÉCNICO
BENCHMARK EDITORIAL
EXPERIMENTO
EVALUACIÓN HUMANA
```

Registrar variables fijas y modificadas.

### Gates

```text
NARRATIVE_ARCHITECTURE_APPROVED=PASS
OPENING_UNIT_EDITORIAL_APPROVAL=PASS
PROTOTYPE_EDITORIAL_BENCHMARK=PASS
EXPERIMENT_VARIABLE_CONTROL=PASS
```

---

## FASE 7 — B6–B7: producción profesional del guion

**Objetivo:** implementar redacción, edición y auditoría final con independencia real.

### Topología

```text
ORCHESTRATOR
├── WRITER
├── EDITOR
└── FINAL_EDITORIAL_VERIFIER
```

### Responsabilidades

- Writer produce por bloques con contexto global.
- Editor modifica y documenta cambios.
- Auditor final no modifica: dicta, bloquea y enruta.
- Researcher se separa cuando herramientas externas, volumen o riesgo factual lo justifiquen.

### Loop de reparación

```text
PRODUCIR
→ VALIDAR FORMA
→ VERIFICAR CONTENIDO
→ DEVOLVER DEFECTOS
→ CORREGIR
→ REEVALUAR
```

Máximo 2–3 ciclos. Persistencia de defectos críticos implica escalamiento humano.

### Controles adicionales obligatorios

1. Enforcement de estado ejecutable de skills.
2. Gateway central de tools y permisos.
3. Budgets de tokens, coste, turnos, retries, timeout y latencia.
4. Observabilidad por agente, rol y fase.
5. Política contra prompt injection y datos externos tratados como instrucciones.
6. Archivo controlado de outputs y auditorías históricas.
7. Validación textual de riesgos de YouTube, monetización y copyright que sí afecten al guion.

### Gates

```text
WRITER_INDEPENDENCE=PASS
EDITOR_INDEPENDENCE=PASS
FINAL_AUDITOR_INDEPENDENCE=PASS
REPAIR_LOOP_BOUNDED=PASS
TOOL_PERMISSION_ENFORCEMENT=PASS
TOKEN_COST_OBSERVABILITY=PASS
EXTERNAL_SOURCE_TRUST_POLICY=PASS
EDITORIAL_SCRIPT_APPROVED=PASS
```

---

## FASE 8 — Contratos de conocimiento e integraciones futuras

**Objetivo:** diseñar interfaces sin implementar conectores ni mezclar repositorios.

### 7.1 Fuente canónica de investigación

Definir Vault/repositorio de evidencias con:

- fuente original;
- autor/título/fecha;
- localizador;
- método de adquisición;
- checksum;
- fragmentos relevantes;
- claims asociados;
- estado de verificación;
- revisión y vigencia;
- restricciones de uso.

### 7.2 NotebookLM

Diseñar contrato para:

1. cuaderno temporal de investigación;
2. cuaderno de memoria editorial aprobada.

NotebookLM no será fuente de verdad.

### 7.3 Obsidian

Definirlo como interfaz humana portable sobre Markdown/Vault, sin segunda verdad.

### 7.4 Seguridad

Todo conector futuro debe emitir:

```yaml
source_origin:
source_locator:
retrieval_method:
external_workspace_id:
retrieved_at:
content_checksum:
verification_status:
trusted_as_instruction: false
```

### 7.5 Audio y Video

Diseñar `EDITORIAL_SCRIPT_PACKAGE` y contratos de retorno:

- versión;
- compatibilidad;
- checksum;
- aprobación;
- invalidación;
- feedback;
- reentrega;
- autoridad sobre cambios de vuelta.

No implementar runtimes de Audio o Video.

### Gates

```text
KNOWLEDGE_VAULT_CONTRACT=PASS
NOTEBOOKLM_CONTRACT_DESIGNED=PASS
OBSIDIAN_CONTRACT_DESIGNED=PASS
EXTERNAL_SOURCE_TRUST_POLICY=PASS
AUDIO_VIDEO_CONTRACTS_DESIGNED=PASS
```

---

## FASE 9 — B9, B9.5 y B10: validación, aprendizaje y cierre

**Objetivo:** demostrar que el sistema produce calidad consistente y cerrar el MVP de manera portable.

### Pilotos obligatorios

1. Episodio evergreen.
2. Episodio híbrido o de oportunidad.
3. Episodio con evidencia difícil o insuficiente.

Deben incluir estructuras narrativas diferentes.

### Medición

- precisión de gates;
- falsos PASS;
- falsos FAIL;
- calidad comparada con evaluación humana;
- coste y latencia por episodio/agente;
- número de ciclos de corrección;
- defectos repetidos;
- estabilidad del perfil y lineage.

### Aprendizaje

```text
observación
→ hipótesis
→ benchmark/experimento
→ evidencia acumulada
→ aprendizaje candidato
→ revisión humana
→ aprobación
→ nueva versión
```

No activar reglas por un solo episodio.

### Lean/5S

- archivar históricos;
- eliminar caches y temporales;
- retirar skills superadas;
- resolver documentación duplicada;
- verificar portabilidad;
- evaluar extracciones solo con evidencia de ciclo de vida independiente.

### Stage 2

Solo puede activarse mediante autorización expresa posterior al cierre del MVP.

### Gates

```text
THREE_REAL_PILOTS=PASS
DIFFICULT_EVIDENCE_CASE=PASS
NARRATIVE_VARIETY_DEMONSTRATED=PASS
GATE_CALIBRATION=PASS
HUMAN_AI_EVALUATOR_CALIBRATION=PASS
COST_LATENCY_BASELINE=PASS
LEAN_PORTABILITY_CLOSURE=PASS
STAGE_2_EXPLICIT_AUTHORIZATION=PASS_OR_NOT_REQUESTED
```

---

# 7. Matriz de cobertura de la auditoría

## P0

| Hallazgo de auditoría | Cobertura en este plan |
|---|---|
| `AGENTS.md` y mapa de autoridad | Fase 4 |
| Saneamiento de `workspace/` | Fase 4 |
| Perfil versionado como única autoridad | Fases 4 y 5 |
| Neutralizar equipos internos en ejecutables | Fase 4 |
| Corregir tests B4-I1 y catálogo de 22 skills | Fase 5 |
| Corregir `prompt_version` obsoleto | Fase 4 |
| Eliminar prohibición fija de subagentes | Fase 1 |
| Auditor semántico independiente B5-I2 | Fases 1 y 2 |
| Reauditoría funcional antes de avanzar | Fase 3 |
| Reparar lineage y estados del perfil | Fase 5 |
| Empaquetado por allowlist | Fase 5 |
| Suite completa terminante | Fase 5 |

## P1

| Recomendación | Cobertura |
|---|---|
| Writer, editor y auditor independientes | Fase 7 |
| Loop de reparación limitado | Fase 7 |
| Enforcement de activación de skills | Fase 7 |
| Gateway de tools y permisos | Fase 7 |
| Budgets de tokens/coste/turnos/retries/timeout | Fase 7 |
| Instalación reproducible y CI | Fase 5 |
| Archivar outputs y auditorías históricas | Fases 7 y 9 |
| Política de fuentes externas/prompt injection | Fases 7 y 8 |
| Contratos NotebookLM y Obsidian | Fase 8 |
| Paquetes Audio y Video | Fase 8 |

## P2

| Recomendación | Cobertura |
|---|---|
| Tres pilotos reales | Fase 9 |
| Caso de evidencia insuficiente | Fases 2 y 9 |
| Estructuras narrativas diferentes | Fases 6 y 9 |
| Medir falsos PASS/FAIL | Fase 9 |
| Medir coste y latencia | Fases 7 y 9 |
| Calibrar evaluadores IA/humanos | Fase 9 |
| Stage 2 solo con autorización | Fase 9 |
| Evaluar extracciones por evidencia | Fase 9 |

---

# 8. Cobertura de gates recomendados por la auditoría

| Gate | Fase de cierre |
|---|---|
| `CANONICAL_AUTHORITY_SINGLE` | Fase 4 |
| `LEGACY_DOCUMENTS_CLASSIFIED` | Fase 4 |
| `ROOT_AGENT_ENTRYPOINT` | Fase 4 |
| `FUNCTIONAL_DOMAINS_NEUTRAL` | Fase 4 |
| `SKILL_REGISTRY_CONSISTENT` | Fase 5 |
| `FULL_TEST_SUITE_TERMINATES` | Fase 5 |
| `FRESH_INSTALL_REPRODUCIBLE` | Fase 5 |
| `B5_SEMANTIC_AUDITOR_INDEPENDENT` | Fases 1 y 2 |
| `B5_FUNCTIONAL_REAUDIT` | Fase 3 |
| `AGENT_DEPENDENCY_GATE` | Fase 1 |
| `TOOL_PERMISSION_ENFORCEMENT` | Fase 7 |
| `TOKEN_COST_OBSERVABILITY` | Fase 7 |
| `EXTERNAL_SOURCE_TRUST_POLICY` | Fases 7 y 8 |
| `PACKAGING_HYGIENE` | Fase 5 |
| `AUDIO_VIDEO_CONTRACTS_DESIGNED` | Fase 8 |

Todos los gates de la auditoría quedan asignados a una fase y a un criterio de salida.

---

# 9. Dependencias y orden obligatorio

```text
FASE 0
→ FASE 1 SUBAGENT_FOUNDATION
→ FASE 2 S5 real B5-I2
→ FASE 3 auditoría funcional SCRIPT_PRODUCT
→ FASE 4 autoridad canónica
→ FASE 5 estabilización reproducible
→ autorización OWNER
→ FASE 6 B5-I3/B5.5
→ FASE 7 B6/B7
→ FASE 8 contratos futuros
→ FASE 9 pilotos y cierre
```

### Paralelismo permitido

Después de cerrar Fase 3:

- Fase 4 y Fase 5 pueden avanzar en paralelo mediante worktrees, siempre que no modifiquen los mismos archivos.
- Fase 8 documental puede comenzar después de `EDITORIAL_SCRIPT_APPROVED`, sin bloquear B9 salvo contratos indispensables.

### Paralelismo prohibido

- S5 no puede ejecutarse antes de Fase 1.
- Fases 4 y 5 no sustituyen la auditoría funcional de B5-I2, pero sus gates P0 deben cerrarse antes de la autorización del propietario.
- B5-I3 no puede iniciarse antes de cerrar S5, auditoría funcional, Fases 4–5 y autorización del propietario.
- B6/B7 no pueden iniciarse antes de B5.5.
- Stage 2 no puede activarse por continuidad automática.

---

# 10. Política de commits y auditorías

Cada fase debe ejecutarse mediante incrementos pequeños y auditables.

Un incremento solo puede commitearse cuando:

- las pruebas dirigidas pasan;
- `git diff --check` pasa;
- no contiene archivos locales o temporales;
- la auditoría externa técnica lo aprueba;
- la auditoría funcional correspondiente se registra cuando aplique.

No se crearán documentos de respuesta funcional temporales solo para demostrar una conversación. Las decisiones deben registrarse en sedes canónicas y durables.

---

# 11. Definition of Done del PLAN 002

El plan se considera completado cuando:

1. Existe una sola autoridad canónica por tipo de decisión.
2. Los documentos heredados están clasificados y no gobiernan ejecución.
3. Existe `AGENTS.md` neutral.
4. La foundation de subagentes está implementada y demostrada.
5. B5-I2 se ejecutó realmente y recibió aprobación funcional.
6. B5-I3, B5.5, B6 y B7 producen `EDITORIAL_SCRIPT_APPROVED`.
7. Writer, editor y auditor son independientes.
8. La suite completa termina de forma confiable.
9. La instalación limpia es reproducible.
10. El empaquetado es seguro y limpio.
11. Tools, skills y permisos se aplican en runtime.
12. Tokens, coste y latencia son observables.
13. Las fuentes externas se tratan como datos, no instrucciones.
14. NotebookLM y Obsidian tienen contratos sin convertirse en fuente de verdad.
15. Audio y Video tienen contratos de integración, sin mezclarse con este repositorio.
16. Tres pilotos demuestran calidad, variedad y calibración.
17. B10 cierra deuda, portabilidad y documentación.
18. Stage 2 permanece diferido o cuenta con autorización expresa.

---

# 12. Próxima acción autorizable

La primera misión derivada de este plan debe ser:

```text
PLAN-002-F0-RECONCILE-BASELINE
```

Después:

```text
PLAN-002-F1-SUBAGENT-FOUNDATION
```

No se autoriza todavía S5 ni B5-I3.

---

## Estado final del documento

```text
PLAN_002_COVERAGE_REVIEW: PASS
AUDIT_FINDINGS_COVERED: 30/30
AUDIT_GATES_COVERED: 15/15
PLAN_002_DOCUMENT_STATUS: PROPOSAL
PLAN_002_OPERATIONAL_AUTHORITY: NOT_GRANTED
PLAN_002_AGENT_ARCHITECTURE: NOT_APPROVED
PLAN_002_FINAL_DECISION: SUPERSEDED_BY_APPROVED_ARCHITECTURE
IMPLEMENTATION_AUTHORIZED: NO
NEXT_REQUIRED_APPROVAL: OWNER
NEXT_TECHNICAL_ACTION_AFTER_APPROVAL: FASE_0
```
