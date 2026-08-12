# PLAN 005 — Autonomía, delegación, contexto y eficiencia operativa

**Versión:** `1.1.0`
**Estado:** `OWNER_CLOSED`
**Implementación autorizada:** `NO — OWNER_CLOSURE_RECORDED`
**Tipo:** `TRANSVERSAL_AUTONOMY_AND_EFFICIENCY_PLAN`
**Plan rector:** `PLAN 001 — Reestructuración del sistema agéntico, del motor editorial y del arnés de control`
**Plan previo relacionado:** `PLAN 004 — Hardening transversal de harness, capabilities, contexto y calidad`
**Relación con PLAN 004:** `POST_HARDENING_EXTENSION_WITHOUT_REOPENING_PLAN_004`
**Autoridad de estado vivo:** `plans/001_CONTROL_OPERATIVO.md`
**Ruta canónica propuesta:** `plans/plan_005/005_autonomia_delegacion_contexto_y_eficiencia_operativa.md`
**Fecha de creación:** `2026-08-11`
**Aprobación del propietario:** `APPROVED_FOR_CORRECTION_2026-08-12`
**Cierre del propietario:** `OWNER_CLOSED_2026-08-12`
**Proveedor/modelo canónico:** `NONE`
**Dependencia obligatoria de Gentle / Pi / Engram / OpenSpec:** `NO`

---

## 0. Decisión de numeración y naturaleza del plan

La numeración consecutiva vigente del proyecto contiene PLAN 001, PLAN 002, PLAN 003 y PLAN 004. El siguiente identificador independiente disponible es:

```text
PLAN 005
```

Este documento no debe convertirse en un segundo plan rector ni en un roadmap paralelo del producto.

Su relación correcta es:

```text
PLAN 001
  └── gobierna el producto y su roadmap

PLAN 004
  └── cerró el hardening transversal del harness

PLAN 005
  └── mejora la autonomía y eficiencia del harness ya endurecido
      sin reabrir PLAN 004
      sin modificar criterios funcionales de producto
      sin autorizar automáticamente R1-M4 ni otra fase del producto
```

Por tanto:

```text
PLAN_005_ROLE: TRANSVERSAL_SUPPORTING_PLAN
PLAN_005_CAN_MODIFY_PRODUCT_CRITERIA: NO
PLAN_005_CAN_REOPEN_PLAN_004: NO
PLAN_005_CAN_AUTHORIZE_PRODUCT_PHASES: NO
LIVE_STATE_AUTHORITY: plans/001_CONTROL_OPERATIVO.md
```

---

# 1. Propósito

PLAN 005 debe aumentar la capacidad del sistema para completar una misión autorizada de forma autónoma dentro del mismo entorno operativo, reduciendo la necesidad de instrucciones externas intermedias y manteniendo evidencia, calidad, trazabilidad, límites y escalamiento proporcional.

La definición operativa de autonomía para este plan es:

> **Una misión autónoma, no un agente solitario.**

Una misión es autónoma cuando, una vez autorizada con suficiente definición, el sistema puede:

```text
entender el contrato
→ resolver contexto
→ decidir si ejecuta inline o delega
→ seleccionar capability / role / profile suficiente
→ ejecutar
→ verificar
→ autoauditar adversarialmente
→ usar revisión interna independiente cuando corresponda
→ reparar
→ revalidar
→ recuperar continuidad si cambia la sesión o se compacta
→ converger o bloquearse honestamente
→ escalar externamente solo cuando policy, riesgo o autoridad lo exijan
```

sin requerir que el usuario actúe continuamente como bus manual entre OpenCode, Codex, ChatGPT u otras herramientas.

---

# 2. Problema que resuelve

PLAN 004 dejó materializada una base fuerte de autorización, contexto, evidencia fail-closed, freshness, convergence y autoauditoría. El siguiente cuello de botella ya no es “falta de control”.

El problema pendiente es de **autonomía operacional eficiente**:

1. el agente todavía puede consumir demasiado contexto del orquestador haciendo directamente trabajos separables;
2. no existe necesariamente una regla portable y explícita para elegir entre ejecución inline, delegación interna o escalamiento;
3. una delegación puede perder el beneficio si recibe demasiada documentación o contexto irrelevante;
4. la existencia de una skill no demuestra que haya sido resuelta y aplicada;
5. la revisión puede convertirse en deuda humana o en ping-pong externo innecesario;
6. una sesión larga puede perder continuidad si se compacta o reinicia;
7. elegir un modelo o perfil más costoso de lo necesario puede elevar coste sin mejorar el resultado;
8. no debe asumirse que más subagentes equivalen a más autonomía.

PLAN 005 debe resolver estos puntos **reutilizando el harness existente**, no creando un segundo sistema paralelo.

---

# 3. Qué NO significa “evitar ping-pong”

El ping-pong indeseado es externo al entorno operativo:

```text
OpenCode
→ usuario copia resultado
→ ChatGPT crea otra instrucción
→ usuario la pasa a Codex
→ Codex responde
→ usuario vuelve a ChatGPT
→ nueva instrucción
```

Esto introduce dependencia humana continua, pérdida de contexto, latencia y retrabajo.

No se considera ping-pong problemático:

```text
ORQUESTADOR
  ├── scout interno
  ├── implementer interno
  ├── reviewer interno
  ├── tester interno
  └── specialist interno
```

si todos ellos:

- operan dentro de la misma misión;
- reciben contexto gobernado;
- conservan lineage;
- producen artefactos/evidencia estructurada;
- respetan autorización y presupuesto;
- no requieren una nueva instrucción humana para cada microfase.

---

# 4. Principios rectores

## 4.1 SEARCH BEFORE CREATE

Antes de crear cualquier schema, script, policy, registry, workflow, skill, adapter o módulo nuevo se debe buscar un equivalente existente.

```text
EXISTING_CAPABILITY_FOUND
→ EXTEND_OR_REUSE

NO_EXISTING_CAPABILITY
→ CREATE_MINIMUM_REQUIRED_COMPONENT
```

PLAN 005 no autoriza duplicación por nomenclatura.

## 4.2 Determinismo antes que IA

Cuando una decisión o validación pueda resolverse de forma determinista, debe preferirse esa vía.

Orden económico preferido:

