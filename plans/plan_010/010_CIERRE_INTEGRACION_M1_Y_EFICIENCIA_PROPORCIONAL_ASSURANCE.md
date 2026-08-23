# PLAN 010 — Cierre de integración M1 y eficiencia proporcional del assurance

**PLAN_ID:** `010`
**Proyecto:** YouTube — *Más Allá del Guion*
**Naturaleza:** plan técnico correctivo y acotado
**Autoridad de estado vivo:** `plans/001_CONTROL_OPERATIVO.md`
**Relación con PLAN 009:** PLAN 009 conserva la hoja de ruta progresiva; PLAN 010 propone correcciones técnicas verificadas para su integración M1 y el uso proporcional del assurance.

## 0. Estado y autorización

```text
PLAN_010_STATUS: IN_PROGRESS
PLAN_010_IMPLEMENTATION: AUTHORIZED_FOR_M1_ONLY
PLAN_010_ACTIVE_BLOCK: NONE
PLAN_010_M0_STATUS: COMPLETED
PLAN_010_M1_STATUS: OWNER_ACCEPTED
PLAN_010_M1_COMMIT: COMPLETED
PLAN_010_M1_PUSH: COMPLETED
PLAN_010_M1_REMOTE_BRANCH: origin/plan010/m1-integration-lean-assurance
PLAN_010_M2_M3: NOT_AUTHORIZED
PLAN_010_PRODUCT_USE: NOT_AUTHORIZED
PLAN_010_REAL_PROVIDER: NO
PLAN_010_P2: NOT_AUTHORIZED
PLAN_010_B5_I2_REAL: NOT_AUTHORIZED
PLAN_010_B5_I3: NOT_AUTHORIZED
PLAN_010_COMMIT: NO
PLAN_010_PUSH: NO
```

La materialización de este documento no inicia ninguno de sus bloques. La autoridad operativa y las autorizaciones de implementación se resuelven exclusivamente desde el control operativo vigente.

## 1. Propósito

Cerrar, mediante misiones futuras explícitamente autorizadas, los defectos confirmados de integración M1 y aplicar únicamente mejoras LEAN de assurance que reutilicen mecanismos existentes.

Principios obligatorios:

```text
REUSE BEFORE CREATE
CONNECT BEFORE REDESIGN
SIMPLIFY BEFORE EXTEND
NO_NEW_GENERAL_HARDENING
```

PLAN 010 no redefine criterios funcionales, no crea una nueva fase de producto y no sustituye la autoridad de PLAN 009 ni del control operativo.

## 2. Límites globales

Quedan fuera de PLAN 010:

```text
REAL_PROVIDER
P2_REAL
B5_I2_REAL
B5_I3
B5_5
B6
PRODUCTION
PUBLICATION

NEW_AGENT_FRAMEWORK
NEW_GENERAL_GATE
NEW_REGISTRY
NEW_FRESHNESS_SYSTEM
NEW_RECOVERY_SYSTEM
NEW_MATURITY_SYSTEM
NEW_TEST_CACHE
CONCURRENCY
CONTROL_OPERATIVO_RESTRUCTURE
TELEMETRY_PLATFORM
ZIP
AUTOZIP
```

No se autoriza fabricar una autorización dentro del CLI, habilitar un fallback fake fuera de tests ni promover una capability a uso productivo.

## 3. Mapa de bloques

```text
M0 — Aislamiento y baseline
M1 — Cierre técnico de Topic Belonging
M2 — Recovery administrativo del episodio
M3 — Preparación técnica pre-P2 del prompt cognitivo
M4 — Eficiencia LEAN transversal mínima
M5 — Cierre comparativo
```

Una misión autorizada puede cerrar un bloque y detenerse. El cierre de un bloque no autoriza el siguiente.

## 4. M0 — Aislamiento y baseline

Objetivo:

- preservar el estado local existente;
- trabajar en una rama propia;
- mantener `master` disponible en un worktree independiente;
- clasificar cambios M1 y cambios ajenos sin limpiar ni sobrescribir nada.

El baseline debe registrar branch, HEAD, status, archivos modificados, archivos untracked y worktrees. M0 no autoriza implementación funcional.

## 5. M1 — Cierre técnico de Topic Belonging

### Problema confirmado

La ruta actual conecta CLI, factory y workflow, pero el CLI no proporciona una `MissionAuthorization` M1 válida y el boundary parte de un modo no permitido para M1. Existe además un hueco de demostración cuando un test sustituye la factory crítica.

### Objetivo futuro

```text
entrypoint controlado
→ MissionAuthorization canónica válida
→ factory real
→ workflow real
→ fake únicamente en la frontera cognitiva
→ producer
→ reviewer independiente
→ gate
→ persistencia
→ TOPIC_BELONGING_TECHNICAL_STOP
```

La demostración debe conservar reales la aplicación, factory, workflow, storage, contratos, autorización, routing, gates y persistencia. El fake solo puede sustituir la frontera cognitiva en tests o ejecución sintética autorizada.

### Reutilización obligatoria

```text
MissionAuthorization
execution_preflight
factory actual
TopicBelongingTechnicalWorkflow
ExecutionCognitiveBoundary
persistencia actual
gate actual
```

No crear otro sistema de autorización, workflow paralelo, runtime ni cliente de modelo.

### Criterio de cierre futuro

