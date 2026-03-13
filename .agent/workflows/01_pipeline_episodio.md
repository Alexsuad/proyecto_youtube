---
description: Workflow orquestador del pipeline completo de episodio (Fases 0-10). Realiza Gate 0, inicia el episodio en el Vault, recorre cada fase verificando gates, y cierra al final.
---

# Workflow: Pipeline Completo de Episodio (Orquestador)

> **Ejecutor actual:** Antigravity como agente único.
> **Futuro:** Cada fase puede ser ejecutada por un agente independiente.
> **Regla de oro:** No se avanza a la siguiente fase si no existe el entregable de la fase actual.

---

## PREREQUISITOS (leer antes de comenzar)

Antigravity debe tener disponibles:
- `config/local_settings.json` con `vault_root` y `channel_id`
- El **tema** del episodio y su **slug** confirmados por el usuario
- El **número** de episodio (siguiente al último registrado)

---

## FASE 0 — Gate 0 (Control previo a producción)

**Objetivo:** Verificar que el entorno está limpio y listo.

### Paso 0.1 — Auditoría de sistema
// turbo
```
python src/scripts/gate0_auditoria.py
```
- Leer `output/auditoria_sistema_v1.md`
- Extraer `ESTADO_GLOBAL`
- Si `FAIL` → **🔴 DETENER** y reportar al usuario.

### Paso 0.2 — Integridad del pipeline
// turbo
```
python src/scripts/gate0_integridad.py
```
- Leer `output/control_integridad_pipeline.md`
- Extraer `ESTADO_GLOBAL`
- Si `FAIL` → **🔴 DETENER**.
- Si `WARN` → notificar al usuario y esperar confirmación antes de continuar.

### Gate 0 — Decisión final
| Auditoría Sistema | Integridad Pipeline | Decisión |
|---|---|---|
| OK | OK | 🟢 Continuar |
| OK | WARN | 🟡 Continuar con advertencia (confirmar con usuario) |
| FAIL (cualquiera) | cualquiera | 🔴 DETENER |

---

## FASE 1 — Iniciar Episodio en Vault

**Objetivo:** Crear la carpeta del episodio y registrarla en el índice.

### Paso 1.1 — Ejecutar script de inicio
// turbo
```
python src/scripts/iniciar_episodio.py --num <NUM> --slug <SLUG>
```
- Capturar `EP_PATH` del output del script.
- Mantener `EP_PATH` como variable de contexto para todas las fases siguientes.

**⛔ Gate:** Si el script retorna error → DETENER. No improvisar rutas.

---

## FASE 2 — Brief del Episodio

**Objetivo:** Crear el brief base que guiará todo el pipeline.

### Paso 2.1 — Ejecutar skill
- Skill: `skill_crear_brief_episodio.md`
- Leer: `workspace/01_canal_identidad.md`, `workspace/05_estilo_y_voz.md`
- Crear: `<EP_PATH>/00_brief_episodio.md`

---

## FASE 3 — Investigación y QA (Momento 1)

**Objetivo:** Extender el brief con investigación profunda e identificar obras sin inventar datos, validando un estándar estricto de calidad.

### Paso 3.1 — Ejecutar skill de Research
- Skill: `skill_research_tema_y_obras.md`
- Entrada: `<EP_PATH>/00_brief_episodio.md`
- Crear: `<EP_PATH>/01_research_bruto.md`

### Paso 3.2 — QA Automático del Momento 1
- Skill: `skill_qa_brief_research.md` 
// turbo
```
python src/scripts/qa_brief_research.py --ep_path <EP_PATH>
```
- Leer el reporte generado en `output/auditoria_brief_research_<EP_NAME>.md`
- Si el `ESTADO_GLOBAL` es `FAIL` → **🔴 DETENER** y corregir los entregables según la lista. No pedir revisión humana hasta que sea `PASS`.

### Paso 3.3 — Revisión del usuario (Gate Humano del Momento 1)
- **⛔ Gate:** El usuario debe revisar y aprobar explícitamente el brief y la investigación antes de pasar a estructura.
- Preguntar: "¿La investigación y la tesis están correctas? ¿Damos check al Momento 1?"

---

## FASE 4 — Curación de Obras

**Objetivo:** Reducir de 5–8 candidatas a 3–5 obras seleccionadas.

### Paso 4.1 — Ejecutar skill
- Skill: `skill_curation_obras.md`
- Entrada: `<EP_PATH>/01_research_bruto.md`
- Crear: `<EP_PATH>/02_curation_obras.md`

### Paso 4.2 — Confirmación del usuario
- **⛔ Gate:** Usuario confirma obras seleccionadas antes de continuar.
- Preguntar: "¿Las obras son correctas? ¿Procedo con el mapa de eventos?"

---

## FASE 5 — Mapa de Eventos y Outline

**Objetivo:** Crear la estructura narrativa del episodio.

