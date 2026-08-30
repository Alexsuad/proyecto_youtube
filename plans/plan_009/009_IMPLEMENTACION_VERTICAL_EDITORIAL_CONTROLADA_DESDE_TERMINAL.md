# PLAN 009 — IMPLEMENTACIÓN PROGRESIVA DE LA VERTICAL EDITORIAL CONTROLADA DESDE TERMINAL

**PLAN_ID:** `009`  
**Ruta canónica:** `plans/plan_009/009_IMPLEMENTACION_VERTICAL_EDITORIAL_CONTROLADA_DESDE_TERMINAL.md`  
**Proyecto:** YouTube — _Más Allá del Guion_  
**Fecha:** 2026-08-22  
**Naturaleza:** plan de implementación progresiva  
**Estado documental:** hoja de ruta; el estado vivo se resuelve exclusivamente en `plans/001_CONTROL_OPERATIVO.md`
**Autorización operativa por este documento:** `NO`  
**Autoridad de estado vivo:** `plans/001_CONTROL_OPERATIVO.md`

## Registro histórico de cierre de la misión correctiva

`PLAN009_P2_CORRECTIVE_RUNTIME_NEUTRALITY` queda cerrada administrativamente
después de la evidencia técnica aprobada y de la revisión independiente del
OWNER sobre `proyecto_youtube_2026-08-30_10-26-27.zip`:

```text
TECHNICAL_IMPLEMENTATION: PASS
MissionCompletionGate: PASS
INDEPENDENT_OWNER_REVIEW: PASS
CORRECTIVE_MISSION: CLOSED
mission_contract_sha256: e0976e48247a61adf39a2c63b12c2e190d5590ee2b3a6b977d5d95fa12d30d8c
```

Este registro es histórico y no constituye `P2_PASS`,
`REAL_COGNITIVE_EXECUTION`, `PRODUCT_READY` ni autorización de uso
productivo. P2 real permanece sin ejecutar y su roundtrip requiere una
misión independiente de integración con autorización expresa del OWNER.

## Registro histórico de cierre de la integración técnica P2

La misión `PLAN009_P2_ROUNDTRIP_INTEGRATION` queda cerrada tras la
implementación técnica aprobada y la revisión independiente del OWNER.

```text
PLAN009_P2_ROUNDTRIP_INTEGRATION: CLOSED
TECHNICAL_IMPLEMENTATION: PASS
INDEPENDENT_OWNER_REVIEW: PASS
P2_TECHNICAL_INFRASTRUCTURE: READY
P2_REAL_EXECUTION: NOT_EXECUTED
REAL_COGNITIVE_EXECUTION: NOT_DEMONSTRATED
AUTHORIZED_FOR_PRODUCT_USE: NO
NEXT_STEP: OWNER_AUTHORIZATION_REQUIRED_FOR_P2_REAL_EXECUTION
```

Este cierre es exclusivamente técnico y documental. No equivale a `P2_PASS`,
no ejecuta cognición real, no autoriza uso productivo y no sustituye la
autorización OWNER separada necesaria para una futura ejecución P2 real.

---

# 0. Propósito

PLAN 009 define **cómo llevar la aplicación desde la entrada por terminal hasta las primeras ejecuciones editoriales reales**, de forma incremental, trazable y fail-closed.

No redefine los criterios funcionales de PLAN 001 ni sustituye la autoridad operativa viva.

La progresión prevista es:

```text
Terminal
→ input humano
→ primera capability cognitiva
→ revisión independiente
→ gate
→ persistencia
→ investigación controlada
→ evidencia y tesis
→ arquitectura editorial
→ guion controlado
```

Cada tramo se implementa y prueba por separado.

**Una fase aprobada no autoriza automáticamente la siguiente.**

---

# 1. Relación con las sedes canónicas

## 1.1 Autoridad operativa

`plans/001_CONTROL_OPERATIVO.md` es la única sede que puede declarar:

- misión vigente;
- autorización de ejecución;
- scope operativo;
- fase abierta o bloqueada;
- autorización de provider;
- autorización de uso productivo.

