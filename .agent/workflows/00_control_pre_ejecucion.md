---
description: Workflow de control pre-ejecución (Gate 0). Ejecuta auditorías de sistema y de integridad antes de permitir operaciones.
---

# Workflow: Control Pre-Ejecución (Gate 0)

Este workflow asegura que el entorno (Repo + Vault) sea estable antes de iniciar cualquier trabajo.

## 1. Ejecutar Auditoría de Sistema
Esta skill verifica config, carpetas del repo y estructura del Vault (auto-creándola si es necesario).

// turbo
- Revisar y ejecutar: `.agent/skills/skill_auditoria_sistema.md`
- Output esperado: `output/auditoria_sistema_v1.md`

## 2. Ejecutar Control de Integridad de Pipeline
Esta skill verifica que no haya "basura" o procesos inconclusos que puedan causar colisiones.

// turbo
- Revisar y ejecutar: `.agent/skills/skill_control_integridad_pipeline.md`
- Output esperado: `output/control_integridad_pipeline.md`
- Nota: Asegurarse de mapear el resultado a OK / WARN / FAIL.

## 3. Consolidación y Decisión Final
Analizar los resultados de ambas auditorías para emitir un juicio de viabilidad.

### Lógica de Decisión:
1.  **Leer** `output/auditoria_sistema_v1.md` y extraer `ESTADO_GLOBAL`:
    - Si `FAIL` -> **Resultado: 🔴 DETENER**.

2.  **Leer** `output/control_integridad_pipeline.md` y determinar estado mapeado:
    - Si es bloqueo real del sistema -> **FAIL**.
    - Si son incompletos históricos -> **WARN**.
    - Si todo ok -> **OK**.

3.  **Regla final**:
    - Si auditoría sistema = FAIL -> 🔴
    - Si auditoría sistema = OK y control integridad = FAIL -> 🔴
    - Si cualquiera = WARN (y ninguno FAIL) -> 🟡
    - Si ambos = OK -> 🟢

### Acción Final:
Generar el reporte de aprobación:
- Archivo: `output/control_pre_ejecucion_v1.md`
- Contenido:
  - `ESTADO_GLOBAL: OK|WARN|FAIL`
  - Decisión explícita: **GO / GO_CON_RIESGO / NO_GO**
  - Lista breve (máx. 7) de razones.
  - Lista de acciones recomendadas.
