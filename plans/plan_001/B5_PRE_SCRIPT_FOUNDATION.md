# PLAN-001 / B5_PRE — Planeación, investigación y curación previa al guion

**PLAN_ID:** `B5_PRE`
**PLAN_NAME:** Planeación, investigación y curación previa al guion
**PLAN_RECTOR:** [`../001_reestructuracion_motor_agentico_editorial_y_harness.md`](../001_reestructuracion_motor_agentico_editorial_y_harness.md)
**LIVE_STATE_AUTHORITY:** [`../001_CONTROL_OPERATIVO.md`](../001_CONTROL_OPERATIVO.md)
**Índice del plan:** [`plans/plan_001/README.md`](README.md)

> Este plan es un incremento subordinado a **Plan 001**. No es un nuevo plan rector y no compite con la sede del estado vivo. El estado operativo y la única siguiente acción autorizada se leen exclusivamente desde `plans/001_CONTROL_OPERATIVO.md`.
>
> **No confundir con `B5_5_prototipo_editorial.md`:** ese documento es el prototipo editorial controlado **posterior** (post-guion). Este documento representa la **planeación previa al guion** (pre-script): entrada, pertenencia, investigación, obras candidatas, obras finales, análisis, curación, tesis, promesa editorial y restricciones de adaptación temprana. No produce todavía outline, arquitectura completa, apertura ni guion.

---

## 1. Identidad del plan

```text
PLAN_ID                       = B5_PRE
PLAN_NAME                     = Planeación, investigación y curación previa al guion
PLAN_RECTOR                   = Plan 001
LIVE_STATE_AUTHORITY          = plans/001_CONTROL_OPERATIVO.md
PLAN_STATUS                   = FUNCTIONAL_FOUNDATION_RECONCILED
FUNCTIONAL_SCOPE              = SPECIFIED_AND_RECONCILED
IMPLEMENTATION_STATUS         = PARTIAL_EXISTING_BASE_REQUIRES_LATER_DESIGN
TECHNICAL_VALIDATION_STATUS   = PARTIAL
OPERATIONAL_DEMONSTRATION_STATUS = NOT_DEMONSTRATED
FUNCTIONAL_APPROVAL_STATUS    = NOT_APPROVED_AS_OPERATIONAL_CAPABILITY
AUTHORIZED_FOR_PRODUCT_USE    = NO
```

La base parcial existente no equivale a capacidad operativa implementada. Esta misión no implementa componentes ni demuestra una vertical real.

---

## 2. Objetivo

Transformar:

```text
tema, obra o corpus
```

en:

```text
pregunta central
+ pertenencia aprobada
+ investigación suficiente
+ obras verificadas
+ cinco a ocho candidatas normales
+ tres a cinco obras finales
+ tesis provisional
+ tesis refinada
+ promesa editorial
+ restricciones de adaptación temprana
+ preparación para diseñar el guion
```

No producir todavía:

```text
outline final
arquitectura narrativa completa
OPENING_UNIT
guion
packaging final
publicación
```

---

## 3. Tres modalidades de entrada

Toda propuesta declara exactamente una modalidad.

### 3.1 `TOPIC_FIRST`

```text
problema o pregunta
→ pertenencia
→ investigación
→ candidatas
→ análisis
→ curación
→ tesis
```

`TOPIC_FIRST` puede comenzar por un problema o pregunta humana, social o cultural sin una obra definida. Antes de la aprobación hacia B5-I1 debe haber identificado una puerta narrativa verificable y obras candidatas suficientes para el formato principal (ver `policies/channel_intelligence/topic_belonging_policy.md`).

### 3.2 `ANCHOR_WORK_FIRST`

```text
obra ancla
→ conflictos y temas
→ pregunta central
→ investigación externa
→ obras complementarias
→ análisis
→ curación
→ tesis
```

### 3.3 `CORPUS_FIRST`

```text
autor, saga, género, franquicia o universo
→ inventario
→ patrones
→ pregunta central
→ investigación
→ selección
→ tesis
```

---

## 4. Reglas de obras y formato

La regla 5–8 / 3–5 tiene sede canónica en las políticas de formato del producto:

- `policies/script_product/main_episode_format_policy.md`
- `policies/script_product/episode_discovery_and_material_curation_policy.md`

```text
CANDIDATE_WORKS       = 5_TO_8_NORMAL_RANGE

FINAL_SUBSTANTIVE_WORKS:
  minimum = 3
  maximum = 5
```

Una **obra sustantiva** (cuenta para el mínimo 3–5) es una obra que:

- recibe análisis real;
- aporta evidencia narrativa;
- cumple una función diferenciada;
- participa en la progresión argumentativa.

No cuentan para el mínimo:

```text
menciones breves
referencias visuales
citas aisladas
noticias
papers
fuentes académicas
obras nombradas sin análisis
ejemplos incidentales
```

La regla pertenece a una **política de formato del producto**, no al `EditorialProfile`.

---

## 5. Orden funcional canónico

```text
entrada
→ pertenencia
→ descubrimiento
→ investigación
→ candidatas
→ verificación
→ B5-I1
→ selección preliminar
→ análisis narrativo y humano
→ curación final
→ tesis refinada
→ promesa editorial
→ adaptación temprana a YouTube
→ decisión de evaluación
```

La **curación final** no puede realizarse antes del análisis sustantivo.

---

## 6. Incrementos posteriores (diferidos)

La implementación posterior se organiza (sin ejecutarse en esta misión) en bloques equivalentes:

```text
B5_PRE.1 — Entrada, modalidad y pertenencia
B5_PRE.2 — Descubrimiento y especialistas
B5_PRE.3 — Investigación y verificación de obras
B5_PRE.4 — Cierre B5-I1
B5_PRE.5 — Cierre semántico B5-I2
B5_PRE.6 — Integración YouTube Adaptation
B5_PRE.7 — Ejecución real controlada
B5_PRE.8 — Auditoría funcional y técnica
```

No se crea un archivo separado por incremento durante esta misión.

---

## 7. Componentes existentes y faltantes

Etiquetas: `EXISTING_REUSE | NEEDS_EXTENSION | MISSING | LEGACY_CONFLICT | PENDING_REAL_DEMONSTRATION`.

| Componente | Estado | Nota |
|---|---|---|
| Topic Belonging | `EXISTING_REUSE` | policy + schemas + roles `CHANNEL_INTELLIGENCE_*` |
| B5-I1 | `EXISTING_REUSE` | EpisodeBrief, ResearchPack, ClaimsLedger, SourceAccess, ProvisionalThesis |
| B5-I2 | `EXISTING_REUSE` / `LEGACY_CONFLICT` | NarrativeHumanAnalysis, MaterialCuration, RefinedThesis, EditorialScriptPromise |
| SCRIPT_PRODUCT_PRODUCER / AUDITOR | `EXISTING_REUSE` | — |
| YOUTUBE_ADAPTATION_PRODUCER / AUDITOR | `EXISTING_REUSE` / `PARTIAL` | implementado sin demostración real |
| provenance | `EXISTING_REUSE` | execution_provenance_registry |
| handoffs / gates | `NEEDS_EXTENSION` | handoffs incompletos; gates parciales |

Artefactos registrados como **faltantes o por verificar** (no implementar en esta misión):

```text
EntryModeResolution
EffectiveTopicBelongingDecision
EpisodeDiscoveryFrame
SpecialistResearchPlan
SpecialistResearchContribution
CandidateWorkSet
WorkVerificationReport
B5I1Package
PreScriptReadinessDecision
```

Destino: `FUTURE_B5_PRE_TECHNICAL_IMPLEMENTATION_BACKLOG`.

---

## 8. Criterios de cierre (estado futuro)

```text
THREE_ENTRY_MODES          = PASS
TOPIC_BELONGING            = SPECIFIED_AND_RECONCILED
DYNAMIC_RESEARCH_PLAN      = PASS
CANDIDATE_WORKS             = 5_TO_8
FINAL_WORKS               = 3_TO_5
WORK_VERIFICATION          = PASS
B5_I1                     = PASS
B5_I2_SCRIPT_PRODUCT      = PASS
B5_I2_YOUTUBE_ADAPTATION  = PASS
REAL_EXECUTION            = NOT_DEMONSTRATED
PROVENANCE                = PASS
FALSE_EDITORIAL_PASS      = 0
```

Estado final futuro:

```text
B5_PRE_STATUS                  = RECONCILED_NOT_IMPLEMENTED
PRE_SCRIPT_PLANNING          = NOT_DEMONSTRATED
READY_FOR_SCRIPT_ARCHITECTURE = YES
SCRIPT_WRITTEN              = NO
```

