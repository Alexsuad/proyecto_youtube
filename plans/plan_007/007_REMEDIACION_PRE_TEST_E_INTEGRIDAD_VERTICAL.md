# PLAN 007 — REMEDIACIÓN PRE-TEST E INTEGRIDAD VERTICAL

**PLAN_ID:** `007`
**Ruta canónica propuesta:** `plans/plan_007/007_REMEDIACION_PRE_TEST_E_INTEGRIDAD_VERTICAL.md`
**Proyecto:** YouTube — *Más Allá del Guion*
**Fecha:** 2026-08-17
**Baseline auditada:** `ce044572298c5cd021436c30d266545278689296`
**Rama observada:** `master`
**Naturaleza:** corrección técnica y de integración derivada de auditoría PRE-TEST
**Estado inicial:** `PLAN_DEFINED_PENDING_OWNER_AUTHORIZATION`
**Objetivo:** eliminar los defectos materiales demostrados que impiden una vertical PRE-TEST confiable, sin ampliar funcionalidad ni abrir nuevas fases.

---

# 0. Autoridad y límites

Este plan:

- **no reabre completamente PLAN 004, PLAN 005 ni PLAN 006**;
- puede corregir defectos materiales descubiertos en mecanismos provenientes de ellos;
- no redefine criterios de `CHANNEL_INTELLIGENCE`, `SCRIPT_PRODUCT` ni `YOUTUBE_ADAPTATION`;
- no autoriza B5-I3, B5.5, B6 ni episodio real;
- no autoriza publicación ni producción real;
- no crea nuevos agentes permanentes salvo que aparezca una necesidad material que requiera decisión separada;
- no convierte los RCM ni `INT-NEW` en conceptos runtime;
- no copia la organización de los chats al repositorio;
- no autoriza push automáticamente.

Los criterios funcionales ya aprobados deben reutilizarse. Si durante una corrección aparece **una ambigüedad funcional genuinamente no resuelta**, la misión se detiene únicamente en esa decisión y la remite al owner correspondiente.

Este plan define dirección, dependencias, criterios de cierre y secuencia lógica. No sustituye el estado vivo del repositorio ni concede por sí mismo autorización de ejecución. La autorización de cada misión debe resolverse contra la autoridad operativa vigente en el momento de ejecutarla.

---

# 1. Entrada de auditoría

El plan nace de:

```text
31 hallazgos externos
→ 20 clusters RCM reconciliados
→ auditoría interna del repositorio
→ reauditoría independiente
```

Inventario resultante:

```text
18 RCM confirmados
2 RCM parcialmente confirmados
0 RCM refutados

1 hallazgo interno adicional:
INT-NEW-001
```

### Definicion canonica de INT-NEW-001

Un entry point operativo podia completar una ejecucion tecnica controlada y persistir provenance etiquetada como `REAL` sin que una `MissionAuthorization` valida fuese un prerrequisito obligatorio de esa ruta.

Este finding no afirma produccion editorial real no autorizada: distingue ejecucion tecnica/controlled-smoke de ejecucion editorial real. Su saneamiento queda demostrado cuando:

- una ejecucion controlada/sintetica sin `MissionAuthorization` valida no puede persistir provenance `REAL`;
- toda ruta que pretenda persistir provenance `REAL` satisface la autorizacion exigida por el preflight vigente; y
- existe una regresion adversarial de esa propiedad.

`INT-NEW-001` permanece unicamente como trazabilidad de auditoria; no es estado, capability ni concepto runtime.

Los parcialmente confirmados son:

```text
RCM-02
RCM-03
```

La parcialidad significa que la infraestructura puede demostrar cobertura, representación y ejecución semántica, pero no puede convertir una prueba estructural en prueba absoluta de calidad cognitiva.

---

# 2. Principio de remediación

No se ejecutará:

```text
1 RCM
→ 1 parche
→ 1 misión
```

La unidad de corrección será:

```text
CAUSA / INVARIANTE
→ manifestaciones afectadas
→ corrección mínima
→ regresiones
→ demostración integrada
```

