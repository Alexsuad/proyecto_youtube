---
trigger: always_on
---

# Formato estándar de outputs — Proyecto YouTube
Versión: 1.2
Fecha: 19/02/2026

---

## 1) Ubicación de Archivos (V1.2 - Vault)

**REPO (Este repositorio):**
La carpeta `output/` del repositorio se usa EXCLUSIVAMENTE para:
- Reportes de auditoría del sistema (Gate 0)
- Logs de ejecución y control de estado
- Documentos de diagnóstico del pipeline

**CONTENT VAULT (Externo — fuente de verdad del contenido):**
Todos los archivos de trabajo de un episodio se generan en:
`<VAULT_ROOT>/<CHANNEL_ID>/episodios/ep_<ID>_<SLUG>/`

Valores configurados en `config/local_settings.json`:
- `vault_root` = `C:\YT_VAULT`
- `channel_id` = `MasAllaDelGuion`
- Ejemplo ruta episodio: `C:\YT_VAULT\MasAllaDelGuion\episodios\ep_0001_abandono\`

Si no hay Vault configurado, el sistema debe detenerse y pedir configuración.

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
- `<EP_PATH>/07_qa_revisiones.md`
- `<EP_PATH>/08_shorts.md`
- `<EP_PATH>/09_packaging.md`
- `<EP_PATH>/10_seo.md`
- `<EP_PATH>/99_notebooklm_pack.md`

`<EP_PATH>` se determina en el Gate 0 (`skill_iniciar_episodio`) y queda
registrado en `C:\YT_VAULT\MasAllaDelGuion\index\episodes_index.json`.

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
