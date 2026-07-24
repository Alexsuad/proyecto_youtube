# Skill — Tesis provisional y refinada

## Objetivo
Construir un `ThesisArtifact` trazable sin confundir la hipótesis inicial con la tesis refinada.

## Modo B5-I1: THESIS_PROVISIONAL
Entradas obligatorias:
- `episode_brief.json`;
- `research_pack.json`;
- `source_access_and_evidence_report.json`;
- gate de evidencia en `PASS` o `WARN`.

Debe reconstruirse tras investigar: premisas vinculadas a hallazgos concretos, evidencia que tensiona, explicaciones alternativas, supuestos, condiciones de revisión, preguntas abiertas y restricciones heredadas. Cada premisa mantiene la cadena hallazgo → fuente → evidencia admitida; no basta una referencia amplia a una fuente. La salida es `<EP_PATH>/thesis_provisional.json`.

La tesis será validada por `thesis_provisional_gate.py` tras su creación. Solo PASS o WARN permiten continuar a B5-I2.

## Modo THESIS_REFINED
El modo refinado estuvo bloqueado hasta B5-I2. En B5-I2 produce `RefinedThesis` desde análisis narrativo, curación, evidencia y tesis provisional. Debe declarar qué confirmó, cambió y descartó, su matiz, razón de refinamiento y restricciones heredadas; si conserva la misma formulación, justifica por qué sigue siendo defendible. No crea outline ni apertura.

## Bloqueos
- evidencia en `FAIL` o `BLOCKED`;
- referencias de fuente ausentes;
- intento de marcar la tesis como refinada antes de B5-I2.
