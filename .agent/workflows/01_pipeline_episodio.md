---
description: Workflow operativo de la ruta actual del episodio. Realiza Gate 0 y recorre la ruta moderna portable; la ruta Vault legacy es opcional.
---

# Workflow: Pipeline operativo de episodio (ruta actual)

> **Ejecutor actual:** el runtime operativo como agente único.
> **Futuro:** Cada fase puede ser ejecutada por un agente independiente.
> **Regla de oro:** Solo se avanza a la siguiente fase cuando el entregable requerido de la fase actual existe y supera su schema, referencias, provenance y gate aplicables; su mera existencia nunca habilita el avance.
> **Alcance:** este workflow describe la ruta actual hasta el núcleo pre-script/B5-I2; no es una autorización ni un pipeline de publicación completo.

---

## PREREQUISITOS (leer antes de comenzar)

El flujo moderno debe tener disponibles:
La ruta legacy de episodio además requiere `config/local_settings.json` con `vault_root` y `channel_id`; esa configuración no es un prerrequisito universal de Gate 0 ni del cierre moderno del MVP.
- El **tema** del episodio y su **slug** confirmados por el usuario
- El **número** de episodio (siguiente al último registrado)
- La referencia editorial explícita: `profile_id`, `profile_version`, `profile_checksum`.

**Gate editorial:** si no hay perfil editorial activo válido que coincida exactamente con la referencia, devolver `BLOCKED` y detener. No inferir identidad, voz o formato desde `workspace/` ni seleccionar automáticamente la versión más reciente.

---

## FASE 0 — Gate 0 (Control previo a producción)

**Objetivo:** Verificar que el entorno está limpio y listo.

### Paso 0.1 — Auditoría de sistema
// turbo
```
python src/scripts/gate0_auditoria.py
```
- Consumir `output/gates/system/gate0_auditoria.json` y su exit code.
- `FAIL`, `BLOCKED` y error técnico → **🔴 DETENER**.

### Paso 0.2 — Integridad del pipeline
// turbo
```
python src/scripts/gate0_integridad.py
```
- Consumir `output/gates/system/gate0_integridad.json` y su exit code.
- `FAIL`, `BLOCKED` y error técnico → **🔴 DETENER**; `WARN` requiere política explícita.

### Gate 0 — Decisión final
| Auditoría Sistema | Integridad Pipeline | Decisión |
|---|---|---|
| OK | OK | 🟢 Continuar |
| OK | WARN | 🟡 Continuar con advertencia (confirmar con usuario) |
| FAIL (cualquiera) | cualquiera | 🔴 DETENER |

---

## FASE 1 — Resolver almacenamiento de episodio

**Objetivo:** Usar la ruta moderna portable por defecto. Solo si el operador dispone de `config/local_settings.json` y desea conservar el flujo legacy se crea y registra un episodio en Vault.

### Paso 1.1 — Ruta legacy opcional
// turbo
```
python src/scripts/iniciar_episodio.py --num <NUM> --slug <SLUG>
```
 - Capturar `EP_PATH` del output del script.
 - Mantener `EP_PATH` como variable de contexto para todas las fases siguientes.
 - Si no existe la configuración local, continuar con los artefactos contractuales del checkout y no ejecutar este script.

**⛔ Gate:** Si se elige la ruta legacy y el script retorna error → DETENER. No improvisar rutas. La ausencia de Vault no bloquea la ruta moderna.

---

## R2-M1 — Vertical técnica Topic Belonging

Cuando `CURRENT_MISSION` sea `R2_M1_PLAN009_TOPIC_BELONGING_TECHNICAL_VERTICAL`, la ruta moderna se detiene en:

```text
Gate 0
→ captura moderna por terminal
→ EditorialIntakeHandoff
→ enriquecimiento cognitivo mínimo de CHANNEL_INTELLIGENCE
→ TopicBelongingInput
→ CHANNEL_INTELLIGENCE_PRODUCER
→ CHANNEL_INTELLIGENCE_REVIEWER independiente
→ Topic Belonging gate
→ persistencia
→ STOP
```

    El enriquecimiento no amplía el formulario visible ni constituye una capability adicional. Los fakes solo pueden inyectarse en la frontera cognitiva del harness técnico. Esta ruta no crea `EpisodeBrief`, `ResearchPack`, tesis, guion ni artefactos de fases posteriores.

El CLI real permanece fail-closed durante P1: sin una `MissionAuthorization` válida no ejecuta `READY_NOT_AUTHORIZED`. El harness puede inyectar un fake únicamente en la frontera cognitiva y con configuración temporal de test; no es un fallback productivo.

## B5-I1 — Entrada editorial canónica

### 1. EpisodeBrief
- Ejecutar `skill_crear_brief_episodio.md`.
- Crear `<EP_PATH>/episode_brief.json`.
- Exigir material narrativo de partida e hipótesis editorial inicial revisable; audiencia y estructura siguen siendo hipótesis.
- Validar ID, versión y checksum contra `config/active_editorial_profile.json`.
- No usar `00_brief_episodio.md` como fuente canónica.

