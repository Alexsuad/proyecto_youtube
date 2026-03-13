# Auditoría Agentes y Skills — Proyecto YouTube
**Fecha:** 19/02/2026 | **Auditor:** Antigravity (modo estricto)

---

## RESUMEN EJECUTIVO

El proyecto tiene una base documental sólida y una visión híbrida (IA + Python) bien definida **en papel**, pero en la práctica el sistema tiene **graves problemas de implementación real**: no existe ningún script Python, los workflows tienen inconsistencias, y varios skills hacen trabajo que debería ser determinista/Python. El sistema tal como está no es ejecutable de forma autónoma; solo funciona con supervisión manual constante.

**Diagnóstico global: 🟡 USABLE CON RIESGOS CRÍTICOS — Requiere correcciones antes de producir en escala.**

---

## 1. INVENTARIO REAL DEL SISTEMA

### 1.1 Skills existentes (13)
| Archivo | Propósito | Ejecutable sin humano |
|---|---|---|
| skill_crear_brief_episodio.md | Crear brief | ❌ Solo IA |
| skill_research_tema_y_obras.md | Investigar obras | ❌ Solo IA |
| skill_curation_obras.md | Seleccionar obras | ❌ Solo IA |
| skill_mapa_eventos_y_outline.md | Estructura del ep. | ⚠️ Parcial (usa workflow) |
| skill_analisis_patrones.md | Analizar obras | ❌ Solo IA |
| skill_sintesis_tesis.md | Tesis central | ❌ Solo IA |
| skill_guion_longform.md | Escribir guion | ❌ Solo IA |
| skill_qa_editorial.md | QA del guion | ❌ Solo IA |
| skill_shorts.md | Generar shorts | ❌ Solo IA |
| skill_packaging.md | Títulos/miniaturas | ❌ Solo IA |
| skill_seo_youtube.md | SEO YT | ❌ Solo IA |
| skill_auditoria_sistema.md | Gate 0 sistema | ⚠️ CRÍTICO (ver abajo) |
| skill_control_integridad_pipeline.md | Gate 0 pipeline | ⚠️ CRÍTICO (ver abajo) |

### 1.2 Workflows existentes (2)
| Archivo | Propósito | Estado |
|---|---|---|
| piloto-outline.md | Crear mapa + outline | ✅ Bien estructurado, referencias válidas |
| 00_control_pre_ejecucion.md | Gate 0 | ⚠️ Lógica bien definida, sin ejecución real |

### 1.3 Agentes definidos en documentación
El archivo `00_sistema_agentes_v1.md` define **10 agentes** (Orquestador, Investigador, Curador, Planner, Analista, Guionista, QA, Shorts, Packaging, SEO). **No existe ningún archivo de agente individual**: todo confluye en Antigravity como agente único. No hay separación real entre agentes.

---

## 2. PROBLEMAS CRÍTICOS

### 🔴 CRÍTICO #1 — `skill_auditoria_sistema.md` es un documento de intenciones, no ejecutable
**Problema:** El skill describe "Paso A: verificar existencia de VAULT_ROOT. Si no existe, 🔴 STOP". Pero **¿quién ejecuta eso?** No hay ningún script Python que haga:
- `os.path.exists("C:\\YT_VAULT")`
- `os.makedirs(...)`
- Escribir/leer `episodes_index.json`

El "ESTADO_GLOBAL" que aparece en `output/auditoria_sistema_v1.md` fue **escrito manualmente por mí en la sesión anterior**, no fue generado por ningún proceso automático. El output es una **simulación**, no evidencia real.

**Impacto:** Si el Vault no existe, el sistema no lo detectará ni lo creará. El Gate 0 no existe en la práctica.

**Solución → Python:**
```
src/scripts/gate0_auditoria.py
- Lee config/local_settings.json
- Verifica carpetas del repo
- Verifica/crea estructura del Vault
- Escribe output/auditoria_sistema_v1.md con ESTADO_GLOBAL real
```

---

### 🔴 CRÍTICO #2 — `skill_control_integridad_pipeline.md` también es IA pura
**Problema:** El skill busca archivos en `output/` para verificar si hay episodios anteriores incompletos. La IA no puede verificar el sistema de archivos de forma confiable. Esta es una tarea **100% determinista**: existe el archivo o no existe.

**Solución → Python:**
```
src/scripts/gate0_integridad.py
- glob("output/*.md") para listar archivos
- Verifica qué entregables del episodio anterior existen
- Escribe output/control_integridad_pipeline.md con ESTADO_GLOBAL real
```

---

### 🔴 CRÍTICO #3 — `01_formato_outputs.md` tiene una **contradicción interna**
**Problema:** La sección 1 dice "output/ es solo para auditorías" (V1.2 Vault), pero la sección 2 lista `output/00_brief_episodio.md`, `output/06_guion_longform.md`, etc. (archivos de episodio). Una regla invalida a la otra.

**Impacto:** Cualquier agente que lea este archivo recibirá instrucciones contradictorias sobre dónde escribir.

**Solución:** Unificar la sección 2 para que apunte rutas del Vault:
- Cambiar "output/06_guion_longform.md" → `<VAULT_ROOT>/<CHANNEL_ID>/episodios/ep_<ID>_<SLUG>/06_guion_longform.md`

---

