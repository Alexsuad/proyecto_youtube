PLAN 013 — REMEDIACIÓN E2E POST-AUDITORÍA GENERAL

Versión del plan: 0.2.1
Estado: `IN_PROGRESS`
Tipo: plan de recuperación y remediación técnica
Autoridad de implementación: `PLAN013_EXECUTION_AUTHORIZED`
Alcance actual: `PLAN013_INTEGRATED_IMPLEMENTATION`
Baseline técnica de implementación: commit Git `000dea2234bf7275ebd0f6fd2d76dd6e62b4d476` en rama `master`; 00E/00F conservan la evidencia documental de auditoría.
Auditoría de origen: `00F_AUDITORIA_GENERAL_FINAL_2026-09-10`
Reconciliación funcional de origen: `00E_RECONCILIACION_PROD_R2_2026-09-10`

```text
PLAN013_CANONICAL_PATH: plans/plan_013/PLAN013_Remediación_E2E_post_auditoría_general.md
PLAN013_STATUS: IN_PROGRESS
PLAN013_OWNER_APPROVED: YES
PLAN013_INDEPENDENT_AUDIT_STATUS: PASS
PLAN013_M0_AUTHORIZED: YES
PLAN013_BUILD_AUTHORIZED: YES
PLAN013_EXECUTION_AUTHORIZED: YES
PLAN013_DOCUMENT_REVIEW_STATUS: PASS
PLAN013_OWNER_APPROVAL_SCOPE: PLAN013_INTEGRATED_IMPLEMENTATION
PLAN013_OWNER_APPROVAL: APPROVED
PLAN013_PACKAGE_REPRODUCIBILITY_STATUS: READY_FOR_INDEPENDENT_AUDIT
CURRENT_SCOPE: PLAN013_INTEGRATED_IMPLEMENTATION
PLAN013_M0_STATUS: CLOSED_OWNER_ACCEPTED
AUDIT_BASELINE_ARTIFACT: OPTIONAL_INFORMATIONAL_BACKUP_REFERENCE
IMPLEMENTATION_BASELINE_GIT_COMMIT: 000dea2234bf7275ebd0f6fd2d76dd6e62b4d476
IMPLEMENTATION_BASELINE_BRANCH: master
IMPLEMENTATION_BASELINE_WORKTREE: DIRTY_PREEXISTING_CHANGES_REGISTERED
CURRENT_RECOVERY_PLAN: PLAN013
CURRENT_RECOVERY_PHASE: PLAN013_IMPLEMENTATION
CURRENT_MISSION: PLAN013_INTEGRATED_EXECUTION
CURRENT_MISSION_EXECUTION_BUNDLE: plans/plan_013/PLAN013_Remediación_E2E_post_auditoría_general.md
EXTEND_01: SUSPENDED_BY_PLAN013_AND_PRESERVED
REAL_AI_EXECUTION: NO
PRODUCT_USE_AUTHORIZED: NO
```

0\. DECISIÓN DE DIRECCIÓN

Este plan convierte los 16 hallazgos funcionales R2 confirmados y las causas raíz sistémicas de la auditoría general en una secuencia única de implementación. La versión 0.2.1 fue revisada y auditada; PLAN013 está activado para su implementación integral. Se mantienen las protecciones del perfil activo, la prohibición de IA REAL y la prohibición de uso productivo.

No se crearán 16 misiones independientes. Los hallazgos se agrupan en seis bloques de remediación para corregir causas comunes, reutilizar componentes existentes y reducir retrabajo.

La remediación no reabre PLAN012. PLAN012 permanece cerrado como antecedente histórico y técnico.

El OWNER aprobó este plan, la auditoría independiente resultó PASS y la materialización de M0 ya fue completada en `plans/001_CONTROL_OPERATIVO.md`. Mientras PLAN013 esté activo, la preparación de la corrida REAL de EXTEND-01/M2 queda suspendida. Al cerrar PLAN013, el control deberá quedar preparado para solicitar la reanudación de EXTEND-01 en el punto exacto donde fue interrumpido, sin autorizarla automáticamente.

PLAN013 no ejecuta por sí mismo ninguna corrida REAL. Su resultado documental final es `READY_TO_REQUEST_EXTEND_01_RESUMPTION`. La corrida REAL posterior conserva autorización explícita separada del OWNER y no se habilita por el cierre de PLAN013.

### 0.1 Secuencia de autoridad y estados

El estado previo a M0 queda conservado en el checkpoint; el estado vivo actual ya refleja la activación de PLAN013:

```text
CURRENT_RECOVERY_PLAN: PLAN013
CURRENT_RECOVERY_PHASE: PLAN013_IMPLEMENTATION
CURRENT_MISSION: PLAN013_INTEGRATED_EXECUTION
NEXT_ALLOWED_ACTION: EXECUTE_PLAN013
REAL_AI_EXECUTION: NO
PRODUCT_USE_AUTHORIZED: NO
```

La secuencia obligatoria es:

```text
PLAN013 v0.1 — REJECTED_PRE_BUILD
→ package hardening documental
→ PLAN013 v0.2.1 — DRAFT_FOR_INDEPENDENT_AUDIT (completado)
→ PLAN013_INDEPENDENT_AUDIT_PASS (completado)
→ OWNER_APPROVAL_PLAN013 (completado)
→ OWNER_AUTHORIZATION_M0 (completado)
→ M0 — activación en el control operativo (completado)
→ PLAN013_INTEGRATED_EXECUTION (actual)
→ revisión técnica e independiente de cada misión
→ cierre técnico y funcional separado
→ PLAN013_OWNER_APPROVED_CLOSED
→ READY_TO_REQUEST_EXTEND_01_RESUMPTION
→ decisión separada del OWNER sobre EXTEND-01
```

La cadena de cierre de una misión es:

```text
MISSION_IMPLEMENTED
→ TECHNICAL_PASS
→ INDEPENDENT_REVIEW_PASS
→ FUNCTIONAL_CONFORMANCE_PASS cuando corresponda
→ OWNER_ACCEPTED
→ MISSION_CLOSED
```

`FUNCTIONAL_CONFORMANCE_PASS` no equivale a aprobación de producto, `EDITORIAL_SCRIPT_APPROVED` ni autorización de uso productivo.

### 0.2 Paquete mínimo para auditoría independiente

Antes de solicitar `PLAN013_INDEPENDENT_AUDIT_PASS`, el repositorio debe contener, dentro del alcance de `plans/plan_013/`, un paquete reproducible y no normativo:

- `plans/plan_013/findings_manifest.json` con los 16 findings.
- `plans/plan_013/audit_evidence/` con exportes legibles de la auditoría general y de la reconciliación R2.
- Hash SHA-256, origen, fecha, tipo y limitaciones de cada fuente.
- `plans/plan_013/mission_contracts/` con contratos draft completos y no autorizantes de las misiones PLAN013.
- Matriz de trazabilidad finding → RCA → misión → archivo → prueba → evidencia → disposición.

Los enlaces o identificadores de Google Drive se conservarán como provenance, pero no serán la única evidencia de la auditoría. Si una fuente no puede exportarse o su hash no puede verificarse, el paquete queda `BLOCKED_UNTIL_REPRODUCIBLE_EVIDENCE` y no puede pasar a auditoría independiente.

Cada entrada de `findings_manifest.json` debe contener como mínimo:

```text
finding_id
severity
source_artifact
source_locator
evidence_refs
critical_path
production_cause
escape_cause
functional_owner
technical_owner
remediation_mission
acceptance_criteria
residual_risk
disposition
```

