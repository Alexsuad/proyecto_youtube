---
name: auditar-trazabilidad-input-output
description: Compara instrucción, alcance autorizado, acciones ejecutadas, cambios observables y resultado reportado para detectar omisiones o desvíos.
---

# Auditar trazabilidad de input a output

## Propósito

Comprobar que la ejecución y el reporte siguen la instrucción y el alcance autorizado, con evidencia observable del repositorio.

## Entradas

- instrucción y misión;
- autoridad viva aplicable;
- alcance permitido y exclusiones;
- estado previo, archivos tocados y acciones realizadas;
- validaciones ejecutadas y resultado reportado.

## Procedimiento

1. Leer la autoridad viva y la instrucción original.
2. Comparar rutas autorizadas con `git status --short` y `git diff --name-status`.
3. Comparar acciones realizadas con las acciones permitidas.
4. Comprobar requisitos, límites y resultados declarados frente a evidencia real.
5. Identificar omisiones, cambios de alcance, conclusiones no soportadas y validaciones incompletas.
6. Emitir un dictamen trazable, conservando el estado sin modificarlo.

## Salida

Informar coincidencias, divergencias, requisitos perdidos, evidencia faltante y un único dictamen:

- `TRAZABILIDAD_OK`;
- `DESVIO_MENOR`;
- `DESVIO_CRITICO`;
- `ALCANCE_CAMBIADO`.

## Límites

- No tomar decisiones de negocio o de producto.
- No abrir, cerrar ni relajar gates.
- No sustituir una aprobación humana o un contrato canónico.
- No presentar una hipótesis como hecho.
- No corregir directamente la entrega durante la auditoría.

## Criterio de cierre

La trazabilidad queda demostrada cuando cada cambio y cada afirmación del reporte pueden relacionarse con la instrucción, el alcance y una evidencia concreta, o quedan marcados como divergencia.
