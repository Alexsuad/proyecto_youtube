# PLAN-001 / B3 - Perfil editorial y frontera del canal

**Plan rector:** `plans/001_reestructuracion_motor_agentico_editorial_y_harness.md`
**Control operativo:** `plans/001_CONTROL_OPERATIVO.md`
**Especificación funcional canónica:** `docs/specifications/B3_editorial_profile_functional_specification.md`

## Estado operativo

```text
ACTIVE_EDITORIAL_PROFILE: mas_alla_del_guion@1.2.1
PROFILE_1_1_0_STATUS: INVALID_APPROVAL_CHAIN
PROFILE_1_1_0_ACTIVE: false
PROFILE_1_2_0_STATUS: FUNCTIONAL_REVIEW_BLOCKED
PROFILE_1_2_0_ACTIVE: false
PROFILE_1_2_0_CHECKSUM: b1029e85289c51d4585c555ed20566dfd6f1f6db30b875f989fc23bf46fc5977
PROFILE_1_2_1_STATUS: ACTIVE
PROFILE_1_2_1_ACTIVE: true
PROFILE_1_2_1_CHECKSUM: d0355ea43f1d46f6ec94499bd81ae2f99c48f11e4402d1604c634abde70d48f1
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

La versión 1.2.0 permanece inactiva como antecedente sustituido. La versión activa es 1.2.1 y su checksum coincide con las aprobaciones funcional y técnica registradas. El corpus de voz es `AUTHENTIC_CORPUS_PARTIAL`; esta situación limita la representatividad global, pero no invalida la activación ya aprobada.

## Evidencia canónica

- `config/editorial_profile_registry.json`
- `profiles/editorial/mas_alla_del_guion/1.2.1/functional_approval.json`
- `profiles/editorial/mas_alla_del_guion/1.2.1/technical_validation.json`
- `config/active_editorial_profile.json`
- `profiles/voice/corpus_manifest.json`

Las fuentes históricas son evidencia de migración y no autoridad operativa. La preparación de R6-B no modifica el perfil editorial activo.
