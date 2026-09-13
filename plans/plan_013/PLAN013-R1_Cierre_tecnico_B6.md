# PLAN013-R1 — Cierre técnico de B6

**Proyecto:** Proyecto YouTube — Más Allá del Guion<br>
**Plan padre:** PLAN013 — Remediación E2E post-auditoría general<br>
**Tipo:** Subplan correctivo subordinado a PLAN013<br>
**Ubicación prevista:** `plans/plan_013/PLAN013-R1_Cierre_tecnico_B6.md`<br>
**Estado inicial:** `READY_FOR_INTEGRATED_EXECUTION`<br>
**Autoridad:** OWNER + `plans/001_CONTROL_OPERATIVO.md`<br>
**Alcance:** técnico sintético; no autoriza IA REAL ni uso productivo<br>
**Modelo de ejecución:** `INTEGRATED_PLAN_EXECUTION`<br>

---

## 1. Propósito

Cerrar de forma controlada los bloqueos técnicos restantes de `PLAN013_B6_GATE` detectados tras la remediación principal y la auditoría focal posterior.

Este documento **no crea un nuevo plan rector**. Es un subplan correctivo de PLAN013 y existe únicamente para ordenar cinco frentes técnicos relacionados que comparten un mismo objetivo de salida:

```text
PLAN013_B6_GATE: PASS
PLAN013_TECHNICAL_PASS: PASS
```

El cierre de este subplan **no autoriza** por sí mismo:

- IA REAL;
- uso productivo;
- reanudación de EXTEND-01;
- cierre OWNER de PLAN013;
- push;
- activación de proveedores.

---

## 2. Estado de entrada

Estado operativo esperado al comenzar:

```text
CURRENT_RECOVERY_PLAN: PLAN013
CURRENT_MISSION: PLAN013_INTEGRATED_EXECUTION
PLAN013_STATUS: IN_PROGRESS
PLAN013_B6_GATE: BLOCKED
PLAN013_TECHNICAL_PASS: BLOCKED_PENDING_B6
NEXT_ALLOWED_ACTION: RESOLVE_PLAN013_B6_BLOCKERS

REAL_AI_EXECUTION: NO
PRODUCT_USE_AUTHORIZED: NO
EXTEND_01_STATUS: SUSPENDED_BY_PLAN013
```

Hallazgos relevantes en el estado actual:

### 2.1 PROD01-R2-F002 — lineage B3

Existe una contradicción material entre tres checksums asociados a la misma fuente B3:

- `config/editorial_profile_registry.json`
- `profiles/voice/corpus_manifest.json`
- `docs/specifications/B3_editorial_profile_functional_specification.md`

La validación actual detecta inconsistencias internas dentro de un payload, pero no demuestra todavía una reconciliación física y cross-registry completa.

**Estado esperado de entrada:** `PARTIALLY_RESOLVED`.

### 2.2 PROD02-R2-F003 — adquisición externa

Existe `SoftwareAcquisitionAdapter` y capacidad sintética de materialización/gobernanza de bindings, provenance y estados.

No está demostrada todavía una capacidad general canónica:

```text
Search / Discovery
→ Fetch / Acquisition
→ Verify
→ Source Registry
```

ni una limitación de alcance canónica suficientemente explícita que cierre el finding.

**Estado esperado de entrada:** `PARTIALLY_RESOLVED`.

### 2.3 PLAN012/M7 — seis fallos stale

Los seis fallos conocidos comparten:

```text
MISSION_STALE_AGAINST_LIVE_STATE
```

Los fixtures intentan ejecutar un flujo histórico EXTEND suspendido contra una autoridad viva que exige PLAN013.

El guard se considera correcto; el problema es el aislamiento de los tests históricos.

La disposición vigente de `PROD01-R2-F003` es
`DEFERRED_WITH_EVIDENCE`. La implementación y las pruebas del motor de
invalidación selectiva no demuestran todavía un consumidor productivo real;
esta observación no se convierte en `RESOLVED` ni se reinterpreta como un
bloqueador adicional de B6 durante R1.

### 2.4 Hybrid runtime — once fallos

Estado conocido:

```text
37 passed
11 failed
```

