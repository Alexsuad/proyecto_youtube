# PLAN-001 — Control operativo

**Documento:** Proyección operativa resumida  
**Plan rector:** [`001_reestructuracion_motor_agentico_editorial_y_harness.md`](001_reestructuracion_motor_agentico_editorial_y_harness.md)  
**Índice por bloques:** [`plan_001/README.md`](plan_001/README.md)  
**Versión del plan:** `1.4`
**Última sincronización:** `2026-07-22`

## 1. Estado canónico

```yaml
plan_id: PLAN-001
plan_version: "1.4"
plan_status: READY_FOR_EXTERNAL_AUDIT
implementation_authorized: true
authorized_blocks: [B0, B1, B2]
current_block: B3
current_mission: B3-I4-VALIDATION
b3_i1_implementation: COMPLETED
b3_i1_technical_audit: PASS
b3_profile_status: DRAFT
b3_implementation_status: IN_PROGRESS
b3_i2_implementation: COMPLETED
b3_i2_external_technical_audit: PASS
b3_i2_commit: 5872aa8cda6ff65cd2228ff3d681afbb8ff53f53
b3_i3_implementation: COMPLETED
b3_i3_external_technical_audit: PASS
b3_i3_commit: ad306fe46a9d58546369308be10716eea656afae
b3_i4_authorization: CONDITIONAL
b3_i4_primary_voice_sample: DEPRECATED
b3_i4_team_01_functional_approval: REQUIRED
b3_i4_functional_blocker: REMOVED
team_01_clarification: APPROVED
voice_evidence_level: SPECIFICATION_BASED
authentic_editorial_writing_sample_status: NOT_AVAILABLE
editorial_writing_reference_corpus_mechanism: AVAILABLE
b3_authorized_missions: [B3-I4-VALIDATION]
b3_not_authorized_missions: [B4]
b3_i4_preflight_implementation: COMPLETED
b3_i4_preflight_external_audit: PASS
b3_i4_primary_sample_available: NOT_REQUIRED
b3_i4_authorized_complementary_samples: 0
b3_i4_invalid_or_incomplete_samples: 0
b3_i4_corpus_ready: YES
b3_i4_execution: IN_PROGRESS
next_allowed_action: COMPLETE_B3-I4_VALIDATION
next_implementation_block_if_approved: B3-I4-VALIDATION
active_plan: plans/001_reestructuracion_motor_agentico_editorial_y_harness.md
```

La aclaración aprobada del Equipo 01 establece evidencia de voz `SPECIFICATION_BASED`; una muestra auténtica futura es opcional. B3-I4 continúa en validación. El perfil editorial real continúa en `DRAFT`. No existe activación real, no hay aprobación del Equipo 01, no hay validación técnica final y B4 no está autorizado.

## 2. Autoridad documental

```text
1. Decisiones explícitas posteriores del propietario
2. docs/ALCANCE_Y_COORDINACION_EQUIPOS.md
3. Decisiones funcionales aprobadas de la responsabilidad competente
4. Plan 001 v1.4
5. Auditorías finales vigentes de las responsabilidades funcionales
6. Este control operativo
7. Archivo del bloque activo
8. Misión técnica autorizada
9. Reportes del agente ejecutor
```

Este control resume estado y navegación. No sustituye contratos, criterios ni decisiones del plan rector.

La autoridad se resuelve por especialidad. El Plan 001 y este control operativo no pueden sustituir la aprobación funcional de la responsabilidad competente ni permitir que se invadan las decisiones de otra responsabilidad.

## 3. Lectura mínima por misión

```text
OBLIGATORIO:
- AGENTS.md, si existe
- docs/ALCANCE_Y_COORDINACION_EQUIPOS.md
- plans/001_CONTROL_OPERATIVO.md
- plans/plan_001/<BLOQUE_ACTIVO>.md
- misión técnica autorizada
- archivos reales expresamente indicados

NO LEER POR DEFECTO:
- el Plan 001 completo
- otros bloques
- todo workspace/
- todo output/
- auditorías históricas no vinculadas
```

Consultar el plan rector completo solo para resolver contradicciones, autoridad, cambio de alcance, dependencia, estado o referencia expresa.

## 4. Reglas globales no negociables

1. Más Allá del Guion sigue siendo el producto rector.
2. Cada responsabilidad decide y audita únicamente su especialidad.
3. La responsabilidad de validación técnica es el único puente hacia agentes operativos.
4. El agente ejecutor termina en `READY_FOR_AUDIT`, nunca se autoaprueba.
5. Un input obligatorio ausente o vacío no puede producir `PASS`.
6. Estados y códigos de salida deben ser coherentes.
7. Producción, edición y auditoría final permanecen separadas.
8. Evidencia insuficiente bloquea; no se finge acceso a fuentes u obras.
9. Un artefacto aprobado no se sobrescribe silenciosamente.
10. Un cambio posterior invalida las aprobaciones y gates dependientes.
11. `EDITORIAL_SCRIPT_APPROVED`, `YOUTUBE_PRODUCTION_READY`, `YOUTUBE_READY` y `PUBLISHED` son estados distintos.
12. Ningún componente garantiza monetización, copyright seguro ni rendimiento.
13. NotebookLM y cualquier proveedor externo son opcionales, no el runtime obligatorio.
14. No se crean agentes, skills, scripts o documentos si una pieza más simple basta.
15. El plan no se modifica silenciosamente durante la implementación.

## 5. Estados y códigos canónicos

```text
GATES: PASS | WARN | FAIL | BLOCKED
EXIT:  PASS=0 | WARN=0 | FAIL=1 | BLOCKED=2 | ERROR=3
MISIONES: PLANNED | IN_PROGRESS | BLOCKED | READY_FOR_AUDIT | PASS | SUPERSEDED
```

