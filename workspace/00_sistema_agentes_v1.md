# 📄 `workspace/00_sistema_agentes_v1.md`

## Documento Maestro del Sistema — Proyecto YouTube (V1.2)

**Proyecto:** `proyecto_youtube`
**Versión:** 1.2
**Fecha de creación:** 19 de febrero de 2026
**Última actualización:** 20 de febrero de 2026
**Estado:** Documento Maestro/Norte — Fuente de verdad única del sistema
**Objetivo:** Operar un pipeline de producción de episodios de YouTube de forma repetible, organizada y escalable.

> **Frase estándar oficial (roles vs agentes):**
> El sistema se organiza por **roles del pipeline**. En V1, todos los roles son ejecutados por **Antigravity (agente único)**.
> En V2+, los roles podrán convertirse en agentes independientes orquestados por Python
> (y opcionalmente multi-modelo por configuración). Ver sección 6 para el detalle de escalamiento.

---

## 0. Norte del Proyecto (Documento Maestro)

**Este archivo es la guía única de verdad del sistema.** Si hay contradicción entre cualquier otro documento y este, **este documento manda**.

### Referencias obligatorias (leer antes de operar)

| Documento | Qué contiene |
|---|---|
| [`workspace/01_canal_identidad.md`](../workspace/01_canal_identidad.md) | Objetivo del canal, enfoque emocional, público y promesa |
| [`workspace/05_estilo_y_voz.md`](../workspace/05_estilo_y_voz.md) | Tono, voz, muletillas permitidas y prohibidas |
| [`workspace/07_arquitectura_storage_repo_vs_vault_v1_2.md`](../workspace/07_arquitectura_storage_repo_vs_vault_v1_2.md) | Arquitectura Repo vs Vault, rutas reales |
| [`workspace/02_reglas_editoriales.md`](../workspace/02_reglas_editoriales.md) | Reglas de contenido y formato editorial |
| [`workspace/03_formato_longform.md`](../workspace/03_formato_longform.md) | Estructura del guion longform |
| [`.agent/workflows/01_pipeline_episodio.md`](../.agent/workflows/01_pipeline_episodio.md) | Secuencia operativa completa (fases + gates) |

### Cuándo actualizar este documento
- Cuando cambie la arquitectura del sistema (nuevos scripts, nuevos roles, nuevas fases).
- Cuando se agregue un nuevo tipo de gate o contrato de entregables.
- Siempre actualizar `Última actualización` y el número de versión.

---

## 1) Idea central del sistema

Este proyecto se opera con una lógica simple:

* **NotebookLM = cerebro (fuentes y memoria acumulativa)**
* **Antigravity = manos (ejecución, agentes, workflows, entregables)**

El objetivo es producir capítulos de YouTube de forma **repetible, organizada y escalable**, sin improvisación y sin perder consistencia.

---

## 2) Regla de oro: Antigravity es ejecutor, no adivino

Antigravity actúa como “equipo de producción” dentro del repositorio, pero debe cumplir estas reglas:

### Reglas duras

* **No inventar información** sobre obras, autores, escenas o datos.
  Si falta algo: marcar como **PENDIENTE** y solicitarlo.
* **Siempre leer primero `workspace/`** antes de escribir estructura, guion o packaging.
* **Cada fase debe dejar un archivo de salida**. No se avanza “a ojo”.
* **Sin código muerto / sin duplicar documentos**: si un archivo deja de servir, se elimina o se reemplaza limpiamente.
* **Entregable limpio**: evitar contaminar el repo con carpetas locales que no pertenecen a la entrega (por ejemplo, entornos virtuales).

---

## 3) Fuente de verdad del canal (obligatoria)

Antes de cualquier generación, los agentes deben usar estos documentos como referencia principal:

* `workspace/01_canal_identidad.md`
* `workspace/02_reglas_editoriales.md`
* `workspace/03_formato_longform.md`
* `workspace/05_estilo_y_voz.md`
* Cualquier política adicional del proyecto (clichés/patrones, etc.)

Esto evita que el contenido se vuelva genérico o “sin personalidad”.

---

