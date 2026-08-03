# PLAN-001 — Índice operativo por bloques

**Plan rector:** [`../001_reestructuracion_motor_agentico_editorial_y_harness.md`](../001_reestructuracion_motor_agentico_editorial_y_harness.md)  
**Control operativo:** [`../001_CONTROL_OPERATIVO.md`](../001_CONTROL_OPERATIVO.md)  
**Versión:** `1.4`
PLAN_001_EXECUTION: TEMPORARILY_PAUSED_BY_RECOVERY
CURRENT_RECOVERY_PLAN: PLAN_003
CURRENT_RECOVERY_PHASE: R6_B_POST_DIAGNOSTIC_RECONCILIATION_CLOSED
B5_5_M2: NEXT_RECOVERY_ACTION_UNDER_PLAN_003
B5_5_M2_DEFINED_AS_NEXT_ACTION: YES
B5_5_M2_OWNER_AUTHORIZATION: PENDING
B5_5_M2_STARTED: NO
IMPLEMENTATION_AUTHORIZED: NO_PENDING_NEXT_MISSION
current_mission: NONE_PENDING_B5_PRE_M2_AUTHORIZATION
NEXT_ALLOWED_ACTION: B5_PRE_M2_TECHNICAL_OPERATIONAL_CLOSURE
R6_B_0_EXTERNAL_AUDIT: PASS

## 1A. Prioridad y etapas

La fuente canónica es el Plan 001 principal. Tras R1 del Plan 003, el Plan 001 conserva autoridad como plan rector del producto, pero su continuación de implementación permanece temporalmente pausada hasta una misión posterior autorizada. B5-I2 sigue siendo el incremento pendiente; B5-I3 no está autorizado. B7.5, B8 y B8.5 se conservan como Etapa 2 diferida, no como continuación automática. Audio pertenece a un repositorio externo futuro y Video queda fuera del repositorio.

## 1. Propósito

Esta carpeta reduce el contexto que deben cargar los agentes operativos. Cada archivo contiene únicamente la especificación derivada de un bloque del Plan 001.

La jerarquía es:

```text
Plan rector completo
→ Control operativo vigente
→ Archivo del bloque activo
→ Misión técnica autorizada
→ Archivos reales afectados
```

Los archivos de esta carpeta:

- no sustituyen el plan rector;
- no pueden ampliar su alcance;
- no autorizan por sí mismos una implementación;
- no deben editarse sin comprobar si el plan rector también requiere cambio;
- deben mantenerse sincronizados cuando cambie la parte correspondiente del plan rector.

## 2. Política de lectura

### Leer siempre

1. `AGENTS.md`, cuando exista.
2. docs/ALCANCE_Y_COORDINACION_EQUIPOS.md.
3. `plans/001_CONTROL_OPERATIVO.md`.
4. El archivo del bloque activo.
5. La misión concreta.
6. Solo los archivos expresamente indicados o necesarios para ejecutar esa misión.

### No leer por defecto

- el Plan 001 completo;
- bloques no activos;
- todo `workspace/`;
- todos los reportes históricos;
- todo `output/`;
- fuentes de Producto no vinculadas a la misión.

### Consultar el plan rector completo solo cuando

- exista una contradicción;
- falte una autoridad;
- se proponga cambiar alcance, dependencias o estados;
- el archivo del bloque remita a una sección concreta;
- una corrección pueda afectar a más de un bloque.

## 3. Índice de bloques

| Bloque | Archivo | Dependencia | Estado | Gate resumido |
|---|---|---|---|---|
| `B0` | [B0_gobernanza_baseline_benchmarks.md](B0_gobernanza_baseline_benchmarks.md) | Ninguna | `OPEN` | EVIDENCE_REVIEW_REQUIRED |
| `B1` | [B1_contratos_schemas_estados_versionado.md](B1_contratos_schemas_estados_versionado.md) | B0 | `PASS` | Contratos canónicos aprobados |
| `B2` | [B2_reparacion_harness_gates.md](B2_reparacion_harness_gates.md) | B1 | `PASS` | Cero falsos PASS conocidos |
| `B3` | [B3_perfil_editorial_frontera_canal.md](B3_perfil_editorial_frontera_canal.md) | B1–B2 | `PASS` | PROFILE_1_2_1_ACTIVE |
| `B4` | [B4_responsabilidades_skills_portabilidad.md](B4_responsabilidades_skills_portabilidad.md) | B3 | `OPEN` | CONTRACTUAL_FOUNDATION_PASS / REAL_EXECUTION_NOT_DEMONSTRATED |
| `B5` | [B5_diseno_editorial.md](B5_diseno_editorial.md) | B3–B4 | `IN_PROGRESS` | B5-I1_FUNCTIONAL_CONFIRMATION_PENDING / B5-I2_OPEN / B5-I3 `NOT_AUTHORIZED` |
| `B5_PRE` | [B5_PRE_SCRIPT_FOUNDATION.md](B5_PRE_SCRIPT_FOUNDATION.md) | B5 | `FUNCTIONAL_FOUNDATION` | Planeación previa al guion: pertenencia, investigación, 5–8 candidatas, 3–5 finales, tesis, promesa |
| `B5.5` | [B5_5_prototipo_editorial.md](B5_5_prototipo_editorial.md) | B5 | `PLANNED` | Mejora editorial temprana demostrada |
| `B6` | [B6_redaccion_edicion_verificacion.md](B6_redaccion_edicion_verificacion.md) | B5.5 | `PLANNED` | Candidato final coherente y trazable |
| `B7` | [B7_auditoria_aprobacion_editorial.md](B7_auditoria_aprobacion_editorial.md) | B6 | `PLANNED` | Guion aprobado editorialmente |
| `B7.5` | [B7_5_adaptacion_youtube.md](B7_5_adaptacion_youtube.md) | B7 | `DEFERRED_NOT_AUTHORIZED` | Adaptación y packaging futuros |
| `B8` | [B8_plataforma_derechos_paquete.md](B8_plataforma_derechos_paquete.md) | B7.5 | `DEFERRED_NOT_AUTHORIZED` | Componentes de texto pueden evaluarse en Etapa 1; plataforma y distribución son futuras |
| `B8.5` | [B8_5_aprobacion_youtube_production_ready.md](B8_5_aprobacion_youtube_production_ready.md) | B8 | `DEFERRED_NOT_AUTHORIZED` | Producción futura |
| `B9` | [B9_validacion_tres_episodios.md](B9_validacion_tres_episodios.md) | B7 / `EDITORIAL_SCRIPT_APPROVED` | `PLANNED` | Validación del núcleo profesional de Guion |
| `B9.5` | [B9_5_aprendizaje_controlado.md](B9_5_aprendizaje_controlado.md) | B9 | `PLANNED` | Aprendizaje editorial; distribución diferida |
| `B10` | [B10_lean_portabilidad_cierre.md](B10_lean_portabilidad_cierre.md) | B9 + aprendizaje editorial B9.5 | `PLANNED` | Cierre de Etapa 1 y portabilidad |