La hipótesis principal es que fixtures y expectativas legacy todavía entregan o esperan metadata técnica que el contrato actual asigna a Software.

No se autoriza relajar el contrato para hacer pasar tests.

### 2.5 B6

B6 debe permanecer `BLOCKED` hasta que:

- los findings materiales relevantes estén reconciliados;
- los tests stale estén correctamente aislados;
- hybrid runtime esté verde;
- la suite completa esté verde;
- la evidencia documental esté alineada con el estado real.

### 2.6 Decisión del OWNER y preparación documental

La decisión del OWNER para el Frente B es `VIA_A_AUTHORIZED`. La autorización se limita a
materializar y demostrar sintéticamente una capacidad neutral y agnóstica de
proveedor:

```text
Search / Discovery
→ Fetch / Acquisition
→ Verify
→ Source Registry
```

Esta decisión no autoriza Internet REAL, provider REAL, IA REAL ni selección de
un proveedor o API concreta. La capacidad debe incluir la rama negativa:

```text
capacidad no disponible
→ UNAVAILABLE
→ fail-closed
→ no fabricar evidencia
```

El estado documental que debe preservarse durante PLAN013-R1 es:

```text
PLAN013_STATUS: IN_PROGRESS
PLAN013_B6_GATE: BLOCKED
PLAN013_TECHNICAL_PASS: BLOCKED_PENDING_B6
REAL_AI_EXECUTION: NO
PRODUCT_USE_AUTHORIZED: NO
EXTEND_01_STATUS: SUSPENDED_BY_PLAN013
```

La cadena operativa de autoridad para esta ejecución es:

```text
PLAN013
→ PLAN013-R1
→ EJECUCIÓN INTEGRADA AUTORIZADA
```

La aprobación de este plan autoriza a OpenCode a ejecutar el plan completo de
extremo a extremo. Los cinco frentes siguientes son una descomposición interna,
no unidades independientes de autorización. OpenCode decide autónomamente la
secuencia local, iteraciones, paralelización segura, uso de subagentes y retorno
a un frente anterior cuando la integración lo requiera. Los checkpoints técnicos
no crean nuevas autorizaciones y no se requiere revisión del OWNER entre frentes.

La reparación técnica de las representaciones de lineage B3 está dentro del
alcance autorizado. Puede actualizar una representación normalmente protegida
si no cambia el contenido funcional/editorial aprobado y si conserva evidencia
before/after, versionado, checksum y validación de activación. Solo se detiene
si la solución exige cambiar una decisión funcional, editorial o arquitectónica.

---

# 3. Principios de ejecución

1. **Search before create.**
2. **Reuse → Extend → Create.**
3. No crear arquitectura nueva si una corrección focal resuelve el problema.
4. No modificar el contenido o la aprobación del perfil editorial activo para
   hacer pasar pruebas; las representaciones técnicas de lineage B3 se rigen
   por la autorización específica del Frente A.
5. No inventar checksums, provenance, identidades ni estados.
6. No reinterpretar findings para hacer verde B6.
7. No usar IA REAL ni providers reales.
8. No autorizar producto.
9. No reabrir PLAN012.
10. No reactivar EXTEND-01.
11. No commit ni push durante este plan salvo autorización expresa posterior del OWNER.
12. La ejecución integrada continúa autónomamente mientras permanezca dentro del alcance autorizado.
13. La auditoría independiente final ocurre **después** de B6 PASS, no antes.

---

# 4. Estructura del subplan

```text
PLAN013-R1
│
├── Frente A — Reconciliación lineage B3 / PROD01-R2-F002
│
├── Frente B — Cierre de adquisición / PROD02-R2-F003
│
├── Frente C — Aislamiento de tests stale PLAN012/M7
│
├── Frente D — Corrección Hybrid Runtime
│
└── Frente E — Revalidación completa y cierre B6
        ↓
   PLAN013_B6_GATE: PASS
        ↓
   PLAN013_TECHNICAL_PASS: PASS
        ↓
   Auditoría independiente
```

Los frentes se ejecutan en el orden técnicamente conveniente. OpenCode puede
reordenarlos, iterarlos o paralelizarlos cuando la evidencia lo justifique sin
crear una autorización adicional.

