# PLAN 011 — REBALANCEO SOFTWARE–IA DE LA VERTICAL EDITORIAL

**PLAN_ID:** `011`
**Ruta:** `plans/plan_011/011_REBALANCEO_SOFTWARE_IA_VERTICAL_EDITORIAL.md`
**Proyecto:** YouTube — *Más Allá del Guion*
**Fecha:** 2026-09-01
**Naturaleza:** plan correctivo transversal de frontera Software–IA
**Estado documental:** propuesta; no autoriza ejecución
**Autoridad de estado vivo:** `plans/001_CONTROL_OPERATIVO.md`

---

# 0. Propósito y límite de autoridad

PLAN 011 corrige una desviación arquitectónica: algunas capacidades mezclan
trabajo cognitivo con operaciones exactas, repetibles y verificables que debe
controlar el software.

El patrón objetivo es:

```text
USUARIO
→ SOFTWARE prepara y resuelve lo determinista
→ IA razona solo donde existe ambigüedad semántica real
→ SOFTWARE valida, combina, persiste y enruta
→ HUMANO decide donde la autoridad está reservada
```

## 0.1 Relación con PLAN 001

PLAN 001 conserva exclusivamente la autoridad funcional para decidir:

```text
qué producto debe existir
qué artefactos, criterios y gates funcionales aplican
qué significa calidad editorial
qué depende de qué bloque
```

PLAN 011 no redefine el producto, los criterios editoriales, los gates
funcionales ni el orden de PLAN 001. Solo gobierna la separación:

```text
Software ↔ IA ↔ Humano
```

No crea una arquitectura, runtime, gate, registry, lifecycle, sistema de
provenance ni sistema de estado nuevo. Reutiliza y extiende de forma mínima los
mecanismos canónicos que la misión concreta autorice.

## 0.2 Regla de autorización

Este documento no activa ni autoriza:

```text
B5-I1 fuera de una misión vigente
B5-I2
B5-I3
B5.5
B6
B7
P2 REAL
uso productivo
ejecución cognitiva real
```

Cada tramo requiere, antes de cualquier escritura o ejecución:

1. `CURRENT_MISSION` no vacío en la autoridad operativa;
2. autorización, contrato y alcance de archivos de esa misión;
3. preflight canónico que vincule la misión con la autoridad viva;
4. una comprobación de que el tramo y sus dependencias siguen autorizados.

El cierre de un tramo no autoriza el siguiente. PLAN 011 no modifica por sí
mismo `plans/001_CONTROL_OPERATIVO.md`; solo una decisión autorizada puede
registrar allí cambios de estado, misión o siguiente acción.

---

# 1. Problema confirmado y decisión arquitectónica

El repositorio ya dispone de schemas, gates, tests, checksums, persistencia,
provenance, autorización, routing y lifecycle. También declara el principio:

```text
IF DETERMINISTICALLY VERIFIABLE
→ DO NOT SPEND LLM TOKENS TO DECIDE IT
```

La desviación aparece cuando una misma skill o llamada pide a la IA que:

- copie datos de la persona;
- resuelva perfil, estado o política canónicos;
- cree IDs, fechas, rutas o checksums;
- produzca una decisión editorial;
- construya el JSON final completo; y
- valide requisitos mecánicos.

Solo las decisiones editoriales o semánticas pertenecen a la IA.

## 1.1 Clasificación obligatoria

Cada dato debe declarar su procedencia y dueño en el contrato de la misión.
Una misma idea puede tener etapas distintas; por ejemplo, una pregunta puede
ser propuesta por IA y después aceptada o reemplazada por una persona.