PLAN 009 únicamente describe la hoja de ruta de implementación.

La integración técnica de roundtrip P2 es una misión independiente y no
equivale a ejecutar cognición real. Su ruta canónica conserva el control en
Proyecto YouTube y permite el ciclo persistido:

```text
HANDOFF_PREPARED
→ PENDING_EXTERNAL_RESULT
→ import_result
→ VALIDATED
→ PERSISTED
→ resume
```

El mismo resultado importado es idempotente; un resultado distinto para una
etapa cerrada se bloquea. El estado y el resultado original se conservan en
el almacenamiento del episodio para que un proceso nuevo pueda reanudar sin
memoria de proceso. `AGENT_HARNESS` sigue siendo neutral: el propietario
selecciona externamente el harness y el modelo. Esta infraestructura no
declara `REAL_COGNITIVE_EXECUTION`, no activa P2 real ni autoriza uso
productivo; la misión de integración técnica queda cerrada, pero para la
ejecución P2 real se requiere una autorización OWNER separada.

Si existe contradicción:

```text
001_CONTROL_OPERATIVO
> PLAN 009
```

y se aplica `STOP_LOCAL` al tramo afectado.

## 1.2 Autoridad funcional

Los requisitos editoriales, gates funcionales, contratos y criterios de cada fase siguen en PLAN 001 y sus documentos canónicos.

PLAN 009 **no duplica** esos requisitos.

Cuando una fase necesite detalles funcionales, debe consultar su sede canónica vigente.

## 1.3 Regla de no duplicación

Este plan conserva únicamente:

- secuencia de implementación;
- límites;
- dependencias;
- criterios técnicos de entrada/salida;
- STOP_LOCAL;
- estrategia de pruebas;
- relación entre fases.

No debe copiar extensamente gates, schemas o decisiones funcionales que ya tengan sede canónica.

---

# 2. Objetivo operativo

El objetivo inmediato es demostrar primero:

```text
python -m src.cli iniciar
→ HumanInput
→ EditorialIntakeHandoff
→ TOPIC_BELONGING_ASSESSMENT
→ reviewer independiente
→ gate
→ persistencia
→ STOP
```

Después, y solo con nueva autorización expresa, avanzar progresivamente hacia investigación y guion.

---

# 3. Principios obligatorios

## 3.1 Menos es más

Antes de crear:

```text
SEARCH BEFORE CREATE
REUSE BEFORE REIMPLEMENT
```

No crear salvo necesidad demostrada:

- otro runtime;
- otro sistema de autorización;
- otro registry;
- otro storage;
- otro lifecycle;
- otro gate equivalente;
- otro workflow paralelo;
- abstracciones genéricas para una sola necesidad.

## 3.2 IA para criterio; código para invariantes

```text
runtime cognitivo
→ análisis, investigación, síntesis, redacción

lógica determinista
→ autorización, schemas, routing, checksums,
  persistencia, lifecycle, provenance, gates estructurales
```

## 3.3 No fabricar editorial

La aplicación no puede inventar valores para satisfacer contratos.

Si un campo requerido no proviene de:

```text
usuario
derivación determinista válida
artefacto canónico
capability cognitiva autorizada
```

se aplica `STOP_LOCAL`.

## 3.4 Neutralidad

No introducir en producto:

- nombres de chats;
- numeraciones de equipos humanos;
- nombres de herramientas de desarrollo como autoridad funcional;
- coordinación externa del cliente.

## 3.5 Datos editoriales fuera del repositorio

Tema, pregunta, investigación, obras, dossiers, claims, tesis y guion pertenecen al almacenamiento editorial del episodio.

No deben hardcodearse en PLAN 009 ni en configuración del producto.

## 3.6 Fakes

Fake/mock únicamente en tests y exclusivamente en la frontera cognitiva.

Nunca:

```text
provider real ausente
→ fallback automático a fake
```

---

# 4. Estado de partida

