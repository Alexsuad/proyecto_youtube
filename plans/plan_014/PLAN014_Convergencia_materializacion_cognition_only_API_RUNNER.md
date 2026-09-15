# PLAN014 — Convergencia de materialización cognition-only API/RUNNER en Topic Belonging

**Versión del plan:** `0.1.0`
**Estado:** `CLOSED`
**Autoridad actual:** `OWNER_ACCEPTANCE: ACCEPTED`
**Alcance de esta intervención:** implementación funcional completada y cierre documental; no nuevas ejecuciones.

```text
PLAN014_CANONICAL_PATH: plans/plan_014/PLAN014_Convergencia_materializacion_cognition_only_API_RUNNER.md
PLAN014_STATUS: CLOSED
PLAN014_OWNER_AUTHORIZATION: YES
PLAN014_AUTHORITY_PREPARATION: CLOSED
PLAN014_FUNCTIONAL_IMPLEMENTATION: PASS
INDEPENDENT_AUDIT: PASS
OWNER_ACCEPTANCE: ACCEPTED
PLAN014_CLOSURE_EVIDENCE: proyecto_youtube_2026-09-15_02-11-37.zip
PLAN014_EXECUTION_AUTHORIZED: NO
PLAN014_PRODUCT_USE_AUTHORIZED: NO
CURRENT_PLAN: NONE
CURRENT_ACTIVITY: NONE
CURRENT_MISSION: NONE
CURRENT_MISSION_EXECUTION_BUNDLE: NONE
NEXT_ALLOWED_ACTION: NEW_OWNER_DECISION_AND_AUTHORIZATION_REQUIRED
EXECUTION_AUTHORIZED: NO
EXECUTION_AUTHORIZATION_SCOPE: NONE
REAL_AI_EXECUTION: NO
PRODUCT_USE_AUTHORIZED: NO
EXTEND_01: PRESERVED_AND_SUSPENDED_PENDING_NEW_OWNER_DECISION
```

## 1. Decisión de dirección

PLAN014 se crea como corrección técnica separada para un defecto demostrado en
la frontera de Topic Belonging. Esta preparación materializa únicamente el
plan y su bundle de autoridad. No cambia `src/`, `tests/`, `schemas/`,
`config/`, `prompts/` ni ningún artifact de producto, y no ejecuta providers,
IA, episodios ni el E2E funcional.

`EXTEND_01_M2_REAL_E2E` y sus contratos permanecen intactos como antecedente
preservado. Su continuación queda suspendida mientras PLAN014 se somete a
auditoría independiente y a una autorización funcional posterior.

## 2. Problema demostrado

El E2E mecánico público ejecutó la ruta:

```text
src.cli.main(["iniciar", ...])
→ execution_mode REAL
→ perfil deepseek_chat
→ ruta api_model
→ DeepSeekProvider contra pytest-httpserver en localhost
→ ENRICHMENT cognition-only
→ PRODUCER cognition-only
→ ASSESSMENT_INVALID
```

La evidencia previa demuestra que el transporte HTTP, `urllib.request`, la
resolución del perfil, la autorización temporal y la recepción de la salida
cognitiva funcionan sin Internet, API key real ni IA real. El primer fallo
real aparece después de una respuesta válida de
`topic_belonging_cognitive_assessment`: el workflow la valida directamente
como `topic_belonging_assessment`.

## 3. Causa raíz

La ruta API recibe correctamente una proyección cognitiva reducida. La ruta
RUNNER ya posee materializadores para convertir resultados cognitivos externos
en artifacts canónicos antes de validar y persistirlos, conceptualmente:

- `_materialize_producer_assessment(...)`;
- `_materialize_reviewer_decision(...)`.

La lógica existente está ligada al flujo de `import_result`, mientras la ruta
API directa devuelve cognition-only al workflow sin atravesar la misma frontera
de materialización. Por ello se mezclan dos contratos distintos:

```text
topic_belonging_cognitive_assessment ≠ topic_belonging_assessment
topic_belonging_cognitive_decision   ≠ topic_belonging_decision
```

El defecto no se corrige ampliando los schemas cognitivos ni haciendo que el
provider fabrique IDs, checksums o provenance.

## 4. Objetivo

Hacer converger API y RUNNER mediante una única materialización software-owned:

```text
                    cognitive result
                         │
         ┌───────────────┴───────────────┐
         │                               │
        API                            RUNNER
         │                               │
         └───────────────┬───────────────┘
                         ↓
              materialización común
                         ↓
              artifact canónico completo
                         ↓
                   validación
                         ↓
                    workflow
```

La implementación futura deberá mantener:

```text
SOFTWARE OWNS ORCHESTRATION AND MATERIALIZATION.
AI OWNS COGNITION ONLY.
```

## 5. Alcance de la preparación actual

La única escritura autorizada por esta misión es:

- `plans/001_CONTROL_OPERATIVO.md`;
- `plans/plan_014/`.

Dentro de `plans/plan_014/` se materializan este documento y los artifacts de
autoridad necesarios para resolver el bundle activo. No se crea
`run_configuration.json`: esta intervención no invoca el runtime y el
runtime vigente no requiere configuración de ejecución para materializar la
autoridad documental.

## 6. Alcance funcional futuro propuesto, no autorizado todavía

Una misión posterior, con autorización separada del OWNER, deberá autorizar de
forma exacta y no indiscriminada como mínimo:

- `src/application/topic_belonging.py`;
- `tests/harness/test_topic_belonging_http_e2e.py`;
- `tests/harness/test_plan009_m1_vertical.py`;
- `tests/harness/test_plan014_materialization.py` como prueba focal nueva, si
  la inspección final confirma que es el lugar más acotado.

La misión futura no deberá autorizar todo `src/` ni todo `tests/`. Su alcance
deberá limitarse a reutilizar o exponer la materialización canónica existente,
converger PRODUCER y REVIEWER, actualizar el test histórico desfasado y poner
verde el E2E sin cambiar schemas cognitivos.

## 7. Diseño de la corrección futura

### 7.1 PRODUCER

Para `topic_belonging_cognitive_assessment`, Software deberá ensamblar el
artifact `topic_belonging_assessment` a partir de la entrada canónica, el
perfil activo, el episodio, la identidad/rol/run de la ejecución y la
provenance disponible. Deberá generar y validar los campos técnicos requeridos
por el contrato actual, incluyendo IDs, bindings, checksums y provenance.

La validación `validate_assessment(...)` solo podrá ejecutarse después de esa
materialización. Un resultado cognitivo inválido o incompleto deberá bloquear
la materialización sin crear un artifact canónico parcial.

### 7.2 REVIEWER

La corrección deberá verificar la misma frontera para
`topic_belonging_cognitive_decision` y `topic_belonging_decision` si el E2E
reproduce el defecto. La decisión deberá quedar ligada al assessment canónico,
con reviewer actor/role/run, profile binding, checksums y provenance
software-owned. La independencia `PRODUCER ≠ REVIEWER` es obligatoria.

### 7.3 Convergencia con RUNNER

La implementación deberá reutilizar los materializadores existentes o extraer
una función común mínima. No se deben crear dos implementaciones paralelas
`materialize_api_assessment()` y `materialize_runner_assessment()` con lógica
duplicada. El comportamiento ya verificado de `import_result` debe conservarse.

ENRICHMENT queda fuera del refactor salvo que una extracción común estrictamente
necesaria lo afecte sin cambiar su comportamiento.

## 8. Propiedad de los campos

El fake cognitivo solo podrá suministrar razonamiento y decisiones cognitivas:

- propuesta de ángulo, territorio, evidencia y triggers;
- evaluación cognitiva;
- decisión cognitiva.

Software deberá suministrar y vincular:

- IDs de artifacts;
- run IDs y actor/role bindings;
- profile bindings;
- checksums y manifests;
- provenance técnica;
- bindings de entrada/salida;
- timestamps técnicos;
- lineage;
- estado de workflow y gate.

`SOFTWARE_OWNED_FIELDS_SUPPLIED_BY_FAKE` debe ser `NO`.

## 9. Pruebas previstas para la implementación posterior

La misión funcional futura deberá añadir solo pruebas focales suficientes para
demostrar:

1. assessment cognition-only válido → assessment canónico válido;
2. campos software-owned generados desde Software/contexto;
3. decision cognition-only válida → decision canónica válida;
4. resultado cognitivo inválido → no se materializa artifact canónico;
5. RUNNER conserva el comportamiento previo tras la extracción común;
6. el E2E público usa exactamente tres requests HTTP y despacha por el
   contrato real (`stage` y schema de salida), no por contador.

El servidor fake deberá reconocer exactamente:

```text
ENRICHMENT + topic_belonging_cognitive_proposal
PRODUCER   + topic_belonging_cognitive_assessment
REVIEWER   + topic_belonging_cognitive_decision
```

Con `REQUEST_MORE_EVIDENCE`, el workflow esperado es
`TOPIC_BELONGING_TECHNICAL_STOP`, sin Research ni downstream.

## 10. Invariantes y límites