La autorización debe seguir siendo explícita y fail-closed; no se habilita provider real, P2 ni uso productivo.

## 6. M2 — Recovery administrativo del episodio

### Problema confirmado

Un episodio puede quedar en `en_progreso` después de una interrupción o cancelación y bloquear la creación de episodios posteriores, sin existir una salida administrativa trazable.

### Dirección

```text
SEARCH EXISTING LIFECYCLE
→ reutilizar transición o mecanismo compatible
→ extender mínimamente storage/lifecycle si resulta imprescindible
```

No predeterminar estados nuevos como `ABANDONED`, `CANCELLED` o `INVALIDATED`. Si la semántica no puede reutilizarse, la misión deberá detenerse y solicitar la autoridad contractual correspondiente.

La solución futura debe conservar evidencia, razón administrativa, actor, lineage, integridad y trazabilidad. No se creará un segundo sistema de recovery.

## 7. M3 — Preparación técnica pre-P2 del prompt cognitivo

### Problema confirmado

La vertical construye `ExecutionRequest` con identidad de prompt y versión, pero la ruta de provider requiere materializar un prompt no vacío.

### Dirección

Reutilizar:

```text
prompt registry
prompt resolver/builder existente
ExecutionRequest
context resolution
providers existentes
```

Una futura prueba sintética o captura en la frontera cognitiva debe comprobar:

```text
prompt != vacío
input presente
EditorialProfile presente
policy presente
output contract presente
prompt_id y prompt_version trazables
```

Este bloque prepara la frontera técnica; no ejecuta provider real ni P2.

## 8. M4 — Eficiencia LEAN transversal mínima

M4 no reimplementa PLAN-006. Solo podrá ejecutar cambios acotados, autorizados y respaldados por consumers existentes.

### 8.1 Lectura inicial

Retirar PLAN-002 de la lectura inicial de `AGENTS.md` solo si la comprobación vigente confirma que continúa siendo una referencia superseded y la misión autoriza esa modificación documental.

### 8.2 Secuencia de assurance

Aplicar, cuando corresponda:

```text
CONVERGE
→ INDEPENDENT REVIEW
```

No eliminar el reviewer independiente. No convertir `REVERIFY` técnico en una revisión independiente implícita.

### 8.3 Testing proporcional

Usar la ladder existente:

```text
test focal
→ grupo relacionado
→ regresiones afectadas
→ suite amplia solo si aporta evidencia nueva
```

No reducir cobertura final ni crear un cache general.

### 8.4 Completion Gate

Usar `MissionCompletionGate` como validación canónica final. No modificarlo para añadir caching en esta etapa. La reutilización de evidencia solo será válida si freshness, revisión, revisión del mismo commit, dependencias y alcance son verificables.

### 8.5 Reparación y rereview

Después de una reparación:

```text
repair conjunto
→ reverify
→ focal rereview si el cambio no invalida toda la revisión
```

La capacidad técnica de focal rereview debe comprobarse antes de implementarse; no se asume que exista una interfaz nueva.

### 8.6 Medición

Cuando los datos sean observables, reutilizar las estructuras existentes para medir de forma mínima:

```text
wall time
pytest invocations
broad suite invocations
independent review invocations
review wall time
completion gate invocations
```

No crear una plataforma de telemetría.

## 9. M5 — Cierre comparativo

El cierre futuro debe comprobar, con evidencia proporcional:

### Flujo

```text
entrypoint controlado
→ M1 sintético completo
→ STOP
```

### Seguridad e integridad

- autorización fail-closed;
- ausencia de fallback fake no autorizado;
- producer y reviewer independientes;
- checksums, provenance y lineage válidos;
- persistencia y recovery M1 conservados;
- salida administrativa segura para episodios irrecuperables.

### Eficiencia

```text
menos trabajo duplicado observable
+
mismos invariantes y controles fail-closed
+
sin regresiones focales
```

Una única misión no puede afirmar por sí sola ausencia de defectos escapados longitudinales.

## 10. Criterios de STOP_LOCAL

Detener el bloque afectado cuando:

- falte autorización explícita;
- se requiera modificar una ruta fuera del scope;
- sea necesario inventar un estado o contrato funcional;
- aparezca provider real, P2 o uso productivo;
- no exista consumer verificable para una pieza propuesta;
- el estado vivo contradiga el bloque;
- la evidencia no permita distinguir una reparación material de una mejora cosmética.

## 11. Rutas previstas por futuras misiones

Las rutas dependerán de la misión concreta autorizada. La materialización de PLAN 010 por sí sola no autoriza modificar código, tests, schemas, configs, registries, agentes o skills.

## 12. Criterio de cierre de PLAN 010

PLAN 010 solo podrá cerrarse cuando:

1. cada bloque realmente ejecutado tenga autorización y evidencia;
2. M1 esté demostrado en la frontera autorizada sin provider real;
3. recovery administrativo, si se implementa, sea trazable y compatible con el lifecycle vigente;
4. la preparación de prompt no se confunda con P2;
5. las mejoras LEAN no hayan creado gates, caches, registries, autoridades o runtimes paralelos;
6. las comparaciones de eficiencia estén limitadas a datos observables;
7. el control operativo refleje el estado real sin promover uso productivo.

El plan no cambia por sí mismo:

```text
AUTHORIZED_FOR_PRODUCT_USE
P2
B5_I2_AUTHORIZED
B5_I3_AUTHORIZED
```