| Categoría | Dueño | Regla |
|---|---|---|
| `USER_PROVIDED` | Usuario | Se conserva literalmente. Solo cambia mediante una nueva entrada o corrección explícita y trazable. |
| `SYSTEM_GENERATED` | Software | IDs, fechas, rutas, checksums, versiones, manifests y estados. La IA no los genera. |
| `CANONICAL_DERIVED` | Software | Perfil activo, políticas, roles, dependencias y artefactos existentes se resuelven desde su fuente canónica. |
| `AI_PROPOSED` | IA | Interpretaciones, ángulos, hipótesis, curación, tesis, narrativa, redacción y crítica. Se validan y se registran como propuestas. |
| `HUMAN_DECISION` | Persona autorizada | Aprobaciones, excepciones, cambios de alcance y autorizaciones reales. Ni IA ni software las sustituyen. |

El software puede hacer aritmética de presupuesto y validar límites. La
asignación editorial del presupuesto entre bloques sigue siendo cognitiva si
depende del significado, la progresión o la función narrativa.

---

# 2. Fuentes, reutilización y límites

Toda misión autorizada debe aplicar:

```text
SEARCH BEFORE CREATE
REUSE → EXTEND → CREATE
CONNECT BEFORE REDESIGN
SIMPLIFY BEFORE EXTEND
```

Fuentes de referencia según el tramo afectado:

```text
PLAN 001 y su bloque activo
PLAN 009 para handoff e integración progresiva, cuando aplique
PLAN 010 solo como antecedente cerrado, sin reabrirlo
.agents/skills/harness-determinista/SKILL.md
.agents/skills/verificar-no-mezcla-de-capas/SKILL.md
config/, schemas/, src/ y tests estrictamente necesarios
```

Queda fuera salvo brecha demostrada y nueva autorización:

```text
NEW_AGENT_FRAMEWORK
NEW_AI_RUNTIME
NEW_PROVIDER
NEW_GENERAL_GATE
NEW_REGISTRY
NEW_STORAGE
NEW_LIFECYCLE
NEW_PROVENANCE_SYSTEM
NEW_OBSERVABILITY_PLATFORM
NEW_AUTHORIZATION_SYSTEM
NEW_GLOBAL_REVIEWER
NEW_GENERAL_SCHEMA_FAMILY
```

También queda fuera reactivar skills legacy no ejecutables, convertir juicio
editorial en reglas rígidas, ejecutar P2 REAL, o reemplazar una aprobación
humana con IA.

---

# 3. P0 — Decisión y registro operativo previo

P0 no es una misión de implementación de PLAN 011. Es una condición previa
que debe resolver el OWNER en la autoridad operativa.

## P2 REAL

Puede existir una decisión OWNER de aplazar P2 REAL para priorizar la
continuidad técnica. Mientras esa decisión no esté registrada por la autoridad
operativa correspondiente, PLAN 011 debe expresarla únicamente como:

```text
P2_REAL_OWNER_DECISION: PENDING_OPERATIONAL_MATERIALIZATION
```

No puede declararla como estado vivo `DEFERRED`, ni cambiar por ella la
siguiente acción permitida.

## Salida esperada de P0

Antes de abrir cualquier tramo, la autoridad operativa debe indicar la misión
concreta autorizada, su alcance y si P2 REAL mantiene, cambia o difiere su
prioridad. Si falta esa decisión, se aplica `STOP_LOCAL` al tramo solicitado.

---

# 4. M0 — Preflight local de frontera

M0 no es un inventario anticipado de B5-I1 → B7 ni una auditoría de todo el
repositorio. Se ejecuta solo para el bloque que una misión vaya a abrir.

## Acciones

1. Localizar los contratos, prompts, skills, código, gates y tests de ese
   bloque.
2. Clasificar únicamente las mezclas demostrables de ese bloque según §1.1.
3. Verificar que `harness-determinista` existe, es reutilizable y remite a los
   controles canónicos aplicables.
4. Identificar si la corrección requiere una decisión funcional, humana o de
   compatibilidad antes de editar.

## Límite del harness

M0 no repara `harness-determinista`. Si el harness presenta un defecto propio:

```text
STOP_LOCAL
→ registrar el defecto y la evidencia
→ solicitar una misión separada, con alcance propio, para corregirlo
```