### 🟡 IMPORTANTE #4 — 10 agentes documentados, 0 agentes reales
**Problema:** `00_sistema_agentes_v1.md` describe 10 agentes con nombres y responsabilidades distintas. En la realidad, no existe ningún archivo de definición de agente, ningún prompt de sistema individual, ninguna separación de roles. Todo es Antigravity haciendo todo.

**Impacto:** El sistema no escala. Si en el futuro se quieren usar agentes paralelos o especializados (ej: OpenAI Assistants, CrewAI), no hay base.

**Recomendación:** Por ahora, es aceptable que Antigravity sea el único agente. Pero la documentación debe reflejarlo con honestidad: "Agente único con skills especializados", no "10 agentes".

---

### 🟡 IMPORTANTE #5 — Skills de producción NO leen el Vault
**Problema:** Todos los skills de producción (brief, research, guion, etc.) apuntan a `output/00_brief_episodio.md`, `output/01_research_bruto.md`, etc. Tras migrar a V1.2 (Vault), estas rutas quedaron **desactualizadas**. Los skills van a escribir en el repo, no en el Vault.

**Impacto:** La promesa de "output/ solo para auditorías" es mentira mientras los skills digan lo contrario.

---

### 🟡 IMPORTANTE #6 — `piloto-outline.md` lee de `input/brief_capitulo.md`, pero el sistema estándar crea `output/00_brief_episodio.md`
**Problema:** El workflow lee desde `input/brief_capitulo.md` (plantilla estática), pero el skill estándar `skill_crear_brief_episodio.md` crea `output/00_brief_episodio.md`. Son dos orígenes distintos para el mismo dato.

**Impacto:** Fuente de verdad fragmentada. El Planner puede ignorar el brief real del episodio.

---

### ℹ️ OBSERVACIÓN #7 — `output/eventos/` es una carpeta misteriosa
**Problema:** Existe `output/eventos/` sin documentación de para qué sirve, qué entra y qué sale. Ningún skill la menciona.

**Acción recomendada:** Investigar y documentar, o eliminar si está vacía/es un artefacto.

---

## 3. ANÁLISIS IA vs PYTHON (Estricto)

| Tarea | Actual | Debería ser |
|---|---|---|
| Verificar si existe C:\YT_VAULT | IA (simulado) | 🐍 Python obligatorio |
| Crear carpetas del Vault | IA (simulado) | 🐍 Python obligatorio |
| Detectar archivos en output/ | IA | 🐍 Python obligatorio |
| Escribir episodes_index.json | IA (simulado) | 🐍 Python obligatorio |
| Validar que local_settings.json tenga todas las claves | IA | 🐍 Python obligatorio |
| Investigar obras/temas | IA | ✅ IA correcta |
| Curar y seleccionar obras | IA + humano | ✅ IA correcta |
| Analizar patrones emocionales | IA | ✅ IA correcta |
| Escribir guion | IA | ✅ IA correcta |
| QA anti-clichés | IA | ✅ IA correcta |
| Generar títulos/packaging | IA | ✅ IA correcta |
| Generar SEO | IA | ✅ IA correcta |
| Generar shorts | IA | ✅ IA correcta |

---

## 4. SKILLS — ¿SOBRAN O FALTAN?

### ¿Sobran skills?
- No. Los 11 skills de producción corresponden 1:1 con las fases del pipeline. Están bien dimensionados.
- Los 2 skills de Gate 0 son necesarios, pero deben ser respaldados por scripts Python.

### ¿Faltan skills?
Sí, faltan:
1. **skill_iniciar_episodio.md** → Que cree la carpeta del episodio en el Vault y registre en `episodes_index.json`. Hoy nadie hace esto.
2. **skill_cerrar_episodio.md** → Que valide entregables completos, genere `99_notebooklm_pack.md` y actualice el índice.
3. **skill_orquestador_pipeline.md** → Hoy el orquestador solo existe en el documento de sistema. No hay skill que lo implemente.

---

## 5. CONCLUSIÓN Y PLAN DE ACCIÓN

### Estado final
| Área | Estado | Severidad |
|---|---|---|
| Skills de producción (contenido) | ✅ Bien diseñados | OK |
| Gate 0 (auditoria_sistema) | 🔴 Solo simulado | CRÍTICO |
| Gate 0 (integridad pipeline) | 🔴 Solo simulado | CRÍTICO |
| Consistencia rutas Vault | 🔴 Contradicción | CRÍTICO |
| Agentes (documentados vs reales) | 🟡 Sobredimensionado | IMPORTANTE |
| Scripts Python | 🔴 No existen | CRÍTICO |
| Workflows | 🟡 Parciales | IMPORTANTE |

### Acciones prioritarias (en orden)
1. 🐍 **Crear `src/scripts/gate0_auditoria.py`** — Para que el Gate 0 sea real y no simulado.
2. 🐍 **Crear `src/scripts/gate0_integridad.py`** — Para detectar conflictos reales en el filesystem.
3. 📝 **Corregir contradicción en `01_formato_outputs.md`** — Unificar rutas hacia el Vault.
4. 📝 **Actualizar rutas en todos los skills de producción** — Que apunten al Vault.
5. 📝 **Crear `skill_iniciar_episodio.md` y `skill_cerrar_episodio.md`** — Cerrar el ciclo de vida del episodio.
6. 📝 **Simplificar documentación de agentes** — Ser honestos: es 1 agente (Antigravity) con skills especializados.
