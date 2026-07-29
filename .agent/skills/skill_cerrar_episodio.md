# Skill — Cerrar Episodio
Objetivo: validar que el episodio alcanzó `EDITORIAL_SCRIPT_APPROVED` sin exigir entregables diferidos.

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

### Paso B — Actualizar índice (Python)
Actualizar `episodes_index.json` con:
- `"estado": "completado"`
- `"cerrado": "<timestamp>"`

---

## Script Python requerido
`src/scripts/cerrar_episodio.py`

---

## Salida
- `episodes_index.json` actualizado con estado `completado`.
