# Skill — Auditoría de Sistema (V1 - Pre-Ejecución)

**Objetivo:** Verificar que el checkout y, cuando se solicite, el adaptador Vault legacy están listos para operar.
Este skill corresponde al **Gate 0** técnico. La ruta portable no requiere configuración local ni Vault.

---

## Entradas
- Ruta portable del checkout y sus contratos.
- `config/local_settings.json` solo si se selecciona explícitamente la ruta legacy Vault.
- Opcional: variables de entorno (solo diagnóstico). En modo legacy la fuente de verdad es la configuración local.

---

## Pasos

### 1. Verificación de Configuración
- Auditar siempre la estructura contractual del checkout.
- Si se selecciona el adaptador legacy, leer `config/local_settings.json` y validar `vault_root`, `channel_id`.
- Si la configuración legacy falta, está incompleta o la ruta no existe, omitir ese adaptador y continuar por la ruta portable con `WARN`.

### 2. Verificación del Repositorio (Estructura Base)
- Confirmar existencia de directorios críticos:
  - `.agent/rules/`
  - `.agent/skills/`
  - `.agent/workflows/`
  - `templates/`
  - `workspace/`
- Validar presencia de reglas core:
  - `00_reglas_globales.md`
  - `01_formato_outputs.md`
  - `02_reglas_notebooklm.md`
- **Acción:** Si falta algo crítico 🔴 STOP. Si falta algo menor 🟡 WARN.

### 3. Verificación del Vault (solo adaptador legacy seleccionado)
- Usar las rutas leídas de la config: `<VAULT_ROOT>\<CHANNEL_ID>\`.
- **Paso A:** Verificar existencia de `VAULT_ROOT`. (Si no existe, 🔴 STOP - El usuario debe montar el disco/ruta).
- **Paso B:** Verificar/Crear `<VAULT_ROOT>\<CHANNEL_ID>\`.
- **Paso C:** Verificar/Crear subestructuras obligatorias:
  - `...\episodios\`
  - `...\index\`
  - Opcional: `...\biblioteca\` (no se crea automáticamente).
- **Paso D:** Verificar existencia de `index\episodes_index.json`.
  - Si no existe, crear un JSON válido vacío: `{"episodes": [], "last_updated": null}`.
- **Acción:** Reportar qué se creó y qué ya existía. No se auto-crea Vault desde la ruta portable ni se convierte en condición universal.

### 4. Diagnóstico Final
- Generar reporte consolidado.
- Determinar estado global y agregar línea final obligatoria:
  - `ESTADO_GLOBAL: OK` (Todo existe o fue auto-creado exitosamente).
  - `ESTADO_GLOBAL: WARN` (Configuración usable pero con deuda técnica).
  - `ESTADO_GLOBAL: FAIL` (Error bloqueante).

---

## Salida
- `output/auditoria_sistema_v1.md`