### Paso 5.1 — Ejecutar skill + workflow
- Skill: `skill_mapa_eventos_y_outline.md`
- Workflow interno: `piloto-outline.md`
- Entradas: `<EP_PATH>/00_brief_episodio.md`, `<EP_PATH>/02_curation_obras.md`
- Crear:
  - `<EP_PATH>/03_mapa_eventos.md` (obligatorio)
  - `<EP_PATH>/05_outline_escenas.md` (si aplica)

**⛔ Gate:** Verificar que `03_mapa_eventos.md` exista.

---

## FASE 6 — Análisis de Patrones

**Objetivo:** Análisis emocional, social y conductual por obra.

### Paso 6.1 — Ejecutar skill
- Skill: `skill_analisis_patrones.md`
- Entrada: `<EP_PATH>/02_curation_obras.md`
- Crear: `<EP_PATH>/04_analisis_patrones.md`

**⛔ Gate:** Verificar que `04_analisis_patrones.md` exista.

---

## FASE 7 — Síntesis y Tesis

**Objetivo:** Unir todo en una idea central que guíe el guion.

### Paso 7.1 — Ejecutar skill
- Skill: `skill_sintesis_tesis.md`
- Entradas: `<EP_PATH>/03_mapa_eventos.md`, `<EP_PATH>/04_analisis_patrones.md`
- Crear: `<EP_PATH>/05_sintesis_tesis.md`

**⛔ Gate:** Verificar que `05_sintesis_tesis.md` exista.

---

## FASE 7.5 — Gate Pre-Guion (QA Lenguaje YouTube)

**Objetivo:** Auditar el Brief, el Mapa de Patrones y la Síntesis antes de mandar al guionista, evitando que palabras penalizables ("amarillas" o "rojas") se filtren a la redacción masiva.

### Paso 7.5.1 — Ejecutar script
- Skill: `skill_qa_lenguaje_youtube_ultra.md`
// turbo
```
python src/scripts/qa_lenguaje_youtube_ultra.py --ep_path <EP_PATH> --fase pre-guion
```
- Leer el reporte generado en `output/qa_youtube_lenguaje/<EP_NAME>__qa_youtube_ultra.md`
- Si el `ESTADO_GLOBAL` es `FAIL` → **🔴 DETENER** y cambiar los términos marcados antes de escribir el guion.

---

## FASE 8 — Guion Longform

**Objetivo:** Escribir el guion completo listo para grabar.

### Paso 8.1 — Ejecutar skill
- Skill: `skill_guion_longform.md`
- Entradas: `<EP_PATH>/03_mapa_eventos.md`, `<EP_PATH>/05_sintesis_tesis.md`
- Leer: `workspace/02_reglas_editoriales.md`, `workspace/03_formato_longform.md`, `workspace/05_estilo_y_voz.md`
- Crear: `<EP_PATH>/06_guion_longform.md`

### Paso 8.2 — Revisión del usuario
- **⛔ Gate HUMANO (obligatorio):** El usuario debe leer y aprobar el guion.
- Preguntar: "¿El guion está listo para QA?"

---

## FASE 8.8 — QA de Duración (Determinista)

**Objetivo:** Validar que el guion tiene la longitud adecuada para el target del canal.

### Paso 8.8.1 — Ejecutar script de duración
// turbo
```
python src/scripts/qa_duracion_guion.py --ep_path <EP_PATH> --min_target 18 --max_target 22
```
- Leer el reporte en `output/qa_duracion/<EP_NAME>__qa_duracion.md`
- Si `ESTADO_GLOBAL` es `FAIL` → Notificar recomendación (recortar/expandir) y decidir si se procede o se ajusta.

---

## FASE 9 — QA Editorial

**Objetivo:** Detectar clichés, frases "IA" e incoherencias de voz.

### Paso 9.1 — Ejecutar skill
- Skill: `skill_qa_editorial.md`
- Entrada: `<EP_PATH>/06_guion_longform.md`
- Crear: `<EP_PATH>/07_qa_revisiones.md`

### Paso 9.2 — Aplicar correcciones
- Si hay correcciones sustanciales: volver a Fase 8 y actualizar el guion.
- Si son menores: aplicar directamente y continuar.

**⛔ Gate:** `07_qa_revisiones.md` debe existir.

---

## FASE 9.5 — Gate V: Verificación de Veracidad (NotebookLM)

**Objetivo:** Confirmar que los hechos del guion están respaldados por las fuentes del Acto 1, antes de producir derivados.

> ⚠️ Este gate protege contra la propagación de datos incorrectos a shorts, packaging y SEO.

### Paso 9.5.1 — Ejecutar skill
- Skill: `skill_verificacion_veracidad_notebooklm.md`
- Entradas:
  - `<EP_PATH>/01_research_bruto.md`
  - `<EP_PATH>/02_curation_obras.md`
  - `<EP_PATH>/06_guion_longform.md`
