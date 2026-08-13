# PLAN 006 — LEAN HARNESS, ASSURANCE, ORQUESTACIÓN Y EFICIENCIA OPERATIVA

**PLAN_ID:** `006`  
**Ruta canónica propuesta:** `plans/plan_006/006_LEAN_HARNESS_ASSURANCE_ORQUESTACION_EFICIENCIA.md`  
**Proyecto:** YouTube — *Más Allá del Guion*  
**Fecha:** 2026-08-13  
**Versión:** 1.1  
**Estado:** PLAN_DEFINED_PENDING_OPERATIONAL_AUTHORIZATION  
**Naturaleza:** plan de implementación técnica transversal; no es fuente de estado vivo ni autorización automática de ejecución  
**Ámbito:** arquitectura, harness, assurance, contexto, evidencia, cierre técnico, delegación, routing, telemetría, eficiencia, integración de executors y decisión posterior sobre concurrencia  
**Executors posibles:** Codex, OpenCode u otros compatibles; ninguno adquiere autoridad funcional ni se convierte en dependencia canónica  

---

# 0. Regla de autoridad de este documento

Este plan es **vigente como dirección de implementación transversal**, pero **no puede convertirse en una segunda sede de estado vivo**.

Antes de ejecutar cualquier incremento, el executor debe resolver la realidad desde el repositorio y Git del momento, respetando la jerarquía operativa vigente del proyecto. En el repositorio auditado, `plans/001_CONTROL_OPERATIVO.md` es la sede declarada del estado vivo; ese hecho debe volver a comprobarse en cada misión y no asumirse eternamente desde este documento.

Por tanto:

```text
ESTE PLAN
→ define dirección, objetivos, dependencias y criterios de aceptación

REPOSITORIO + GIT + AUTORIDAD VIVA
→ determinan el estado real y si una misión puede ejecutarse
```

Un ZIP, una copia exportada, un chat o una versión previa de este plan sirven únicamente para auditoría externa, contraste o memoria histórica. **Nunca autorizan trabajo operativo.**

Este documento tampoco autoriza por sí solo:

- cambiar criterios funcionales de `CHANNEL_INTELLIGENCE`;
- cambiar criterios funcionales de `SCRIPT_PRODUCT`;
- cambiar criterios funcionales de `YOUTUBE_ADAPTATION`;
- promover estados de producto;
- abrir una fase funcional;
- ejecutar episodios reales;
- modificar el estado vivo;
- hacer push;
- crear nuevos agentes permanentes por conveniencia;
- ampliar el alcance de una misión sin nueva autoridad.

La secuencia `F0 → T0 → T1 → T2 → T3 → T4 → T5 → D1` descrita en este plan define dependencias y orden lógico de los incrementos. No concede `MissionAuthorization` ni autoriza su ejecución: cada incremento solo podrá ejecutarse cuando la autoridad viva autorice expresamente la misión concreta.

---

# 1. Propósito

El objetivo del plan es corregir una tensión real observada en el proyecto:

```text
HARNESS MUY CONTROLADO
+
MUCHAS VALIDACIONES
+
EVIDENCIA ABUNDANTE

no garantiza por sí solo

MAYOR EFICIENCIA
ni
MAYOR CAPACIDAD PARA DETECTAR DEFECTOS MATERIALES
```

El plan debe conseguir simultáneamente:

1. reducir tiempo de pared (`wall_time`);
2. reducir contexto innecesario y tokens cuando sean observables;
3. reducir reejecuciones equivalentes;
4. reutilizar evidencia válida cuando realmente siga siendo aplicable;
5. reducir intervención humana en decisiones técnicamente determinables;
6. mejorar la selección de cuándo usar `INLINE`, delegación o escalamiento;
7. usar el perfil/modelo/executor suficiente, no necesariamente el más fuerte ni el más barato;
8. aumentar la capacidad del assurance para encontrar defectos materiales antes del cierre;
9. proteger invariantes críticos mediante pruebas adversariales y mutation testing selectivo;
10. mantener intactas las responsabilidades funcionales y la calidad del producto;
11. demostrar que OpenCode puede aportar autonomía y topología dinámica sin convertirse en dependencia canónica;
12. decidir sobre concurrencia únicamente después de medir si aporta valor real.

El criterio rector es:

```text
COSTE / WALL TIME / CONTEXTO ↓

SIN

ESCAPED MATERIAL DEFECTS ↑
CRITICAL INVARIANT PROTECTION ↓
PRODUCT CAPABILITY ↓
```

Una optimización que solo ejecute menos pruebas, use menos agentes o consuma menos tokens **no es suficiente** si reduce la probabilidad de detectar un defecto material o degrada una responsabilidad funcional.

---

# 2. Problema empírico que motiva el plan

## 2.1 Benchmark histórico negativo: R1-M5

R1-M5 se conserva únicamente como **evidencia histórica para aprender**, no como fase actual, dependencia, bloqueo ni trabajo pendiente de este plan.

La referencia histórica disponible indica aproximadamente:

```text
wall_time_reported ≈ 17m15s
reported_files_modified = 5
tests_reported = 131
independent_review = YES
initial_technical_pass = REPORTED
material_bypasses_later_reproduced = YES
```

Los bypasses reproducidos se agruparon en cuatro familias:

1. **estado / historial:** estados como `SCREENED_WORK`, `EXCLUDED_WORK` o `INVALIDATED_WORK` podían existir sin transición requerida;
2. **lineage:** referencias previas podían ser inexistentes, incompatibles, futuras, de otra obra o con `transition_id` duplicado;
3. **authority:** se aceptaban autoridades inventadas en lugar de resolverlas contra el registro canónico;
4. **critical doubt / return routes:** podían existir resoluciones o rutas de retorno sin trigger, activación, autorización o relación válida.

La lección no es “los tests no sirven”. La lección es más precisa:

```text
ALTO COSTE
+
MUCHAS PRUEBAS
+
REVISIÓN INDEPENDIENTE

puede coexistir con

FALSA CONFIANZA
```

Por tanto, el objetivo de assurance debe medirse por **qué defectos materiales detecta**, no por cantidad bruta de tests, gates, agentes o minutos ejecutados.

## 2.2 Segundo patrón de ineficiencia observado

También se observó que misiones pequeñas podían consumir alrededor de 17–18 minutos debido a combinaciones como:

- baterías completas repetidas;
- `MissionCompletionGate` reejecutando pruebas ya ejecutadas;
- regeneración de receipts/completion;
- checksums en cascada;
- lecturas amplias;
- inspección de diffs repetida;
- revalidaciones provocadas por cambios administrativos del estado vivo;
- salida demasiado extensa.

Esto demuestra que la optimización debe actuar sobre dos dimensiones distintas:

```text
A. EFFICIENCY
   ¿cuánto trabajo cuesta demostrar algo?

B. ASSURANCE EFFECTIVENESS
   ¿qué tan bien detecta el sistema los defectos que importan?
```

No se acepta mejorar A deteriorando B.

---

# 3. Base existente que debe reutilizarse

La auditoría del repositorio exportado el 2026-08-13 muestra que el proyecto **ya tiene** una base significativa. Este plan no parte de cero.

Capacidades relevantes existentes:

| Capacidad existente | Uso en este plan |
|---|---|
| `MissionContract` | contrato padre de misión; no crear otro runtime de misión |
| `MissionAuthorization` | autorización activa, scope, roles, rutas y operaciones |
| `execution_preflight` | validación previa y lineage de ejecución |
| `MissionCompletionGate` | cierre técnico determinista; será una superficie crítica de T1/T2 |
| `evidence_freshness` | freshness directa y transitiva; debe reutilizarse y refinarse |
| `ResolvedContextManifest` | contexto resuelto, tamaño y estimación informativa |
| `context_resolution` | resolución segura y reproducible de contexto |
| `delegation_policy` | decisiones `INLINE / DELEGATE / ESCALATE` |
| `delegation_contract` | child scope, lineage y límites |
| `review_workload` | `SELF_ONLY / INDEPENDENT_REVIEW / OWNER_REVIEW` |
| `routing_policy` | selección/recomendación dentro de candidate set autorizado |
| `agent_execution_profiles` | executors/perfiles provider-neutral |
| `execution_benchmark_matrix` | sede existente de benchmarks; debe extenderse/reutilizarse |
| `execution_provenance_policy` | trazabilidad de ejecución |
| `mission_convergence` | loop de convergencia y revisión |
| `repair_integrity` | integridad de reparaciones materiales |
| `mutation_baseline` | base para mutation testing selectivo |
| PLAN 004 | context hardening, quality baseline, mutation selectivo, evidence governance |
| PLAN 005 | autonomía, delegación, context lineage, review workload, recovery, routing, E2E |
| integración OpenCode | `opencode.json`, implementer, reviewer, preflight y pruebas focales |

Regla obligatoria:

```text
SEARCH BEFORE CREATE

EXISTE CAPACIDAD EQUIVALENTE
→ REUSE / EXTEND

NO EXISTE
→ CREATE MINIMUM REQUIRED COMPONENT
```

Está prohibido crear, bajo este plan, un segundo:

- sistema de evidence;
- sistema de context resolution;
- runtime de misión;
- convergence loop;
- sistema de telemetry completo paralelo;
- router completamente nuevo;
- mutation framework alternativo;
- autoridad funcional.

---

# 4. Principios de diseño obligatorios

## 4.1 Deterministic first

Todo lo que pueda comprobarse mecánicamente debe resolverse primero con lógica determinista.

Orden preferido:

```text
DETERMINISTIC TOOL
→ LOWEST SUFFICIENT EXECUTION PROFILE
→ HIGH-REASONING PROFILE
→ SPECIALIST / OWNER si la decisión no es delegable
```

Ejemplos deterministas:

