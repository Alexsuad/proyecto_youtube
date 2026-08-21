# R1_GATE — Revisión funcional de capacidades de investigación

**Fecha:** 2026-08-21
**Autoridad funcional:** `SCRIPT_PRODUCT`
**Baseline técnico:** `f9a3201bc778d0f2208eb6495442e52077892a32` (`feat(r1-gate): integrate canonical research provenance`)
**Tipo de evidencia:** decisión funcional para cierre de `R1_GATE` y habilitación controlada de R2.

## Alcance de la revisión

La revisión funcional cubre las capacidades técnicas de investigación integradas en R1-M1 a R1-M11 para una ejecución controlada de B5-I1 en R2. No ejecuta R2, no produce un episodio, no demuestra una vertical real y no autoriza uso productivo.

La revisión confirma la representación funcional de:

- investigación del fenómeno y de las obras;
- `WorkResearchDossier` y lifecycle de obras;
- provenance, transformaciones y trazabilidad de evidencia;
- claims, suficiencia por uso y contradicciones;
- `ResearchStopDecision`;
- memoria semántica y contribuciones especializadas;
- auditoría independiente y rutas de retorno/corrección.

## Decisiones funcionales verificadas

La revisión confirma como materializadas, sin reinterpretación, las tres decisiones definitivas:

- `SP-IR0-CRITICAL_WORK_DOUBT`;
- `SP-IR0-MULTILINGUAL_RESEARCH_THRESHOLD`;
- `SP-IR0-MATERIAL_CLAIM_THRESHOLD`.

## Decisión funcional recibida

```text
SCRIPT_PRODUCT_RESEARCH_REVIEW: PASS_FOR_TECHNICAL_CAPABILITIES
R1_GATE_FUNCTIONAL_DECISION: PASS
R2_CONTROLLED_B5_I1_TEST: AUTHORIZED_FROM_SCRIPT_PRODUCT_SCOPE

REAL_RESEARCH_VERTICAL: NOT_DEMONSTRATED
AUTHORIZED_FOR_PRODUCT_USE: NO
B5_I2_AUTHORIZED_BY_THIS_REVIEW: NO
B5_I3_AUTHORIZED_BY_THIS_REVIEW: NO
B5_5_AUTHORIZED_BY_THIS_REVIEW: NO
B6_AUTHORIZED_BY_THIS_REVIEW: NO
```

## Estado resultante

```text
R1_GATE: PASS
R1_EXECUTION: COMPLETED
R1_GATE_TECHNICAL_REVIEW: PASS
R1_GATE_FUNCTIONAL_DECISION: PASS
R2_CONTROLLED_EXECUTION: AUTHORIZED
R2_SCOPE: B5_I1_CONTROLLED_EXECUTION
REAL_RESEARCH_VERTICAL: NOT_DEMONSTRATED
REAL_PRE_SCRIPT_VERTICAL: NOT_DEMONSTRATED
AUTHORIZED_FOR_PRODUCT_USE: NO
```

La autorización se limita a la ejecución controlada de B5-I1 en R2. R2 todavía no se inicia: no se ejecuta episodio, selección de tema, investigación, brief ni producción. La decisión no autoriza B5-I2, B5-I3, B5.5, B6, producto, publicación ni demostración de una vertical real.

## Frontera de autoridad

Este informe registra la decisión funcional de `SCRIPT_PRODUCT`; no sustituye el control operativo, contratos, schemas ni gates ejecutables. La autorización de R2 no se interpreta como aprobación de uso productivo ni como evidencia de ejecución real.
