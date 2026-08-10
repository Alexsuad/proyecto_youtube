# PLAN 004 — Hardening transversal de harness, capabilities, contexto y calidad

**PLAN_ID:** `PLAN_004`
**CANONICAL_PATH:** `plans/plan_004/004_hardening_transversal_harness_capabilities_contexto_calidad.md`
**DOCUMENT_ID:** `TECHNICAL_HARDENING_TH01_TH08`
**DOCUMENT_TYPE:** `TRANSVERSAL_TECHNICAL_HARDENING_PLAN`
**PLAN_RECTOR:** `PLAN_001`
**PLAN_004_ROLE:** `TRANSVERSAL_HARDENING_GOVERNANCE_PLAN`
**RELATION_TO_PLAN_001:** `SUBORDINATE_SUPPORTING_PLAN`
**LIVE_STATE_AUTHORITY:** `plans/001_CONTROL_OPERATIVO.md`
**ARCHITECTURAL_SPECIFICATION:** `plans/plan_001/TRANSVERSAL_CAPABILITY_GOVERNANCE.md`
**SCOPE:** `TH-01` → `TH-08` + `HARDENING_COMPLETION_REVIEW`
**IMPLEMENTATION_AUTHORIZED_BY_THIS_DOCUMENT:** `NO`
**CURRENT_LIVE_STATE_CHANGED_BY_THIS_DOCUMENT:** `NO`
**STATUS:** `OPERATIVE_PLAN_READY_FOR_REPOSITORY`

> Este documento define el alcance operativo del bloque de hardening transversal. No sustituye el estado vivo, no autoriza por sí mismo una misión y no modifica criterios funcionales de `CHANNEL_INTELLIGENCE`, `SCRIPT_PRODUCT` o `YOUTUBE_ADAPTATION`.

---

## 1. Propósito

Convertir el repositorio en un sistema agéntico portable capaz de:

```text
producir
→ verificar
→ auditar
→ detectar defectos
→ identificar causa raíz
→ reparar en la fuente correcta
→ invalidar dependencias afectadas
→ revalidar
→ demostrar evidencia
→ escalar solamente decisiones que requieren autoridad
```

El objetivo no es aumentar el número de agentes, sino reducir dependencia de revisión manual y lograr que la mayor cantidad posible de controles sea verificable por el propio harness.

El hardening debe preservar:

- portabilidad;
- neutralidad de proveedor;
- autoridad funcional separada de ejecución técnica;
- estado vivo único;
- evidencia verificable;
- mínimo contexto suficiente;
- mínimo número necesario de agentes;
- separación productor/revisor;
- posibilidad de auto-test, auto-audit y reparación controlada;
- prohibición de autoaprobación.

---

## 2. Autoridades y precedencia

La precedencia obligatoria es:

```text
1. plans/001_CONTROL_OPERATIVO.md
2. autoridad funcional aprobada aplicable
3. TRANSVERSAL_CAPABILITY_GOVERNANCE.md
4. este plan operativo TH-01 → TH-08
5. misión concreta autorizada
6. evidencia derivada de ejecución
```

Ante contradicción:

```text
STOP
→ no inferir
→ registrar contradicción
→ escalar a la autoridad competente
```

Este documento nunca puede abrir una misión ni declarar `IMPLEMENTATION_AUTHORIZED`.

---

## 3. Estado y autorización

Este plan no contiene estados operativos actuales. La misión vigente, la autorización de
implementación, el estado de cada TH, la siguiente acción permitida y cualquier decisión
de apertura o cierre se leen exclusivamente desde `plans/001_CONTROL_OPERATIVO.md`.

PLAN 004 no puede autorizarse a sí mismo, modificar la autoridad viva, abrir una TH
posterior por inferencia ni convertir evidencia técnica en aprobación funcional. Las
referencias a TH-01, TH-02 y TH-03 en este documento describen contexto técnico,
dependencias y evidencia que debe conservarse; no duplican su estado mutable.

---

## 4. Principios transversales obligatorios

### 4.1 Deterministic-first

```text
IF DETERMINISTICALLY VERIFIABLE
→ DO NOT SPEND LLM TOKENS TO DECIDE IT
```

Usar determinismo para:

- schemas;
- checksums;
- paths;
- scope;
- Git diff/status;
- tests;
- AST/syntax;
- lint;
- coverage;
- complejidad;
- CRAP;
- mutation testing;
- dependency graphs;
- provenance;
- authorization;
- replay;
- invalidation;
- context resolution;
- gates.

Usar IA para:

- investigación;
- diseño;
- diagnóstico;
- interpretación;
- análisis semántico;
- root cause no trivial;
- revisión adversarial;
- evaluación especialista;
- decisiones ambiguas.

### 4.2 Minimum necessary agentic complexity

No asumir:

```text
more agents = better system
```

Usar un solo agente cuando sea suficiente. Multiagente únicamente cuando aporte al menos una de estas propiedades:

- independencia;
- especialización real;
- revisión adversarial;
- aislamiento;
- paralelismo útil;
- reducción demostrable de riesgo o tiempo.

### 4.3 Portabilidad

Nunca convertir en autoridad canónica ni dependencia obligatoria a:

```text
Codex
OpenCode
ChatGPT
Claude Code
Antigravity
un proveedor
un modelo
un IDE
```

Son ejecutores/adaptadores sustituibles.

La arquitectura canónica se expresa mediante:

```text
domain
capability
role
contract
policy
rubric
execution_profile
execution_interface
mission
authorization
evidence
provenance
gate
```

### 4.4 No autoaprobación

Ningún ejecutor puede:

```text
modify acceptance rule
+
approve own modification
```

Una modificación sensible de detector, gate, threshold, rubric, policy, requirement o expected output debe pasar por `RepairIntegrity` y por la autoridad competente aplicable.

### 4.5 Estado vivo describe realidad

```text
STATE MUST DESCRIBE OBSERVED REALITY
NOT DESIRED REALITY
```

No promover estados por intención, por respuesta textual del agente ni por simple existencia de código.

---

## 5. Método operativo para cada TH

Cada TH es una misión independiente.

```text
OWNER_AUTHORIZATION
      ↓
MISSION_PREFLIGHT
      ↓
IMPLEMENTATION
      ↓
DETERMINISTIC_VALIDATION
      ↓
INDEPENDENT_REVIEW
      ↓
OWNER_CLOSURE
      ↓
LIVE_STATE_UPDATE
      ↓
NEXT_MISSION_AUTHORIZATION
```

No se autoriza `TH-(n+1)` por inferencia.

Cada misión TH debe materializar, antes de implementar, este contrato mínimo:

```text
MISSION_ID
OBJECTIVE
PRECONDITIONS
CANONICAL_INPUTS
AUTHORIZED_SCOPE
ALLOWED_FILE_FAMILIES
PROTECTED_FILES
NON_OBJECTIVES
EXPECTED_OUTPUTS
DETERMINISTIC_VALIDATIONS
ADVERSARIAL_CASES
STOP_CONDITIONS
REVIEW_REQUIREMENTS
OWNER_CLOSURE_REQUIREMENTS
```

Un `PASS` textual del ejecutor nunca constituye evidencia suficiente. Los hechos
verificables deben provenir de Git, archivos, tests, validadores, scripts o artefactos
estructurados. La misión debe detenerse si el alcance no es resoluble o si una
autoridad canónica externa contradice materialmente la especificación sin una
resolución ya definida por la jerarquía del repositorio.

### 5.1 Preflight obligatorio

Antes de escribir:

- leer `AGENTS.md`;
- leer `plans/001_CONTROL_OPERATIVO.md`;
- verificar misión autorizada;
- reconciliar Git real;
- identificar cambios preexistentes;
- identificar paths autorizados/protegidos;
- comprobar dependencias y estado previo;
- detenerse si el alcance no es resoluble.

### 5.2 Paralelismo controlado

Cuando el trabajo lo permita:

```text
IMPLEMENTER
WRITE / isolated worktree

        + EN PARALELO

REVIEWER
READ_ONLY / independent context
```

El auditor paralelo no modifica la implementación y debe buscar antes del cierre:

- bypasses;
- duplicaciones;
- inconsistencias;
- casos negativos faltantes;
- contaminación entre capas;
- autoridad irresoluble;
- requisitos adelantados de otra TH.

No ejecutar en paralelo dos implementaciones dependientes sobre el mismo alcance si una consume decisiones todavía no estabilizadas de la otra.

### 5.3 Skills de ingeniería disponibles

Los procedimientos generales de ingeniería viven separados de las skills productivas/editoriales.

```text
.agent/skills/
→ producto/editorial

.agents/skills/
→ procedimientos generales de ingeniería
```

Para este bloque pueden utilizarse, según aplicabilidad:

- `preparar-paquete-ejecucion-tecnica`;
- `auditar-trazabilidad-input-output`;
- `evidencia-proporcional-git`;
- `verificar-no-mezcla-de-capas`;
- `harness-determinista`.

Estas skills guían el proceso; no sustituyen gates, scripts, schemas ni contratos deterministas existentes.

### 5.4 Evidencia mínima

Cada misión debe dejar evidencia verificable de:

- autorización;
- scope autorizado;
- inputs;
- paths modificados;
- diff;
- tests;
- gates;
- findings;
- limitaciones pendientes;
- provenance cuando aplique.

No aceptar un simple `PASS` declarado por el agente.

---

# TH-01 — Reconciliación de realidad

## 6. Objetivo

