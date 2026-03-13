# Convención de Outputs y NotebookLM (V1)

## Objetivo
Estandarizar cómo se guardan los archivos de cada episodio y qué información exacta se envía a NotebookLM para construir nuestro "cerebro" del canal.

---

## 1. Estructura de Carpetas (V1 - Actual)

Todo el trabajo de un episodio vive en el **Content Vault** externo.
La carpeta `output/` del repositorio se reserva únicamente para **logs de auditoría y reportes del sistema**.

### Flujo de Archivos (Dentro del Vault: `.../episodios/ep_xxxx_slug/`)

### Flujo de Archivos
1.  `00_brief_episodio.md` (Semilla)
2.  `01_research_bruto.md` (Investigación - **NO SUBIR A NOTEBOOKLM**)
3.  `02_curation_obras.md` (Selección de obras)
4.  `03_mapa_eventos.md` (Estructura)
5.  `04_analisis_patrones.md` (Análisis profundo)
6.  `05_sintesis_tesis.md` (La "verdad" del episodio)
7.  `06_guion_longform.md` (**FINAL** - Fuente principal para NotebookLM)
8.  `07_qa_revisiones.md` (Control de calidad)
9.  `08_shorts.md` (**FINAL** - Derivados)
10. `09_packaging.md` (**FINAL** - Títulos/Miniaturas)
11. `10_seo.md` (**FINAL** - Metadatos)
12. `99_notebooklm_pack.md` (**INDICE** - Resumen para subir)

*(Nota V1.2: Esta estructura ahora vive dentro de la carpeta del episodio en el VAULT, no en el repositorio)*

---

## 2. Convención NotebookLM

NotebookLM no es un basurero de archivos. Es la memoria limpia del canal.
**Solo le damos "verdades terminadas", no "borradores confusos".**

### ¿Qué se sube?
Únicamente el **Paquete Final** definido en `99_notebooklm_pack.md`.

-   **SI Sube:** Guiones finales, Shorts finales, Packaging final, SEO final.
-   **NO Sube:** Research bruto, notas de reunion, borradores intermedios.

### Convención de nombres para fuentes en NotebookLM (V1)

Cada archivo subido a NotebookLM debe renombrarse con este patrón:

```
EPI_<EP_ID>__<SLUG>__<TIPO>
```

Donde `<TIPO>` es uno de:
- `GUION` → para `06_guion_longform.md`
- `SHORTS` → para `08_shorts.md`
- `PACKAGING` → para `09_packaging.md`
- `SEO` → para `10_seo.md`
- `PACK` → para `99_notebooklm_pack.md`

**Ejemplos:**
- `EPI_ep_0007__duelo_y_culpa__GUION`
- `EPI_ep_0007__duelo_y_culpa__SHORTS`
- `EPI_ep_0007__duelo_y_culpa__PACK`

> ✅ Razón: permite buscar y automatizar consultas futuras en NotebookLM sin ambigüedades.

---

### ¿Cómo usar `99_notebooklm_pack.md`?
Al terminar un episodio, Antigravity (usando `skill_cerrar_episodio.md`) debe generar este archivo usando la plantilla `templates/99_notebooklm_pack_template.md`.
Este archivo actúa como una "hoja de remito" o "packing list".

### Control de Repetición (El "Test de Historia")
Antes de aprobar un tema nuevo, usamos NotebookLM para preguntar:
*"¿Qué episodios ya hemos hecho sobre [TEMA]? ¿Qué obras hemos analizado ya?"*
Esto evita repetirnos y nos permite hacer referencias cruzadas inteligentes ("Como vimos en el episodio de X...").

---

## 3. Evolución a V2 — Biblioteca por Capítulos (FUTURO)

Actualmente (V1), todo vive plano en `output/` y se sobrescribe o archiva manualmente.
En el futuro (V2), implementaremos una **Biblioteca Permanente**.

### Ruta futura propuesta:
`reference/youtube_biblioteca/`

### Estructura (V2):
Dentro de esta biblioteca, cada episodio tendrá su propia carpeta inmutable:
`reference/youtube_biblioteca/capitulos/cap_001_abandono_emocional/`

Contenido de esa carpeta futura:
-   `guion_final.md`
-   `shorts.md`
-   `metadata.json` (Packaging + SEO)
-   `assets/` (Miniaturas generadas, etc.)

**Por qué esperar a V2:**
Primero necesitamos estabilizar el flujo de producción (V1) antes de automatizar el archivado permanente.
Por ahora, `99_notebooklm_pack.md` es nuestro puente manual hacia la gestión del conocimiento.