No se declaran alcanzados en esta misión.

---

## 9. Trazabilidad material de auditorías y requisitos

Esta sección registra por hallazgo la relación entre cada fuente externa, el requisito funcional que la B5_PRE consolida y la evidencia actual en el repositorio. No copia auditorías completas al repositorio y no declara reconciliadas fuentes que no hayan podido leerse.

**Estado global de fuentes:** las fuentes canónicas de P-08 utilizadas para esta reconciliación están disponibles localmente en `docs/reconciliation/p08/2026-08-05/`. Esta disponibilidad permite sostener la reconciliación documental de B5_PRE-M2. No convierte automáticamente cada hallazgo histórico de auditorías anteriores en verificado, implementado, demostrado o aprobado.

### 9.1 Matriz material por functional_owner

Leyenda de columnas por fila:

```text
source_document              = nombre exacto de la fuente externa
source_date_or_version       = fecha o versión de la fuente (no disponible si no se leyó)
audited_repository_or_snapshot = snapshot auditado (no verificable si no se leyó)
functional_owner             = responsable funcional del hallazgo
finding_id                   = identificador del hallazgo
requirement_summary          = requisito funcional consolidado en B5_PRE
current_repository_evidence  = evidencia concreta en el repositorio (path + sección)
current_status               = estado permitido
canonical_destination        = sede canónica del requisito
implementation_phase         = fase de implementación
notes                        = observaciones
```

#### 9.1.1 Channel Intelligence

Fuente: `01.1 Auditoría Inteligencia Canal.txt` — `source_date_or_version: NOT_AVAILABLE` — `audited_repository_or_snapshot: NOT_VERIFIED` — `current_status: NOT_VERIFIED` — `notes: source content unavailable during this execution`.

| finding_id | requirement_summary | current_repository_evidence | canonical_destination | implementation_phase |
|---|---|---|---|---|
| CI-01 | identidad y territorios | `policies/channel_intelligence/topic_belonging_policy.md` §1, §2 | topic_belonging_policy §1, §2 | B5_PRE_M1 (política) / M2 (implementación) |
| CI-02 | puerta narrativa | `policies/channel_intelligence/topic_belonging_policy.md` §2 (dimensiones) | topic_belonging_policy §2 | B5_PRE_M1 (política) / M2 (implementación) |
| CI-03 | pregunta central | `policies/channel_intelligence/topic_belonging_policy.md` §2; `plans/plan_001/B5_PRE_SCRIPT_FOUNDATION.md` §10.2.1 | topic_belonging_policy §2; B5_PRE §10.2.1 | B5_PRE_M1 (política) / M2 (implementación) |
| CI-04 | valor más allá de la obra | `policies/channel_intelligence/topic_belonging_policy.md` §2, §6 | topic_belonging_policy §2, §6 | B5_PRE_M1 (política) / M2 (implementación) |
| CI-05 | potencial de tesis | `policies/channel_intelligence/topic_belonging_policy.md` §2 | topic_belonging_policy §2 | B5_PRE_M1 (política) / M2 (implementación) |
| CI-06 | audiencia matriz | `policies/channel_intelligence/topic_belonging_policy.md` §2 | topic_belonging_policy §2 | B5_PRE_M1 (política) / M2 (implementación) |
| CI-07 | persona autoral | `policies/channel_intelligence/topic_belonging_policy.md` §2 | topic_belonging_policy §2 | B5_PRE_M1 (política) / M2 (implementación) |
| CI-08 | límites permanentes | `policies/channel_intelligence/topic_belonging_policy.md` §2, §10 | topic_belonging_policy §2, §10 | B5_PRE_M1 (política) / M2 (implementación) |
| CI-09 | sensibilidad | `policies/channel_intelligence/topic_belonging_policy.md` §9 (escalamiento) | topic_belonging_policy §9 | B5_PRE_M1 (política) / M2 (implementación) |
| CI-10 | precedente | `policies/channel_intelligence/topic_belonging_policy.md` §9 | topic_belonging_policy §9 | B5_PRE_M1 (política) / M2 (implementación) |
| CI-11 | viabilidad 3–5 obras | `policies/channel_intelligence/topic_belonging_policy.md` §10; `policies/script_product/main_episode_format_policy.md` §2 | topic_belonging_policy §10; main_episode_format_policy §2 | B5_PRE_M1 (política) / M2 (implementación) |
| CI-12 | revisión independiente | `policies/channel_intelligence/topic_belonging_policy.md` §8; `prompts/roles/CHANNEL_INTELLIGENCE_REVIEWER/1.0.0.md` | topic_belonging_policy §8 | B5_PRE_M1 (política) / M2 (implementación) |
| CI-13 | decisión efectiva | `policies/channel_intelligence/topic_belonging_policy.md` §5, §8; `schemas/topic_belonging_decision.json` | topic_belonging_policy §5, §8 | B5_PRE_M1 (política) / M2 (implementación) |
| CI-14 | demostración real | `plans/001_CONTROL_OPERATIVO.md` (REAL_EXECUTION=NOT_DEMONSTRATED); `prompts/roles/CHANNEL_INTELLIGENCE_PRODUCER/1.0.0.md` | control_operativo (REAL_EXECUTION) | M2 (demostración) |

#### 9.1.2 Script Product — B5-I1

Fuente: `02.1 Auditoria de guiones.txt` — `source_date_or_version: NOT_AVAILABLE` — `audited_repository_or_snapshot: NOT_VERIFIED` — `current_status: NOT_VERIFIED` — `notes: source content unavailable during this execution`.

| finding_id | requirement_summary | current_repository_evidence | canonical_destination | implementation_phase |
|---|---|---|---|---|
| SP-I1-01 | descubrimiento | `policies/script_product/episode_discovery_and_material_curation_policy.md` §1 | episode_discovery_policy §1 | B5_PRE_M1 (política) / M2 (implementación) |
| SP-I1-02 | investigación adaptativa | `policies/script_product/episode_discovery_and_material_curation_policy.md` §2 | episode_discovery_policy §2 | B5_PRE_M1 (política) / M2 (implementación) |
| SP-I1-03 | especialistas | `policies/script_product/episode_discovery_and_material_curation_policy.md` §3 | episode_discovery_policy §3 | B5_PRE_M1 (política) / M2 (implementación) |
| SP-I1-04 | verificación de obras | `policies/script_product/episode_discovery_and_material_curation_policy.md` §4 | episode_discovery_policy §4 | B5_PRE_M1 (política) / M2 (implementación) |
| SP-I1-05 | claims | `B5_PRE_SCRIPT_FOUNDATION.md` §10.2.6, §10.2.7; `schemas/claims_ledger.json` | B5_PRE §10.2.6–10.2.7 | B5_PRE_M1 (plan) / M2 (implementación) |
| SP-I1-06 | evidencia | `B5_PRE_SCRIPT_FOUNDATION.md` §10.2.6; `schemas/research_pack.json`; `schemas/source_access_and_evidence_report.json` | B5_PRE §10.2.6 | B5_PRE_M1 (plan) / M2 (implementación) |
| SP-I1-07 | acceso directo e indirecto | `B5_PRE_SCRIPT_FOUNDATION.md` §10.2.4, §10.2.5; `schemas/source_access_and_evidence_report.json` | B5_PRE §10.2.4–10.2.5 | B5_PRE_M1 (plan) / M2 (implementación) |
| SP-I1-08 | tesis provisional | `B5_PRE_SCRIPT_FOUNDATION.md` §10.2.10; `schemas/thesis_artifact.json` | B5_PRE §10.2.10 | B5_PRE_M1 (plan) / M2 (implementación) |
| SP-I1-09 | once dimensiones de auditoría | `B5_PRE_SCRIPT_FOUNDATION.md` §10.2.1–10.2.11 | B5_PRE §10.2 | B5_PRE_M1 (plan) / M2 (implementación) |
| SP-I1-10 | independencia productor–auditor | `B5_PRE_SCRIPT_FOUNDATION.md` §10.3; `schemas/semantic_sufficiency_audit.json`; `prompts/roles/SCRIPT_PRODUCT_AUDITOR/1.0.0.md` | B5_PRE §10.3 | B5_PRE_M1 (plan) / M2 (implementación) |
| SP-I1-11 | handoff | `B5_PRE_SCRIPT_FOUNDATION.md` §5 (orden funcional) | B5_PRE §5 | B5_PRE_M1 (plan) / M2 (implementación) |
| SP-I1-12 | demostración real | `plans/001_CONTROL_OPERATIVO.md` (REAL_EXECUTION=NOT_DEMONSTRATED); `src/scripts/b5_i2_gate.py` | control_operativo (REAL_EXECUTION) | M2 (demostración) |

