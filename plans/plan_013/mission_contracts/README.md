# PLAN013 mission contracts

Todos los archivos `PLAN013_M*.json` de esta carpeta son `DRAFT`, `NON-AUTHORIZING` y no contienen una `MissionAuthorization` efectiva. Su existencia no habilita ninguna misión.

La ejecución futura exige, como mínimo:

1. `CURRENT_RECOVERY_PLAN: PLAN013` en el control operativo;
2. `CURRENT_MISSION` y `CURRENT_MISSION_EXECUTION_BUNDLE` coincidentes;
3. autorización explícita del OWNER para la misión concreta;
4. checksum del contrato y alcance exacto verificados por el preflight;
5. preservación de las denylist y cambios preexistentes indicados.

| Misión | Contrato | Gate |
|---|---|---|
| M0 | `PLAN013_M0_ACTIVATION.json` | `PLAN013_M0_GATE` |
| M1 | `PLAN013_M1_RESEARCH_TRUTH_AND_BINDING.json` | `PLAN013_B1_GATE` |
| M2 | `PLAN013_M2_IDENTITY_LINEAGE.json` | `PLAN013_B2_GATE` |
| M3 | `PLAN013_M3_ACQUISITION_HANDOFF.json` | `PLAN013_B3_GATE` |
| M4 | `PLAN013_M4_SCRIPT_ROUTING.json` | `PLAN013_B3_GATE` |
| M5 | `PLAN013_M5_RUNTIME_CONTRACTS.json` | `PLAN013_B4_GATE` |
| M6 | `PLAN013_M6_THESIS_AND_AUDIT_CONTRACTS.json` | `PLAN013_B4_GATE` |
| M7 | `PLAN013_M7_SCRIPT_COORDINATOR.json` | `PLAN013_B4_GATE` |
| M8 | `PLAN013_M8_YOUTUBE_FINAL_REVIEW.json` | `PLAN013_B5_GATE` |
| M9 | `PLAN013_M9_CLOSURE_AND_CONVERGENCE.json` | `PLAN013_B6_GATE` |
| M10 | `PLAN013_M10_SYNTHETIC_E2E_AND_TECHNICAL_PACKAGE.json` | `PLAN013_B6_GATE` |

No contract authorizes BUILD, provider selection, IA REAL, product use, commit or push.