---

## 4.1 Modelo de ejecución integrada

La unidad canónica de autorización es este documento:

```text
plans/plan_013/PLAN013-R1_Cierre_tecnico_B6.md
```

Los frentes A–E no son misiones independientes y no requieren, individualmente,
artefactos de contrato, autorización o gate, checksum de contrato,
`CURRENT_MISSION` separado ni aprobación del OWNER. No se crean autoridades
nuevas por frente.

Si el harness necesita una representación machine-readable, podrá existir como
máximo una representación vinculada al PLAN013-R1 completo. Esta adaptación no
rediseña el harness ni duplica el contenido del plan.

Durante la ejecución integrada, el estado vivo identifica PLAN013 como recovery
plan y PLAN013-R1 como la autoridad técnica en uso; no se cambia
`CURRENT_MISSION` entre frentes. OpenCode controla internamente la
descomposición, las pruebas intermedias, los subagentes, las iteraciones y la
estrategia de convergencia.

---

# 5. Frente A — Reconciliación lineage B3 / PROD01-R2-F002

## Objetivo

Resolver de forma verificable la contradicción de identidad/checksum B3 entre registry, corpus y archivo físico.

## Trabajo requerido

1. Identificar la fuente canónica real de B3.
2. Verificar:
   - `source_id`;
   - `locator`;
   - versión;
   - checksum;
   - pointer activo;
   - registry;
   - corpus manifest;
   - archivo físico.
3. Distinguir en la evidencia tres clases de checksum:
   - checksum declarado de lineage de una fuente;
   - checksum físico de la propia fuente;
   - checksum físico de un manifest o registry que contiene declaraciones.
4. Registrar como evidencia de entrada, sin tratarlos como hashes del mismo
   objeto:

   | Evidencia | Valor observado | Significado |
   |---|---|---|
   | `config/editorial_profile_registry.json` → lineage B3 | `73618cbe03da6ab3837f669e431fc7c7b21e7e698a9eb5a8d8b8ce32f0ddc8f1` | checksum de lineage declarado para la especificación B3 |
   | `profiles/voice/corpus_manifest.json` → lineage B3 | `c2108e34fa5113e22c01dc70888e8e510eede12c7b54ccff76bd810045a6aadc` | checksum de lineage declarado para la especificación B3 |
   | `docs/specifications/B3_editorial_profile_functional_specification.md` | `899478a6b5be428bca3b8038c3878225f26ae6107aef4f911e69cfe45440265d` | SHA-256 físico actual de la fuente B3 |
   | `profiles/voice/corpus_manifest.json` | `bf8288ac9dd9db2d5010a7df40caf55656cb802c3d0b8b5858e433cbe9b47aa9` | SHA-256 físico del manifest, no de la especificación B3 |

5. Recalcular los hashes físicos con un mecanismo reproducible Linux/WSL, como:

   ```bash
   sha256sum docs/specifications/B3_editorial_profile_functional_specification.md
   sha256sum profiles/voice/corpus_manifest.json
   ```

6. Reconciliar las representaciones mediante la relación:

   ```text
   registry ↔ corpus ↔ fuente física
   ```

   La comparación debe respetar el objeto al que pertenece cada hash y no puede
   comparar el hash físico de un manifest o registry como si fuera el checksum
   de la fuente B3.
7. Añadir o extender una validación cross-registry/física que falle cuando:
   - misma identidad durable;
   - misma versión;
   - checksum incompatible.
8. Preservar versiones históricas válidas mediante identidad/versionado explícito, no por sobrescritura silenciosa.

## No hacer

- No fabricar hashes.
- No cambiar contenido funcional de B3 para hacer coincidir un checksum.
- Se autoriza modificar técnicamente las representaciones de lineage protegidas
  cuando sea necesario para restaurar la identidad B3, siempre que no cambie el
  contenido funcional/editorial aprobado y se registren checksums before/after,
  binding de versión y validación de activación.
- No declarar `RESOLVED` solo porque la validación interna de payload pase.

## Criterio de salida

`PROD01-R2-F002` puede pasar a `RESOLVED` únicamente si:

- existe una única identidad verificable por versión;
- registry, corpus y fuente física son coherentes;
- el checksum está calculado sobre la fuente correcta;
- existe regresión cross-registry/física;
- no queda contradicción silenciosa.

## Evidencia mínima

- tests focales lineage;
- validación del archivo físico;
- `git diff --check`.

---

# 6. Frente B — Cierre de adquisición / PROD02-R2-F003

## Objetivo

Cerrar de manera explícita y verificable el finding de adquisición externa sin sobredeclarar capacidades.

## Decisión del OWNER

El Frente B queda autorizado por `VIA_A_AUTHORIZED`. El frente debe materializar una
capacidad neutral sintética y mantener explícitamente su rama `UNAVAILABLE`.
La decisión no vuelve a elevarse al OWNER durante la ejecución salvo que aparezca
una contradicción funcional o arquitectónica material.

La implementación no puede quedar acoplada a ChatGPT, Codex, OpenCode, web.run,
un proveedor concreto ni una API específica.

## Garantía de adquisición

El frente debe cerrar el finding mediante la capacidad neutral autorizada,
manteniendo la limitación `UNAVAILABLE` como rama negativa obligatoria:

### Vía A — Capacidad neutral materializada

Demostrar una ruta canónica, agnóstica de proveedor:

```text
Search / Discovery
→ Fetch / Acquisition
→ Verify
→ Source Registry
```

conservando como mínimo:

- `source_id`;
- `locator`;
- método de adquisición;
- `retrieval_status`;
- `evidence_status`;
- provenance;
- error;
- checksum cuando aplique.

### Rama negativa `UNAVAILABLE`

Cuando una capacidad no esté disponible:

- declararlo explícitamente;
- definir `UNAVAILABLE` o equivalente cuando la capacidad no exista;
- impedir que el sistema fabrique evidencia;
- permitir continuar únicamente en el alcance que no dependa de material no adquirido;
- registrar la limitación en la autoridad funcional/técnica adecuada.

## No hacer

- No ejecutar Internet real.
- No ejecutar provider real.
- No ejecutar IA real.
- No simular una búsqueda externa y declararla real.
- No llamar “Search→Fetch→Verify” a un adapter que solo recibe bindings ya preparados.
- No crear una integración de proveedor específica.

## Criterio de salida

`PROD02-R2-F003` puede pasar a `RESOLVED` únicamente si:

- existe una capacidad neutral demostrada con su rama `UNAVAILABLE` explícita y
  fail-closed compatible con PLAN013.

## Evidencia mínima

- pruebas positivas sintéticas;
- pruebas de `UNAVAILABLE`;
- fallo de adquisición preservando provenance/error;
- ausencia de evidencia fabricada;
- `git diff --check`.

---

# 7. Frente C — Aislamiento de tests stale PLAN012/M7

## Objetivo

Corregir los seis tests históricos que fallan por depender de la autoridad viva actual.

## Diagnóstico aceptado

Los seis fallos comparten:

```text
MISSION_STALE_AGAINST_LIVE_STATE
```

El guard no debe relajarse.

## Trabajo requerido

1. Identificar los seis tests exactos.
   La identidad durable debe registrarse por nombre, no solo por línea:
   - `test_extend01_b4_prepares_external_handoff_and_stops_before_b2`
   - `test_extend01_b4_r1_imports_research_planning_and_resumes_without_replanning`
   - `test_extend01_verified_external_provenance_reenters_resume_context`
   - `test_extend01_b4_r3_imports_consecutive_cognitive_seams_without_repeating_b2`
   - `test_extend01_b4_r1_rejects_tampered_execution_controls`
   - `test_extend01_b4_r5_integrated_external_roundtrip_m4_m6`
   Todos pertenecen a `tests/harness/test_plan012_m7_b5.py` y deben conservar el
   comportamiento fail-closed `MISSION_STALE_AGAINST_LIVE_STATE` contra la
   autoridad viva.
2. Preservar el comportamiento fail-closed de la autoridad viva.
3. Construir autoridad de test aislada en fixture/repositorio temporal para el flujo histórico EXTEND correspondiente.
4. Evitar que tests históricos dependan de:
   - `CURRENT_MISSION` vivo;
   - PLAN013 activo;
   - estado global mutable del repositorio real.
