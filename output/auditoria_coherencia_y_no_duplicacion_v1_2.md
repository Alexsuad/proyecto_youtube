# Auditoría de Coherencia y No-Duplicación — V1.2

**Fecha:** 20/02/2026
**Auditor:** Antigravity (modo lectura + propuesta — sin cambios automáticos)
**Alcance:** workspace/, .agent/rules/, .agent/skills/, .agent/workflows/, config/, src/scripts/

---

## 1. Resumen Ejecutivo

Se auditaron 30+ archivos del repo contra los 10 puntos de la matriz de coherencia.
El sistema V1.2 es operativamente correcto en su mayoría.
Se detectaron **3 contradicciones activas** (🔴) relacionadas con la incorporación del Gate V,
**5 desfasados/duplicaciones** (🟡), y **2 huérfanos potenciales** (🟡).
No hay ninguna contradicción que rompa el flujo central del pipeline si se ejecutan los scripts Python,
pero hay riesgo si un operador sigue `skill_cerrar_episodio.md` en lugar del script.

**ESTADO_GLOBAL: 🟡 WARN**
> 3 contradicciones activas de media severidad (Gate V). Sin ellas: OK.

---

## 2. Tabla de Hallazgos

| # | Sev | Tipo | Archivo A | Archivo B | Descripción | Recomendación |
|---|---|---|---|---|---|---|
| H1 | 🔴 | Contradicción | `.agent/skills/skill_cerrar_episodio.md` | `src/scripts/cerrar_episodio.py` | Skill lista 4 obligatorios; el script ya exige 5 (Gate V añadido) | Actualizar skill: añadir `07_verificacion_veracidad_notebooklm.md` |
| H2 | 🔴 | Contradicción | `.agent/rules/01_formato_outputs.md` (sección 2) | `src/scripts/cerrar_episodio.py` | Lista de archivos estándar omite `07_verificacion_veracidad_notebooklm.md` (ahora obligatorio) | Añadir la entrada faltante en la sección 2 |
| H3 | 🔴 | Contradicción | `workspace/00_sistema_agentes_v1.md` (sección 8) | `src/scripts/cerrar_episodio.py` | Doc Maestro lista 4 obligatorios para DONE; el script ya exige 5 | Actualizar sección 8 del Doc Maestro |
| H4 | 🟡 | Duplicación | `workspace/00_sistema_agentes_v1.md` (sección 9 Storage) | `workspace/07_arquitectura_storage_repo_vs_vault_v1_2.md` | Ambos definen la misma estructura Repo/Vault en detalle. Doble fuente de verdad | Hacer canónico el `07_arquitectura_storage_repo_vs_vault_v1_2.md`; en el Doc Maestro dejar solo enlace |
| H5 | 🟡 | Duplicación | `.agent/rules/00_reglas_globales.md` (sección 4) | `workspace/00_sistema_agentes_v1.md` (sección 8 Contrato) | Ambos listan los 4 entregables obligatorios con redacción diferente (y la regla ahora tampoco reflejará el 5to) | Reglas globales: referenciar al Doc Maestro en lugar de duplicar la lista |
| H6 | 🟡 | Duplicación | `workspace/06_convencion_outputs_y_notebooklm_v1.md` | `.agent/rules/01_formato_outputs.md` | Ambos definen el flujo de archivos del episodio y reglas NotebookLM | Marcar `workspace/06_` como guía narrativa; `01_formato_outputs.md` como operativo canónico |
| H7 | 🟡 | Doble Gate 0 | `.agent/workflows/00_control_pre_ejecucion.md` | `.agent/workflows/01_pipeline_episodio.md` (Fase 0) | El workflow `00_control_pre_ejecucion.md` delega a skills (IA); el `01_pipeline_episodio.md` delega a scripts Python. Son dos definiciones del mismo Gate 0, que divergen en el ejecutor | Aclarar que `00_control_pre_ejecucion.md` es el legacy/alternativo y `01_pipeline_episodio.md` es el canónico |
| H8 | 🟡 | Huérfano | `.agent/workflows/piloto-outline.md` | — | Referencia `input/brief_capitulo.md` (no existe; el equivalente es `templates/brief_capitulo_template.md`) | Corregir ruta: `templates/brief_capitulo_template.md` |
| H9 | 🟡 | Huérfano | `workspace/04_politica_spoilers.md` | — | Existe en disco pero NO está en la lista de fuentes de verdad del Doc Maestro (`workspace/00_sistema_agentes_v1.md`, sección 0) ni en `.agent/rules/00_reglas_globales.md` | Añadir referencia en las fuentes de verdad, o marcarlo como apéndice editorial |
| H10 | 🟡 | NotebookLM sin definir | `workspace/00_sistema_agentes_v1.md` (sección 7, Acto 1) | — | Doc Maestro menciona `01_notebooklm_context_pack.md` como salida del Acto 1, pero ese archivo no figura en `01_formato_outputs.md` ni existe en el Vault aún. No está definido contractualmente | Definir el archivo en `01_formato_outputs.md` o aclarar que es output futuro/opcional |

---