`RCM-09`, en particular, **no tendrá una reparación propia**. Es una conclusión compuesta:

> La vertical B5 no está demostrada como conjunto.

Debe cerrarse mediante integración real después de corregir sus dependencias.

---

# 3. Mapa del PLAN 007

```text
P0 — Congelar baseline y evidencia
             ↓
P1 — Integridad transversal de ejecución
             ↓
    ┌────────┼─────────┬───────────┐
    ↓        ↓         ↓           ↓
P2 B5      P3 YA     P4 Legacy   P5 Semántica
    └────────┴─────────┴───────────┘
             ↓
P6-A — Vertical técnica B5
P6-B — Integración estructural SP→YA
             ↓
P7 — Reconciliación documental y readiness
```

P2–P5 pueden trabajar en paralelo **solo después de comprobar que sus write-sets no se pisan**. P3-B y P3-C quedan además condicionados a P2-D (`ClaimsLedger` corregido): la independencia del auditor YA y el grounding de rights/platform risk se validan sobre el ledger corregido.

No se crearán worktrees ni ramas por defecto; se utilizarán únicamente cuando aporten paralelismo real y seguro.

---

# P0 — BASELINE Y EVIDENCIA DE AUDITORÍA

## Propósito

Crear un punto inequívoco desde el cual ejecutar todas las reparaciones.

## Trabajo

Registrar:

- HEAD exacto;
- rama;
- estado Git;
- cambios preexistentes;
- informe externo de reconciliación;
- inventario definitivo RCM;
- `INT-NEW-001`.

El archivo preexistente:

```text
reports/reconciliation/pre_test_external_audit_reconciliation_2026-08-17.md
```

debe conservarse.

Debe existir una referencia documental definitiva de la auditoría PRE-TEST antes de cerrar PLAN 007, pero no es necesario crear múltiples informes redundantes.

## Resultado

Una sola baseline auditable para todas las misiones posteriores.

La baseline material de este plan es el HEAD del workspace `ce044572298c5cd021436c30d266545278689296` en `master`, no un ZIP. La identidad byte a byte del ZIP externo `proyecto_youtube_2026-08-17_10-30-24.zip` **no ha sido verificada** contra este HEAD: la reconciliación externa lo referencia como baseline invariable, pero este plan no afirma equivalencia exacta entre ZIP y workspace. Cualquier corrección y su evidencia se anclan al HEAD y al estado Git observados.

---

# P1 — INTEGRIDAD TRANSVERSAL DE EJECUCIÓN, AUTORIZACIÓN Y EVIDENCIA

## Cubre

```text
RCM-16
RCM-17
RCM-18
RCM-19
RCM-20A
RCM-20B
INT-NEW-001
```

Este bloque va primero porque no tiene sentido demostrar el producto con un harness cuya autorización, recovery, provenance o freshness todavía pueden mentir.

---

## P1-A — Autorización y provenance

### Problema

Una ruta puede ejecutar un controlled-smoke y persistir:

```text
execution_mode="REAL"
```

sin `MissionAuthorization` obligatoria.

### Invariante

```text
REAL EXECUTION PROVENANCE
→ requiere autoridad válida compatible con esa ejecución
```

Si una ruta es intencionalmente smoke/no autorizada, no puede presentarla como ejecución `REAL` equivalente a una misión autorizada.

### Cierre

Debe existir regresión negativa que demuestre que la combinación inválida no puede producirse.

---

## P1-B — Reservation y recovery

### Cubre

```text
RCM-17
RCM-20B
```

### Invariantes

`SAME_RESERVATION_LEASE` debe tener una sola semántica coherente entre:

- contrato;
- implementación;
- recovery;
- tests.

Y:

```text
provider success
+
reservation finalization failure
≠
SUCCEEDED limpio manteniendo RESERVED
```

Un fallo material al consumir/finalizar una reserva debe expresarse en el estado terminal, no esconderse únicamente dentro de `usage`.

### Cierre

