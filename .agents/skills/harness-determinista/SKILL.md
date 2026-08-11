---
name: harness-determinista
description: Procedimiento para separar razonamiento de comprobaciones mecánicas y reutilizar los controles deterministas canónicos del repositorio.
---

# Harness determinista

## Objetivo

Hacer que las comprobaciones exactas dependan de mecanismos reproducibles, no de una lectura manual del agente.

## Regla de reutilización

Antes de proponer una comprobación nueva, localizar el mecanismo canónico que ya la materializa:

- `src/core/mission_authorization.py` y `schemas/mission_authorization_contract.json` para autorización de ejecución;
- `src/core/mission_completion_gate.py` y `src/scripts/mission_completion_gate.py` para cierre de misión;
- `src/core/repair_integrity.py` y `src/scripts/repair_integrity_gate.py` para integridad de reparación;
- `src/core/execution_preflight.py` para preflight de ejecución;
- gates existentes en `src/scripts/` y sus tests;
- schemas en `schemas/` y validaciones deterministas asociadas.

La skill orienta el procedimiento; no reimplementa esos controles ni los sustituye por una evaluación manual.

## Procedimiento

1. Expresar qué afirmación exacta debe comprobarse.
2. Buscar primero el test, gate, schema o contrato canónico que la cubre.
3. Ejecutar el mecanismo con un intérprete y comandos reproducibles aceptados por el repositorio.
4. Registrar comando, salida relevante, alcance y limitaciones.
5. Si no existe cobertura determinista suficiente, marcar la evidencia como incompleta y proponer un test o validador acotado, sin crearlo fuera de la misión.
6. Separar el resultado mecánico de cualquier aprobación funcional, de gobernanza o de activación.

## No confiar solo en lectura visual para

- conteos y enumeraciones;
- parsing y schemas;
- checksums y comparación de archivos;
- alcance Git y ausencia de cambios;
- estados de gates y contratos;
- regresiones de seguridad o autorización.

## Evidencia mínima

- mecanismo canónico utilizado;
- comando o test ejecutado;
- salida relevante;
- afirmación validada y afirmación no validada;
- limitaciones ambientales o temporales.

## Convergencia de misión reducida

Cuando un `MissionContract` declare `mission_mode: REDUCED`, el executor debe
usar el flujo canónico de `src/core/mission_convergence.py` tras
`MissionAuthorization` y `execution_preflight`:

```text
IMPLEMENT → VERIFY → SELF_ADVERSARIAL_REVIEW → REPAIR → REVERIFY
```

En modo gobernado, cada fase decisiva entrega `passed` y referencias de
evidencia estructuradas. Un booleano o una declaración textual no autoriza
`CONVERGED`. El resultado técnico indica el escalado exigido por
`review_policy`; no equivale a `INDEPENDENT_REVIEW` ni a aprobación del owner.

## Límites

No crear un segundo registry, contrato, gate o autoridad para cubrir una comprobación que ya existe. No convertir un resultado técnico en autorización de ejecución, aprobación funcional o readiness productivo.
