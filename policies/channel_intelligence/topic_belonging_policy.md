# Política funcional de pertenencia temática — Más Allá del Guion

**Owner funcional:** CHANNEL_INTELLIGENCE
**Owner técnico (implementa y valida):** INFRASTRUCTURE_GOVERNANCE
**Sede canónica de B5_PRE:** `plans/plan_001/B5_PRE_SCRIPT_FOUNDATION.md`

## Autoridad y lectura obligatoria

Esta política es la autoridad funcional canónica para `CHANNEL_INTELLIGENCE_PRODUCER` y `CHANNEL_INTELLIGENCE_REVIEWER`. Antes de decidir, ambos resuelven el puntero activo, el registro editorial y su `compiled_profile_path` exacto; no infieren identidad desde documentos históricos ni desde la versión más reciente.

## Criterio de pertenencia

Una propuesta puede entrar mediante **`TOPIC_FIRST`**, **`ANCHOR_WORK_FIRST`** o **`CORPUS_FIRST`**; no existe una única vía de entrada.

`TOPIC_FIRST` puede comenzar por un problema, pregunta humana, social o cultural sin una obra definida. En esa modalidad no se exige una obra definitiva en la entrada.

Independientemente de la modalidad, antes de aprobar el paso hacia B5-I1 toda propuesta debe haber identificado una **puerta narrativa verificable** y **obras candidatas suficientes** para sostener el formato principal.

La pertenencia formula una pregunta humana, social o cultural verificable, ofrece una interpretación propia más allá de la recapitulación y puede sostener una tesis alineada con identidad, posicionamiento, promesa, audiencia y territorios del perfil activo.

No se aprueban crítica convencional, resumen como producto principal, noticias sin puerta narrativa, propaganda partidista, terapia/coaching, tendencias sin profundidad, conspiraciones presentadas como hechos ni explotación morbosa. Evidencia insuficiente no se transforma en aprobación.

Los territorios `ACTIVE` pueden resultar aprobables; los `EXCLUDED` se rechazan o bloquean; los `EXPERIMENTAL` se escalan. Condiciones y exclusiones han de ser concretas y verificables. La actualidad solo es admisible cuando se interpreta mediante una obra o puerta narrativa y conserva la promesa central.

## 1. Evaluación por modalidad

Cada propuesta declara exactamente una modalidad y se evalúa inicialmente según ella.

### 1.1 `TOPIC_FIRST`

Se evalúa inicialmente:

```text
problema
pregunta central
identidad
territorio
audiencia
potencial de puerta narrativa
potencial de tesis
límites
```

No se exige una obra definitiva en la entrada. La puerta narrativa y las obras candidatas se consolidan durante la investigación antes de B5-I1.

### 1.2 `ANCHOR_WORK_FIRST`

Se evalúa:

```text
obra ancla
conflicto
tema extraído
pregunta central
valor más allá de la obra
```

### 1.3 `CORPUS_FIRST`

Se evalúa:

```text
corpus
patrones
delimitación
pregunta central
selección futura
```

### 1.4 Gate funcional

Se distinguen dos estados:

```text
ENTRY_ELIGIBILITY
PRE_B5_I1_BELONGING_APPROVAL
```

- Una propuesta puede ser **elegible para investigación** (`ENTRY_ELIGIBILITY`) sin haber completado todavía la selección de obras.
- No puede aprobarse para B5-I1 (`PRE_B5_I1_BELONGING_APPROVAL`) si continúa sin una **puerta narrativa verificable** y sin **obras candidatas suficientes** para el formato principal.

## 2. Criterio funcional completo de evaluación

La evaluación de pertenencia debe considerar cada una de estas dimensiones:

- relación con la identidad;
- puerta narrativa (obra concreta solidificada antes de B5-I1);
- pregunta humana, social o cultural;
- valor más allá de la obra;
- potencial de tesis;
- territorio;
- audiencia matriz;
- persona autoral;
- límites permanentes;
- actualidad;
- sensibilidad;
- precedente;
- viabilidad del formato de tres a cinco obras;
- evidencia disponible;
- condiciones de avance.