Distinciones de producto:

```text
EDITORIAL_SCRIPT_APPROVED
→ guion aprobado; no autoriza producción ni publicación

YOUTUBE_PRODUCTION_READY
→ paquete exacto aprobado para producción; no existe todavía pieza audiovisual final aprobada

YOUTUBE_READY
→ pieza audiovisual final, miniatura y metadatos definitivos auditados; no significa publicado

PUBLISHED
→ versión efectivamente publicada y registrada
```

## 6. Dependencias

```text
B0
 └── B1
      ├── B2
      └── B3
           └── B4
                └── B5
                     └── B5.5
                          └── B6
                               └── B7
                                    └── B7.5
                                         └── B8
                                              └── B8.5
                                                   └── B9
                                                        └── B9.5
                                                             └── B10
```

## 7. Tablero de bloques

| Bloque | Nombre | Dependencia | Estado | Especificación operativa |
|---|---|---|---|---|
| B0 | Gobernanza, baseline y benchmarks editoriales | Ninguna | `PASS` | [B0_gobernanza_baseline_benchmarks.md](plan_001/B0_gobernanza_baseline_benchmarks.md) |
| B1 | Contratos, schemas, estados y versionado | B0 | `PASS` (auditoría aprobada, 29/29 tests) | [B1_contratos_schemas_estados_versionado.md](plan_001/B1_contratos_schemas_estados_versionado.md) |
| B2 | Reparación del arnés y gates críticos | B1 | `PASS` | [B2_reparacion_harness_gates.md](plan_001/B2_reparacion_harness_gates.md) |
| B3 | Perfil editorial y frontera del canal | B1–B2 | `BLOCKED` (B3-I3 `COMPLETED`, preflight `PASS`; B3-I4 bloqueado por falta de muestra principal real) | [B3_perfil_editorial_frontera_canal.md](plan_001/B3_perfil_editorial_frontera_canal.md) |
| B4 | Responsabilidades, skills, prompts y portabilidad | B3 | `PLANNED` | [B4_responsabilidades_skills_portabilidad.md](plan_001/B4_responsabilidades_skills_portabilidad.md) |
| B5 | Profesionalización del diseño editorial | B3–B4 | `PLANNED` | [B5_diseno_editorial.md](plan_001/B5_diseno_editorial.md) |
| B5.5 | Prototipo editorial controlado | B5 | `PLANNED` | [B5_5_prototipo_editorial.md](plan_001/B5_5_prototipo_editorial.md) |
| B6 | Redacción, ensamblaje, edición y verificación | B5.5 | `PLANNED` | [B6_redaccion_edicion_verificacion.md](plan_001/B6_redaccion_edicion_verificacion.md) |
| B7 | Auditoría independiente, correcciones y aprobación editorial | B6 | `PLANNED` | [B7_auditoria_aprobacion_editorial.md](plan_001/B7_auditoria_aprobacion_editorial.md) |
| B7.5 | Adaptación profesional a YouTube | B7 | `PLANNED` | [B7_5_adaptacion_youtube.md](plan_001/B7_5_adaptacion_youtube.md) |
| B8 | Plataforma, monetización, copyright y paquete para producción | B7.5 | `PLANNED` | [B8_plataforma_derechos_paquete.md](plan_001/B8_plataforma_derechos_paquete.md) |
| B8.5 | Aprobación para producción y cierre YOUTUBE_PRODUCTION_READY | B8 | `PLANNED` | [B8_5_aprobacion_youtube_production_ready.md](plan_001/B8_5_aprobacion_youtube_production_ready.md) |
| B9 | Validación con tres episodios completos | B2–B8.5 | `PLANNED` | [B9_validacion_tres_episodios.md](plan_001/B9_validacion_tres_episodios.md) |
| B9.5 | Registro publicado y aprendizaje controlado | B9 | `PLANNED` | [B9_5_aprendizaje_controlado.md](plan_001/B9_5_aprendizaje_controlado.md) |
| B10 | Lean/5S, portabilidad, documentación y cierre | B9.5 | `PLANNED` | [B10_lean_portabilidad_cierre.md](plan_001/B10_lean_portabilidad_cierre.md) |

## 8. Evidencia prevista

```text
reports/implementation/plan_001/<BLOQUE>/
```

Cada misión debe registrar, cuando aplique:

- archivos leídos, modificados y creados;
- comandos y pruebas ejecutadas;
- códigos de salida;
- estado de Git;
- resumen de diff;
- rutas de evidencia;
- riesgos y bloqueos;
- autoauditoría;
- estado `READY_FOR_EXTERNAL_AUDIT`.

## 9. Control de cambios

Una modificación del plan rector debe:

1. registrar versión, motivo, impacto y autoridad;
2. identificar bloques afectados;
3. actualizar este control cuando cambien estado o dependencias;
4. actualizar las proyecciones operativas afectadas;
5. validar que no aparezcan requisitos nuevos fuera del plan rector.

## 10. Próxima decisión

```text
NEXT_ALLOWED_ACTION: COMPLETE_B3-I4_VALIDATION
B3-I4_PREFLIGHT_IMPLEMENTATION: COMPLETED
B3-I4_PREFLIGHT_EXTERNAL_AUDIT: PASS
B3-I4_FUNCTIONAL_BLOCKER: REMOVED
B3_IMPLEMENTATION_STATUS: IN_PROGRESS
B4_AUTHORIZED: NO
```

B3-I4 continúa con evidencia `SPECIFICATION_BASED`; una muestra auténtica futura es opcional. B4 no está autorizado.