## 4) Entrega final obligatoria por capítulo

Todo capítulo debe terminar con estos 4 entregables finales:

1. **Guion longform** (listo para grabar)
2. **Shorts derivados** (3–10 piezas)
3. **Packaging** (títulos + concepto de miniatura + prompts si aplica)
4. **SEO YouTube** (descripción + capítulos + keywords/tags sugeridos)

Estos entregables se generan al final, pero dependen de fases previas.

---

## 5) Estructura de fases (pipeline) y archivos esperados

> El sistema funciona con “gates”: si falta un archivo, no se puede pasar a la siguiente fase.

### Fase 0 — Preparación del episodio

**Entrada mínima:**

* Tema central del video (ej: “Abandono”)
* Intención del episodio (qué quiere provocar en la audiencia)

**Salida:**

* `<EP_PATH>/00_brief_episodio.md`
  (tema, objetivo emocional, límites, enfoque, advertencias spoiler)

---

### Fase 1 — Investigación (teoría + obras candidatas)

**Objetivo:** entender el tema y encontrar material narrativo útil.

**Salida:**

* `<EP_PATH>/01_research_bruto.md`

  * Definición del tema (psicológica, social, narrativa)
  * 5–8 obras candidatas (libros/películas/series)
  * Por qué cada obra aplica al tema
  * Notas de riesgo (spoilers/sensibilidad)

> Si se usa NotebookLM: esta fase alimenta cuadernos y extrae síntesis verificable.

---

### Fase 2 — Curación (selección final de obras)

**Objetivo:** escoger 3–5 obras con alto valor para el episodio.

**Salida:**

* `<EP_PATH>/02_curation_obras.md`

  * Obras seleccionadas (3–5)
  * Justificación clara
  * Qué aporta cada una al tema

---

### Fase 3 — Mapa de eventos y estructura del video

**Objetivo:** convertir el tema en una ruta clara para un capítulo longform.

**Salida:**

* `<EP_PATH>/03_mapa_eventos.md`

  * Secuencia de “eventos/segmentos”
  * Qué emoción se activa en cada parte
  * Dónde van re-hooks / micro loops

**Workflow recomendado:**

* `.agent/workflows/piloto-outline.md`

---

### Fase 4 — Análisis profundo (emocional / social / conductual)

**Objetivo:** sacar conclusiones útiles para la audiencia, no solo “resumen de obra”.

**Salida:**

* `<EP_PATH>/04_analisis_patrones.md`
  Para cada obra:

  * Lectura emocional (qué duele, qué cambia, qué se evita)
  * Lectura social (relaciones, roles, poder, contexto)
  * Lectura conductual (decisiones, reacciones, patrones)
  * Conexión directa con el tema del episodio

---

### Fase 5 — Síntesis (tesis y promesa del episodio)

**Objetivo:** unir todo en una idea central que guíe el guion.

**Salida:**

* `<EP_PATH>/05_sintesis_tesis.md`

  * Tesis del video (una frase clara)
  * 3–5 ideas fuerza
  * Promesa al espectador (qué se lleva)
  * Cierre esperado (reflexión final)

---

### Fase 6 — Guion longform (listo para grabar)

**Objetivo:** entregar el guion completo con tono del canal y estructura pensada para retención.

**Salida obligatoria final #1:**

* `<EP_PATH>/06_guion_longform.md`

---

### Fase 7 — QA editorial (anti-clichés y coherencia)

**Objetivo:** asegurar calidad humana, evitar muletillas genéricas y frases “IA”.

**Salida:**

* `<EP_PATH>/07_qa_revisiones.md`

  * Frases marcadas (por qué son problema)
  * Propuestas de reemplazo
  * Checklist final de cumplimiento editorial

---

### Fase 8 — Shorts (derivados del guion)

**Objetivo:** generar piezas cortas coherentes, cada una con hook y remate.

**Salida obligatoria final #2:**

* `<EP_PATH>/08_shorts.md`

---

### Fase 9 — Packaging (títulos + miniatura)

**Objetivo:** maximizar CTR sin traicionar el contenido.

**Salida obligatoria final #3:**