```text
DETERMINISTIC TOOL
→ LOWEST SUFFICIENT EXECUTION PROFILE
→ HIGH-REASONING PROFILE
→ SPECIALIST / OWNER cuando la decisión no sea delegable
```

## 4.3 Fresh context no significa contexto vacío

Un subagente debe comenzar sin ruido conversacional heredado, pero debe recibir todo el contexto canónico mínimo necesario para cumplir su tarea.

```text
FRESH_CONTEXT
≠ NO_CONTEXT

FRESH_CONTEXT
= MINIMUM_SUFFICIENT_AUTHORIZED_CONTEXT
```

## 4.4 La delegación debe ser proporcional

No toda tarea merece un subagente.

La delegación se justifica cuando reduce contexto, coste, latencia, deuda de revisión o interferencia cognitiva sin reducir calidad ni trazabilidad.

## 4.5 Evidencia antes que autoafirmación

Los resultados internos de orquestador, minion, reviewer o recovery deben continuar gobernados por evidencia verificable.

```text
"PASS"
≠ VERIFIED_PASS
```

## 4.6 Autonomía no elimina autoridad

Un agente puede resolver problemas técnicos dentro de su alcance, pero no puede inventar ni aprobar criterios funcionales pertenecientes a una especialidad distinta o al owner.

## 4.7 Provider neutrality

PLAN 005 no debe codificar como requisito canónico ningún proveedor o modelo concreto.

## 4.8 LEAN / 5S

Cada nueva pieza debe demostrar una función distinta y necesaria. Componentes experimentales sin valor demostrable deben retirarse o no activarse.

---

# 5. Base existente que PLAN 005 debe reutilizar

PLAN 005 parte de capacidades ya materializadas y no debe recrearlas con otros nombres:

| Capacidad existente                         | Uso obligatorio en PLAN 005            |
| ------------------------------------------- | -------------------------------------- |
| `MissionContract` y modo `REDUCED`          | contrato padre de toda misión autónoma |
| Mission Authorization                       | límite de scope y operaciones          |
| execution preflight                         | validación previa y lineage            |
| `ResolvedContextManifest`                   | contexto mínimo y trazable             |
| capability / role / profile governance      | resolución de ejecutores               |
| provider-neutral execution                  | portabilidad                           |
| evidence governance fail-closed             | avance verificable                     |
| evidence freshness                          | impedir evidencia stale/unverifiable   |
| autonomous convergence loop                 | loop canónico de ejecución/corrección  |
| self-adversarial review                     | revisión interna mínima                |
| review escalation                           | límite de autoaprobación               |
| schemas / result contracts                  | interoperabilidad entre fases          |
| quality / mutation / contamination controls | QA y regresión                         |
| Git / worktree / commits                    | trazabilidad y recuperación técnica    |

Regla:

> **PLAN 005 extiende el camino canónico existente; no crea otro runtime de misión, otro sistema de evidencia, otro context resolver ni otro convergence loop.**

---

# 6. Fuera de alcance

PLAN 005 no autoriza por sí mismo:

- reabrir PLAN 004;
- modificar criterios de `CHANNEL_INTELLIGENCE`;
- modificar criterios de `SCRIPT_PRODUCT`;
- modificar criterios de `YOUTUBE_ADAPTATION`;
- abrir R1-M4 u otra fase del producto;
- producir episodios reales;
- cambiar identidad, voz, audiencia, tesis, packaging o políticas funcionales;
- adoptar Gentle como dependencia;
- adoptar Pi Agent como runtime obligatorio;
- adoptar Engram como memoria obligatoria;
- adoptar OpenSpec como dependencia obligatoria;
- crear 20/30 harnesses por imitación;
- crear un subagente para cada microtarea;
- delegación recursiva ilimitada;
- strict TDD universal para cualquier misión;
- MCP orchestration sin necesidad operativa real;
- memoria vectorial externa sin demostrar primero insuficiencia del recovery basado en artefactos;
- hardcodear “modelo frontier padre” y “modelo barato hijo”.

---

# 7. Resultado arquitectónico objetivo

```text
                         OWNER
                           │
                    MissionContract
                           │
                           ▼
                 AUTHORIZATION/PREFLIGHT
                           │
                           ▼
                    ORCHESTRATOR
              intención + estado + decisiones
                           │
                 Context / Skill Resolution
                           │
                   Delegation Decision
                 ┌─────────┼─────────┐
                 │         │         │
               INLINE   DELEGATE   ESCALATE
                 │         │         │
                 │     fresh context │
                 │         │         │
                 │       MINION      │
                 │   bounded task    │
                 │         │         │
                 │   artifact/evidence
                 │         │
                 └────┬────┘
                      ▼
                    VERIFY
                      │
            SELF-ADVERSARIAL REVIEW
                      │
             workload/risk decision
               ┌──────┴─────────┐
               │                │
             REPAIR       INTERNAL REVIEW
               │                │
               └──────┬─────────┘
                      ▼
                   REVERIFY
                      │
             CONVERGED / BLOCKED /
            MAX_ITERATIONS_REACHED
                      │
              Recovery/Progress State
                      │
          external/owner review solo
           cuando policy/hito lo exige
```

---

# 8. Estructura de implementación

PLAN 005 se divide en ocho incrementos técnicos. Los incrementos pueden materializarse en menos commits o misiones si el agente demuestra que hacerlo no reduce trazabilidad ni calidad.

```text
P5-A0 — Baseline e inventario
P5-A1 — Política autónoma INLINE / DELEGATE / ESCALATE
P5-A2 — Contrato de delegación, fresh context y profundidad
P5-A3 — Skill Digestion
P5-A4 — Skill Resolution Feedback
P5-A5 — Review Workload + Internal Independent Review
P5-A6 — Session / Compaction Recovery
P5-A7 — Routing económico + medición + demostración final
```

## 8.1 Topología de autorización obligatoria

La agrupación técnica de incrementos no crea autorización implícita. Antes de ejecutar cualquier incremento debe existir una de estas dos topologías explícitas:

```text
OPTION_A
MissionContract padre autorizado
→ enumera exactamente los P5-Ax permitidos
→ delimita paths, operaciones, capabilities, roles, profiles, presupuesto y delegación

OPTION_B
Autorización individual
→ una MissionAuthorization explícita por P5-Ax
```

En ambos casos:

```text
PASS(P5-Ax) != AUTHORIZATION(P5-Ax+1)
```