## 3. Contradicciones Operativas Activas (🔴)

### H1 — `skill_cerrar_episodio.md` vs `cerrar_episodio.py`

**Dónde:** `.agent/skills/skill_cerrar_episodio.md`, Paso A (líneas 18–22)
**Qué contradice:** `src/scripts/cerrar_episodio.py`, constante `ENTREGABLES_OBLIGATORIOS` (líneas 30–35)

**Por qué confunde:**
El skill dice que los obligatorios son 4 (`06`, `08`, `09`, `10`).
El script Python ahora exige 5 (se añadió `07_verificacion_veracidad_notebooklm.md` + Gate V).
Si un operador lee el skill y no el script, asumirá que puede cerrar sin Gate V.

**Micro-fix propuesto:**
En `.agent/skills/skill_cerrar_episodio.md`, Paso A:
```
Reemplaza:
"verifica la existencia de los 4 entregables obligatorios:
- <EP_PATH>/06_guion_longform.md
- <EP_PATH>/08_shorts.md
- <EP_PATH>/09_packaging.md
- <EP_PATH>/10_seo.md"

Por:
"verifica la existencia de los 5 entregables obligatorios y que el Gate V sea OK:
- <EP_PATH>/06_guion_longform.md
- <EP_PATH>/07_verificacion_veracidad_notebooklm.md  ← Gate V (ESTADO_GLOBAL: OK)
- <EP_PATH>/08_shorts.md
- <EP_PATH>/09_packaging.md
- <EP_PATH>/10_seo.md"
```

---

### H2 — `01_formato_outputs.md` incompleto

**Dónde:** `.agent/rules/01_formato_outputs.md`, sección 2 "Nombres estándar de archivos por episodio" (líneas 35–46)
**Qué contradice:** Contrato real del sistema (Gate V es obligatorio)

**Por qué confunde:**
La lista de archivos estándar del episodio no incluye `07_verificacion_veracidad_notebooklm.md`.
Cualquier validación basada en esta lista estará incompleta.

**Micro-fix propuesto:**
Entre `07_qa_revisiones.md` y `08_shorts.md`, insertar:
```
- <EP_PATH>/07_verificacion_veracidad_notebooklm.md   ← Gate V (obligatorio)
```

---

### H3 — Doc Maestro sección 8 incompleta

**Dónde:** `workspace/00_sistema_agentes_v1.md`, sección 8 "Contrato de Entregables por Episodio", tabla (líneas ~355–365)
**Qué contradice:** `src/scripts/cerrar_episodio.py` (5 obligatorios)

**Por qué confunde:**
La tabla solo lista 4 obligatorios para DONE. Esto contradice el contrato real del script.

**Micro-fix propuesto:**
En la tabla de la sección 8, añadir fila:
```
| 1.5 | <EP_PATH>/07_verificacion_veracidad_notebooklm.md | Acto 2 → Gate V |
```

---

## 4. Duplicación / Doble Fuente de Verdad (🟡)

### H4 — Storage: Doc Maestro vs workspace/07

**Canónico:** `workspace/07_arquitectura_storage_repo_vs_vault_v1_2.md`
**En Doc Maestro:** Sección 9 repite la misma información con igual detalle.

**Propuesta:** Reducir la sección 9 del Doc Maestro a un párrafo con enlace:
> "Ver detalles en `workspace/07_arquitectura_storage_repo_vs_vault_v1_2.md`."
> Y mantener solo el bloque JSON de config (que es útil como referencia rápida).

---

### H5 — Lista de obligatorios duplicada en `.agent/rules/00_reglas_globales.md`

**Canónico:** `workspace/00_sistema_agentes_v1.md`, sección 8
**Duplicado:** `.agent/rules/00_reglas_globales.md`, sección 4 (lista los 4 outputs)

**Propuesta:** Reemplazar la sección 4 de las reglas globales por:
> "Los entregables obligatorios por episodio se definen en `workspace/00_sistema_agentes_v1.md`, sección 8."

---

### H6 — Flujo de archivos duplicado entre `workspace/06_` y `01_formato_outputs.md`

**Canónico operativo:** `.agent/rules/01_formato_outputs.md`
**Narrativo (ok como guía):** `workspace/06_convencion_outputs_y_notebooklm_v1.md`

**Propuesta:** No eliminar `workspace/06_`. Añadir al inicio del `06_`:
> "Esta guía es narrativa. La lista operativa canónica está en `.agent/rules/01_formato_outputs.md`."

---

### H7 — Doble definición de Gate 0

**00_control_pre_ejecucion.md:** workflow legacy — delega a skills (IA), genera `output/control_pre_ejecucion_v1.md`.
**01_pipeline_episodio.md Fase 0:** workflow actual — llama scripts Python directamente.

**Propuesta:**
- Añadir al inicio de `00_control_pre_ejecucion.md`: nota de que es el workflow alternativo (sin Python directo), y que `01_pipeline_episodio.md` es el canónico.
- O marcarlo como `> ⚠️ HISTÓRICO — usar 01_pipeline_episodio.md como secuencia principal.`

---

## 5. Huérfanos / Referencias Rotas (🟡)