Garantizar que el estado vivo representa la realidad observada del repositorio.

Separar:

```text
WHAT CONTROL SAYS
vs
WHAT REPOSITORY SHOWS
```

## 6.1 Entrega

- reconciliación de estado;
- contaminación real observada;
- bloqueos reales;
- siguiente acción permitida basada en evidencia.

## 6.2 Criterio de cierre

El estado vivo coincide con la realidad observada, aunque esa realidad sea `FAIL`, `BLOCKED` o incompleta.

## 6.3 Relación con el estado vivo

El resultado y el cierre de TH-01 se leen exclusivamente desde la autoridad viva.
Esta sección conserva el criterio técnico de cierre, no un estado operativo.

---

# TH-02 — Neutralidad y contaminación

## 7. Objetivo

Eliminar dependencia canónica de equipos históricos, proveedor, agente de desarrollo o implementación particular.

## 7.1 Clasificación requerida

```text
ACTIVE_PRODUCT_CONTAMINATION
OPTIONAL_ADAPTER
ADAPTER_TEST
NEGATIVE_ASSERTION
HISTORICAL_REFERENCE
OPERATIONAL_METADATA
```

Debe distinguirse:

```text
HISTORICAL_ARTIFACT
!=
HISTORICAL_SECTION_INSIDE_LIVE_AUTHORITY
```

## 7.2 Criterio de cierre

- contaminación activa corregida;
- adaptadores legítimos preservados;
- tests negativos/históricos no confundidos con runtime;
- neutralidad de proveedor demostrada.

## 7.3 Relación con el estado vivo

El resultado y el cierre de TH-02 se leen exclusivamente desde la autoridad viva.
Esta sección conserva el criterio técnico de cierre, no un estado operativo.

---

# TH-03 — Integridad verificable de reparación

## 8. Objetivo

Impedir reparaciones cosméticas y demostrar reparación en la causa correcta.

```text
FINDING
→ ROOT CAUSE
→ SOURCE ARTIFACT
→ REPAIR AT SOURCE
→ DOWNSTREAM IMPACT
→ INVALIDATION
→ REVALIDATION
→ DETECTOR IMPACT
→ REGRESSION
→ INDEPENDENT REVIEW
```

## 8.1 Profundidad

```text
L0_PRESENTATION
L1_OUTPUT
L2_STRUCTURE
L3_DECISION
L4_EVIDENCE
L5_REQUIREMENT_OR_POLICY
```

Regla:

```text
repair_depth >= root_cause_depth
```

## 8.2 Authorized write scope

El manifest real del reviewer/repair debe derivarse del scope autorizado de escritura y detectar modificaciones incluso en paths autorizados pero no declarados como input/output.

## 8.3 L5 y autoridad competente

TH-03 ya exige separación entre:

```text
GOVERNANCE_APPROVAL
→ aprobación funcional/normativa

MISSION_AUTHORIZATION
→ permiso de ejecución técnica
```

La aprobación L5 debe vincular:

- requirement;
- artefacto exacto;
- versión;
- checksum;
- autoridad competente resoluble desde la gobernanza canónica de capabilities;
- decisión válida.

Una `authority_identity` arbitraria no es suficiente.

## 8.4 Criterio de cierre

- manifest desde authorized scope;
- side effects detectables;
- root cause/repair depth consistente;
- detector integrity;
- anti-compensating patches;
- reviewer independiente;
- L5 authority competence verificada;
- regresiones adversariales satisfactorias.

## 8.5 Relación con el estado vivo

El resultado y el cierre de TH-03 se leen exclusivamente desde la autoridad viva.
Esta sección conserva la evidencia y el criterio técnico de cierre, no un estado
operativo ni una aprobación duplicada.

---

# TH-04 — Inventario canónico de capabilities ejecutables

## 9. Objetivo

Responder de forma cerrada y verificable:

> ¿Qué elementos del repositorio son realmente capabilities ejecutables y cuáles no?

TH-04 es **inventario y clasificación**, no activación, no rediseño general de registries y no context engineering.

## 9.1 Precondiciones

TH-04 solo puede comenzar cuando `001_CONTROL_OPERATIVO.md` indique explícitamente una misión TH-04 autorizada.

Debe existir:

- registry canónico de capabilities actual;
- responsibility registry y artefactos relacionados disponibles;
- estado Git reconciliado;
- un `CAPABILITY_DISCOVERY_SCOPE` congelado antes del descubrimiento.

## 9.2 Universo auditable

Separar explícitamente:

```text
CAPABILITY_DISCOVERY_SCOPE
→ entradas y reglas congeladas de búsqueda

CAPABILITY_AUDIT_UNIVERSE
→ resultado completo y reproducible del descubrimiento

CAPABILITY_REGISTRY_DELTA_PROPOSAL
→ diferencias propuestas contra el registry canónico
```

