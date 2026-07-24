# Skill — Análisis narrativo y humano B5-I2
Objetivo: producir `NarrativeHumanAnalysis` con lectura específica de deseos, miedos, creencias, contradicciones, decisiones, causas, costes, transformación, entorno, poder, instituciones, historia, cultura y sociedad.

> **Rol ejecutor actual:** Antigravity (en el futuro puede ser un agente Analista con modelo especializado en análisis de texto — ej: Claude 3.5 Sonnet)

---

## Entrada mínima
- `<EP_PATH>/02_curation_obras.md`

---

## Pasos
1) Analizar según el material y la pregunta del episodio, sin imponer una lista fija.
2) Producir un `NarrativeHumanAnalysis` por cada material que pueda quedar `SELECTED`; un material sin análisis solo puede quedar explícitamente `EXCLUDED`.
3) Separar hecho, interpretación, hipótesis y contraargumento; cada hallazgo debe enlazar evidencia narrativa concreta y fuente existente.
4) Propagar IDs de restricciones B5-I1, registrar interpretación rival y límites —o justificar explícitamente que no aplican— y declarar qué demuestra y qué no permite concluir.

5) Conectar cada hallazgo con el tema y producir `<EP_PATH>/narrative_human_analysis.json`.

---

## Salida
- `<EP_PATH>/04_analisis_patrones.md`
