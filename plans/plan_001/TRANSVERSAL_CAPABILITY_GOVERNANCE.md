# Gobernanza transversal de capacidades

**DOCUMENT_ID:** `TRANSVERSAL_CAPABILITY_GOVERNANCE`
**DOCUMENT_TYPE:** `TRANSVERSAL_IMPLEMENTATION_SPECIFICATION`
**PLAN_RECTOR:** `PLAN_001`
**LIVE_STATE_AUTHORITY:** `plans/001_CONTROL_OPERATIVO.md`
**SCOPE:** `R1-R9`
**IMPLEMENTATION_AUTHORIZED_BY_THIS_DOCUMENT:** `NO`
**CURRENT_LIVE_STATE_CHANGED_BY_THIS_DOCUMENT:** `NO`
**DOCUMENT_STATUS:** `READY_FOR_AUTHORITY_REVIEW`

## Neutralidad y portabilidad

El repositorio no depende de la identidad del proveedor, modelo, cliente,
entorno, solicitante, operador o mecanismo ejecutor. El significado funcional
se expresa mediante dominios, capacidades, roles, contratos, policies,
rúbricas, perfiles, interfaces, schemas, autorización, evidencia y provenance.

Los dominios canónicos son `CHANNEL_INTELLIGENCE`, `SCRIPT_PRODUCT`,
`YOUTUBE_ADAPTATION` e `INFRASTRUCTURE_GOVERNANCE`. Los roles representan
funciones y no productos. La sustitución de un ejecutor compatible no cambia
el significado funcional ni los contratos.

Este documento no abre fases, no cambia `NEXT_ALLOWED_ACTION`, no activa
capacidades y no autoriza ejecuciones. Cada incremento requiere una misión
explícita emitida contra el estado vivo vigente.

## Baseline funcional

La baseline funcional se incorporará como snapshot inmutable, trackeado
normalmente, con locator, versión, checksum de origen, checksum de repositorio,
referencia de aprobación y provenance de incorporación. Mientras falte el
artefacto fuente estable, `FUNCTIONAL_BASELINE_RESOLVABLE` permanece bloqueado.

No se aceptan snapshots ignorados, temporales, no trackeados o añadidos por
mecanismos excepcionales.

## Registry y estados

Existe un único registry canónico de capacidades. Su migración debe conservar
las entradas actuales, ampliar el schema para los dominios aplicables y
actualizar lectores, escritores, validadores, fixtures, tests y consumidores
sin dual-write.

La maturity conserva exactamente:

```text
DEFINED → REGISTERED → IMPLEMENTED → DEMONSTRATED
```

Maturity, availability, technical assurance, semantic assurance, functional
approval y operational evidence son dimensiones independientes. Ninguna se
infiere de otra. Cada misión declara un `CAPABILITY_AUDIT_UNIVERSE` cerrado y
el inventario producido es evidencia derivada, nunca fuente de verdad.

## Resolución de contexto

Toda referencia operacional usa `ContextReference` con clase `NORMATIVE`,
`EVIDENTIARY` o `HISTORICAL`, ruta relativa, tipo, versión, checksum,
`authority_domain` y `required`.

La resolución debe permanecer dentro de roots permitidos, rechazar rutas
absolutas, traversal y escapes mediante symlink, y verificar los bytes exactos.
Los artefactos JSON estructurados usan únicamente el mecanismo canónico de
JSON del proyecto. Las referencias obligatorias no resolubles bloquean antes
de la ejecución; las opcionales generan `CONTEXT_OPTIONAL_UNRESOLVED` y quedan
registradas.

Cada ejecución semántica construye un `ResolvedContextManifest` y lo liga a la
provenance junto con capability, role, misión, profile, input, output, prompt y
checksums. Los cambios posteriores producen una nueva ejecución o
revalidación explícita.

## Autorización y replay

Toda ejecución controlada puede validarse mediante un contrato machine-readable
de misión compatible con la familia de contratos existente. El contrato limita
capabilities, roles, operaciones, paths y modo de ejecución; contiene checksum
del estado vivo y una referencia verificable a la autoridad que lo emitió.

El sistema valida autorización, estado vivo, scope, capability, availability,
profile, routing y contexto antes de ejecutar. `single_use` es verdadero por
defecto. La reserva de ejecución es atómica antes de invocar al ejecutor para
evitar carreras concurrentes; la reutilización produce `MISSION_REPLAY_DETECTED`.

Routing sólo resuelve cómo se ejecuta una capacidad. No decide maturity,
availability, aprobación funcional ni autorización vigente.

## Correcciones funcionales delimitadas

`TOPIC_FIRST` incorpora `entry_mode` y usa únicamente `NO_WORK_YET` como
ausencia inicial de obra. `TOPIC_FIRST + NO_WORK_YET` es válido;
`ANCHOR_WORK_FIRST + NO_WORK_YET` y `CORPUS_FIRST` sin corpus son inválidos.
La combinación `TOPIC_FIRST` con obra real permanece bloqueada hasta aclaración
funcional competente.

Los defaults de `YOUTUBE_ADAPTATION` se corregirán antes de su primera ejecución
autorizada, cubriendo registry, roles, profiles, prompts, contratos, routing,
separación productor/revisor y tests. No se materializan capacidades futuras
por anticipado.

## Gates y evidencia

Los validadores deben distinguir, como mínimo:

```text
CAP_OWNER_UNRESOLVED
CAP_REQUIREMENT_REF_UNRESOLVED
CAP_IMPLEMENTATION_REF_MISSING
CAP_CONTEXT_REF_UNRESOLVED
CAP_MATURITY_EVIDENCE_MISMATCH
CAP_AVAILABILITY_CONTRADICTION
MISSION_CONTRACT_INVALID
MISSION_STALE_AGAINST_LIVE_STATE
MISSION_REPLAY_DETECTED
CONTEXT_PATH_NOT_ALLOWED
CONTEXT_REQUIRED_UNRESOLVED
```

Se mantienen separadas `STRUCTURAL_VALIDATION`, `TECHNICAL_VALIDATION`,
`SEMANTIC_VALIDATION`, `OPERATIONAL_DEMONSTRATION` y `FUNCTIONAL_APPROVAL`.
Los fixtures semánticos deben tener trazabilidad a requisitos y autoridad
funcional aprobada.

La implementación no activa capacidades, no abre R2-R9, no ejecuta producción,
publicación ni S5, no modifica el control operativo y no hace commit ni push.
