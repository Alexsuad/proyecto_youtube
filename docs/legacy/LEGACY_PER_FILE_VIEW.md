# Vista per-file de documentación legacy (derivada)

> Documento generado de forma determinista por `src/scripts/check_material_decisions.py --render`.
> NO editar manualmente. La fuente canónica es `docs/legacy/material_decision_registry.json`;
> esta vista es una proyección derivada y no una segunda fuente de verdad.

## Decisiones materiales

| Id | Estado | Autoridad | Sujeto |
|---|---|---|---|
| MD-LEGACY-001 | VIGENTE | TECHNICAL_GOVERNANCE | workspace/* (documentación legacy material) |
| MD-LEGACY-002 | VIGENTE | TECHNICAL_GOVERNANCE | B3-M1 (matriz canónica de componentes por archivo) |
| MD-LEGACY-003 | SUSTITUIDA | TECHNICAL_GOVERNANCE | workspace/00_sistema_agentes_v1.md |
| MD-LEGACY-004 | SUSTITUIDA | TECHNICAL_GOVERNANCE | workspace/01..05c y workspace/07 (documentación editorial migrada o histórica) |
| MD-LEGACY-005 | SUSTITUIDA | TECHNICAL_GOVERNANCE | workspace/06_convencion_outputs_y_notebooklm_v1.md y contratos auxiliares de workspace/ |
| MD-LEGACY-006 | SUSTITUIDA | TECHNICAL_GOVERNANCE | workspace/policy/POLICY_DETECCION_PATRONES_Y_CLICHES_V2.md y templates/evento_template_v2.md (material editorial legacy omitido en el índice inicial) |

## Sucesión de decisiones

| Id | Sustituido por |
|---|---|
| MD-LEGACY-001 | — |
| MD-LEGACY-002 | — |
| MD-LEGACY-003 | MD-LEGACY-001 |
| MD-LEGACY-004 | MD-LEGACY-001 |
| MD-LEGACY-005 | MD-LEGACY-001 |
| MD-LEGACY-006 | MD-LEGACY-001 |

## Vista per-file

| Archivo | Estado | Disposición | Sucesor | Consumidor activo | Duplicación material | Ejecutable |
|---|---|---|---|---|---|---|
| workspace/00_sistema_agentes_v1.md | SUSTITUIDA | SUPERSEDED_NON_EXECUTABLE | plans/001_CONTROL_OPERATIVO.md | — | Gobernanza operativa y arquitectura del motor agéntico | no |
| workspace/01_canal_identidad.md | SUSTITUIDA | MIGRATION_SOURCE | config/editorial_profile_registry.json | — | Identidad del perfil editorial activo | no |
| workspace/02_reglas_editoriales.md | SUSTITUIDA | MIGRATION_SOURCE | .agent/rules/ | — | Reglas editoriales activas en .agent/rules/ y perfil | no |
| workspace/03_formato_longform.md | SUSTITUIDA | MIGRATION_SOURCE | policies/script_product/main_episode_format_policy.md | — | Política de formato de episodio principal | no |
| workspace/04_politica_spoilers.md | SUSTITUIDA | HISTORICAL_REFERENCE | — | — | Política de spoilers pendiente de integración en consumidores canónicos (prerrequisito B5-I3/B6/B7.5) | no |
| workspace/05_estilo_y_voz.md | SUSTITUIDA | MIGRATION_SOURCE | config/editorial_profile_registry.json | — | Voz editorial del perfil activo (voice_profile) | no |
| workspace/05c_voice_profile.md | SUSTITUIDA | HISTORICAL_REFERENCE | — | — | Observaciones de voz; no constituyen reglas (Misión 4 del PLAN 008) | no |
| workspace/06_convencion_outputs_y_notebooklm_v1.md | SUSTITUIDA | HISTORICAL_REFERENCE | .agent/rules/01_formato_outputs.md | — | Convención de outputs activa en .agent/rules/ | no |
| workspace/07_arquitectura_storage_repo_vs_vault_v1_2.md | SUSTITUIDA | HISTORICAL_REFERENCE | — | — | Arquitectura de almacenamiento; la ruta portable no depende de Vault | no |
| workspace/CHECKLIST_REVISION_COMPETENCIA.md | SUSTITUIDA | HISTORICAL_REFERENCE | — | — | Contrato auxiliar de operación humana | no |
| workspace/CONTRATO_NOTEBOOKLM.md | SUSTITUIDA | HISTORICAL_REFERENCE | — | — | Contrato auxiliar; NotebookLM no es gate universal | no |
| workspace/INDICE_EPISODIOS.md | SUSTITUIDA | HISTORICAL_REFERENCE | — | — | Índice auxiliar histórico | no |
| workspace/LISTA_DE_NO_COPIA.md | SUSTITUIDA | HISTORICAL_REFERENCE | — | — | Lista auxiliar de no copia | no |
| workspace/MAPA_DE_LENTES.md | SUSTITUIDA | HISTORICAL_REFERENCE | — | — | Mapa auxiliar histórico de lentes | no |
| reference/estilo_usuario/README.md | HISTORICA | HISTORICAL_REFERENCE | — | — | Referencia de voz histórica; metadata reconciliada y sin autoridad conductual | no |
| workspace/policy/POLICY_DETECCION_PATRONES_Y_CLICHES_V2.md | SUSTITUIDA | MIGRATION_SOURCE | policies/script_product/main_episode_format_policy.md | — | Reglas de patrones, clichés, ritmo, cierre y voz; aspectos de voz remiten al perfil activo y la política de spoilers a su integración en B5-I3/B6/B7.5 | no |
| templates/evento_template_v2.md | SUSTITUIDA | MIGRATION_SOURCE | policies/script_product/main_episode_format_policy.md | — | Estructura de evento legacy (re-hook, proporciones obra/análisis) sustituida por la política de formato vigente | no |