- Git status/diff;
- checksums;
- schema validation;
- inventory;
- freshness;
- dependency comparison;
- test execution;
- compile/parse;
- contamination scan;
- structured metrics;
- lineage validation;
- scope verification.

## 4.2 Minimum necessary agentic complexity

No existe una meta de “más agentes”.

La topología debe derivarse de necesidad:

```text
FUNCTIONAL RESPONSIBILITIES
+
RISK
+
COST
+
CONTEXT
+
AVAILABLE EVIDENCE

→ MINIMUM SUFFICIENT TOPOLOGY
```

El orquestador podrá decidir:

```text
0 additional actors
1 delegated specialist
N delegated specialists
```

No se interpreta “0 actores adicionales” como ausencia del executor principal; significa que la misión se resuelve inline sin delegación extra.

## 4.3 Contexto mínimo suficiente

Patrón de lectura:

```text
SEARCH
→ FIND / GREP
→ READ SLICE
→ DIGEST
→ READ FULL FILE solo si existe una razón concreta
```

No se debe leer un repositorio entero “por si acaso”.

El presupuesto de contexto es **soft**, no una cuota rígida. Una tarea editorial compleja puede necesitar más contexto que una corrección de configuración. El sistema debe justificar la ampliación, no bloquearla arbitrariamente.

## 4.4 Evidencia antes que autoafirmación

```text
"PASS"
≠
VERIFIED_PASS
```

Las afirmaciones de un executor deben comprobarse contra artefactos, tests, diffs, lineage y evidencia persistida.

## 4.5 Misiones proporcionales

Cada misión operativa derivada de este plan debe contener solo el contexto necesario para ejecutarla con seguridad.

Validación preferida:

```text
DIRECT VALIDATION
→ TARGETED TESTS
→ AFFECTED REGRESSION
→ BROADER SUITE solo si risk/fan-in/closure lo justifica
```

No pedir:

```text
individual test
+ same module suite
+ gate containing same test
+ full suite containing same test
```

salvo que cada nivel aporte evidencia diferente.

## 4.6 No crear trabajo porque sea posible

Regla transversal:

> **No ejecutar trabajo porque sea posible. Ejecutarlo porque aporta evidencia nueva necesaria.**

## 4.7 Provider / executor neutrality

Codex, OpenCode, Antigravity u otro executor compatible pueden aprovechar capacidades nativas distintas, pero el contrato canónico no debe depender de una marca concreta.

Neutralidad significa:

```text
CANONICAL CONTRACT
→ provider/executor-neutral

ADAPTER / PILOT
→ puede aprovechar capacidad específica
```

No significa que cada experimento deba repetirse automáticamente en dos executors.

## 4.8 Assurance multicapa

Debe preservarse:

```text
LAYER 1
Technical deterministic assurance

LAYER 2
Domain / specialist assurance

LAYER 3
Human / owner milestone review
```

Ninguna capa sustituye automáticamente a otra.

---

# 5. Arquitectura general del plan

```text
F0  REAL STATE + ISOLATION
 │
 ▼
T0  BASELINE + TELEMETRY FOUNDATION
 │
 ▼
T1  HISTORICAL COMPLETION + OWNER CLOSURE
 │
 ▼
T2  LEAN EXECUTION + ASSURANCE
 │
 ├── T2-A Evidence reuse + semantic applicability
 ├── T2-B Targeted invalidation + proportional verification
 ├── T2-C Adversarial assurance + selective mutation
 └── T2-D Context/output economy + product impact protection
 │
 ▼
T3  PERMISSION MODEL SIMPLIFICATION
     STATUS: RESOLVED_AT_CURRENT_BASELINE
     REOPEN_ONLY_ON_DEMONSTRATED_REGRESSION
 │
 ▼
T4  RESOURCE-AWARE ORCHESTRATOR
 │
 ▼
T5  MEASURED OPENCODE PILOT
 │
 ▼
D1  CONCURRENCY DECISION
     OPTIONAL
     BUILD NOTHING unless evidence justifies it
```

F0 no es una fase que se ejecuta una sola vez. Es un **precondicionamiento repetible antes de cada misión**.

T3 figura en el plan porque forma parte de la línea de trabajo y debe quedar registrado, pero no debe producir desarrollo adicional mientras no exista una regresión demostrada.

---

# 6. Dos carriles independientes: PRODUCT LANE y LEAN LANE

El desarrollo funcional/técnico del producto y este trabajo transversal pueden continuar en paralelo:

```text
PRODUCT LANE
CHANNEL_INTELLIGENCE / SCRIPT_PRODUCT / YOUTUBE_ADAPTATION / roadmap funcional

||

LEAN LANE
completion / evidence / assurance / routing / context / orchestration / executor pilots
```

No existe una regla general de:

```text
PRODUCT MUST STOP UNTIL LEAN FINISHES
```

ni de:

```text
LEAN MUST WAIT FOR CURRENT PRODUCT MILESTONE TO CLOSE
```

Solo deben coordinarse cuando exista una colisión concreta:

- mismos archivos;
- misma rama/worktree;
- misma dependencia compartida;
- mismo contrato crítico;
- cambio transversal que altere un consumidor funcional;
- cambio funcional que invalide una premisa del trabajo LEAN.

Cuando no exista colisión material, ambos carriles pueden ser autorizados y ejecutados independientemente: PRODUCT LANE puede recibir sus propias misiones autorizadas y LEAN LANE las suyas, sin que ninguna dependa automáticamente de la otra.

Esta independencia de carriles no exime de autorización. Cada ejecución sigue requiriendo la autoridad que corresponda según el estado vivo; que un carril no colisione con archivos del otro no sustituye la `MissionAuthorization` de la misión concreta.

---

# 7. F0 — REAL STATE + ISOLATION

## 7.1 Objetivo

Resolver el estado real del repositorio en el momento exacto de ejecutar una misión transversal y evitar que el trabajo LEAN contamine cambios de producto o viceversa.

## 7.2 F0 no es una auditoría general

F0 debe ser corto y operativo. No debe releer toda la historia del proyecto.

Debe resolver únicamente lo necesario para la superficie que se va a tocar.

## 7.3 Comprobaciones mínimas

Antes de cada misión:

```text
git branch --show-current
git rev-parse HEAD
git status --short
git diff --name-only
git worktree list
```

Además:

- leer la autoridad operativa viva aplicable;
- comprobar misión/autorización vigente;
- detectar cambios tracked preexistentes;
- detectar untracked preexistentes relevantes;
- localizar un worktree/branch LEAN ya existente;
- reutilizarlo si es seguro;
- no crear otro worktree automáticamente si no aporta aislamiento real;
- identificar cualquier solapamiento con PRODUCT LANE.

## 7.4 Regla de snapshots

Una exportación ZIP puede usarse por ChatGPT para auditoría externa, pero el executor operativo debe resolver:

```text
LIVE REPOSITORY
+
LIVE GIT
+
CURRENT CANONICAL AUTHORITIES
```

Nunca:

```text
OLD ZIP
→ operational authority
```

## 7.5 Salida mínima de F0

No se requiere un artefacto permanente nuevo si la evidencia existente de misión/preflight ya puede contenerlo.

Debe quedar comprobable:

- branch/worktree usado;
- HEAD inicial;
- cambios preexistentes;
- scope LEAN;
- colisiones reales o ausencia de ellas;
- autoridad de ejecución;
- decisión `PROCEED` o `STOP`.

## 7.6 Criterio de aceptación F0

PASS cuando:

1. la misión se ejecuta contra estado real, no una copia histórica;
2. los cambios preexistentes quedan identificados y preservados;
3. no se mezcla involuntariamente PRODUCT LANE con LEAN LANE;
4. no se crea aislamiento adicional sin necesidad;
5. no se modifica estado funcional como efecto del preflight.

## 7.7 Kill criteria

STOP si:

- no puede resolverse la autoridad vigente;
- el scope solicitado contradice el estado vivo;
- hay una colisión de escritura no aislable;
- falta una dependencia canónica necesaria;
- ejecutar la misión implicaría cambiar criterio funcional no autorizado.

---

# 8. T0 — BASELINE + TELEMETRY FOUNDATION

## 8.1 Objetivo

Medir antes de optimizar.

La pregunta de T0 es:

> **¿Dónde se consumen realmente tiempo, contexto, pruebas, delegaciones y loops de reparación?**

No se acepta optimizar por intuición si el repositorio puede producir evidencia suficiente.

## 8.2 Reutilización obligatoria

El repositorio ya tiene:

- `config/execution_benchmark_matrix.json`;
- evidencia de PLAN 005;
- `ResolvedContextManifest` con `resolved_context_size` y `estimated_tokens`;
- provenance;
- reports estructurados;
- tiempos de comandos en varias rutas de ejecución.

T0 debe **extender/reutilizar** esas superficies. No crear un segundo sistema completo de observabilidad.

## 8.3 Unidad de medición

La telemetría principal debe ser por **misión** y por **fase interna** cuando sea observable.

Fases recomendadas:

```text
context_discovery
planning_reasoning
implementation
deterministic_validation
independent_review
repair
revalidation
git_operations
```

No todas las fases existirán en todas las misiones.

## 8.4 Métricas obligatorias cuando sean observables

### Tiempo

```text
mission_wall_time
phase_wall_time
command_wall_time cuando la infraestructura ya lo exponga
```

### Validación

```text
commands_executed
unique_tests_or_test_groups_executed
tests_repeated_equivalently
full_suite_runs
targeted_suite_runs
gates_executed
```

### Contexto

```text
resolved_context_size
estimated_tokens_method
context_references_count
context_expansions
self_contained_handoffs
```

### Delegación

```text
delegation_decision
additional_actors_used
delegated_context_size
delegation_overhead
parallel_or_sequential
```

### Convergencia / repair

