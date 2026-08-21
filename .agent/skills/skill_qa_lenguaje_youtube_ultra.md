# Skill — QA Lenguaje YouTube (Modo A Ultra Seguro)

> **STATUS:** `NON_CANONICAL_CURRENT` / `MERGE`. No ejecutar como gate independiente: la política canónica vigente es la de `skill_qa_lenguaje_youtube.md` hasta una consolidación autorizada.

Objetivo: Auditoría automática buscando lenguaje que afecte la distribución algorítmica y la monetización en YouTube bajo reglas ultraseguras.

> **Rol previsto:** wrapper de compatibilidad sobre la validación automatizada; no constituye un gate canónico independiente mientras permanezca en `MERGE`.

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

  Packaging final (`09_packaging.md`) y SEO (`10_seo.md`) pertenecen a la Etapa 2 diferida y no son entradas de este gate.

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