Antes de ejecutar cualquier fase, verificar el estado vivo.

PLAN 009 nace con la expectativa de que:

```text
R1_GATE: PASS
R1_EXECUTION: COMPLETED
R2_CONTROLLED_EXECUTION: AUTHORIZED
R2_SCOPE: B5_I1_CONTROLLED_EXECUTION
AUTHORIZED_FOR_PRODUCT_USE: NO
B5_I2_AUTHORIZED: NO
B5_I3_AUTHORIZED: NO
B5_5_AUTHORIZED: NO
B6_AUTHORIZED: NO
```

Estos valores no se asumen: se leen del control operativo vigente.

---

# 5. Mapa de fases

```text
P0 — Base segura previa
P1 — Vertical técnica Topic Belonging
P2 — Primera ejecución cognitiva real
P3 — B5-I1 por incrementos
P4 — B5-I2, solo si se autoriza
P5 — B5-I3, solo si se autoriza
P6 — B5.5, solo si se autoriza
P7 — B6, solo si se autoriza
```

Regla global:

```text
cerrar fase
→ auditoría independiente
→ actualizar estado vivo
→ solicitar autorización de siguiente misión
→ solo entonces continuar
```

---

# 6. P0 — BASE SEGURA PREVIA

**Estado:** `IN_PROGRESS_OR_PENDING_AUDIT` hasta que `001_CONTROL_OPERATIVO.md` refleje su cierre.

## 6.1 Objetivo

Cerrar únicamente las invariantes técnicas necesarias para que una futura capability cognitiva no pueda:

- saltarse autorización;
- ejecutarse sin estar registrada;
- usar un registry alternativo;
- declararse lista sin entrypoint;
- usar una decisión material no canónica.

## 6.2 Invariantes

Debe cumplirse:

```text
capability no registrada
→ CAPABILITY_UNREGISTERED

NON_EXECUTABLE_CURRENT / SUSPENDED / DEPRECATED
→ CAPABILITY_UNAVAILABLE

READY_NOT_AUTHORIZED
→ exige MissionAuthorization válida

ACTIVE
→ conserva semántica vigente
```

El estado de disponibilidad se consulta únicamente desde:

```text
repository_root/config/capability_registry.json
```

La decisión material se consulta únicamente desde:

```text
docs/legacy/material_decision_registry.json
```

La autoridad de la decisión debe corresponder al dominio funcional de la capability.

## 6.3 Routing

Para capabilities semánticas:

```text
NON_EXECUTABLE_CURRENT / SUSPENDED / DEPRECATED
→ entrypoint puede ser NOT_APPLICABLE

READY_NOT_AUTHORIZED / ACTIVE
→ entrypoint real obligatorio
```

No presentar un gate determinista como entrypoint cognitivo.

## 6.4 Cierre P0

P0 solo cierra cuando:

- tests focales pasan;
- tests adversariales pasan;
- auditor cross-registry pasa;
- registries pasan;
- contamination guard pasa;
- suite transversal no muestra regresiones;
- auditoría independiente da PASS.

**P0 cerrado no autoriza P1.**

---

# 7. P1 — VERTICAL TÉCNICA TOPIC BELONGING

**Estado:** `BLOCKED_PENDING_EXPLICIT_R2_M1_AUTHORIZATION`

P1 no puede comenzar hasta que `plans/001_CONTROL_OPERATIVO.md` autorice expresamente la misión concreta correspondiente.

## 7.1 Objetivo

Implementar únicamente:

```text
HumanInput
→ EditorialIntakeHandoff
→ TopicBelongingInput válido
→ producer
→ validación
→ reviewer independiente
→ validación
→ gate
→ persistencia
→ STOP
```

No investigación, obras, claims, tesis ni guion.

## 7.2 Frontera de TopicBelongingInput

Antes de implementar, clasificar cada campo obligatorio como:

```text
USER_SUPPLIED
DETERMINISTICALLY_DERIVED
ALREADY_AVAILABLE
COGNITIVELY_PRODUCED
```

