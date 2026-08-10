# Skills de ingeniería

Esta es la sede neutral de procedimientos reutilizables para desarrollo, auditoría y verificación del repositorio.

No es una sede de skills funcionales del producto. No se registra en `config/skill_catalog.json`, no se ejecuta como capability runtime y no altera los contratos editoriales.

## Regla arquitectónica

Los nombres `GENERAL_CAPABILITIES` que aparecen en `tests/core/test_b4_i1_contracts.py` y en `covered_by_general_capability` son etiquetas de cobertura conceptual del catálogo productivo; no autorizan copiar esas capacidades en `.agent/skills/`.

Cuando una capacidad general de ingeniería se materializa como procedimiento versionado para futuras misiones, su sede física es `.agents/skills/<id>/SKILL.md`. La separación entre `.agent/skills/` y `.agents/skills/` es intencional: el primer árbol es productivo/editorial y el segundo es procedimental/de ingeniería.

## Skills disponibles

- `preparar-paquete-ejecucion-tecnica`: convierte una decisión técnica ya tomada en un paquete ejecutable cerrado.
- `auditar-trazabilidad-input-output`: compara instrucción, alcance, ejecución, cambios y resultado reportado.
- `evidencia-proporcional-git`: define la evidencia Git mínima suficiente para una revisión.
- `verificar-no-mezcla-de-capas`: identifica cruces indebidos entre autoridad, producto, proceso y evidencia.
- `harness-determinista`: decide qué debe comprobarse mecánicamente y reutiliza controles deterministas existentes.

## Uso normal

1. Leer `plans/001_CONTROL_OPERATIVO.md` y `AGENTS.md`.
2. Seleccionar solo la skill de ingeniería necesaria para la misión.
3. Aplicarla sobre el alcance declarado, conservando cambios previos y archivos protegidos.
4. Ejecutar los gates, tests o validadores canónicos que correspondan.
5. Reportar evidencia, límites y cualquier divergencia sin cambiar la autoridad viva por inferencia.

La sede se descubre por este índice y por la convención `*/SKILL.md`; el catálogo productivo no debe usarse para localizar estas skills.
