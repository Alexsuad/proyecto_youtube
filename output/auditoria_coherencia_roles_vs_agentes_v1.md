# Auditoría de Coherencia — Roles vs Agentes (V1.2)

**Fecha:** 2026-02-19
**Auditor:** Antigravity (modo lectura y propuesta — sin cambios automáticos)
**Alcance:** Toda la documentación del repo (`workspace/`, `output/`, `.agent/rules/`)

---

## Frase Estándar Oficial (Adoptar en todo el repo)

> "El sistema se organiza por **roles del pipeline**. En V1, todos los roles son ejecutados por **Antigravity (agente único)**. En V2+, los roles podrán convertirse en agentes independientes."

Este enunciado ya existe —con las mismas palabras— en `workspace/00_sistema_agentes_v1.md` (líneas 12–16). Es la referencia canónica.

---

## Resumen Ejecutivo

| Categoría | Cantidad |
|---|---|
| ✅ Archivos coherentes (source of truth) | 3 |
| 🟡 Archivos desfasados (reportes históricos) | 3 |
| 🔴 Archivos con contradicción activa operativa | 0 |

---

## ✅ Archivos Coherentes — Fuentes de Verdad

### 1. `workspace/00_sistema_agentes_v1.md`
**Estado: ✅ COHERENTE — Documento maestro correcto**

Este es el documento canónico y ya refleja la nomenclatura correcta:
- Línea 3: "Sistema de **Roles del Pipeline** V1.1"
- Líneas 12–16: Nota explícita sobre Antigravity como agente único hoy y escalamiento V2+
- Sección 6: Titulada "Roles del Pipeline" (Rol 1–Rol 11), no "Agentes"
- Cada rol tiene campo `Futuro:` que sitúa correctamente el multi-agente en tiempo futuro

**Único punto menor (no crítico):** Línea 48 dice "los agentes deben usar estos documentos" — pero en este contexto "agentes" se refiere al ejecutor (Antigravity) y es semánticamente correcto. No es contradicción.

---

### 2. `workspace/07_arquitectura_storage_repo_vs_vault_v1_2.md`
**Estado: ✅ COHERENTE**

Línea 14: `"🧠 Agentes & Skills: .agent/skills/"` → Aquí "Agentes" es el nombre de la carpeta del sistema de archivos (`.agent/`), no una entidad funcional. No es una contradicción de nomenclatura — es literalmente el nombre del directorio.

---

### 3. `output/auditoria_post_fix_v1.md`
**Estado: ✅ COHERENTE — Es un reporte de historial de correcciones**

Menciona explícitamente que el problema de "10 agentes ficticios" ya fue **resuelto**. Su función es dejar trazabilidad de lo que se corrigió.

---

## 🟡 Archivos Desfasados — Solo Documentación / Reportes Históricos

### 4. `workspace/06_convencion_outputs_y_notebooklm_v1.md`
**Estado: 🟡 DESFASADO — 1 frase con nomenclatura anterior**

**Línea 45 — Frase original:**
> "Al terminar un episodio, el **Agente Arquitecto** debe generar este archivo usando la plantilla..."

**Problema:** "Agente Arquitecto" no existe en la nomenclatura oficial V1.1. El rol equivalente es el **Orquestador** (Rol 1) o, en la práctica, Antigravity directamente.

**Corrección propuesta:**
> "Al terminar un episodio, **Antigravity (usando `skill_cerrar_episodio.md`)** debe generar este archivo usando la plantilla..."

**¿Afecta operación?** No. El archivo es una guía de convención, no un skill ni workflow.

---

### 5. `output/implementacion_convencion_notebooklm_v1.md`
**Estado: 🟡 DESFASADO — Reporte histórico de V1 pre-corrección**

**Línea 15 — Frase original:**
> "el **'Agente de Cierre'** (o Arquitecto) deberá asegurarse de generar el `99_notebooklm_pack.md`"

**Problema:** "Agente de Cierre" y "Arquitecto" son nombres anteriores a la nomenclatura V1.1.

**Corrección propuesta (si se actualiza):**
> "el **Orquestador (Rol 1), usando `skill_cerrar_episodio.md`,** deberá asegurarse de generar el `99_notebooklm_pack.md`"

**¿Afecta operación?** No. Es un reporte de implementación ya-ejecutada. Puede quedar como histórico con una nota al inicio: `> ⚠️ Reporte histórico — Nomenclatura V1.0 pre-corrección`.

---

### 6. `output/auditoria_no_sobrescritura_v1.md`
**Estado: 🟡 DESFASADO — Reporte histórico con dos problemas**

**Línea 42 — Frase original:**
> "*(Requiere que el **Agente Arquitecto** solicite un ID al inicio)*"

**Problema 1:** "Agente Arquitecto" no existe en la nomenclatura actual.

**Problema 2 (más importante):** El análisis completo del archivo es obsoleto — dice que el sistema es propenso a sobrescrituras y recomienda prefijos dinámicos o backups. Ambos problemas ya fueron **resueltos** con `iniciar_episodio.py` (crea carpeta única por episodio en el Vault, con 3 guardas anti-sobrescritura). El reporte no refleja el estado actual del sistema.

**Corrección propuesta (si se actualiza):**
Agregar al inicio del archivo:
> `> ⚠️ Reporte histórico — Estado V1.0. Las vulnerabilidades descritas fueron resueltas en V1.2 mediante el Vault externo y scripts deterministas. Ver `output/auditoria_post_fix_v1.md`.`

---

## 🔴 Contradicciones Operativas Activas

**Ninguna detectada.**

Los skills (`skill_*.md`), workflows (`.agent/workflows/`) y scripts Python (`src/scripts/`) usan correctamente las abstracciones `<EP_PATH>`, `roles del pipeline`, y referencias a skills concretos. No hay ningún "Agente X" referenciado en código ejecutable.

---

## Recomendación Final

| Archivo | Acción Recomendada | Urgencia |
|---|---|---|
| `workspace/00_sistema_agentes_v1.md` | Ninguna — ya es correcto | — |
| `workspace/07_arquitectura_storage_repo_vs_vault_v1_2.md` | Ninguna — `.agent/` es nombre de directorio | — |
| `workspace/06_convencion_outputs_y_notebooklm_v1.md` | Actualizar línea 45: "Agente Arquitecto" → skill correcto | Baja |
| `output/implementacion_convencion_notebooklm_v1.md` | Agregar nota de "reporte histórico" al inicio | Muy baja |
| `output/auditoria_no_sobrescritura_v1.md` | Agregar nota de "reporte histórico + problema resuelto" | Baja |

**Nota sobre `output/auditoria_agentes_y_skills_v1.md`:** Este reporte fue el que detectó el problema en primer lugar — es el origen de las correcciones V1.1. Su contenido es intencionalmente "antes del fix" y debe conservarse sin cambios como trazabilidad histórica.

---

## ESTADO_GLOBAL: ✅ OK

> Toda la documentación operativa activa (source of truth) usa nomenclatura coherente.
> Solo existen 3 reportes históricos con terminología anterior. Ninguno afecta la operación.
> La única corrección activa recomendada es en `workspace/06_convencion_outputs_y_notebooklm_v1.md` (1 línea, baja urgencia).