Si un campo obligatorio no tiene origen canónico:

```text
STOP_LOCAL
```

No ampliar el formulario por conveniencia técnica.

## 7.3 Entry point real

`TOPIC_BELONGING_ASSESSMENT` solo puede pasar a `READY_NOT_AUTHORIZED` cuando existan:

- entrypoint semántico real;
- routing resoluble;
- runtime existente conectado;
- producer;
- reviewer;
- contratos;
- preflight;
- persistencia;
- gate;
- tests E2E.

## 7.4 Ejecución

Reutilizar la frontera canónica de ejecución existente.

No crear otro cliente de modelo.

## 7.5 Independencia

Producer y reviewer deben representar ejecuciones independientes verificables por provenance.

Como mínimo:

```text
producer_run_id != reviewer_run_id
```

y la separación de actor exigida por contrato.

## 7.6 Prueba E2E técnica

Usar fake únicamente en la frontera cognitiva.

Mantener reales:

- CLI/ApplicationService;
- workflow;
- storage;
- schemas;
- authorization;
- routing;
- gates;
- persistencia.

Debe demostrarse al menos:

```text
happy path técnico
output producer inválido
output reviewer inválido
run no independiente
auth ausente/inválida
capability no registrada
routing no resoluble
input incompleto
checksum/provenance inválidos
```

## 7.7 Cierre P1

P1 se considera técnicamente cerrado cuando:

- la cadena E2E llega al gate;
- los outputs se validan y persisten;
- no se fabrica editorial;
- no se amplía scope;
- auditoría independiente da PASS.

**P1 no autoriza P2.**

Tras P1:

```text
STOP
→ actualizar 001_CONTROL_OPERATIVO
→ solicitar autorización expresa de P2
```

---

# 8. P2 — PRIMERA EJECUCIÓN COGNITIVA REAL

**Estado operativo:** consultar `plans/001_CONTROL_OPERATIVO.md`; la autorización
no equivale a ejecutabilidad.

La selección de P2 se resuelve exclusivamente en
`plans/001_CONTROL_OPERATIVO.md` y en el selector booleano canónico
`config/execution_family_selection.json`. Para el MVP queda activa únicamente
la familia `AGENT_HARNESS`. El producto no selecciona agente, proveedor ni
modelo: el OWNER opera el harness y el modelo que ya tenga activo. Ningún
perfil concreto, executor, proveedor o modelo se convierte en dependencia
funcional del producto. Siguen bloqueados:

- cualquier provider API de pago;
- cualquier modelo local o provider API;
- la cognición real hasta completar handoff e importación canónica;
- toda promoción de madurez, uso productivo o fase posterior.

## 8.1 Objetivo

Probar desde terminal una `REAL_COGNITIVE_EXECUTION` mediante el mecanismo
canónico `agent_handoff`:

```text
paquete contractual
→ agent_handoff (agente/harness seleccionado explícitamente por el owner)
→ cognición real fuera del runtime
→ importación canónica y validación de checksum
→ Topic Belonging / reviewer independiente
→ gate
→ persistencia
→ STOP
```

`REAL_COGNITIVE_EXECUTION` no equivale a `INTEGRATED_PROVIDER_EXECUTION`.
Para P2 basta la primera ruta; desarrollar un executor integrado específico
queda fuera del MVP/P2. `HANDOFF_PREPARED` solo demuestra preparación y nunca
se declara como cognición real hasta que exista resultado del agente e
importación canónica válida.

## 8.2 Autorización exacta

Antes de ejecutar debe existir una MissionAuthorization estrecha con:

```text
capability exacta
familia exacta
route exacta
mode exacto
roles permitidos
paths mínimos
decisión material vigente
checksums válidos
```

No usar `ANY`.

## 8.3 Ruta de ejecución

La selección se realiza por ejecución y pertenece al owner. En el MVP se
declara una sola familia booleana activa. Para `AGENT_HARNESS` no se declara
perfil, executor, provider ni modelo: esos valores pertenecen al harness que
esté operando el OWNER. Los overrides solo se transportan para familias que
los autoricen explícitamente; no se introduce ningún default vinculante.

