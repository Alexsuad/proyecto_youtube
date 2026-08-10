---
name: evidencia-proporcional-git
description: Selecciona evidencia Git mínima y suficiente para revisar cambios sin mezclar alcance ni generar material innecesario.
---

# Evidencia proporcional con Git

## Objetivo

Producir evidencia suficiente para revisar una intervención, proporcional a su riesgo y alcance.

## Procedimiento

1. Capturar el estado del árbol con `git status --short`.
2. Resumir archivos afectados con `git diff --stat` y `git diff --name-status`.
3. Revisar el diff puntual con `git diff -U0` cuando sea necesario.
4. Ejecutar `git diff --check` y las validaciones canónicas de la misión.
5. Separar cambios propios, preexistentes, protegidos y no incluidos.
6. Si la misión autoriza commit, verificar que sea atómico y revisar el staged diff; si no lo autoriza, no preparar ni crear commit.

## Evidencia mínima

- archivos tocados;
- diff resumido y cualquier fragmento relevante;
- validaciones, resultado y limitaciones;
- estado final del árbol;
- commit únicamente cuando esté expresamente autorizado.

No pegar archivos completos si el diff y los fragmentos necesarios bastan. No afirmar que una suite terminó si fue interrumpida o limitada por el entorno.

## Límites

- No borrar ni ocultar cambios preexistentes.
- No usar la evidencia Git para aprobar requisitos funcionales.
- No convertir un diff limpio en autorización de ejecución o publicación.
- No mezclar documentación, refactor y lógica sin justificación de alcance.
