# PLAN 003 — Recuperación, reconciliación y cierre de falsos positivos

**Versión:** `1.0.0`
**Estado:** `APPROVED_ACTIVE`
**Implementación autorizada:** `COMPLETED_THROUGH_R6_B_POST_DIAGNOSTIC_RECONCILIATION`
**Tipo:** Plan correctivo temporal
**Plan rector del producto:** `PLAN 001 — Reestructuración del sistema agéntico, del motor editorial y del arnés de control`
**Plan relacionado:** `PLAN 002 — Cierre de arquitectura operativa y maduración del núcleo editorial`
**Fecha de creación:** `2026-07-28`
**Aprobación del propietario:** `2026-07-28`
**current_phase:** `R6_B_POST_DIAGNOSTIC_RECONCILIATION_CLOSED`
**implementation_completed_through:** `R6_B_POST_DIAGNOSTIC_RECONCILIATION`
**next_phase:** `TEAM_03_R3_IMPLEMENTATION`
**R6_B_STATUS:** `BLOCKED_PENDING_TEAM_03_R3_IMPLEMENTATION`
**R6_B_0_EXTERNAL_AUDIT:** `PASS`
**PLAN_003_STATUS:** `APPROVED_ACTIVE`
**PLAN_003_FINAL_CLOSURE:** `OPEN`

---

## 0. Inventario de numeración y justificación del identificador

La carpeta `plans/` contiene actualmente:

```text
plans/
├── 001_CONTROL_OPERATIVO.md
├── 001_reestructuracion_motor_agentico_editorial_y_harness.md
├── plan_001/
├── plan_002/
└── plan_003/
```

La carpeta `plan_001/` contiene especificaciones derivadas de los bloques `B0` a `B10`; no representa planes adicionales numerados.

Conclusión del inventario:

```text
PLAN 001 = existente
PLAN 002 = existente
PLAN 003 = siguiente numeración libre
```

El nombre externo “Plan de acción 12” no aparece como identificador canónico dentro del repositorio. Hasta que se documente una equivalencia expresa, no debe utilizarse para gobernar estados, dependencias ni misiones.

Este archivo adopta por tanto el identificador canónico:

```text
PLAN 003
```

---

## 1. Propósito

Este plan corrige falsos cierres, contradicciones de autoridad, estados no sustentados por evidencia y componentes declarados como terminados sin estar funcionalmente completos.

No reemplaza el Plan 001 ni vuelve a planear todo el producto.

Su función es:

```text
contener avances incompatibles
→ reconciliar planes y autoridades
→ corregir falsos positivos
→ recuperar evidencia y aprobaciones
→ cerrar pendientes de saneamiento
→ redefinir correctamente la arquitectura agéntica
→ devolver el control al Plan 001
```

El Plan 003 es temporal. Debe cerrarse cuando los bloques reabiertos queden reconciliados y exista una única siguiente acción válida dentro del Plan 001.

---


## 1.1 Estado vivo reconciliado posterior a R6-B

El estado vivo posterior al diagnóstico de Ollama, la no recuperación de la evidencia real anterior de R6-B, la implementación técnica de `SCRIPT_PRODUCT` para B5-I2, la reparación transversal de integridad textual y la recepción de la ampliación funcional de `YOUTUBE_ADAPTATION` queda así:

```text
OLLAMA = DEFERRED
OLLAMA_DIAGNOSTIC = CLOSED
OLLAMA_OPTIMIZATION = DEFERRED
OLLAMA_MODEL_SELECTION = NONE
OLLAMA_FULL_CONTRACT_ROUTE = NOT_VIABLE_ON_CURRENT_HARDWARE
R6_B_REAL_PRODUCER_EVIDENCE = NOT_RECOVERED
R6_B_REAL_AUDITOR_EXECUTION = BLOCKED
R6_B_PRODUCER_AUDITOR_INDEPENDENCE = NOT_DEMONSTRATED
R6_B_VERTICAL_DEMONSTRATED = NO
R6_B_TECHNICAL_CLOSURE = OPEN
TEAM_02_B5_I2_FUNCTIONAL_SPECIFICATION = COMPLETE
TEAM_02_B5_I2_IMPLEMENTATION = PASS
TEAM_02_B5_I1_FUNCTIONAL_SPECIFICATION = PENDING_COMPLETION
TEAM_03_R3_FUNCTIONAL_SPECIFICATION = COMPLETE
TEAM_03_R3_IMPLEMENTATION = PENDING
TEXT_INTEGRITY_REPAIR = PASS
TEXT_INTEGRITY_PREVENTION = ACTIVE
NEXT_ALLOWED_ACTION = B5_5_M2_TECHNICAL_OPERATIONAL_SANITATION
```

Esta sección es una proyección sincronizada del estado vivo. La sede canónica única permanece en `plans/001_CONTROL_OPERATIVO.md`. Las menciones posteriores a `SELECTED_PROVIDER = ollama`, `SELECTED_MODEL = Qwen2.5-Coder:latest` o a la autorización y ejecución de R6-B deben leerse únicamente como snapshots históricos del estado observado en fases anteriores, no como estado operativo vigente.

## 2. Alcance

### 2.1 Incluido

- autoridad documental y operativa;
- reconciliación entre Plan 001, Plan 002, `AGENTS.md` y control operativo;
- corrección de falsos `PASS` o cierres parciales;
- recuperación o reconstrucción de evidencia faltante;
- cobertura real del guard de contaminación;
- saneamiento de especificaciones operativas activas;
- recuperación de requisitos funcionales de los especialistas;
- decisión correcta entre agente, subagente, skill, script, regla, gate, workflow y decisión humana;
- aprobación de la arquitectura agéntica antes de implementarla;
- cierre funcional y técnico del `EditorialProfile 1.2.1`;
- cierre multidimensional de B0, B3, B4, B5-I1 y B5-I2;
- integración automática del guard;
- estabilización mínima de pruebas, instalación y empaquetado necesaria para demostrar los cierres;
- retorno controlado al Plan 001.

### 2.2 Excluido

Mientras este plan permanezca abierto no se autoriza:

- B5-I3;
- S5 real;
- B5.5;
- B6;
- B7;
- Etapa 2;
- producción de episodios reales;
- packaging final;
- Shorts;
- SEO;
- publicación;
- NotebookLM;
- Obsidian;
- memoria semántica avanzada;
- integración con Audio;
- integración con Video;
- creación simultánea de toda la arquitectura multiagente;
- activación automática de aprendizajes o reglas.

---

## 3. Principios rectores

### 3.1 No crear una tercera arquitectura competidora

El Plan 003 puede corregir estados, dependencias, autoridades y evidencias, pero no redefine unilateralmente el producto del Plan 001.

### 3.2 Un cierre técnico no equivale a un cierre funcional

```text
TESTS_PASS
≠ FUNCTIONAL_APPROVAL
≠ REAL_EXECUTION
≠ OWNER_APPROVAL
≠ FINAL_CLOSURE
```

### 3.3 Un prompt o registro no equivale a un agente

Un agente solo existe operativamente cuando demuestra ejecución real, contexto separado, contratos, permisos aplicados, handoff, bloqueo, retries, provenance, costes y revisión funcional.

### 3.4 Ningún plan en estado de propuesta puede gobernar la ejecución

Un plan puede pasar a autoridad operativa únicamente mediante:

```text
OWNER_APPROVAL
→ registro en control operativo
→ dependencias reconciliadas
→ siguiente acción explícita
```

### 3.5 El control operativo es la única sede del estado vivo

Los planes explican alcance, fases y criterios. `plans/001_CONTROL_OPERATIVO.md` debe ser la única sede que determine:

- plan temporalmente activo;
- bloque actual;
- acción siguiente autorizada;
- dependencias pendientes;
- bloqueos;
- estados multidimensionales.

### 3.6 No se corrigen síntomas sin cerrar fuentes generadoras

Toda corrección de contaminación debe cubrir:

```text
artefacto afectado
+ fuente generadora
+ prueba de regresión
+ enforcement automático
```

### 3.7 No se repite una auditoría ya resuelta

Cuando un defecto esté diagnosticado, la siguiente intervención debe ser una corrección quirúrgica o una misión concreta con verificación observable.

---

## 4. Jerarquía documental durante la recuperación

Mientras el Plan 003 esté aprobado y abierto, la jerarquía será:

```text
1. Decisiones explícitas posteriores del OWNER
2. docs/ALCANCE_Y_COORDINACION_EQUIPOS.md
3. docs/product/MVP_BASELINE.md
4. Decisiones funcionales aprobadas del dominio competente
5. PLAN 003, solo para recuperación y reconciliación
6. PLAN 001, para secuencia y producto rector
7. plans/001_CONTROL_OPERATIVO.md, para estado vivo y navegación
8. Especificación activa del bloque
9. Misión técnica autorizada
10. Reporte del agente ejecutor
```

Plan 002 quedó `SUPERSEDED_BY_APPROVED_ARCHITECTURE` en R4 y no conserva autoridad operativa.

El Plan 003 no puede modificar identidad, tesis, estructura narrativa, packaging o políticas funcionales sin decisión del especialista competente.

---

## 5. Estado de partida

### 5.1 Estado general

`````yaml
active_product_stage: SCRIPT_CORE
active_editorial_profile: NONE
profile_1_1_0:
  status: INVALID_APPROVAL_CHAIN
  active: false
profile_1_2_0:
  status: PENDING_FUNCTIONAL_APPROVAL
  active: false
  checksum: b1029e85289c51d4585c555ed20566dfd6f1f6db30b875f989fc23bf46fc5977
voice_corpus_state: AUTHENTIC_CORPUS_PARTIAL
real_operational_subagents: 0
real_multiagent_runtime: NOT_DEMONSTRATED
end_to_end_agentic_execution: NOT_DEMONSTRATED
b5_i3: NOT_AUTHORIZED
s5_real_execution: NOT_EXECUTED
```

### 5.2 Cierres que deben revisarse

| Elemento | Estado anterior | Problema detectado | Estado provisional correcto |
|---|---|---|---|
| B0 | `PASS` | evidencia de baseline y benchmarks no localizada | `REOPENED_FOR_EVIDENCE_REVIEW` |
| B3 | `PASS` / implementación completa | perfil no aprobado ni activo; especificación operativa desactualizada | `IN_PROGRESS` |
| B4 | `PASS` | base contractual y mocks confundidos con agentes reales | `CONTRACTUAL_FOUNDATION_PASS / OPERATIONAL_PENDING` |
| B5-I1 | `TECHNICALLY_CLOSED` | aprobación funcional no localizada | `PENDING_FUNCTIONAL_CONFIRMATION` |
| B5-I2 | implementación completada | ejecución real y aprobación funcional pendientes | `OPEN_PENDING_REAL_EXECUTION_AND_APPROVAL` |
| Saneamiento | guard `PASS` | planes operativos clasificados ampliamente como históricos | `PASS_WITH_COVERAGE_GAP` |
| Plan 002 | propuesta | tratado como autoridad operativa | `PENDING_OWNER_DECISION` |

---

## 6. Modelo obligatorio de estados

A partir de este plan ningún bloque relevante podrá resumirse únicamente como `PASS`.

Cada bloque deberá registrar, cuando corresponda:

`````yaml
implementation_status: NOT_STARTED | PARTIAL | COMPLETED
technical_validation_status: NOT_RUN | PASS | FAIL | BLOCKED
mock_validation_status: NOT_APPLICABLE | NOT_RUN | PASS | FAIL
real_execution_status: NOT_REQUIRED | NOT_DEMONSTRATED | PASS | FAIL | BLOCKED
functional_approval_status: NOT_REQUIRED | PENDING | PASS | FAIL | BLOCKED
owner_approval_status: NOT_REQUIRED | PENDING | PASS | REJECTED
final_closure_status: OPEN | BLOCKED | READY_FOR_AUDIT | PASS | SUPERSEDED
```

### Ejemplo obligatorio para B4

`````yaml
implementation_status: PARTIAL
technical_validation_status: PASS
mock_validation_status: PASS
real_execution_status: NOT_DEMONSTRATED
functional_approval_status: PENDING
owner_approval_status: PENDING
final_closure_status: OPEN
```

---

## 7. Registro inicial de conflictos