5. Mantener la intención original de esos tests.

## No hacer

- No cambiar `plans/001_CONTROL_OPERATIVO.md` para hacer pasar tests.
- No reactivar EXTEND-01.
- No deshabilitar el guard.
- No reemplazar el comportamiento histórico esperado por un simple skip si el test puede aislarse correctamente.

## Criterio de salida

Los seis tests deben pasar utilizando autoridad aislada y el guard debe seguir rechazando una ejecución stale contra la autoridad viva.

## Evidencia mínima

- seis casos previamente fallidos → PASS;
- regresión explícita del guard vivo → PASS;
- `git diff --check`.

---

# 8. Frente D — Corrección Hybrid Runtime

## Objetivo

Resolver los 11 fallos de `tests/ai/test_hybrid_runtime.py` alineando fixtures y expectativas con el contrato actual, sin debilitar la autoridad de Software.

## Contrato de referencia

Software conserva autoridad sobre metadata técnica, incluyendo cuando aplique:

- IDs;
- run IDs;
- checksums;
- provider/model provenance;
- timestamps;
- artifact references;
- profile bindings;
- estados técnicos.

La IA/proveedor no debe fabricar ni controlar esos campos.

## Trabajo requerido

1. Ejecutar el archivo focal completo.
2. Agrupar los 11 fallos por causa raíz.
3. Usar como hipótesis inicial, sujeta a confirmación durante el Frente D:
   - **Grupo A:** 8 fallos relacionados con metadata técnica software-owned y
     `EDITORIAL_RUNTIME_FIELDS`.
   - **Grupo B:** 3 fallos relacionados con payload semántico incompleto,
     incluido `b5_i2_semantic_sufficiency_audit.json`.
4. Confirmar o refutar la agrupación mediante reproducción y evidencia de causa.
5. Para cada grupo determinar:
   - fixture legacy;
   - expectativa legacy;
   - payload incompleto real;
   - defecto del runtime.
6. Corregir preferentemente fixtures/expectativas cuando el contrato actual sea inequívoco.
7. Corregir runtime solo si existe un defecto real demostrado.
8. Preservar fail-closed cuando el proveedor intente suministrar metadata software-owned.

## No hacer

- No aceptar metadata técnica del proveedor para hacer pasar tests.
- No degradar validaciones.
- No eliminar controles de integridad.
- No cambiar el contrato actual sin contradicción técnica demostrada.
- No convertir rechazo correcto en overwrite silencioso.

## Criterio de salida

```text
tests/ai/test_hybrid_runtime.py
48 passed
0 failed
```

y las pruebas deben confirmar explícitamente que la metadata técnica sigue siendo software-owned.

## Evidencia mínima

- hybrid runtime completo;
- suites directamente afectadas;
- `git diff --check`.

---

# 9. Frente E — Revalidación completa y cierre B6

## Objetivo

Demostrar que PLAN013 está técnicamente listo para pasar a auditoría independiente.

## Precondiciones

Los frentes A–D deben tener evidencia suficiente para la convergencia, sin
requerir una autorización o gate independiente entre ellos.

## Trabajo requerido

1. Reconciliar:
   - `findings_manifest.json`;
   - `traceability_matrix.md`;
   - `CP-01.md`;
   - `PLAN013_B6_GATE.md`;
   - `PLAN013_TECHNICAL_PASS.md`.
2. Confirmar que documentos históricos no se presentan como autoridad viva.
3. Ejecutar validaciones focales relevantes.
4. Ejecutar suite completa.
5. Si la suite monolítica excede timeout:
   - obtener primero la colección completa mediante `python -m pytest --collect-only -q`;
   - registrar todos los node IDs de la colección;
   - formar particiones deterministas, disjuntas y reproducibles;
   - demostrar que la unión exacta de las particiones cubre el 100 % de la
     colección, sin omisiones silenciosas;
   - ejecutar todas las particiones.
6. Confirmar `git diff --check`.
7. Verificar que no se ejecutó IA REAL ni uso productivo.

