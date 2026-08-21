# Skill — Control de Integridad del Pipeline
Objetivo: Garantizar que el checkout está estable antes de una operación. El escaneo de Vault es un adaptador legacy opcional.

> **Nota:** La verificación de archivos es **determinista**. La ejecución real la hace:
> `src/scripts/gate0_integridad.py`
> Este skill define la lógica; el script la aplica.

---

## Entrada mínima
- Checkout del repositorio y sus contratos.
- `config/local_settings.json` y `<VAULT_ROOT>/<CHANNEL_ID>/index/episodes_index.json` solo para seleccionar el adaptador legacy.

---

## Pasos

1) **Ejecutar script de integridad** (determinista):
   ```
   python src/scripts/gate0_integridad.py
   ```
   El script:
   - Si existe una configuración legacy válida, lee el `episodes_index.json` del Vault.
   - Si se selecciona esa ruta, escanea carpetas de episodios en `<VAULT_ROOT>/<CHANNEL_ID>/episodios/`.
   - Sin configuración legacy válida, comprueba la integridad portable y devuelve `WARN` informativo sin bloquear el checkout.
   - Detecta episodios con estado `en_progreso` o con entregables finales faltantes.

2) **Los entregables finales verificados son:**
   - `<EP_PATH>/06_guion_longform.md`
   - `<EP_PATH>/06_guion_longform_limpio.md`
   - `<EP_PATH>/06_guion_longform_anotado.md`
   - `<EP_PATH>/script_version_manifest.json`
   - `<EP_PATH>/editorial_script_approval.json`
   - `<EP_PATH>/claims_ledger.json`
   - `<EP_PATH>/final_delivery_manifest.json`

3) **Diagnóstico (asignado por el script):**
   - `OK` → Checkout limpio o Vault legacy limpio.
   - `WARN` → Episodio con entregables incompletos (riesgo de colisión).
   - `FAIL` → Error técnico real de integridad. La ausencia de Vault solo afecta al adaptador legacy.

4) **Reporte generado por el script:**
   - `output/control_integridad_pipeline.md` (con `ESTADO_GLOBAL`)

---

## Salida
- `output/control_integridad_pipeline.md`
