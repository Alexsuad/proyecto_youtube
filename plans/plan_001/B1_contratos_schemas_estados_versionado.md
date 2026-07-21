# PLAN-001 / B1 — Contratos, schemas, estados y versionado

**Plan rector:** [`../001_reestructuracion_motor_agentico_editorial_y_harness.md`](../001_reestructuracion_motor_agentico_editorial_y_harness.md)  
**Control operativo:** [`../001_CONTROL_OPERATIVO.md`](../001_CONTROL_OPERATIVO.md)  
**Versión derivada:** `PLAN-001 v1.3`  
**Estado inicial:** `PLANNED`  
**Dependencia:** `B0`  
**Siguiente tramo:** `B2 y B3`  
**Gate resumido:** Contratos canónicos aprobados

> Este archivo es una proyección operativa del Plan 001. No crea autoridad nueva ni sustituye el plan rector. Ante una contradicción, prevalece el plan rector y debe bloquearse la misión hasta resolverla.

## 0. Uso operativo

Lectura mínima para ejecutar una misión de este bloque:

1. `AGENTS.md` del repositorio, si existe.
2. docs/ALCANCE_Y_COORDINACION_EQUIPOS.md.
3. `plans/001_CONTROL_OPERATIVO.md`.
4. Este archivo.
5. La misión concreta y los archivos expresamente autorizados.

No leer por defecto el Plan 001 completo, otros bloques, todo `workspace/` ni reportes históricos. Consultar el plan rector únicamente para resolver una contradicción, una autoridad, una dependencia o una referencia expresa.

### Referencias normativas relacionadas

- §10 Estados canónicos
- §11 Modelo de artefactos y versionado
- §28 Política de implementación por misiones

---

## 1. Objetivo

Definir una única fuente de verdad para entradas, salidas, estados, versiones, correcciones y entregables antes de modificar scripts o skills.

## 2. Contratos obligatorios

### B1-C1 — EditorialProfile

Campos mínimos:

```text
profile_id
channel_id
version
status
created_at
updated_at

functional_owner
functional_approval_status
functional_approved_by
functional_approved_at

identity
purpose
positioning
primary_promise
secondary_benefits

audience
audience_relationship
brand_personality
narrator_role

editorial_territories
pillars
exclusions
topic_selection_criteria

tone
language
voice_rules

conceptual_title_principles
conceptual_thumbnail_principles

ethical_limits
psychological_analysis_policy
spoiler_policy
citation_style
attribution_policy
quotation_policy
source_visibility

themes
formats
narrative_preferences
quality_criteria
required_elements
forbidden_elements

stable_brand_core
editorial_preferences
format_rules
transversal_policies
approved_learnings

decision_confidence
pending_identity_decisions
change_rationale

source_lineage
source_hashes
checksum
```

El contenido debe conservar diferenciadas estas dimensiones, aunque se compile en un solo artefacto:

```text
NÚCLEO_ESTABLE_DE_MARCA
PREFERENCIAS_EDITORIALES
REGLAS_DE_FORMATO
POLÍTICAS_TRANSVERSALES
APRENDIZAJES_APROBADOS
DECISIONES_PENDIENTES
```

La aprobación funcional del contenido corresponde al Equipo 01. La validación técnica del contrato, compilación, lineage, versionado, checksum e invalidación corresponde al Equipo 04.

### B1-C2 — EpisodeBrief

```text
episode_id
profile_id
profile_version
tema
pregunta_central
conflicto_o_tension
tesis_provisional
objetivo
transformacion_esperada
audiencia_concreta
angulo_diferencial
alcance
fuera_de_alcance
spoilers
tono
duracion_objetivo
ritmo_locucion
nivel_investigacion
fuentes_requeridas
obra_o_fuente_principal
tipo_de_guion_principal
tipo_de_guion_secundario
estructura_candidata
razon_de_eleccion
citation_style
attribution_policy
quotation_policy
source_visibility
salida_esperada
```