#### 9.1.3 Script Product — B5-I2

Fuente: `Se ha pegado el markdown(42).md` — `source_date_or_version: NOT_AVAILABLE` — `audited_repository_or_snapshot: NOT_VERIFIED` — `current_status: NOT_VERIFIED` — `notes: source content unavailable during this execution`.

| finding_id | requirement_summary | current_repository_evidence | canonical_destination | implementation_phase |
|---|---|---|---|---|
| SP-I2-01 | análisis humano y narrativo | `B5_PRE_SCRIPT_FOUNDATION.md` §11.2.2, §11.2.9; `schemas/narrative_human_analysis.json` | B5_PRE §11.2.2, §11.2.9 | B5_PRE_M1 (plan) / M2 (implementación) |
| SP-I2-02 | selección preliminar | `policies/script_product/episode_discovery_and_material_curation_policy.md` §5 | episode_discovery_policy §5 | B5_PRE_M1 (política) / M2 (implementación) |
| SP-I2-03 | curación final | `policies/script_product/episode_discovery_and_material_curation_policy.md` §7, §8; `B5_PRE_SCRIPT_FOUNDATION.md` §11.2.6 | episode_discovery_policy §7–8 | B5_PRE_M1 (política) / M2 (implementación) |
| SP-I2-04 | tesis refinada | `B5_PRE_SCRIPT_FOUNDATION.md` §11.2.1, §11.2.5; `schemas/refined_thesis.json` | B5_PRE §11.2.1, §11.2.5 | B5_PRE_M1 (plan) / M2 (implementación) |
| SP-I2-05 | promesa editorial | `B5_PRE_SCRIPT_FOUNDATION.md` §11.2.1; `schemas/editorial_script_promise.json` | B5_PRE §11.2.1 | B5_PRE_M1 (plan) / M2 (implementación) |
| SP-I2-06 | diez dimensiones | `B5_PRE_SCRIPT_FOUNDATION.md` §11.2.1–11.2.10; `schemas/b5_i2_semantic_sufficiency_audit.json` (dimension_results) | B5_PRE §11.2 | B5_PRE_M1 (plan) / M2 (implementación) |
| SP-I2-07 | falsos PASS | `B5_PRE_SCRIPT_FOUNDATION.md` §11.3 (invariantes) | B5_PRE §11.3 | B5_PRE_M1 (plan) / M2 (implementación) |
| SP-I2-08 | coherencia de decisión | `B5_PRE_SCRIPT_FOUNDATION.md` §11.4 | B5_PRE §11.4 | B5_PRE_M1 (plan) / M2 (implementación) |
| SP-I2-09 | handoff | `B5_PRE_SCRIPT_FOUNDATION.md` §5 (orden funcional) | B5_PRE §5 | B5_PRE_M1 (plan) / M2 (implementación) |
| SP-I2-10 | demostración real | `plans/001_CONTROL_OPERATIVO.md` (REAL_EXECUTION=NOT_DEMONSTRATED); `src/scripts/run_b5_i2_semantic_audit.py` | control_operativo (REAL_EXECUTION) | M2 (demostración) |

#### 9.1.4 YouTube Adaptation

Fuente: `03.1 Adaptación a YouTube.txt` — `source_date_or_version: NOT_AVAILABLE` — `audited_repository_or_snapshot: NOT_VERIFIED` — `current_status: NOT_VERIFIED` — `notes: source content unavailable during this execution`.

| finding_id | requirement_summary | current_repository_evidence | canonical_destination | implementation_phase |
|---|---|---|---|---|
| YT-01 | cinco resultados | `B5_PRE_SCRIPT_FOUNDATION.md` §12.1; `config/youtube_adaptation_r3_traceability.json` | B5_PRE §12.1 | B5_PRE_M1 (plan) / M2 (implementación) |
| YT-02 | diez decisiones | `B5_PRE_SCRIPT_FOUNDATION.md` §12.2; `schemas/youtube_adaptation_b5_i2_package.json` | B5_PRE §12.2 | B5_PRE_M1 (plan) / M2 (implementación) |
| YT-03 | packaging temprano | `B5_PRE_SCRIPT_FOUNDATION.md` §12.1–12.2; `schemas/early_packaging_hypothesis.json` | B5_PRE §12.1–12.2 | B5_PRE_M1 (plan) / M2 (implementación) |
| YT-04 | apertura futura | `B5_PRE_SCRIPT_FOUNDATION.md` §12.2 (YT_OPENING_READINESS) | B5_PRE §12.2 | B5_PRE_M1 (plan) / M2 (implementación) |
| YT-05 | duración | `B5_PRE_SCRIPT_FOUNDATION.md` §12.2 (YT_DURATION_ENVELOPE) | B5_PRE §12.2 | B5_PRE_M1 (plan) / M2 (implementación) |
| YT-06 | sobrepromesa | `B5_PRE_SCRIPT_FOUNDATION.md` §12.2 (YT_OVERPROMISE_REVIEW) | B5_PRE §12.2 | B5_PRE_M1 (plan) / M2 (implementación) |
| YT-07 | riesgo textual | `B5_PRE_SCRIPT_FOUNDATION.md` §12.2 (YT_TEXT_PLATFORM_RISK) | B5_PRE §12.2 | B5_PRE_M1 (plan) / M2 (implementación) |
| YT-08 | derechos y reutilización | `B5_PRE_SCRIPT_FOUNDATION.md` §12.2 (YT_SCRIPT_RIGHTS_REUSE_RISK) | B5_PRE §12.2 | B5_PRE_M1 (plan) / M2 (implementación) |
| YT-09 | límites de autoridad | `B5_PRE_SCRIPT_FOUNDATION.md` §12.3 | B5_PRE §12.3 | B5_PRE_M1 (plan) / M2 (implementación) |
| YT-10 | estado técnico | `B5_PRE_SCRIPT_FOUNDATION.md` §12.4; `config/youtube_adaptation_r3_traceability.json` | B5_PRE §12.4 | B5_PRE_M1 (plan) / M2 (implementación) |
| YT-11 | demostración real | `plans/001_CONTROL_OPERATIVO.md` (REAL_EXECUTION=NOT_DEMONSTRATED); `src/scripts/youtube_adaptation_b5_i2_gate.py` | control_operativo (REAL_EXECUTION) | M2 (demostración) |

#### 9.1.5 Infrastructure Governance

Fuentes: `Revisión equipo 04.txt`, `guia_base_para_gobernar_agentes.md`, `documento_maestro_lecciones_aprendidas_03_07_v1.5.md`, `auditoria_planeacion_proyecto_youtube_2026-07-27(1).md` — `source_date_or_version: NOT_AVAILABLE` — `audited_repository_or_snapshot: NOT_VERIFIED` — `current_status: NOT_VERIFIED` — `notes: source content unavailable during this execution`.

| finding_id | requirement_summary | current_repository_evidence | canonical_destination | implementation_phase |
|---|---|---|---|---|
| IG-01 | autoridad funcional vs. técnica | `B5_PRE_SCRIPT_FOUNDATION.md` §13; `docs/ALCANCE_Y_COORDINACION_EQUIPOS.md` | B5_PRE §13; ALCANCE_Y_COORDINACION_EQUIPOS.md | B5_PRE_M1 (plan) / M2 (implementación) |
| IG-02 | registries | `config/editorial_profile_registry.json`; `config/responsibility_registry.json`; `config/skill_catalog.json`; `config/capability_registry.json` | registries en `config/` | M2 (saneamiento) |
| IG-03 | maturity | `plans/001_CONTROL_OPERATIVO.md` (estados de madurez de bloques) | control_operativo | M2 (saneamiento) |
| IG-04 | availability | `B5_PRE_SCRIPT_FOUNDATION.md` §7 (componentes existentes/faltantes) | B5_PRE §7 | B5_PRE_M1 (plan) / M2 (saneamiento) |
| IG-05 | gates | `src/scripts/b5_i2_gate.py`; `src/scripts/run_b5_i2_semantic_audit.py`; `src/scripts/topic_belonging_gate.py`; `src/scripts/youtube_adaptation_b5_i2_gate.py` | gates en `src/scripts/` | M2 (saneamiento) |
| IG-06 | provenance | `schemas/execution_provenance_registry.json`; `output/execution_provenance_registry.json` | execution_provenance_registry | M2 (saneamiento) |
| IG-07 | estado operativo | `plans/001_CONTROL_OPERATIVO.md` | control_operativo | B5_PRE_M1 (plan) / M2 (saneamiento) |
| IG-08 | suite canónica | `tests/` (suite de tests del repositorio) | suite de tests | M2 (saneamiento) |
| IG-09 | contaminación | `src/scripts/runtime_contamination_guard.py`; `config/runtime_contamination_policy.json` | runtime_contamination_guard.py | B5_PRE_M1 (verificación) / M2 (saneamiento) |

