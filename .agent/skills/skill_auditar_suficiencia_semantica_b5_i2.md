# Skill — Auditar suficiencia semántica de B5-I2

## Identidad

```text
skill_id: skill_auditar_suficiencia_semantica_b5_i2
version: 1.0.0
status: FUNCTIONAL_SPEC_APPROVED
functional_owner: SCRIPT_PRODUCT
technical_owner: INFRASTRUCTURE_GOVERNANCE
active_block: B5-I2
role: INDEPENDENT_EDITORIAL_AUDITOR
```

## Objetivo

Determinar si los artefactos editoriales producidos durante B5-I2 poseen suficiente especificidad, profundidad, trazabilidad, contraste y capacidad argumentativa para alimentar B5-I3.

La skill debe impedir que B5-I2 avance con resultados formalmente completos y estructuralmente válidos, pero genéricos, formularios, decorativos o editorialmente inútiles.

La salida de la IA contiene únicamente juicio semántico. IDs, versiones, fechas,
checksums, referencias canónicas, perfil activo, lineage, provenance, estados y
bindings pertenecen al Software y no deben ser inventados por la skill.

Pregunta central:

> ¿Los análisis, la curación y la tesis refinada contienen decisiones editoriales sustantivas y demostrables que permitan construir después un recorrido, una arquitectura y un outline profesionales?

## Autoridad funcional

La autoridad funcional pertenece a `SCRIPT_PRODUCT`.

`INFRASTRUCTURE_GOVERNANCE` puede decidir la estructura técnica, schema, runtime, integración, provenance, gate, catálogo, pruebas y mecanismo de ejecución.

`INFRASTRUCTURE_GOVERNANCE` no puede reducir ni modificar los criterios editoriales críticos de esta skill sin nueva validación de `SCRIPT_PRODUCT`.

## Cuándo debe ejecutarse

Debe ejecutarse cuando B5-I2 haya producido como mínimo:

```text
NarrativeHumanAnalysis[]
MaterialCuration — FINAL
RefinedThesis
```

y estén disponibles los antecedentes autorizados de B5-I1.

Debe ejecutarse:

1. después de completar análisis, curación y tesis refinada;
2. antes de solicitar la reauditoría funcional final de `SCRIPT_PRODUCT`;
3. antes de permitir cualquier inicio de B5-I3;
4. nuevamente cuando cambie cualquiera de los artefactos auditados o una restricción heredada.

## Cuándo no debe utilizarse

No debe utilizarse para auditar:

- briefs;
- schemas;
- integridad de archivos;
- código;
- arquitectura narrativa;
- outline;
- redacción;
- edición de desarrollo;
- edición de línea;
- oralidad;
- packaging;
- título;
- miniatura;
- SEO;
- Shorts;
- Audio;
- Video;
- publicación;
- analítica.

Tampoco sustituye:

- el gate técnico;
- la auditoría funcional humana de `SCRIPT_PRODUCT`;
- la auditoría de packaging de `YOUTUBE_ADAPTATION`;
- la auditoría editorial final del guion.

## Entradas obligatorias

### Antecedentes de B5-I1

```text
ResearchPack
SourceAccessAndEvidenceReport
ThesisArtifact — THESIS_PROVISIONAL
restricciones heredadas
claims críticos
claims excluidos
disclosures obligatorios
análisis permitidos, limitados y prohibidos
```

### Productos de B5-I2

```text
NarrativeHumanAnalysis[]
MaterialCuration — FINAL
RefinedThesis
EditorialScriptPromise
```

### Contexto editorial necesario

```text
EpisodeBrief
EditorialProfile exacto consumido
pregunta central
objetivo editorial
materiales candidatos
materiales seleccionados y excluidos
```

### Entrada de coordinación funcional opcional

Puede recibir, en modo de solo lectura:

```text
EarlyPackagingHypothesis
```

Su uso se limita a responder:

> ¿La tesis y la evidencia pueden cumplir honestamente la promesa temprana?

La skill no debe evaluar:

- calidad comercial del título;
- eficacia de miniatura;
- audiencia concreta;
- potencial de clic;
- estrategia de packaging.

Esas decisiones pertenecen a `YOUTUBE_ADAPTATION`.

## Salida funcional

La skill debe producir un dictamen estructurado con:

```text
audit_id
episode_id
audited_artifact_ids
audited_artifact_versions
decision
readiness
criteria_results
findings
blocking_defects
non_blocking_defects
cited_evidence
required_corrections
unresolved_questions
inherited_restrictions_checked
youtube_adaptation_interface_observation
auditor_statement
```

### Estados de decisión

```text
PASS
WARN
FAIL
BLOCKED
```

### Estados de preparación

```text
READY_FOR_EDITORIAL_FUNCTIONAL_REVIEW
NOT_READY_FOR_EDITORIAL_FUNCTIONAL_REVIEW
BLOCKED_BY_MISSING_INPUT
```

La skill no debe producir ni inferir:

```text
B5_I3_AUTHORIZED
```

## Criterios obligatorios de auditoría

### 1. Especificidad del análisis

Debe comprobar que los hallazgos no sean intercambiables entre obras, personajes o episodios.

Un análisis suficiente debe identificar, según corresponda:

- sujeto, personaje, relación, grupo o institución;
- acción, decisión, escena, pasaje o patrón concreto;
- tensión o contradicción;
- relación entre causas, decisiones y consecuencias;
- coste humano, relacional o social;
- cambio o ausencia de cambio;
- función del hallazgo dentro del episodio;
- límites de la interpretación.

No es suficiente:

```text
El personaje tiene miedo.
La sociedad influye en las personas.
El poder puede corromper.
Cada situación depende del contexto.
```

El auditor debe explicar qué elementos concretos impiden que el análisis sea genérico.

### 2. Evidencia narrativa y externa

Cada afirmación relevante debe apoyarse en evidencia adecuada.

Debe distinguirse entre:

```text
evidencia narrativa
→ escena, acción, diálogo, pasaje, capítulo o decisión

evidencia externa
→ fuente histórica, social, cultural, psicológica o institucional
```

La auditoría debe comprobar:

- referencia identificable;
- localizador suficiente;
- relación explícita entre evidencia y afirmación;
- uso autorizado de la fuente;
- respeto a limitaciones de acceso;
- ausencia de autorreferencia circular.

No es válido:

```text
El análisis es correcto porque otro campo del mismo análisis lo afirma.
```

### 3. Separación epistemológica

Debe comprobar que estén diferenciados:

```text
FACT
INTERPRETATION
HYPOTHESIS
COUNTERARGUMENT
```

Debe bloquearse cuando:

- una interpretación se presenta como hecho;
- una hipótesis se presenta como conclusión demostrada;
- se atribuye intención sin evidencia;
- se generaliza de una obra a la realidad sin límite;
- se utiliza ficción como prueba directa de un fenómeno real.

### 4. Profundidad y utilidad editorial

El análisis debe aportar algo que pueda transformar el episodio.

Debe cumplir al menos una función real, como:

- revelar una contradicción;
- complejizar la lectura inicial;
- conectar individuo y sistema;
- introducir una causa o consecuencia;
- aportar una interpretación rival;
- establecer un límite;
- modificar la tesis;
- preparar una progresión futura.

Un análisis puede ser correcto y aun así ser editorialmente inútil. En ese caso no debe calificarse como suficiente.

### 5. Cobertura de materiales

Cada material seleccionado debe contar con análisis suficiente.

La auditoría debe comprobar que:

- todos los materiales seleccionados fueron analizados;
- ningún material seleccionado depende exclusivamente de afinidad temática;
- los materiales no analizados fueron excluidos;
- las exclusiones están justificadas;
- no existe una selección apoyada en conocimiento no documentado.

### 6. Curación por función

La curación debe demostrar qué función cumple cada material.

Posibles funciones, sin convertirlas en plantilla obligatoria:

- reconocimiento;
- ejemplificación;
- contradicción;
- complicación;
- contraste;
- ampliación histórica;
- dimensión institucional;
- consecuencia;
- clímax;
- síntesis;
- límite de la tesis.

No basta indicar:

```text
Material 1 aporta una perspectiva.
Material 2 aporta otra perspectiva.
```

Debe explicarse qué aporta cada uno y por qué sería una pérdida retirarlo.

### 7. Contraste, complementariedad y progresión

Cuando exista más de un material seleccionado, la auditoría debe comprobar:

- diferencias sustantivas;
- complementariedad;
- tensión o contraste;
- no sustituibilidad;
- razón del orden;
- evolución de la comprensión.