No se imponen cantidades arbitrarias sin política editorial aprobada.

### B1-C3 — SourceAccessAndEvidenceReport

```text
material_principal_disponible
tipo_de_acceso
fuentes_primarias
fuentes_secundarias
escenas_verificadas
escenas_descritas_indirectamente
claims_sostenibles
claims_pendientes
limitaciones
nivel_de_confianza
can_proceed
required_disclosures
```

### B1-C4 — PackagingHypothesis

```text
episode_audience
audience_profile_ref
audience_knowledge_assumption
recognized_tension
relevance_reason
expectation_to_avoid

promesa_de_clic
titulo_de_trabajo
concepto_de_miniatura
pregunta_que_el_espectador_espera_resolver
diferenciador_del_video
riesgo_de_sobrepromesa

functional_owner
team_03_approval_status
team_03_approved_by
team_03_approved_at

team_02_deliverability_validation
team_02_validation_notes

alignment_with_thesis
alignment_with_opening
version
checksum
```

La audiencia concreta debe derivarse del `EditorialProfile` aprobado. No puede utilizarse para redefinir silenciosamente la audiencia general del canal.

La autoridad funcional se divide así:

```text
Equipo 03
→ define o aprueba audiencia concreta, promesa visible
  e hipótesis temprana de packaging.

Equipo 02
→ valida que la tesis y la arquitectura puedan cumplir
  honestamente la promesa.

Equipo 02 no aprueba unilateralmente el packaging.
Equipo 03 no modifica unilateralmente la tesis.
```

### B1-C5 — ViewerJourney

```text
estado_inicial_del_espectador
creencia_inicial_probable
pregunta_que_lo_mantiene
primer_descubrimiento
complicacion
cambio_de_perspectiva
tension_principal
revelacion_o_payoff
estado_final_del_espectador
```

Cada bloque incluye:

```text
que_sabe_antes
que_sabe_despues
que_siente_o_cuestiona
por_que_quiere_continuar
promesa_parcial_resuelta
pregunta_abierta
```

### B1-C6 — OpeningDesign

```text
hook_function
opening_question
initial_tension
minimum_context
early_payoff
promise
first_transition
estimated_words
estimated_time
risks
```

### B1-C7 — ClosingDesign

```text
central_question_answer
thesis_payoff
opening_callback
final_image_or_idea
emotional_resolution
cta_strategy
new_ideas_prohibited
estimated_words
estimated_time
```

El CTA puede ser inexistente si perjudica el cierre.

### B1-C8 — NarrativePlan

```text
script_plan_id
episode_id
script_type
thesis_provisional
thesis_refined
main_objection
nuance
promise
packaging_hypothesis_ref
viewer_journey_ref
opening_design_ref
closing_design_ref
blocks
climax
word_budget_total
wpm_target
```

Cada bloque:

```text
block_id
function
central_question
new_information
emotional_or_intellectual_change
source_refs
word_budget
entry_transition
exit_transition
must_not_repeat
prepares_next
viewer_state_before
viewer_state_after
partial_payoff
open_question
```

### B1-C9 — ScriptBlockContract

```text
block_id
plan_version
context_pack_version
required_sources
forbidden_repetitions
required_transition
word_budget_min
word_budget_max
narrative_function
previous_block_summary
next_block_purpose
output_path
```

### B1-C10 — CorrectionRoutingPolicy

El reporte de defecto debe incluir:

```text
defect_type
severity
origin_artifact
invalidated_artifacts
return_state
required_revalidation
suggested_owner
```

Rutas canónicas:

```text
Problema de datos                 -> investigación
Problema de acceso o evidencia    -> evidencia
Problema de selección             -> curación
Problema de tesis                 -> tesis refinada
Problema de promesa               -> packaging hypothesis
Problema de recorrido             -> viewer journey
Problema de estructura            -> outline
Problema de continuidad           -> edición de desarrollo
Problema de frase u oralidad       -> edición de línea
Problema factual                  -> verificación
Problema de originalidad          -> transformación de fuentes
Problema de identidad             -> perfil o aplicación del perfil
```