### 9.2 Resumen de cobertura de fuentes

| Fuente | Disponibilidad | Hallazgos | Estado |
|---|---|---|---|
| `01.1 Auditoría Inteligencia Canal.txt` | UNAVAILABLE | CI-01 … CI-14 | NOT_VERIFIED |
| `02.1 Auditoria de guiones.txt` | UNAVAILABLE | SP-I1-01 … SP-I1-12 | NOT_VERIFIED |
| `Se ha pegado el markdown(42).md` | UNAVAILABLE | SP-I2-01 … SP-I2-10 | NOT_VERIFIED |
| `03.1 Adaptación a YouTube.txt` | UNAVAILABLE | YT-01 … YT-11 | NOT_VERIFIED |
| `Revisión equipo 04.txt` | UNAVAILABLE | IG-01 … IG-09 | NOT_VERIFIED |
| `guia_base_para_gobernar_agentes.md` | UNAVAILABLE | IG-01 … IG-09 | NOT_VERIFIED |
| `documento_maestro_lecciones_aprendidas_03_07_v1.5.md` | UNAVAILABLE | IG-01 … IG-09 | NOT_VERIFIED |
| `auditoria_planeacion_proyecto_youtube_2026-07-27(1).md` | UNAVAILABLE | IG-01 … IG-09 | NOT_VERIFIED |

Cierre de trazabilidad material:

```text
AUDIT_SOURCES_REGISTERED = ALL
AUDIT_SOURCE_CONTENT_VERIFIED = NO
EXTERNAL_AUDIT_FINDINGS_RECONCILED = NOT_VERIFIED
FUNCTIONAL_REQUIREMENTS_MAPPED = YES
UNSUPPORTED_RECONCILIATION_CLAIMS = 0
```

Aclaración de cobertura: `CI-01…CI-14`, `SP-I1-01…SP-I1-12`, `SP-I2-01…SP-I2-10`, `YT-01…YT-11` e `IG-01…IG-09` son **identificadores internos de cobertura funcional** creados para organizar los requisitos. No son identificadores extraídos de auditorías externas, porque sus contenidos no estuvieron disponibles durante la ejecución. Las fuentes externas se mantienen como `UNAVAILABLE` y `NOT_VERIFIED`; sus hallazgos no se declaran `RESOLVED`, `CURRENT` ni `SUPERSEDED`.

### 9.3 Contradicciones funcionales resueltas (decisión canónica documentada)

| Hallazgo (fuente) | Afirmación anterior | Decisión canónica | Estado |
|---|---|---|---|
| `docs/specifications/B3_especificacion_funcional_equipo_01.md` §6 | El sistema debe admitir "una sola obra" y no debe establecerse "obligación de usar varias obras" | El formato principal exige 3–5 obras sustantivas finales y 5–8 candidatas; la afirmación "una sola obra" queda `SUPERSEDED` para el formato principal. Cualquier excepción material requiere aprobación del OWNER | SUPERSEDED |
| `.agent/skills/skill_curation_obras.md` | "sin mínimos rígidos de materiales" | La regla del formato principal (3–5 finales, 5–8 candidatas) es la autoridad de formato; la skill queda como trabajo técnico para Misión 2 (ver §15, fila 1) | CONTRADICTED → decisión documentada; corrección diferida a M2 |
| `.agent/skills/skill_analisis_patrones.md` | "sin imponer una lista fija" (en contexto de análisis) | No contradice la regla 3–5: la lista fija se refiere a dimensiones de análisis, no a la cantidad de obras. No se cambia nada | RESOLVED (sin cambio) |
| `workspace/` (referencias históricas 3–5) | Reglas 3–5 en documentos históricos | Se conservan como referencia histórica; la autoridad vigente está en las políticas de formato | STALE (para consumo operativo) |

Las contradicciones funcionales activas quedan en `0` tras esta decisión documentada.

---

## 10. Requisitos funcionales vigentes de B5-I1

### 10.1 Artefactos

```text
EpisodeBrief
ResearchPack
ClaimsLedger
SourceAccessAndEvidenceReport
ProvisionalThesis
SemanticSufficiencyAudit
```

### 10.2 Matriz de defectos B5-I1 (definición funcional completa)

Las **once dimensiones** siguientes constituyen el criterio funcional completo de la auditoría semántica de B5-I1. La Misión 2 debe materializarlas técnicamente (schema, gate y habilidad) sin añadir ni suprimir criterios. Cada dimensión emite una decisión propia. Ninguna dimensión puede quedar en `PASS` por defecto; la ausencia de evaluación produce `BLOCKED`.

Dimensiones requeridas: `11`. Definidas en este plan: `11`. Indefinidas: `0`.

#### 10.2.1 `VAGUE_CENTRAL_QUESTION`

```text
defect_id: VAGUE_CENTRAL_QUESTION
definition:
  La pregunta central no es concreta ni delimitada: admite respuestas
  genéricas, no determina el objeto de investigación ni el alcance, o
  puede sustituirse por otra sin cambiar el trabajo.
evidence_expected:
  - pregunta central formulada como interrogación específica;
  - sujeto, objeto y límite temporal/espacial/cultural identificables;
  - diferencia observable entre la pregunta y el tema general.
request_changes_condition:
  Existe material suficiente para reformular: la investigación es
  aprovechable y la ambigüedad se localiza en la enunciación.
fail_condition:
  La pregunta no puede delimitarse sin descartar partes sustantivas
  de la investigación, o la ambigüedad persiste tras la reformulación.
blocked_condition:
  - falta el enunciado de la pregunta en el paquete;
  - no puede determinarse cuál era la pregunta investigada;
  - no existe criterio previo de alcance para evaluarla.
correction_route:
  Delimitar sujeto, objeto y límites; reformular la interrogación;
  re-verificar que la investigación responde a la pregunta nueva.
acceptance_condition:
  La pregunta es específica, delimitable y determinante del paquete;
  cada parte de la investigación responde a ella.
reaudit_condition:
  Volver a auditar la dimensión solo con el paquete corregido;
  reutilizar evidencia previa únicamente para lo no afectado.
```

#### 10.2.2 `HYPOTHESIS_DISGUISED_AS_THESIS`

```text
defect_id: HYPOTHESIS_DISGUISED_AS_THESIS
definition:
  Una hipótesis inicial (conjetura a contrastar) se presenta como tesis
  provisional, sin que la evidencia la sostenga todavía; la tesis no
  puede distinguirse de la hipótesis de partida.
evidence_expected:
  - registro diferenciado de hipótesis inicial y tesis provisional;
  - cadena explícita: evidencia → inferencia → tesis;
  - declaración de qué confirma, matiza o refuta la hipótesis.
request_changes_condition:
  Existe evidencia suficiente para derivar una tesis distinta de la
  hipótesis; el defecto se limita a la redacción o al enlace.
fail_condition:
  La evidencia no sostiene la tesis presentada, o la tesis permanece
  indistinguible de la hipótesis tras el intento de corrección.
blocked_condition:
  - falta la hipótesis inicial registrada;
  - falta la evidencia que permitiría contrastarla;
  - no puede evaluarse la relación hipótesis → tesis.
correction_route:
  Reconstruir la tesis desde la evidencia; declarar la distancia con la
  hipótesis inicial y el grado de certeza que la evidencia autoriza.
acceptance_condition:
  Tesis provisional claramente diferenciada de la hipótesis inicial y
  sostenida por evidencia trazable.
reaudit_condition:
  Auditar de nuevo la dimensión tras reconstruir la tesis.
```

#### 10.2.3 `SOURCE_VOLUME_DISGUISED_AS_COVERAGE`