## Evidencia de misión

La salida de M0 es una clasificación acotada, rutas revisadas y los controles
reutilizados. No crea skills nuevas ni nuevos mecanismos generales.

---

# 5. Dependencias y riesgos transversales

Estas condiciones se evalúan por materialidad; no bloquean automáticamente
B5-I1.

| Condición | Tratamiento |
|---|---|
| B0 abierto y benchmarks pendientes | Riesgo material para B5.5, porque el prototipo necesita comparar mejora editorial. Si faltan benchmarks suficientes, B5.5 queda `STOP_LOCAL`; no se inventan sustitutos. |
| B4 abierto y operación real no demostrada | Para cada misión, comprobar que el rol, contrato y veto que consume están definidos. Si falta una responsabilidad necesaria para ese tramo, aplicar `STOP_LOCAL` a ese tramo. |
| Corpus de voz parcial y no representativo | No impide por sí solo B5-I1. En B6/B7 debe declararse como limitación de la evaluación de voz; si el criterio exigido requiere representatividad no disponible, esa evaluación queda bloqueada. |
| Episodios y artefactos persistidos | No se sobrescriben ni se reinterpretan silenciosamente. Toda evolución de contrato debe preservar lectura, reanudación y validación de evidencia histórica dentro del alcance autorizado. |

---

# 6. M1 — B5-I1 y nueva frontera contractual

**Precondición:** misión B5-I1 autorizada de forma independiente. La
autorización actual de un alcance controlado no se interpreta como autorización
automática para esta corrección o para B5-I2.

## 6.1 Objetivo

Separar en B5-I1 los datos humanos, datos del sistema, datos canónicos y
propuestas cognitivas, sin cambiar el criterio editorial definido por PLAN 001.

## 6.2 Topic Belonging: contrato de frontera

La IA no devuelve el `TopicBelongingInput` final completo. Devuelve solamente
una propuesta cognitiva acotada:

```text
TopicBelongingCognitiveProposal
  proposed_angle
  proposed_territory
  strategic_triggers
  initial_evidence, únicamente si el contrato vigente permite que la IA la complete
  proposed_central_question, solo si la entrada no contiene pregunta central
```

`initial_evidence` conserva el nombre del campo del `TopicBelongingInput`
vigente. No se introduce un campo nuevo llamado `initial_interpretation`.
La misión debe definir además si esa evidencia procede del usuario, de una
fuente registrada o de una propuesta de IA antes de permitir que la IA la
complete.

`proposed_central_question` nunca reemplaza una pregunta proporcionada por el
usuario. Si una persona proporcionó la pregunta, el software conserva ese valor
y rechaza cualquier contradicción. Si no la proporcionó, el software puede
incorporar la propuesta conforme a la regla autorizada de la misión y registrar
su procedencia como `AI_PROPOSED`.

La misión M1 puede materializar este contrato focalizado o extender un contrato
existente solo después de demostrar que el mecanismo actual no basta. No crea
una familia general de schemas.

### Datos por dueño

| Dueño | Datos |
|---|---|
| Usuario | tema, pregunta central cuando exista, obra o corpus inicial cuando exista, restricciones y contexto explícito. |
| Software | `episode_id`, `topic_input_id`, fecha, modalidad de entrada ya resuelta, bindings, perfil activo y sus identificadores/versiones/checksum, referencias internas, checksums, schema, persistencia, lifecycle y routing. |
| IA | solo los campos de `TopicBelongingCognitiveProposal`. |
| Humano | excepciones de alcance, cambios estratégicos y cualquier decisión reservada por la política vigente. |

### Combinación y validación

1. El software crea una base inmutable a partir de la entrada y de las fuentes
   canónicas.
2. La IA recibe la base necesaria y devuelve solo la propuesta cognitiva.
3. El software comprueba schema de la propuesta, campos permitidos, bindings y
   ausencia de cambios a datos protegidos.