```text
repair_iterations
revalidation_iterations
findings_before_completion
findings_after_completion
false_convergence_events
```

### Git

```text
initial_head
final_head
actual_git_diff_files
staged_files
commit_count
```

## 8.5 Métricas por actor cuando exista actor separado

```text
actor_id_or_role
execution_profile
model_if_observable
wall_time
context_bytes
tokens_if_observable
findings
accepted_findings
```

No registrar `false_positive_count` salvo que exista una clasificación fiable posterior. No convertir opiniones del mismo actor en verdad canónica.

## 8.6 Tokens y coste

Si el executor/proveedor no expone el dato:

```text
NOT_OBSERVABLE
```

No estimar dinero o tokens como evidencia oficial salvo que exista metodología aprobada.

La estimación informativa ya existente de `ResolvedContextManifest` puede seguir utilizándose para comparar contexto, siempre identificando el método (`UTF8_BYTES_DIVIDED_BY_4`) y sin confundirlo con tokens reales facturados.

## 8.7 Baselines requeridos

T0 debe capturar al menos:

### A. Baseline histórico R1-M5

Solo como referencia negativa histórica.

Separar:

```text
reported_files_modified
actual_git_diff_files_or_NOT_VERIFIABLE
```

No reconstruir R1-M5 ni convertirlo en fase viva.

### B. Una misión técnica pequeña representativa

Sirve para medir overhead fijo del harness.

### C. Una misión de riesgo medio con validación y review

Sirve para medir coste de assurance.

### D. Cuando sea posible, una misión con delegación existente

Sirve para medir overhead y ahorro real de contexto.

No es obligatorio crear misiones artificiales solo para llenar la matriz si existen ejecuciones recientes comparables.

## 8.8 Resultado de T0

El resultado debe permitir responder:

- dónde se concentra el wall time;
- qué verificaciones se repiten;
- qué evidencia cara se vuelve a generar;
- cuánto contexto recibe cada actor;
- cuándo la delegación ahorra o añade overhead;
- qué parte del coste no es observable;
- qué optimizaciones son medibles en T1/T2/T4/T5.

## 8.9 Criterios de aceptación T0

PASS si:

1. existe baseline reproducible o verificable;
2. se distingue `MEASURED / NOT_OBSERVABLE / NOT_APPLICABLE`;
3. no se inventan números;
4. se puede atribuir tiempo al menos a las fases principales observables;
5. el baseline no requiere crear otra arquitectura de telemetry;
6. la instrumentación añade overhead pequeño y conocido;
7. R1-M5 queda registrado solo como benchmark histórico.

## 8.10 Kill criteria T0

- si medir cuesta más que el fenómeno a medir de forma recurrente, simplificar;
- si la métrica no influye en una decisión posterior, no persistirla;
- si una métrica requiere cambiar producto funcional, excluirla;
- si tokens/coste no son observables, no bloquear T0 por ello.

## 8.11 Superficies candidatas

Resolver en F0; en el snapshot actual las candidatas principales son:

- `config/execution_benchmark_matrix.json`;
- reports/evidence existentes de PLAN 005;
- `schemas/resolved_context_manifest.json`;
- `src/core/context_resolution.py`;
- provenance/mission evidence ya existentes.

Crear un componente nuevo solo si esas superficies no permiten representar la telemetría mínima sin contaminar su significado.

## 8.12 Measurement Contract

Cada optimización posterior (T2/T4/T5) debe declarar, reutilizando las superficies de T0, un contrato mínimo de medición con:

```text
metric
baseline
comparison unit
capture method
observability
decision rule
evidence reference
```

Reglas:

```text
NOT_OBSERVABLE
→ el dato no lo expone la herramienta/executor; no implica fallo automático de la misión.
   La decisión se toma con las demás métricas observables y se documenta el límite.

UNVERIFIABLE
→ garantía obligatoria que no puede comprobarse; fail-closed.
   La misión no puede cerrar como PASS sobre esa garantía sin evidencia.

No crear un nuevo sistema de telemetría si los mecanismos actuales pueden extenderse.
```

Cada contrato debe permitir responder al cierre: qué se comparó, contra qué baseline, con qué método de captura, con qué regla de decisión y con qué referencia de evidencia.

---

# 9. T1 — HISTORICAL COMPLETION + OWNER CLOSURE

## 9.1 Problema

El repositorio actual tiene una relación fuerte entre autorización activa, live state y completion.

`MissionAuthorization.verify()` comprueba que el checksum actual del live state siga coincidiendo con el snapshot de autorización. Eso es correcto durante la ejecución activa.

El problema aparece cuando una evidencia histórica de completion vuelve a depender de esa autorización **después** de haber terminado la ejecución. Entonces un cambio administrativo o futuro del live state puede hacer que evidencia histórica previamente válida parezca stale o fuerce una revalidación completa.

Patrón a eliminar:

```text
LIVE STATE CAMBIA
↓
AUTORIZACIÓN HISTÓRICA YA NO COINCIDE
↓
COMPLETION HISTÓRICO SE REVALIDA CONTRA EL PRESENTE
↓
STALE / FAIL
↓
REGENERACIÓN + TESTS + GATES
```

## 9.2 Distinción fundamental

T1 debe separar tres conceptos:

```text
A. ACTIVE EXECUTION AUTHORIZATION
   ¿puede ejecutarse esta misión ahora?

B. HISTORICAL TECHNICAL COMPLETION
   ¿qué se ejecutó y verificó realmente entonces?

C. CURRENT APPLICABILITY
   ¿sigue siendo aplicable hoy esa evidencia para una nueva decisión?
```

La relación correcta es:

```text
EXECUTION AUTHORITY SNAPSHOT
↓
TECHNICAL EXECUTION
↓
TECHNICAL COMPLETION
↓
IMMUTABLE COMPLETION IDENTITY
↓
OWNER CLOSURE REFERENCES COMPLETION
```

Mientras:

```text
LIVE STATE
→ puede seguir evolucionando
```

## 9.3 Restricción crítica

**No debilitar `MissionAuthorization.verify()` para una misión activa.**

Durante ejecución:

```text
CURRENT LIVE STATE MISMATCH
→ FAIL CLOSED
```

La optimización se aplica al **tratamiento histórico del completion**, no a permitir que una misión stale continúe ejecutándose.

## 9.4 Snapshot histórico mínimo

El completion histórico debe poder conservar, de forma inmutable o verificable, al menos:

```text
mission_id
mission_contract_sha256
authorization_artifact_sha256
authorized_scope_sha256
live_state_path
live_state_sha256_at_execution
authority_ref
authority_sha256
repository_revision_or_equivalent
required_test/evidence identities
git binding relevant to completion
completion_generated_at
```

Esto es un modelo conceptual. Debe reutilizarse el contrato/evidence envelope existente antes de crear un schema adicional.

## 9.5 Immutable completion identity

La identidad de completion debe derivarse de datos históricos congelados, no de volver a leer el live state futuro.

Conceptualmente:

```text
completion_identity = SHA256(
    canonical_execution_snapshot
    + technical_evidence_refs_and_hashes
    + completion_result
)
```

No se debe incluir metadata volátil que obligue a cambiar la identidad sin modificar la ejecución material.

## 9.6 Owner closure

El owner closure debe expresar:

```text
ACCEPTED_COMPLETION_IDENTITY
+
OWNER_DECISION
+
CLOSURE_METADATA
```

No debe significar:

```text
RE-EXECUTE MISSION
```

ni:

```text
REBUILD HISTORICAL AUTHORIZATION AGAINST CURRENT LIVE STATE
```

## 9.7 Current applicability

Si una evidencia histórica se quiere reutilizar para una misión nueva, entonces sí debe evaluarse su aplicabilidad actual mediante T2.

Por tanto:

```text
HISTORICAL_VALIDITY
≠
CURRENT_APPLICABILITY
```

Una evidencia puede seguir siendo históricamente válida y, al mismo tiempo, ser no reutilizable para una nueva misión porque cambiaron dependencias materiales.

## 9.8 Caso mínimo de aceptación

Escenario obligatorio:

1. misión autorizada contra live state A;
2. ejecución técnica completa PASS;
3. completion identity congelada;
4. live state cambia posteriormente por una acción administrativa legítima del owner;
5. el completion histórico sigue verificándose como el resultado que ocurrió;
6. owner closure puede referenciarlo sin volver a correr los implementation tests;
7. una nueva ejecución con autorización antigua sigue bloqueada contra el live state B.

## 9.9 Caso material de invalidación

También debe demostrarse:

1. cambia un input material de la ejecución;
2. la evidencia histórica no se borra ni se reescribe;
3. su **current applicability** para el nuevo caso se degrada o invalida según T2;
4. el sistema no reutiliza esa evidencia indebidamente.

## 9.10 Criterios de aceptación T1

PASS solo si:

- una edición posterior del estado vivo no vuelve stale el hecho histórico de una ejecución ya completada;
- `MissionAuthorization.verify()` continúa fail-closed durante active execution;
- owner closure no reejecuta required implementation tests únicamente para cerrar;
- el completion mantiene binding verificable con misión, autoridad, evidencia y revisión original;
- material execution dependency changes siguen afectando current applicability;
- no se convierte owner closure en aprobación funcional de producto;
- targeted authorization/freshness/completion regressions pasan.

## 9.11 Superficies candidatas actuales

El snapshot muestra acoplamiento relevante en:

- `src/core/mission_completion_gate.py`;
- `src/core/plan_005_completion_review.py`;
- `src/core/evidence_freshness.py`;
- `src/core/mission_authorization.py`;
- schemas de mission/completion/evidence relacionados.

La corrección debe localizar **el punto exacto de dependencia histórica**. No iniciar un rediseño general de invalidation ni cambiar la semántica de autorización activa salvo evidencia directa de necesidad.

## 9.12 Product impact check T1

Consumidores a proteger:

- MissionAuthorization;
- RepairIntegrity;
- recovery/anti-replay;
- MissionCompletionGate;
- provenance;
- cualquier gate de producto que dependa de evidence freshness.

Demostrar que:

```text
TECHNICAL_COMPLETION
no se convierte en
FUNCTIONAL_APPROVAL
```

---

# 10. T2 — LEAN EXECUTION + ASSURANCE

T2 es el núcleo del plan. No es una única optimización; contiene cuatro incrementos relacionados.

---

# 10A. T2-A — EVIDENCE REUSE + SEMANTIC APPLICABILITY

## 10A.1 Objetivo

Evitar reejecutar evidencia cara cuando sigue siendo válida **para el uso concreto actual**.

## 10A.2 Regla central

```text
FRESH
≠
AUTOMATICALLY REUSABLE
```

La reutilización requiere:

```text
STRUCTURAL VALIDITY
+
FRESHNESS / HISTORICAL VALIDITY
+
UNCHANGED MATERIAL DEPENDENCIES
+
SEMANTIC COMPATIBILITY WITH INTENDED USE
```

## 10A.3 Dimensiones mínimas de compatibilidad

Cuando aplique:

- identidad del test/gate;
- versión o hash de implementación del test;
- código/input afectado;
- entorno relevante;
- revisión o repository revision relevante;
- scope cubierto;
- coverage/intended assurance;
- evidencia refs;
- invalidadores conocidos;
- cambios funcionales que alteren el significado del test.

## 10A.4 Outcomes conceptuales

No necesariamente nuevos estados runtime:

```text
REUSE
→ evidencia suficiente y compatible

TARGETED_REVERIFY
→ parte sigue siendo válida; una dependencia afectada requiere revisión focal

RERUN_REQUIRED
→ cambio material invalida la evidencia para el uso solicitado

UNVERIFIABLE
→ no existe información suficiente para reutilizar con seguridad
```

Antes de crear enums/schemas nuevos, buscar si los estados existentes pueden expresar estas decisiones.

## 10A.5 Ejemplo obligatorio

```text
127 tests PASS
+
receipt históricamente válido
+
solo cambia OWNER_CLOSED administrativo

→ NO rerun 127 tests
→ closure/applicability consistency check
```

Pero:

```text
cambia código cubierto por esos tests

→ reuse denied or targeted reverify
```

## 10A.6 Criterios de aceptación

- al menos una demostración evita una reejecución cara legítimamente;
- una mutación material del input invalida la reutilización;
- `FRESH` por sí solo no basta;
- no se reutiliza una evidencia cuya cobertura no contiene el nuevo uso;
- toda reuse decision conserva provenance.

---

# 10B. T2-B — TARGETED INVALIDATION + PROPORTIONAL VERIFICATION

## 10B.1 Objetivo

Reducir cascadas de revalidación sin perder sensibilidad a cambios materiales.

## 10B.2 Materialidad

Cuando la materialidad sea funcional, la decide el owner del dominio. Infraestructura solo representa/ejecuta el impacto.

Usar la clasificación ya aprobada cuando sea aplicable:

```text
DIRECT_IMPACT
PARTIAL_DEPENDENCY_IMPACT
FULL_REASSESSMENT_REQUIRED
NO_MATERIAL_IMPACT
```

## 10B.3 Cadena de validación

Cada reparación o cambio debe empezar por el riesgo/invariante afectado:

```text
1. DIRECT CHECK / ADVERSARIAL INVARIANT
2. TARGETED MODULE TESTS
3. AFFECTED CONSUMER REGRESSION
4. BROADER SUITE only if fan-in/risk/closure justifies
5. git diff --check
```

## 10B.4 Repeated equivalent work detector

T2-B debe poder identificar, al menos en telemetría o decisión, cuando una misma prueba material se ejecuta repetidamente por wrappers equivalentes.

Ejemplos:

```text
same pytest node
same module suite repeated by gate
same evidence generator rerun without changed dependency
same completion gate rebuilt only due admin metadata
```

El objetivo no es prohibir repeticiones, sino exigir una razón.

## 10B.5 Fan-in rule

Una suite más amplia se justifica cuando:

- cambia una utilidad compartida;
- cambia un schema consumido por muchos módulos;
- cambia mission authorization/completion core;
- el targeted test no cubre consumidores relevantes;
- la reparación mostró daño más amplio;
- la misión está en un cierre técnico donde la evidencia adicional es distinta y necesaria.

## 10B.6 Criterios de aceptación

- al menos una ruta redundante se sustituye por verificación dirigida;
- un cambio shared/fan-in todavía provoca broader regression cuando corresponde;
- no se pierde ningún test crítico por simplificación ceremonial;
- las decisiones quedan explicables con evidence refs.

---

# 10C. T2-C — ADVERSARIAL ASSURANCE + SELECTIVE MUTATION

## 10C.1 Objetivo

Mejorar la capacidad de encontrar defectos materiales, usando el incidente histórico R1-M5 como fuente de invariantes que deben quedar protegidos.

## 10C.2 Regla

```text
FIX DEFECT
+
FIX CONTROL THAT LET IT ESCAPE
```

No basta con reparar la implementación.

## 10C.3 Familias de adversarial tests prioritarias

### Estado / historial

```text
SCREENED_WORK without required transition
→ FAIL

EXCLUDED_WORK without required transition
→ FAIL

INVALIDATED_WORK without required transition
→ FAIL
```

### Lineage

```text
previous ref nonexistent
→ FAIL

previous ref belongs to another work
→ FAIL

previous ref is future/incompatible
→ FAIL

duplicate transition_id
→ FAIL
```

### Authority

```text
invented authority string
→ FAIL

authority not resolvable against canonical responsibility registry
→ FAIL
```

### Critical doubt / return route

```text
RESOLVED without valid trigger/activation/authorization/evidence
→ FAIL

return route not associated with approved trigger
→ FAIL
```

Estos casos son ejemplos mínimos derivados de un defecto real. La misión debe comprobar el repositorio actual antes de fijar nombres/campos exactos.

## 10C.4 Mutation testing selectivo

Reutilizar el mecanismo existente de PLAN 004 / `mutation_baseline` cuando sea suficiente.

No crear mutation testing repo-wide.

Seleccionar invariantes críticos y mutantes **must-kill**.

Ejemplos:

```text
remove unique transition_id check
bypass responsibility_registry lookup
accept nonexistent previous transition
bypass required authorization evidence
```

Para cada must-kill mutant:

```text
TARGETED CRITICAL TESTS
→ MUST FAIL
```

Si sobrevive:

```text
SURVIVING MUTANT
→ ASSURANCE GAP
```

Otros survivors automáticos deben clasificarse:

```text
MISSING_TEST
EQUIVALENT_MUTANT
LOW_VALUE_MUTATION
REAL_WEAKNESS
```

No imponer un kill-rate global arbitrario. Para los mutantes manuales críticos seleccionados, la expectativa es que todos queden matados o que el plan se bloquee con una explicación válida de equivalencia/no aplicabilidad.

## 10C.5 Métricas de assurance

Registrar cuando sea posible:

```text
known_adversarial_cases
known_adversarial_cases_blocked
material_findings_before_completion
material_findings_after_completion
must_kill_mutants
must_kill_mutants_killed
other_survivors_classified
review_findings
accepted_review_findings
false_convergence_count
```

## 10C.6 Criterio comparativo

El éxito no es:

```text
tests_count ↑
```

Sino:

```text
COST ↓ or ≤ baseline
AND
ESCAPED MATERIAL DEFECTS ≤ baseline
AND
CRITICAL INVARIANT PROTECTION ≥ baseline
```

---

# 10D. T2-D — CONTEXT ECONOMY + OUTPUT ECONOMY + PRODUCT IMPACT

## 10D.1 Context economy

Empezar por contexto mínimo y ampliar solo por:

```text
contradiction
missing dependency
insufficient evidence
unresolved reference
material test failure
```

Reutilizar `ResolvedContextManifest`.

Soft budget conceptual:

```text
SEARCH / SLICE
↓
DIGEST / COMPRESS
↓
LOWER-COST ROUTE when sufficient
↓
JUSTIFIED LARGER CONTEXT if still needed
```

No bloquear legítimamente una investigación editorial porque supere una cuota de tokens estimada.

## 10D.2 Delegated context

Un reviewer no debería heredar automáticamente toda la conversación del implementer.

Ejemplo:

```text
ORCHESTRATOR CONTEXT
mission + authority + plan + decisions

REVIEWER CONTEXT
relevant diff + invariant + affected files + relevant tests + evidence refs
```

El objetivo es independencia y menor contaminación.

## 10D.3 Output economy

Preferencia:

```text
SUMMARY / STRUCTURED FINDINGS
→ raw logs only by reference or on demand
```

No insertar stdout masivo en el contexto del parent si basta con:

- exit code;
- test count;
- failing nodes;
- evidence ref;
- concise finding.

## 10D.4 Product Impact Check

Toda misión LEAN que cambie una superficie transversal debe comprobar:

```text
TOUCHED TECHNICAL SURFACE
↓
KNOWN CONSUMERS
↓
FUNCTIONAL RESPONSIBILITIES AFFECTED
↓
TARGETED PRODUCT REGRESSION
```

No debe convertirse en una auditoría completa ni crear un sistema documental paralelo.

### Ejemplos

**Context resolution**

Proteger:

- `EditorialProfile` exacto;
- research inputs;
- work dossiers;
- thesis context;
- opening constraints;
- provenance.

**Delegation**

Proteger:

- producer/reviewer independence;
- auditor independence;
- fidelity audit;
- functional specialist separation;
- child authority ≤ parent authority.

**Evidence reuse**

Proteger:

```text
VALID_SCHEMA
≠ FUNCTIONAL_APPROVAL
```