Debe poder responder:

```text
¿Qué permite entender el segundo material
que no podía entenderse solo con el primero?
```

y:

```text
¿Por qué este orden produce una progresión
mejor que un orden alternativo?
```

La cantidad de materiales es variable. No se exige un número fijo.

### 8. Gestión de redundancia y coste de contexto

Debe comprobar:

- si dos materiales cumplen la misma función;
- si el solapamiento está realmente justificado;
- si el contexto necesario consume más espacio del valor que aporta;
- si una obra exige una explicación desproporcionada;
- si eliminar un material mejora claridad sin perder profundidad.

La redundancia no se justifica afirmando únicamente:

```text
El solapamiento es útil.
```

Debe explicarse qué diferencia concreta conserva cada material.

### 9. Refinamiento sustantivo de la tesis

La tesis refinada debe ser funcionalmente distinta de:

```text
hipótesis inicial
tesis provisional
```

No siempre necesita una redacción completamente diferente, pero debe demostrar qué ocurrió después del análisis y la curación.

Debe registrar:

- qué se confirmó;
- qué cambió;
- qué se descartó;
- qué se limitó;
- qué aumentó o redujo su grado de certeza;
- qué objeción se volvió relevante;
- qué interpretación rival permanece viable;
- qué materiales provocaron cada cambio.

### 10. Calidad argumentativa de la tesis

La tesis refinada debe:

- responder a la pregunta central;
- adoptar una posición específica;
- ser defendible;
- evitar obviedades;
- poder sostener el episodio previsto;
- estar abierta a revisión;
- integrar evidencia favorable y adversa;
- incluir matiz y límites;
- orientar decisiones de B5-I3.

No es suficiente:

```text
El contexto influye en las personas.
Cada caso es diferente.
Puede haber excepciones.
```

### 11. Contribución de los materiales a la tesis

Debe existir correspondencia explícita entre:

```text
material seleccionado
→ hallazgo
→ función narrativa
→ contribución a la tesis refinada
```

La auditoría debe comprobar:

- que cada aporte sea específico;
- que no existan contribuciones inventadas;
- que las referencias correspondan;
- que la tesis no dependa de materiales excluidos;
- que ningún material seleccionado resulte decorativo.

### 12. Propagación de restricciones

Debe comprobar que las restricciones heredadas de B5-I1 lleguen a:

```text
NarrativeHumanAnalysis
MaterialCuration
RefinedThesis
```

Debe revisar especialmente:

- acceso indirecto;
- análisis prohibidos;
- claims excluidos;
- disclosures;
- límites de generalización;
- incertidumbre;
- fuentes no autorizadas como evidencia principal.

No basta conservar el identificador de una restricción. Debe comprobarse su aplicación operativa.

### 13. Promesa editorial interna

La skill puede evaluar la promesa editorial interna entendida como:

> La obligación intelectual, narrativa o humana que el episodio debe cumplir mediante su desarrollo.

Debe comprobar que:

- deriva de la pregunta y la tesis;
- es demostrable con la evidencia;
- no promete una certeza inexistente;
- no exige conclusiones que la investigación no sostiene;
- puede gobernar la futura apertura y el desarrollo.

No debe decidir audiencia concreta, título o miniatura.

### 14. Interfaz honesta con `YOUTUBE_ADAPTATION`

Cuando exista `EarlyPackagingHypothesis`, la skill debe limitarse a comprobar:

- si la tesis puede sostener honestamente la promesa;
- si existe evidencia suficiente;
- si la formulación exigiría deformar el análisis;
- si hay riesgo de que el contenido no entregue lo anunciado.

La salida debe ser una observación para `YOUTUBE_ADAPTATION`:

```text
FULFILLABLE
FULFILLABLE_WITH_LIMITS
NOT_FULFILLABLE
NOT_EVALUABLE
```

No constituye aprobación de packaging.

### 15. Preparación para B5-I3

B5-I2 estará editorialmente preparado para reauditoría cuando permita responder con claridad:

- qué tesis gobernará el episodio;
- qué materiales se utilizarán;
- por qué se utilizarán;
- qué aporta cada uno;
- qué progresión permiten;
- qué afirmaciones pueden realizarse;
- qué afirmaciones están prohibidas;
- qué límites deben conservarse;
- qué pregunta debe recorrer el episodio;
- qué tensión necesita resolver la arquitectura.