La familia `AGENT/HARNESS` usa `agent_handoff` como mecanismo canónico. No se
trata como provider nativo ni se añade a `REAL_EXTERNAL_PROVIDERS`.

Las familias `API_PROVIDER` y `LOCAL_MODEL` permanecen desacopladas y siguen
sujetas a sus propias autorizaciones; no hay fallback entre familias.

Si no existe una familia explícitamente seleccionada y autorizada, o no existe
una ruta canónica de handoff/importación válida:

```text
BLOCKED
```

con mensaje accionable.

Nunca fallback a fake, `SYNTHETIC_TEST`, API o modelo local.

## 8.4 Input real

El tema y la pregunta se introducen por CLI.

No se almacenan en este plan.

## 8.5 Resultado válido

La prueba no necesita terminar en aprobación editorial.

Puede terminar legítimamente en:

```text
REQUEST_MORE_EVIDENCE
BLOCK
u otro estado canónico
```

si demuestra que la cognición real verificable, el reviewer, el gate y la persistencia funcionaron correctamente.

El resultado solo puede clasificarse como `REAL_COGNITIVE_EXECUTION` cuando
la entrada procede del paquete contractual, el agente seleccionado realizó la
cognición, `agent_handoff.import_result` (o su consumidor canónico equivalente)
validó paquete, input y output, y provenance/MissionAuthorization siguen
siendo válidas. La preparación del paquete, por sí sola, permanece
`HANDOFF_PREPARED`.

## 8.6 Cierre P2

P2 cierra solo con:

- `REAL_COGNITIVE_EXECUTION` alcanzada mediante una ruta permitida y verificable;
- `REAL_COGNITIVE_EXECUTION` no equivale a `INTEGRATED_PROVIDER_EXECUTION`;
- `HANDOFF_PREPARED` no equivale a `REAL_COGNITIVE_EXECUTION`;
- `HANDOFF_IMPORTED` no equivale por sí solo a `P2 PASS`;
- provenance válida;
- autorización exacta;
- outputs contractuales;
- reviewer independiente;
- gate ejecutado;
- persistencia válida;
- ausencia de fallback a fake;
- auditoría independiente PASS.

**P2 no autoriza P3.**

Tras P2:

```text
STOP
→ actualizar 001_CONTROL_OPERATIVO
→ solicitar autorización expresa de la primera misión P3
```

---

# 9. P3 — B5-I1 POR INCREMENTOS

**Estado:** `BLOCKED_PENDING_EXPLICIT_MISSION_AUTHORIZATION`

P3 no es una única misión.

Se ejecuta mediante misiones independientes autorizadas una por una.

Secuencia de referencia:

```text
P3.1 Brief y modos de entrada
P3.2 memoria e investigación inicial
P3.3 descubrimiento, screening y dossiers
P3.4 claims, suficiencia y tesis provisional
P3.5 auditorías B5-I1
P3.6 vertical B5-I1 controlada
```

Los requisitos funcionales de cada subfase se leen de PLAN 001 y contratos vigentes.

## 9.1 Regla de avance

Para cada subfase:

```text
autorización expresa
→ implementación
→ pruebas
→ auditoría independiente
→ cierre
→ STOP
→ solicitud de siguiente autorización
```

Nunca avanzar automáticamente.

## 9.2 Cierre P3

P3 solo cierra cuando la vertical B5-I1 completa haya sido:

- ejecutada;
- persistida;
- auditada;
- aprobada conforme a la autoridad funcional vigente.

**P3 no autoriza B5-I2.**

---

# 10. P4–P7 — FASES POSTERIORES

Estas fases son hoja de ruta, no autorización.

## P4 — B5-I2

**Estado:** `BLOCKED_UNTIL_EXPLICIT_AUTHORIZATION`

Objetivo general: profundización, análisis, curación y tesis refinada conforme a la sede funcional vigente.

## P5 — B5-I3