* `<EP_PATH>/09_packaging.md`
  Incluye:

  * 8–15 títulos (A/B/C) con intención distinta
  * 3–5 conceptos de miniatura (texto + composición)
  * Prompts de miniatura (si aplica)

---

### Fase 10 — SEO YouTube (búsqueda e intención)

**Objetivo:** dejar el video listo para publicar con base SEO simple.

**Salida obligatoria final #4:**

* `<EP_PATH>/10_seo.md`
  Incluye:

  * Descripción (estructura clara)
  * Keywords objetivo
  * Tags sugeridos
  * Capítulos (timestamps propuestos)

---

## 6) Roles del Pipeline (quién hace qué)

> **Estado actual (V1.1):** Todos los roles son ejecutados por Antigravity.
> **Futuro (V2+):** Cada rol puede ser asignado a un agente independiente con su propio modelo.
> La configuración futura vive en `config/agents_config.example.json`.

### Rol 1 — Orquestador
* Coordina el pipeline por fases
* Verifica gates (Gate 0 = `src/scripts/gate0_auditoria.py`)
* No permite avanzar con archivos faltantes
* **Skill:** Ninguno propio — es el agente principal

### Rol 2 — Investigador
* Produce `<EP_PATH>/01_research_bruto.md`
* Si usa NotebookLM: crea/consulta cuadernos y extrae síntesis
* **Skill:** `skill_research_tema_y_obras.md`
* **Futuro:** Agente con Perplexity / GPT-4o-search

### Rol 3 — Curador
* Produce `<EP_PATH>/02_curation_obras.md`
* Evalúa valor narrativo y riesgo spoiler
* **Skill:** `skill_curation_obras.md`
* **Futuro:** Agente con Claude 3.5 Sonnet

### Rol 4 — Planner
* Produce `<EP_PATH>/03_mapa_eventos.md`
* Usa workflow `piloto-outline.md`
* **Skill:** `skill_mapa_eventos_y_outline.md`
* **Futuro:** Agente con Claude 3.5 Sonnet o Gemini 1.5 Pro

### Rol 5 — Analista
* Produce `<EP_PATH>/04_analisis_patrones.md`
* Mantiene enfoque emocional/social/conductual
* **Skill:** `skill_analisis_patrones.md`
* **Futuro:** Agente con Claude 3.5 Sonnet

### Rol 6 — Sintetizador
* Produce `<EP_PATH>/05_sintesis_tesis.md`
* **Skill:** `skill_sintesis_tesis.md`
* **Futuro:** Agente con Claude 3.5 Sonnet

### Rol 7 — Guionista
* Produce `<EP_PATH>/06_guion_longform.md`
* Aplica reglas editoriales + estilo
* **Skill:** `skill_guion_longform.md`
* **Futuro:** Agente con Gemini 1.5 Pro o GPT-4o

### Rol 8 — QA Editorial
* Produce `<EP_PATH>/07_qa_revisiones.md`
* Aplica política anti-clichés/anti-genérico
* **Skill:** `skill_qa_editorial.md`
* **Futuro:** Agente con Claude 3.5 Sonnet

### Rol 9 — Shorts Writer
* Produce `<EP_PATH>/08_shorts.md`
* Deriva siempre desde el guion, no desde ideas sueltas
* **Skill:** `skill_shorts.md`
* **Futuro:** Agente con Gemini 1.5 Flash o GPT-4o-mini

### Rol 10 — Packaging
* Produce `<EP_PATH>/09_packaging.md`
* Trabaja títulos + miniatura como conjunto
* **Skill:** `skill_packaging.md`
* **Futuro:** Agente con GPT-4o

### Rol 11 — SEO
* Produce `<EP_PATH>/10_seo.md`
* Con intención y estructura, sin "relleno"
* **Skill:** `skill_seo_youtube.md`
* **Futuro:** Agente con GPT-4o o Gemini 1.5 Flash

---

## 7. Arquitectura en 3 Actos (NotebookLM → Guion → Producción)

El pipeline se divide en 3 actos lógicos. Cada acto tiene entradas, salidas y herramientas definidas.

