# Sistema Canónico de Contratos, Schemas, Estados y Versionado (Misión B1)

**Versión:** 1.0.0  
**Fecha:** 2026-07-21  
**Propietario:** Infraestructura y Gobernanza (validación técnica)  
**Propósito:** Especificación de la fuente de verdad única para contratos, schemas, estados canónicos, exit codes, versionado e invalidación del motor agéntico.

---

## 1. Módulo de Estados Canónicos y Exit Codes

Los estados del sistema están centralizados en `src/core/status.py` y `src/core/gate_result.py`.

### 1.1 Estados de Artefacto y Pipeline
- `DRAFT`: Artefacto en elaboración inicial.
- `IN_REVIEW`: Artefacto sometido a auditoría o gate.
- `EDITORIAL_SCRIPT_APPROVED`: Guion aprobado por un rol editorial autorizado. No autoriza producción ni publicación.
- `YOUTUBE_PRODUCTION_READY`: Paquete de producción aprobado por un rol de producción autorizado. No existe aún pieza audiovisual final auditada.
- `YOUTUBE_READY`: Pieza audiovisual final, miniatura y metadatos aprobados por un rol de publicación autorizado con activos finales auditados.
- `PUBLISHED`: Pieza publicada en YouTube y registrada en el manifiesto.
- `INVALIDATED`: Artefacto u aprobación anulada por cambios en sus insumos.
- `DEPRECATED`: Versión obsoleta reemplazada por una versión superior.

### 1.2 Mapeo Estricto de Exit Codes (GateResult)
| Gate Status | Exit Code | Descripción |
|---|---|---|
| `PASS` | `0` | El artefacto o fase cumple el 100% de los criterios del gate. |
| `WARN` | `0` | Advertencias no bloqueantes registradas. |
| `FAIL` | `1` | Incumplimiento de criterios; detiene el avance del pipeline. |
| `BLOCKED` | `2` | Insuficiencia de fuentes, falta de inputs o inconsistencia de aprobaciones. |

Nota: El exit code `3` (`ERROR`) corresponde a un error técnico o de infraestructura no representado como un `GateResult` de gate válido.

---

## 2. Aprobaciones y Roles Funcionales Autorizados

Los contratos de aprobación requieren **identidad verificable** (no texto ambiguo como `"aprobado"` o `"usuario"`) y un **rol funcional autorizado**:

| Tipo de Aprobación | Roles Autorizados | Transición Permitida |
|---|---|---|
| `EditorialScriptApproval` | `EDITORIAL_LEAD`, `EDITORIAL_REVIEWER` | `EDITORIAL_SCRIPT_APPROVED` |
| `HumanProductionApproval` | `PRODUCTION_LEAD` | `YOUTUBE_PRODUCTION_READY` |
| `HumanPublicationApproval` | `PUBLICATION_LEAD` | `YOUTUBE_READY` (requiere activos audiovisuales finales) |
| `TechnicalValidation` | `TECHNICAL_AUDITOR`, `SYSTEM_AUTOMATION` | Validación de contratos, schemas y checksums |

---

## 3. Catálogo de Contratos y Schemas JSON (B1-C1 a B1-C34)