**Routing**

Proteger:

- no asignar autoridad funcional equivocada;
- no usar un perfil no autorizado;
- no convertir un modelo fuerte en owner.

**Context compression**

Proteger:

- no perder evidencia crítica;
- no eliminar limitaciones;
- no omitir rival readings/claims necesarios por ahorrar tokens.

**OpenCode / Codex**

Proteger:

- executor ≠ functional authority;
- adapter ≠ canonical runtime dependency.

## 10D.5 Criterios de aceptación T2-D

- una misión representativa consume menos contexto o demuestra reducción de ruido medible;
- no se pierde información funcional necesaria;
- output del parent se comprime sin perder trazabilidad;
- cada superficie transversal modificada tiene regresión focal de sus consumidores;
- no se crea otro artefacto obligatorio si una evidencia existente puede alojar el check.

---

# 11. T3 — PERMISSION MODEL SIMPLIFICATION

## 11.1 Estado

```text
STATUS: RESOLVED_AT_CURRENT_BASELINE
REOPEN_ONLY_ON_DEMONSTRATED_REGRESSION
```

## 11.2 Baseline observado en el snapshot auditado

El repositorio exportado el 2026-08-13 muestra:

```text
opencode.json
→ no repository-local permission block
→ no agent.build.permission block

technical-implementer
→ no permission block

technical-reviewer
→ no permission block
→ mantiene instrucción de independencia/read-only

mission-preflight
→ conserva comportamiento read-only y validación de autoridad

test_controlled_integration
→ verifica ausencia de permission local
→ verifica que no reaparezca la frase residual de allowlist
```

## 11.3 Qué significa “resuelto”

No significa que este plan sea autoridad futura sobre OpenCode. Significa que, en el baseline actual auditado, el defecto conocido está corregido.

F0 debe volver a comprobar la realidad antes de T5.

Tampoco significa que el repositorio tenga prohibido para siempre expresar cualquier protección técnica puntual. La decisión vigente es más precisa:

```text
NO deny-by-default
NO allowlist general de operaciones normales
NO política repository-local que convierta OpenCode en un executor artificialmente más restringido

SÍ protecciones puntuales explícitamente aprobadas por el owner
   para operaciones destructivas concretas
   cuando exista una razón demostrada
   y sin reducir la paridad operativa OpenCode ↔ Codex
```

Por ejemplo, una protección granular explícitamente aprobada como:

```text
"rm -rf *": "deny"
```

puede incorporarse si la autoridad viva la aprueba y su aplicación no reintroduce una política general de restricciones ni crea una asimetría material entre executors. La protección debe ser la mínima necesaria para el riesgo concreto, no el inicio de una nueva deny-list expansiva.

## 11.4 Reopen conditions

Reabrir T3 solo si existe evidencia como:

- reaparece una política repository-local amplia o una restricción no decidida por el owner/proyecto que altere operaciones normales o la paridad entre executors;
- OpenCode vuelve a requerir prompts por acción debido a configuración del repo;
- una actualización de OpenCode rompe la integración;
- un test descubre una asimetría material de executor causada por nuestra configuración.

No reabrir por preferencia abstracta de seguridad ni para rediseñar una política de permisos que el owner no pidió.

## 11.5 Reviewer read-only

Actualmente:

```text
reviewer read-only
→ responsabilidad/instrucción de rol
```

La garantía mecánica neutral:

```text
reviewer mechanically read-only across executors
```

queda diferida.

No es criterio de aceptación inicial de T5.

Si los pilotos demuestran necesidad real, deberá diseñarse como garantía neutral, no como una restricción exclusiva de OpenCode.

---

# 12. T4 — RESOURCE-AWARE ORCHESTRATOR

## 12.0 — T4.0 ORCHESTRATION GAP ANALYSIS

Antes de cualquier implementación de T4, exigir una comparación verificable de la necesidad de decisión contra las capacidades ya existentes:

```text
config/delegation_policy.json + src/core/delegation_policy.py
src/core/routing_policy.py
src/core/review_workload.py
config/agent_execution_profiles.json
MissionAuthorization
context resolution / ResolvedContextManifest
```

Clasificar cada necesidad como:

```text
ALREADY_COVERED
PARTIALLY_COVERED
REAL_GAP
```

No reimplementar bajo este plan:

```text
decisión INLINE / DELEGATE / ESCALATE
delegación acotada por autorización
review floor (SELF_ONLY / INDEPENDENT_REVIEW / OWNER_REVIEW)
routing dentro del candidate set autorizado
```

Implementar posteriormente solo `REAL_GAP`, con el mínimo cambio necesario y evidencia de que la capacidad existente no lo cubre.

## 12.1 Objetivo

Convertir las capacidades existentes de delegación, routing, context y review workload en una decisión unificada y proporcional de ejecución.

No crear un “superagente” permanente por defecto.

## 12.2 Base existente a extender

- `config/delegation_policy.json`;
- `src/core/delegation_policy.py`;
- `src/core/routing_policy.py`;
- `src/core/review_workload.py`;
- `config/agent_execution_profiles.json`;
- `ResolvedContextManifest`;
- mission authorization;
- PLAN 005 convergence/recovery.

## 12.3 Decisión de topología

El orquestador debe decidir, dentro de la autoridad de la misión:

```text
INLINE
→ 0 additional actors

DELEGATE
→ 1 or N delegated specialists

ESCALATE
→ owner / external specialist / higher authority
```

## 12.4 Variables mínimas de decisión

```text
task_complexity
risk
scope_size
context_size
separability
required_capability
required_reasoning
tool_requirements
latency
expected_cost_or_NOT_OBSERVABLE
availability
review_requirement
evidence_already_available
fan_in_risk
parallelizability
```

No todas deben convertirse en campos persistentes si no son necesarias para reproducir la decisión.

## 12.5 Orden de decisión recomendado

```text
1. Is deterministic execution sufficient?
   YES → deterministic / INLINE

2. Is semantic reasoning required?
   NO → stop at deterministic result

3. Is task small and low-risk?
   YES → INLINE

4. Is work separable and delegation expected to add value?
   NO → INLINE

5. Does delegation have authorized candidate capability/role/scope?
   NO → ESCALATE or INLINE according to task

6. Determine review floor.

7. Select lowest sufficient authorized execution profile.

8. Decide sequential vs parallel only when independent work exists.
```

## 12.6 Lowest sufficient route

No usar:

```text
cheapest always
```

ni:

```text
strongest always
```

Usar:

```text
LOWEST SUFFICIENT CAPABILITY
SUBJECT TO
RISK + QUALITY + POLICY + AUTHORIZED CANDIDATE SET
```

## 12.7 Model/profile policy

El modelo/perfil puede cambiar por actor si el executor lo soporta y la misión lo autoriza.

Ejemplo conceptual:

```text
EXPLORE / discovery
→ fast / low-cost sufficient profile

IMPLEMENT
→ coding-capable efficient profile

CRITICAL REVIEW
→ stronger reasoning profile if risk justifies

DETERMINISTIC VALIDATION
→ no LLM
```

No codificar nombres de modelos concretos como requisito canónico.

## 12.8 Review strategy

Usar la política existente:

```text
SELF_ONLY
INDEPENDENT_REVIEW
OWNER_REVIEW
```

No crear niveles nuevos por comodidad.

El orquestador puede elevar review, nunca reducirlo por debajo del floor canónico.

## 12.9 Context budget

Decidir:

- referencias mínimas del parent;
- qué actor necesita qué subset;
- cuándo usar `REFERENCE_ONLY`;
- cuándo `INLINE_MINIMAL`;
- `SELF_CONTAINED` solo si está justificado.

## 12.10 Verification budget

El orquestador debe seleccionar la ladder de T2-B:

```text
DIRECT
→ TARGETED
→ AFFECTED REGRESSION
→ BROAD only when justified
```

Debe poder reutilizar T2-A.

## 12.11 Delegation value check

Antes de delegar:

```text
EXPECTED VALUE OF DELEGATION
>
DELEGATION OVERHEAD
```

Señales de valor:

- reduce parent context;
- requiere especialidad separada;
- permite revisión realmente independiente;
- permite paralelismo de tareas independientes;
- reduce wall time de forma material;
- evita contaminar el razonamiento principal.

Señales de overhead sin valor:

- tarea de 1–2 minutos;
- mismo contexto duplicado en child;
- child no tiene capacidad distinta;
- parent tendrá que repetir toda la revisión;
- output del child no es reutilizable;
- delegación solo existe para “demostrar multiagent”.

## 12.12 No crear orchestrator permanente todavía

T4 debe materializar primero la **decisión provider-neutral** y las interfaces necesarias.

La forma concreta de un primary orchestrator dentro de OpenCode pertenece al piloto T5.

No crear inmediatamente un `.opencode/agents/orchestrator.md` permanente salvo que T5 lo demuestre necesario y útil.

## 12.13 Criterios de aceptación T4

PASS si, en demostraciones controladas:

1. una tarea pequeña selecciona `INLINE`;
2. una tarea separable selecciona `DELEGATE` solo con valor justificable;
3. una tarea fuera de autoridad selecciona `ESCALATE`;
4. el review floor nunca se degrada;
5. el router no sale del candidate set autorizado;
6. el executor/model profile seleccionado es trazable cuando observable;
7. el verification budget reutiliza evidencia cuando corresponde;
8. el context budget no propaga toda la conversación a cada child;
9. la decisión es reproducible con el mismo input estructurado;
10. no se crea una nueva autoridad funcional.

---

# 13. T5 — MEASURED OPENCODE PILOT

## 13.1 Objetivo

Demostrar en una misión técnica controlada que OpenCode puede aprovechar una topología dinámica de actores/subagentes, perfiles/modelos y contexto aislado, gobernada por el harness del proyecto, con menor fricción y sin dependencia canónica.