4. El software combina base y propuesta para construir el único
   `TopicBelongingInput` final.
5. El software valida el schema final existente, lineage, checksum y reglas de
   consistencia antes de persistir y enrutar.

`TOPIC_FIRST` sigue siendo válido sin obra narrativa inicial. La misión no
puede introducir una obra obligatoria como requisito heredado.

### Compatibilidad con episodios persistidos — requisito de implementación

La implementación deberá garantizar, dentro de la compatibilidad que autorice
la misión, que los episodios anteriores con un `TopicBelongingInput` final
válido:

- no se reescriben;
- continúan leyéndose, reanudándose y validándose mediante su contrato
  histórico vigente;
- no se reclasifican ni se les inventa una propuesta cognitiva retrospectiva.

Estas garantías son requisitos que deben demostrarse con pruebas y evidencia;
este plan no declara que ya estén demostradas en el repositorio.

La nueva frontera se aplica a nuevas ejecuciones autorizadas. Si se requiere
aceptar un resultado externo antiguo, la misión debe declarar una ruta de
compatibilidad explícita y probar que no cambia evidencia ya guardada.

## 6.3 EpisodeBrief y ResearchPack

La misión clasifica sus campos sin cambiar decisiones editoriales:

```text
EpisodeBrief
  software: perfil activo, IDs, versiones, checksums, paths, serialización,
            policies canónicas, validación, lineage y persistencia
  IA: conflicto, transformación, ángulo, hipótesis, alcance, estructura y
      pregunta solo cuando falte y el contrato permita proponerla

ResearchPack
  fuente externa, usuario o IA: URL, localizador, declaración de acceso,
                              contenido o referencia de evidencia
  software: asigna IDs, valida formato y procedencia, normaliza, deduplica,
             vincula, registra cobertura estructural, calcula checksums y
             persiste
  IA: relevancia, interpretación, contraste, relación con tesis, lectura rival
      y evaluación semántica de la evidencia
```

El software no inventa URLs, localizadores ni estado de acceso. Si su fuente
no puede determinarse, el artefacto se bloquea o queda limitado según el
contrato vigente.

## Cierre de M1

La evidencia de la misión debe demostrar:

```text
USER_DATA_PRESERVED
SYSTEM_AND_CANONICAL_DATA_SOFTWARE_OWNED
AI_OUTPUT_LIMITED_TO_COGNITIVE_PROPOSAL
FINAL_TOPIC_BELONGING_INPUT_VALIDATED_AND_PERSISTED
PERSISTED_EPISODE_COMPATIBILITY_PRESERVED
SYNTHETIC_COGNITIVE_BOUNDARY_TESTED
```

La cognición puede ser simulada. El fake solo sustituye la frontera cognitiva;
aplicación, contratos, persistencia, recovery, routing y controles siguen
siendo reales.

---

# 7. M2 — B5-I2, solo con nueva autorización

**Precondición:** misión B5-I2 expresamente autorizada. PLAN 011 no convierte
la existencia de componentes B5-I2 en permiso para integrarlos.

## Aplicación de la frontera

Reutilizar, antes de crear cualquier componente:

```text
SCRIPT_PRODUCT_PRODUCER
SCRIPT_PRODUCT_AUDITOR
YOUTUBE_ADAPTATION_PRODUCER
YOUTUBE_ADAPTATION_AUDITOR
schemas, gates y auditoría semántica B5-I2 existentes
```

| Software | IA |
|---|---|
| secuencia, paradas, persistencia, recovery, checksums, lineage, bindings de rol, independencia comprobable, invalidación, reanudación y QA mecánico | análisis, curación, redundancia semántica, tesis refinada, lectura rival, promesa editorial, valor de materiales, suficiencia semántica y criterio de adecuación textual temprano |

La auditoría cognitiva no repite existencia de archivos, schemas, checksums,
versiones ni bindings que el software ya puede determinar.

