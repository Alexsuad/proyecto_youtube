# Skill — Investigación por cobertura

## Objetivo
Crear un `ResearchPack` trazable y suficiente para evaluar evidencia y formular una tesis provisional.

## Entradas
- `<EP_PATH>/episode_brief.json`;
- fuentes y materiales accesibles;
- políticas de fuentes del brief.

## Procedimiento
1. Investigar por cobertura, no por una cantidad fija de URLs u obras.
2. Separar hechos, interpretaciones, hipótesis, contradicciones, perspectivas alternativas, evidencia de escenas, claims utilizables, claims no sostenibles y oportunidades narrativas.
3. Registrar por entrada las fuentes, el localizador y el nivel de confianza.
4. Declarar limitaciones y accesos indirectos. No fingir visionado ni acceso directo.
5. Escribir y validar `<EP_PATH>/research_pack.json`.
6. Preparar `<EP_PATH>/source_access_and_evidence_report.json` para el gate canónico.

## Salidas
- `<EP_PATH>/research_pack.json`;
- `<EP_PATH>/source_access_and_evidence_report.json`.

## Regla
Tres fuentes excelentes pueden ser suficientes. Ocho fuentes débiles no producen `PASS` por volumen.
