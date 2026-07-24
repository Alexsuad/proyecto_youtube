# Skill — Investigación por cobertura

## Objetivo
Crear un `ResearchPack` trazable y suficiente para evaluar evidencia y formular una tesis provisional.

## Entradas
- `<EP_PATH>/episode_brief.json`;
- fuentes y materiales accesibles;
- políticas de fuentes del brief.

## Procedimiento
1. Investigar por cobertura, no por una cantidad fija de URLs u obras.
2. Cubrir explícitamente pregunta, conflicto, hipótesis inicial, fenómeno, material narrativo, claims críticos y perspectivas alternativas; cada dimensión se declara cubierta, parcial, pendiente o no verificable con decisión de reducción o bloqueo.
3. Separar `NARRATIVE_EVIDENCE` (escena, pasaje, capítulo u otro elemento del medio) de `EXTERNAL_REALITY_EVIDENCE` (estudio, documento, dato, registro o análisis experto).
4. Intentar confirmar, matizar o refutar la hipótesis inicial. En investigación profunda o crítica registrar rival, contradicción o justificación trazable de su ausencia.
5. Registrar por entrada las fuentes, el localizador y el nivel de confianza.
6. Declarar limitaciones y accesos indirectos. No fingir visionado ni acceso directo.
5. Escribir y validar `<EP_PATH>/research_pack.json`.
6. Preparar `<EP_PATH>/source_access_and_evidence_report.json` para el gate canónico.

## Salidas
- `<EP_PATH>/research_pack.json`;
- `<EP_PATH>/source_access_and_evidence_report.json`.

## Regla
Tres fuentes excelentes pueden ser suficientes. Ocho fuentes débiles no producen `PASS` por volumen.