| ID | Conflicto | Documento A | Documento B | Decisión provisional | Estado |
|---|---|---|---|---|---|
| C-001 | Plan 002 es propuesta pero se usa como autoridad | Plan 002 | `AGENTS.md` / control operativo | retirar autoridad hasta aprobación | `RESOLVED_IN_R0` |
| C-002 | B3 aparece cerrado pero no existe perfil activo | índice/control | registro de perfiles | B3 permanece abierto | `RESOLVED_STATUS_RECONCILED_IN_R1` |
| C-003 | B4 aparece cerrado pero no hay agentes reales | control/Plan 001 | registros y pruebas mock | separar foundation contractual de operación | `RESOLVED_STATUS_RECONCILED_IN_R1` |
| C-004 | B0 aparece `PASS` sin evidencia visible | control/índice | estructura real del repo | localizar evidencia o reabrir | `RESOLVED_STATUS_RECONCILED_IN_R1` |
| C-005 | B5-I1 técnico se interpreta como cierre total | control | aprobación funcional | exigir cierre funcional | `RESOLVED_STATUS_RECONCILED_IN_R1` |
| C-006 | B5-I2 implementado se interpreta como ejecutado | control | output/provenance real | exigir vertical real | `RESOLVED_STATUS_RECONCILED_IN_R1` |
| C-007 | planes activos excluidos por política histórica | política del guard | referencias operativas | corregir clasificación | `OPEN_ASSIGNED_TO_R2` |
| C-008 | “Plan de acción 12” no tiene identificador canónico | coordinación externa | carpeta `plans/` | no usar hasta documentar equivalencia | `RESOLVED_IN_R0` |

Un conflicto solo puede cerrarse cuando se corrijan todos los documentos, estados, tests y fuentes generadoras afectados.

---

# 8. Fases del Plan 003

## R0 — Contención, autoridad y baseline de recuperación

### Objetivo

Congelar desarrollos incompatibles y establecer una única autoridad temporal.

### Trabajo

1. Registrar el Plan 003 como plan correctivo temporal aprobado y activo.
2. Conservar su alcance limitado exclusivamente a `R0`.
3. Actualizar el control operativo para declarar:

```text
current_recovery_plan = PLAN_003
current_phase_at_R0_closure = R0_CLOSED
NEXT_ALLOWED_ACTION_AT_R0_CLOSURE = R1_STATUS_AND_EVIDENCE_RECONCILIATION
ACTIVE_PLAN_COVERAGE = PASS
CONTAMINATION_GUARD_DIRECT = PASS
CONTAMINATION_GUARD_AUTOMATIC_ENFORCEMENT = PASS
B3_NEUTRAL_SPEC_TRACKABLE = YES
B5_I3 = NOT_AUTHORIZED
S5_REAL_EXECUTION = BLOCKED
PROFILE_ACTIVATION = NOT_AUTHORIZED
```

4. Retirar al Plan 002 cualquier autoridad operativa mientras siga como propuesta.
5. Capturar baseline:
   - estado Git;
   - guard;
   - colección y grupos principales de pruebas;
   - inventario de planes;
   - estado de perfiles;
   - estado de registros agénticos.
6. Registrar qué cambios preexistentes pertenecen a saneamiento, cuáles son históricos y cuáles son desconocidos.

### Evidencia R0 capturada

Fecha y hora de ejecución:

```text
2026-07-28 21:06:07 +02:00
```

Rama actual:

```text
master
```

`git status --short` resumido:

```text
exit_code = 0
modified_or_deleted_tracked = 52
untracked = 18
authorized_files_with_preexisting_changes = 5
```

Inventario observado bajo `plans/`:

```text
plans/
├── 001_CONTROL_OPERATIVO.md
├── 001_reestructuracion_motor_agentico_editorial_y_harness.md
├── plan_001/
├── plan_002/
└── plan_003/
```

Estado exacto de perfiles desde el registro:

```text
ACTIVE_EDITORIAL_PROFILE = mas_alla_del_guion@1.2.1
ACTIVE_EDITORIAL_PROFILE_CHECKSUM = d0355ea43f1d46f6ec94499bd81ae2f99c48f11e4402d1604c634abde70d48f1
PROFILE_1_2_1 = ACTIVE
PROFILE_1_1_0 = INVALID_APPROVAL_CHAIN / inactive
PROFILE_1_2_0 = FUNCTIONAL_REVIEW_BLOCKED / inactive
PROFILE_1_2_0_CHECKSUM = b1029e85289c51d4585c555ed20566dfd6f1f6db30b875f989fc23bf46fc5977
```

Cantidad y estado de agentes/subagentes desde el registro:

```text
agents_registered = 3
real_operational_subagents = 0
real_multiagent_runtime = NOT_DEMONSTRATED
maturity_states = AGENT_TESTED_IN_ISOLATION x3
```

Resultado del guard existente:

```text
command = py -3 src/scripts/runtime_contamination_guard.py
exit_code = 0
ACTIVE_PRODUCT_CONTAMINATION = 0
CONTAMINATED_GENERATOR_SOURCE = 0
FALSE_POSITIVE = 32
MANUAL_REVIEW = 0
blocked = []
summary = PASS_WITH_FALSE_POSITIVE_BACKLOG
```

Colección de pruebas:

```text
command = .venv\Scripts\python.exe -m pytest --collect-only -q --basetemp=.runtime-tmp\pytest-collect
exit_code = 0
tests_collected = 277
warnings = 2
summary = PASS
```

Verificación estructural de diff:

```text
command = git diff --check
exit_code = 0
summary = PASS_WITH_CRLF_WARNINGS_ONLY
```

Clasificación de cambios preexistentes observados antes de esta misión:

```text
PLAN_003_MISSION_CHANGE
- none at baseline capture time

PREEXISTING_KNOWN_CHANGE
- AGENTS.md
- plans/001_CONTROL_OPERATIVO.md
- plans/plan_001/README.md
- plans/plan_002/
- plans/plan_003/
- config/editorial_profile_registry.json
- config/subagent_registry.json
- src/scripts/runtime_contamination_guard.py
- tests/ai/test_subagent_foundation.py
- tests/core/test_runtime_contamination_guard.py

TEMPORARY_ARTIFACT
- output/runtime_contamination_initial_2026-07-27.json
- output/runtime_contamination_mid_2026-07-27.json
- output/runtime_contamination_final_2026-07-27.json

UNKNOWN_PRESERVED
- remaining modified/untracked paths outside the authorized-file subset
```