Los seeds primarios autorizados son exclusivamente:

```text
config/capability_registry.json
config/responsibility_registry.json
config/agent_prompt_registry.json
config/agent_execution_profiles.json
config/subagent_registry.json
config/capability_routing.yaml
config/skill_catalog.json
```

`schemas/`, `src/`, `src/scripts/`, `prompts/`, `.agent/skills/` y `.agents/skills/`
son roots resolubles únicamente cuando exista una referencia explícita alcanzable
desde un seed. Está prohibido escanearlos recursivamente para inferir capabilities.
`.agents/skills/` representa tooling de ingeniería y no constituye automáticamente
una capability productiva.

El algoritmo obligatorio es:

1. cargar y validar los seeds autorizados;
2. extraer identificadores y referencias explícitas;
3. resolver únicamente artefactos referenciados;
4. normalizar identificadores solo para comparación;
5. conservar siempre los identificadores originales;
6. detectar aliases;
7. deduplicar mediante evidencia;
8. registrar conflictos sin resolverlos silenciosamente;
9. clasificar todos los candidatos;
10. cerrar el universo cuando todos estén clasificados o marcados `UNRESOLVED`.

El universo es evidencia derivada y no constituye una nueva fuente de verdad.

Cada candidato debe incluir, como mínimo:

```text
candidate_id
source_type
source_ref
current_registry_presence
canonical_identity
observed_role_ref
observed_prompt_ref
observed_profile_ref
observed_route_ref
observed_contract_ref
observed_implementation_ref
observed_tests
object_class
disposition
registry_state
classification_reason
owner_resolution
maturity_observed
inconsistencies
evidence_refs
```

## 9.3 Criterio de registrabilidad

Una capability merece identidad propia únicamente cuando posee evidencia suficiente de:

1. identidad funcional estable;
2. owner/authority identificable;
3. decisión, transformación o evaluación acotada;
4. inputs identificables;
5. outputs identificables;
6. participación actual o planificada en ejecución/routing/gate;
7. necesidad de maturity/evidence independiente.

No convertir automáticamente en capability:

- cada script;
- cada función Python;
- cada policy;
- cada gate;
- cada actividad textual;
- cada utilidad;
- cada responsabilidad descriptiva.

## 9.4 Clasificación obligatoria

Cada candidato recibe exactamente un valor por dimensión:

```text
OBJECT_CLASS:
  EXECUTABLE_CAPABILITY
  NON_EXECUTABLE_RESPONSIBILITY
  POLICY
  GATE
  UTILITY
  ORCHESTRATION_ONLY
  UNRESOLVED_CANDIDATE

DISPOSITION:
  CURRENT
  DEFERRED
  DUPLICATE
  OBSOLETE

REGISTRY_STATE:
  REGISTERED
  UNREGISTERED
  NOT_OBSERVED
  UNRESOLVED
  CONFLICTING
```

Toda exclusión de `EXECUTABLE_CAPABILITY`, disposición no `CURRENT` o estado no
`REGISTERED` debe tener razón y evidencia verificables.

## 9.5 Registry

Mantener un único registry canónico.

Prohibido crear, salvo necesidad arquitectónica demostrada y autorización separada:

```text
capability_registry_v2
new_capability_registry
runtime_capabilities
parallel_capability_registry
```

Durante TH-04 `config/capability_registry.json` es `READ_ONLY`. Cualquier diferencia
se entrega únicamente en:

`reports/implementation/plan_004/TH04_registry_delta_proposal.json`

Las únicas operaciones permitidas en la propuesta son:

```text
ADD
CORRECT_METADATA
ADD_ALIAS
MERGE_CANDIDATE
DEPRECATE_CANDIDATE
NO_CHANGE
```

Quedan prohibidas:

```text
ACTIVATE
FUNCTIONALLY_APPROVE
PROMOTE_TO_DEMONSTRATED
CHANGE_FUNCTIONAL_AUTHORITY
```

## 9.6 Maturity

Conservar exactamente:

```text
DEFINED
REGISTERED
IMPLEMENTED
DEMONSTRATED
```

No introducir otra escala.

Separar siempre:

```text
maturity
availability
technical_assurance
semantic_assurance
operational_demonstration
functional_approval
```

No inferir una dimensión desde otra.

## 9.7 Owner/authority

TH-04 debe observar para cada capability, cuando exista:

```text
capability
→ functional_authority_domain
→ decision_authority / owner
```

TH-04 no inventa autoridad funcional nueva.

Los únicos resultados de la observación de autoridad son:

```text
RESOLVED_FROM_CANONICAL_FIELD
UNRESOLVED
CONFLICTING_CLAIMS
```

Si no puede resolverse:

```text
CAP_OWNER_UNRESOLVED
```

o el finding equivalente canónico existente.