### Acto 1 — Investigación y Curación (NotebookLM)

**Herramienta principal:** NotebookLM (cerebro y memoria).
**Modo por defecto:** "Sentimiento primero" — partir del concepto emocional y buscar obras que lo representen.
**Modo alternativo:** "Obra primero" — partir de una obra conocida y derivar el concepto emocional.
**Ambos modos desembocan en el mismo entregable.**

**Salida obligatoria del Acto 1:**
- `<EP_PATH>/01_research_bruto.md` — investigación bruta con obras candidatas
- `<EP_PATH>/02_curation_obras.md` — selección final de 3–5 obras con justificación

> Si se usa NotebookLM, las obras y análisis deben estar sustentados en citas o referencias verificables.
> **No se avanza al Acto 2 sin una selección curada confirmada.**

---

### Acto 2 — Guion Longform (Antigravity)

**Herramienta principal:** Antigravity + reglas de `workspace/`.
**Fuente única permitida:** el resultado del Acto 1 + reglas editoriales de `workspace/`.

**Salida obligatoria del Acto 2:**
- `<EP_PATH>/06_guion_longform.md` — guion completo listo para grabar

> Antigravity no puede inventar datos sobre obras. Todo lo que no esté en el Acto 1 se marca `PENDIENTE`.

---

### Acto 3 — Producción (Derivados y Cierre)

**Herramienta:** Antigravity + scripts Python.
**Fuente exclusiva:** `<EP_PATH>/06_guion_longform.md`.

**Salidas obligatorias del Acto 3:**
- `<EP_PATH>/08_shorts.md`
- `<EP_PATH>/09_packaging.md`
- `<EP_PATH>/10_seo.md`
- `<EP_PATH>/99_notebooklm_pack.md` (pack de cierre para NotebookLM)

**Cierre determinista:**
- `src/scripts/cerrar_episodio.py` valida los 4 entregables obligatorios y marca el episodio como `completado`.

---

## 8. Contrato de Entregables por Episodio (Vault)

Para que un episodio sea marcado como `DONE` en el índice, son **obligatorios** estos 4 entregables:

| # | Archivo | Acto |
|---|---|---|
| 1 | `<EP_PATH>/06_guion_longform.md` | Acto 2 |
| 2 | `<EP_PATH>/08_shorts.md` | Acto 3 |
| 3 | `<EP_PATH>/09_packaging.md` | Acto 3 |
| 4 | `<EP_PATH>/10_seo.md` | Acto 3 |

### Contrato de inicio (anti-sobrescritura)

Antes de empezar cualquier episodio:
```
python src/scripts/iniciar_episodio.py --num <NUM> --slug <SLUG>
```
- Crea `<EP_PATH>` en el Vault.
- Registra el episodio en `<VAULT_ROOT>/<CHANNEL_ID>/index/episodes_index.json`.
- Bloquea si ya hay un episodio `en_progreso` sin cerrar.

### Contrato de cierre (determinista)

Para cerrar un episodio:
```
python src/scripts/cerrar_episodio.py
```
- Verifica los 4 entregables obligatorios.
- Si faltan → `🔴 STOP`. No se puede cerrar.
- Si están todos → actualiza el índice a `completado`.

---

## 9. Storage: Repo vs Vault

### Configuración activa

Los valores de entorno se leen **exclusivamente** desde:
- `config/local_settings.json` ← **local, no versionado** (fuente de verdad en producción)
- `config/local_settings.example.json` ← versionado, solo de ejemplo

```json
{
    "vault_root": "C:\\YT_VAULT",
    "channel_id": "MasAllaDelGuion",
    "episode_id_format": "ep_{num:04d}"
}
```

### Estructura del Vault

```
<VAULT_ROOT>/
  └── <CHANNEL_ID>/
        ├── episodios/
        │   └── ep_<ID>_<SLUG>/    ← EP_PATH
        │       ├── 00_brief_episodio.md
        │       ├── 06_guion_longform.md
        │       └── ...
        └── index/
            └── episodes_index.json
```

### Qué vive en el Repo (liviano)