La corrección debe reutilizar los estados existentes (`ExecutionStatus.FAILED` en `src/ai/contracts.py`); no se inventará un estado nuevo si PLAN 005 ya posee uno aplicable. Un fallo al finalizar la reserva tras éxito del provider debe producir `FAILED` como resultado terminal, marcar la reserva como no consumida (nunca `CONSUMED`) y conservar el error verificable en provenance.

Debe existir regresión adversarial que compruebe simultáneamente:

- el resultado terminal no es `SUCCEEDED` cuando la finalización de la reserva falló;
- la reserva no queda `CONSUMED`;
- el error de finalización es observable en `usage`; y
- la semántica `SAME_RESERVATION_LEASE` es idéntica entre contrato, implementación, recovery y tests, sin distinguir `FRESH` de `STALE`/`UNVERIFIABLE` salvo que el contrato lo defina explícitamente.

---

## P1-C — Freshness, applicability y closure

### Cubre

```text
RCM-18
RCM-19
RCM-20A
```

### Invariantes

Separar explícitamente:

```text
HISTORICAL_COMPLETION
CURRENT_APPLICABILITY
CURRENT_FRESHNESS
CURRENT_CLOSURE
```

Freshness debe depender no solo de inputs, sino también de aquello que materialmente determina el resultado:

```text
inputs relevantes
+
criterio/generador relevante
+
schema/contrato relevante
```

Un cambio material del generador no puede dejar evidencia anterior en `FRESH` por accidente.

Si un schema requerido no existe:

```text
FileNotFoundError
```

no puede escapar como sustituto de una decisión fail-closed estructurada.

No se debe “resolver” RCM-20A creando a ciegas el schema inexistente. Primero se determinará si la referencia es incorrecta o si realmente falta un contrato canónico.

---

## P1-D — Tests que realmente alcanzan la capa objetivo

### Cubre

`RCM-16`.

No se debilitará el preflight para conseguir tests verdes.

Los tests de:

- provider;
- timeout;
- output;
- provenance;

deben preparar un preflight válido de prueba y **demostrar que alcanzaron realmente esa capa**.

Un bloqueo temprano por semantic evaluator no es evidencia de provider ni timeout.

### Criterio de cierre de P1

P1 solo cierra cuando las regresiones adversariales demuestran los invariantes anteriores y los mecanismos comunes pueden utilizarse con confianza para auditar P2–P6.

---

# P2 — CONTINUIDAD CONTRACTUAL E INTEGRACIÓN B5

## Cubre

```text
RCM-01
RCM-06
RCM-07
RCM-08
RCM-13
```

RCM-09 depende de este bloque, pero no se cierra todavía.

---

## P2-A — `TOPIC_FIRST / NO_WORK_YET`

La corrección debe cubrir la cadena completa con las dos fronteras canónicas de la política de pertenencia (`policies/channel_intelligence/topic_belonging_policy.md`):

```text
TOPIC_FIRST
→ ENTRY_ELIGIBILITY (sin obra definitiva)
→ investigación + puerta narrativa + candidatas suficientes
→ PRE_B5_I1_BELONGING_APPROVAL
→ brief
→ B5-I1
```

No basta con corregir un schema aislado.

### Invariante

`TOPIC_FIRST` puede comenzar legítimamente sin obra: la elegibilidad de entrada (`ENTRY_ELIGIBILITY`) no exige obra definitiva ni material narrativo.

Los contratos no pueden imponer material narrativo antes del momento funcional en que realmente pasa a ser obligatorio: la exigencia de investigación, puerta narrativa y candidatas suficientes se resuelve en la frontera de aprobación de pertenencia (`PRE_B5_I1_BELONGING_APPROVAL`), no antes.

El relajamiento de `narrative_work`/`narrative_materials` solo aplica hasta `ENTRY_ELIGIBILITY` y no puede degradar la frontera de aprobación.

Si una exigencia funcional no puede resolverse con las fronteras existentes, el plan debe detenerse y remitir la decisión a la capa funcional correspondiente.

No debe degradarse `ANCHOR_WORK_FIRST` ni `CORPUS_FIRST`.

---