```text
defect_id: SOURCE_VOLUME_DISGUISED_AS_COVERAGE
definition:
  La cantidad de fuentes se presenta como cobertura suficiente sin
  comprobar la cobertura real por dimensión (pregunta, conflicto,
  fenómeno, claims, perspectivas); el volumen sustituye a la
  profundidad.
evidence_expected:
  - matriz de cobertura por dimensión, no recuento de fuentes;
  - declaración por dimensión: CUBIERTA | PARCIAL | PENDIENTE | NO_VERIFICABLE;
  - justificación de reducción o bloqueo cuando una dimensión no está cubierta.
request_changes_condition:
  El volumen es aprovechable pero la distribución de cobertura está
  desequilibrada; puede corregirse reclasificando sin nueva investigación.
fail_condition:
  Dimensiones esenciales quedan sin cubrir y sin justificación, o el
  volumen oculta vacíos que invalidan la suficiencia.
blocked_condition:
  - no puede determinarse qué dimensiones se cubrieron;
  - no existe matriz de cobertura ni listado de fuentes;
  - el acceso a fuentes clave no está registrado.
correction_route:
  Construir la matriz de cobertura por dimensión; reclasificar fuentes;
  reducir el alcance o bloquear las dimensiones sin cobertura.
acceptance_condition:
  Toda dimensión requerida queda declarada con estado y evidencia,
  y cada estado distinto de CUBIERTA tiene decisión de reducción o bloqueo.
reaudit_condition:
  Volver a auditar la matriz de cobertura tras reclasificar.
```

#### 10.2.4 `SOURCE_ACCESS_INFLATION`

```text
defect_id: SOURCE_ACCESS_INFLATION
definition:
  Se declara un nivel de acceso real (visionado, lectura, audición o
  consulta directa) que la evidencia no sostiene; se exagera la calidad
  o el tipo de acceso para inflar la validez de la fuente.
evidence_expected:
  - declaración de acceso por fuente: DIRECT | INDIRECT | SECONDARY_ONLY | NOT_ACCESSED;
  - localizador y registro de consulta que correspondan al nivel declarado;
  - distinción entre lo verificado y lo referido.
request_changes_condition:
  La clasificación de acceso es corregible re-verificando el registro de
  consulta, sin rehacer la investigación.
fail_condition:
  El acceso declarado es falsamente superior al real, y esa inflación
  sostiene afirmaciones críticas del paquete.
blocked_condition:
  - no existe registro de acceso por fuente;
  - no puede determinarse qué se consultó realmente;
  - la fuente no está disponible para verificación.
correction_route:
  Reclasificar el nivel de acceso real de cada fuente; limitar las
  afirmaciones que dependen de acceso no demostrado; marcar
  incertidumbre donde corresponda.
acceptance_condition:
  Cada fuente declara su nivel de acceso real y ninguna afirmación
  crítica depende de acceso no demostrado.
reaudit_condition:
  Re-auditar la dimensión tras reclasificar accesos y limitar afirmaciones.
```

#### 10.2.5 `INDIRECT_SCENE_TREATED_AS_DIRECT`

```text
defect_id: INDIRECT_SCENE_TREATED_AS_DIRECT
definition:
  Una escena, pasaje, capítulo o momento conocido solo a través de un
  resumen, comentario, cita o adaptación se trata como si hubiera sido
  consultado directamente en la fuente primaria.
evidence_expected:
  - localizador de la escena/pasaje en la fuente;
  - tipo de acceso de cada cita: DIRECT | INDIRECT;
  - atribución correcta de la procedencia de la escena.
request_changes_condition:
  El uso de la escena es correcto en sustancia y solo falla la
  atribución del acceso; puede corregirse sin descartar la escena.
fail_condition:
  Afirmaciones críticas de la tesis dependen de escenas tratadas como
  directas siendo indirectas, sin corrección posible.
blocked_condition:
  - no puede identificarse la fuente de la escena;
  - no existe evidencia del tipo de acceso;
  - la obra no está disponible para confirmar la escena.
correction_route:
  Marcar el acceso como indirecto; verificar la escena en la fuente o
  sustituirla; reducir el peso de las afirmaciones dependientes.
acceptance_condition:
  Toda escena citada declara su tipo de acceso real y ninguna
  afirmación crítica descansa sobre una escena falsamente directa.
reaudit_condition:
  Re-auditar la dimensión tras corregir atribuciones de acceso.
```

#### 10.2.6 `CRITICAL_CLAIM_UNSUPPORTED`

```text
defect_id: CRITICAL_CLAIM_UNSUPPORTED
definition:
  Un claim marcado como crítico (sostiene la tesis o la decisión
  editorial) carece de evidencia suficiente, está aislado o se
  apoya solo en la afirmación del propio investigador.
evidence_expected:
  - claims críticos enumerados y trazables;
  - evidencia asociada a cada claim crítico;
  - localizador y nivel de acceso de cada evidencia.
request_changes_condition:
  El claim tiene evidencia posible dentro del material existente; el
  defecto es la falta de enlace o de localizador.
fail_condition:
  Un claim crítico no tiene evidencia disponible y no puede sostener la
  tesis; o la corrección exigiría inventar evidencia.
blocked_condition:
  - no existe lista de claims ni marcación de criticidad;
  - falta la evidencia que permitiría evaluar el claim;
  - no puede determinarse qué afirma exactamente el claim.
correction_route:
  Vincular cada claim crítico a su evidencia; descartar los claims sin
  evidencia; re-verificar que la tesis no dependa de claims huérfanos.
acceptance_condition:
  Todo claim crítico está vinculado a evidencia trazable y ninguna tesis
  depende de claims no soportados.
reaudit_condition:
  Re-auditar la dimensión tras enlazar o descartar claims.
```

#### 10.2.7 `CLAIM_EVIDENCE_MISMATCH`

```text
defect_id: CLAIM_EVIDENCE_MISMATCH
definition:
  La evidencia citada no sostiene el claim que dice sostener: existe
  desajuste entre lo que afirma el claim y lo que demuestra la
  referencia (tema, alcance, contexto o intensidad).
evidence_expected:
  - correspondencia explícita claim → evidencia → localizador;
  - cita o paráfrasis que muestre el contenido realmente soportado;
  - ausencia de evidencia que contradiga el claim sin ser considerada.
request_changes_condition:
  Existe evidencia alternativa en el material que sí sostiene el claim;
  el defecto se corrige sustituyendo o precisando la referencia.
fail_condition:
  La evidencia desmiente o no guarda relación con el claim, y no existe
  evidencia sustituta; el claim no puede mantenerse.
blocked_condition:
  - no puede identificarse la evidencia del claim;
  - la referencia citada no está disponible;
  - no puede determinarse qué demuestra realmente la fuente.
correction_route:
  Sustituir la evidencia por otra que corresponda, o reformular el claim
  para ajustarlo a lo que la evidencia demuestra.
acceptance_condition:
  Cada claim se apoya en evidencia que realmente lo demuestra, con
  localizador verificable y sin contradicciones ignoradas.
reaudit_condition:
  Re-auditar la dimensión tras corregir las correspondencias.
```

#### 10.2.8 `DECORATIVE_RIVAL_VIEW`

```text
defect_id: DECORATIVE_RIVAL_VIEW
definition:
  Una perspectiva rival, contraria o discrepante se menciona solo para
  aparentar equilibrio, sin analizarla, sin evidencia y sin que
  modifique la tesis; la tesis no dialoga con ella.
evidence_expected:
  - enumeración de perspectivas rivales consideradas;
  - análisis de cada rival: en qué consiste, qué evidencia la sostiene;
  - tratamiento de la rival en la tesis (confirmación, matiz o refutación).
request_changes_condition:
  La rival está correctamente identificada y existe material para
  analizarla; el defecto es la ausencia de desarrollo.
fail_condition:
  La rival se menciona decorativamente y la tesis ignora su reto, sin
  que exista material para incorporarla; la suficiencia se pierde.
blocked_condition:
  - no puede identificarse cuál es la rival real;
  - falta la evidencia de la rival para analizarla;
  - no existe registro de rivales consideradas.
correction_route:
  Desarrollar el análisis de cada rival; integrar su reto en la tesis;
  o retirar la mención decorativa y declarar su ausencia justificada.
acceptance_condition:
  Toda rival declarada está analizada y tratada en la tesis; no quedan
  menciones decorativas sin función argumentativa.
reaudit_condition:
  Re-auditar la dimensión tras desarrollar o retirar rivales.
```

#### 10.2.9 `SCOPE_REDUCTION_NOT_PROPAGATED`