### H8 — `piloto-outline.md` referencia `input/brief_capitulo.md` (no existe)

**Ruta referenciada:** `input/brief_capitulo.md` (línea 12)
**Ruta real:** `templates/brief_capitulo_template.md`

**Micro-fix:**
```
Reemplaza (en piloto-outline.md, línea 12):
"input/brief_capitulo.md ← Fuente legado"
Por:
"templates/brief_capitulo_template.md ← Fuente legado (usar solo si no hay EP_PATH activo)"
```

---

### H9 — `workspace/04_politica_spoilers.md` no referenciado en fuentes de verdad

Existe en disco y `piloto-outline.md` lo usa. Pero no está en la tabla de referencias obligatorias del Doc Maestro (sección 0) ni en `.agent/rules/00_reglas_globales.md`.

**Propuesta:**
Añadir referencia en `.agent/rules/00_reglas_globales.md`, sección 1 "Fuente de verdad":
```
- workspace/04_politica_spoilers.md
```

---

### H10 — `01_notebooklm_context_pack.md` mencionado pero no definido

`workspace/00_sistema_agentes_v1.md`, Acto 1 (sección 7) menciona este archivo como output contractual del Acto 1. Sin embargo:
- No figura en `.agent/rules/01_formato_outputs.md`.
- No existe en el Vault (lógico, aún no hay episodio).
- `workspace/06_convencion_outputs_y_notebooklm_v1.md` no lo menciona tampoco.

**Propuesta:** Definirlo en `01_formato_outputs.md` como archivo del Acto 1:
```
- <EP_PATH>/01_notebooklm_context_pack.md  ← salida del Acto 1 (NotebookLM con citas)
```
O bien, si el Acto 1 aún no está formalizado, reemplazar la mención en el Doc Maestro por `PENDIENTE` hasta que se cree el skill del Acto 1.

---

## 6. Acciones Recomendadas (por prioridad)

| Prioridad | Acción | Archivo a tocar | Tipo |
|---|---|---|---|
| 1 | Añadir `07_verificacion_veracidad_notebooklm.md` a la lista de obligatorios del Paso A | `.agent/skills/skill_cerrar_episodio.md` | **🔴 Corrección activa** |
| 2 | Añadir `07_verificacion_veracidad_notebooklm.md` a la lista de archivos estándar | `.agent/rules/01_formato_outputs.md` | **🔴 Corrección activa** |
| 3 | Añadir la fila de Gate V en la tabla de obligatorios DONE | `workspace/00_sistema_agentes_v1.md`, sección 8 | **🔴 Corrección activa** |
| 4 | Corregir la ruta `input/brief_capitulo.md` → `templates/brief_capitulo_template.md` | `.agent/workflows/piloto-outline.md` | 🟡 Referencia rota |
| 5 | Añadir `workspace/04_politica_spoilers.md` a fuentes de verdad | `.agent/rules/00_reglas_globales.md` | 🟡 Huérfano |
| 6 | Marcar `00_control_pre_ejecucion.md` como workflow alternativo | `.agent/workflows/00_control_pre_ejecucion.md` | 🟡 Doble Gate 0 |
| 7 | Definir `01_notebooklm_context_pack.md` en lista de archivos estándar (o marcarlo PENDIENTE) | `.agent/rules/01_formato_outputs.md` | 🟡 No definido |

---

## 7. Lista de Archivos Auditados

```
workspace/
  00_sistema_agentes_v1.md
  01_canal_identidad.md
  02_reglas_editoriales.md
  03_formato_longform.md
  04_politica_spoilers.md  (referenciado en piloto-outline)
  05_estilo_y_voz.md
  06_convencion_outputs_y_notebooklm_v1.md
  07_arquitectura_storage_repo_vs_vault_v1_2.md
  policy/POLICY_DETECCION_PATRONES_Y_CLICHES_V2.md  (referenciada en piloto-outline)

.agent/rules/
  00_reglas_globales.md
  01_formato_outputs.md
  02_reglas_notebooklm.md

.agent/skills/
  skill_auditoria_sistema.md
  skill_cerrar_episodio.md
  skill_iniciar_episodio.md
  skill_control_integridad_pipeline.md
  skill_verificacion_veracidad_notebooklm.md (nuevo)
  [restantes: verificados por grep en sesiones previas — sin referencias a output/ de episodio]

.agent/workflows/
  00_control_pre_ejecucion.md
  01_pipeline_episodio.md
  piloto-outline.md

config/
  local_settings.json
  local_settings.example.json
  agents_config.example.json

src/scripts/
  gate0_auditoria.py
  gate0_integridad.py
  iniciar_episodio.py
  cerrar_episodio.py

templates/
  brief_capitulo_template.md  (nombre real vs referencia en piloto-outline)
  verificacion_veracidad_notebooklm_template.md (nuevo)
  99_notebooklm_pack_template.md

reference/
  estilo_usuario/README.md (nuevo)
```

---

> Reporte generado por: Antigravity (modo auditoría — sin cambios aplicados)
> Micro-fixes requieren aprobación explícita del usuario antes de ejecutarse.