### Snapshot histórico de cierre R4 (no vigente como estado vivo)

```text
PLAN_AUTHORITY_RESOLVED = PASS
RECOVERY_BASELINE_CAPTURED = PASS
INCOMPATIBLE_WORK_FROZEN = PASS
PLAN_002_AUTHORITY_STATUS = RESOLVED
R0_STATUS = PASS
NEXT_ALLOWED_ACTION_AT_R0_CLOSURE = R1_STATUS_AND_EVIDENCE_RECONCILIATION
```

---

## R1 — Reconciliación de estados, evidencias y falsos cierres

```text
CURRENT_RECOVERY_PHASE_AT_R1_CLOSURE = R1_CLOSED
PLAN_003_IMPLEMENTATION_AUTHORIZED = NO_PENDING_NEXT_MISSION
R0_STATUS = PASS
R1_STATUS = PASS
R2_STATUS = PASS
R2_EXECUTION = COMPLETED
R3_EXECUTION = NOT_AUTHORIZED
NEXT_ALLOWED_ACTION_AT_R1_CLOSURE = PREPARE_R2_CANONICAL_SANITATION_AND_ENFORCEMENT
ACTIVE_PLAN_COVERAGE = PASS
CONTAMINATION_GUARD_DIRECT = PASS
CONTAMINATION_GUARD_AUTOMATIC_ENFORCEMENT = PASS
B3_NEUTRAL_SPEC_TRACKABLE = YES
BLOCK_STATUS_MODEL_APPLIED = PASS
B0_STATUS_RECONCILED = PASS
B3_STATUS_RECONCILED = PASS
B4_STATUS_RECONCILED = PASS
B5_I1_STATUS_RECONCILED = PASS
B5_I2_STATUS_RECONCILED = PASS
SANITATION_STATUS_RECONCILED = PASS
ACTIVE_STATE_CONTRADICTIONS = 0
C-002 = RESOLVED_STATUS_RECONCILED_IN_R1
C-003 = RESOLVED_STATUS_RECONCILED_IN_R1
C-004 = RESOLVED_STATUS_RECONCILED_IN_R1
C-005 = RESOLVED_STATUS_RECONCILED_IN_R1
C-006 = RESOLVED_STATUS_RECONCILED_IN_R1
C-007 = RESOLVED_IN_R2
```

HISTORICAL_SNAPSHOT_R1

Este bloque conserva el estado observado al cierre de R1. No representa el estado operativo vigente.

Para el estado actual consultar:
- el encabezado de Plan 003;
- plans/001_CONTROL_OPERATIVO.md;
- los cierres posteriores R2, R5 y R6-A.

```yaml
B0: {implementation_status: PARTIAL, technical_validation_status: NOT_RUN, mock_validation_status: NOT_APPLICABLE, real_execution_status: NOT_REQUIRED, functional_approval_status: PENDING, owner_approval_status: PENDING, final_closure_status: OPEN, evidence_refs: [B0_baseline_not_located], remaining_gap: B0_EVIDENCE_NOT_LOCATED, next_resolution_phase: R6}
B3: {implementation_status: COMPLETED, technical_validation_status: BLOCKED, mock_validation_status: NOT_APPLICABLE, real_execution_status: NOT_REQUIRED, functional_approval_status: PENDING, owner_approval_status: PENDING, final_closure_status: OPEN, evidence_refs: [editorial_profile_registry, 1.2.0_validation, 1.2.0_approval, corpus_manifest], remaining_gap: VALID_FUNCTIONAL_APPROVAL_FOR_EXACT_1_2_0_CHECKSUM, next_resolution_phase: R5}
B4: {implementation_status: PARTIAL, technical_validation_status: PASS, mock_validation_status: PASS, real_execution_status: NOT_DEMONSTRATED, functional_approval_status: PENDING, owner_approval_status: PENDING, final_closure_status: OPEN, real_operational_subagents: 0, evidence_refs: [subagent_registry_mock, isolated_tests], remaining_gap: REAL_PROVIDER_OPERATIONAL_VERTICAL_NOT_DEMONSTRATED, next_resolution_phase: R4_AND_R6}
B5_I1: {implementation_status: COMPLETED, technical_validation_status: PASS, functional_approval_status: PENDING, owner_approval_status: PENDING, final_closure_status: OPEN, evidence_refs: [plan_001], remaining_gap: VALID_FUNCTIONAL_APPROVAL_NOT_LOCATED, next_resolution_phase: R3_OR_R6}
B5_I2: {implementation_status: COMPLETED, technical_validation_status: PASS_WITH_RESIDUAL_RISK, mock_validation_status: PASS, real_execution_status: NOT_DEMONSTRATED, semantic_audit_status: NOT_DEMONSTRATED, functional_approval_status: PENDING, owner_approval_status: PENDING, final_closure_status: OPEN, evidence_refs: [semantic_audit_script, isolated_tests], remaining_gap: REAL_EXECUTION_SEMANTIC_AUDIT_AND_FUNCTIONAL_APPROVAL_NOT_DEMONSTRATED, next_resolution_phase: R4_AND_R6}
SANITATION: {implementation_status: COMPLETED, technical_validation_status: PASS, direct_guard_status: PASS, active_product_contamination: 0, contaminated_generator_source: 0, false_positive_backlog: 32, active_plan_coverage: PENDING_R2, automatic_enforcement_status: PENDING_R2, final_closure_status: OPEN, next_resolution_phase: R2}
```

---

## R2 — Cierre del saneamiento canónico y enforcement

### Objetivo

Cerrar las fuentes generadoras de contaminación y garantizar enforcement automático.

### Trabajo

1. Modificar la política del guard para diferenciar:

```text
ACTIVE_RECTOR_PLAN
ACTIVE_BLOCK_SPECIFICATION
HISTORICAL_PLAN_VERSION
EXTERNAL_COORDINATION_DOCUMENT
```

2. Eliminar exclusiones amplias sobre planes activos.
3. Sanear o regenerar `plans/plan_001/B3_perfil_editorial_frontera_canal.md` desde fuentes neutrales actuales.
4. Verificar todas las especificaciones activas de bloques.
5. Integrar el guard como mínimo en:
   - gate superior de integridad o comando canónico de cierre;
   - validación previa a commit;
   - CI cuando exista.