La autonomía interna solo puede operar dentro del scope ya autorizado. Si el contrato padre no enumera el siguiente incremento o si no existe autorización individual válida, el sistema debe bloquearse y escalar; no puede progresar por inferencia.

---

# 9. P5-A0 — Baseline e inventario antes de crear

## 9.1 Objetivo

Establecer la realidad observable antes de modificar arquitectura y evitar duplicaciones.

## 9.2 Inventario obligatorio

Buscar y clasificar componentes existentes relacionados con:

- delegation;
- subagents;
- task contracts;
- context manifests;
- execution profiles;
- model routing;
- skills registry/resolution;
- handoff contracts;
- review policies;
- session/progress/recovery;
- cost/token accounting;
- context budgets;
- mission convergence;
- internal/external review.

Cada candidato debe clasificarse como:

```text
REUSE_AS_IS
EXTEND
DEPRECATE
UNRELATED
MISSING
```

## 9.3 Baseline de autonomía y coste

Capturar al menos una misión controlada representativa y registrar, cuando sea observable:

```text
external_interventions_per_mission
manual_handoffs_between_tools
orchestrator_context_growth
total_context_loaded
total_tokens_or_cost_if_available
review_steps
rework_iterations
compaction_or_restart_events
mission_completion_state
```

No inventar métricas que el runtime no pueda observar. Lo no medible debe declararse `NOT_OBSERVABLE`.

## 9.4 Artefacto

Artefacto propuesto, sujeto a SEARCH BEFORE CREATE:

```text
reports/implementation/plan_005/P5_A0_BASELINE_AND_REUSE_INVENTORY.json
```

Debe incluir source revisions/checksums cuando aplique.

## 9.5 Gate P5-A0

PASS solo si:

- existe inventario completo de componentes candidatos;
- no se propone duplicar capacidades existentes;
- existe baseline observable suficiente para comparar antes/después;
- las limitaciones de medición están declaradas;
- PLAN 004 permanece cerrado e intacto.

---

# 10. P5-A1 — Política autónoma `INLINE / DELEGATE / ESCALATE`

## 10.1 Objetivo

Convertir la decisión de delegar en una política portable y verificable, no en una preferencia espontánea del modelo.

## 10.2 Resultado lógico

La política debe producir exactamente una decisión operacional:

```text
INLINE
DELEGATE
ESCALATE
```

acompañada por razones y evidence/context refs suficientes.

## 10.3 Señales para `INLINE`

- alcance pequeño/local;
- contexto necesario ya resuelto;
- operación determinista o de baja ambigüedad;
- pocos componentes afectados;
- el coste de delegar supera razonablemente el beneficio;
- no requiere separación de contexto para proteger al orquestador.

## 10.4 Señales para `DELEGATE`

- exploración amplia;
- lectura de numerosas fuentes/archivos;
- contexto especializado grande pero separable;
- tarea acotable con salida estructurada;
- capability/role/profile disponible;
- fresh context reduce contaminación del orquestador;
- trabajo paralelo o especializado aporta valor;
- reviewer interno necesita independencia contextual.

## 10.5 Señales para `ESCALATE`

- contradicción de autoridad;
- decisión funcional no delegable;
- operación fuera del scope autorizado;
- riesgo sensible no permitido por policy;
- falta de contexto canónico imprescindible;
- cambio que requiere owner review/approval;
- imposibilidad de resolver executor/capability de forma segura.

## 10.6 Restricción anti-burocracia

La política no debe forzar delegación por existir subagentes disponibles.

Caso mínimo de regresión:

```text
one-line low-risk local change
→ INLINE
```

si no existe otra razón de riesgo.

## 10.7 Materialización candidata

Solo si no existe equivalente:

```text
config/delegation_policy.json
src/core/delegation_policy.py
schemas/delegation_decision.json
```

Los nombres no son obligatorios. Si existe una policy/engine canónica equivalente, debe extenderse.

## 10.8 Tests mínimos

- tarea pequeña → INLINE;
- exploración grande y separable → DELEGATE;
- authority conflict → ESCALATE;
- falta de capability adecuada → ESCALATE o fallback permitido explícitamente;
- contexto grande pero inseparable → no delegar ciegamente;
- decisión reproducible para la misma entrada/policy;
- provider neutrality.

## 10.9 Gate P5-A1

PASS solo si el sistema toma decisiones reproducibles, conservadoras ante riesgo y sin transformar cada operación en delegación.

---

# 11. P5-A2 — Contrato de minion, fresh context, lineage y profundidad

## 11.1 Objetivo

Asegurar que una delegación interna preserve scope, autoridad, contexto y evidencia sin heredar ruido conversacional del orquestador.

## 11.2 Derivación desde la misión padre

Toda delegación debe derivarse del `MissionContract` padre y conservar como mínimo:

```text
task_id
parent_mission_id
parent_contract_ref
objective
capability_id / role_id
canonical_inputs
context_refs
allowed_files / operations
required_skills_or_rules
expected_artifact
deterministic_validations
forbidden_operations
context_budget
delegation_depth
max_delegation_depth
review_requirements
```

No todos los campos requieren un schema nuevo si el contrato existente puede representar la relación sin ambigüedad.

## 11.3 Resultado estructurado del minion

El orquestador debe recibir un resultado resumido y verificable:

```text
status
artifact_ref
evidence_refs
files_touched
checks_executed
limitations
unresolved_findings
context_manifest_ref
context_used_observation
cost/token_observation_if_available
parent_run_id
child_run_id
delegation_lineage_ref
```

No debe incorporar automáticamente todo el historial conversacional del minion.

## 11.4 Fresh context

El contexto del minion debe ser derivado por el mecanismo canónico de resolución de contexto.

Debe ser posible demostrar:

```text
PARENT_RUN_ID != CHILD_RUN_ID
CHILD_CONTEXT_REFS ⊆ AUTHORIZED_CONTEXT_FOR_TASK
CHILD_CONVERSATION_HISTORY_INHERITED = NO
CHILD_LINEAGE → PARENT_MISSION / PARENT_CONTRACT / PARENT_RUN
```

Padre e hijo pueden compartir contenido canónico cuando realmente sea necesario. El aislamiento se demuestra mediante manifests separados, refs autorizadas y lineage verificable, no mediante una desigualdad textual artificial de contenido.

## 11.5 Profundidad de delegación

Default:

```text
delegation_depth = 1
```