El manifest debe separar explícitamente `audit_baseline` de `implementation_baseline`. `audit_baseline` identifica la fotografía sobre la que se produjeron los findings; `implementation_baseline` identifica el commit Git, rama y estado del worktree desde el que se iniciará la implementación. El estado del worktree debe enumerar cualquier cambio preexistente y sus checksums, sin atribuirlo a PLAN013.

La disposición informativa permitida es `RESOLVED`, `PARTIALLY_RESOLVED`, `NOT_RESOLVED`, `SUPERSEDED_BY_VERIFIED_FIX` o `DEFERRED_WITH_EVIDENCE`. Ninguna disposición parcial o negativa equivale por sí sola a PASS.

Mientras alguno de los artefactos anteriores no exista y no tenga hash verificable, el estado del paquete es `BLOCKED_UNTIL_ARTIFACTS_MATERIALIZED`; no se puede declarar `PLAN013_INDEPENDENT_AUDIT_PASS`, `PLAN013_TECHNICAL_PASS` ni autorizar M0.

### 0.3 Baseline protegida del perfil activo

La identidad activa del perfil editorial queda congelada como baseline de lectura:

```text
ACTIVE_PROFILE_ID: mas_alla_del_guion
ACTIVE_PROFILE_VERSION: 1.2.2
ACTIVE_PROFILE_CHECKSUM: 2c373b88860a2d17e3f625adfac267a173b5f7f586a6c87bed2c14c0d254cd2b
ACTIVE_PROFILE_STATUS: ACTIVE
FUNCTIONAL_APPROVAL: APPROVE
TECHNICAL_VALIDATION: PASS
```

`config/active_editorial_profile.json` y el artefacto activo son `NO_WRITE_BY_DEFAULT`. M2.1 puede corregir referencias derivadas y lineage incompatible sin cambiar el contenido ni el checksum activo. Si la corrección exige cambiar el perfil activo:

```text
STOP
→ PROFILE_CHANGE_REQUIRED
→ nueva validación técnica
→ nueva revisión funcional
→ aprobación explícita
→ activación de la nueva identidad y checksum
```

Nunca se hereda automáticamente la aprobación del checksum anterior.

### 0.4 Decisiones técnicas cerradas

PLAN013 v0.2.1 fija estas decisiones y no las deja abiertas al BUILD:

- `YOUTUBE_ADAPTATION` conserva la autoridad existente y se extiende con el contrato explícito `FINAL_SCRIPT_REVIEW`; no se crea un auditor YouTube paralelo.
- `FINAL_SCRIPT_REVIEW` consume el guion terminado y se liga a `episode_id`, `artifact_id`, `script_version` y `script_checksum`.
- `cerrar_episodio.py` conserva el entrypoint por compatibilidad, pero deja de ser autoridad de cierre y delega en una única operación software-owned.
- La operación única de cierre valida todas las autoridades finales y reconcilia los stores de forma idempotente.
- `api_base_env` es el nombre canónico de configuración OpenAI-compatible. `base_url_env` solo puede conservarse como alias transitorio si existe un consumidor real demostrado y con prueba de regresión.

1\. OBJETIVO

Eliminar los bloqueos que hoy impiden demostrar una ruta canónica, coherente y verificable desde la entrada humana hasta EDITORIAL\_SCRIPT\_APPROVED.

El objetivo técnico no es reescribir el proyecto. Es conseguir que las piezas ya diseñadas e implementadas formen un producto ejecutable con una única cadena de autoridad:

INPUT HUMANO
→ identidad y pertenencia
→ Research V2
→ evidencia utilizable
→ RESEARCH\_READY
→ arquitectura narrativa
→ WRITING
→ EDITOR
→ FINAL\_EDITORIAL\_AUDITOR
→ YOUTUBE\_ADAPTATION final sobre el guion
→ aprobación humana
→ cierre software-owned
→ estados persistidos convergentes

Al terminar, el sistema debe poder demostrar localmente ese recorrido con una ejecución sintética representativa. Solo después puede volver a intentarse la demostración REAL de EXTEND-01.

2\. PRINCIPIOS NO NEGOCIABLES

2.1 Reutilizar antes de crear

Aplicar SEARCH BEFORE CREATE y REUSE → EXTEND → CREATE.

No crear un segundo mecanismo de evidence truth, invalidación, cierre, lineage, review YouTube o ejecución de roles si ya existe una pieza utilizable que pueda extenderse.

2.2 Software conserva la autoridad determinista

IDs, versiones, checksums, bindings, provenance, estados, autorización, invalidación y cierre permanecen bajo autoridad del software.

La IA puede investigar, analizar, escribir o auditar semánticamente. No decide silenciosamente si una fuente existe, si una versión es la vigente, si un gate está satisfecho o si el episodio puede cerrarse.

2.3 Separación de responsabilidades

Productor ≠ auditor.
WRITING ≠ EDITOR ≠ FINAL\_EDITORIAL\_AUDITOR.
YOUTUBE\_ADAPTATION final debe ser independiente del productor del guion.
La aprobación humana ocurre después de las auditorías obligatorias.

2.4 Neutralidad de proveedor y agente

No introducir dependencias obligatorias con Codex, OpenCode, DeepSeek, OpenAI, Antigravity o un harness concreto.

Un proveedor o modelo usado en una prueba REAL puede registrarse como provenance de esa ejecución, pero no debe convertirse en autoridad del producto.

2.5 Fail-closed real

Cuando falte una entrada obligatoria, una ruta, un contexto requerido, una fuente recuperada, una identidad de artefacto o una auditoría necesaria, el sistema debe bloquear con una causa observable.

Nunca debe transformar ausencia, PENDING, NOT\_RECOVERED o NOT\_REVIEWED en evidencia positiva por conveniencia.

2.6 Validación proporcional

Cada misión ejecuta primero pruebas focales del cambio y de sus consumidores directos.

La suite completa no se repite por reflejo en cada modificación. Se reserva para gates de bloque y para el cierre integral cuando el riesgo lo justifique.

2.7 No rigidizar el producto editorial

No convertir referencias históricas como 144 WPM, 18–22 minutos, cantidades de rehooks, segundos o estructuras narrativas específicas en reglas universales de PASS/FAIL.

Los contratos deben exigir que las dimensiones relevantes sean evaluadas, no imponer una única forma creativa de resolverlas.

3\. ALCANCE

Incluido:

Corrección de verdad de evidencia y propósito Research.
Integridad de ResearchPlan al hacer binding.
Integridad de identidad y lineage de fuentes B3.
Aplicación determinista de territorios ACTIVE/EXCLUDED en Topic Belonging.
Conexión mínima de invalidación selectiva cuando existan dependencias reales.
Capacidad/contrato de adquisición externa necesario para los casos admitidos por Research V2.
Transferencia consultiva Research→Script con provenance.
Resolución de B5-I3 en capability routing.
Materialización técnica en runtime de WRITING, EDITOR y FINAL\_EDITORIAL\_AUDITOR usando roles existentes, sin activación productiva.
Continuidad contractual de RefinedThesis.
Refuerzo proporcional de ScriptBlockContract, EditorialEditReport y FinalEditorialAudit.
YOUTUBE\_ADAPTATION FINAL script-only sobre el guion exacto.
Scanner léxico como sensor, duración como telemetría y decisión contextual de autenticidad/repetición.
Resolución estricta de required\_context.
Coherencia de configuración OpenAI-compatible.
Autoridad de cierre única software-owned.
Convergencia de workflow\_state, episode\_state, episodes\_index y evidencias finales.
E2E sintético representativo desde input hasta cierre.
Gate para volver a EXTEND-01.

Fuera de alcance:

