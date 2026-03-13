# Skill — QA Lenguaje YouTube (Modo A Ultra Seguro)

Objetivo: Auditoría automática buscando lenguaje que afecte la distribución algorítmica y la monetización en YouTube bajo reglas ultraseguras.

> **Rol ejecutor actual:** Script de validación automatizada (`src/scripts/qa_lenguaje_youtube_ultra.py`).

---

## Entrada mínima
Requiere un parámetro temporal de fase: `--fase pre-guion` o `--fase post-guion`.
Además requiere el argumento `--ep_path` con la ruta al episodio.

- **PRE-GUION audita:**
  - `00_brief_episodio.md` (Título y Promesa)
  - `04_analisis_patrones.md`
  - `05_sintesis_tesis.md`
- **POST-GUION audita:**
  - `06_guion_longform.md` (Hook, guion general, CTA)
  - `09_packaging.md` (Títulos y Miniatura)
  - `10_seo.md` (Descripción y tags)

Dependencia: `config/qa_youtube_lenguaje_ultra_seguro.md`

---

## Pasos

1) Cargar el diccionario (listas roja y amarilla) y zonas críticas desde `config/qa_youtube_lenguaje_ultra_seguro.md`.
2) Leer el contenido de todos los archivos indicados para la fase seleccionada.
3) Detectar:
   - Términos en la Lista Roja → FAIL automático (independientemente del contexto).
   - Términos en la Lista Amarilla → FAIL si aparecen en zonas críticas (Título, Miniatura, Hook, Promesa, CTA). WARN si aparecen en el resto del cuerpo, sugiriendo un reemplazo suave.
4) Formatear un reporte con los hallazgos en formato Markdown Table (Palabra, Archivo, Ubicación, Severidad, Reemplazo).
5) Si hay un FAIL, detener el avance del pipeline.

---

## Salida
- Reporte detallado en: `output/qa_youtube_lenguaje/<ep_folder_name>__qa_youtube_ultra.md`
- ESTADO_GLOBAL: PASS o FAIL
