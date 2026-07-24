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
READY_FOR_TEAM_02_FUNCTIONAL_REAUDIT
```

Esto no autoriza B5-I2. Las skills heredadas permanecen no ejecutables hasta sus bloques registrados en `config/skill_catalog.json`.