**Estado:** `BLOCKED_UNTIL_EXPLICIT_AUTHORIZATION`

Objetivo general: arquitectura editorial, outline, apertura/cierre y demás artefactos autorizados por la fase.

## P6 — B5.5

**Estado:** `BLOCKED_UNTIL_EXPLICIT_AUTHORIZATION`

Objetivo general: prototipo editorial controlado.

## P7 — B6

**Estado:** `BLOCKED_UNTIL_EXPLICIT_AUTHORIZATION`

Objetivo general: primer guion completo controlado.

Regla:

```text
P(n) PASS
≠
P(n+1) AUTHORIZED
```

Cada fase requiere actualización y autorización expresa en `plans/001_CONTROL_OPERATIVO.md`.

---

# 11. Persistencia

El repositorio conserva:

- código;
- schemas;
- registries;
- workflows;
- gates;
- configuración;
- tests;
- documentación técnica.

El almacenamiento editorial conserva:

- input humano;
- decisiones;
- investigación;
- fuentes;
- obras;
- dossiers;
- claims;
- tesis;
- guiones;
- resultados editoriales.

No crear memoria paralela.

---

# 12. Human-in-the-loop

Toda decisión humana debe ser:

- persistida;
- trazable;
- ligada a artefacto/sujeto;
- versionada/checksum cuando aplique;
- reanudable;
- fail-closed ante stale o incompatibilidad.

No distribuir `input()` por la lógica de negocio.

---

# 13. Política de pruebas

## 13.1 Proporcionalidad

Por misión:

```text
tests focales
→ regresiones afectadas
→ tests adversariales
→ suite transversal si el cambio lo justifica
→ suite completa cuando el cambio es realmente transversal
```

## 13.2 Pruebas obligatorias según riesgo

Cuando aplique:

- schema/contract;
- authorization;
- routing;
- lifecycle;
- provenance;
- checksum;
- persistencia;
- recovery;
- independencia producer/reviewer;
- contamination;
- fail-closed.

## 13.3 Test positivo

Un test positivo debe demostrar un resultado real:

```text
SUCCEEDED
PASS
artefacto persistido
provider fake alcanzado
```

No basta comprobar ausencia de un error concreto.

---

# 14. STOP_LOCAL

Aplicar `STOP_LOCAL` cuando:

- falta autorización concreta;
- la capability no está registrada;
- el estado vivo contradice la misión;
- falta contrato necesario;
- falta origen canónico de un dato requerido;
- la ruta exige inventar gobernanza;
- falta provider autorizado para ejecución real;
- se necesita ampliar scope;
- aparece contaminación de coordinación externa;
- una fase posterior no está autorizada.

`STOP_LOCAL` detiene solo el tramo afectado.

No autoriza diseñar una solución alternativa fuera de alcance.

---

# 15. Política de ejecución por misión

Cada misión derivada de PLAN 009 debe declarar:

- objetivo único;
- fase/subfase;
- autoridad vigente;
- archivos o superficies esperadas;
- límites;
- criterios de PASS;
- STOP_LOCAL;
- tests requeridos.

No deben agruparse varias fases para ahorrar misiones.

---

# 16. Cierre operativo de cada misión con cambios

Cuando la misión haya terminado completamente, incluidas correcciones, pruebas y revisión final, ejecutar desde la raíz:

```text
autozip
```

Debe ser el último paso operativo si hubo modificaciones o creación de archivos.

Si se modifica algo después:

```text
revalidar
→ autozip nuevamente
```

La entrega debe indicar el nombre exacto del ZIP generado.

---

# 17. Auditoría independiente y Git

Flujo obligatorio para cambios materiales:

```text
implementación
→ autoauditoría del ejecutor
→ tests
→ autozip
→ auditoría independiente
→ corrección si aplica
→ nueva auditoría
→ commit/push solo tras PASS
```

No aceptar `PASS` autodeclarado como evidencia suficiente.

---

# 18. Referencia operativa en 001_CONTROL_OPERATIVO

