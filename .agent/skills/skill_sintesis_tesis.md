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
El owner canónico es `RESEARCH_AND_CURATION`. `NARRATIVE_ARCHITECTURE` solo puede leer `RefinedThesis`; no puede reconstruirla, modificarla ni convertirla en outline.

El modo refinado produce `RefinedThesis` desde la evidencia consolidada de Research V2: `ClaimsLedger`, comparación post-deep, decisiones de suficiencia, `ResearchPack` profundo y tesis provisional. `NarrativeHumanAnalysis` y `MaterialCuration` son entradas históricas de compatibilidad, identificadas como `LEGACY / NARRATIVE B5-I2`, y no son autoridad de investigación ni fuente de decisiones de selección. Debe declarar qué confirmó, cambió y descartó, su matiz, razón de refinamiento y restricciones heredadas. Cada dimensión de refinamiento cita posición provisional, posición resultante, evidencia y razón. Si conserva la misma formulación, justifica qué hipótesis contrastó, qué evidencia la confirmó, qué alternativas descartó y por qué no debe reducirse, ampliarse o matizarse. No crea outline ni apertura.

## Bloqueos
- evidencia en `FAIL` o `BLOCKED`;
- referencias de fuente ausentes;
- intento de marcar la tesis como refinada antes de B5-I2.