El cierre de la misión debe evidenciar reutilización, ausencia de arquitectura
duplicada, separación de QA mecánico/semántico y persistencia recuperable.

---

# 8. M3 — B5-I3, solo con nueva autorización

**Precondición:** misión B5-I3 expresamente autorizada y sus prerrequisitos
funcionales de PLAN 001 satisfechos.

La misión aplica `SEARCH BEFORE CREATE` a `ViewerJourney`, `OpeningDesign`,
`ClosingDesign`, `NarrativePlan`, outline y presupuesto. Si hacen falta
contratos focalizados, su necesidad, dueño, entrada, salida, validación y
compatibilidad deben declararse en la misión antes de implementarlos.

| Software | IA |
|---|---|
| IDs, versiones, lineage, artefactos disponibles, orden contractual, cálculos, conteos, checksums, persistencia y validación | recorrido del espectador, función de apertura y cierre, progresión, arquitectura argumentativa, outline y decisiones de énfasis o secuencia dependientes de significado |

`skill_mapa_eventos_y_outline` continúa no ejecutable hasta su modificación
autorizada. No se reactivan reglas legacy.

---

# 9. M4 — B5.5, solo con nueva autorización

**Precondición:** misión B5.5 expresamente autorizada, diseño B5 aprobado y
benchmarks B0 suficientes y trazables.

B5.5 no se fusiona con B6. Su función es producir evidencia editorial temprana
con el prototipo definido por PLAN 001 y decidir si B6 puede comenzar.

El principio de frontera aplica así:

```text
software: prepara artefactos aprobados, versiones, trazabilidad y comparación
           estructural disponible
IA:       produce los fragmentos cognitivos autorizados
humano:   emite cualquier decisión editorial reservada
```

Si B0 no aporta benchmarks suficientes, aplicar `STOP_LOCAL` a B5.5. No se
declara una mejora editorial ni se inicia B6 por sustitutos improvisados.

---

# 10. M5 — B6, solo con nueva autorización

**Precondición:** misión B6 expresamente autorizada y B5.5 aprobada conforme a
PLAN 001.

## Decisión obligatoria previa

Antes de implementar B6, la responsabilidad competente debe elegir una única
convención canónica para los entregables finales:

```text
final_script_clean.md / final_script_annotated.md
o
06_guion_longform.md / 06_guion_longform_limpio.md /
06_guion_longform_anotado.md
```

La decisión debe identificar contratos, cierre y compatibilidad afectados. No
se mantienen dos nombres canónicos para el mismo artefacto.

## Frontera B6

| Software | IA |
|---|---|
| context pack, selección de artefactos aprobados, versiones, cálculos, orden, bloques faltantes o duplicados, persistencia, versionado, ensamblaje, hashes, manifest e invalidación | redacción, argumentación, transiciones, voz, claridad, ritmo, edición semántica, oralidad y coherencia narrativa |

El ensamblaje permanece determinista. `skill_guion_longform` continúa
`REWRITE_REQUIRED_IN_B6` y no se reactiva sin la misión y la reconciliación
funcional correspondientes.

---

# 11. M6 — B7, solo con nueva autorización

**Precondición:** misión B7 expresamente autorizada y candidato B6 disponible.

| Software | IA | Humano |
|---|---|---|
| versión auditada, checksum, evidencia existente o faltante, coincidencia de aprobaciones, cambios posteriores, manifest, lineage y continuación del cierre | calidad editorial, fidelidad, coherencia, profundidad, voz, naturalidad, originalidad semántica y problemas de interpretación | aprobación editorial final y decisiones reservadas |

`src/scripts/cerrar_episodio.py` se reutiliza como base parcial. La misión B7
debe extender solo lo necesario para cumplir el cierre vigente de PLAN 001; no
puede asumir que el cierre actual representa B7 completo.

`skill_qa_editorial` continúa pendiente de reemplazo o división autorizada.
La división conserva QA mecánico en software y QA semántico en IA.