La formalización transversal requirement/policy → competent authority pertenece a TH-05 salvo las relaciones ya existentes necesarias para validar la capability observada.

## 9.8 Casos adversariales mínimos

La implementación/tests de TH-04 deben cubrir, cuando apliquen:

- candidato presente solo como nombre textual;
- script utilitario confundido con capability;
- gate confundido con capability;
- capability duplicada bajo dos nombres;
- capability registrada sin implementation real;
- capability implementada sin registry;
- owner irresoluble;
- maturity declarada superior a evidencia observada;
- capability futura/deferred tratada erróneamente como activa;
- referencias específicas de proveedor tratadas como capability canónica.

## 9.9 Entregables

TH-04 debe producir:

```text
reports/implementation/plan_004/TH04_capability_discovery_scope.json
reports/implementation/plan_004/TH04_capability_audit_universe.json
reports/implementation/plan_004/TH04_registry_delta_proposal.json
schemas/capability_audit_universe.json
```

Los artefactos deben contener el envelope común definido en §9.12.

## 9.10 No objetivos

TH-04 NO debe:

- formalizar todavía toda la integridad cross-registry;
- rediseñar roles/prompts/profiles;
- implementar ContextReference;
- implementar handoffs;
- abrir TH-05;
- activar capabilities;
- modificar criterios funcionales;
- tocar R1-M4.

## 9.11 Criterios de aceptación

TH-04 puede proponerse para owner review solo si:

1. el universo auditable está cerrado y reproducible;
2. cada candidato está clasificado;
3. cada exclusión tiene razón;
4. no existe segundo registry canónico;
5. maturity usa únicamente los cuatro estados existentes;
6. capabilities ejecutables tienen evidencia suficiente de identidad/inputs/outputs/participación;
7. la observación de owner/authority se resuelve desde un campo canónico o queda explícitamente unresolved; la competencia funcional permanece reservada a TH-05;
8. los tests adversariales relevantes pasan;
9. el diff queda dentro del scope autorizado;
10. no se activó ninguna capability;
11. auditor independiente no identifica bypass material abierto.

## 9.12 Envelope machine-readable común

Todo artefacto estructurado de PLAN 004 debe incluir como mínimo:

```text
schema_version
plan_id
mission_id
repository_revision
generated_at
source_inputs
evidence_refs
limitations
result
```

Cada TH añade sus campos específicos. Los schemas y reports definidos como entregables
futuros pertenecen a sus respectivas misiones; esta especificación no los crea ni los
convierte en una segunda fuente de autoridad.

---

# TH-05 — Coherencia cross-registry y autoridad

## 10. Objetivo

Garantizar que cada capability ejecutable tenga referencias coherentes y autoridad competente resoluble en los sistemas donde dicha referencia sea aplicable.

```text
CAPABILITY
↔ OWNER/AUTHORITY
↔ ROLE
↔ PROMPT
↔ EXECUTION_PROFILE
↔ CONTRACT
↔ ROUTING
↔ REQUIREMENT/POLICY
↔ ASSURANCE
```

## 10.1 Precondición

TH-04 debe estar cerrado por owner.

## 10.2 Regla de aplicabilidad maturity-aware

No exigir el mismo conjunto de referencias a todas las capabilities.

Ejemplos:

```text
DEFINED
→ puede no tener runtime/prompt/route

SEMANTIC + IMPLEMENTED
→ puede requerir role + prompt + execution profile

DETERMINISTIC + IMPLEMENTED
→ puede requerir implementation + contracts + dependencies
→ no necesariamente prompt
```

La validación debe distinguir `not applicable` de `missing`.

## 10.3 Authority mapping

Formalizar/reutilizar la relación canónica necesaria para responder:

```text
WHO MAY APPROVE THIS REQUIREMENT / POLICY / CAPABILITY CHANGE?
```

La competencia funcional solo puede resolverse desde:

```text
config/capability_registry.json
config/responsibility_registry.json
```

y las referencias canónicas que esos documentos declaren. No inferir competencia por
nombre de role, prompt, dominio textual, nombre de equipo, nombre de modelo o identidad
aparente del ejecutor. Si no existe una relación verificable, el resultado debe ser:

```text
AUTHORITY_RESOLUTION: UNRESOLVED
```

Los estados permitidos son:

```text
RESOLVED
UNRESOLVED
CONFLICTING
```

No aceptar identidad autodeclarada sin competencia verificable.

No crear un registry de autoridad duplicado si la relación puede resolverse mediante registries existentes.

## 10.4 Routing

Routing responde únicamente:

```text
HOW TO EXECUTE
```

No decide:

```text
maturity
availability
functional approval
mission authorization
```

## 10.5 Gate esperado

Extender/reutilizar el gate canónico correspondiente para detectar según aplicabilidad:

```text
CAP_OWNER_UNRESOLVED
CAP_REQUIREMENT_REF_UNRESOLVED
CAP_IMPLEMENTATION_REF_MISSING
ROLE_UNRESOLVED
PROMPT_UNRESOLVED
PROFILE_UNRESOLVED
CONTRACT_UNRESOLVED
ROUTE_UNRESOLVED
AUTHORITY_CONTRADICTION
MATURITY_REFERENCE_MISMATCH
```

No crear un segundo gate si uno existente puede ampliarse limpiamente.

## 10.6 Casos adversariales mínimos

- role de otra capability;
- prompt inexistente;
- execution profile de proveedor hardcodeado como autoridad;
- route válida pero capability no autorizada;
- owner declarado pero competente para otro dominio;
- requirement asociado a autoridad arbitraria;
- deterministic capability obligada erróneamente a tener prompt;
- `DEFINED` bloqueada por referencias solo requeridas en `IMPLEMENTED`.

## 10.7 Criterio de cierre

- relaciones aplicables resolubles;
- ausencia de segunda fuente de verdad;
- competencia de autoridad verificable;
- routing separado de approval/maturity;
- gate cross-registry operativo;
- casos adversariales satisfactorios;
- auditor independiente sin bypass material abierto.

Los entregables mínimos son:

```text
reports/implementation/plan_004/TH05_cross_registry_integrity.json
reports/implementation/plan_004/TH05_authority_resolution.json
```

Ambos deben usar el envelope común de §9.12.

---

# TH-06 — Context engineering y handoffs eficientes

## 11. Objetivo

Reducir contaminación, context drift, lecturas masivas, duplicación y tokens mediante contexto mínimo suficiente, resoluble y reproducible.

## 11.1 Precondición

TH-05 cerrado por owner.

## 11.2 Precedencia canónica

```text
NORMATIVE_CONTEXT
>
OWNER_AUTHORIZED_MISSION_SCOPE
>
CASE_INPUT
>
OPTIONAL_EVIDENCE
```

Una capa inferior nunca puede ampliar, contradecir ni anular una restricción superior.
Una capa superior puede limitar o invalidar información inferior. Los datos del caso
nunca adquieren autoridad normativa.

## 11.3 ContextReference

Cada referencia operacional debe poder expresar:

```text
class
path/ref
type
version
checksum
authority_domain
required
```

Clases:

```text
NORMATIVE
EVIDENTIARY
HISTORICAL
```

## 11.4 Resolución segura

Bloquear:

- absolute paths;
- drive-letter absolute paths;
- UNC paths;
- traversal;
- symlink escape;
- junction/reparse-point escape;
- required unresolved reference;
- checksum mismatch;
- root no autorizado.

Las referencias opcionales no resolubles deben quedar registradas, no desaparecer silenciosamente.

## 11.5 ResolvedContextManifest

Las ejecuciones semánticas relevantes deben registrar:

```text
what context was actually resolved and used
```

ligado a:

- mission;
- capability;
- role;
- profile;
- prompt;
- input/output;
- checksums;
- provenance.

## 11.6 Handoffs

Modos:

```text
REFERENCE_ONLY
INLINE_MINIMAL
SELF_CONTAINED
```

Preferencia:

```text
REFERENCE_ONLY
→ cuando el consumidor puede resolver referencias

INLINE_MINIMAL
→ cuando necesita material mínimo en línea

SELF_CONTAINED
→ solo cuando el consumidor legítimamente no puede resolver referencias
```

`SELF_CONTAINED` no es default.

## 11.7 Context budget

Registrar inicialmente de forma informativa:

```text
required_context_count
resolved_context_size
estimated_tokens
```

No imponer threshold arbitrario en TH-06.

## 11.8 Context escalation

El agente empieza con contexto mínimo y amplía solo por:

```text
contradiction
missing dependency
insufficient evidence
unresolved reference
```

No leer todo el repositorio “por si acaso”.

## 11.9 Casos adversariales mínimos

- absolute path;
- `../` traversal;
- symlink escape;
- checksum obsoleto;
- referencia normativa no resoluble;
- evidencia opcional ausente;
- case input intentando reemplazar normativa;
- handoff SELF_CONTAINED usado sin justificación;
- manifest que declara contexto distinto al realmente resuelto.

## 11.10 Criterio de cierre

- context resolution seguro;
- precedence verificable;
- ResolvedContextManifest reproducible;
- handoffs gobernados;
- token/context baseline observable;
- regresiones adversariales satisfactorias;
- auditor independiente sin bypass material abierto.

Los entregables mínimos son:

```text
reports/implementation/plan_004/TH06_context_resolution.json
reports/implementation/plan_004/TH06_handoff_audit.json
schemas/resolved_context_manifest.json
```

Todos deben usar el envelope común de §9.12.