## P2-B — `WorkResearchDossier` progresivo

### Cubre

`RCM-06`.

El dossier debe poder crecer según lifecycle.

Un estado temprano no puede exigir retrospectivamente:

```text
NarrativeHumanAnalysis
ClaimsLedger completo
```

si esos productos corresponden a una fase posterior.

La profundidad exigida aumenta con el lifecycle y con el uso previsto.

---

## P2-C — Curación final 3–5

### Cubre

`RCM-07`.

La política vigente se aplicará donde corresponde:

```text
FINAL
→ normalmente 3–5 obras sustantivas
```

No debe aplicarse erróneamente a:

- screening;
- fixtures preliminares;
- candidatos;
- estados tempranos.

Las excepciones funcionales ya aprobadas deben conservarse.

---

## P2-D — Integridad de `ClaimsLedger`

### Cubre

`RCM-08`.

Como mínimo:

```text
claim_id no vacío
claim_text no vacío
claim_id único dentro del ledger
```

y los consumidores críticos deben poder confiar en esas invariantes.

No crear un segundo ledger.

---

## P2-E — `B5_I2_SEMANTIC_AUDITOR`

### Cubre

`RCM-13`.

Debe existir una única ruta canónica coherente entre:

```text
capability
routing
prompt
skill
runner/preflight
```

No basta con añadir una clave al registry: debe pasar integridad cross-registry y ser resoluble por el flujo real.

---

# P3 — INDEPENDENCIA Y GROUNDING DE YOUTUBE ADAPTATION

## Cubre

```text
RCM-04
RCM-10
RCM-12
```

---

## P3-A — Retorno estratégico YA → CI

Cuando YouTube Adaptation descubre una condición que materialmente afecta:

- identidad;
- audiencia matriz;
- promesa principal;
- territorio;
- posicionamiento;

debe existir un retorno explícito hacia la autoridad correspondiente.

No puede resolverse silenciosamente dentro de YA.

La clasificación de la condición debe reutilizar la taxonomía de triggers estratégicos ya aprobada en la capa CI (`schemas/topic_belonging_input.json` y `policies/channel_intelligence/topic_belonging_policy.md`); no se define una taxonomía paralela. Si el retorno YA→CI requiere un mecanismo funcional distinto del existente, el plan debe detenerse y remitir la decisión a la capa funcional, no inventar el mecanismo.

---

## P3-B — Independencia del auditor YA

El auditor no puede depender únicamente de la síntesis del productor.

Debe poder contrastar, mediante referencias originales e inmutables cuando corresponda:

```text
tesis
ClaimsLedger
evidencia relevante
paquete producido
```

No significa copiar todos los inputs al contexto. Debe conservarse economía de contexto usando referencias y carga proporcional.

### Dependencia

P3-B depende materialmente de P2-D: la independencia del auditor se ejerce contrastando el `ClaimsLedger` corregido, con referencias originales y grounding coherente. No puede validarse la independencia del auditor sobre un ledger cuya integridad sigue sin corregir.

---

## P3-C — Grounding de rights/platform risk

Una decisión material de:

```text
rights
reuse
platform risk
```

no puede quedar sustentada exclusivamente por:

- referencias vacías;
- referencias genéricas;
- severidad + mitigación sin evidencia pertinente.

Debe existir vínculo verificable con la evidencia específica utilizada para esa decisión.

### Dependencia

P3-C depende materialmente de P2-D: el grounding de rights/reuse/platform risk se vincula a referencias originales cuya integridad queda garantizada por el `ClaimsLedger` corregido.

---

# P4 — FRONTERA LEGACY Y PORTABILIDAD

## Cubre

```text
RCM-11
RCM-14
```

---

## P4-A — Packaging diferido

Debe distinguirse:

```text
early packaging permitido
≠
packaging final diferido
```

Las rutas legacy no pueden bloquear un cierre permitido por el MVP actual exigiendo:

```text
09_packaging.md
10_seo.md
```

cuando esos outputs pertenezcan a una fase todavía diferida.

No se elimina código legacy por reflejo; se aísla, condiciona o adapta según la autoridad vigente.