Reabrir PLAN012.
Rediseñar toda la arquitectura.
Crear nuevos dominios funcionales.
Crear nuevos agentes si los roles actuales bastan.
Packaging final, miniatura, SEO, Shorts, publicación o audiovisual.
Multi-provider completo, router automático de modelos o BYOK.
Optimización de tokens sin mediciones reales.
Base de datos, colas o infraestructura enterprise sin defecto demostrado.
Corrida REAL de Research V2 sin autorización posterior del OWNER.

4\. TRAZABILIDAD DE LOS 16 HALLAZGOS

La agrupación siguiente es una vista de navegación, no sustituye el `findings_manifest.json`. Cada finding debe conservar su severidad original, evidencia hashada, critical path, causa de producción, causa de escape, owner funcional y técnico, criterio de aceptación y disposición final.

PROD01-R2-F001 → Bloque 2 — Topic Belonging contra territorios del perfil.
PROD01-R2-F002 → Bloque 2 — identidad/checksum único de lineage B3.
PROD01-R2-F003 → Bloque 2 — demostrar conexión de invalidación selectiva.

PROD02-R2-F001 → Bloque 1 — binding de ResearchPlan sin pérdida.
PROD02-R2-F002 → Bloque 1 — verdad de evidencia y estados positivos.
PROD02-R2-F003 → Bloque 3 — adquisición externa o restricción explícita.
PROD02-R2-F004 → Bloque 1 — resolución canónica de intended\_use.
PROD02-R2-F005 → Bloque 3 — handoff consultivo Research→Script con provenance.

PROD03-R2-F001 → Bloques 3 y 4 — routing B5-I3 y grafo Writing→Editor→Final Audit.
PROD03-R2-F002 → Bloque 4 — binding inequívoco de RefinedThesis.
PROD03-R2-F003 → Bloque 4 — FinalEditorialAudit con garantías v2.1 evaluadas.
PROD03-R2-F004 → Bloque 4 — contratos de bloque/edición con evidencia suficiente.

PROD04-R2-F001 → Bloques 5 y 6 — review YouTube FINAL y consumo obligatorio por cierre.
PROD04-R2-F002 → Bloque 5 — scanner léxico convertido en sensor.
PROD04-R2-F003 → Bloque 5 — duración como envelope/telemetría episódica.
PROD04-R2-F004 → Bloque 5 — decisión contextual de autenticidad/repetición.

### 4.1 Regla de RCA doble

Para cada defecto material se debe documentar por separado:

- `production_cause`: por qué el sistema produjo o permitió el defecto.
- `escape_cause`: si un control interno aplicable debía detectarlo y por qué no lo detectó.

Si ningún control interno corresponde legítimamente, `escape_cause` debe clasificarse como `OUT_OF_SCOPE_BY_DESIGN` y justificarse. La corrección se aplica en la sede de la causa demostrada y la reauditoría debe revisar ambas causas.

5\. GRAFO DE DEPENDENCIAS

M0 ACTIVACIÓN DEL PLAN DE RECUPERACIÓN
↓
BLOQUE 1 — RESEARCH: VERDAD, PROPÓSITO E INTEGRIDAD
↓
BLOQUE 2 — IDENTIDAD Y LINEAGE
↓
BLOQUE 3 — ADQUISICIÓN Y FRONTERA RESEARCH→SCRIPT
↓
BLOQUE 4 — GRAFO PRODUCTIVO DE GUION Y CONTRATOS
↓
BLOQUE 5 — YOUTUBE FINAL SCRIPT-ONLY
↓
BLOQUE 6 — CIERRE, PREFLIGHT Y E2E
↓
OWNER REVIEW
↓
READY_TO_REQUEST_EXTEND_01_RESUMPTION

La ejecución se recomienda secuencial. No hay una necesidad actual de trabajo paralelo que justifique ramas o worktrees adicionales.

5.1 GRANULARIDAD OPERATIVA RECOMENDADA

Los identificadores M1.1, M1.2, etc. describen frentes técnicos y criterios que deben quedar resueltos; NO obligan a crear una misión independiente por cada subpunto.

Para la ejecución con un agente operativo, la agrupación recomendada es de 11 misiones máximas, siempre que la inspección real confirme que los cambios están suficientemente acoplados. La agrupación no autoriza ejecución: cada misión requiere un contrato cerrado y una autorización independiente.

Misión 0 — Activar PLAN013 y suspender temporalmente EXTEND-01 REAL.
Misión 1 — Bloque 1 completo: evidence truth \+ intended\_use \+ binding ResearchPlan.
Misión 2 — Bloque 2 completo: lineage B3 \+ Topic Belonging \+ demostración focal de invalidación.
Misión 3 — Adquisición externa neutral y estados de capacidad.
Misión 4 — Handoff Research→Script \+ route B5-I3.
Misión 5 — Runtime contracts y routing de WRITING/EDITOR/FINAL\_EDITORIAL\_AUDITOR.
Misión 6 — Continuidad de RefinedThesis \+ contratos de bloques/edición/auditoría.
Misión 7 — Coordinador sintético del tramo de guion.
Misión 8 — YouTubeAdaptationReview FINAL con política contextual, duración y autenticidad.
Misión 9 — required\_context \+ configuración OpenAI-compatible \+ autoridad de cierre/convergencia.
Misión 10 — E2E sintético integral \+ paquete de evidencia \+ `PLAN013_TECHNICAL_PASS`.

Una misión podrá dividirse únicamente si durante la ejecución aparece un riesgo real, un cambio de capa material o una condición de bloqueo. También podrá fusionarse con otra si el mismo cambio y las mismas pruebas demuestran ambas sin ampliar el riesgo.

La `INDEPENDENT_REMEDIATION_AUDIT` es un gate posterior a M10, no una actividad del ejecutor de M10. El auditor independiente revisa el paquete técnico, los 16 findings, las RCA y los critical paths antes de cualquier conformidad funcional o cierre OWNER. La revisión técnica o aceptación de la misión M10 no equivale a auditoría independiente ni cierra PLAN013.

Cada misión debe quedar materializada como paquete draft no autorizante con:

- objetivo y no objetivos;
- archivos permitidos y denylist explícita;
- capacidades, roles, rutas y operaciones permitidos;
- dependencias y estado previo requerido;
- pruebas focales, regresiones y evidencia esperada;
- stop conditions;
- política de commit y push;
- `MissionContract`, `MissionAuthorization`, `execution_preflight` y `MissionCompletionGate` aplicables;
- revisión independiente y cierre OWNER cuando corresponda.

Los contratos draft no pueden modificar el control operativo ni activar una capacidad. La autorización efectiva debe ligar `mission_id`, checksum del contrato, estado vivo y alcance exacto.

Ninguna misión M1–M10 puede ejecutarse únicamente porque exista su contrato draft. Antes de cada ejecución, `plans/001_CONTROL_OPERATIVO.md` debe registrar `CURRENT_RECOVERY_PLAN: PLAN013`, el `CURRENT_MISSION` concreto, el bundle de misión en `CURRENT_MISSION_EXECUTION_BUNDLE` y una `NEXT_ALLOWED_ACTION` compatible con la ejecución. El `MissionAuthorization` debe coincidir con esos valores, su checksum y su alcance; si falta cualquiera de ellos, la misión queda bloqueada.

Asignación mínima de responsabilidad:

| Misión | Owner funcional principal | Owner técnico | Revisión requerida |
|---|---|---|---|
| M0 | OWNER / `INFRASTRUCTURE_GOVERNANCE` | `INFRASTRUCTURE_GOVERNANCE` | OWNER review del cambio de estado |
| M1 | `SCRIPT_PRODUCT` | `INFRASTRUCTURE_GOVERNANCE` | revisión independiente técnica |
| M2 | `CHANNEL_INTELLIGENCE` | `INFRASTRUCTURE_GOVERNANCE` | revisión funcional de identidad si aplica |
| M3 | `SCRIPT_PRODUCT` / `YOUTUBE_ADAPTATION` según el contrato | `INFRASTRUCTURE_GOVERNANCE` | revisión independiente de capacidad |
| M4–M7 | `SCRIPT_PRODUCT` | `INFRASTRUCTURE_GOVERNANCE` | revisión técnica y funcional separadas |
| M8 | `YOUTUBE_ADAPTATION` | `INFRASTRUCTURE_GOVERNANCE` | revisión funcional de adaptación |
| M9–M10 | `INFRASTRUCTURE_GOVERNANCE` con owners de dominio | `INFRASTRUCTURE_GOVERNANCE` | revisión técnica de misión; sin auditoría independiente ni cierre de PLAN013 |

La tabla no transfiere autoridad: el owner funcional decide sobre su dominio y el owner técnico no puede autoaprobarlo.

### 5.2 Artefactos de protección y checkpoint

Los contratos de misión deben incluir una denylist hashada para preservar, como mínimo, estas sedes inmutables durante PLAN013:

- `config/active_editorial_profile.json`;
- `profiles/editorial/mas_alla_del_guion/1.2.2/editorial_profile.json`;
- `profiles/editorial/mas_alla_del_guion/1.2.2/profile_payload.json`;
- `profiles/editorial/mas_alla_del_guion/1.2.2/functional_approval.json`;
- `profiles/editorial/mas_alla_del_guion/1.2.2/technical_validation.json`;
- `profiles/voice/corpus_manifest.json`.

`config/editorial_profile_registry.json` es una superficie controladamente modificable solo en M2.1: la misión puede actualizar referencias derivadas de lineage, pero debe preservar el contenido, versión, checksum y estado del perfil activo. El cambio debe validarse mediante comparación estructural antes/después y no puede modificar el puntero activo.

`profiles/voice/corpus_manifest.json` permanece `DENYLIST_BY_DEFAULT`. Solo M2.1 puede solicitar una excepción temporal de allowlist si la reconciliación demuestra que el checksum incompatible reside allí. La excepción requiere justificación, checksum before, autorización específica, modificación mínima, checksum after, validación de lineage y confirmación de que no se alteró contenido editorial o corpus fuera de la referencia necesaria. Si cualquiera de esas condiciones falta, M2.1 queda bloqueada.

La denylist debe conservar checksum observado antes de cada misión que pueda consumir lineage o configuración editorial y debe fallar ante cualquier modificación no autorizada.

M0 debe crear `plans/plan_013/checkpoints/extend_01_pre_plan013.json` como registro no normativo del checkpoint anterior. Debe contener `CURRENT_MISSION`, `NEXT_ALLOWED_ACTION`, `CURRENT_RECOVERY_PLAN`, `live_state_sha256`, `CURRENT_MISSION_EXECUTION_BUNDLE`, fecha de captura, actor, motivo y `checkpoint_sha256`. El registro no sustituye `plans/001_CONTROL_OPERATIVO.md` ni autoriza reanudación.

`live_state_sha256` es SHA-256 de los bytes exactos en UTF-8 de `plans/001_CONTROL_OPERATIVO.md`, sin normalización de saltos de línea. `checkpoint_sha256` usa el algoritmo SHA-256 y se expresa como 64 caracteres hexadecimales en minúscula; se calcula sobre el objeto JSON completo excluyendo `checkpoint_sha256`, serializado en UTF-8, con claves ordenadas y separadores compactos. La verificación debe volver a calcular ambos hashes, validar el esquema y comparar `CURRENT_MISSION`, `NEXT_ALLOWED_ACTION`, `CURRENT_RECOVERY_PLAN` y `CURRENT_MISSION_EXECUTION_BUNDLE` contra el estado observado. Para restaurar o solicitar reanudación se debe verificar primero el checksum actual del control contra la evidencia; no existe restauración automática desde el archivo de checkpoint.

6\. M0 — ACTIVACIÓN SEGURA DEL PLAN

Estado:
M0 ya fue materializado en el control operativo; PLAN013 permanece activado para la implementación integral y bloquea temporalmente la corrida REAL pendiente de EXTEND-01.

Precondiciones obligatorias:
Auditoría independiente de PLAN013 v0.2.1 = PASS.
OWNER approval del plan = YES.
OWNER authorization de M0 = YES.
Evidencia reproducible y `findings_manifest.json` disponibles.

Cambios materializados en M0:
Usar únicamente `plans/plan_013/PLAN013_Remediación_E2E_post_auditoría_general.md`; no crear una segunda copia ni alias del plan.
Actualizar `plans/001_CONTROL_OPERATIVO.md` para reflejar PLAN013 como recovery plan activo.
Preservar PLAN012 como CLOSED.
Preservar EXTEND-01 y su progreso; cambiar únicamente su condición operativa a suspendida por remediación.
Mantener `REAL_AI_EXECUTION: NO` y `PRODUCT_USE_AUTHORIZED: NO`.

Estado vivo registrado al abrir M0:

```text
CURRENT_RECOVERY_PLAN: PLAN013
CURRENT_RECOVERY_PHASE: PLAN013_M0_ACTIVATION
CURRENT_MISSION: PLAN013_M0_ACTIVATION
CURRENT_MISSION_EXECUTION_BUNDLE: plans/plan_013/mission_contracts/PLAN013_M0_ACTIVATION.json
NEXT_ALLOWED_ACTION: OWNER_DECISION_PLAN013_M1_AUTHORIZATION
PLAN013_STATUS: IN_PROGRESS
EXTEND_01_STATUS: SUSPENDED_BY_PLAN013
REAL_AI_EXECUTION: NO
PRODUCT_USE_AUTHORIZED: NO
```

La captura del estado anterior debe conservar `CURRENT_MISSION: EXTEND_01_M2_REAL_E2E`, `NEXT_ALLOWED_ACTION: OWNER_REVIEW_B4_R4` y su checksum. Al cerrar PLAN013 no se restaura un estado aproximado: se solicita explícitamente la reanudación desde ese checkpoint.

Estado vivo actual después del cierre de M0:

```text
CURRENT_RECOVERY_PLAN: PLAN013
CURRENT_RECOVERY_PHASE: PLAN013_IMPLEMENTATION
CURRENT_MISSION: PLAN013_INTEGRATED_EXECUTION
CURRENT_MISSION_EXECUTION_BUNDLE: plans/plan_013/PLAN013_Remediación_E2E_post_auditoría_general.md
PLAN013_M0_STATUS: CLOSED_OWNER_ACCEPTED
NEXT_ALLOWED_ACTION: EXECUTE_PLAN013
EXTEND_01_STATUS: SUSPENDED_BY_PLAN013
REAL_AI_EXECUTION: NO
PRODUCT_USE_AUTHORIZED: NO
```

M0 activó el recovery plan y quedó cerrado como `CLOSED_OWNER_ACCEPTED`. La ejecución integral de PLAN013 está autorizada por la autoridad viva; cada misión conserva sus gates, allowlist, checksum y revisión requeridos.

No hacer:
No modificar código productivo.
No ejecutar providers.
No cambiar estados históricos de planes cerrados.
No borrar ni reemplazar EXTEND-01.
No crear una nueva rama salvo autorización expresa.

Verificación:
Control operativo coherente.
PLAN013 localizable.
La autorización integral de PLAN013 consta explícitamente en el control operativo.
`git diff --check`.
OWNER review antes de continuar.