El objetivo **no** es “migrar el proyecto a OpenCode”.

## 13.2 Precondiciones

- F0 ejecutado contra repo/Git vivo;
- T0 telemetry disponible;
- T1/T2 suficientemente materializados para medir reuse/verification cuando aplique;
- T3 sigue sin regresión;
- T4 puede producir una decisión de topología/routing/review;
- la misión concreta del piloto autoriza expresamente, cuando sean necesarios:
  `DELEGATE`, actores delegados, candidate capability set, perfiles, rutas y scope de cada actor.

La topología descrita por T5 (primary / implementation / review) es una hipótesis experimental y no constituye por sí misma autorización para crear o usar subagentes. Solo podrá materializarse si la misión autorizada la incluye expresamente y respeta los límites de `AGENTS.md` y de la autoridad viva.

## 13.3 Resolver primero el primary real

No asumir desde este plan quién es el primary efectivo de OpenCode.

Antes del piloto:

- descubrir agentes/configuración efectiva;
- comprobar si el flujo usa built-in `Build`, `technical-implementer` u otra ruta;
- comprobar qué mecanismos nativos de delegación/session isolation están disponibles;
- no crear un primary permanente solo porque el diseño conceptual lo menciona.

## 13.4 Topología piloto conceptual

La hipótesis de evaluación es:

```text
PRIMARY / ORCHESTRATION RESPONSIBILITY
        │
        ├── IMPLEMENTATION responsibility
        │      bounded mission scope
        │
        └── REVIEW responsibility
               independent context / authorship
```

Puede materializarse con capacidades nativas distintas según OpenCode actual.

La topología canónica no debe depender de nombres OpenCode.

## 13.5 Review independence en T5

Requisito inicial:

```text
review independence
=
separation of responsibility
+
separate context where useful
+
separate authorship/run identity
+
no self-approval
+
findings provenance
```

No requisito inicial:

```text
mechanical READ_ONLY enforcement across executors
```

Eso queda diferido salvo evidencia de necesidad.

## 13.6 Escenario piloto recomendado

Usar una misión técnica real pero controlada de tamaño pequeño/medio que:

- tenga un cambio concreto;
- permita targeted tests;
- tenga al menos un riesgo suficiente para justificar reviewer independiente;
- no sea una fase funcional crítica del producto;
- no requiera push;
- permita medir before/after contra una ruta previa o baseline comparable.

No crear una misión artificial enorme solo para mostrar subagentes.

## 13.7 Qué medir

### Topología

```text
decision: INLINE/DELEGATE/ESCALATE
additional_actors
parallel_or_sequential
```

### Contexto

```text
primary_context_bytes
child_context_bytes
context_reuse
context_expansions
```

### Tiempo

```text
wall_time_total
phase_wall_time
review_time
repair_time
```

### Coste

```text
tokens/cost if observable
NOT_OBSERVABLE otherwise
```

### Calidad

```text
findings_detected
accepted_findings
repair_iterations
adversarial_cases
post_completion_findings
false_convergence
```

### Evidencia

- lineage parent/child;
- refs de contexto;
- actor/run identity;
- output estructurado;
- targeted validations;
- product impact check.

## 13.8 Criterios de éxito T5

PASS si:

- OpenCode ejecuta la misión sin la antigua fricción de permisos repository-local;
- la topología elegida coincide con T4, no con una obligación de “usar muchos agentes”;
- el reviewer tiene independencia suficiente de responsabilidad/contexto/autoria;
- la evidencia permite atribuir qué hizo cada actor;
- no se pierde autoridad ni scope;
- el parent no absorbe conversaciones completas innecesarias;
- la validación es proporcional;
- el resultado es igual o mejor en calidad que el baseline comparable;
- existe mejora observable en al menos una dimensión relevante o un trade-off documentado;
- no se crea dependencia canónica de OpenCode.

## 13.9 Neutralidad

No es obligatorio repetir inmediatamente el piloto en Codex.

Neutralidad se demuestra inicialmente mediante:

- contratos provider-neutral;
- roles/responsabilidades neutrales;
- executor adapter;
- ausencia de identifiers OpenCode en contratos de producto;
- posibilidad arquitectónica de sustitución.

Repetir con Codex solo si aporta evidencia nueva necesaria.

## 13.10 External environment blockers

Si OpenCode falla por una condición de instalación/home/log fuera del workspace:

- registrar blocker externo;
- no modificar repo para “arreglar” el home del usuario;
- no ampliar scope;
- ejecutar en el entorno nativo apropiado cuando corresponda.

---

# 14. D1 — CONCURRENCY DECISION

## 14.1 Naturaleza

D1 es una **decisión**, no una fase de implementación obligatoria.

La pregunta es:

> **¿La concurrencia reduce de forma medible wall time o coste sin degradar assurance, trazabilidad ni producto?**

## 14.2 Default

```text
NO EVIDENCE OF BENEFIT
→ BUILD NOTHING
```

## 14.3 No implementar todavía

No crear por adelantado:

```text
ACTIVE_WAVE
ACTIVE_MISSIONS
MISSION_DEPENDENCIES
multi-mission scheduler
multi-mission lifecycle
mandatory concurrent acceptance gate
```

El dolor actual demostrado es eficiencia + calidad de assurance, no ausencia de un scheduler general.

## 14.4 Cuándo tiene sentido experimentar

Solo si T0/T5 muestran tareas con:

- independencia real;
- poca colisión de archivos;
- contexto separable;
- suficiente duración como para amortizar overhead;
- review/analysis paralelizables;
- beneficio potencial de wall time.

## 14.5 Métricas de decisión

Comparar:

```text
SEQUENTIAL WALL TIME
vs
PARALLEL WALL TIME

TOTAL TOKENS/COST
DELEGATION OVERHEAD
MERGE/CONFLICT OVERHEAD
QUALITY FINDINGS
ESCAPED DEFECTS
CONTEXT DUPLICATION
```

Puede ocurrir:

```text
wall_time ↓
cost ↑
```

La decisión debe registrar el trade-off y el caso de uso donde compensa.

## 14.6 Outcome

D1 debe terminar en uno de estos resultados conceptuales:

```text
NO_CONCURRENCY_NEEDED

LIMITED_CONCURRENCY_FOR_SPECIFIC_TOPOLOGIES

FURTHER_EXPERIMENT_REQUIRED
```

No hace falta crear esos valores como enums canónicos si un artefacto existente puede documentar la decisión.

## 14.7 Criterio de aceptación global

El plan puede cerrarse con:

```text
NO_CONCURRENCY_NEEDED
```

sin considerarlo fracaso.

---

# 15. Secuencia de implementación recomendada

## 15.1 Orden lógico

```text
F0
→ T0
→ T1
→ T2-A
→ T2-B
→ T2-C
→ T2-D
→ T3 regression check only
→ T4
→ T5
→ D1
```

## 15.2 Dependencias reales

### T0 antes de T1/T2/T4/T5

Sin baseline no podemos demostrar ahorro ni comparar trade-offs.

### T1 antes del cierre final de T2

T1 elimina una fuente concreta de reejecución histórica y clarifica la semántica de evidencia que T2 reutilizará.

### T2-A y T2-B están estrechamente relacionados

Evidence reuse necesita saber qué cambió; targeted invalidation necesita saber qué evidencia puede conservarse.

Pueden implementarse en incrementos separados pero deben converger en una decisión coherente.

### T2-C puede comenzar una vez identificados los invariantes críticos

No depende de que toda la optimización de contexto esté terminada.

### T2-D consume mecanismos previos

Debe verificar que las optimizaciones de evidencia/assurance no dañan producto ni contexto.

### T3 no genera misión salvo regresión

Solo comprobar baseline antes de T5.

### T4 requiere T0 + suficiente T2

El orquestador debe poder decidir con información real de coste/riesgo/evidence reuse.

### T5 requiere T4

OpenCode debe pilotar una política ya definida, no improvisar la arquitectura canónica.

### D1 requiere T5/T0

Sin métricas reales no hay decisión racional sobre concurrencia.

## 15.3 Agrupación operativa en fases

La descomposición `M-LEAN-01` a `M-LEAN-08` es una descomposición conceptual de capacidades para trazabilidad; no obliga a ejecutar ocho misiones independientes. La ejecución real se agrupa en tres fases secuenciales y una decisión final:

```text
FASE 1 → F0 preflight + T0 (BASELINE + TELEMETRY) + T1 (HISTORICAL COMPLETION + OWNER CLOSURE)
FASE 2 → T2-A + T2-B + T2-C + T2-D (LEAN assurance + evidencia + contexto)
FASE 3 → T4.0 (gap analysis) + T4 + T5 (orquestación adaptativa + piloto OpenCode)
D1     → decisión de concurrencia, no una cuarta fase
```

- Cada fase se autoriza y ejecuta como misión propia antes de iniciar la siguiente.
- No se exigen auditorías profundas independientes entre fases; la auditoría transversal se realiza una sola vez al final de las tres fases.
- `D1 — CONCURRENCY DECISION` es una decisión, no una cuarta misión, y puede concluir válidamente en `NO_CONCURRENCY_NEEDED` sin evidencia de que construir algo aporte valor.

---

# 16. Paquetes de misión propuestos

Este plan es detallado; las misiones derivadas deben seguir siendo **quirúrgicas y proporcionales**.

## M-LEAN-01 — Baseline y telemetría

**Cubre:** T0  
**Objetivo:** reutilizar/expandir telemetry existente y generar baseline comparable.  
**No incluye:** optimizar todavía.  

## M-LEAN-02 — Historical completion / closure decoupling

**Cubre:** T1  
**Objetivo:** congelar completion histórico y evitar revalidación causada solo por futuro live state.  
**Protección:** active MissionAuthorization continúa fail-closed.  