6. Evitar un segundo scanner o una segunda política paralela.
7. Confirmar que las excepciones locales sean estrechas y no excluyan patrones completos.
8. Verificar que la especificación neutral B3 esté rastreada por Git y no quede anulada por `.gitignore`.

### Gate de salida

```text
ACTIVE_PRODUCT_CONTAMINATION = 0
CONTAMINATED_GENERATOR_SOURCE = 0
MANUAL_REVIEW = 0
ACTIVE_PLAN_COVERAGE = PASS
LEGACY_EXECUTABLE_SURFACES = 0
CONTAMINATION_GUARD_DIRECT = PASS
CONTAMINATION_GUARD_AUTOMATIC_ENFORCEMENT = PASS
```

---

## R3 — Recuperación de requisitos funcionales

### Objetivo

Obtener los requisitos faltantes antes de diseñar agentes definitivos.

### Trabajo

Preparar solicitudes separadas para:

```text
CHANNEL_INTELLIGENCE
SCRIPT_PRODUCT
YOUTUBE_ADAPTATION
```

Cada solicitud deberá identificar únicamente vacíos reales y preguntar por:

- decisiones que requieren criterio propio;
- tareas repetibles;
- entradas y salidas;
- permisos;
- prohibiciones;
- condiciones de bloqueo;
- conflictos de interés;
- revisión independiente;
- aprobación humana;
- correcciones automáticas permitidas;
- escalamiento;
- qué debe ser agente, skill, script, regla, gate, workflow o decisión humana.

Después, el propietario deberá decidir:

- grado de autonomía;
- decisiones reservadas;
- proveedores y costes aceptables;
- máximo de ciclos;
- condiciones para continuar sin preguntar;
- condiciones de detención;
- evidencia requerida;
- primera capacidad que se demostrará.

### Prohibiciones

- no modificar runtime;
- no crear agentes nuevos;
- no cambiar prompts de rol;
- no aprobar Plan 002 por defecto;
- no repetir preguntas ya respondidas en documentación vigente.

### Gate de salida

```text
CHANNEL_INTELLIGENCE_REQUIREMENTS = APPROVED
SCRIPT_PRODUCT_REQUIREMENTS = APPROVED
YOUTUBE_ADAPTATION_REQUIREMENTS = APPROVED
OWNER_AUTONOMY_DECISIONS = APPROVED
NO_AGENT_ARCHITECTURE_INVENTED = PASS
```

---

## R4 — Reconciliación y aprobación de arquitectura agéntica

### Objetivo

Decidir correctamente qué capacidades requieren agentes y qué capacidades deben permanecer como piezas más simples.

### Matriz obligatoria

| Capacidad | Propietario funcional | Pieza propuesta | Razón | Entrada | Salida | Puede modificar | Puede bloquear | Revisión independiente | Aprobación humana |
|---|---|---|---|---|---|---|---|---|---|

Tipos permitidos:

```text
AGENT
SUBAGENT
SKILL
SCRIPT
RULE
GATE
WORKFLOW
HUMAN_DECISION
```

### Prueba de necesidad de agente

Solo se propondrá un agente si necesita:

- criterio no determinista;
- contexto especializado;
- responsabilidad diferenciada;
- límites claros;
- veto o escalamiento;
- ejecución separada;
- evidencia propia;
- independencia frente al productor.

### Reconciliación del Plan 002

Al finalizar, el Plan 002 deberá quedar en uno de estos estados:

```text
APPROVED_AS_IS
APPROVED_WITH_CHANGES
SUPERSEDED_BY_APPROVED_ARCHITECTURE
REJECTED
```

No puede permanecer simultáneamente como propuesta y autoridad.

### Snapshot histórico de cierre R4 (no vigente como estado vivo)