Gate `PLAN013_M0_GATE`:
`PLAN013_RECOVERY_PLAN_ACTIVE`
`EXTEND_01_REAL_RUN_SUSPENDED`
`PLAN012_UNCHANGED`
`M0_NO_PRODUCT_CODE_CHANGED`

7\. BLOQUE 1 — RESEARCH: VERDAD, PROPÓSITO E INTEGRIDAD

Objetivo del bloque:
Eliminar falsos positivos de evidencia y alinear el contrato de Research con el intake sin obligar al usuario a repetir información que el sistema puede derivar.

M1.1 — Verdad única de evidencia utilizable

Problema:
La presencia de source\_entries puede producir DIRECT/can\_proceed aunque la fuente esté NOT\_RECOVERED, PENDING o NOT\_REVIEWED.

Archivos principales previstos:
`src/application/research_b2.py`
`schemas/source_access_and_evidence_report.json`
`schemas/research_source_access.json`
`tests/core/test_plan012_m3_b2_base_research.py`
tests relacionados con evidence/provenance y Research V2

Cambio esperado:
Definir una única evaluación software-owned de evidencia utilizable.
Una fuente solo cuenta como disponible para el uso previsto cuando existe adquisición positiva y el estado mínimo de verificación exigido por ese uso.
material\_principal\_disponible, tipo\_de\_acceso, can\_proceed, claims\_sostenibles y confidence deben derivarse de esa verdad, no de la mera existencia de un registro.
Los estados negativos y pendientes deben conservarse y provocar LIMITATION, MORE\_RESEARCH\_REQUIRED o BLOCK según el contrato aplicable.

Criterio de aceptación:
Una fuente registrada pero NOT\_RECOVERED nunca produce DIRECT ni can\_proceed.
Una fuente recuperada pero todavía no verificada no puede sostener un claim que exige verificación.
Los casos positivos existentes continúan funcionando.

M1.2 — Resolución canónica del propósito Research

Problema:
Research REAL exige intended\_use/research\_intended\_use aunque el intake canónico no lo produce.

Archivos principales previstos:
`src/application/research_m7.py`
`src/application/research_planning.py`
contrato de intake/handoff aplicable
`schemas/research_plan.json`
`tests/harness/test_plan012_m7_b5.py`
tests de intake→Research

Cambio esperado:
Crear una regla única de precedencia:
1\. intención humana explícita válida, cuando exista;
2\. propósito estándar derivable de la intención/brief/autoridad vigente;
3\. BLOCK si existe ambigüedad material que cambia alcance, evidencia o suficiencia.

No añadir un campo humano obligatorio universal si el propósito estándar es inequívoco.
Persistir el origen de la decisión para distinguir DERIVED\_STANDARD de OWNER\_EXPLICIT.

Criterio de aceptación:
El flujo estándar llega a Research sin pedir un dato redundante.
Una intención específica del OWNER prevalece y queda trazada.
Una contradicción entre intención explícita y propósito derivado bloquea.

M1.3 — Binding íntegro de ResearchPlan

Problema:
bind\_research\_plan puede regenerar o colapsar IDs/relaciones y vaciar gaps\_risks o potential\_specialists.

Archivos principales previstos:
`src/application/research_planning.py`
`schemas/research_plan_proposal.json`
`schemas/research_plan.json`
tests de ResearchPlanningService

Cambio esperado:
Preservar IDs válidos y relaciones de la propuesta.
Generar identificadores solo cuando falten y hacerlo determinísticamente donde corresponda.
Preservar gaps\_risks y potential\_specialists.
Validar referencias internas después del binding.
No permitir que un plan formalmente válido pierda información semántica aprobada.

Gate `PLAN013_B1_GATE`:
PROD02-R2-F001 \= RESOLVED
PROD02-R2-F002 \= RESOLVED
PROD02-R2-F004 \= RESOLVED
Pruebas focales PASS.
Regresiones directas PASS.
Suite Research relevante PASS.
No providers reales.
No autoaprobación funcional.

8\. BLOQUE 2 — IDENTIDAD Y LINEAGE

Objetivo del bloque:
Restaurar una identidad verificable de fuentes y hacer que las decisiones de pertenencia respeten de forma determinista el EditorialProfile activo.

M2.1 — Reconciliar lineage B3

Problema:
El mismo source\_id/locator está representado con checksums incompatibles.

Archivos principales previstos:
`config/editorial_profile_registry.json`
`profiles/voice/corpus_manifest.json`
perfil editorial activo y sus fuentes
documento fuente B3 referenciado
`tests/core/test_context_manifest_lineage.py`
`tests/core/test_editorial_profile_registry.py`

Cambio esperado:
Determinar cuál es la versión/identidad canónica actual de la fuente.
Actualizar referencias derivadas para que un mismo source\_id \+ locator \+ versión no tenga checksums incompatibles.
No reescribir contenido funcional por el simple hecho de corregir el lineage.
Añadir validación cruzada que falle si una misma identidad durable se registra con checksums incompatibles sin cambio explícito de versión.

Criterio de aceptación:
Una única identidad verificable por versión.
Pointer activo, registry, compiled profile y corpus no se contradicen.
No se fabrica un checksum para hacer verde el test: se calcula sobre la fuente correcta.

M2.2 — Topic Belonging contra territorios reales del perfil

Problema:
La evaluación puede aceptar proposed\_territory aunque el perfil activo lo marque EXCLUDED.

Archivos principales previstos:
`src/application/topic_belonging.py`
carga/autoridad del active editorial profile
schemas de Topic Belonging correspondientes
`tests/core/test_application_intake.py`
`tests/core/test_channel_intelligence.py`
`tests/harness/test_plan009_m1_vertical.py`

Cambio esperado:
Resolver proposed\_territory contra el perfil activo exacto antes de una decisión positiva.
La IA puede proponer un territorio; Software comprueba su existencia y estado.
EXCLUDED no puede convertirse en ACTIVE por salida cognitiva.
Territorio desconocido o ambiguo bloquea o solicita corrección según el contrato vigente.
Conservar binding de profile\_id/version/checksum.

M2.3 — Conectar invalidación selectiva a una dependencia real

Naturaleza:
Este punto proviene de una OBSERVATION, no de un blocker.

Cambio esperado:
No construir un nuevo grafo.
Usar el mecanismo de invalidación existente.
Conectar al menos una dependencia real de perfil→artefacto y demostrar:
NO\_MATERIAL\_IMPACT cuando el cambio no afecta el artefacto;
PARTIAL/DIRECT\_IMPACT cuando sí lo afecta;
invalidación de la decisión antigua cuando cambia el input versionado relevante.

Si durante la inspección se demuestra que ya existe un consumidor productivo correcto, limitar la misión a añadir la prueba que lo demuestre.

Gate `PLAN013_B2_GATE`:
PROD01-R2-F001 \= RESOLVED
PROD01-R2-F002 \= RESOLVED
PROD01-R2-F003 \= DEMONSTRATED o explícitamente DEFERRED\_WITH\_EVIDENCE si sigue sin consumidor real
Perfil activo coherente.
Topic Belonging no contradice territorios.
Lineage test PASS.

9\. BLOQUE 3 — ADQUISICIÓN Y FRONTERA RESEARCH→SCRIPT

Objetivo del bloque:
Hacer que RESEARCH\_READY signifique que el sistema puede entregar al siguiente tramo investigación realmente adquirida, trazada y utilizable.

M3.1 — Capacidad canónica de adquisición externa

Problema:
TOPIC\_FIRST no dispone de una vía general de adquisición cuando la evidencia requerida no está en el corpus upstream.