- Crear: `<EP_PATH>/07_verificacion_veracidad_notebooklm.md`
- Template: `templates/verificacion_veracidad_notebooklm_template.md`

### Paso 9.5.2 — Evaluar ESTADO_GLOBAL
Leer `07_verificacion_veracidad_notebooklm.md` y extraer `ESTADO_GLOBAL`:

| ESTADO_GLOBAL | Acción |
|---|---|
| `OK` | 🟢 Continuar a Fase 10 |
| `WARN` | 🟡 **DETENER** — corregir guion, volver a Fase 9.5 |
| `FAIL` | 🔴 **STOP OBLIGATORIO** — corregir guion (Fase 8), luego repetir QA y Gate V |

**⛔ Gate:** `07_verificacion_veracidad_notebooklm.md` debe existir Y contener `ESTADO_GLOBAL: OK`.

---

## FASE 9.8 — Gate Post-Guion (QA Lenguaje YouTube Final)

**Objetivo:** Última red de seguridad algorítmica. Audita el Guion, Packaging y SEO para certificar que el contenido que leerá el Bot de YouTube está higienizado y 100% monetizable.

### Paso 9.8.1 — Ejecutar script
- Skill: `skill_qa_lenguaje_youtube_ultra.md`
// turbo
```
python src/scripts/qa_lenguaje_youtube_ultra.py --ep_path <EP_PATH> --fase post-guion
```
- Leer el reporte generado en `output/qa_youtube_lenguaje/<EP_NAME>__qa_youtube_ultra.md`
- Si el `ESTADO_GLOBAL` es `FAIL` → **🔴 DETENER** y corregir los términos en el guion o empaquetado.

---

## FASE 10 — Entregables Finales (paralelo)

**Objetivo:** Generar los 3 entregables finales a partir del guion aprobado.

### Paso 10.1 — Shorts
- Skill: `skill_shorts.md`
- Entrada: `<EP_PATH>/06_guion_longform.md`
- Crear: `<EP_PATH>/08_shorts.md`

### Paso 10.2 — Packaging
- Skill: `skill_packaging.md`
- Entradas: `<EP_PATH>/06_guion_longform.md`, `<EP_PATH>/05_sintesis_tesis.md`
- Crear: `<EP_PATH>/09_packaging.md`

### Paso 10.3 — SEO
- Skill: `skill_seo_youtube.md`
- Entradas: `<EP_PATH>/06_guion_longform.md`, `<EP_PATH>/05_sintesis_tesis.md`
- Crear: `<EP_PATH>/10_seo.md`

**⛔ Gate:** Los 3 deben existir antes de continuar.

---

## FASE 11 — Cierre del Episodio

**Objetivo:** Validar entregables y marcar el episodio como completado en el Vault.

### Paso 11.1 — Cerrar episodio (determinista)
// turbo
```
python src/scripts/cerrar_episodio.py
```
- Si hay faltantes obligatorios → 🔴 STOP. Completar antes de cerrar.
- Si `07_verificacion_veracidad_notebooklm.md` tiene ESTADO_GLOBAL distinto de OK → 🔴 STOP.
- Si todo OK → episodio marcado como `completado` en `episodes_index.json`.

### Paso 11.2 — Generar pack NotebookLM (IA)
- Skill: `skill_cerrar_episodio.md` (Paso B — generación del pack)
- Crear: `<EP_PATH>/99_notebooklm_pack.md`

---

## RESUMEN DE GATES

| Fase | Entregable Gate | Tipo de verificación |
|---|---|---|
| 0 | ESTADO_GLOBAL en reportes | Python (script) |
| 1 | EP_PATH creado | Python (script) |
| 2 | `00_brief_episodio.md` | Humano (confirmación) |
| 3 | `01_research_bruto.md` | IA (verificar existencia) |
| 4 | `02_curation_obras.md` | Humano (confirmar obras) |
| 5 | `03_mapa_eventos.md` | IA (verificar existencia) |
| 6 | `04_analisis_patrones.md` | IA (verificar existencia) |
| 7 | `05_sintesis_tesis.md` | IA (verificar existencia) |
| **7.5** | **`qa_youtube_ultra.md` + ESTADO_GLOBAL: PASS** | **Python (script)** |
| 8 | `06_guion_longform.md` | **Humano (revisar guion)** |
| 9 | `07_qa_revisiones.md` | IA (verificar existencia) |
| **9.5** | **`07_verificacion_veracidad_notebooklm.md` + ESTADO_GLOBAL: OK** | **IA + NotebookLM (Gate V)** |
| **9.8** | **`qa_youtube_ultra.md` + ESTADO_GLOBAL: PASS** | **Python (script)** |
| 10 | Los 3 entregables finales | IA (verificar existencia) |
| 11 | `cerrar_episodio.py` OK | Python (script) |