## M-LEAN-03 — Evidence reuse + targeted invalidation

**Cubre:** T2-A + parte de T2-B  
**Objetivo:** decidir reuse/reverify/rerun de forma verificable.  

## M-LEAN-04 — Proportional verification

**Cubre:** resto de T2-B  
**Objetivo:** eliminar al menos una ruta equivalente redundante y mantener fan-in protection.  

## M-LEAN-05 — Assurance adversarial + selective mutation

**Cubre:** T2-C  
**Objetivo:** transformar defectos escapados en invariantes/must-kill mutants.  

## M-LEAN-06 — Context/output economy + product impact

**Cubre:** T2-D  
**Objetivo:** reducir context/output sin perder capacidades funcionales.  

## M-LEAN-07 — Resource-aware orchestration

**Cubre:** T4  
**Objetivo:** integrar routing/delegation/review/context/verification budgets.  

## M-LEAN-08 — OpenCode measured pilot

**Cubre:** T5  
**Objetivo:** demostrar topología dinámica medible sin dependencia canónica.  

## D-LEAN-01 — Concurrency decision

**Cubre:** D1  
**Objetivo:** decidir si construir algo o no.  
**Default:** no implementación sin evidencia.

Las misiones pueden fusionarse o dividirse si F0 demuestra que los cambios reales del repositorio lo justifican. La numeración no debe convertirse en autoridad operativa ni obligar a ejecutar un incremento irrelevante.

---

# 17. Política de pruebas del plan

## 17.1 Principio

```text
TEST COUNT
≠
ASSURANCE QUALITY
```

## 17.2 Capas

### Capa A — Direct / invariant

Comprueba la regla exacta que se está cambiando.

### Capa B — Targeted module

Comprueba regresiones inmediatas.

### Capa C — Consumer regression

Comprueba consumidores reales afectados.

### Capa D — Broader suite

Solo por:

- shared fan-in;
- riesgo alto;
- cambio core;
- cierre técnico cuando aporta evidencia distinta;
- defecto que demuestre alcance mayor.

## 17.3 Selective mutation

Solo sobre invariantes críticos elegidos.

## 17.4 `git diff --check`

Debe mantenerse como control barato de cierre de cambios textuales/código.

## 17.5 No repetir wrappers equivalentes

Si un gate ya ejecutó y verificó exactamente la misma suite, otra ejecución debe justificar qué evidencia nueva aporta.

---

# 18. Política de evidencia

## 18.1 Evidencia debe ahorrar trabajo

Si persistir evidence no permite reutilizarla cuando las dependencias siguen compatibles, su utilidad es incompleta.

## 18.2 Identidad

Todo artefacto reutilizable debe tener suficiente identidad para comprobar:

- qué se ejecutó;
- con qué inputs;
- contra qué revisión/scope;
- con qué tests;
- qué produjo;
- qué dependencias materiales lo soportan.

## 18.3 Freshness

Freshness sigue siendo fail-closed donde corresponda, pero debe distinguir:

```text
historical evidence validity
current reuse applicability
```

## 18.4 No borrar historia

Una evidencia que ya no sea aplicable no debe reescribirse como si nunca hubiera sido válida.

Debe conservar su historia y degradar su aplicabilidad actual.

---

# 19. Política de contexto

## 19.1 Precedencia

Conservar:

```text
NORMATIVE_CONTEXT
>
OWNER_AUTHORIZED_MISSION_SCOPE
>
CASE_INPUT
>
OPTIONAL_EVIDENCE
```

## 19.2 Progressive disclosure

No enviar a cada actor:

- todo el plan;
- toda la conversación;
- toda la historia del repositorio;
- stdout completo;
- todos los schemas “por si acaso”.

## 19.3 Context expansion triggers

Solo ampliar por causa concreta.

## 19.4 Context quality

Menos contexto no es mejor si elimina:

- restricciones funcionales;
- evidencia;
- limitaciones;
- claims rivales;
- owner authority;
- consumers relevantes.

---

# 20. Política de agentes y subagentes

Orden de preferencia:

```text
existing deterministic tool
↓
existing script/gate
↓
existing skill/procedure
↓
existing agent capability
↓
temporary delegated actor
↓
new persistent agent only if evidence justifies it
```

No crear un agente nuevo únicamente porque exista una responsabilidad conceptual.

Un actor temporal de Codex/OpenCode no se convierte en un agente del producto por existir durante una misión.

---

# 21. Política de Git y aislamiento

## 21.1 Preservar cambios ajenos

Cada misión debe identificar preexistentes antes de editar.

## 21.2 Staging selectivo

No mezclar cambios PRODUCT/LEAN en el mismo commit salvo que la dependencia sea inseparable y esté autorizada.

## 21.3 Worktrees

Usarlos cuando reduzcan colisión real. No crear un worktree por ceremonia.

## 21.4 Push

No hacer push salvo autorización explícita separada.

## 21.5 Commits

La política de cada misión determinará si hay commit local. El plan no impone confirmaciones de herramienta adicionales.

---

# 22. Product capability protection

El plan protege como mínimo las responsabilidades funcionales aprobadas:

```text
CHANNEL_INTELLIGENCE
→ identidad, pertenencia, audiencia matriz, promesa principal,
  territorios, voz, límites, EditorialProfile

SCRIPT_PRODUCT
→ brief, investigación, evidencia, obras, tesis, estructura,
  escritura, edición, fidelidad, aprobación editorial

YOUTUBE_ADAPTATION — ACTIVO EN EL ALCANCE ACTUAL
→ audiencia concreta del episodio
→ promesa visible
→ YT_EARLY_PACKAGING_HYPOTHESIS
   (título de trabajo provisional y concepto inicial de miniatura)
→ promise-content alignment
→ opening readiness / obligaciones de apertura
→ adaptación textual de la apertura cuando corresponda al MVP
→ duración orientativa para plataforma
→ overpromise
→ riesgos de plataforma derivados del texto
→ riesgos preliminares de rights/reuse derivados del guion

YOUTUBE_ADAPTATION — DIFERIDO (Etapa 2, no autorizada)
→ packaging final
→ título final
→ miniatura final
→ Shorts
→ SEO
→ metadatos de publicación
→ distribución
→ aprendizaje post-publicación
```

Reglas no negociables:

```text
TECHNICAL_PASS ≠ FUNCTIONAL_APPROVAL
FUNCTIONAL_APPROVAL ≠ TECHNICAL_ACTIVATION
MOCK_PASS ≠ REAL_OPERATION_DEMONSTRATED
VALID_SCHEMA ≠ GOOD_EDITORIAL_RESULT
```

Toda optimización debe respetar estas fronteras.

---

# 23. Riesgos principales y mitigaciones

| Riesgo | Consecuencia | Mitigación |
|---|---|---|
| Reuse demasiado agresivo | falsa confianza | semantic applicability + fail-closed `UNVERIFIABLE` |
| T1 debilita autorización activa | ejecución fuera de estado vivo | proteger `MissionAuthorization.verify()` durante active execution |
| Menos tests = menos detección | defectos escapados | adversarial invariants + must-kill mutation |
| Telemetry excesiva | nuevo overhead | solo métricas con decisión asociada |
| Context compression excesiva | pérdida funcional | Product Impact Check + soft budgets |
| Orchestrator demasiado complejo | más coste que valor | minimum sufficient topology |
| Delegación por moda | overhead | delegation value check |
| Reviewer pierde independencia | autoaprobación | responsibility/context/authorship separation + review floor |
| OpenCode se vuelve dependencia | lock-in | provider-neutral contracts/adapters |
| Concurrencia genera conflictos | más tiempo/coste | D1 default build-nothing |
| Plan se vuelve live-state | doble autoridad | F0 + authority rule §0 |
| Mutation testing global | coste/noise | selective critical scope |
| Suite completa ceremonial | wall time alto | proportional verification |

---

# 24. Criterios globales de aceptación

El plan puede considerarse exitoso cuando se demuestre, con evidencia controlada:

1. **Historical completion:** una ejecución técnicamente completada conserva validez histórica después de un cambio administrativo posterior del estado vivo.
2. **Active authorization:** una autorización vieja sigue bloqueada si el live state actual cambió materialmente.
3. **Closure fast path:** owner closure no reejecuta implementation tests solo por cerrar.
4. **Evidence reuse:** al menos una evidencia cara compatible se reutiliza y evita una reejecución innecesaria.
5. **Material invalidation:** un cambio material sigue invalidando/requiriendo revalidación de la evidencia afectada.
6. **Targeted verification:** al menos una ruta redundante/equivalente se reemplaza por una validación dirigida con la misma o mayor protección relevante.
7. **Assurance effectiveness:** los ataques conocidos de invariantes críticos quedan bloqueados.
8. **Mutation:** todos los must-kill mutants seleccionados de invariantes críticos son matados o justificados como no aplicables/equivalentes con evidencia.
9. **Survivors:** un survivor real se clasifica como assurance gap, no se ignora.
10. **Context economy:** una misión representativa reduce contexto innecesario de forma medible o demuestra una mejora de distribución entre actores.
11. **Output economy:** raw logs no se propagan innecesariamente al parent.
12. **Wall time:** se mide y mejora en al menos un caso representativo o se documenta un trade-off donde la mayor duración compra assurance material demostrable.
13. **Orchestration:** una misión pequeña usa `INLINE`.
14. **Delegation:** una misión separable usa `DELEGATE` solo cuando aporta valor observable/razonado.
15. **Escalation:** una decisión fuera de autoridad escala en lugar de inventarse.
16. **Review:** el review floor nunca se degrada.
17. **Product protection:** no hay regresión material en consumidores funcionales de las superficies modificadas.
18. **Layer separation:** L1 técnico no sustituye L2 especialista ni L3 owner.
19. **OpenCode:** un piloto demuestra utilidad real y medible sin dependencia canónica.
20. **Executor neutrality:** el contrato canónico no contiene requisitos específicos de OpenCode/Codex innecesarios.
21. **T3 baseline:** no reaparece una política repository-local amplia de permisos OpenCode; solo pueden añadirse protecciones puntuales explícitamente aprobadas por el owner, proporcionales al riesgo y sin degradar la paridad operativa entre executors.
22. **Reviewer independence:** T5 demuestra separación de responsabilidad/contexto/autoria; mechanical read-only no es requisito inicial.
23. **Product lane independence:** el roadmap de producto puede continuar sin esperar el cierre total del plan LEAN.
24. **Concurrency optional:** el plan puede cerrarse sin scheduler ni dos misiones concurrentes.
25. **Overall:** existe una mejora observable relevante de eficiencia sin regresión material de assurance o producto.