Decisión de diseño:
El producto objetivo necesita poder investigar temas que no estén preaportados por el OWNER. Por tanto, la solución preferida es materializar una vía canónica de adquisición, no reducir permanentemente el producto a corpus local.

Requisitos:
Separar búsqueda/descubrimiento de adquisición/fetch y de verificación.
Mantener el adaptador externo como herramienta, nunca como autoridad editorial.
Conservar source\_id, locator, acquisition method, retrieval status, evidence status, provenance y errores.
No simular descubrimiento.
Si una herramienta no está disponible para una corrida concreta, el software debe declarar capacidad UNAVAILABLE y bloquear únicamente el alcance que la necesita.

Archivos a localizar y reutilizar antes de crear:
`src/application/research_planning.py`
SoftwareAcquisitionAdapter existente
registries/capability routing aplicables
contratos de source access/provenance
infraestructura de tools/adapters ya existente
EXTEND-01, porque esta capacidad debe servir a su futura demostración REAL

No hacer:
No construir un navegador propio.
No crear un proveedor específico de investigación si puede existir un adapter neutral.
No acoplar Research a ChatGPT/web.run, Codex u OpenCode.

M3.2 — Handoff consultivo Research→Script

Problema:
Research conoce matices, límites, contraevidencia y utilidad editorial que pueden perderse o rederivarse downstream.

Cambio esperado:
Extender el handoff/ResearchReady existente con una proyección consultiva versionada que incluya únicamente información editorialmente útil:
contribuciones materiales;
límites;
contraevidencia;
lecturas rivales;
restricciones heredadas;
provenance/evidence refs;
incertidumbres restantes.

Esa proyección es CONSULTATIVE\_ONLY.
No decide hook, pacing, orden narrativo, Viewer Journey ni escritura.

M3.3 — Resolver B5-I3 en el grafo real

Problema:
B5\_I3\_NARRATIVE\_ARCHITECTURE figura como routing\_resolvable=true pero no existe la route correspondiente.

Archivos principales previstos:
`config/capability_registry.json`
`config/capability_routing.yaml`
`src/ai/role_execution.py`
`prompts/roles/NARRATIVE_ARCHITECTURE`
`tests/harness/test_plan011_m3_b5_i3.py`
`tests/harness/test_plan009_m1_vertical.py`
`tests/harness/test_plan012_m7_b5.py`

Cambio esperado:
Registrar una única ruta canónica B5-I3 que consuma el paquete aprobado.
Validar required inputs, output schemas y preflight.
No autorizar todavía ejecución REAL de B5-I3.
La prueba estructural ROUTE\_ENTRYPOINT\_UNRESOLVED debe desaparecer por una route real, no relajando el test.

Gate `PLAN013_B3_GATE`:
PROD02-R2-F003 \= RESOLVED como capacidad o limitación explícita demostrable.
PROD02-R2-F005 \= RESOLVED.
Parte Research→B5-I3 de PROD03-R2-F001 \= CONNECTED.
RESEARCH\_READY tiene consumidor canónico resoluble.
Adquisición negativa bloquea limpiamente.
Adquisición positiva puede representarse sin provider específico.

10\. BLOQUE 4 — GRAFO PRODUCTIVO DE GUION Y CONTRATOS

Objetivo del bloque:
Conectar arquitectura narrativa, redacción, edición y auditoría final sin que el agente operador tenga que completar huecos fuera del producto.

M4.1 — Runtime contracts para roles existentes

Problema:
WRITING, EDITOR y FINAL\_EDITORIAL\_AUDITOR existen en responsabilidades/prompts/perfiles, pero no tienen materialización equivalente completa en ROLE\_REQUIRED\_INPUTS / ROLE\_ALLOWED\_OUTPUT\_SCHEMAS ni un grafo productivo.

Archivos principales previstos:
`src/ai/role_execution.py`
`config/responsibility_registry.json`
`config/agent_prompt_registry.json`
`config/agent_execution_profiles.json`
`config/capability_registry.json`
`config/capability_routing.yaml`
prompts/roles/WRITING
prompts/roles/EDITOR
`prompts/roles/FINAL_EDITORIAL_AUDITOR`
schemas correspondientes

Cambio esperado:
Añadir únicamente los contratos y routes faltantes.
Reutilizar roles existentes; no crear reemplazos.
Cada rol debe tener inputs obligatorios, outputs permitidos, independencia y límites claros.
El runtime debe fallar si un input obligatorio no se resuelve.

M4.2 — Continuidad contractual de RefinedThesis

Problema:
NarrativePlan conserva thesis como string y downstream puede perder la identidad exacta de RefinedThesis.

Cambio esperado:
Propagar una referencia inequívoca:
thesis\_id
artifact/version
checksum
research/evidence lineage relevante

El texto de la tesis puede mantenerse como snapshot legible, pero la autoridad downstream es la referencia versionada.
Una nueva RefinedThesis invalida planes, drafts y auditorías dependientes de la anterior.

Archivos principales previstos:
`schemas/refined_thesis.json`
`schemas/narrative_plan.json`
schema de ScriptDraft/ScriptVersionManifest aplicable
`schemas/script_version_manifest.json`
validators y tests de contratos

M4.3 — Reforzar ScriptBlockContract y EditorialEditReport

Problema:
Los contratos pueden validar sin evidencia de continuidad, transición, repetición, oralidad y pendientes.

Cambio esperado:
Hacer obligatoria la decisión sobre esas dimensiones, no obligar a que existan defectos.
Ejemplo: continuity\_findings puede ser \[\], pero debe estar presente si esa dimensión aplica.
Permitir N/A únicamente con justificación cuando sea legítimo.
Conservar referencia al plan/tesis/versión que se editó.

No imponer un número universal de palabras, rehooks o transiciones.

M4.4 — Reforzar FinalEditorialAudit

Problema:
Campos críticos existen pero no son obligatorios.

Cambio esperado:
Exigir decisión explícita sobre las dimensiones v2.1 aplicables:
viewer journey;
opening;
progression;
coherence;
originality;
source transformation;
voice;
orality;
closing;
factual traceability;
riesgos que pertenezcan a su dominio.

Cada dimensión debe ser PASS / WARN / REQUEST\_CHANGES / BLOCK o N/A\_JUSTIFIED según el contrato final elegido.
El PASS global solo es posible si todas las dimensiones obligatorias tienen una disposición válida.

M4.5 — Coordinador mínimo del tramo de guion

Cambio esperado:
Materializar el encadenamiento:
NARRATIVE\_ARCHITECTURE
→ WRITING
→ EDITOR
→ FINAL\_EDITORIAL\_AUDITOR

El coordinador no toma decisiones editoriales por los roles.
Solo prepara inputs, valida outputs, persiste referencias, mantiene identidad/version/checksum y enruta correcciones.

Gate `PLAN013_B4_GATE`:
PROD03-R2-F001 \= RESOLVED para el tramo de guion.
PROD03-R2-F002 \= RESOLVED.
PROD03-R2-F003 \= RESOLVED.
PROD03-R2-F004 \= RESOLVED.
Ruta sintética NarrativePlan→FinalEditorialAudit PASS.
Productor/editor/auditor mantienen independencia.
Cambio de tesis invalida downstream dependiente.

11\. BLOQUE 5 — YOUTUBE FINAL SCRIPT-ONLY

Objetivo del bloque:
Crear la validación final de YouTube que realmente audita el guion terminado sin reintroducir packaging final, SEO, miniatura, Shorts o publicación.

M5.1 — YouTubeAdaptationReview FINAL

Problema:
El review existente está ligado a artefactos tempranos/pre-script y el cierre no exige una evaluación del guion final exacto.

