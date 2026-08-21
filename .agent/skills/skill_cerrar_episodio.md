# Skill — Cerrar Episodio
Objetivo: validar que el episodio alcanzó `EDITORIAL_SCRIPT_APPROVED` sin exigir entregables diferidos.

La QA de duración usa un `YT_DURATION_ENVELOPE` episódico válido cuando se le entrega junto con su package, review independiente y registro de ejecución verificables. El gate debe declarar `duration_policy_source` como `EPISODIC_YT_DURATION_ENVELOPE` o `TECHNICAL_FALLBACK`; solo cuando no existe un envelope aprobado se aplica el fallback técnico documentado, que no constituye una decisión editorial universal. La ruta portable de cierre consume los gates generados en el checkout y no exige Vault ni configuración local.

> **Rol ejecutor actual:** Python (`src/scripts/cerrar_episodio.py`) para validación determinista de contratos y actualización del índice.

---

## Entrada mínima
- `<EP_PATH>` activo (del índice o del contexto)
- gates requeridos en `output/gates/<EP_ID>/`

---

## Pasos

### Paso A — Validación determinista (Python)
Ejecutar `src/scripts/cerrar_episodio.py` que verifica la existencia de los entregables obligatorios del núcleo editorial:
- `<EP_PATH>/06_guion_longform.md`
- `<EP_PATH>/06_guion_longform_limpio.md`
- `<EP_PATH>/06_guion_longform_anotado.md`
- `<EP_PATH>/script_version_manifest.json`
- `<EP_PATH>/editorial_script_approval.json`
- `<EP_PATH>/claims_ledger.json`
- `<EP_PATH>/final_delivery_manifest.json`

Si falta alguno: STOP — listar los faltantes, no cerrar el episodio.

### Paso B — Actualizar índice cuando se use Vault legacy (Python)
En la ruta portable el cierre valida los gates del checkout y no modifica ningún índice externo. Solo en la ruta Vault legacy seleccionada se actualiza `episodes_index.json` con:
- `"estado": "completado"`
- `"cerrado": "<timestamp>"`

---

## Script Python requerido
`src/scripts/cerrar_episodio.py`

---

## Salida
- Ruta portable: gate de cierre PASS y artefacto de resultado en el output configurado.
- Ruta Vault legacy: además, `episodes_index.json` actualizado con estado `completado`.