### 2. ResearchPack
- Ejecutar `skill_research_tema_y_obras.md`.
- Crear `<EP_PATH>/research_pack.json`.
- Investigar por cobertura, sin mínimos universales de URLs u obras.
- No avanzar si la cobertura crítica está pendiente sin reducción o bloqueo explícito.

### 3. QA de brief e investigación
```bash
python src/scripts/qa_brief_research.py --ep_path <EP_PATH> --ep-id <EP_ID>
```
- `FAIL`, `BLOCKED` o error técnico detienen.
- `WARN` permite continuar únicamente conservando las limitaciones declaradas.

### 4. Reporte y gate de evidencia
- Crear `<EP_PATH>/source_access_and_evidence_report.json`.
- Validar contra `schemas/source_access_and_evidence_report.json`.
```bash
python src/scripts/evidence_sufficiency_gate.py --report <EP_PATH>/source_access_and_evidence_report.json --ep-id <EP_ID>
```
- `FAIL`, `BLOCKED` o error técnico detienen.
- `WARN` debe conservarse como restricción de la tesis provisional.
- El reporte declara análisis permitidos, limitados y prohibidos, claims excluidos, disclosures y restricciones propagadas. Acceso indirecto prohíbe análisis cercano e intención autoral no respaldada.

### 5. Tesis provisional
- Ejecutar `skill_sintesis_tesis.md` en modo `THESIS_PROVISIONAL`.
- Crear `<EP_PATH>/thesis_provisional.json`.
- Validar contra `schemas/thesis_artifact.json`.
- No crear ni declarar una tesis refinada.
- La tesis hereda todas las restricciones del reporte y debe vincular cada premisa a hallazgos específicos.

### 6. Gate de tesis provisional
```powershell
python src/scripts/thesis_provisional_gate.py `
  --thesis <EP_PATH>/thesis_provisional.json `
  --research <EP_PATH>/research_pack.json `
  --evidence-report <EP_PATH>/source_access_and_evidence_report.json `
  --ep-id <EP_ID>
```
- `FAIL`, `BLOCKED` o error técnico detienen.
- Solo `PASS` o `WARN` permiten terminar B5-I1.

### 7. Auditoría semántica de suficiencia
- Un revisor IA produce `<EP_PATH>/semantic_sufficiency_audit.json` sobre los cuatro artefactos exactos; no se sustituye por heurísticas Python.
```powershell
python src/scripts/semantic_sufficiency_gate.py --brief <EP_PATH>/episode_brief.json --research <EP_PATH>/research_pack.json --evidence-report <EP_PATH>/source_access_and_evidence_report.json --thesis <EP_PATH>/thesis_provisional.json --audit <EP_PATH>/semantic_sufficiency_audit.json --ep-id <EP_ID>
```
- `FAIL`, `BLOCKED` o auditoría ausente detienen. `WARN` conserva restricciones para la reauditoría.

## Gate de salida B5-I1

Cuando los artefactos y la auditoría semántica permitan continuar, B5-I1 queda preparado para reauditoría en:

```text
READY_FOR_EDITORIAL_FUNCTIONAL_REVIEW
```

Esto no autoriza B5-I2. Las skills heredadas permanecen no ejecutables hasta sus bloques registrados en `config/skill_catalog.json`.

## B5-I2 — análisis, curación, tesis refinada y promesa editorial de guion

1. Crear un `narrative_human_analysis.json` por cada material que pueda quedar seleccionado y `material_curation.json` con lineage y restricciones B5-I1.
2. Crear `refined_thesis.json`, distinta de `THESIS_PROVISIONAL`, vinculada a análisis, curación, evidencia y restricciones heredadas.
3. Crear `editorial_script_promise.json` como entrada para escribir el guion: audiencia, promesa, tensión, expectativas legítimas y a evitar, alineación con la tesis, riesgo textual y obligaciones de apertura. No produce título, miniatura, packaging, Shorts ni SEO.
4. Un revisor IA produce `b5_i2_semantic_sufficiency_audit.json` con los nueve criterios B5-I2, los artefactos originales B5-I1 y checksums exactos.
5. Ejecutar `src/scripts/b5_i2_gate.py` incluyendo la auditoría B5-I2 de `SCRIPT_PRODUCT`. Cualquier checksum divergente, auditoría insuficiente, análisis sin evidencia original, curación final incompleta, tesis sin refinamiento demostrado, referencia circular o promesa textual deshonesta bloquea.

La adaptación `YOUTUBE_ADAPTATION` tiene un gate B5-I2 separado (`src/scripts/youtube_adaptation_b5_i2_gate.py`) y no se sustituye con el gate de `SCRIPT_PRODUCT`.

El estado de salida permitido es `READY_FOR_B5_I2_FUNCTIONAL_REAUDIT`. B5-I3, B6 y B7 permanecen sin iniciar.
