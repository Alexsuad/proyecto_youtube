# Skill — Curación por función narrativa B5-I2
Objetivo: producir `MaterialCuration` sin convertir los rangos normales en cuotas ciegas.

## Rangos operativos y suficiencia

- El screening normal trabaja con 5–8 obras candidatas.
- La selección final normal contiene 3–5 obras sustantivas.
- Una excepción solo es válida si está declarada explícitamente, identifica su aprobación y conserva el impacto funcional y de alcance; no existe excepción implícita.
- La cantidad nunca sustituye la suficiencia, la evidencia narrativa, la diferenciación funcional, el contraste ni la progresión argumentativa.
- No se exige un mínimo universal de fuentes: se conserva la trazabilidad necesaria para la decisión concreta.

> **Rol ejecutor actual:** el runtime operativo (en el futuro puede ser un agente Curador especializado en análisis narrativo)

---

## Entrada mínima
- Consumir el `ResearchPack` de B5-I1 y los `narrative_human_analysis.json` canónicos producidos tras la selección preliminar. La curación final solo puede ejecutarse después del análisis narrativo y comparativo; `<EP_PATH>/01_research_bruto.md` se conserva como proyección legacy compatible cuando exista.

---

## Pasos
1) Consumir el `ResearchPack` de B5-I1; si se recibe `<EP_PATH>/01_research_bruto.md`, tratarlo únicamente como proyección legacy compatible.
2) Evaluar función, contribución a tesis, perspectiva nueva, redundancia, coste de contexto, evidencia, contradicción y uso narrativo.
3) Diferenciar selección preliminar y final, y justificar exclusiones; no seleccionar solo por afinidad temática. Una curación `FINAL` no conserva `CANDIDATE`.
4) Registrar razón de secuencia, relación del conjunto, contribución única por material seleccionado y justificación de solapamientos funcionales.
5) Para `CURATION_CONTRAST_AND_PROGRESSION: SATISFIED`, citar para cada material su cambio de comprensión, evidencia, no sustituibilidad y relación de contraste, complemento o tensión con el conjunto. La razón de orden debe ser editorialmente concreta; no hay secuencia universal ni obligación de contradicción.
6) Registrar toda restricción heredada, su impacto en selección/exclusión/función, materiales afectados, disclosures y claims que no pueden sostenerse.

7) Crear `<EP_PATH>/material_curation.json` como artefacto canónico. `<EP_PATH>/02_curation_obras.md` es una salida documental compatible y no sustituye al contrato JSON.

---

## Salida
- `<EP_PATH>/material_curation.json` (salida canónica).
- `<EP_PATH>/02_curation_obras.md` (proyección documental legacy compatible y opcional; no sustituye al contrato JSON).