- No ampliar schemas cognitivos con campos técnicos.
- No debilitar validators ni eliminar provenance.
- No generar placeholders silenciosos para campos indispensables.
- No conectar DeepSeek real, Internet, `YT_VAULT` ni uso productivo.
- No iniciar Research, Writing, Editor, auditoría final, packaging o
  publicación.
- `is_real_editorial_execution` no se usará como evidencia de IA real; la
  preparación mantiene `REAL_AI_EXECUTION: NO`.
- Los cambios y artifacts de EXTEND-01 quedan preservados y no se reinterpretan
  ni se ejecutan.

## 11. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Materialización API divergente de RUNNER | Reutilizar el materializador canónico y probar ambos caminos. |
| IA suministra campos técnicos | Validar schemas cognitivos estrictos y rechazar campos reservados. |
| Assessment o decision parcial | Fallar cerrado antes de persistir el artifact canónico. |
| Pérdida de independencia | Generar bindings separados para PRODUCER y REVIEWER y verificar runs distintos. |
| Cambio accidental de autoridad | Hash de live state, autoridad, autorización y contrato; scope solo documental. |
| Ampliación a downstream | Gate final y asserts de ausencia de artifacts posteriores. |

## 12. Criterios PASS de la implementación futura

```text
PRODUCTION_FIX_MINIMAL = YES
API_AND_RUNNER_MATERIALIZATION_CONVERGED = YES
COGNITIVE_SCHEMAS_CHANGED = NO
CANONICAL_SCHEMAS_CHANGED = NO
VALIDATORS_WEAKENED = NO
PRODUCER_CANONICAL_MATERIALIZATION = PASS
REVIEWER_CANONICAL_MATERIALIZATION = PASS
PRODUCER_REVIEWER_INDEPENDENCE = PASS
HTTP_CALL_COUNT = 3
HTTP_STAGE_ORDER = ENRICHMENT,PRODUCER,REVIEWER
HTTP_SCHEMA_ORDER = topic_belonging_cognitive_proposal,topic_belonging_cognitive_assessment,topic_belonging_cognitive_decision
SOFTWARE_OWNED_FIELDS_SUPPLIED_BY_FAKE = NO
WORKFLOW_FINAL_STATUS = TOPIC_BELONGING_TECHNICAL_STOP
DOWNSTREAM_EXECUTION_STARTED = NO
REAL_API_KEY_USED = NO
INTERNET_USED = NO
REAL_AI_USED = NO
YT_VAULT_MODIFIED = NO
RUNTIME_RESIDUE = NONE
```

## 13. STOP conditions

Detener la misión funcional y reportar `BLOCKED` si la corrección exige:

- cambiar schemas cognitivos o canónicos;
- debilitar validators o guards;
- rediseñar el workflow o los contratos entre etapas;
- modificar Research/downstream;
- alterar gobernanza o autoridad viva fuera del bundle aprobado;
- introducir un segundo sistema de materialización duplicado;
- usar provider real, Internet, API key real o `YT_VAULT`.

El primer fallo deberá reportar capa, etapa, causa, esperado, observado y
cambio arquitectónico requerido, sin ampliar el alcance.

## 14. Auditoría y secuencia de autoridad

La preparación de autoridad se materializa ahora bajo
`PLAN014_AUTHORITY_PREPARATION`. Antes de cualquier implementación funcional
se requiere:

1. revisión de coherencia del plan y del bundle;
2. auditoría independiente del alcance y de los bindings;
3. autorización separada del OWNER para `PLAN014_FUNCTIONAL_IMPLEMENTATION`;
4. ejecución de la misión funcional únicamente dentro de su allowlist;
5. validación focal, regresiones afectadas y auditoría independiente.

El cierre de esta preparación no autoriza providers, IA real, uso productivo,
commit ni push.

## 15. Cierre formal

El alcance técnico de este documento se conserva como referencia de diseño y
evidencia. La implementación funcional fue completada y aceptada por el
OWNER, con auditoría independiente PASS.

```text
PLAN014_STATUS: CLOSED
PLAN014_FUNCTIONAL_IMPLEMENTATION: PASS
INDEPENDENT_AUDIT: PASS
OWNER_ACCEPTANCE: ACCEPTED
PLAN014_CLOSURE_EVIDENCE: proyecto_youtube_2026-09-15_02-11-37.zip
CURRENT_PLAN: NONE
CURRENT_ACTIVITY: NONE
CURRENT_MISSION: NONE
CURRENT_MISSION_EXECUTION_BUNDLE: NONE
EXECUTION_AUTHORIZED: NO
REAL_AI_EXECUTION: NO
PRODUCT_USE_AUTHORIZED: NO
NEXT_ALLOWED_ACTION: NEW_OWNER_DECISION_AND_AUTHORIZATION_REQUIRED
```