```text
CAPABILITY_MATRIX = APPROVED
AGENT_NECESSITY = DEMONSTRATED
AGENT_OVERLAPS = RESOLVED
PLAN_002_FINAL_DECISION = SUPERSEDED_BY_APPROVED_ARCHITECTURE
OWNER_AGENT_ARCHITECTURE_APPROVAL = APPROVED
PIPELINE_ORCHESTRATOR = DETERMINISTIC
AGENT_ROLES = 7
NESTED_SUBAGENTS_DURING_MVP = 0
MATERIALIZATION = PROGRESSIVE_BY_PHASE
RUNTIME_MODIFIED = NO
AGENTS_CREATED = NO
ACTIVE_PRODUCT_CONTAMINATION = 0
NEXT_ALLOWED_ACTION = AUTHORIZE_AND_EXECUTE_R6_B_WITH_SELECTED_LOCAL_ROUTE
R5_EXECUTION = COMPLETED
R5A_STATUS = PASS
R5A_CURRENT_PHASE = CLOSED
R5B_STATUS = PASS
R5B_CURRENT_PHASE = CLOSED
R6_PREPARATION = COMPLETE
R6_A_STATUS = CLOSED
R6_A_CURRENT_PHASE = CLOSED
RUNTIME_FOUNDATION = PASS
MOCK_ONLY_DEPENDENCIES_IDENTIFIED = YES
SELECTED_PROVIDER = ollama
SELECTED_MODEL = Qwen2.5-Coder:latest
REAL_EXECUTION_ROUTE = LOCAL_MODEL
PAID_PROVIDER_REQUIRED = NO
CONTROL_CASE_VALID = READY
CONTROL_CASE_SEMANTIC_FAILURE = READY
CONTROL_CASE_INSUFFICIENT_EVIDENCE = READY
BUDGET_POLICY_ENFORCED = PASS
PROVENANCE_FIELDS_READY = PASS
PROMPTS_READY = PASS
REGISTRY_READY = PASS
R6_B_READY = YES
R6_B_0_STATUS = PASS
HYBRID_RUNTIME_READY = YES
AGENT_RUNTIME_PORT = PASS
COMMON_ADAPTER = AgentRuntimePort
EXECUTOR_ABSTRACTION = PASS
PROVIDER_RESOLUTION_MODE = PER_AGENT_PROFILE
OLLAMA_INTEGRATION = PASS
OLLAMA_CONFIGURATION = READY
OLLAMA_RUNTIME_AVAILABILITY = READY
DEEPSEEK_INTEGRATION = PASS
DEEPSEEK_CONFIGURATION = READY_FOR_SECRET
ENV_EXAMPLE_READY = PASS
PROVIDER_CONFIG_COHERENCE = PASS
DEEPSEEK_READY_FOR_OWNER_SECRET = PASS
OLLAMA_READY_FOR_ACTIVATION = PASS
DEEPSEEK_ERROR_CLASSIFICATION = PASS
R6_B_0_EXTERNAL_AUDIT = PASS
DEEPSEEK_RUNTIME_AVAILABILITY = CREDENTIALS_MISSING
CONTROLLED_EXECUTORS = INVENTORIED_AND_CONFIGURABLE
CODEX_EXECUTOR = HANDOFF_ONLY
OPENCODE_EXECUTOR = HANDOFF_ONLY
ANTIGRAVITY_EXECUTOR = UNAVAILABLE
PROFILE_SWITCH_WITHOUT_CODE_CHANGE = PASS
HYBRID_PROFILE_CONFIGURATION = PASS
ROLE_INDEPENDENCE = PASS
PROVENANCE_HYBRID_SUPPORT = PASS
SECRET_HANDLING = PASS
NEGATIVE_CASES = PASS
PAID_CALL_EXECUTED = NO
R6_B_STATUS = READY_NOT_AUTHORIZED
R6_B_AUTHORIZATION_GATE = SELECT_ROUTE_AND_OWNER_REAUTHORIZE
R6_B_PREFLIGHT_STATUS = PASS
R6_B_SELECTED_PROFILE = ollama_local
R6_B_SELECTED_EXECUTOR = native_provider
R6_B_SELECTED_PROVIDER = ollama
R6_B_SELECTED_MODEL_PRODUCER = Qwen2.5-Coder:latest
R6_B_SELECTED_MODEL_AUDITOR = Qwen2.5-Coder:latest
R6_B_PREFLIGHT_DATE = 2026-07-29
ACTUAL_EXECUTOR = NONE
ACTUAL_PROVIDER = NONE
ACTUAL_MODEL = NONE
R6_EXECUTION_EXPANDED = NO
R6_A_EXTERNAL_AUDIT = PASS
R6_A_MISSION = CLOSED
R6_B_TO_R6_E = NOT_AUTHORIZED
R6_C_STATUS = NOT_RUN
R6_D_STATUS = NOT_RUN
R6_E_STATUS = NOT_RUN
REAL_AGENT_RUN_EXECUTED = NO
PROFILE_CANDIDATE = mas_alla_del_guion@1.2.1
PROFILE_ACTIVATION = PASS
VOICE_CORPUS_STATE = AUTHENTIC_CORPUS_PARTIAL
GLOBAL_VOICE_REPRESENTATIVENESS = NOT_VALIDATED
R6_EXECUTION = NOT_AUTHORIZED
B5_I3_EXECUTION = NOT_AUTHORIZED
R4_STATUS = PASS
R4_CURRENT_PHASE = CLOSED
R4_EXECUTION = NOT_AUTHORIZED
```

---

## R5 — Aprobación y activación controlada del EditorialProfile 1.2.1

### Objetivo

Cerrar el perfil editorial sin mezclarlo con la implementación multiagente.

### Secuencia

```text
CHANNEL_INTELLIGENCE_REVIEW
→ SCRIPT_PRODUCT_INPUT_SUFFICIENCY_REVIEW
→ YOUTUBE_ADAPTATION_LIMITED_REVIEW
→ OWNER_APPROVAL
→ TECHNICAL_VALIDATION
→ CONTROLLED_ACTIVATION
→ CONSUMER_VALIDATION
→ INVALIDATION_CHECK
```

### Condiciones

- checksum exacto conocido;
- ninguna aprobación puede escribirse automáticamente;
- una modificación al payload invalida las aprobaciones anteriores;
- el puntero activo debe coincidir con registro, checksum y control operativo;
- ningún consumidor puede reconstruir identidad desde `workspace/`.

### Gate de salida

```text
PROFILE_1_2_1_FUNCTIONAL_APPROVAL = PASS
PROFILE_1_2_1_OWNER_APPROVAL = PASS
PROFILE_1_2_1_TECHNICAL_VALIDATION = PASS
ACTIVE_EDITORIAL_PROFILE = mas_alla_del_guion@1.2.1
ACTIVE_PROFILE_CHECKSUM_MATCH = PASS
DEPENDENT_INVALIDATION = PASS
```

---

## R6 — Cierre real de bloques reabiertos

### Estado de preparación R6-A

