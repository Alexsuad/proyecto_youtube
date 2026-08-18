---
description: Control pre-ejecución mediante GateResult JSON y códigos canónicos.
---

# Workflow: Control Pre-Ejecución (Gate 0)

1. Ejecutar `python src/scripts/gate0_auditoria.py`.
2. Consumir `output/gates/system/gate0_auditoria.json` y su exit code.
3. Ejecutar `python src/scripts/gate0_integridad.py`.
4. Consumir `output/gates/system/gate0_integridad.json` y su exit code.

La decisión usa únicamente el `status` estructurado, el exit code y la política explícita: `PASS` permite continuar; `WARN` requiere aplicar la política de riesgo; `FAIL` (1), `BLOCKED` (2) y error técnico (3) detienen. El Markdown es solo una representación humana y no se parsea para decidir transiciones.

`config/local_settings.json` y el Vault son opcionales para el camino portable del checkout. Su ausencia produce `WARN` y deja evidencia de que se omitieron las comprobaciones legacy; cuando existen, Gate 0 conserva las comprobaciones del flujo legacy.
