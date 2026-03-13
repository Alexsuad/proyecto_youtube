# Skill — Control de Integridad del Pipeline
Objetivo: Garantizar que el sistema está estable y limpio antes de iniciar una nueva producción.

> **Nota:** La verificación de archivos es **determinista**. La ejecución real la hace:
> `src/scripts/gate0_integridad.py`
> Este skill define la lógica; el script la aplica.

---

## Entrada mínima
- `config/local_settings.json` (vault_root + channel_id)
- `<VAULT_ROOT>/<CHANNEL_ID>/index/episodes_index.json`

---

## Pasos

1) **Ejecutar script de integridad** (determinista):
   ```
   python src/scripts/gate0_integridad.py
   ```
   El script:
   - Lee el `episodes_index.json` del Vault.
   - Escanea carpetas de episodios en `<VAULT_ROOT>/<CHANNEL_ID>/episodios/`.
   - Detecta episodios con estado `en_progreso` o con entregables finales faltantes.

2) **Los entregables finales verificados son:**
   - `<EP_PATH>/06_guion_longform.md`
   - `<EP_PATH>/08_shorts.md`
   - `<EP_PATH>/09_packaging.md`
   - `<EP_PATH>/10_seo.md`

3) **Diagnóstico (asignado por el script):**
   - `OK` → Vault limpio o episodio anterior completo.
   - `WARN` → Episodio con entregables incompletos (riesgo de colisión).
   - `FAIL` → Error de configuración o Vault inaccesible.

4) **Reporte generado por el script:**
   - `output/control_integridad_pipeline.md` (con `ESTADO_GLOBAL`)

---

## Salida
- `output/control_integridad_pipeline.md`