```text
R6_PREPARATION = COMPLETE
R6_A_STATUS = CLOSED
RUNTIME_FOUNDATION = PASS
MOCK_ONLY_DEPENDENCIES_IDENTIFIED = YES
SELECTED_PROVIDER = ollama
SELECTED_MODEL = Qwen2.5-Coder:latest
REAL_EXECUTION_ROUTE = LOCAL_MODEL
PAID_PROVIDER_REQUIRED = NO
CONTROL_CASE_VALID = READY
CONTROL_CASE_SEMANTIC_FAILURE = READY
CONTROL_CASE_INSUFFICIENT_EVIDENCE = READY
BUDGET_POLICY_ENFORCED = PASS
PROVENANCE_FIELDS_READY = PASS
PROMPTS_READY = PASS
REGISTRY_READY = PASS
R6_B_READY = YES
R6_B_0_STATUS = PASS
HYBRID_RUNTIME_READY = YES
AGENT_RUNTIME_PORT = PASS
COMMON_ADAPTER = AgentRuntimePort
EXECUTOR_ABSTRACTION = PASS
PROVIDER_RESOLUTION_MODE = PER_AGENT_PROFILE
OLLAMA_INTEGRATION = PASS
OLLAMA_CONFIGURATION = READY
OLLAMA_RUNTIME_AVAILABILITY = READY
DEEPSEEK_INTEGRATION = PASS
DEEPSEEK_CONFIGURATION = READY_FOR_SECRET
ENV_EXAMPLE_READY = PASS
PROVIDER_CONFIG_COHERENCE = PASS
DEEPSEEK_READY_FOR_OWNER_SECRET = PASS
OLLAMA_READY_FOR_ACTIVATION = PASS
DEEPSEEK_ERROR_CLASSIFICATION = PASS
R6_B_0_EXTERNAL_AUDIT = PASS
DEEPSEEK_RUNTIME_AVAILABILITY = CREDENTIALS_MISSING
CONTROLLED_EXECUTORS = INVENTORIED_AND_CONFIGURABLE
CODEX_EXECUTOR = HANDOFF_ONLY
OPENCODE_EXECUTOR = HANDOFF_ONLY
ANTIGRAVITY_EXECUTOR = UNAVAILABLE
PROFILE_SWITCH_WITHOUT_CODE_CHANGE = PASS
HYBRID_PROFILE_CONFIGURATION = PASS
ROLE_INDEPENDENCE = PASS
PROVENANCE_HYBRID_SUPPORT = PASS
SECRET_HANDLING = PASS
NEGATIVE_CASES = PASS
PAID_CALL_EXECUTED = NO
R6_B_STATUS = READY_NOT_AUTHORIZED
R6_B_AUTHORIZATION_GATE = SELECT_ROUTE_AND_OWNER_REAUTHORIZE
R6_B_PREFLIGHT_STATUS = PASS
R6_B_SELECTED_PROFILE = ollama_local
R6_B_SELECTED_EXECUTOR = native_provider
R6_B_SELECTED_PROVIDER = ollama
R6_B_SELECTED_MODEL_PRODUCER = Qwen2.5-Coder:latest
R6_B_SELECTED_MODEL_AUDITOR = Qwen2.5-Coder:latest
R6_B_PREFLIGHT_DATE = 2026-07-29
ACTUAL_EXECUTOR = NONE
ACTUAL_PROVIDER = NONE
ACTUAL_MODEL = NONE
R6_EXECUTION_EXPANDED = NO
R6_A_EXTERNAL_AUDIT = PASS
R6_A_MISSION = CLOSED
R6_B_TO_R6_E = NOT_AUTHORIZED
R6_C_STATUS = NOT_RUN
R6_D_STATUS = NOT_RUN
R6_E_STATUS = NOT_RUN
REAL_AGENT_RUN_EXECUTED = NO
B5_I3_EXECUTION = NOT_AUTHORIZED
```

Snapshot histórico del 29 de julio de 2026: R6-A cerró con auditoría externa aprobada y dejó preparada una ruta local con Ollama. Ese snapshot no representa el estado vivo posterior al diagnóstico contractual, la pérdida no recuperable de la evidencia real y la decisión de diferir Ollama hasta nuevo aviso.

### Objetivo

Cerrar B0, B3, B4, B5-I1 y B5-I2 con evidencia multidimensional.

### R6.1 B0

Debe demostrar:

- baseline reproducible;
- benchmarks editoriales diferenciados de tests;
- rúbrica funcional;
- evidencia versionada;
- comandos y resultados verificables.

### R6.2 B3

Debe demostrar:

- perfil activo exacto;
- lineage coherente;
- corpus correctamente clasificado;
- consumidores bloqueados ante identidad inválida;
- aprobación y activación separadas.

### R6.3 B4

Primero se implementará una sola vertical pequeña aprobada en R4.

Debe demostrar:

```text
ORCHESTRATOR
→ PRODUCTOR FUNCIONAL
→ VERIFICADOR INDEPENDIENTE
→ CORRECCIÓN LIMITADA
→ GATE
```

Criterios mínimos:

- proveedor real o modelo local autorizado;
- runs distintos;
- contexto separado;
- contratos de entrada y salida;
- permisos aplicados;
- productor sin autoaprobación;
- auditor sin edición silenciosa;
- handoff con checksum;
- caso defectuoso detectado;
- bloqueo real;
- máximo de iteraciones;
- escalamiento;
- provenance;
- tokens, coste y latencia;
- pruebas unitarias, integradas y negativas;
- revisión funcional.

### R6.4 B5-I1

Debe existir aprobación funcional sobre artefactos exactos y estado final canónico.

### R6.5 B5-I2

Debe ejecutar la vertical real sobre casos controlados y demostrar:

- suficiencia semántica;
- auditoría independiente;
- corrección limitada;
- bloqueo por evidencia insuficiente;
- revisión funcional de Producto Guion;
- revisión de la interfaz temprana de YouTube cuando corresponda.

### Gate de salida

```text
B0_FINAL_CLOSURE = PASS
B3_FINAL_CLOSURE = PASS
B4_CONTRACTUAL_FOUNDATION = PASS
B4_OPERATIONAL_VERTICAL = PASS
B5_I1_FINAL_CLOSURE = PASS
B5_I2_FINAL_CLOSURE = PASS
NO_FALSE_PASS_REMAINS = PASS
```

---

## R7 — Estabilización mínima y retorno al Plan 001

### Objetivo

Cerrar el Plan 003 y reanudar el Plan 001 desde un estado coherente.

### Trabajo

1. Definir instalación reproducible y comando canónico de pruebas.
2. Separar pruebas unitarias, integración y subprocess.
3. Registrar duración y tests lentos.
4. Incorporar CI mínima limpia.
5. Crear empaquetado por allowlist con manifiesto y checksum.
6. Excluir configuración local, temporales, caches y ZIPs anidados.
7. Aplicar estados de madurez a skills activas, diferidas, históricas y de prueba.
8. Actualizar todas las sedes canónicas.
9. Ejecutar auditoría final técnica y funcional proporcional.
10. Determinar el siguiente bloque autorizado del Plan 001.

### Gate final

```text
PLAN_003_CONFLICT_REGISTER = CLOSED
PLAN_003_ALL_GATES = PASS
PLAN_003_FINAL_STATUS = PASS
PLAN_001_STATUS = RESUMED
NEXT_AUTHORIZED_BLOCK = <BLOCK_ID>
B5_I3_AUTHORIZATION = EXPLICIT_DECISION
```

El siguiente bloque no se presumirá. Deberá registrarse después de verificar todas las dependencias.

---

## 9. Matriz de impacto e invalidación

Toda misión del Plan 003 debe declarar:

| Campo | Contenido requerido |
|---|---|
| Cambio | qué se modifica |
| Autoridad | quién aprobó el cambio |
| Artefactos afectados | archivos y contratos |
| Estados invalidados | aprobaciones o gates que dejan de ser válidos |
| Estados preservados | qué no se invalida |
| Revalidación requerida | pruebas y revisiones |
| Rollback | cómo volver al estado anterior |