```text
defect_id: SCOPE_REDUCTION_NOT_PROPAGATED
definition:
  Una reducción de alcance (obra, periodo, territorio, dimensión o
  promesa) decidida durante la investigación no se propaga a los demás
  artefactos: preguntas, claims, tesis, exclusiones y límites siguen
  refiriendo al alcance original.
evidence_expected:
  - registro del alcance vigente tras la reducción;
  - propagación explícita a pregunta, claims, tesis, exclusiones y límites;
  - coherencia entre el alcance declarado y lo afirmado.
request_changes_condition:
  La reducción está registrada pero su propagación es incompleta; puede
  corregirse alineando los artefactos sin nueva investigación.
fail_condition:
  La reducción no se propaga y deja afirmaciones fuera del alcance
  vigente, o la tesis depende de material excluido por la reducción.
blocked_condition:
  - no puede determinarse el alcance vigente;
  - falta el registro de la decisión de reducción;
  - los artefactos no permiten verificar la propagación.
correction_route:
  Propagar el alcance reducido a todos los artefactos; ajustar claims y
  tesis al alcance vigente; re-verificar exclusiones y límites.
acceptance_condition:
  Todo artefacto es coherente con el alcance vigente y ninguna
  afirmación excede el alcance declarado.
reaudit_condition:
  Re-auditar la dimensión tras propagar el alcance.
```

#### 10.2.10 `TRIVIAL_PROVISIONAL_THESIS`

```text
defect_id: TRIVIAL_PROVISIONAL_THESIS
definition:
  La tesis provisional es trivial: una obviedad, una tautología, un
  lugar común o una recapitulación sin posición propia; no aporta una
  lectura que el espectador no pudiera construir solo.
evidence_expected:
  - tesis con posición específica y defendible;
  - distancia respecto de la mera descripción del fenómeno;
  - grado de certeza y límites declarados.
request_changes_condition:
  La investigación sostiene una tesis no trivial y el defecto es la
  formulación; puede corregirse re-expresando la posición.
fail_condition:
  La tesis permanece trivial tras la corrección, o la investigación no
  contiene material para construir una posición no trivial.
blocked_condition:
  - falta la tesis provisional en el paquete;
  - no puede determinarse la posición sostenida;
  - falta la evidencia mínima para evaluar su no trivialidad.
correction_route:
  Derivar una posición específica desde la evidencia; sustituir
  formulaciones obvias; declarar qué lectura propia aporta la tesis.
acceptance_condition:
  La tesis provisional es específica, defendible, no obvia y ofrece una
  lectura propia sostenida por evidencia.
reaudit_condition:
  Re-auditar la dimensión tras reformular la tesis.
```

#### 10.2.11 `FACT_INTERPRETATION_HYPOTHESIS_CONFUSION`

```text
defect_id: FACT_INTERPRETATION_HYPOTHESIS_CONFUSION
definition:
  Se confunde el estatus epistemológico de las afirmaciones: un hecho
  se presenta como interpretación, una interpretación como hecho, una
  hipótesis como conclusión demostrada, o una conjetura sin marcación
  propia.
evidence_expected:
  - clasificación explícita de cada afirmación: FACT | INTERPRETATION | HYPOTHESIS;
  - coherencia entre el estatus declarado y la evidencia;
  - ausencia de inferencias presentadas como hechos.
request_changes_condition:
  La clasificación es corregible marcando el estatus correcto de cada
  afirmación sin alterar la sustancia.
fail_condition:
  Afirmaciones críticas presentan estatus falseado (interpretación como
  hecho, hipótesis como conclusión) y esa confusión sostiene la tesis.
blocked_condition:
  - no puede determinarse el estatus de las afirmaciones;
  - falta la evidencia para clasificar;
  - el paquete mezcla estatus sin permitir desambiguación.
correction_route:
  Clasificar cada afirmación por su estatus epistemológico; suavizar el
  lenguaje de las interpretaciones; marcar hipótesis y conjeturas como
  tales.
acceptance_condition:
  Cada afirmación relevante declara su estatus y el estatus es coherente
  con la evidencia aportada.
reaudit_condition:
  Re-auditar la dimensión tras reclasificar las afirmaciones.
```

### 10.3 Decisiones de B5-I1

```text
PASS | REQUEST_CHANGES | FAIL | BLOCKED
```

### 10.4 Cierre esperado de B5-I1

```text
B5_I1_REQUIRED_DIMENSIONS = 11
B5_I1_DIMENSIONS_FULLY_DEFINED = 11
B5_I1_UNDEFINED_DIMENSIONS = 0
```

Las reglas de decisión son:

- `REQUEST_CHANGES`: existe material suficiente, el defecto es localizado, no invalida el paquete y existe una ruta concreta de corrección.
- `FAIL`: el defecto invalida materialmente la suficiencia; la investigación, tesis o evidencia no puede aprobarse y requiere rehacer una parte sustantiva.
- `BLOCKED`: falta un input obligatorio, la evidencia no está disponible, no puede evaluarse la dimensión, existe contradicción no resoluble por el auditor o falta una decisión previa obligatoria.
- `PASS`: solo cuando la dimensión queda evaluada, con evidencia suficiente y sin defectos.

---

## 11. Requisitos funcionales vigentes de B5-I2

### 11.1 Artefactos

```text
NarrativeHumanAnalysis
MaterialCuration
RefinedThesis
EditorialScriptPromise
B5I2SemanticAudit
```

### 11.2 Dimensiones obligatorias (definición funcional completa)

Las **diez dimensiones** siguientes constituyen el criterio funcional completo de la auditoría semántica de B5-I2. La Misión 2 debe materializarlas técnicamente (schema, gate y habilidad) sin añadir ni suprimir criterios. Cada dimensión emite una decisión propia. Ninguna dimensión puede quedar en `PASS` por defecto.

Dimensiones requeridas: `10`. Definidas en este plan: `10`. Indefinidas: `0`.

#### 11.2.1 `TRIVIAL_THESIS`

```text
defect_id: TRIVIAL_THESIS
definition:
  La tesis refinada es trivial: obvia, tautológica o un lugar común;
  no presenta una posición específica, defendible y con matices que
  gobierne el episodio y oriente B5-I3.
evidence_expected:
  - tesis refinada con posición específica y defendible;
  - respuesta a la pregunta central;
  - integración de evidencia favorable y adversa;
  - matices y límites declarados.
request_changes_condition:
  La tesis tiene material subyacente para ser específica; el defecto es
  la formulación y puede corregirse sin rehacer análisis o curación.
fail_condition:
  La tesis permanece trivial tras la corrección, o análisis y curación
  no contienen material para sostener una posición no trivial.
blocked_condition:
  - falta la tesis refinada en el paquete;
  - no puede determinarse la posición sostenida;
  - faltan análisis o curación para evaluar la no trivialidad.
correction_route:
  Derivar una posición específica desde análisis y curación; sustituir
  formulaciones obvias; declarar qué lectura propia aporta la tesis.
acceptance_condition:
  Tesis específica, defendible, no obvia, con matices, límites y
  evidencia favorable y adversa integrada.
reaudit_condition:
  Re-auditar la dimensión tras reformular la tesis.
```

#### 11.2.2 `INTERCHANGEABLE_ANALYSIS`

```text
defect_id: INTERCHANGEABLE_ANALYSIS
definition:
  Los análisis son intercambiables entre obras, personajes o episodios:
  si se reemplazara el nombre del sujeto, el hallazgo no cambiaría;
  falta especificidad concreta.
evidence_expected:
  - hallazgos anclados a sujeto, acción, decisión, escena, pasaje o patrón;
  - tensión o contradicción identificada;
  - relación causa → decisión → consecuencia;
  - límites de la interpretación.
request_changes_condition:
  Existe material específico aprovechable y el defecto es que el análisis
  no lo utiliza; puede corregirse anclando los hallazgos.
fail_condition:
  Los análisis permanecen intercambiables tras la corrección, o el
  material no contiene especificidad aprovechable.
blocked_condition:
  - faltan los artefactos de análisis;
  - no puede identificarse qué obra o elemento se analizó;
  - falta la evidencia narrativa para evaluar.
correction_route:
  Re-anclar cada hallazgo a elementos concretos; rechazar formulaciones
  genéricas; indicar qué impide que el análisis sea intercambiable.
acceptance_condition:
  Cada hallazgo es específico de su objeto y no sobreviviría a un
  cambio de sujeto sin alteración.
reaudit_condition:
  Re-auditar la dimensión tras re-anclar los hallazgos.
```

#### 11.2.3 `DECORATIVE_OBJECTION`