### B1-C11 — ScriptVersionManifest

Incluye los campos definidos en la sección 11.3 y controla invalidación y checksum.

### B1-C12 — GateResult

```text
gate_id
artifact_id
artifact_version
status
summary
violations
warnings
evidence
checked_at
checker_version
exit_code
```

### B1-C13 — EditorialEditReport

```text
input_version
output_version
edit_type
changes_by_category
continuity_findings
redundancy_findings
line_findings
orality_findings
unresolved_issues
invalidated_artifacts
```

### B1-C14 — FinalEditorialAudit

```text
profile_compliance
brief_compliance
packaging_promise_compliance
evidence_sufficiency
thesis_quality
viewer_journey
opening_quality
progression
coherence
originality
source_transformation
voice
orality
closing_quality
factual_traceability
platform_risk
production_readiness
system_review
product_review
decision
correction_route
```

El auditor no modifica el guion auditado.

### B1-C15 — FinalDeliveryManifest

Debe identificar:

```text
final_script_clean
final_script_annotated
claims_ledger
metrics
known_limitations
final_candidate_version
human_approved_version
checksums
approval_record
```

### B1-C16 — EditorialLearningCandidate

```text
learning_id
observed_change
reason
scope
evidence_count
contexts
exceptions
confidence
status
approved_by
source_episode_versions
```

### B1-C17 — ResearchPack

```text
research_id
episode_id
brief_version
scope
facts
interpretations
hypotheses
contradictions
alternative_views
scene_evidence
source_registry
claims_candidates
unsupported_claims
narrative_opportunities
narrative_human_analysis_by_material
limitations
created_at
```

Cada entrada de `narrative_human_analysis_by_material` debe poder representar, cuando aplique:

```text
material_id
character_or_subject
desire
feared_loss
avoidance
self_and_world_beliefs
stated_vs_observed_contradiction
revealing_decision
decision_cost
change_and_persistence
environment_role
supporting_scene_or_behavior
alternative_reading
fact_interpretation_or_hypothesis
real_life_analogy_limits
unique_contribution
thesis_support_tension_or_contradiction
confidence
```

### B1-C18 — CurationDecision

```text
curation_id
research_version
narrative_human_analysis_ref
preselected_materials
selected_materials
rejected_materials
narrative_function_by_material
sequence_rationale
perspective_diversity
context_cost
redundancy_risk
climax_contribution
unique_contribution_by_material
thesis_support_tension_or_contradiction
spoiler_requirements
decision
```

### B1-C19 — ThesisArtifact

Debe admitir dos estados diferenciados:

```text
THESIS_PROVISIONAL
THESIS_REFINED
```

Campos mínimos:

```text
thesis_id
stage
statement
supporting_reasoning
main_objection
nuance
simplification_risk
open_questions
source_refs
packaging_alignment
viewer_transformation
version
```

### B1-C20 — ReadAloudReview

```text
input_version
method
reviewer_or_tool
pronunciation_issues
breathing_issues
syntax_issues
subject_clarity_issues
pause_issues
monotony_issues
density_issues
transition_issues
recommended_changes
status
```

### B1-C21 — ClaimsLedger y FactCheckReport

`ClaimsLedger` registra:

```text
claim_id
script_location
claim_text
claim_type
source_refs
evidence_excerpt
attribution_required
verification_status
confidence
limitations
```

`FactCheckReport` registra:

```text
input_version
verified_claims
corrected_claims
blocked_claims
interpretations_reclassified
unresolved_claims
required_disclosures
output_version
status
```

### B1-C22 — SourceTransformationAndOriginalityReview