Cambio esperado:
Extender la autoridad `YOUTUBE_ADAPTATION` existente dentro de la misma familia mediante el contrato explícito `FINAL_SCRIPT_REVIEW`. No crear un segundo auditor ni una autoridad paralela.
La entrada debe incluir como mínimo:
episode\_id;
script artifact\_id;
script\_version;
script\_checksum;
perfil activo;
promesa visible vigente aplicable;
FinalEditorialAudit de la misma versión;
evidencia necesaria para policy/rights.

La revisión final debe emitir una decisión independiente y versionada. Debe consumir el guion terminado exacto y conservar `episode_id`, `artifact_id`, `script_version` y `script_checksum` en su entrada, salida y provenance.

M5.2 — Política contextual en lugar de gate léxico como autoridad

Problema:
qa\_lenguaje\_youtube puede decidir mediante palabras/patrones sin comprender contexto.

Cambio esperado:
Mantener el scanner léxico como sensor barato.
Su salida alimenta la revisión contextual.
Una coincidencia léxica por sí sola no produce FAIL final.
Un resultado contextual debe identificar el riesgo, el fragmento, el motivo y la mitigación/corrección requerida.

M5.3 — Duración como telemetría episódica

Problema:
144 WPM / 18–22 min puede convertirse en criterio universal de cierre.

Cambio esperado:
Mantener cálculo WPM como medición.
Consumir el duration envelope específico del episodio cuando exista.
Sin envelope válido, producir UNKNOWN/NEEDS\_REVIEW o una estimación claramente no normativa.
El fallback histórico puede servir como referencia técnica, nunca como bloqueo editorial universal.

Archivos principales previstos:
`src/core/duration_envelope.py`
`src/scripts/qa_duracion_guion.py`
schemas y tests de duration envelope / YouTube review

M5.4 — Autenticidad, repetición y producción masiva

Cambio esperado:
Incorporar una dimensión explícita al review final:
riesgo de texto genérico;
repetición sustantiva;
dependencia excesiva de plantilla;
producción masiva/inauténtica;
transformación real del material.

La evaluación debe ser contextual.
Uso de IA, estructura recurrente o formato de canal no son FAIL automáticos.

M5.5 — Rights/reuse y apertura sobre manifestación final

Confirmar en el mismo review final:
que la apertura real cumple la promesa aplicable;
que el texto no depende de reproducción sustitutiva;
que citas/escenas/reutilización prevista están dentro de límites documentados;
que incertidumbres relevantes quedan visibles.

Gate `PLAN013_B5_GATE`:
PROD04-R2-F001 \= implementación standalone final demostrada.
PROD04-R2-F002 \= RESOLVED.
PROD04-R2-F003 \= RESOLVED.
PROD04-R2-F004 \= RESOLVED.
El review final queda ligado a artifact/version/checksum exactos.
Todavía no cerrar episodio en este bloque.

12\. BLOQUE 6 — CIERRE, PREFLIGHT Y E2E

Objetivo del bloque:
Hacer que EDITORIAL\_SCRIPT\_APPROVED sea un estado real del producto y no un verde parcial producido por un script legacy.

M6.1 — required\_context verdaderamente obligatorio

Problema:
role\_execution.\_applicable\_policies ignora silenciosamente required\_context que no sea una ruta .md o .json.

Cambio esperado:
Crear una resolución canónica de referencias de contexto.
Una referencia puede resolver a archivo, perfil/registry u otra sede aprobada.
Si está declarada como required y no puede resolverse, preflight \= BLOCK.
No mantener tokens simbólicos obligatorios que el runtime simplemente omite.

M6.2 — Coherencia OpenAI-compatible

Problema:
runtime/config utiliza api\_base\_env mientras OpenAICompatibleProvider busca base\_url\_env.

Cambio esperado:
Usar `api_base_env` como nombre canónico en el contrato runtime.
Mantener `base_url_env` únicamente como alias transitorio si existe un consumidor real demostrado y con prueba de regresión.
Añadir prueba que recorra configuración→request→provider y verifique que `OPENAI_API_BASE` llega realmente al adaptador.
Revisar DeepSeek/Ollama/Gemini/Anthropic solo para evitar que la normalización rompa configuraciones existentes; no ampliar el alcance a un router multi-provider.

M6.3 — Autoridad única de cierre

Problema:
cerrar\_episodio.py puede marcar completado sin convergencia de todas las autoridades finales modernas.

Cambio esperado:
Mantener `cerrar_episodio.py` como entrypoint de compatibilidad, pero retirar su autoridad de cierre. Debe delegar en una única operación software-owned que compruebe sobre el MISMO script:
`artifact_id`
`script_version`
`checksum`

La operación canónica se materializa extendiendo la persistencia existente en `src/application/storage.py`; no se crea un segundo cierre independiente. La implementación debe demostrar que ningún entrypoint legacy puede marcar por sí mismo el episodio como completado y que todos los cierres pasan por la operación única.

Prerrequisitos mínimos:
ScriptVersionManifest vigente.
Evidencia/claims/factual traceability vigente según contrato.
FinalEditorialAudit independiente.
YouTubeAdaptationReview FINAL.
EditorialScriptApproval humano posterior a las auditorías.
Registro/manifest de cierre.

Una versión nueva invalida auditorías y aprobación de la versión anterior. No pueden coexistir dos mecanismos de cierre con capacidad de marcar el episodio como completado.

M6.4 — Convergencia persistente y retry seguro

La operación de cierre debe reconciliar de forma idempotente:
workflow\_state
episode\_state
episodes\_index
manifest/evidencias finales

La evidencia de convergencia debe registrar el estado anterior, el estado posterior, cada store afectado, sus checksums, el resultado de la operación y el resultado de un retry. Un fallo parcial debe restaurar los valores anteriores o completar la transacción de forma verificable; nunca puede dejar un store en estado completado y otro abierto.

Un crash parcial no puede dejar un índice completado mientras los otros stores continúan abiertos.
Un retry debe completar o restaurar coherencia sin duplicar la aprobación.

No introducir una base de datos por reflejo. Reutilizar locks, temp+replace y persistencia local existente mientras sean suficientes.

M6.5 — E2E sintético representativo

Crear una prueba de integración aislada en temporales de test que empiece por el entrypoint humano y mantenga el mismo `episode_id` hasta el cierre.

Debe cubrir como mínimo:
propósito Research estándar derivado;
override humano válido;
fuente no recuperada bloqueada;
fuente recuperada/verificada positiva;
RESEARCH\_READY;
B5-I3;
WRITING;
EDITOR;
FINAL\_EDITORIAL\_AUDITOR;
YouTube final;
aprobación humana sintética posterior, marcada exclusivamente como fixture de test y sin producir aprobación funcional o estado productivo;
cierre;
convergencia de stores;
mismatch de checksum;
nueva versión que invalida decisiones previas;
required\_context irresoluble;
route ausente;
config OpenAI-compatible coherente.

La prueba puede utilizar cognición sintética. Debe declararse `SYNTHETIC_E2E`, nunca `REAL_RESEARCH_QUALITY` o `REAL_SCRIPT_QUALITY`, y no puede escribir estados vivos, evidencias productivas ni aprobar el uso del producto.

M6.6 — Auditoría focal de remediación

No repetir la auditoría general completa.

Realizar una reauditoría independiente y limitada a:
los 16 findings R2;
las causas raíz que los agrupan;
los tres critical paths CP-01, CP-02 y CP-03;
regresiones introducidas por PLAN013.