```text
defect_id: DECORATIVE_OBJECTION
definition:
  Una objeción o interpretación rival se menciona de forma formularia
  sin tensionar la tesis: no se analiza, no exige respuesta ni modifica
  la argumentación.
evidence_expected:
  - objeciones e interpretaciones rivales enumeradas;
  - análisis de cada una y de su evidencia;
  - efecto de cada objeción sobre la tesis (confirmación, matiz o refutación).
request_changes_condition:
  La objeción es real y existe material para analizarla; el defecto es
  la ausencia de desarrollo.
fail_condition:
  La objeción permanece decorativa y la tesis ignora su reto, sin
  material para incorporarla.
blocked_condition:
  - no puede identificarse la objeción real;
  - falta la evidencia para analizarla;
  - no existe registro de objeciones consideradas.
correction_route:
  Desarrollar el análisis de la objeción; integrar su reto en la tesis;
  o retirarla y declarar su ausencia justificada.
acceptance_condition:
  Toda objeción declarada está analizada y tiene efecto sobre la tesis;
  no quedan objeciones decorativas.
reaudit_condition:
  Re-auditar la dimensión tras desarrollar o retirar objeciones.
```

#### 11.2.4 `FALSE_DEPTH`

```text
defect_id: FALSE_DEPTH
definition:
  El análisis simula profundidad mediante jerga, paralelismos aparentes
  o generalizaciones abstractas, sin identificar mecanismos concretos,
  contradicciones ni consecuencias reales.
evidence_expected:
  - mecanismo causal o estructural identificado;
  - conexión individuo → sistema cuando se afirma;
  - consecuencia concreta;
  - ausencia de jerga que ocupe el lugar del análisis.
request_changes_condition:
  El defecto se localiza en pasajes específicos y existe material para
  sustituir la profundidad aparente por análisis real.
fail_condition:
  La profundidad aparente persiste tras la corrección y no hay material
  para construir profundidad real.
blocked_condition:
  - no puede determinarse qué se analizó realmente;
  - falta el artefacto de análisis;
  - no puede evaluarse la sustancia del texto.
correction_route:
  Sustituir cada pasaje de profundidad aparente por un análisis anclado
  a evidencia concreta; retirar jerga no justificada.
acceptance_condition:
  Todo pasaje aporta profundidad demostrable anclada a evidencia, sin
  jerga sustitutiva.
reaudit_condition:
  Re-auditar la dimensión tras sustituir los pasajes.
```

#### 11.2.5 `REPHRASED_NOT_REFINED_THESIS`

```text
defect_id: REPHRASED_NOT_REFINED_THESIS
definition:
  La tesis refinada es una reformulación cosmética de la provisional:
  no demuestra qué ocurrió tras el análisis y la curación, ni qué se
  confirmó, cambió, descartó o limitó.
evidence_expected:
  - registro de qué se confirmó, cambió, descartó y limitó;
  - identificación de qué análisis o curación provocó cada cambio;
  - tesis funcionalmente distinta o confirmación demostrable.
request_changes_condition:
  Análisis y curación contienen cambios reales; el defecto es que la
  tesis no los refleja y puede corregirse su reconstrucción.
fail_condition:
  La tesis permanece cosmética tras la corrección, o análisis y curación
  no contienen cambios que reflejar.
blocked_condition:
  - falta la tesis provisional o la refinada;
  - faltan análisis y curación para comparar;
  - no puede determinarse el estado previo de la tesis.
correction_route:
  Reconstruir la tesis refinada registrando confirmaciones, cambios,
  descartes y límites, vinculando cada uno a su material.
acceptance_condition:
  La tesis refinada demuestra su evolución desde la provisional y
  cada cambio es trazable a análisis o curación.
reaudit_condition:
  Re-auditar la dimensión tras reconstruir la tesis.
```

#### 11.2.6 `REDUNDANT_CURATION`

```text
defect_id: REDUNDANT_CURATION
definition:
  Dos o más materiales seleccionados cumplen la misma función sin
  justificación sustantiva: la eliminación de uno no modificaría la
  argumentación ni la profundidad.
evidence_expected:
  - función diferenciada por material;
  - diferencia concreta conservada por cada material;
  - coste de contexto justificado frente al valor aportado.
request_changes_condition:
  La redundancia es corregible eliminando o re-funcionando materiales
  sin perder profundidad.
fail_condition:
  La redundancia persiste tras la corrección y no puede justificarse la
  duplicación de función.
blocked_condition:
  - no puede identificarse qué materiales se seleccionaron;
  - falta la curación final;
  - no puede determinarse la función de cada material.
correction_route:
  Eliminar materiales redundantes o reasignarles funciones diferenciadas;
  justificar el solapamiento con una diferencia concreta.
acceptance_condition:
  Cada material conserva una función diferenciada y ningún solapamiento
  carece de justificación sustantiva.
reaudit_condition:
  Re-auditar la dimensión tras ajustar la curación.
```

#### 11.2.7 `NO_ARGUMENTATIVE_PROGRESSION`

```text
defect_id: NO_ARGUMENTATIVE_PROGRESSION
definition:
  El orden de los materiales no produce progresión argumentativa: no hay
  evolución de la comprensión, complementariedad ni tensión; un orden
  alternativo no alteraría el resultado.
evidence_expected:
  - diferencia sustantiva y complementariedad entre materiales;
  - razón del orden;
  - respuesta a qué permite el material posterior que no permitía el anterior;
  - evolución de la comprensión entre inicio y fin.
request_changes_condition:
  Existe material para justificar o reordenar; el defecto es la ausencia
  de razón argumentativa del orden.
fail_condition:
  No existe progresión posible con el material seleccionado y el orden
  no puede aportar argumentación.
blocked_condition:
  - falta la curación final;
  - no puede determinarse el orden;
  - faltan los análisis para evaluar la progresión.
correction_route:
  Reordenar los materiales con criterio argumentativo; justificar la
  razón de cada paso; verificar la evolución de la comprensión.
acceptance_condition:
  El orden produce una progresión demostrable y un orden alternativo
  sería peor o distinto en términos argumentativos.
reaudit_condition:
  Re-auditar la dimensión tras reordenar.
```

#### 11.2.8 `UNSUPPORTED_INFERENCE`

```text
defect_id: UNSUPPORTED_INFERENCE
definition:
  Una inferencia carece de evidencia suficiente, se apoya en evidencia
  autorreferencial (un campo del propio análisis que cita a otro) o
  generaliza más allá de lo que la evidencia permite.
evidence_expected:
  - cada inferencia vinculada a evidencia identificable;
  - relación explícita entre evidencia y afirmación;
  - respeto a límites de generalización y acceso.
request_changes_condition:
  La inferencia es plausible y existe evidencia para sostenerla; el
  defecto es el enlace o la limitación.
fail_condition:
  La inferencia no tiene evidencia disponible o la evidencia la
  contradice, sin corrección posible.
blocked_condition:
  - no puede identificarse la evidencia de la inferencia;
  - falta la fuente citada;
  - no puede determinarse el alcance de la generalización.
correction_route:
  Vincular cada inferencia a evidencia; limitar la generalización;
  retirar las inferencias sin soporte.
acceptance_condition:
  Toda inferencia es trazable a evidencia y ninguna generaliza sin
  límite declarado.
reaudit_condition:
  Re-auditar la dimensión tras vincular o retirar inferencias.
```

#### 11.2.9 `SUMMARY_INSTEAD_OF_ANALYSIS`

```text
defect_id: SUMMARY_INSTEAD_OF_ANALYSIS
definition:
  El análisis recapitula la obra o el material sin interpretarlo: no
  aporta una lectura propia, no identifica tensiones ni consecuencias y
  no transforma el episodio.
evidence_expected:
  - hallazgos interpretativos y no descriptivos;
  - función real del hallazgo: revelar contradicción, complejizar,
    conectar, introducir causa o consecuencia, aportar rival, limitar,
    modificar la tesis o preparar progresión.
request_changes_condition:
  El material permite interpretación y el defecto es la recapitulación;
  puede corregirse transformando la descripción en análisis.
fail_condition:
  El resumen persiste tras la corrección y no hay base interpretativa
  aprovechable.
blocked_condition:
  - no puede distinguirse descripción de interpretación;
  - falta el artefacto de análisis;
  - falta la evidencia narrativa del material.
correction_route:
  Convertir cada pasaje descriptivo en análisis: identificar tensión,
  causa, consecuencia, límite o rival; declarar la función editorial.
acceptance_condition:
  Todo pasaje aporta interpretación con función editorial demostrable y
  no queda recapitulación como sustituto del análisis.
reaudit_condition:
  Re-auditar la dimensión tras transformar los pasajes descriptivos.
```

#### 11.2.10 `MISSING_INTERPRETIVE_LIMIT`

