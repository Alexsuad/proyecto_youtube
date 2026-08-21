---
trigger: always_on
---

# Formato estándar de outputs — Proyecto YouTube
Versión: 1.3
Fecha: 27/07/2026

---

## 1) Ubicación de Archivos (V1.3 - ruta portable y adaptador Vault legacy)

**REPO (Este repositorio):**
La carpeta `output/` del repositorio se usa EXCLUSIVAMENTE para:
- Reportes de auditoría del sistema (Gate 0)
- Logs de ejecución y control de estado
- Documentos de diagnóstico del pipeline

**RUTA PORTABLE (actual):**
Los artefactos de un episodio pueden vivir dentro del checkout, bajo la ruta de episodio entregada al runtime. Esta es la ruta válida sin configuración local ni path físico predeterminado.

**CONTENT VAULT (adaptador legacy opcional):**
Cuando se conserva el flujo legacy, los archivos de trabajo de un episodio pueden generarse en:
`<VAULT_ROOT>/<CHANNEL_ID>/episodios/ep_<ID>_<SLUG>/`

Valores configurados en `config/local_settings.json`:
- `vault_root` = ruta local configurada por cada operador
- `channel_id` = identificador contractual del canal
- Ejemplo ruta episodio: `<VAULT_ROOT>/<CHANNEL_ID>/episodios/ep_0001_abandono/`

La configuración del Vault es necesaria únicamente para la ruta legacy que crea episodios con `iniciar_episodio.py`, pero no es autoridad universal ni dependencia de Gate 0 o del cierre moderno del MVP. Sin ella, Gate 0 continúa por la ruta portable con `WARN`.

---

## 2) Nombres estándar de archivos por episodio
Todos los paths son relativos a `<EP_PATH>` = ruta del episodio activo entregada por el runtime. Puede ser un checkout portable o una ruta del adaptador Vault legacy:

- `<EP_PATH>/00_brief_episodio.md`
- `<EP_PATH>/01_research_bruto.md`
- `<EP_PATH>/02_curation_obras.md`
- `<EP_PATH>/03_mapa_eventos.md`
- `<EP_PATH>/04_analisis_patrones.md`
- `<EP_PATH>/05_sintesis_tesis.md`
- `<EP_PATH>/06_guion_longform.md`
- `<EP_PATH>/06_guion_longform_limpio.md`
- `<EP_PATH>/06_guion_longform_anotado.md`
- `<EP_PATH>/07_qa_revisiones.md`
- `<EP_PATH>/script_version_manifest.json`
- `<EP_PATH>/editorial_script_approval.json`
- `<EP_PATH>/claims_ledger.json`
- `<EP_PATH>/final_delivery_manifest.json`

`<EP_PATH>` lo proporciona el contexto portable del runtime o, en el adaptador legacy, el índice de episodios. Ninguna ruta local concreta es autoridad editorial.

---

## 3) Estructura mínima dentro de cada archivo
- Título claro
- Objetivo del documento (1 párrafo)
- Secciones con encabezados
- Checklist final (si aplica)

---

## 4) Regla de consistencia
Si el usuario decide cambiar el formato, se actualiza este archivo.
El sistema nunca debe asumir rutas: las recibe del contexto portable o las resuelve desde la configuración/índice únicamente cuando se selecciona el adaptador legacy.