PLAN 009 debe quedar referenciado en el estado vivo sin convertirse en autoridad.

Referencia recomendada:

```yaml
PLAN_009_DOCUMENT: plans/plan_009/009_IMPLEMENTACION_VERTICAL_EDITORIAL_CONTROLADA_DESDE_TERMINAL.md
PLAN_009_LIVE_STATE_AUTHORITY: plans/001_CONTROL_OPERATIVO.md
PLAN_009_MUTABLE_STATE: RESOLVED_EXCLUSIVELY_FROM_LIVE_STATE_AUTHORITY
```

La presencia de estas claves **no autoriza ninguna fase ni duplica el estado vivo**.

---

# 19. Matriz resumida

| Fase | Propósito                        | Estado por defecto | Qué la habilita                                       |
| ---- | -------------------------------- | ------------------ | ----------------------------------------------------- |
| P0   | Base segura                      | según estado vivo  | misión correctiva vigente                             |
| P1   | Vertical técnica Topic Belonging | BLOCKED            | autorización R2-M1 expresa                            |
| P2   | Ejecución cognitiva real         | SEGÚN_AUTORIDAD_VIVA | familia autorizada + handoff/import canónicos; `OWNER_MANAGED_EXTERNALLY` |
| P3   | B5-I1 incremental                | BLOCKED            | autorización independiente por subfase                |
| P4   | B5-I2                            | BLOCKED            | autorización explícita posterior                      |
| P5   | B5-I3                            | BLOCKED            | autorización explícita posterior                      |
| P6   | B5.5                             | BLOCKED            | autorización explícita posterior                      |
| P7   | B6                               | BLOCKED            | autorización explícita posterior                      |

---

# 20. Acción operativa vigente

La secuencia operativa vigente se resuelve exclusivamente contra el control
operativo vivo. Este roadmap no replica estados mutables ni concede autoridad.
Cuando el control operativo autorice el tramo correspondiente, la secuencia es:

```text
1. Resolver la misión activa desde `plans/001_CONTROL_OPERATIVO.md`.
2. Verificar la MissionAuthorization vigente de esa misión.
3. Ejecutar únicamente el roundtrip P2 si existe autorización específica para
   su integración y el handoff/import canónicos.
4. Ejecutar reviewer, gate y persistencia.
5. STOP y actualizar el estado vivo; P2 PASS no autoriza P3.1.
```

Si falla la resolución del executor, la importación, la provenance, el gate o
la persistencia, aplicar `STOP_LOCAL` y solicitar una reparación específica.
No se inicia P3 ni se infiere autorización de fases posteriores.

---

# 21. Estado final esperado

PLAN 009 puede considerarse completado únicamente en la medida en que las fases autorizadas hayan sido ejecutadas y auditadas.

No existe obligación de llegar automáticamente a P7.

Estados aceptables:

```text
PARTIALLY_COMPLETED_BY_OWNER_DECISION
COMPLETED
BLOCKED_BY_AUTHORITY
BLOCKED_BY_TECHNICAL_DEPENDENCY
```

El plan nunca cambia por sí mismo:

```text
AUTHORIZED_FOR_PRODUCT_USE
PUBLICATION_AUTHORIZATION
```

---

# 22. Criterio de cierre

PLAN 009 se cierra cuando:

1. las fases realmente ejecutadas están reflejadas en el estado vivo;
2. cada fase cerrada tiene evidencia y auditoría;
3. no se presenta como completada ninguna fase no autorizada;
4. no existen transiciones automáticas entre fases;
5. los datos editoriales permanecen fuera del repositorio;
6. el producto sigue sin adquirir uso productivo o publicación por efecto de este plan.

---

## Regla final

PLAN 009 es una **hoja de ruta de implementación**.

No es:

```text
autorización
estado vivo
contrato editorial
gate funcional
```

La secuencia correcta siempre es:

```text
planificar
→ autorizar misión concreta
→ implementar
→ probar
→ auditar
→ cerrar
→ volver a autorizar
```