No se exige un porcentaje arbitrario global de ahorro. La comparación debe ser real, reproducible y útil.

---

# 25. Condiciones globales de bloqueo

Detener una misión y escalar si:

- requiere inventar criterio funcional;
- requiere modificar autoridad de otro dominio;
- la optimización necesita reducir una garantía crítica sin evidencia compensatoria;
- no puede determinarse qué evidencia se está reutilizando;
- current applicability es `UNVERIFIABLE` y la misión intenta reutilizar de todos modos;
- un must-kill mutant sobrevive;
- el review necesario se degrada por ahorrar coste;
- la topología necesita scope fuera de autoridad;
- una ruta/modelo de pago no está autorizado cuando esa autorización es necesaria;
- el executor intenta convertir una capacidad específica en dependencia canónica;
- PRODUCT LANE y LEAN LANE colisionan y no existe aislamiento seguro;
- la misión necesita cambiar el live state sin autorización explícita.

---

# 26. Qué NO hacer durante este plan

No:

- reabrir PLAN 004 completo;
- reabrir PLAN 005 completo;
- convertir R1-M5 en fase viva;
- hacer depender LEAN del owner review de un milestone de producto no relacionado;
- usar ZIPs como autoridad operacional;
- crear un segundo evidence system;
- crear un segundo context resolver;
- crear otro convergence loop;
- crear telemetry paralela completa;
- usar test count como proxy de calidad;
- ejecutar full suite automáticamente después de cada reparación;
- hacer mutation testing global;
- crear un swarm permanente;
- crear un orchestrator OpenCode permanente antes del piloto;
- repetir el piloto automáticamente en Codex;
- crear multi-mission scheduler antes de D1;
- convertir concurrency en criterio de aceptación;
- usar hard token limits que degraden investigación/editorial;
- confundir reducción de coste con éxito si baja assurance;
- confundir technical completion con functional approval;
- convertir OpenCode/Codex en autoridad funcional;
- crear restricciones repository-local de OpenCode sin decisión explícita del owner.

---

# 27. Evidencia final esperada del programa

Sin imponer nombres nuevos si no hacen falta, al cierre debe existir evidencia suficiente para reconstruir:

```text
BASELINE
→ qué costaba antes

T1
→ cómo se separó historical completion de live-state futuro

T2
→ qué evidencia se reutilizó
→ qué invalidación fue dirigida
→ qué tests adversariales protegen invariantes
→ qué mutantes críticos fueron matados
→ qué contexto/output se redujo
→ qué consumidores de producto fueron protegidos

T4
→ por qué una misión fue INLINE/DELEGATE/ESCALATE
→ por qué se eligió ese review/profile/context/verification budget

T5
→ cómo funcionó OpenCode realmente
→ qué actores/contextos/evidence produjo
→ coste/tiempo/calidad comparados

D1
→ por qué concurrency se implementa o no
```

La evidencia debe preferir reports estructurados y refs antes que logs gigantes.

---

# 28. Estado actual de T3 en el snapshot externo auditado

**Nota importante:** esta sección es observación externa del snapshot exportado el 2026-08-13 y **no sustituye F0 ni el estado vivo**.

Observado:

```text
opencode.json
= schema + AGENTS instructions + share disabled + subagent_depth

NO repository-local permission
NO agent.build.permission

technical-implementer
= no permission block

technical-reviewer
= no permission block
= independent/read-only instruction retained
= no residual "allowlisted inspection commands"

test_controlled_integration.py
= asserts absence of local permission policy
= asserts residual phrase does not reappear
```

Esto justifica:

```text
T3_STATUS = RESOLVED_AT_CURRENT_BASELINE
```

pero cualquier ejecución futura debe confirmarlo desde el repo vivo.

---

# 29. Primer incremento candidato tras autorización expresa

La secuencia lógica del plan no constituye autorización operativa.

No empezar por T4 ni por el piloto multiagente.

La primera misión candidata de PLAN 006 es:

```text
F0
→ M-LEAN-01 / T0 BASELINE + TELEMETRY
```

Su existencia en este plan no constituye autorización. Solo podrá ejecutarse cuando la autoridad viva autorice expresamente esa misión.

Después:

```text
M-LEAN-02 / T1
→ M-LEAN-03 / T2-A
→ M-LEAN-04 / T2-B
→ M-LEAN-05 / T2-C
→ M-LEAN-06 / T2-D
→ T3 regression check
→ M-LEAN-07 / T4
→ M-LEAN-08 / T5
→ D-LEAN-01 / D1
```

No iniciar una misión que dependa de evidencia todavía no producida.

Las misiones independientes pueden prepararse o ejecutarse en paralelo cuando F0 confirme que no existe dependencia causal, colisión material de escritura ni conflicto sobre una superficie compartida y cada misión cuente con su propia autorización operativa. El paralelismo no se fuerza: se utiliza solo cuando reduce espera o retrabajo sin debilitar assurance, trazabilidad o producto.

---

# 30. Regla de cierre del plan

Este plan se considera cumplido cuando el harness puede demostrar:

```text
LESS UNNECESSARY WORK
+
MORE TARGETED ASSURANCE
+
MEASURED RESOURCE-AWARE EXECUTION
+
NO PRODUCT REGRESSION
+
NO EXECUTOR LOCK-IN
```

El éxito **no** se mide por:

- número de agentes;
- número de tests;
- número de schemas;
- número de gates;
- número de reportes;
- cantidad de paralelismo;
- cantidad de automatización creada.

Se mide por una relación mejor entre:

```text
MATERIAL DEFECTS DETECTED
--------------------------------
TIME + CONTEXT + TOKENS + TESTS + HUMAN FRICTION
```

sin perder las garantías funcionales y técnicas que hacen confiable al producto.

---

# 31. Fuentes y superficies usadas para reconstruir esta versión

## Repositorio auditado externamente

Snapshot exportado recibido el 2026-08-13 aproximadamente a las 09:48. Se utilizó únicamente para contrastar la implementación existente; no constituye autoridad operacional.

Superficies revisadas para este plan:

- `AGENTS.md`;
- `plans/001_CONTROL_OPERATIVO.md`;
- `plans/plan_004/004_hardening_transversal_harness_capabilities_contexto_calidad.md`;
- `plans/plan_005/005_autonomia_delegacion_contexto_y_eficiencia_operativa.md`;
- `config/delegation_policy.json`;
- `config/agent_execution_profiles.json`;
- `config/execution_benchmark_matrix.json`;
- `config/context_resolution_policy.json`;
- `config/execution_provenance_policy.json`;
- `src/core/mission_authorization.py`;
- `src/core/mission_completion_gate.py`;
- `src/core/evidence_freshness.py`;
- `src/core/context_resolution.py`;
- `src/core/delegation_policy.py`;
- `src/core/routing_policy.py`;
- `src/core/review_workload.py`;
- `src/core/mutation_baseline.py`;
- `src/core/plan_005_completion_review.py`;
- `opencode.json`;
- `.opencode/agents/technical-implementer.md`;
- `.opencode/agents/technical-reviewer.md`;
- `.opencode/commands/mission-preflight.md`;
- `tests/opencode/test_controlled_integration.py`.

## Fuentes metodológicas del proyecto

Se preservan especialmente los principios ya documentados de:

- misiones proporcionales y mínimo contexto suficiente;
- no repetir controles equivalentes;
- reutilizar patrones existentes;
- reducir microgestión, tokens, fricción y retrabajo;
- separar autoridad funcional y materialización técnica;
- convertir errores reales en controles útiles;
- usar agentes/skills solo cuando exista razón arquitectónica;
- no convertir executors en el producto.

---

# 32. Resumen ejecutivo final

```text
F0
REALITY FIRST, EVERY MISSION

T0
MEASURE BEFORE OPTIMIZE

T1
FREEZE HISTORICAL COMPLETION
DO NOT WEAKEN ACTIVE AUTHORIZATION

T2
REUSE WHAT IS STILL VALID
INVALIDATE ONLY WHAT CHANGED
TEST CRITICAL INVARIANTS ADVERSARIALLY
MUTATE SELECTIVELY
REDUCE CONTEXT/OUTPUT
PROTECT PRODUCT

T3
RESOLVED_AT_CURRENT_BASELINE
REOPEN ONLY ON REAL REGRESSION

T4
CHOOSE MINIMUM SUFFICIENT TOPOLOGY
0 / 1 / N ADDITIONAL ACTORS
LOWEST SUFFICIENT PROFILE
PROPORTIONAL REVIEW + VERIFICATION

T5
MEASURE OPENCODE IN REAL CONTROLLED WORK
NO CANONICAL DEPENDENCY
NO MECHANICAL READ_ONLY REQUIREMENT YET

D1
CONCURRENCY IS A DECISION, NOT A GOAL
BUILD NOTHING IF DATA DOES NOT JUSTIFY IT
```

**Primer incremento candidato tras autorización expresa:** `F0 → T0 / M-LEAN-01`. Esta referencia no constituye autorización operativa.