---

# TH-07 — Baseline determinista de calidad

## 12. Objetivo

Introducir observabilidad de calidad técnica antes de imponer thresholds.

```text
OBSERVE
→ INTERPRET
→ OWNER DECIDES POLICY
```

## 12.1 Métricas iniciales

Cuando sean técnicamente aplicables:

```text
test coverage
complexity
duplication
dead/unreachable code
static-analysis findings
critical-path/test distribution
```

Cada dimensión debe registrarse como `MEASURED`, `NOT_APPLICABLE` o `LIMITATION`,
con razón y evidencia. Añadir otras solo con utilidad demostrable.

## 12.2 Baseline por riesgo

No limitarse a promedio global. Identificar:

- módulos críticos;
- hotspots;
- alta complejidad;
- baja cobertura;
- seguridad/gobernanza;
- frecuencia de cambio si puede obtenerse de forma fiable.

## 12.3 Determinismo

```text
tool
→ structured report
→ agent interprets only anomalies
```

No pedir a un LLM que estime métricas leyendo el codebase.

## 12.4 No objetivos

No establecer automáticamente:

```text
coverage >= X
CRAP <= Y
complexity <= Z
```

sin baseline y decisión posterior.

## 12.5 Entrega

`QUALITY_BASELINE` reproducible y evidencia suficiente para la recomendación definida
en §12.6.

## 12.6 Criterio de cierre

- baseline reproducible;
- módulos de riesgo identificados;
- coste de medición conocido;
- sin thresholds inventados;
- owner dispone de evidencia para decidir siguiente política.

El entregable mínimo es:

```text
reports/implementation/plan_004/TH07_quality_baseline.json
```

Las decisiones de política son recomendaciones, no autorizaciones automáticas:

```text
RECOMMENDATION:
KEEP_INFORMATIONAL
ADD_SELECTIVE_THRESHOLDS
ADD_RISK_BASED_GATES
```

El envelope común de §9.12 es obligatorio.

---

# TH-08 — Mutation testing selectivo

## 13. Objetivo

Evaluar si mutation testing detecta falsa confianza en módulos críticos con una relación valor/coste aceptable.

## 13.1 Precondición

TH-07 cerrado y baseline disponible.

## 13.2 Scope

Seleccionar un subconjunto pequeño según riesgo real, por ejemplo:

- mission authorization;
- mission completion;
- repair integrity;
- provenance;
- invalidation;
- contamination guard;
- context resolution;
- critical gates.

La selección final debe justificarse desde el repositorio real.

## 13.3 Medición

Registrar:

```text
mutants_generated
mutants_killed
survivors
runtime
cost
useful_findings
noisy_findings
```

## 13.4 Clasificación de survivors

```text
MISSING_TEST
EQUIVALENT_MUTANT
LOW_VALUE_MUTATION
REAL_WEAKNESS
```

No asumir que todo survivor es un bug.

## 13.5 Recomendación obligatoria

Al cierre, TH-08 produce una recomendación:

```text
KEEP
KEEP_SELECTIVELY
DROP
```

basada en:

```text
VALUE / COST
```

## 13.6 Criterio de cierre

- scope crítico justificado;
- mutation run reproducible;
- survivors clasificados;
- findings útiles convertidos en regresiones cuando corresponda;
- recomendación `MUTATION_TESTING_RECOMMENDATION` registrada.

La decisión final pertenece al owner durante `HARDENING_COMPLETION_REVIEW`.

El entregable mínimo es:

```text
reports/implementation/plan_004/TH08_mutation_testing.json
```

Debe usar el envelope común de §9.12.

---

# HARDENING_COMPLETION_REVIEW

## 14. Objetivo

Después de TH-08, reconciliar el bloque completo antes de volver al roadmap funcional.

No abrir automáticamente R1-M4 ni otra fase.

## 14.1 Preguntas obligatorias

### Autoverificación

¿Qué puede verificar el sistema sin ChatGPT/humano?

### IA

¿Qué continúa requiriendo razonamiento semántico de IA?

### Owner / autoridad funcional

¿Qué decisiones siguen requiriendo aprobación humana/funcional?

### Reparación

¿Puede detectar y bloquear reparación cosmética o autoaprobación?

### Contexto

¿Resuelve únicamente contexto suficiente y reproducible?

### Portabilidad

¿Puede sustituirse el ejecutor sin cambiar contratos funcionales?

### Coste

¿Qué verificaciones dejaron de consumir tokens de IA?

### Calidad

¿Qué métricas/gates demostraron valor suficiente para permanecer?

### Paralelismo

¿El patrón implementador + auditor paralelo redujo iteraciones sin aumentar contaminación, coste o conflictos?

## 14.2 Evidencia final esperada

El review debe poder demostrar o negar explícitamente:

```text
DETERMINISTIC_CONTROLS_OPERATIONAL
MISSION_SCOPE_VERIFIABLE
EXECUTION_PROVENANCE_VERIFIABLE
CONTEXT_RESOLUTION_VERIFIABLE
REPAIR_INTEGRITY_OPERATIONAL
INDEPENDENT_REVIEW_VERIFIABLE
AUTHORITY_COMPETENCE_RESOLVABLE
CAPABILITY_REGISTRY_COHERENT
CROSS_REGISTRY_INTEGRITY
QUALITY_BASELINE_AVAILABLE
MUTATION_DECISION_RECORDED
PROVIDER_PORTABILITY_PRESERVED
```

No es obligatorio que todas las respuestas sean `PASS`; una limitación real puede quedar registrada sin falsear madurez.

Los estados permitidos son:

```text
PASS
FAIL
LIMITATION
NOT_APPLICABLE
```

El entregable mínimo es:

```text
reports/implementation/plan_004/HARDENING_COMPLETION_REVIEW.json
```

Debe usar el envelope común de §9.12. El resultado técnico del bloque es
`HARDENING_COMPLETED_PENDING_OWNER_REVIEW`; la decisión posterior pertenece al owner.

---

## 15. Regreso al roadmap funcional

Solo después del `HARDENING_COMPLETION_REVIEW`:

```text
read plans/001_CONTROL_OPERATIVO.md
↓
reconcile R1 current state
↓
confirm R1-M3 real state
↓
determine NEXT_ALLOWED_ACTION
```

No copiar estados actuales de R1 en este documento. No asumir que el siguiente paso
será R1-M4 si el estado vivo futuro indica otra cosa.

---

## 16. Git y artefactos protegidos

Por defecto en misiones TH:

```text
COMMIT: NO
PUSH: NO
```

salvo autorización explícita.

Cuando exista autorización de commit:

- staging quirúrgico;
- no `git add .`;
- preservar cambios preexistentes;
- revisar staged diff;
- ejecutar validaciones aplicables;
- un commit coherente por cierre/integración autorizada.

Preservar artefactos protegidos y cambios ajenos identificados por el estado vivo/preflight.

---

## 17. Reglas para minimizar iteraciones correctivas

Antes de implementar cualquier TH, la misión debe especificar:

1. objetivo único;
2. precondiciones;
3. universo/scope cerrado;
4. fuentes canónicas;
5. archivos o familias potencialmente afectadas;
6. invariantes que no pueden romperse;
7. no objetivos;
8. casos adversariales mínimos;
9. criterios de aceptación;
10. validaciones deterministas;
11. responsabilidades del reviewer independiente;
12. condición exacta para detenerse.

El implementador debe buscar antes de crear.

El reviewer paralelo debe buscar fallos antes del cierre, no después de varias rondas de reparación.

Una misión no debe pedir respuestas declarativas como sustituto de evidencia del repositorio.

---

## 18. Secuencia canónica del bloque

```text
TH-01  REALITY RECONCILIATION
  ↓
TH-02  NEUTRALITY / CONTAMINATION
  ↓
TH-03  REPAIR INTEGRITY
  ↓
TH-04  EXECUTABLE CAPABILITY INVENTORY
  ↓
TH-05  CROSS-REGISTRY + AUTHORITY
  ↓
TH-06  CONTEXT + HANDOFF EFFICIENCY
  ↓
TH-07  QUALITY BASELINE
  ↓
TH-08  SELECTIVE MUTATION TESTING
  ↓
HARDENING_COMPLETION_REVIEW
  ↓
RETURN TO PLAN-001 / R1 ACCORDING TO LIVE STATE
```

---

## 19. Condición de uso por agentes

Cualquier ejecutor compatible debe poder leer este documento para comprender el alcance
de la TH, pero **no puede tomarlo como autorización viva**.

Antes de actuar deben verificar siempre:

```text
plans/001_CONTROL_OPERATIVO.md
+
mission authorization
+
actual Git/repository state
```

Si el plan describe TH-04 pero el estado vivo no la autoriza:

```text
STOP
```

Si el estado vivo autoriza una TH, la misión concreta debe permanecer dentro de su
sección correspondiente de este plan y de la especificación arquitectónica transversal.

---

## 20. Resultado esperado de esta versión

Con este documento en el repositorio:

- TH-04–TH-08 dejan de depender de memoria de chats;
- cualquier ejecutor compatible puede distinguir el alcance de cada TH;
- el preflight puede detener ejecuciones no autorizadas sin perder la especificación;
- el owner puede autorizar una misión concreta sin reconstruir su propósito;
- el implementador y reviewer pueden trabajar en paralelo con límites compartidos;
- las futuras iteraciones correctivas deben disminuir porque los casos adversariales y criterios de aceptación están definidos antes de implementar.