Una profundidad superior solo puede existir si:

- el contrato/policy lo autoriza;
- hay límite explícito;
- se preserva lineage;
- se conserva presupuesto;
- cada hijo tiene scope más acotado o una justificación verificable;
- ningún minion puede autoelevar `max_delegation_depth`.

## 11.6 Fail-closed

Debe bloquearse o escalarse:

- child sin parent lineage;
- child que amplía allowed paths;
- child que solicita capability no autorizada;
- depth excedida;
- child sin expected artifact;
- child sin context manifest verificable cuando sea obligatorio.

## 11.7 Materialización candidata

Sujeto a inventario:

```text
schemas/delegated_task_contract.json
schemas/delegated_task_result.json
src/core/delegation_contract.py
```

Preferir extensión del `MissionContract` si evita duplicar estructuras.

## 11.8 Gate P5-A2

PASS si una misión puede delegar internamente, el minion trabaja con contexto limpio y suficiente, devuelve un artefacto verificable y no puede ampliar autoridad ni profundidad por sí mismo.

---

# 12. P5-A3 — Skill Digestion / compilación de reglas operativas

## 12.1 Objetivo

Reducir contexto sin perder fidelidad a reglas canónicas.

## 12.2 Problema

Un agent/minion puede conocer la existencia de numerosas skills, pero cargar todos sus documentos completos puede:

- inflar contexto;
- aumentar tokens;
- introducir reglas irrelevantes;
- elevar riesgo de contradicción;
- reducir el beneficio de fresh context.

## 12.3 Comportamiento objetivo

```text
canonical rules / skills
        ↓
resolve applicability
        ↓
select minimum relevant set
        ↓
digest into actionable rules
        ↓
attach provenance + checksum/version
        ↓
executor context package
```

## 12.4 Restricciones

La digestión:

- no se convierte en source of truth;
- no sustituye la consulta de la fuente canónica; para una skill obligatoria, el ejecutor debe resolver y consultar la fuente completa;
- no puede modificar significado funcional;
- debe citar/source-ref cada regla derivada;
- debe invalidarse cuando cambie la fuente relevante;
- debe poder omitirse cuando la skill ya sea suficientemente pequeña;
- no debe usar IA si una extracción determinista basta.

## 12.5 Salida mínima

```text
digest_id
task_id
selected_rules
source_refs
source_checksums
canonical_skill_ref
canonical_skill_checksum_or_version
resolution_evidence
application_evidence
excluded_candidate_rules + reason
limitations
freshness
```

## 12.6 Pruebas adversariales

- una regla crítica no puede desaparecer silenciosamente;
- una fuente STALE/UNVERIFIABLE no puede producir digest FRESH;
- cambios en fuente invalidan digest;
- reglas de otro dominio no deben introducirse por similitud semántica;
- digest no debe ampliar permisos;
- una skill pequeña no debe ser “digerida” si solo añade overhead.

## 12.7 Kill criterion

Si la digestión no muestra reducción de contexto/coste o empeora fidelidad, debe quedar desactivada o eliminarse como capa adicional.

## 12.8 Gate P5-A3

PASS si el context package es menor o más enfocado que cargar las fuentes completas y las reglas críticas siguen siendo trazables y fieles.

---

# 13. P5-A4 — Skill Resolution Feedback

## 13.1 Objetivo

Demostrar qué capacidades/referencias de conocimiento fueron realmente consideradas, resueltas y aplicadas durante la ejecución.

## 13.2 Estado mínimo por skill/regla

```text
CONSIDERED
SELECTED
RESOLVED
APPLIED
UNAVAILABLE
NOT_APPLICABLE
FALLBACK_USED
```

No todos deben coexistir; el modelo debe conservar una secuencia coherente.

## 13.3 Evidencia mínima

Por delegación/misión:

```text
skills_considered
skills_selected
skills_resolved
skills_applied
skills_unavailable
fallback_used
source_refs
digest_ref_if_any
```

## 13.4 Restricciones

- `APPLIED` no equivale a aprobación funcional;
- el agente no puede declarar `RESOLVED` sin localizar la fuente correspondiente;
- un digest por sí solo no demuestra `RESOLVED` ni `APPLIED`;
- `APPLIED` requiere `canonical_skill_ref`, checksum o versión canónica, `resolution_evidence` y `application_evidence`;
- fallback debe ser explícito;
- ausencia de skill crítica debe bloquear o escalar si policy lo exige;
- no inflar artefactos con telemetría inútil.

## 13.5 Integración

Preferir integrar este feedback en result/evidence envelopes existentes en vez de crear un log paralelo.

## 13.6 Gate P5-A4

PASS cuando el orquestador puede saber si el executor trabajó con los estándares requeridos sin tener que inspeccionar manualmente toda su conversación.

---

# 14. P5-A5 — Review Workload + Internal Independent Review

## 14.1 Objetivo

Mantener calidad sin volver a un flujo de revisión externa para cada microiteración.

## 14.2 Niveles de revisión

PLAN 005 conserva exclusivamente los niveles canónicos:

```text
SELF_ONLY
INDEPENDENT_REVIEW
OWNER_REVIEW
```

La procedencia de una revisión independiente se expresa como provenance, no como un nivel adicional:

```text
review_level: INDEPENDENT_REVIEW
review_origin: INTERNAL | EXTERNAL

NO_NEW_REVIEW_LEVELS
NO_NEW_FUNCTIONAL_AUTHORITY
NO_IMPLICIT_EXECUTION_AUTHORIZATION
NO_PROVIDER_AUTHORITY_CHANGE
```

### SELF_ONLY

Parte del convergence loop del mismo ejecutor/orquestador.

### INDEPENDENT_REVIEW con `review_origin: INTERNAL`

Subagente separado dentro de la misma misión, con:

- fresh context;
- role de revisión;
- artefactos/evidencia como entrada;
- read-only cuando la naturaleza de la revisión lo permita;
- prohibición de autoaprobar cambios fuera de policy;
- resultado estructurado.

### INDEPENDENT_REVIEW con `review_origin: EXTERNAL`

Otro entorno/agente/persona cuando el riesgo o policy exige independencia mayor.

### OWNER_REVIEW

Decisiones reservadas al propietario.

## 14.3 Review Workload Decision

Antes de escalar externamente, el sistema debe poder evaluar proporcionalmente:

- riesgo;
- número de áreas/componentes afectados;
- separabilidad;
- sensibilidad;
- tamaño de evidence package;
- necesidad de authority externa;
- historial de fallos/reparaciones;
- cambio contractual o de seguridad.

No establecer umbrales arbitrarios de líneas de código como regla universal. Pueden existir señales auxiliares, no autoridad única.

## 14.4 Política anti-downgrade

Un agent/minion no puede reducir:

```text
OWNER_REVIEW → INTERNAL
INDEPENDENT_REVIEW → SELF_ONLY
```

si la policy original exige un nivel superior.

Puede elevar revisión cuando detecta riesgo real.

## 14.5 Flujo objetivo

```text
IMPLEMENT
→ VERIFY
→ SELF_ONLY
→ [si policy/risk] INDEPENDENT_REVIEW (review_origin: INTERNAL)
→ REPAIR
→ REVERIFY
→ CONVERGED
→ [si policy/hito] INDEPENDENT_REVIEW (review_origin: EXTERNAL) / OWNER
```

## 14.6 Tests mínimos

- cambio pequeño: no fuerza review externo;
- cambio sensible: no permite SELF_ONLY;
- reviewer interno recibe contexto aislado;
- reviewer interno detecta finding y provoca repair sin intervención humana;
- review policy no puede degradarse;
- authority conflict escala;
- false PASS sin evidence no cierra revisión.
- no se introducen nuevos enums canónicos de review.

## 14.7 Gate P5-A5

PASS si al menos un defecto controlado puede ser detectado por revisión interna, reparado y revalidado dentro de la misma misión sin intervención externa, manteniendo escalamiento correcto cuando se requiere.

---

# 15. P5-A6 — Session / Compaction Recovery basado en artefactos

## 15.1 Objetivo

Permitir que una misión larga sobreviva a:

- restart del proceso;
- nueva sesión compatible;
- compactación;
- transferencia entre executors compatibles;

sin depender de reconstruir la conversación completa.

## 15.2 Principio

El repositorio y los artefactos verificables continúan siendo source of truth. El recovery artifact es una **proyección operacional recuperable**, no una memoria semántica paralela.

## 15.3 Estado mínimo recuperable

```text
mission_id
contract_ref
current_state
completed_units
current_unit
remaining_units
open_findings
resolved_findings
latest_evidence_refs
active_context_refs
critical_decisions_to_preserve
last_verified_revision
next_allowed_action
review_stage
delegation_lineage_summary
```

## 15.4 Requisitos

- pequeño;
- machine-readable;
- versionado;
- checksum/freshness;
- derivable/reconciliable con estado real;
- sin chain-of-thought;
- sin secretos;
- provider-neutral;
- no puede autorizar nuevas operaciones.

## 15.4.1 Compatibilidad obligatoria con anti-replay

El recovery debe usar una de estas topologías explícitas:

```text
OPTION_A
misma reservation_id
→ lease reanudable verificable
→ identidad, scope, contract y estado real reconciliados

OPTION_B
nueva MissionAuthorization
→ vinculada al recovery artifact verificable
→ scope y autoridad nuevamente validados
```

Default fail-closed:

```text
si el replay protector vigente no soporta resume seguro con lease verificable
→ OPTION_B obligatoria
```

Una reserva huérfana, ambigua, stale o incompatible bloquea; nunca se considera autorización para reanudar.

## 15.5 Recovery fail-closed

No reanudar automáticamente cuando:

- el artifact es STALE/UNVERIFIABLE;
- el contract cambió de forma incompatible;
- cambió autoridad/scope;
- Git/state real contradice el recovery state;
- falta evidence crítica;
- la siguiente acción requiere owner.

## 15.6 Escenario E2E obligatorio

```text
start mission
→ execute/delegate partially
→ persist recovery artifact
→ simulate restart/compaction
→ new compatible executor loads only canonical minimum
→ reconcile state
→ continue
→ verify
→ converge
```

sin repetir trabajo ya verificado ni perder findings abiertos.

## 15.7 Memoria externa

Engram, vector DB u otra memoria persistente queda fuera de alcance hasta demostrar que este mecanismo es insuficiente en una misión real.

## 15.8 Gate P5-A6

PASS si la misión se puede reanudar correctamente a partir de artefactos y estado verificable, con contexto mínimo y sin dependencia de la conversación anterior.

---

# 16. P5-A7 — Routing económico, telemetría proporcional y demostración final

## 16.1 Objetivo

Elegir el executor/profile suficiente para cada trabajo y demostrar que PLAN 005 mejora autonomía o eficiencia sin degradar calidad.

## 16.2 Variables de routing

La política puede considerar:

```text
task_complexity
risk
context_size
required_capability
required_reasoning
tool_requirements
latency
expected_cost
availability
review_requirement
```

## 16.3 Regla de suficiencia

No usar “modelo más barato siempre” ni “modelo más fuerte siempre”.

```text
SELECT LOWEST SUFFICIENT CAPABILITY
SUBJECT TO RISK + QUALITY + POLICY + AUTHORIZED_CANDIDATE_SET
```

El router solo puede seleccionar o recomendar dentro del candidate set, rutas, execution profiles y presupuesto previamente autorizados. Si la misión reserva la selección al owner, el router solo recomienda. Una ruta externa, proveedor nuevo, coste de pago no autorizado o cambio de autoridad debe bloquearse; la neutralidad de proveedor no concede autoridad de proveedor.

## 16.4 Determinismo primero

Ejemplos de trabajo que deben preferir herramientas deterministas cuando sea posible:

- checksums;
- schema validation;
- file inventory;
- Git status/diff;
- test execution;
- freshness;
- compilation;
- contamination scanning;
- métricas mecánicas.

## 16.5 Telemetría mínima

Solo registrar lo que sea observable y útil:

### Autonomía

```text
external_interventions_per_mission
manual_handoffs_between_tools
missions_completed_without_external_intermediate_instruction
autonomous_repair_iterations
```

### Contexto

```text
orchestrator_context_growth
delegated_context_size
context_saved_estimate_or_NOT_OBSERVABLE
compaction_events
recovery_success
```

### Coste

```text
orchestrator_tokens_or_NOT_OBSERVABLE
minion_tokens_or_NOT_OBSERVABLE
delegation_overhead
total_cost_or_NOT_OBSERVABLE
```

### Calidad