Ejemplo:

`````yaml
change: APPROVED_AGENT_ARCHITECTURE
invalidates:
  - PLAN_002_UNAPPROVED_AGENT_DEFINITIONS
  - SUBAGENT_REGISTRY_CURRENT_VERSION
  - RELATED_ROLE_PROMPTS
  - B5_I2_READINESS_BASED_ON_MOCKS
preserves:
  - APPROVED_EDITORIAL_CONTRACTS
  - VALID_CONTENT_SCHEMAS
  - SANITATION_EVIDENCE
requires_revalidation:
  - agent_registry_tests
  - permission_tests
  - b5_i2_integrated_execution
```

---

## 10. Gate de coherencia documental

Debe crearse o ampliarse un control determinista que detecte, como mínimo:

- plan `PROPOSAL` utilizado como autoridad;
- bloque en `PASS` con aprobación requerida pendiente;
- perfil activo distinto entre puntero, registro y control;
- siguiente acción incompatible con dependencias;
- especificación activa clasificada como histórica;
- fase posterior autorizada con prerrequisito abierto;
- estado final incompatible con ejecución real no demostrada;
- referencia a artefactos inexistentes;
- denominaciones externas dentro de superficies productivas.

Este gate no sustituye la auditoría funcional. Solo impide contradicciones estructurales detectables.

Estados:

```text
PASS = 0
FAIL = 1
BLOCKED = 2
ERROR = 3
```

---

## 11. Política de misiones

Cada misión debe indicar:

```text
Objetivo
Plan y fase
Entrada funcional aprobada
Lectura inicial mínima
Archivos a modificar
Archivos prohibidos
Cambio esperado
Validación
Condición de detención
Entrega
Commit/push autorizado o prohibido
```

No debe pedir al agente:

- reauditar todo el repositorio;
- investigar decisiones ya resueltas;
- crear documentación no necesaria;
- ampliar alcance;
- corregir fallos ajenos sin autorización;
- autoaprobar el resultado.

---

## 12. Auditorías y aprobaciones por especialidad

| Área | Auditor funcional | Auditor técnico | Aprobación final cuando aplique |
|---|---|---|---|
| Identidad y perfil | `CHANNEL_INTELLIGENCE` | `INFRASTRUCTURE_GOVERNANCE` | OWNER |
| Producto Guion | `SCRIPT_PRODUCT` | `INFRASTRUCTURE_GOVERNANCE` | OWNER según estado |
| Adaptación a YouTube | `YOUTUBE_ADAPTATION` | `INFRASTRUCTURE_GOVERNANCE` | OWNER según estado |
| Arquitectura, runtime y pruebas | no sustituye revisión funcional | `INFRASTRUCTURE_GOVERNANCE` | OWNER para cambios estructurales |

Ninguna auditoría técnica sustituye la aprobación funcional. Ninguna aprobación funcional demuestra por sí sola implementación técnica correcta.

---

## 13. Evidencia mínima de cierre del Plan 003

El cierre debe incluir:

`````yaml
plan_003_status: PASS
conflicts_open: 0
false_passes_open: 0
active_product_contamination: 0
contaminated_generator_sources: 0
active_plan_coverage: PASS
guard_automatic_enforcement: PASS
profile_active_and_valid: true
b0_final_closure: PASS
b3_final_closure: PASS
b4_contractual_foundation: PASS
b4_operational_vertical: PASS
b5_i1_final_closure: PASS
b5_i2_final_closure: PASS
functional_requirements_approved: true
agent_architecture_owner_approved: true
full_suite: PASS
ci: PASS
clean_package_smoke_test: PASS
next_plan_001_block: <BLOCK_ID>
```

---

## 14. Riesgos

| Riesgo | Mitigación |
|---|---|
| convertir Plan 003 en un nuevo plan rector permanente | cierre obligatorio en R7 |
| volver a inventar agentes desde Infraestructura | R3 y R4 obligatorios |
| reabrir trabajo válido innecesariamente | estados multidimensionales e invalidación selectiva |
| borrar trazabilidad histórica | reclasificar, no eliminar sin evidencia |
| crear otro scanner paralelo | reutilizar política y guard existentes |
| bloquear indefinidamente el desarrollo | gates concretos y siguiente acción única |
| aprobar por tests mock | exigir proveedor real y vertical integrada |
| mezclar cambios preexistentes | baseline y clasificación en R0 |
| contradicciones entre documentos | registro de conflictos y gate documental |
| dependencia de una herramienta o proveedor | contratos neutrales y adaptadores |

---

## 15. Criterio de aprobación del Plan 003

El propietario debe decidir explícitamente:

```text
PLAN_003 = APPROVED
```

Estado ya materializado en esta sede:

1. se registra en `plans/001_CONTROL_OPERATIVO.md`;
2. R0 se convierte en la única fase autorizada;
3. Plan 002 pierde autoridad operativa hasta R4;
4. B5-I3 y S5 permanecen bloqueados;
5. ninguna implementación agéntica puede iniciarse antes de R3 y R4.

La creación de este archivo no equivale por sí sola a autorización de implementación.

---

## 16. Resultado esperado

```text
PLAN_AUTHORITY = CONSISTENT
FALSE_PASSES = CLOSED_OR_CORRECTLY_REOPENED
ACTIVE_PLAN_COVERAGE = PASS
FUNCTIONAL_REQUIREMENTS = APPROVED
AGENT_ARCHITECTURE = OWNER_APPROVED
REAL_OPERATIONAL_VERTICAL = DEMONSTRATED
EDITORIAL_PROFILE = VALID_AND_ACTIVE
B0_B3_B4_B5_I1_B5_I2 = CLOSED_WITH_EVIDENCE
PLAN_003 = CLOSED
PLAN_001 = RESUMED
NEXT_AUTHORIZED_BLOCK = EXPLICIT
```

---

## 17. Regla final

No volver a confundir:

```text
plan escrito
con plan aprobado

estado PASS
con cierre completo

prompt creado
con agente operativo

mock en PASS
con ejecución real

implementación técnica
con aprobación funcional

propuesta arquitectónica
con autoridad vigente

archivo histórico
con especificación activa
```

El Plan 003 existe para corregir precisamente esas confusiones y devolver el proyecto a una secuencia verificable dentro del Plan 001.
