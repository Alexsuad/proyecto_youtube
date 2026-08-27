# PLAN 010 — Cierre de integración M1 y eficiencia proporcional del assurance

**PLAN_ID:** `010`
**Proyecto:** YouTube — *Más Allá del Guion*
**Naturaleza:** plan técnico correctivo y acotado
**Autoridad de estado vivo:** `plans/001_CONTROL_OPERATIVO.md`
**Relación con PLAN 009:** PLAN 009 conserva la hoja de ruta progresiva; PLAN 010 propone correcciones técnicas verificadas para su integración M1 y el uso proporcional del assurance.

## 0. Estado y autorización

```text
CURRENT_MISSION: NONE
PLAN_010_STATUS: OWNER_CLOSED
PLAN_010_IMPLEMENTATION: COMPLETED
PLAN_010_ACTIVE_BLOCK: NONE
PLAN_010_M0_STATUS: COMPLETED
PLAN_010_M1_STATUS: OWNER_ACCEPTED
PLAN_010_M1_COMMIT: COMPLETED
PLAN_010_M1_PUSH: COMPLETED
PLAN_010_M1_REMOTE_BRANCH: origin/plan010/m1-integration-lean-assurance
PLAN_010_M2_M3: OWNER_ACCEPTED
PLAN_010_M4_STATUS: OWNER_ACCEPTED
PLAN_010_M5_STATUS: OWNER_ACCEPTED
PLAN_010_M4_M5: OWNER_ACCEPTED
PLAN_010_INDEPENDENT_REVIEW: PASS
PLAN_010_COMPLETION_GATE: PASS
PLAN_010_OWNER_CLOSURE: ACCEPTED
PLAN_010_M2_M3_FILE_SCOPE:
  - plans/001_CONTROL_OPERATIVO.md
  - plans/plan_010/010_CIERRE_INTEGRACION_M1_Y_EFICIENCIA_PROPORCIONAL_ASSURANCE.md
  - src/application/storage.py
  - src/application/service.py
  - src/application/topic_belonging.py
  - src/cli.py
  - src/ai/role_execution.py
  - src/core/prompt_resolver.py
  - config/agent_prompt_registry.json
  - prompts/roles/CHANNEL_INTELLIGENCE_PRODUCER/1.0.0.md
  - prompts/roles/CHANNEL_INTELLIGENCE_REVIEWER/1.0.0.md
  - tests/core/test_application_intake.py
  - tests/core/test_b4_i2_agent_prompts.py
  - tests/core/test_channel_intelligence.py
  - tests/harness/test_plan009_m1_vertical.py
  - tests/integration/test_r1_m11_integration.py
  - tests/harness/test_plan010_m2_m3.py
PLAN_010_M2_M3_TEMPORARY_SCOPE: .runtime-tmp/plan010-m2-m3/**
PLAN_010_M2_M3_SCOPE_EXTENSION:
  - src/core/mission_authorization.py
  - tests/core/test_plan_006_t1_historical_completion.py
  - tests/core/test_transversal_capability_governance.py
PLAN_010_M2_M3_SCOPE_EXTENSION_REASON: OWNER_AUTHORIZED_SCOPE_EXPANSION_TO_UPDATE_AUTHORIZATION_FIXTURES; canonical MissionAuthorization verification must bind authorization.mission_id to CURRENT_MISSION for every new execution
PLAN_010_PRE_ORIGIN_LEGACY_RESUME: FAIL_CLOSED_WITHOUT_INDEPENDENT_EVIDENCE
PLAN_010_PRE_ORIGIN_LEGACY_REASON: internal mutable markers cannot distinguish historical legacy from coordinated downgrade; no backfill or heuristic is authorized in M2_M3
PLAN_010_EPISODE_ORIGIN_TRUST_MODEL: APPLICATION_TRUSTED_PERSISTENCE
PLAN_010_EPISODE_ORIGIN_SCOPE: INTEGRITY_BINDING_AND_CONSISTENCY_DETECTION_WITHIN_APPLICATION_PERSISTENCE_BOUNDARY
PLAN_010_EPISODE_ORIGIN_LIMITATION: NOT_CRYPTOGRAPHIC_AUTHENTICITY_OR_TAMPER_PROOF_STORAGE
PLAN_010_FULL_STORAGE_REWRITE: OUT_OF_SCOPE_SECURITY_HARDENING
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

### 2.1 Trust model de provenance de episodio

Para M2+M3, `episode_origin.json` es el anchor canónico de origen dentro de la frontera de persistencia de la aplicación. Sus anchors y checksums detectan corrupción, modificaciones parciales, incoherencias entre artifacts y downgrades incompletos; no proporcionan autenticidad criptográfica ni almacenamiento tamper-proof frente a un actor que pueda reescribir coordinadamente todos los artifacts persistidos y recalcular sus hashes.

Ese escenario se clasifica como `OUT_OF_SCOPE_SECURITY_HARDENING`. Defenderlo requeriría una raíz de confianza externa —por ejemplo firma/MAC con clave externa, registro append-only, WORM, servicio remoto confiable o TPM/HSM— y no se implementa en PLAN010 M2+M3.

Los episodios pre-origin sin `episode_origin.json` y sin evidencia independiente verificable permanecen `NOT_RESUMABLE` mediante `FAIL_CLOSED`; no se autoriza backfill, migración ni heurística interna.

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

## 10.1 Cierre técnico M4+M5

M4 materializó únicamente assurance procedural y documental:

- `AGENTS.md` ya no exige leer PLAN002 en la lectura inicial; PLAN002 permanece como propuesta sin autoridad operativa en la jerarquía.
- `harness-determinista` explicita la convergencia `IMPLEMENT → VERIFY → SELF_ADVERSARIAL_REVIEW → REPAIR → REVERIFY → CONVERGED → INDEPENDENT_REVIEW`.
- `evidencia-proporcional-git` explicita la ladder `focal → relacionado → regresiones afectadas → suite amplia solo si aporta evidencia nueva`.
- No se creó skill, gate, cache, registry, runtime ni telemetría nuevos; `preparar-paquete-ejecucion-tecnica` no fue modificado porque SEARCH no demostró un consumer directo que evitara duplicación.

M5 reutilizó las superficies existentes. Evidencia ejecutada:

```text
PLAN009 M1 vertical:                         54 passed
PLAN010 M2+M3 completo:                       35 passed
authorization/integrity:                     39 passed, 1 skipped
integration completa:                        7 passed
```

Comandos exactos de la evidencia focal (intérprete `python`, exit code `0`):

```text
python -m pytest -q tests/harness/test_plan009_m1_vertical.py
python -m pytest -q tests/core/test_transversal_capability_governance.py tests/core/test_plan_006_t1_historical_completion.py
python -m pytest -q tests/harness/test_plan010_m2_m3.py
python -m pytest -q tests/integration/test_r1_m11_integration.py
python -m compileall -q src tests
git diff --check
```

Los dos tests que fijaban `CURRENT_MISSION` a M2+M3 fueron corregidos para comprobar la autoridad viva y la propiedad estable de no promoción, respectivamente. La aceptación positiva de autorización para la misión vigente queda ahora `DEMONSTRATED`; no se modificó código productivo. El resto del entrypoint/factory/workflow M1 sintético, la separación producer–reviewer, persistencia, recovery, provenance, lineage, `episode_origin`, autorización fail-closed, provider real `NO`, P2 y uso productivo no autorizado permanecen demostrados por las superficies existentes.

Medición proporcional observable:

```text
M4+M5 technical-cycle pytest invocations: 16
broad suite invocations actuales:     0
independent review invocations:        8 (previous cycle, superseded by Owner repair)
MissionCompletionGate invocations:    11 (9 previous cycle attempts, 1 Owner-repair PASS superseded, 1 final PASS)
comparación histórica M2+M3:          NOT_COMPARABLE (session-ses_fd11.md ausente)
```

Resultado técnico previo: `NO MATERIAL REGRESSION FOUND WITHIN EXECUTED EVIDENCE`, con `CURRENT_MISSION_ACCEPTANCE_COVERAGE = DEMONSTRATED`; queda superseded por la reparación Owner focal.

La revisión independiente focal de la reparación fue `PASS`. El `MissionCompletionGate` canónico de la reparación fue `PASS` con `violations = []`; su evidencia se conserva en `.runtime-tmp/plan010-m4-m5/gates-owner-repair-final/gates/PLAN010_M4_M5_LEAN_ASSURANCE_AND_COMPARATIVE_CLOSURE/MISSION_COMPLETION.json`. No se afirma reducción porcentual, ausencia longitudinal de defectos, readiness ni autorización de uso productivo.

## 10.2 Reparación focal de cierre Owner

La revisión Owner detectó que `CURRENT_MISSION: NONE` podía coincidir con `authorization.mission_id: NONE` y alcanzar una nueva ejecución sintética. La reparación focal, sin cambiar la autoridad ni crear una ruta paralela, añade en `src/core/mission_authorization.py` el rechazo canónico `NO_ACTIVE_CURRENT_MISSION` antes de aceptar una misión coincidente con el sentinel inactivo.

Pruebas añadidas dentro del scope autorizado:

- core: artifacts válidos con `CURRENT_MISSION: NONE` y `mission_id: NONE` son rechazados;
- vertical Topic Belonging: la ejecución sintética es rechazada y no materializa el directorio de episodios;
- el caso de misión concreta coincidente y el caso mismatch continúan cubiertos.

La reparación no cambia el `CURRENT_MISSION` vivo, mantiene `PLAN_010_STATUS: IN_PROGRESS`, `PLAN_010_ACTIVE_BLOCK: NONE`, M4/M5 y M4+M5 pendientes de Owner, y deja la comparación histórica como `NOT_COMPARABLE`.

Medición reconciliada:

```text
M4+M5 technical-cycle pytest invocations: 16
Owner closure repair pytest invocations:    7 (6 PASS, 1 construcción inicial corregida)
Owner closure repair final M2+M3:            36 passed
Owner closure repair final core group:       40 passed, 1 skipped
Owner closure repair final M1:               54 passed
Owner closure repair final integration:       7 passed
Owner closure repair reviewer attempts:      2 (1 scope clarification, 1 PASS)
```

Comandos finales de la reparación Owner:

```text
python -m pytest -q tests/core/test_transversal_capability_governance.py tests/core/test_plan_006_t1_historical_completion.py
python -m pytest -q tests/harness/test_plan010_m2_m3.py
python -m pytest -q tests/harness/test_plan009_m1_vertical.py
python -m pytest -q tests/integration/test_r1_m11_integration.py
python -m compileall -q src tests
git diff --check
```

La evidencia previa de reviewer y `MissionCompletionGate` queda conservada como historial técnico; la revisión focal y el gate de la reparación fueron completados antes del cierre Owner.

## 10.3 Cierre administrativo Owner

El Owner aceptó M4, M5 y el conjunto M4+M5. Antes de cambiar `CURRENT_MISSION` a `NONE`, el caso límite fue verificado como `CURRENT_MISSION: NONE → NO_ACTIVE_CURRENT_MISSION → fail-closed`; la transición administrativa no reabre desarrollo ni autoriza provider real, P2 o uso productivo.

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