```text
failed_delegations
rework_count
findings_detected_internally
findings_detected_only_externally
false_convergence_count
post_completion_regressions
```

### Review

```text
review_level_used
external_reviews_avoided_when_policy_allowed
external_escalations_required
```

## 16.6 No inventar números

Si el runtime/proveedor no expone tokens o coste, registrar:

```text
NOT_OBSERVABLE
```

No estimar dinero o tokens como evidencia canónica sin una metodología aprobada.

## 16.7 Comparación before/after

El éxito no requiere un porcentaje arbitrario fijo. Debe demostrarse:

1. no regresión de calidad/gates;
2. disminución observable de al menos una fuente de fricción relevante —contexto, intervención externa, retrabajo o coste—; y
3. ausencia de empeoramiento material no justificado en las demás dimensiones.

## 16.8 Gate P5-A7

PASS solo si existe una demostración controlada comparativa y el resultado justifica conservar las nuevas capacidades.

---

# 17. Misiones de demostración obligatorias

PLAN 005 no debe cerrarse únicamente con tests unitarios. Debe ejecutar un conjunto pequeño de escenarios controlados que prueben el camino real.

Toda evidencia D1–D6 debe incluir, o expresar de forma equivalente:

```text
DEMONSTRATION_CLASS: CONTROLLED_TECHNICAL_HARNESS_E2E
REAL_PRODUCT_OPERATION: NO
REAL_OPERATIONAL_SUBAGENTS_PROMOTION: NO
REAL_MULTIAGENT_RUNTIME_PROMOTION: NO
FUNCTIONAL_READINESS_CLAIM: NO
```

Estas demostraciones verifican el harness; no promueven el proyecto a operación multiagente real ni modifican estados de producto o activación.

## D1 — Tarea pequeña inline

Objetivo: demostrar que el sistema no sobreorquesta.

Esperado:

```text
Decision = INLINE
Delegated agents = 0
Mission can converge normally
```

## D2 — Exploración amplia delegada

Objetivo: proteger contexto del orquestador.

Esperado:

```text
Decision = DELEGATE
Scout/minion gets fresh context
Parent receives artifact + evidence
No scope expansion
```

## D3 — Implementación + reviewer interno + repair

Objetivo: demostrar autonomía real dentro del mismo entorno.

Esperado:

```text
IMPLEMENT
→ VERIFY
→ INDEPENDENT_REVIEW (review_origin: INTERNAL) finds controlled defect
→ REPAIR
→ REVERIFY
→ CONVERGED
```

sin instrucción externa intermedia.

## D4 — Escalamiento obligatorio

Objetivo: demostrar que autonomía no significa autoautoridad.

Esperado:

```text
authority/risk condition
→ ESCALATE
→ no unauthorized execution
```

## D5 — Recovery tras restart/compaction

Objetivo: demostrar continuidad portable.

Esperado:

```text
partial progress
→ recovery artifact
→ new compatible session
→ reconcile
→ continue without duplicated completed work
```

## D6 — Routing económico

Objetivo: demostrar que una tarea sencilla no consume perfil de máximo razonamiento sin necesidad y que una decisión compleja no se envía a un perfil insuficiente.

---

# 18. Artefactos de evidencia de PLAN 005

Rutas propuestas, sujetas a SEARCH BEFORE CREATE y al patrón real del repo:

```text
reports/implementation/plan_005/
├── P5_A0_BASELINE_AND_REUSE_INVENTORY.json
├── P5_A1_DELEGATION_POLICY_EVIDENCE.json
├── P5_A2_DELEGATED_CONTEXT_AND_LINEAGE.json
├── P5_A3_SKILL_DIGESTION_EVIDENCE.json
├── P5_A4_SKILL_RESOLUTION_FEEDBACK.json
├── P5_A5_REVIEW_AUTONOMY_EVIDENCE.json
├── P5_A6_RECOVERY_EVIDENCE.json
├── P5_A7_EFFICIENCY_COMPARISON.json
└── PLAN_005_COMPLETION_REVIEW.json
```

No es obligatorio crear nueve archivos si el sistema actual puede consolidar evidencia sin perder auditabilidad. El objetivo es evidencia suficiente, no cantidad documental.

Todos los artefactos finales deben cumplir el modelo de freshness y evidence governance existente.

---

# 19. Componentes candidatos a modificar o crear

Esta sección es **orientativa**, no una autorización ciega. P5-A0 debe resolver qué existe realmente.

## 19.1 Preferir extensión de componentes existentes

Probables superficies de integración:

```text
schemas/mission_contract.json
src/ai/execution.py
src/core/execution_preflight.py
src/core/mission_convergence.py
capability / responsibility / execution-profile governance existente
context resolution existente
result/evidence envelope existente
.agent / .agents skills existentes
```

## 19.2 Solo si faltan equivalentes

Candidatos:

```text
config/delegation_policy.json
src/core/delegation_policy.py
schemas/delegation_decision.json
schemas/delegated_task_contract.json
schemas/delegated_task_result.json
src/core/skill_digest.py
src/core/session_recovery.py
schemas/session_recovery_state.json
```

Cada nuevo archivo requiere justificación en el inventario P5-A0.

## 19.3 Prohibido

No crear simultáneamente:

- otro MissionContract;
- otro context manifest incompatible;
- otro convergence loop;
- otro evidence status system;
- otro capability registry;
- otro review authority registry;
- otro live-state document.

---

# 20. Testing y QA

## 20.1 Tests unitarios

Cubrir como mínimo:

- decisiones INLINE/DELEGATE/ESCALATE;
- fail-closed de scope/depth/lineage;
- derivación de child contract;
- skill digest freshness/provenance;
- skill feedback coherente;
- review policy no downgrade;
- recovery consistency;
- routing policy reproducible.

## 20.2 E2E

Debe existir E2E sobre el harness real, no únicamente mocks del preflight.

Como mínimo:

- D1;
- D2;
- D3;
- D4;
- D5.
- D6.

Para el cierre técnico de PLAN 005, D1–D6 deben quedar demostrados como
`PASS` en evidencia `CONTROLLED_TECHNICAL_HARNESS_E2E`; una clasificación
`INTEGRATION`, ausencia o evidencia stale bloquea el cierre.

## 20.3 Adversarial probes

Ejemplos obligatorios:

```text
child amplía allowed_files
child excede max depth
skill crítica missing pero se declara applied
review policy downgraded
recovery artifact stale se intenta reanudar
parent receives unbounded child conversation
DELEGATE for trivial task despite high overhead
false evidence result without refs
provider-specific token becomes canonical requirement
```

Todos deben ser bloqueados, degradados a LIMITATION o tratados según policy sin falsa convergencia.

## 20.4 QA transversal

Reutilizar, según impacto real:

- schema validation;
- compileall;
- targeted/full pytest;
- contamination guard;
- quality baseline;
- mutation probes selectivos cuando sean relevantes;
- evidence freshness;
- `git diff --check`;
- provider-neutrality checks;
- duplicate/dead-code review proporcional.

No ejecutar suites irrelevantes solo por ceremonia.

---

# 21. Seguridad, permisos y límites

PLAN 005 debe conservar:

- scopes de archivo;
- protected paths;
- no push sin autorización;
- no secretos en context/recovery artifacts;
- no shell/operation elevation por delegación;
- child permissions ≤ parent permissions;
- review agents read-only cuando sea suficiente;
- no autoaprobación funcional;
- no modificación de live-state fuera de autorización explícita.

Regla formal:

```text
CHILD_AUTHORITY ⊆ PARENT_AUTHORITY
```

Toda violación debe bloquearse.

---

# 22. Invalidation y freshness

Las nuevas vistas derivadas deben integrarse al modelo ya existente de invalidación.

Ejemplos:

- cambia una skill fuente → digest afectado STALE;
- cambia MissionContract → child contract incompatible no reutilizable;
- cambia context reference → recovery/context package debe revalidarse;
- cambia review policy → no puede conservarse una decisión de review inferior;
- cambia routing profile → evidence histórica sigue histórica, no se reescribe.

No se permite `FRESH` por ausencia de source inputs verificables.

---

# 23. Portabilidad

El PLAN 005 debe funcionar con ejecutores intercambiables.

El contrato canónico debe hablar de:

```text
capability
role
execution_profile
required_reasoning
context_budget
review_level
tool_requirements
```

No de:

```text
GPT padre
Claude reviewer
OpenCode minion
Codex implementer
```

Los adapters pueden mapear esos conceptos a herramientas concretas sin convertirlos en verdad canónica.

---

# 24. Criterios de aceptación global

PLAN 005 puede considerarse técnicamente completado únicamente si una ejecución controlada demuestra simultáneamente:

1. el owner puede entregar una misión una vez, mediante contrato padre que enumere incrementos o autorizaciones individuales explícitas;
2. `PASS(P5-Ax)` nunca autoriza implícitamente `P5-Ax+1`;
3. el orquestador resuelve el contexto autorizado sin depender de conversación histórica;
4. decide de forma gobernada entre inline, delegar o escalar;
5. no delega tareas triviales sin justificación;
6. las delegaciones usan manifests con `PARENT_RUN_ID != CHILD_RUN_ID`, refs autorizadas, lineage y sin herencia de conversación;
7. child authority nunca supera parent authority;
8. los minions devuelven artefactos/evidencia y no contaminan al padre con su historial completo;
9. las skills/reglas relevantes son trazables; un digest queda subordinado a la fuente canónica y no puede demostrar solo `RESOLVED` ni `APPLIED`;
10. `APPLIED` conserva referencia canónica, checksum o versión, evidencia de resolución y evidencia de aplicación;
11. la revisión usa únicamente `SELF_ONLY`, `INDEPENDENT_REVIEW` u `OWNER_REVIEW`, y `review_origin` registra `INTERNAL` o `EXTERNAL` sin crear niveles nuevos;
12. un reviewer interno puede detectar al menos un defecto controlado y provocar repair/reverify dentro de la misma misión;
13. el sistema mantiene escalation externo/owner cuando policy o autoridad lo exige;
14. el recovery es compatible con anti-replay: usa lease verificable sobre la misma reserva o una nueva autorización vinculada al recovery; ante ambigüedad bloquea;
15. la misión puede sobrevivir a restart/compactación sin perder decisiones críticas ni repetir trabajo verificado;
16. el routing solo selecciona o recomienda dentro de perfiles, rutas, candidate set y presupuesto ya autorizados; no altera autoridad de proveedor;
17. evidencia faltante/stale/unverifiable no produce falsa convergencia;
18. se conserva provider neutrality;
19. D1–D6 se declaran demostraciones técnicas controladas y no promueven operación real, runtime multiagente, readiness funcional ni estados de producto;
20. no se introducen sistemas paralelos a MissionContract/context/evidence/convergence, nuevas autoridades funcionales o autorización implícita de ejecución;
21. no se reabre PLAN 004;
22. no se autoriza una fase funcional del producto por efecto colateral;
23. existe una comparación before/after que muestre una mejora observable relevante sin regresión material de calidad.

---

# 25. Estados de PLAN 005

Estados permitidos del plan:

```text
PROPOSED_FOR_OWNER_REVIEW
APPROVED_NOT_STARTED
IN_PROGRESS
TECHNICALLY_COMPLETED_PENDING_OWNER_REVIEW
OWNER_CLOSED
BLOCKED
```

Estados de cada incremento:

```text
NOT_STARTED
IN_PROGRESS
PASS
LIMITATION
BLOCKED
```

No crear estados adicionales si los existentes expresan suficientemente la realidad.

---

# 26. Condiciones de bloqueo

PLAN 005 debe detenerse y escalar cuando:

- requiera cambiar criterio funcional de otro dominio;
- exista una contradicción con PLAN 001 o control operativo;
- una mejora requiera reabrir PLAN 004 por defecto;
- la delegación necesite ampliar scope no autorizado;
- el recovery no pueda reconciliarse con estado real;
- una policy de revisión requiera owner/external review;
- no exista capacidad suficiente para ejecutar una tarea sensible;
- el anti-replay no permita reanudación segura y no exista nueva autorización vinculada al recovery;
- el routing requiera una ruta, proveedor, perfil o presupuesto fuera del candidate set autorizado;
- la evidencia no sea verificable;
- una nueva capa no pueda justificar su existencia frente a una capacidad ya existente.

---

# 27. Política de commits y entrega

Durante implementación:

- preservar cambios preexistentes/untracked;
- no usar `git add .`;
- commits quirúrgicos por incremento material cuando ayuden a rollback/auditoría;
- mensajes de commit en español;
- no push salvo autorización explícita;
- no crear branches/worktrees adicionales si el scope puede ejecutarse limpiamente en el entorno autorizado;
- sí usar worktree cuando aisle riesgo o trabajo paralelo real.

La geometría de entrega debe decidirse por riesgo y revisabilidad, no por ceremonia.

---

# 28. Revisión proporcional y cierre

PLAN 005 no requiere enviar cada microincremento a ChatGPT, Codex u otro reviewer externo si:

- el mismo entorno ejecuta verification + self-adversarial review + repair + reverify;
- la policy no exige independencia externa;
- la evidencia permanece verificable.

La revisión externa debe concentrarse en:

- cambio de contrato/gobernanza sensible;
- hito de integración;
- demostración final;
- finding que requiera autoridad externa.

Cierre esperado:

```text
P5-A0 ... P5-A7 PASS/LIMITATION_ACCEPTED
→ PLAN_005_COMPLETION_REVIEW
→ OWNER_REVIEW
→ OWNER_CLOSED
```

El owner closure de PLAN 005 no debe abrir automáticamente ninguna fase del producto.

---

# 29. Secuencia recomendada de ejecución

Para mantener LEAN, la implementación puede agruparse en tres bloques autónomos:

## Bloque I — Delegación autónoma mínima

```text
P5-A0 Baseline/inventory
P5-A1 Delegation Policy
P5-A2 Child contract / fresh context / depth
```

Demostrar D1 + D2 antes de continuar.

## Bloque II — Contexto y skills eficientes

```text
P5-A3 Skill Digestion
P5-A4 Skill Resolution Feedback
```

Demostrar reducción/foco de contexto sin pérdida de reglas críticas.

## Bloque III — Revisión, recovery y economía

```text
P5-A5 Review Workload / Internal Review
P5-A6 Recovery
P5-A7 Routing + metrics + final demonstration
```

Demostrar D3 + D4 + D5 + D6.

Esta agrupación permite al mismo agente ejecutar loops largos autónomos sin que el usuario tenga que emitir una misión nueva por cada subfase, siempre dentro de scope y stop conditions.

---

# 30. Kill criteria por capacidad

Para impedir que PLAN 005 aumente complejidad sin valor:

## Delegation Policy

Eliminar/simplificar si toma decisiones equivalentes a una regla ya existente o provoca sobredelegación.

## Child Contract

No crear schema independiente si `MissionContract` puede expresar la relación sin ambigüedad.

## Skill Digestion

Desactivar/eliminar si no reduce contexto o introduce pérdida de fidelidad.

## Skill Resolution Feedback

No crear log paralelo si puede incluirse limpiamente en evidence/result envelopes.

## Review Workload

Simplificar si solo replica review policy existente sin aportar decisión proporcional.

## Recovery

No introducir memoria externa si artifact-based recovery funciona.

## Routing

No crear engine nuevo si profiles/routing actuales pueden incorporar las variables necesarias.

---

# 31. Resultado esperado para el usuario

Al finalizar PLAN 005, una misión típica debería poder verse así:

```text
USER / OWNER
"Ejecuta esta misión"
        ↓
AGENT HARNESS
        ↓
lee contrato y estado
        ↓
resuelve contexto y skills
        ↓
decide qué hace inline y qué delega
        ↓
subagentes trabajan con fresh context
        ↓
resultados vuelven como artefactos/evidence
        ↓
verify
        ↓
self review / internal reviewer según riesgo
        ↓
repair + reverify si es necesario
        ↓
recovery automático si cambia la sesión
        ↓
CONVERGED
        ↓
solo pide al usuario lo que realmente necesita autoridad humana
```

El éxito de PLAN 005 no se mide por “cantidad de agentes”, sino por:

```text
menos intervención externa innecesaria
+ menos contexto irrelevante
+ menor coste cuando sea posible
+ misma o mejor calidad
+ evidencia verificable
+ autoridad correctamente preservada
```

---

# 32. Decisión requerida para activar el plan

Este documento, por sí solo, **no autoriza implementación**.

Para activarlo debe existir una decisión explícita del owner y su reflejo en la única sede de estado vivo:

```text
plans/001_CONTROL_OPERATIVO.md
```

La activación debe declarar al menos:

```text
PLAN_005: APPROVED
PLAN_005_IMPLEMENTATION: AUTHORIZED
CURRENT_PLAN_OR_TRANSVERSAL_WORK: PLAN_005
CURRENT_INCREMENT: P5-A0
NEXT_ALLOWED_ACTION: EXECUTE_PLAN_005_P5_A0
```

utilizando la nomenclatura real vigente del control operativo y sin inventar estados incompatibles.

La autorización persistida cubre únicamente la corrección de autoridad derivada, provenance, evidencia, freshness y conexión con `MissionCompletionGate`. No autoriza activación productiva, readiness, publicación ni runtime multiagente real.

Tras el cierre formal de esta misión correctiva:

```text
PLAN_005_STATUS: OWNER_CLOSED
PLAN_005_IMPLEMENTATION_AUTHORIZED: NO
PLAN_005_PRODUCT_USE_AUTHORIZED: NO
PLAN_005_RUNTIME_PROMOTION_AUTHORIZED: NO
NEXT_ALLOWED_ACTION: OWNER_AUTHORIZATION_REQUIRED_FOR_NEXT_MISSION
```

---

# 33. Resumen ejecutivo

PLAN 005 debe convertir la base endurecida por PLAN 004 en un sistema más autónomo y eficiente mediante cinco ideas principales, materializadas en ocho incrementos:

```text
1. DELEGAR SOLO CUANDO APORTA VALOR
2. DAR A CADA SUBAGENTE CONTEXTO LIMPIO Y MÍNIMO
3. COMPRIMIR/RESOLVER SKILLS CON TRAZABILIDAD
4. HACER REVISIÓN Y REPARACIÓN INTERNAS CUANDO POLICY LO PERMITE
5. RECUPERAR SESIONES Y ROUTEAR CAPACIDAD/COSTE SIN DEPENDER DE PROVEEDORES
```

El criterio rector es:

> **Máxima autonomía útil con mínima complejidad necesaria.**

Y la restricción principal:

> **PLAN 005 mejora el harness; no vuelve a diseñarlo desde cero, no reabre PLAN 004 y no sustituye autoridad funcional ni del owner.**
