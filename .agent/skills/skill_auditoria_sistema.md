# Skill — Auditoría de Sistema (V1 - Pre-Ejecución)

**Objetivo:** Verificar que el entorno (Repo + Vault) está correctamente configurado y listo para operar.
Este skill es el **Gate 0** obligatorio antes de cualquier operación de escritura.

---

## Entradas
- `config/local_settings.json` (Debe existir)
- Opcional: variables de entorno (solo diagnóstico). La fuente de verdad es `config/local_settings.json`.

---

## Pasos

### 1. Verificación de Configuración
- Leer `config/local_settings.json`.
- Validar que existan las claves: `vault_root`, `channel_id`.
- **Acción:** Si falla 🔴 STOP.

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

### 3. Verificación y Auto-Creación del Vault
- Usar las rutas leídas de la config: `<VAULT_ROOT>\<CHANNEL_ID>\`.
- **Paso A:** Verificar existencia de `VAULT_ROOT`. (Si no existe, 🔴 STOP - El usuario debe montar el disco/ruta).
- **Paso B:** Verificar/Crear `<VAULT_ROOT>\<CHANNEL_ID>\`.
- **Paso C:** Verificar/Crear subestructuras obligatorias:
  - `...\episodios\`
  - `...\index\`
  - Opcional: `...\biblioteca\` (no se crea automáticamente).
- **Paso D:** Verificar existencia de `index\episodes_index.json`.
  - Si no existe, crear un JSON válido vacío: `{"episodes": [], "last_updated": null}`.
- **Acción:** Reportar qué se creó y qué ya existía.

### 4. Diagnóstico Final
- Generar reporte consolidado.
- Determinar estado global y agregar línea final obligatoria:
  - `ESTADO_GLOBAL: OK` (Todo existe o fue auto-creado exitosamente).
  - `ESTADO_GLOBAL: WARN` (Configuración usable pero con deuda técnica).
  - `ESTADO_GLOBAL: FAIL` (Error bloqueante).

---

## Salida
- `output/auditoria_sistema_v1.md`