| Carpeta | Contenido |
|---|---|
| `.agent/rules/` | Reglas y protocolos |
| `.agent/skills/` | Skills por rol |
| `.agent/workflows/` | Flujos operativos |
| `workspace/` | Documentación del canal |
| `templates/` | Plantillas reutilizables |
| `config/` | Configuración (no el `.json` local) |
| `src/scripts/` | Scripts Python deterministas |
| `output/` | **Solo auditorías y reportes del sistema** |

> **Regla:** el contenido episódico (guiones, shorts, packaging, SEO) **nunca** va en `output/` del repo. Siempre en `<EP_PATH>` del Vault.

---

## 10. Gates Operativos Reales (Python)

El sistema usa gates deterministas (Python) para verificar antes de avanzar.
La secuencia operativa completa está en `.agent/workflows/01_pipeline_episodio.md`.

### Gate 0 — Sistema (pre-producción)

Verifica entorno completo antes de cualquier episodio.

```
python src/scripts/gate0_auditoria.py
```
- Verifica config, carpetas del repo y estructura del Vault.
- Output: `output/auditoria_sistema_v1.md` con `ESTADO_GLOBAL`.

```
python src/scripts/gate0_integridad.py
```
- Escanea episodios en el Vault, detecta incompletos.
- Output: `output/control_integridad_pipeline.md` con `ESTADO_GLOBAL`.

**Decisión Gate 0:**

| Auditoría | Integridad | Decisión |
|---|---|---|
| OK | OK | 🟢 Continuar |
| OK | WARN | 🟡 Confirmar con usuario |
| FAIL (cualquiera) | — | 🔴 DETENER |

---

### Gate 1 — Inicio de Episodio

Verifica que no hay colisiones antes de crear el contenido.

```
python src/scripts/iniciar_episodio.py --num <N> --slug <SLUG>
```

---

### Gate V — Veracidad (NotebookLM)

Verifica que el guion no contenga datos inventados antes de producir derivados.

**Output obligatorio:**
`<EP_PATH>/07_verificacion_veracidad_notebooklm.md`

> Este gate se ejecuta mediante `skill_verificacion_veracidad_notebooklm.md` y es obligatorio para el cierre.

---

### Gate de Cierre — Entregables Completos

```
python src/scripts/cerrar_episodio.py
```
- Valida los 4 entregables obligatorios (ver sección 8).
- Si todos presentes → episodio `completado` en el índice.

---

## 11. Resultado Esperado del Sistema

Cuando el sistema opera correctamente, cada episodio produce:

* Guion longform fuerte y coherente (listo para grabar)
* 3–10 shorts derivados del guion
* Packaging listo para subir (títulos + concepto de miniatura)
* SEO básico coherente (descripción + tags + timestamps)
* Conocimiento reutilizable en NotebookLM (vía `99_notebooklm_pack.md`)

---

## 12. Nota Operativa del Entorno

El desarrollo se ejecuta actualmente en **Windows**.
La arquitectura es portable: los scripts Python no usan rutas hardcodeadas.
Cualquier migración a WSL/Linux solo requiere actualizar `config/local_settings.json`.

---

## 13. Bitácora de Cambios (Resumen)

| Fecha | Versión | Qué se alineó | PENDIENTE |
|---|---|---|---|
| 19/02/2026 | V1.0 | Estructura inicial de agentes y fases | Rutas inconsistentes |
| 19/02/2026 | V1.1 | Roles del Pipeline, Vault, rutas `<EP_PATH>`, scripts Gate 0 | Scripts `iniciar/cerrar` |
| 20/02/2026 | V1.2 | Sección Norte, 3 Actos, Contratos, Gates reales, Storage, Bitácora | Gate V (veracidad) sin skill |

**PENDIENTES detectados a V1.2:**
- ⚠️ `skill_verificacion_veracidad.md` — no existe. Gate V es manual hasta que se cree.
- ⚠️ Guion ejemplo en `reference/estilo_usuario/` — referenciado en `workspace/05_estilo_y_voz.md` pero no existe. Agregar cuando haya guion piloto aprobado.
