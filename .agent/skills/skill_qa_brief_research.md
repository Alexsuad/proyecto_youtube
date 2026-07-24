# Skill — QA estructurado de brief e investigación

## Objetivo
Auditar `EpisodeBrief` y `ResearchPack` antes del gate de suficiencia de evidencia.

## Entradas
- `<EP_PATH>/episode_brief.json`;
- `<EP_PATH>/research_pack.json`;
- `config/active_editorial_profile.json`.

## Validación
1. Entradas ausentes o vacías: `BLOCKED`.
2. JSON o contrato inválido: `FAIL`.
3. El brief debe referenciar exactamente el perfil activo por ID, versión y checksum.
4. La investigación debe separar hechos, interpretaciones, evidencia narrativa y evidencia externa, y demostrar cobertura trazable del brief.
5. Una dimensión pendiente o no verificable exige reducción explícita de alcance o bloqueo; en profundidad crítica se exige rival, contradicción o justificación.
5. No contar números universales de URLs, ideas, preguntas u obras.
6. Limitaciones o claims no sostenibles declarados producen `WARN` cuando el contrato y la cobertura permiten continuar.

## Salida
`GateResult` canónico persistido por `src/scripts/qa_brief_research.py`.

## Auditoría semántica obligatoria
La suficiencia editorial no se decide por conteos ni por este QA determinista. Un auditor con IA produce `semantic_sufficiency_audit.json` sobre los checksums exactos de brief, investigación, reporte y tesis. Evalúa sustancia, relevancia, rival, claims y preparación real; el gate canónico solo comprueba lineage y decisión.