## 4. Versiones derivadas

La versión derivada de cada bloque indica la última versión del plan que modificó materialmente su contenido. Un bloque puede conservar v1.3 si v1.4 no lo afectó.

## 5. Regla de sincronización

Cuando cambie el Plan 001:

1. registrar la modificación en el control de cambios del plan rector;
2. identificar qué bloques quedan afectados;
3. actualizar únicamente sus proyecciones operativas;
4. actualizar `../001_CONTROL_OPERATIVO.md` si cambian estado, dependencia o siguiente acción;
5. comprobar que ningún archivo operativo introduce requisitos nuevos;
6. registrar evidencia de sincronización.

Una modificación aislada de un archivo de bloque no cambia el plan rector.

## 6. Estado actual

```text
PLAN_STATUS: IN_PROGRESS
PLAN_001_ROLE: PRODUCT_PLAN_RECTOR
PLAN_001_EXECUTION: TEMPORARILY_PAUSED_BY_RECOVERY
CURRENT_RECOVERY_PLAN: PLAN_003
CURRENT_RECOVERY_PHASE: R6_B_POST_DIAGNOSTIC_RECONCILIATION_CLOSED
B5_5_M2: NEXT_RECOVERY_ACTION_UNDER_PLAN_003
B5_5_M2_DEFINED_AS_NEXT_ACTION: YES
B5_5_M2_OWNER_AUTHORIZATION: PENDING
B5_5_M2_STARTED: NO
IMPLEMENTATION_AUTHORIZED: NO_PENDING_NEXT_MISSION
current_mission: NONE_PENDING_B5_PRE_M2_AUTHORIZATION
PLAN_001_SUSPENDED_AT_BLOCK: B5-I2
PLAN_001_SUSPENDED_AT_INCREMENT: B5-I2
CURRENT_ACTIVE_PLAN: PLAN_003
CURRENT_ACTIVE_PHASE: R6_B_POST_DIAGNOSTIC_RECONCILIATION_CLOSED
B4_I1_STATUS: PASS
B4_I1_AUDIT: PASS
B4_I2_STATUS: PASS
B4_I2_AUDIT: PASS
B5_STATUS: IN_PROGRESS
B5_I1_STATUS: OPEN
B5_I2_IMPLEMENTATION: COMPLETED
B5_I2_TECHNICAL_CORRECTION: PASS_WITH_RESIDUAL_RISK
B5_I2_REAL_SEMANTIC_AUDIT: NOT_DEMONSTRATED
B5_I2_SCRIPT_PRODUCT_FUNCTIONAL_REAUDIT: PENDING
B5_I2_FINAL_STATUS: OPEN
B5_I3: NOT_AUTHORIZED
B5_PRE_SCRIPT_FOUNDATION: B5_PRE_SCRIPT_FOUNDATION.md
B5_5_CANONICAL_FOUNDATION: PASS
B5_5_M1_STATUS: PASS
B5_5_STATUS: FUNCTIONAL_FOUNDATION
TECHNICAL_SANITATION: NOT_STARTED
B5_5_M2_STARTED: NO
REAL_EXECUTION: NOT_DEMONSTRATED
STAGE_2_YOUTUBE_DISTRIBUTION: DEFERRED_NOT_AUTHORIZED
AUDIO_INTEGRATION: EXTERNAL_REPOSITORY_FUTURE_CONTRACT
VIDEO_PRODUCTION: OUT_OF_REPOSITORY_SCOPE
PLAN_002_DOCUMENT_STATUS: SUPERSEDED_BY_APPROVED_ARCHITECTURE
PLAN_002_OPERATIONAL_AUTHORITY: NOT_GRANTED
PLAN_002_AGENT_ARCHITECTURE: APPROVED_REPLACEMENT_MODEL
PLAN_002_FINAL_DECISION: SUPERSEDED_BY_APPROVED_ARCHITECTURE
NEXT_ALLOWED_ACTION: B5_PRE_M2_TECHNICAL_OPERATIONAL_CLOSURE
R6_B_0_EXTERNAL_AUDIT: PASS
```
