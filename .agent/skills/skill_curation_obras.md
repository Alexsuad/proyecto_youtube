# Skill — Curación de evidencia Research V2 y frontera narrativa B5-I2
Objetivo: producir una selección investigativa trazable sin convertir los rangos normales en cuotas ciegas. La curación de Research V2 no decide función narrativa, orden, progresión ni recorrido del espectador; esas decisiones pertenecen a `NARRATIVE_ARCHITECTURE` y solo pueden leer sus resultados.

## Modo RESEARCH_V2 (canónico)

El owner canónico es `RESEARCH_AND_CURATION`. La salida es evidencia de comparación y selección investigativa: contribución a claims, cobertura, complementariedad, redundancia, contraste, fidelidad, limitaciones, suficiencia, selección y exclusión. Este modo no produce `MaterialCuration`, no asigna `function`, `narrative_use`, `expected_order`, `sequence_rationale` ni `progression_map`, y no contiene Viewer Journey.

## Modo LEGACY_B5_I2 (compatibilidad histórica)

Cuando una ruta histórica lo exija, `MaterialCuration` puede conservarse como contrato legacy de propiedad narrativa B5-I2. Debe identificarse explícitamente como `LEGACY / NARRATIVE B5-I2`, `LEGACY_TRANSVERSAL_FIXTURE` o equivalente y nunca puede actuar como autoridad de Research V2 ni contaminar su contexto semántico.

## Rangos operativos y suficiencia

- El screening normal trabaja con 5–8 obras candidatas.
- La selección final normal contiene 3–5 obras sustantivas.
- Una excepción solo es válida si está declarada explícitamente, identifica su aprobación y conserva el impacto funcional y de alcance; no existe excepción implícita.
- La cantidad nunca sustituye la suficiencia, la evidencia narrativa, la diferenciación funcional, el contraste ni la progresión argumentativa.
- No se exige un mínimo universal de fuentes: se conserva la trazabilidad necesaria para la decisión concreta.

> **Rol ejecutor actual:** el runtime operativo (en el futuro puede ser un agente Curador especializado en análisis narrativo)

---

## Entrada mínima
- Consumir el `ResearchPack` profundo, `ClaimsLedger`, comparación post-deep y decisiones de suficiencia de Research V2. `narrative_human_analysis.json`, `MaterialCuration` histórica y `<EP_PATH>/01_research_bruto.md` se conservan únicamente como proyecciones legacy compatibles cuando existan; no son autoridad para afirmar evidencia ni para decidir la investigación.

---

## Pasos
1) Consumir el `ResearchPack` profundo de Research V2; si se recibe `<EP_PATH>/01_research_bruto.md`, tratarlo únicamente como proyección legacy compatible.
2) Evaluar evidencia, contribución a claims, perspectiva nueva, redundancia, coste de contexto, contradicción, límites y suficiencia.
3) Diferenciar selección preliminar y final, y justificar exclusiones; no seleccionar solo por afinidad temática. Una curación `FINAL` no conserva `CANDIDATE`.
4) Registrar la relación del conjunto, contribución única por material seleccionado y justificación de solapamientos evidenciales.
5) Registrar contraste, complemento o tensión evidencial sin convertirlos en orden narrativo, progresión de guion o función dramática.
6) Registrar toda restricción heredada, su impacto en selección/exclusión, materiales afectados, disclosures y claims que no pueden sostenerse.

7) En `RESEARCH_V2`, persistir la comparación/selección Research V2 y sus referencias canónicas. En `LEGACY_B5_I2`, conservar `<EP_PATH>/material_curation.json` como artefacto histórico de propiedad narrativa; `<EP_PATH>/02_curation_obras.md` es una proyección documental legacy compatible y no sustituye al contrato JSON.

---

## Salida
- En `RESEARCH_V2`: comparación y selección investigativa con evidencia y lineage.
- En `LEGACY_B5_I2`: `<EP_PATH>/material_curation.json` y, opcionalmente, `<EP_PATH>/02_curation_obras.md`; ambos quedan fuera del contexto semántico Research V2.