## Criterio B6

B6 solo puede pasar si:

- todos los BLOCKER están cerrados;
- findings restantes tienen disposición explícita y compatible con PLAN013;
- CP-01 cumple su criterio;
- CP-02 cumple su criterio;
- CP-03 cumple su criterio;
- E2E sintético pasa;
- hybrid runtime pasa;
- suite completa pasa;
- no hay contradicción documental material;
- `git diff --check` pasa.

## Salida esperada

Solo si todo lo anterior es verdadero:

```text
PLAN013_B6_GATE: PASS
PLAN013_TECHNICAL_PASS: PASS
PLAN013_STATUS: READY_FOR_FINAL_INDEPENDENT_AUDIT
```

Si falla cualquier criterio:

```text
PLAN013_B6_GATE: BLOCKED
PLAN013_TECHNICAL_PASS: BLOCKED_PENDING_B6
PLAN013_STATUS: IN_PROGRESS
```

No se permite un PASS parcial.

---

# 10. Housekeeping no bloqueante

Los siguientes elementos están identificados pero no forman parte del camino crítico de los frentes A–D salvo que interfieran con B6:

- duplicados byte-a-byte de `00E` / `00F`;
- `source_export_status.md` como snapshot histórico;
- residuos `handoff/RUN-AI-*.json` de PLAN009 sintético.

Regla:

- no mezclar su limpieza con los frentes técnicos anteriores;
- tratarlos únicamente en el Frente E si afectan claridad/autoridad/evidencia de B6;
- no borrar nada sin verificar referencias activas;
- preferir clasificación histórica antes que limpieza destructiva.

---

# 11. Stop conditions

La ejecución integrada continúa autónomamente cuando el problema técnico está
dentro del objetivo autorizado. OpenCode puede corregir código dentro del
alcance, modificar representaciones derivadas, reconciliar lineage, ajustar
tests y fixtures legacy, cambiar de estrategia, volver a un frente anterior,
modificar varios módulos o usar subagentes sin detenerse por ello.

Detener la ejecución y devolver control al OWNER únicamente si aparece alguna
de estas fronteras reales:

1. Cambia el objetivo de PLAN013-R1.
2. Se requiere una ampliación material del alcance autorizado.
3. Se requiere cambiar una decisión funcional o editorial no autorizada.
4. Se requiere un cambio arquitectónico material no cubierto por el plan.
5. Se requiere IA REAL, Internet REAL o provider REAL.
6. Existe riesgo de pérdida de datos o destrucción de evidencia.
7. Aparece una contradicción entre autoridades canónicas que no puede resolverse aplicando la jerarquía existente.

---

# 12. Auditoría posterior

La auditoría independiente final **no forma parte de PLAN013-R1**.

PLAN013-R1 termina cuando B6 y Technical Pass están verdes.

Después:

```text
PLAN013_B6_GATE: PASS
        ↓
PLAN013_TECHNICAL_PASS: PASS
        ↓
Auditoría independiente de la implementación corregida
        ↓
PASS / FAIL
```

La auditoría debe revisar especialmente:

- los 16 findings originales;
- los defectos encontrados en la primera auditoría independiente;
- CP-01 / CP-02 / CP-03;
- E2E completo;
- lineage e identidad;
- independencia de roles;
- cierre e invalidación;
- evidencia B6;
- ausencia de sobredeclaraciones.

---

# 13. Cierre del subplan

PLAN013-R1 puede considerarse técnicamente completado cuando:

```text
Frente A: PASS
Frente B: PASS
Frente C: PASS
Frente D: PASS
Frente E: PASS

PLAN013_B6_GATE: PASS
PLAN013_TECHNICAL_PASS: PASS
```

Eso habilita únicamente:

```text
NEXT_ALLOWED_ACTION: REQUEST_PLAN013_FINAL_INDEPENDENT_AUDIT
```

No habilita:

```text
REAL_AI_EXECUTION
PRODUCT_USE
EXTEND_01_RESUMPTION
PLAN013_OWNER_CLOSURE
```

Esas decisiones permanecen fuera del alcance de este subplan y requieren sus propias autoridades posteriores.
