---
trigger: always_on
---

# Formato estándar de outputs — Proyecto YouTube
Versión: 1.3
Fecha: 27/07/2026

---

## 1) Ubicación de Archivos (V1.3 - Vault)

**REPO (Este repositorio):**
La carpeta `output/` del repositorio se usa EXCLUSIVAMENTE para:
- Reportes de auditoría del sistema (Gate 0)
- Logs de ejecución y control de estado
- Documentos de diagnóstico del pipeline

**CONTENT VAULT (Externo — fuente de verdad del contenido):**
Todos los archivos de trabajo de un episodio se generan en:
`<VAULT_ROOT>/<CHANNEL_ID>/episodios/ep_<ID>_<SLUG>/`

Valores configurados en `config/local_settings.json`:
- `vault_root` = ruta local configurada por cada operador
- `channel_id` = identificador contractual del canal
- Ejemplo ruta episodio: `<VAULT_ROOT>/<CHANNEL_ID>/episodios/ep_0001_abandono/`

La configuración del Vault es necesaria para la ruta legacy que crea episodios con `iniciar_episodio.py`, pero no es una dependencia universal de Gate 0 ni del cierre moderno del MVP. Sin ella, Gate 0 continúa por la ruta portable con `WARN`.

---

## 2) Nombres estándar de archivos por episodio (dentro del Vault)
Todos los paths son relativos a `<EP_PATH>` = ruta del episodio activo en el Vault:

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

`<EP_PATH>` se determina en el Gate 0 (`skill_iniciar_episodio`) y queda
registrado en `<VAULT_ROOT>/<CHANNEL_ID>/index/episodes_index.json`.

---

## 3) Estructura mínima dentro de cada archivo
- Título claro
- Objetivo del documento (1 párrafo)
- Secciones con encabezados
- Checklist final (si aplica)

---

## 4) Regla de consistencia
Si el usuario decide cambiar el formato, se actualiza este archivo.
El sistema nunca debe asumir rutas: siempre las lee desde la config o el índice.