---

# 12. M7 — E2E técnico con cognición simulada

**Precondición:** misión E2E expresamente autorizada después de los tramos que
pretenda recorrer. No presupone que B5-I2, B5-I3, B5.5, B6 o B7 hayan sido
autorizados o implementados.

El E2E usa software, contratos, schemas, gates, storage, lifecycle, recovery,
routing, checksums, provenance, manifests, invalidación y ensamblaje reales.
El fake sustituye únicamente cada frontera cognitiva.

Puede demostrar:

```text
VERTICAL_TECHNICAL_CONTINUITY
DETERMINISTIC_BOUNDARIES
COGNITIVE_BOUNDARIES_ISOLATED
```

No demuestra calidad editorial real, uso productivo, independencia operacional
real ni ejecución cognitiva real. Tampoco sustituye B9 ni sus tres episodios
de validación.

---

# 13. Tests, evidencia y STOP_LOCAL

## Tests dirigidos

Cada misión reutiliza primero tests, schemas y gates existentes. Solo crea una
prueba focal cuando demuestre una brecha concreta. La validación debe cubrir,
cuando aplique:

- conservación de datos humanos;
- generación y derivación por software;
- rechazo de salida cognitiva que altere datos protegidos;
- combinación y validación del artefacto final;
- persistencia, recovery, routing, invalidación y compatibilidad afectados;
- misma versión en auditorías y rechazo de contradicciones;
- fake limitado a la frontera cognitiva.

La suite completa solo se ejecuta si el alcance o la evidencia nueva lo
justifican.

## Marcadores de evidencia

Expresiones como `USER_DATA_PRESERVED: PASS` o
`DETERMINISTIC_BOUNDARIES: PASS` son evidencia legible de una misión. No son:

```text
estados del producto
autorizaciones
gates nuevos
una segunda autoridad operativa
aprobaciones funcionales o humanas
```

La evidencia se registra mediante los mecanismos canónicos de la misión,
incluyendo archivos modificados, controles ejecutados, resultado, componentes
reutilizados, limitaciones y justificación de cualquier componente nuevo.

## STOP_LOCAL

Detener solo el tramo afectado cuando:

- falte autorización o misión vigente;
- falte una decisión funcional, humana o de compatibilidad;
- dos fuentes canónicas se contradigan;
- mover una responsabilidad a software exija inventar una regla editorial;
- no pueda determinarse la procedencia de evidencia;
- una corrección invada un frente paralelo o requiera IA REAL;
- el harness determinista tenga un defecto propio.

No se corrigen esos problemas fuera de la misión autorizada ni se bloquean
otros tramos independientes sin causa demostrada.

---

# 14. Antiobjetivos y Definition of Done

PLAN 011 se desvía si crea:

```text
más agentes para controlar agentes
más IA para verificar mecánicamente IA
un segundo runtime, gate, registry o sistema de estado
metadata, IDs, checksums o routing generados por IA
ensamblaje delegado a IA
aprobación humana sustituida por IA
reglas editoriales semánticas convertidas arbitrariamente en if/else
```

Un tramo autorizado puede cerrar cuando su evidencia demuestre que:

1. los datos humanos están preservados y sus cambios son explícitos;
2. los datos de sistema y fuentes canónicas los produce o deriva software;
3. la IA recibe y devuelve solo la tarea cognitiva necesaria;
4. el artefacto final se valida, persiste y recupera con mecanismos existentes;
5. QA mecánico y semántico permanecen separados;
6. no se duplicó arquitectura ni se creó una skill general nueva;
7. no se declaró ejecución real, calidad editorial real ni uso productivo sin
   la evidencia y aprobación correspondientes.

PLAN 011 no puede declarar por sí solo el cierre de fases no autorizadas. La
reactivación de IA REAL y cualquier ejecución P2 siguen siendo decisiones
separadas del OWNER registradas por la autoridad operativa.