| ID Contrato | Nombre del Contrato | Schema JSON | Rol Funcional Autorizado |
|---|---|---|---|
| **B1-C1** | `EditorialProfile` | `schemas/editorial_profile.json` | Rol Editorial |
| **B3-C1** | `EditorialProfileApproval` | `schemas/editorial_profile_approval.json` | Equipo 01 |
| **B3-C2** | `ActiveEditorialProfile` | `schemas/active_editorial_profile.json` | Infraestructura y Gobernanza |
| **B3-C3** | `VoiceSample` | `schemas/voice_sample.json` | Equipo 01 |
| **B1-C2** | `EpisodeBrief` | `schemas/episode_brief.json` | Rol Editorial |
| **B1-C3** | `SourceAccessAndEvidenceReport` | `schemas/source_access_and_evidence_report.json` | Rol Investigación / Evidencia |
| **B1-C4** | `PackagingHypothesis` | `schemas/packaging_hypothesis.json` | Rol Adaptación YouTube / Editorial |
| **B1-C5** | `ViewerJourney` | `schemas/viewer_journey.json` | Rol Editorial |
| **B1-C6** | `OpeningDesign` | *Documentado* | Rol Editorial |
| **B1-C7** | `ClosingDesign` | *Documentado* | Rol Editorial |
| **B1-C8** | `NarrativePlan` | `schemas/narrative_plan.json` | Rol Editorial |
| **B1-C9** | `ScriptBlockContract` | `schemas/script_block_contract.json` | Rol Editorial / Redacción |
| **B1-C10** | `CorrectionRoutingPolicy` | `schemas/correction_routing_policy.json` | Rol Técnico / Auditoría |
| **B1-C11** | `ScriptVersionManifest` | `schemas/script_version_manifest.json` | Rol Técnico |
| **B1-C12** | `GateResult` | `schemas/gate_result.json` | Rol Técnico / Automatización |
| **B1-C13** | `EditorialEditReport` | `schemas/editorial_edit_report.json` | Rol Edición Editorial |
| **B1-C14** | `FinalEditorialAudit` | `schemas/final_editorial_audit.json` | Rol Auditoría Editorial |
| **B1-C15** | `FinalDeliveryManifest` | `schemas/final_delivery_manifest.json` | Rol Entrega / Técnico |
| **B1-C16** | `EditorialLearningCandidate` | `schemas/editorial_learning_candidate.json` | Rol Aprendizaje Editorial |
| **B1-C17** | `ResearchPack` | `schemas/research_pack.json` | Rol Investigación |
| **B1-C18** | `CurationDecision` | `schemas/curation_decision.json` | Rol Curación Editorial |
| **B1-C19** | `ThesisArtifact` | `schemas/thesis_artifact.json` | Rol Editorial |
| **B1-C20** | `ReadAloudReview` | *Documentado* | Rol Oralidad |
| **B1-C21** | `ClaimsLedger` & `FactCheckReport` | `schemas/claims_ledger.json`, `schemas/fact_check_report.json` | Rol Fact-Checking / Verificación |
| **B1-C22** | `SourceTransformationAndOriginalityReview` | *Documentado* | Rol Auditoría Editorial |
| **B1-C23** | `EditorialScriptApproval` | `schemas/editorial_script_approval.json` | Rol Editorial |
| **B1-C24** | `HumanProductionApproval` | `schemas/human_production_approval.json` | Rol Producción |
| **B1-C24A** | `HumanPublicationApproval` | `schemas/human_publication_approval.json` | Rol Publicación |
| **B1-C25** | `PromiseCorrespondenceReport` | *Documentado* | Rol Adaptación YouTube |
| **B1-C26** | `YouTubePackagingDecision` | *Documentado* | Rol Adaptación YouTube |
| **B1-C27** | `PlatformAndMonetizationRiskReport` | *Documentado* | Rol Adaptación YouTube / Derechos |
| **B1-C28** | `CopyrightAndReuseReport` | *Documentado* | Rol Derechos |
| **B1-C29** | `AudiovisualProductionRightsBrief` | *Documentado* | Rol Derechos / Producción |
| **B1-C30** | `SessionContinuityPlan` | *Documentado* | Rol Adaptación YouTube |
| **B1-C31** | `PublicationPackage` | `schemas/publication_package.json` | Rol Adaptación YouTube |
| **B1-C32** | `PublishedVersionManifest` | `schemas/published_version_manifest.json` | Rol Publicación / Trazabilidad |
| **B1-C33** | `PerformanceSnapshot` | `schemas/performance_snapshot.json` | Rol Analítica YouTube |
| **B1-C34** | `YouTubeLearningReport` | *Documentado* | Rol Aprendizaje YouTube |

---

## 4. Reglas de Versionado y Cálculo de Checksums

1. **Hash Canónico:** Todo artefacto o aprobación calcula su `checksum` utilizando el algoritmo SHA-256 sobre la representación JSON canónica (`sort_keys=True`).
2. **Prevención de Sobrescritura Silenciosa:** `VersionManifest` rechaza cualquier intento de re-registrar una versión existente si el checksum difiere del original.
3. **Ligado de Aprobaciones:** Una aprobación almacena obligatoriamente `checksum` y `version`.

---

## 5. Reglas de Invalidación en Cascada

1. **Modificación de Artefacto Aprobado:** Cualquier modificación en el contenido de un artefacto rompe la coincidencia de checksum e invalida automáticamente su aprobación previa.
2. **Modificación del EditorialProfile:** Invalida en cascada briefs, packs de investigación, planes narrativos, guiones y aprobaciones asociadas.
3. **Aprendizajes CANDIDATE:** Un aprendizaje en estado `CANDIDATE` NO puede alterar el `EditorialProfile` activo. Solo un aprendizaje en estado `APPROVED` o `INTEGRATED` emite cambios al perfil.

---

## 6. Diferidos a B2 o Bloques Posteriores

### B4-I1 — Responsabilidades y skills

- `schemas/responsibility_registry.json` define las seis responsabilidades base, dos familias funcionales y el mapeo legado.
- `config/responsibility_registry.json` contiene el registro canónico operativo.
- `schemas/skill_catalog.json` define el contrato del catálogo.
- `config/skill_catalog.json` relaciona cada skill existente con su destino neutral.


- **B2:** Reparación del arnés de ejecución de scripts antiguos (`scripts/`) y gates críticos de CLI.
- **B3:** Compilación formal y validación del `EditorialProfile` de producción.
- **B4-B10:** Integración de skills, pipelines de generación, edición de desarrollo, auditorías avanzadas y métricas en vivo.

## 7. Sede canónica portable y adapter .agent/

La arquitectura del sistema se organiza en dos capas:

### 7.1 Sede canónica (portable)

```
prompts/roles/<role_id>/<version>.md     → prompts oficiales versionados
config/                                  → registros y configuraciones agnósticas
schemas/                                 → contratos JSON Schema
```

Esta sede no depende de ningun proveedor, IDE o modelo concreto. Es la fuente de verdad portable del sistema.

### 7.2 .agent/ como adapter de compatibilidad

```
.agent/rules/     → reglas operativas para el agente del entorno actual
.agent/skills/    → skills locales del agente operativo
.agent/workflows/ → workflows del agente operativo
```

`.agent/` es un adapter de compatibilidad. Contiene reglas, skills y workflows adaptados al entorno del agente operativo (por ejemplo, Antigravity, Codex, OpenCode). No duplica la sede canonica: apunta o deriva de ella.

La sede canónica (`prompts/ + config/ + schemas/`) y el adapter (`.agent/`) mantienen separacion de capas. El adapter puede ser sustituido cuando el entorno operativo cambie, sin afectar la sede canonica.