```text
defect_id: MISSING_INTERPRETIVE_LIMIT
definition:
  Faltan los límites de la interpretación: se generaliza de una obra a
  la realidad, se atribuyen intenciones sin evidencia o se presenta
  ficción como prueba directa de un fenómeno real, sin marcar fronteras.
evidence_expected:
  - límites de generalización declarados;
  - distinción ficción / realidad cuando corresponde;
  - atribución de intención limitada a la evidencia;
  - incertidumbre declarada.
request_changes_condition:
  La interpretación es sostenible y solo faltan sus límites; puede
  corregirse marcándolos.
fail_condition:
  La ausencia de límites permite afirmaciones que la evidencia no
  sostiene y no pueden corregirse sin alterar la tesis.
blocked_condition:
  - no puede determinarse el alcance de la interpretación;
  - falta la evidencia para fijar límites;
  - no puede evaluarse la generalización.
correction_route:
  Declarar límites de generalización, distinguir ficción y realidad,
  limitar atribuciones de intención y marcar incertidumbre.
acceptance_condition:
  Toda interpretación declara sus límites y ninguna afirmación excede lo
  que la evidencia autoriza.
reaudit_condition:
  Re-auditar la dimensión tras declarar los límites.
```

### 11.3 Invariantes obligatorios de B5-I2

```text
INVARIANTS:
- No semantic dimension may default to PASS.
- Every required dimension must be emitted exactly once.
- Missing dimensions must produce BLOCKED.
- Duplicated dimensions must produce BLOCKED.
- Unknown dimensions must produce BLOCKED.
- The global decision must be coherent with every dimension.
```

### 11.4 Coherencia mínima de decisión

Se definen como **inválidas** las combinaciones siguientes:

```text
una dimensión FAIL + decisión global PASS
una dimensión BLOCKED + decisión global distinta de BLOCKED
una dimensión REQUEST_CHANGES + decisión global PASS
REQUEST_CHANGES sin required_changes
BLOCKED sin blocking_reasons
reauditoría solicitada sin reaudit_requirements
```

La decisión global de la auditoría B5-I2 debe derivar del conjunto de decisiones por dimensión, y toda corrección solicitada debe declarar sus motivos y requisitos de reauditoría.

### 11.5 Cierre esperado de B5-I2

```text
B5_I2_REQUIRED_DIMENSIONS = 10
B5_I2_DIMENSIONS_FULLY_DEFINED = 10
B5_I2_UNDEFINED_DIMENSIONS = 0
```

La Misión 2 recibe este criterio funcional completo y se limita a materializarlo técnicamente (schema, gate y habilidad). No se delega la definición en una skill, auditoría externa ni misión futura.

---

## 12. YouTube Adaptation — especificación funcional final

Se usa la especificación final (no la auditoría inicial incompleta). Se conservan:

### 12.1 Cinco resultados

```text
EPISODE_YOUTUBE_POSITIONING
EARLY_PACKAGING_HYPOTHESIS
YOUTUBE_DESIGN_CONSTRAINTS
PRELIMINARY_YOUTUBE_RISK_REVIEW
YOUTUBE_B5_I2_FUNCTIONAL_DECISION
```

### 12.2 Diez decisiones

```text
YT_EARLY_AUDIENCE_FIT
YT_VISIBLE_PROMISE
YT_EARLY_PACKAGING_HYPOTHESIS
YT_PROMISE_CONTENT_ALIGNMENT
YT_OPENING_READINESS
YT_DURATION_ENVELOPE
YT_OVERPROMISE_REVIEW
YT_TEXT_PLATFORM_RISK
YT_SCRIPT_RIGHTS_REUSE_RISK
YT_B5_I2_FUNCTIONAL_DECISION
```

### 12.3 Límites

Adaptación a YouTube:

- no modifica unilateralmente la tesis;
- no cambia obras sin devolución a `SCRIPT_PRODUCT`;
- no aprueba el guion;
- no autoriza producción;
- no autoriza publicación;
- no garantiza monetización;
- no resuelve riesgos audiovisuales todavía inexistentes.

### 12.4 Implementación actual

```text
Estado: PARTIAL / PENDING_REAL_DEMONSTRATION
Evidencia: config/youtube_adaptation_r3_traceability.json (10 capacidades, IMPLEMENTED_NOT_DEMONSTRATED)
```

---

## 13. Referencias de separación funcional / técnica

```text
CHANNEL_INTELLIGENCE      → identidad, pertenencia, territorios, audiencia matriz, persona autoral, límites
SCRIPT_PRODUCT           → descubrimiento, investigación, obras, evidencia, análisis, curación, tesis, promesa editorial
YOUTUBE_ADAPTATION      → audiencia concreta, promesa visible, packaging temprano, apertura futura, duración, riesgos plataforma/derechos
INFRASTRUCTURE_GOVERNANCE → materialización técnica, contrato, schema, agentes, prompts, runtime, gates, estados, pruebas, provenance
```

- Infraestructura no inventa criterio editorial.
- Los equipos funcionales no prescriben arquitectura técnica.

---

## 14. Estado y autoridad de ejecución

```text
PLAN_003                        = ACTIVE_RECOVERY_AUTHORITY
PLAN_001                        = PRODUCT_PLAN_RECTOR
HISTORICAL_B5_PRE_M2                         = RECONCILED_NOT_IMPLEMENTED
HISTORICAL_B5_PRE_M2_DEFINED_AS_NEXT_ACTION  = NO
HISTORICAL_B5_PRE_M2_OWNER_AUTHORIZATION     = COMPLETED_FOR_RECONCILIATION_ONLY
HISTORICAL_B5_PRE_M2_STARTED                 = NO
HISTORICAL_CURRENT_MISSION                   = MISSION_01E_COMPLETED_PENDING_OWNER_REVIEW
HISTORICAL_B5_PRE_CANONICAL_FOUNDATION       = RECONCILED_DOCUMENTATION
HISTORICAL_B5_PRE_M1_STATUS                  = FUNCTIONAL_SCOPE_RECONCILED
DOCUMENTARY_STATE_RECONCILIATION             = COMPLETED
TECHNICAL_CAPABILITY_IMPLEMENTATION          = NOT_STARTED
REAL_EXECUTION                               = NOT_DEMONSTRATED
B5_I3                                        = NOT_AUTHORIZED
```

El estado definitivo y la siguiente acción autorizada de este plan se registran únicamente en `plans/001_CONTROL_OPERATIVO.md`.

---

## 15. Contradicciones técnicas deferidas a la Misión 2
Estas son omisiones/discrepancias **técnicas** en superficies activas que **no** se corrigen en esta misión; se clasifican por componente y destino de corrección `FUTURE_B5_PRE_TECHNICAL_IMPLEMENTATION_BACKLOG`:

| # | Componente | Contradicción / carencia | Destino |
|---|---|---|---|
| 1 | skills | "sin mínimos rígidos" en `skill_curation_obras.md` y `skill_analisis_patrones.md` | M2 skills |
| 2 | schema | `MaterialCuration.minItems=1` frente a regla flexible | M2 schema |
| 3 | workflow | curación heredada se produjo antes del análisis | M2 workflow |
| 4 | fuentes | Markdown heredado como fuente paralela | M2 fuentes/runtime |
| 5 | schema | representaciones duplicadas de `MaterialCuration` | M2 schema |
| 6 | B5-I2 | dimensiones con PASS por defecto | M2 schema/gate |
| 7 | B5-I2 | auditoría con dimensiones omitidas | M2 gate |
| 8 | B5-I2 | incoherencia dimensión vs. decisión global | M2 gate |
| 9 | handoffs | handoffs incompletos | M2 |
| 10 | Topic Belonging | criterio funcional completo en la política; la implementación técnica (schemas, flow, gate) debe alinearse con la modalidad TOPIC_FIRST | M2 |
| 11 | entrada | modalidades de entrada no propagadas | M2 |
| 12 | B5-I1 | especificación funcional completa en este plan; la implementación técnica (schema, gate, habilidad) queda para M2 | M2 |
| 13 | YouTube | implementado parcial, estado desincronizado | M2 |
| 14 | registries | madurez posiblemente exagerada | M2 |
| 15 | tests | tests desactualizados | M2 |
| 16 | smoke tests | sin inputs obligatorios | M2 |
| 17 | env | referencias antiguas a `.env.example` | M2 docs |
| 18 | suite | suite completa no confirmada como verde | M2 |
| 19 | enrutado | rutas activas hacia `B5-I3` / workflows heredados | M2 |