```text
input_version
source_dependency_map
distinctive_phrases
idea_order_similarity
reused_examples
single_source_dependency
interpretation_attribution
structural_similarity
voice_imitation_risk
transformative_value
required_corrections
status
```

### B1-C23 — EditorialScriptApproval

```text
artifact_id
script_version
checksum
decision
approved_by
approved_at
notes
invalidated_at
invalidation_reason
```

Esta aprobación confirma que el guion puede pasar a Adaptación a YouTube. No autoriza publicación.

### B1-C24 — HumanProductionApproval

```text
publication_package_id
publication_package_version
script_version
packaging_version
platform_and_rights_review_version
checksum
decision
approved_by
approved_at
notes
invalidated_at
invalidation_reason
```

Decisiones permitidas:

```text
APPROVED_FOR_PRODUCTION
REQUEST_CHANGES
REJECT
```

Solo `APPROVED_FOR_PRODUCTION` permite declarar `YOUTUBE_PRODUCTION_READY`.

Esta aprobación no autoriza publicar.

### B1-C24A — HumanPublicationApproval

Contrato reservado para la futura revisión de la pieza audiovisual final:

```text
final_candidate_id
audiovisual_version
thumbnail_version
title_version
description_version
chapters_version
clips_and_music_manifest_version
synthetic_or_altered_content_review_version
final_rights_review_version
checksum
decision
approved_by
approved_at
notes
invalidated_at
invalidation_reason
```

Decisiones permitidas:

```text
APPROVED_FOR_PUBLICATION
REQUEST_CHANGES
REJECT
```

Solo `APPROVED_FOR_PUBLICATION` permite declarar `YOUTUBE_READY`.

Este contrato no puede aprobarse antes de existir y auditarse la pieza audiovisual final exacta.

### B1-C25 — PromiseCorrespondenceReport

```text
input_version
episode_audience
visible_promise
title
thumbnail_concept
opening_alignment
central_question_alignment
development_alignment
conclusion_alignment
promise_delivered
overpromise_risk
misleading_risk
required_corrections
status
```

### B1-C26 — YouTubePackagingDecision

```text
input_version
episode_audience
visible_promise
central_conflict
recommended_option
alternative_options
discarded_options
title_thumbnail_complementarity
script_evidence
clickbait_risk
platform_risk
visual_rights_risk
confidence
status
```

### B1-C27 — PlatformAndMonetizationRiskReport

Este contrato evalúa riesgo; no certifica monetización.

```text
input_version
policy_version
advertiser_friendly_risk
sensitive_topics
context_and_treatment
graphic_level
central_or_incidental
glorification_or_criticism
metadata_risk
repetitive_content_risk
reused_content_risk
synthetic_or_altered_content_review
required_corrections
limitations
status
```

Estados funcionales permitidos:

```text
LOW_IDENTIFIED_RISK
LOW_RISK_WITH_NOTES
LIMITED_ADS_RISK
HIGH_PLATFORM_RISK
BLOCKED
```

Estos estados son internos de este reporte y no sustituyen los estados canónicos del gate.

### B1-C28 — CopyrightAndReuseReport

```text
input_version
third_party_materials
source_or_license
editorial_function
expected_duration
original_audio_required
transformative_context
plot_reconstruction_risk
content_id_risk
reuse_policy_risk
alternative_without_asset
required_corrections
limitations
status
```

### B1-C29 — AudiovisualProductionRightsBrief

```text
input_version
block_id
suggested_visual_material
editorial_function
minimum_necessary_use
original_audio_policy
alternative_visual
graphics_or_original_assets
rights_notes
risk_level
status
```

### B1-C30 — SessionContinuityPlan

```text
input_version
recommended_next_video
alternative_video
playlist
continuity_reason
bridge_phrase
end_screen
pinned_comment
no_available_video_justification
future_content_opportunity
status
```

### B1-C31 — PublicationPackage

