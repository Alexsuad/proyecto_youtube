---
name: skill_verificacion_veracidad_notebooklm
description: Gate V — Verifica que los hechos del guion estén sustentados en las fuentes del Acto 1. Bloquea el avance a derivados si hay FAIL o WARN sin resolver.
---

# Skill: Verificación de Veracidad NotebookLM (Gate V)

## Objetivo

Verificar que las afirmaciones de hecho en `06_guion_longform.md` están respaldadas por el material del Acto 1.

> **Qué se verifica:** nombres, fechas, filmografía, citas, estadísticas, contexto histórico.
> **Qué NO se verifica:** análisis emocionales, interpretaciones, opiniones del narrador.

---

## Inputs Obligatorios (en `<EP_PATH>`)

- `01_research_bruto.md` — fuente bruta de investigación
- `02_curation_obras.md` — obras seleccionadas con justificación
- `06_guion_longform.md` — guion completo a verificar

---

## Pasos

### 1) Extraer claims del guion

Leer `06_guion_longform.md` y extraer todas las afirmaciones verificables:
- nombres propios (personas reales, personajes de obras reales)
- fechas (años de estreno, publicación, eventos)
- filmografía (director, actores, productora)
- citas entrecomilladas atribuidas a personas reales
- estadísticas o cifras específicas
- contextos históricos o institucionaes

**No incluir:** "puede que", "a veces", "es posible que" → son hipótesis, no claims.

### 2) Contrastar con fuentes

Para cada claim extraído:
1. Buscar coincidencia en `01_research_bruto.md` o `02_curation_obras.md`.
2. Si hay coincidencia verificable → `OK`.
3. Si el dato está en el guion pero no está en ninguna fuente → `WARN`.
4. Si el dato contradice explícitamente una fuente → `FAIL`.

### 3) Completar el reporte

Seguir exactamente la estructura de:
`templates/verificacion_veracidad_notebooklm_template.md`

- Completar el encabezado con ep_id, slug y fecha.
- Rellenar la tabla de claims con todos los encontrados.
- Listar WARNINGS y FALLOS si existen.
- Calcular el ESTADO_GLOBAL:
  - Cualquier FAIL → `FAIL`
  - Solo WARN (sin FAIL) → `WARN`
  - Todo OK → `OK`

### 4) Output obligatorio

Guardar en:
`<EP_PATH>/07_verificacion_veracidad_notebooklm.md`

---

## Gate (Regla de Bloqueo)

| ESTADO_GLOBAL | Acción |
|---|---|
| `OK` | 🟢 Continuar a Fase 10 (Shorts, Packaging, SEO) |
| `WARN` | 🟡 DETENER — corregir guion antes de continuar |
| `FAIL` | 🔴 STOP OBLIGATORIO — volver a `06_guion_longform.md` y corregir |

---

## Nota de Implementación

Este skill usa la información que ya existe en los archivos del Acto 1.
Si NotebookLM está disponible vía MCP, puede usarse para consultar el cuaderno del episodio.
Si no está disponible, la verificación se hace manualmente con los archivos locales del `<EP_PATH>`.

---

## Skills Relacionados

- `skill_guion_longform.md` → genera el guion que este skill verifica
- `skill_qa_editorial.md` → verifica estilo (distinto: este skill verifica hechos)
- `skill_cerrar_episodio.md` → cierre final (requiere que Gate V sea OK)
