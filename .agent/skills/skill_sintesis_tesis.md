# Skill — Tesis provisional y refinada

## Objetivo
Construir un `ThesisArtifact` trazable sin confundir la hipótesis inicial con la tesis refinada.

## Modo B5-I1: THESIS_PROVISIONAL
Entradas obligatorias:
- `episode_brief.json`;
- `research_pack.json`;
- `source_access_and_evidence_report.json`;
- gate de evidencia en `PASS` o `WARN`.

Debe incluir statement, razonamiento inicial, objeción prevista, riesgo de simplificación, preguntas abiertas, referencias a fuentes y versión. La salida es `<EP_PATH>/thesis_provisional.json`.

La tesis será validada por `thesis_provisional_gate.py` tras su creación. Solo PASS o WARN permiten continuar a B5-I2.

## Modo THESIS_REFINED
Queda bloqueado hasta B5-I2. No puede ejecutarse ni simularse en B5-I1.

## Bloqueos
- evidencia en `FAIL` o `BLOCKED`;
- referencias de fuente ausentes;
- intento de marcar la tesis como refinada antes de B5-I2.