La skill no debe diseñar todavía esa arquitectura.

## Reglas de decisión

### `PASS`

Solo puede emitirse cuando:

- todos los criterios críticos estén evaluados;
- todos los criterios críticos sean satisfactorios;
- no existan defectos bloqueantes;
- todas las restricciones estén propagadas;
- las referencias sean trazables;
- análisis, curación y tesis sean sustantivos;
- el material esté listo para reauditoría funcional.

Salida:

```text
decision: PASS
readiness: READY_FOR_EDITORIAL_FUNCTIONAL_REVIEW
```

### `WARN`

Puede emitirse cuando:

- todos los criterios críticos son satisfactorios;
- existen defectos menores;
- las correcciones no modifican tesis, curación ni selección;
- B5-I3 no tendría que compensar carencias de B5-I2.

Ejemplos:

- redacción poco clara de una justificación ya demostrada;
- pequeño problema de organización;
- observación secundaria incompleta que no afecta la decisión.

Salida:

```text
decision: WARN
readiness: READY_FOR_EDITORIAL_FUNCTIONAL_REVIEW
```

### `FAIL`

Debe emitirse cuando los artefactos existen y pueden auditarse, pero presentan insuficiencia editorial corregible dentro de B5-I2.

Ejemplos:

- análisis genérico;
- material seleccionado sin análisis;
- curación redundante;
- tesis cosméticamente reformulada;
- evidencia desconectada de la afirmación;
- restricciones no aplicadas;
- ausencia de contraste;
- contribuciones decorativas.

Salida:

```text
decision: FAIL
readiness: NOT_READY_FOR_EDITORIAL_FUNCTIONAL_REVIEW
```

### `BLOCKED`

Debe emitirse cuando no sea posible realizar una auditoría válida.

Ejemplos:

- falta un artefacto obligatorio;
- existen versiones canónicas incompatibles;
- B5-I1 está sin cerrar;
- faltan las fuentes citadas;
- no se puede identificar qué materiales fueron seleccionados;
- la evidencia autorizada no está disponible;
- existe una dependencia externa no resuelta.

Salida:

```text
decision: BLOCKED
readiness: BLOCKED_BY_MISSING_INPUT
```

## Criterios críticos

Los siguientes criterios son críticos y no pueden quedar en `WARN`:

```text
ANALYSIS_SPECIFICITY
EVIDENCE_TRACEABILITY
EPISTEMIC_SEPARATION
MATERIAL_COVERAGE
CURATION_FUNCTION
CURATION_CONTRAST_AND_PROGRESSION
THESIS_REFINEMENT_SUBSTANCE
THESIS_ARGUMENTATIVE_QUALITY
MATERIAL_THESIS_CONTRIBUTION
INHERITED_RESTRICTIONS
B5_I3_READINESS
```

Un criterio crítico no satisfecho obliga a:

```text
FAIL
```

o:

```text
BLOCKED
```

según la causa.

## Defectos bloqueantes

- análisis intercambiable entre materiales;
- evidencia inexistente, huérfana o autorreferencial;
- interpretación presentada como hecho;
- material seleccionado sin análisis suficiente;
- curación final con candidatos sin resolver;
- dos o más materiales con la misma función sin justificación sustantiva;
- progresión meramente declarativa;
- tesis refinada sin cambio o confirmación demostrable;
- tesis basada en materiales excluidos;
- contraevidencia ignorada;
- objeción formularia que no tensiona la tesis;
- pérdida de restricciones heredadas;
- uso de un análisis prohibido por B5-I1;
- promesa editorial que la evidencia no puede cumplir;
- vacíos que B5-I3 tendría que resolver inventando decisiones editoriales.

## Evidencia exigida al auditor

Para declarar un criterio `SATISFIED`, el auditor debe incluir:

```text
artifact_ref
element_ref
quoted_or_paraphrased_evidence
specific_observation
why_it_satisfies_the_criterion
generic_alternative_rejected
```

La observación debe señalar qué elemento concreto demuestra suficiencia.

No es válido:

```text
Observación:
El análisis es específico.

Justificación:
Contiene detalles.

Alternativa rechazada:
Una alternativa genérica.
```

Sí es válido:

```text
Observación:
El hallazgo vincula la decisión de M1 de ocultar la deuda
en la escena S4 con su miedo a perder autoridad familiar;
después limita la interpretación al indicar que la escena
no demuestra por sí sola una causa estructural.

Razón:
Identifica sujeto, decisión, motivación inferida,
consecuencia, evidencia y límite.

Alternativa rechazada:
Decir únicamente que M1 actúa por miedo.
```

## Ejemplos positivos

### Análisis positivo

```text
La decisión del personaje de rechazar ayuda no demuestra
simplemente orgullo. En la escena identificada, acepta perder
el trabajo antes que admitir que no sabe resolver el problema.
Eso permite interpretar que su identidad depende de sentirse
autosuficiente. La lectura rival es que teme una sanción laboral,
y la evidencia disponible no permite descartar completamente
esa explicación.
```

### Curación positiva

```text
M1 introduce el conflicto desde la experiencia individual.
M2 muestra cómo la institución recompensa la conducta que daña
al protagonista. M3 contradice la idea de que el problema se
resuelve solo mediante voluntad personal.

El orden permite pasar de individuo a sistema y después
reformular la responsabilidad sin eliminarla.
```

### Tesis refinada positiva

```text
La tesis provisional atribuía el aislamiento principalmente
al miedo al rechazo. El análisis confirma ese miedo, pero la
curación demuestra que el entorno también recompensa la
autosuficiencia y castiga la vulnerabilidad.

La tesis refinada sostiene que el aislamiento nace de la
interacción entre protección personal y reconocimiento social,
no de una única causa individual.
```

## Ejemplos negativos

### Análisis negativo

```text
El personaje tiene miedo.
La sociedad influye en sus decisiones.
Otra lectura es posible.
Hay que tener en cuenta el contexto.
```

### Curación negativa

```text
M1 aporta una perspectiva.
M2 aporta otra.
Se colocan en ese orden porque primero va M1.
El solapamiento es útil.
```

### Tesis refinada negativa

```text
Tesis provisional:
El miedo influye en las personas.

Tesis refinada:
El miedo puede influir en las personas.

Cambio:
Se añade un matiz.

Objeción:
Puede haber excepciones.
```

### Auditoría negativa

```text
criterion: ANALYSIS_SPECIFICITY
result: SATISFIED
observation: El análisis es específico.
evidence_ref: analysis_01
```

## Límites funcionales

La skill:

- audita, pero no reescribe;
- identifica correcciones, pero no modifica artefactos;
- no selecciona materiales nuevos;
- no formula una tesis sustituta;
- no diseña el outline;
- no decide packaging;
- no altera el `EditorialProfile`;
- no convierte resultados en aprendizaje permanente;
- no autoriza B5-I3;
- no sustituye la decisión de `SCRIPT_PRODUCT`.

Cuando detecte un problema deberá indicar:

```text
problema
riesgo editorial
artefacto afectado
evidencia
comportamiento esperado
criterio verificable de corrección
```

No debe prescribir implementación técnica.

## Relación con B5-I2 y B5-I3

```text
B5-I2 produce:
análisis
→ curación
→ tesis refinada

skill_auditar_suficiencia_semantica_b5_i2:
evalúa si esos productos tienen sustancia real

`SCRIPT_PRODUCT`:
realiza reauditoría funcional

`YOUTUBE_ADAPTATION`:
audita su parte de packaging temprano

`INFRASTRUCTURE_GOVERNANCE`:
confirma cierre técnico y operativo

solo después:
puede considerarse la autorización de B5-I3
```

La skill no debe empezar a diseñar:

- recorrido del espectador;
- `OpeningDesign`;
- `ClosingDesign`;
- arquitectura;
- bloques;
- presupuesto;
- outline.

## Resultado esperado

```text
SCRIPT_PRODUCT_FUNCTIONAL_SPEC:
APPROVED_FOR_TECHNICAL_INTEGRATION

DEFINITIVE_SKILL_NAME:
skill_auditar_suficiencia_semantica_b5_i2

REUSE_skill_qa_editorial:
REJECTED_FOR_B5_I2

CANONICAL_ACTIVATION:
PENDING_TECHNICAL_IMPLEMENTATION_AND_SCRIPT_PRODUCT_AUDIT

B5_I3:
NOT_AUTHORIZED
```