```text
package_id
package_version
script_version
approved_title
approved_thumbnail_or_brief
description
chapters_status
attributions
links
cta
end_screen
playlist
next_video
pinned_comment
shorts
promise_correspondence_report_version
platform_risk_report_version
copyright_and_reuse_report_version
audiovisual_rights_brief_version
known_limitations
publication_checklist
status
```

### B1-C32 — PublishedVersionManifest

```text
video_id
publication_date
script_version
audiovisual_version
title_version
thumbnail_version
description_version
end_screen_version
pinned_comment_version
playlist_version
publication_package_version
change_history
status
```

Cada entrada de `change_history` debe incluir:

```text
element
previous_version
new_version
changed_at
change_reason
observation_window_start
observation_window_end
```

Elementos mínimos trazables:

```text
title
thumbnail
description
end_screen
pinned_comment
playlist
```

### B1-C33 — PerformanceSnapshot

Puede alimentarse manualmente durante este plan.

```text
published_version
observation_window
active_title_version
active_thumbnail_version
active_description_version
active_end_screen_version
active_pinned_comment_version
active_playlist_version
mixed_version_window
attribution_status
impressions
ctr_with_context
initial_retention
average_view_duration
retention_by_block
traffic_sources
new_and_returning_viewers
end_screen_results
comment_signals
subscriber_signals
device_context
data_limitations
status
```

Si la ventana contiene más de una versión de un elemento, debe:

* dividirse;
* cerrarse en la fecha del cambio;
* o marcarse como `MIXED_VERSION_WINDOW`.

No puede atribuirse un resultado a un título, miniatura u otro elemento concreto cuando la ventana mezcla versiones sin declararlo.

### B1-C34 — YouTubeLearningReport

```text
published_version
packaging_findings
audience_findings
topic_findings
opening_findings
duration_findings
continuity_findings
confirmed_findings
inconclusive_findings
next_experiment
profile_change_candidate
status
```

Ningún hallazgo modifica automáticamente el `EditorialProfile`.

## 3. Implementación propuesta

```text
docs/contracts/
schemas/
src/core/status.py
src/core/gate_result.py
src/core/contract_validation.py
src/core/version_manifest.py
src/core/invalidation.py
```

## 4. Pruebas mínimas

- estado desconocido se rechaza;
- estados contradictorios se rechazan;
- falta de campo obligatorio produce `BLOCKED`;
- contrato inválido no avanza;
- exit code coincide con estado;
- cambio de artefacto aprobado invalida su aprobación;
- versión no puede sobrescribirse silenciosamente;
- auditoría final no puede señalarse como edición;
- ResearchPack distingue hecho, interpretación e hipótesis;
- ResearchPack contiene análisis narrativo y humano trazable por material;
- CurationDecision asigna función narrativa a cada material;
- CurationDecision referencia el análisis previo y diferencia preselección de selección final;
- ClaimsLedger rechaza claims sin estado y fuente;
- EditorialScriptApproval queda ligada a versión y checksum;
- HumanProductionApproval queda ligada al paquete de producción, versión y checksum;
- HumanPublicationApproval queda ligada a la pieza audiovisual final, activos definitivos, versión y checksum;
- HumanProductionApproval no puede declarar YOUTUBE_READY;
- HumanPublicationApproval no puede emitirse sin activos audiovisuales finales;
- PlatformAndMonetizationRiskReport no puede sustituir la auditoría editorial ni la auditoría de adaptación a YouTube;
- aprendizaje `CANDIDATE` no puede modificar el perfil activo.

## 5. Gate B1

```text
PASS si:
- todos los contratos están documentados y versionados;
- Producto aprueba los campos editoriales;
- Desarrollo aprueba su implementabilidad;
- existe un módulo único de estados;
- versionado e invalidación tienen tests;
- ejemplos válidos e inválidos están cubiertos;
- no se han inventado requisitos editoriales fuera de autoridad.
```

---