---

## P4-B — Gate0 portable

La ejecución desde un checkout válido no puede depender inevitablemente de:

```text
config/local_settings.json
Vault local preparado
```

antes de alcanzar las capacidades modernas si existe una vía portable aprobada.

No se eliminan configuraciones locales útiles; se elimina su condición de dependencia universal.

---

# P5 — ASSURANCE SEMÁNTICO Y MEMORIA MULTIDOMINIO

## Cubre

```text
RCM-02
RCM-03
```

Estos son casos especiales.

El plan **no pretende demostrar matemáticamente que una IA “comprendió correctamente” el contenido**.

---

## P5-A — Semantic assurance

Un gate estructural puede demostrar:

- presencia;
- lineage;
- checksum;
- completitud;
- coherencia de estados.

No debe presentarse por sí solo como prueba de que se evaluaron correctamente todas las dimensiones expertas.

### Invariante

Un `semantic PASS` completo debe conservar evidencia de qué dimensiones funcionales fueron efectivamente sometidas a evaluación.

Una omisión material conocida debe impedir presentar el resultado como cobertura semántica completa.

### Fuentes canónicas

Las dimensiones evaluadas se toman únicamente de fuentes funcionales aprobadas, versionadas y con checksum cuando el runtime las provea:

- dimensiones CI: `policies/channel_intelligence/topic_belonging_policy.md` y schemas de la capa CI;
- dimensiones YA: `config/youtube_adaptation_r3_traceability.json` (capabilities y su clasificación);
- dimensiones SP: schemas y políticas de producto vigentes.

No se inventan dimensiones nuevas en el plan. Si una dimensión funcional requerida no existe en esas fuentes, el plan debe detenerse y remitir la definición a la capa funcional.

---

## P5-B — Semantic memory

La memoria debe representar explícitamente las dimensiones requeridas de:

```text
CHANNEL_INTELLIGENCE
SCRIPT_PRODUCT
YOUTUBE_ADAPTATION
```

sin fusionar owners.

La memoria puede compartir infraestructura, pero:

```text
dimensión CI
≠ dimensión SP
≠ dimensión YA
```

La similitud tampoco puede convertirse por sí sola en bloqueo funcional.

### Extensión sin fusión

El contrato canónico existente `schemas/editorial_semantic_memory.json` se preserva como contrato canónico único de memoria, no como fuente funcional de dimensiones. La extensión de memoria multidominio no crea un segundo catálogo que duplique o fusione owners. Las dimensiones de cada owner (CI/SP/YA) siguen perteneciendo a las fuentes funcionales CI/SP/YA correspondientes, que se referencian por versión y checksum desde el contrato de memoria; la infraestructura compartida es mecánica, no fusión de criterios.

---

# P6 — DEMOSTRACIÓN DE VERTICAL Y DE INTEGRACIÓN ESTRUCTURAL

Este bloque **no introduce arquitectura nueva**.

Utiliza lo corregido en P1–P5 y demuestra que existe una cadena integrada. Se divide en dos demostraciones con naturaleza distinta que **no deben mezclarse**:

## P6-A — Vertical técnica B5

### Cierra

`RCM-09` (bloque B5 técnico efectivo y controlado: entrada a B5-I2, inclusivo).

### Alcance

Debe incluir, como mínimo:

```text
entrada controlada TOPIC_FIRST
→ topic belonging
→ EpisodeBrief
→ B5-I1
→ work lifecycle
→ WorkResearchDossier progresivo
→ ClaimsLedger
→ curación válida
→ B5-I2
→ B5_I2_SEMANTIC_AUDITOR por ruta canónica
→ gates correspondientes
```

La prueba debe utilizar una fixture controlada/sintética o input de prueba autorizado.

**No es todavía un episodio real.** Esta vertical termina en B5-I2; no se ejecuta el retorno funcional a CI ni el paquete YA.

### Criterio crítico

No se aceptará:

```text
test A pasa
+
test B pasa
+
test C pasa
=
vertical demostrada
```