Toda decisión exige **evidencia** y **razonamiento por dimensión**, condiciones verificables, riesgos, límites, incertidumbres y escalamiento cuando corresponda. No se permite una decisión basada únicamente en palabras clave.

## 3. Estados territoriales

```text
ACTIVE
EXPERIMENTAL
EXCLUDED
UNCLASSIFIED
```

## 4. Resultados de pertenencia

```text
ALIGNED
CONDITIONAL
MISALIGNED
INSUFFICIENT_EVIDENCE
```

Se conserva la nomenclatura canónica de los schemas `topic_belonging_assessment.json` (`territory_classification`, `identity_alignment`, `promise_alignment`).

## 5. Decisiones

```text
APPROVE
APPROVE_WITH_CONDITIONS
REQUEST_MORE_EVIDENCE
REJECT
BLOCK
ESCALATE_TO_OWNER
```

Se usa la nomenclatura canónica existente (de `topic_belonging_decision.json`), conservando el significado: `APPROVE_WITH_CONDITIONS` y `REQUEST_MORE_EVIDENCE` reemplazan las denominaciones abstractas `CONDITIONAL` / `REQUEST_CHANGES`, pero el significado se preserva.

## 6. Contenido incompatible como producto principal

Se registran como incompatibles con el producto principal:

```text
resumen
recapitulación
final explicado
curiosidades
crítica convencional
recomendación simple
obra decorativa
tendencia sin relación con identidad
pregunta genérica sin valor más allá de la obra
```

## 7. Productor

El productor recibe exclusivamente `TopicBelongingInput`, perfil activo y evidencia inicial. Evalúa puerta narrativa, pregunta central, ángulo, aporte más allá de la obra, potencial de tesis, territorio, identidad, promesa, audiencia, riesgos, condiciones y exclusiones. Emite únicamente `TopicBelongingAssessment` cerrado con provenance y checksum; nunca aprueba ni modifica el perfil. Incluye razonamiento por dimensión, condiciones verificables y escalamiento.

## 8. Revisor independiente

El revisor usa otro actor, otro `run_id` y otro contexto. Comprueba checksum, provenance, aplicación de esta política, evidencia, territorio, condiciones, exclusiones y escalamiento. No altera el assessment y emite únicamente `TopicBelongingDecision`.

`APPROVE` requiere territorio activo, alineación de identidad y promesa, evidencia suficiente y ausencia de trigger estratégico. `APPROVE_WITH_CONDITIONS` exige condiciones verificables. `REQUEST_MORE_EVIDENCE` no aprueba. `REJECT` deniega un tema incompatible; `BLOCK` impide avanzar por una condición de seguridad, evidencia o integridad. Todo trigger estratégico obliga a `ESCALATE_TO_OWNER`.

## 9. Escalamiento y OWNER

Se escala ante sensibilidad política/partidista u alta, cambio de audiencia, reinterpretación de exclusiones, nueva exposición personal, cambio de voz o persona autoral, expansión de posicionamiento, efecto permanente, precedente alto o territorio experimental. El OWNER decide mediante `TopicBelongingOwnerDecision`: `OWNER_APPROVE`, `OWNER_REJECT` o `OWNER_RETURN_FOR_CORRECTION`.

Una aprobación temática es necesaria, pero nunca autoriza producción, publicación, B5-I3, R6-C ni S5.

## 10. Límites

`CHANNEL_INTELLIGENCE` no decide la regla 3-5 de obras ni la arquitectura técnica. La viabilidad del formato 3–5 es evaluada por `SCRIPT_PRODUCT` (formato) y por `YOUTUBE_ADAPTATION` (audiencia/duración). Infraestructura implementa y valida técnicamente.

## 11. Cierre de coherencia TOPIC_FIRST

```text
TOPIC_FIRST_ACCEPTS_TOPIC_WITHOUT_INITIAL_WORK = YES
NARRATIVE_DOOR_REQUIRED_BEFORE_B5_I1 = YES
TOPIC_FIRST_CONTRADICTION = 0
```

La modalidad `TOPIC_FIRST` no exige obra definida en la entrada; la puerta narrativa verificable y las obras candidatas suficientes son obligatorias antes de la aprobación hacia B5-I1.