El auditor no puede ser el implementador de la corrección. Debe producir para cada finding:
RESOLVED;
PARTIALLY\_RESOLVED;
NOT\_RESOLVED;
SUPERSEDED\_BY\_VERIFIED\_FIX;
DEFERRED\_WITH\_EVIDENCE.

Cada critical path debe quedar definido en el `findings_manifest.json` con su punto de entrada, punto de salida, findings vinculados, pasos obligatorios, evidencia de conexión y casos fail-closed. No se puede declarar un major fuera de un critical path sin justificar explícitamente su impacto.

CP-01, CP-02 y CP-03 son entradas obligatorias del paquete antes de la auditoría independiente, no entregables que puedan definirse después del BUILD. Cada definición debe identificar el recorrido funcional/técnico que representa y su relación con los 16 findings. Si la auditoría de origen usa otra nomenclatura o alcance, el manifest debe conservar el identificador original y documentar la correspondencia sin reinterpretarlo.

Un `OWNER_ACCEPTED_RESIDUAL_RISK` debe registrar como mínimo `finding_id`, impacto, owner, mitigación, vigencia o disparador de revalidación, critical paths afectados, decisión del OWNER, fecha y evidencia de revisión independiente.

Gate `PLAN013_B6_GATE`:
16 findings con disposición explícita.
Todos los BLOCKER cerrados.
E2E sintético PASS.
Suite completa PASS en cierre final.
git diff \--check PASS.
No ejecución REAL.
No uso productivo automático.

13\. ESTRATEGIA DE PRUEBAS

Nivel 1 — misión:
tests focales del componente modificado;
tests directos del consumidor;
lint/compile solo donde aplique;
git diff \--check.

Nivel 2 — gate de bloque:
suite del dominio afectado;
tests de contratos/routing relacionados;
una regresión negativa por defecto corregido;
una regresión positiva para comportamiento preservado.

Nivel 3 — cierre PLAN013:
E2E sintético completo;
suite completa;
validación de registries/routing;
preflight;
integridad textual;
git diff \--check;
revisión de estado Git.

No ejecutar la suite completa varias veces dentro de una misma misión sin una razón nueva.

14\. POLÍTICA DE CAMBIOS Y COMMITS

Este plan no autoriza commit ni push por sí mismo.

Cada misión operativa posterior deberá declarar expresamente:
si commit está autorizado;
si push está autorizado;
qué archivos pertenecen a la misión;
qué cambios preexistentes deben preservarse.

Recomendación:
un commit por unidad cerrada y revisable, no un commit gigante para todo PLAN013.
No mezclar arreglos de bloques diferentes si no existe una dependencia técnica real.

AutoZIP se ejecutará únicamente cuando corresponda al cierre autorizado de una misión con cambios y como última operación, siguiendo la política vigente del proyecto.

15\. CONDICIONES DE DETENCIÓN

El agente debe detener la misión y reportar BLOCKED si:

la solución requiere redefinir un criterio funcional no resuelto por la auditoría v2.1;
aparece una contradicción entre el plan y una autoridad canónica más reciente;
para arreglar un finding necesita modificar una capa no prevista con impacto material;
un cambio exige reabrir PLAN012;
se detecta pérdida de datos o necesidad de migración destructiva;
la única forma de hacer verde un test es debilitar un contrato cognitivo correcto;
una ruta REAL requiere seleccionar provider/modelo sin autorización del OWNER;
la remediación empieza a crear una segunda fuente de verdad;
la evidencia externa de auditoría no puede exportarse o verificarse por hash;
la corrección exige cambiar el perfil activo o su checksum sin la aprobación correspondiente;
un finding material no tiene `production_cause` y `escape_cause` independientes.

16\. CRITERIO DE CIERRE DE PLAN013

PLAN013 solo puede cerrarse cuando:

CP-01 = `CONNECTED_SYNTHETICALLY_AND_FAIL_CLOSED`.
CP-02 = `CONNECTED_SYNTHETICALLY`.
CP-03 = `CONNECTED_SYNTHETICALLY`.
Los cuatro BLOCKER funcionales R2 están `RESOLVED`.
Los once MAJOR están `RESOLVED`, o existe `OWNER_ACCEPTED_RESIDUAL_RISK` explícito, documentado después de revisión independiente y sin afectar CP-01, CP-02 o CP-03.
La OBSERVATION de invalidación queda `DEMONSTRATED` o `DEFERRED_WITH_EVIDENCE` sin afectar el cierre.
Ningún `PARTIALLY_RESOLVED` o `NOT_RESOLVED` puede equivaler silenciosamente a PASS.
La ruta completa mantiene artifact/version/checksum.
El cierre converge estados.
El E2E sintético representativo pasa.
La suite completa pasa.
La reauditoría focal no encuentra un blocker nuevo causado por la remediación.
El resultado técnico pasa revisión independiente.
Las conformidades funcionales de los dominios afectados, cuando correspondan, están separadas de la aprobación técnica.
El OWNER revisa y acepta el cierre.

La cadena de estados del plan es:

```text
PLAN013_TECHNICAL_PASS
→ PLAN013_INDEPENDENT_AUDIT_PASS
→ PLAN013_FUNCTIONAL_CONFORMANCE_PASS cuando corresponda
→ PLAN013_OWNER_APPROVED_CLOSED
→ READY_TO_REQUEST_EXTEND_01_RESUMPTION
```

`PLAN013_FUNCTIONAL_CONFORMANCE_PASS` no declara aprobación del producto. La reanudación de EXTEND-01 y cualquier `REAL_AI_EXECUTION` requieren una decisión posterior e independiente del OWNER.

Estado final permitido:
PLAN013 = `OWNER_APPROVED_CLOSED`
CURRENT_RECOVERY_PLAN = `NONE`
CURRENT_RECOVERY_PHASE = `NONE`
CURRENT_MISSION = `NONE`
CURRENT_MISSION_EXECUTION_BUNDLE = `NONE`
NEXT_ALLOWED_ACTION = `OWNER_DECISION_EXTEND_01_RESUMPTION`
PLAN013_RESULT = `READY_TO_REQUEST_EXTEND_01_RESUMPTION`
EXTEND_01_RESUME_AUTHORIZED = `NO`
REAL_AI_EXECUTION = `NO`
REAL_RESEARCH_QUALITY_DEMONSTRATED = `NO`

17\. SIGUIENTE PASO DESPUÉS DEL CIERRE

Volver exactamente al roadmap post-PLAN012 y retomar EXTEND-01 desde el checkpoint que estaba vigente antes de activar PLAN013.

Antes de la corrida REAL:
confirmar configuración de ejecución;
confirmar capacidad de adquisición;
confirmar presupuesto/límites anti-loop;
confirmar provider/modelo únicamente para provenance de esa corrida;
obtener autorización explícita del OWNER.

La corrida REAL posterior deberá demostrar calidad de Research con evidencia real. No debe usarse para descubrir defectos estructurales que PLAN013 podía detectar sintéticamente.

18\. RESULTADO ESPERADO

PLAN013 no pretende declarar terminado el Proyecto YouTube.

Pretende transformar el estado actual:

MUCHAS PIEZAS CORRECTAS
\+ ISLAS PARCIALMENTE CONECTADAS
\+ CIERRE LEGACY
\+ REAL RUN PREMATURA

En:

UNA RUTA CANÓNICA SINTÉTICAMENTE DEMOSTRADA
\+ EVIDENCIA FAIL-CLOSED
\+ ROLES CONSUMIBLES
\+ AUDITORÍAS FINALES SOBRE LA MISMA VERSIÓN
\+ CIERRE SOFTWARE-OWNED
\+ EXTEND-01 LISTO PARA REANUDARSE DE FORMA SEGURA

FIN DEL PLAN