Tiene que existir al menos una ejecución que atraviese realmente la cadena B5 y conserve lineage entre sus etapas.

### RCM-09

Solo puede cerrarse en P6-A, con una ejecución técnica efectiva, controlada y end-to-end de la cadena B5.

---

## P6-B — Integración estructural SP→YA

### Cierra

Ningún RCM de ejecución real. No cierra capabilities YA.

### Alcance

Demuestra estructuralmente que el pipeline puede producir un paquete YA y encaminarlo al auditor independiente:

```text
salida B5-I2 técnicamente válida y controlada
→ paquete YA estructural
→ auditor YA independiente (estructural)
→ gates correspondientes
```

La demostración es de integración estructural con clase de ejecución `CONTROLLED_TECHNICAL_HARNESS_E2E`, no una ejecución real de YA.

### Límite

Las capabilities YA con `real_execution_required: true` (`config/youtube_adaptation_r3_traceability.json`) **no se ejecutan ni se cierran** en P6-B. Esta demostración no autoriza producción real, publicación ni declaraciones de readiness funcional de YA.

### Criterio crítico

El paquete estructural debe atravesar los contratos de la cadena SP→YA con lineage conservado, sin atribuirse comportamiento real de YA ni cierre de capabilities.

---

# P7 — RECONCILIACIÓN DOCUMENTAL Y READINESS

## Cubre

```text
RCM-05
RCM-15
```

y el estado final del PLAN 007.

---

## RCM-05

El estado vivo debe reflejar el comportamiento reproducible actual del contamination guard.

No se mantiene `FAIL / 2 contaminaciones` si el scanner canónico demuestra `PASS / 0`.

Pero esto se actualiza con evidencia, no simplemente editando el texto.

---

## RCM-15

La matriz de trazabilidad R1 debe reconciliarse con los hitos realmente completados.

No se reescribe historia. Debe distinguir:

```text
estado histórico
estado completado
estado vivo actual
```

---

# 4. Paralelismo

Después de P1:

```text
P2 — B5
P3 — YA
P4 — legacy/portabilidad
P5 — assurance semántico
```

son **candidatos a ejecución paralela**, **excepto P3-B y P3-C**, que dependen materialmente de P2-D (`ClaimsLedger` corregido): la independencia del auditor YA y el grounding de rights/platform risk no pueden validarse sobre un ledger sin corregir.

Los candidatos reales a paralelización inicial son P3-A, P4 y la parte de P5 que no dependa de P2-D. Antes de abrirlos en paralelo se debe calcular:

```text
write-set P2
write-set P3
write-set P4
write-set P5
```

Si existen archivos compartidos materiales:

- se secuencian;
- o se separan por worktrees con integración explícita.

No utilizar worktrees únicamente porque OpenCode los soporte.

---

# 5. Estrategia de agentes y modelos

PLAN 007 no prescribe proveedor.

Una política razonable:

```text
misión conocida/mecánica
→ modelo económico competente

cambio contractual complejo
→ modelo medio/fuerte

ambigüedad causal
→ escalar

review independiente
→ modelo distinto cuando aporte valor
```

`Technical-Implementer` puede utilizarse para las misiones técnicas ya autorizadas.

`technical-reviewer` puede revisar cambios acotados de forma independiente.

No se crean clones por RCM.

---

# 6. Política de pruebas

Cada incremento seguirá:

```text
prueba que reproduce el defecto
→ corrección
→ regresión dirigida
→ tests del componente
→ integración necesaria
```

No ejecutar suites enormes automáticamente después de cada archivo.

La suite amplia se utiliza cuando:

- cambia un mecanismo transversal;
- cierra una wave;
- existe riesgo real de regresión amplia;
- se prepara P6/P7.

Y siempre:

```text
PASS nominal
≠
propiedad demostrada
```

Debe comprobarse que la prueba alcanzó la capa objetivo.

---

# 7. Condiciones de cierre de PLAN 007

PLAN 007 no cierra porque todos los RCM aparezcan como `DONE`.

Cierra cuando existe evidencia de que:

1. los invariantes de autorización, reservation, provenance y freshness son coherentes;
2. `TOPIC_FIRST` atraviesa correctamente la frontera sin obra temprana;
3. el dossier es progresivo;
4. la curación final aplica correctamente la política 3–5/excepción;
5. `ClaimsLedger` mantiene identidad mínima y unicidad;
6. `B5_I2_SEMANTIC_AUDITOR` resuelve por vía canónica;
7. la independencia del auditor YA es demostrable como propiedad de la ruta/contrato del auditor sobre el `ClaimsLedger` corregido (depende de P2-D), sin implicar ejecución funcional real de YA;
8. platform/rights risk está grounded y vinculado a evidencia específica del `ClaimsLedger` corregido (depende de P2-D);
9. existe retorno YA→CI para cambio estratégico, clasificado con la taxonomía CI existente;
10. legacy no obliga outputs diferidos;
11. Gate0 dispone de camino portable;
12. semantic assurance no confunde estructura con juicio experto;
13. semantic memory representa las dimensiones requeridas por owner;
14. existe una **vertical técnica B5 integrada demostrada** (P6-A) y la **integración estructural SP→YA** (P6-B) sin atribuir ejecución real ni cierre de capabilities YA;
15. contamination/live-state y trazabilidad documental coinciden con realidad;
16. los defectos `RCM-17/18/19/20A/20B` y `INT-NEW-001` tienen regresiones adversariales;
17. Git y evidencias permiten demostrar exactamente qué se corrigió.

---

# 8. Resultado final permitido

`PRE_TEST_TECHNICAL_READINESS: READY_FOR_OWNER_REVIEW` es la **conclusión de un informe de evidencia** que PLAN 007 puede producir, no un estado nuevo del runtime, de la misión ni del producto.

PLAN 007 no introduce ni declara estados nuevos en `plans/001_CONTROL_OPERATIVO.md` ni en el runtime: el resultado se registra como conclusión de evidencia y no modifica el estado vivo.

No puede declarar por sí solo:

```text
REAL_PRE_TEST_AUTHORIZED
B5_I3_AUTHORIZED
PRODUCT_USE_AUTHORIZED
```

Eso requiere decisión posterior del owner.

---

# 9. Secuencia de misiones propuesta

El número exacto de misiones puede ajustarse después de comprobar write-sets y dependencias reales.

La secuencia inicial propuesta es:

```text
M1 — Baseline y evidencia documental mínima

M2 — Authorization + reservation + provenance

M3 — Freshness + applicability + closure

M4 — AI target-layer testing

── wave paralela candidata (tras write-sets) ──

M5 — B5 contracts/routing (P2-A, P2-B, P2-C, P2-D, P2-E)

M6-A — YA strategic return (P3-A)

M7 — Legacy + portability (P4)

M8 — Semantic assurance/memory (P5, ligado a fuentes funcionales)

── depende de P2-D (ClaimsLedger corregido) ──

M6-B — YA auditor independence + platform/rights grounding (P3-B, P3-C)

── convergencia ──

M9-A — Vertical técnica B5 (P6-A)

M9-B — Integración estructural SP→YA (P6-B)

M10 — Reconciliation + readiness (P7)
```

El plan gobierna el objetivo; el número de misiones no debe convertirse en arquitectura ni en restricción artificial.

---

# 10. Regla final

PLAN 007 existe para eliminar defectos materiales PRE-TEST demostrados, no para ampliar el sistema.

La secuencia de trabajo debe aplicar:

```text
defecto reproducido
→ causa raíz
→ reutilización de mecanismo existente
→ corrección mínima suficiente
→ prueba adversarial
→ integración
→ evidencia
```

La implementación debe favorecer:

- producto real sobre infraestructura;
- reutilización sobre duplicación;
- evidencia sobre autodeclaración;
- paralelismo solo cuando reduzca tiempo sin aumentar riesgo;
- mínimo contexto suficiente;
- neutralidad de executor;
- protección de autoridad funcional;
- ausencia de nuevas fuentes de verdad innecesarias.
