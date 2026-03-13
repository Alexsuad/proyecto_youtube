# Skill — Cerrar Episodio (Empaquetado Final)
Objetivo: validar que el episodio está completo y preparar el paquete para NotebookLM.

> **Rol ejecutor actual:** Python (`src/scripts/cerrar_episodio.py`) para validación de archivos + Antigravity para generación del pack.
> Esta skill combina determinismo (verificación de archivos) con IA (redacción del pack).

---

## Entrada mínima
- `<EP_PATH>` activo (del índice o del contexto)
- `templates/99_notebooklm_pack_template.md`

---

## Pasos

### Paso A — Validación determinista (Python)
Ejecutar `src/scripts/cerrar_episodio.py` que verifica la existencia de los 5 entregables obligatorios:
- `<EP_PATH>/06_guion_longform.md`
- `<EP_PATH>/07_verificacion_veracidad_notebooklm.md`
- `<EP_PATH>/08_shorts.md`
- `<EP_PATH>/09_packaging.md`
- `<EP_PATH>/10_seo.md`

Si falta alguno: 🔴 STOP — listar los faltantes, no cerrar el episodio.

### Paso B — Generar pack NotebookLM (IA)
Con todos los entregables presentes:
1) Leer `<EP_PATH>/05_sintesis_tesis.md` para extraer tesis e ideas fuerza.
2) Generar `<EP_PATH>/99_notebooklm_pack.md` usando `templates/99_notebooklm_pack_template.md`.

### Paso C — Actualizar índice (Python)
Actualizar `episodes_index.json` con:
- `"estado": "completado"`
- `"cerrado": "<timestamp>"`

---

## Script Python requerido
`src/scripts/cerrar_episodio.py`

---

## Salida
- `<EP_PATH>/99_notebooklm_pack.md` generado.
- `episodes_index.json` actualizado con estado "completado".
