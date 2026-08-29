# PLAN-001 / B3 - Perfil editorial y frontera del canal

**Plan rector:** `plans/001_reestructuracion_motor_agentico_editorial_y_harness.md`
**Control operativo:** `plans/001_CONTROL_OPERATIVO.md`
**Especificación funcional canónica:** `docs/specifications/B3_editorial_profile_functional_specification.md`

## Estado operativo

```text
ACTIVE_EDITORIAL_PROFILE: mas_alla_del_guion@1.2.2
PROFILE_1_2_2_STATUS: ACTIVE
PROFILE_1_2_2_ACTIVE: true
PROFILE_1_2_2_CHECKSUM: 2c373b88860a2d17e3f625adfac267a173b5f7f586a6c87bed2c14c0d254cd2b
VOICE_CORPUS_STATE: AUTHENTIC_CORPUS_PARTIAL
B3_IMPLEMENTATION_STATUS: COMPLETED
B3_TECHNICAL_VALIDATION_STATUS: PASS
B3_FUNCTIONAL_APPROVAL_STATUS: PASS
B3_FINAL_CLOSURE_STATUS: PASS
B3_I4_EXECUTION: COMPLETED
B3_I4_AUTHORIZATION: COMPLETED
REAL_PROFILE_ACTIVATION: PASS
NEXT_ALLOWED_ACTION: PREPARE_R6_B
```

## Alcance

B3 materializa la especificación funcional canónica en un perfil versionado y trazable. La validación técnica no sustituye la aprobación funcional, y ningún consumidor puede seleccionar automáticamente una versión o reconstruir identidad desde fuentes históricas.

La versión activa es 1.2.2 y su checksum coincide con las aprobaciones funcional y técnica registradas. Conserva el contenido funcional vigente y sanea el lineage para depender únicamente de la especificación canónica. El corpus de voz es `AUTHENTIC_CORPUS_PARTIAL`; esta situación limita la representatividad global y no autoriza uso productivo.

## Evidencia canónica

- `config/editorial_profile_registry.json`
- `profiles/editorial/mas_alla_del_guion/1.2.2/functional_approval.json`
- `profiles/editorial/mas_alla_del_guion/1.2.2/technical_validation.json`
- `config/active_editorial_profile.json`
- `profiles/voice/corpus_manifest.json`

Las fuentes históricas son evidencia de migración y no autoridad operativa. La preparación de R6-B no modifica el perfil editorial activo.
