PLAN015 — INTEGRACIÓN E2E OPERATIVA DEL EPISODIO

Versión del plan: 0.4.0  
Estado: IN_PROGRESS  
Baseline de diseño: e6885736e300e7d1543759b577d16a39eb3925be  
Ruta canónica propuesta en repositorio: plans/plan_015/PLAN015_Integracion_E2E_operativa_del_episodio.md  
Auditoría previa: PASS  
OWNER APPROVAL: APPROVED  
IMPLEMENTATION_AUTHORIZED: YES  
Ejecución autorizada: YES  
PRE_FLIGHT_INITIAL: PASS  
Producto autorizado por este documento: NO

1\. DECISIÓN DE DIRECCIÓN

PLAN015 implementa un único resultado de producto: un usuario debe poder crear o reanudar un episodio y recorrer, desde la superficie normal del producto, las capacidades editoriales ya existentes hasta obtener un guion aprobado CURRENT, sin reconstrucción técnica manual del contexto, sin repetir trabajo cognitivo válido y sin depender exclusivamente de una misión temporal de desarrollo.

El plan integra cuatro superficies inseparables para ese resultado:  
\- continuidad/composición general del episodio;  
\- autoridad operacional ordinaria de producto;  
\- roundtrip AGENT_HARNESS como interacción normal;  
\- cierre editorial y entrega CURRENT inequívoca.

La operación multi-episodio queda fuera de PLAN015 y se aborda separadamente en PLAN016.

PLAN015 no presupone una clase EpisodeCoordinator, un nuevo motor de workflow, una base de datos, un checkpoint store, LangGraph ni un subsistema de políticas nuevo. La implementación debe reutilizar y generalizar mínimamente los mecanismos existentes.

2\. ESTADO INICIAL Y PRECONDICIÓN DE ACTIVACIÓN

Baseline de diseño:  
master/origin \= e6885736e300e7d1543759b577d16a39eb3925be  
baseline de código \= HEAD/master/origin en e6885736e300e7d1543759b577d16a39eb3925be; durante auditoría pueden existir únicamente los archivos candidatos PLAN015/PLAN016 sin trackear, pero no otros cambios de código/configuración no explicados  
último plan material cerrado \= PLAN014  
CURRENT_PLAN \= NONE

El estado operativo vivo no es vacío. Antes de activar PLAN015 debe reconciliarse deliberadamente cualquier autoridad temporal previa que siga activa, de modo que no coexistan dos autoridades de ejecución contradictorias.

Como mínimo deben quedar coherentes, según el canon vigente del repositorio:  
\- CURRENT_ACTIVITY;  
\- CURRENT_MISSION;  
\- EXECUTION_AUTHORIZED;  
\- EXECUTION_AUTHORIZATION_SCOPE;  
\- CURRENT_MISSION_EXECUTION_BUNDLE;  
\- PRODUCT_USE_AUTHORIZED;  
\- MVP_REAL_E2E_STATUS;  
\- NEXT_ALLOWED_ACTION.

La transición no puede borrar historia ni invalidar evidencia previa. Debe cerrar, suspender o reemplazar explícitamente la autoridad temporal anterior según los contratos vigentes.

La misión temporal `MVP_REAL_E2E_SCRIPT_01` queda, al activar PLAN015, `SUPERSEDED_BY_PLAN015`. PLAN015 no exige completar esa misión antes de activarse, pero antes de retirar o cambiar `CURRENT_MISSION` debe ejecutarse un inventario fail-closed de sus handoffs mission-bound. Las fuentes mínimas son la bandeja operativa `handoff/`, `Historial/<episode_id>/handoffs/`, los artifacts y bindings persistidos dentro del episodio/Vault, los registros que referencien `handoff_id` y cualquier ruta externa declarada explícitamente por el mission contract vigente.

Cada handoff encontrado debe quedar en exactamente una disposición durable: `CONSUMED`, si el resultado fue validado y su commit durable completado; `CANCELLED`, si se retiró explícitamente sin resultado consumible; o `ARCHIVED`, si se cerró y movió a historia con integridad verificada. La disposición debe conservar handoff_id, mission_id, bindings relevantes, motivo y timestamp en los registros persistentes existentes. La activación exige `AMBIGUOUS_HANDOFFS = 0` y `PENDING_OLD_MISSION_HANDOFFS = 0`, con evidencia durable de la reconciliación. No se crea un subsistema de recovery nuevo si los mecanismos existentes bastan. Una vez retirada la autoridad anterior, cualquier resultado nuevo que pretenda usarla debe rechazarse; no se permite replay silencioso, migración implícita de autoridad ni borrado de evidencia histórica.

Antes de OWNER APPROVAL, el plan debe contrastarse contra el HEAD real. Si el delta desde la baseline cambia contratos, routing, lifecycle, autoridad, cierre o capabilities necesarias, el plan debe corregirse antes de autorizar ejecución.

3\. RESULTADO OBLIGATORIO

Al terminar PLAN015 debe existir una operación E2E capaz de demostrar:

usuario  
→ crea o reanuda episodio  
→ Software carga estado durable  
→ Software determina la próxima transición válida  
→ Software invoca o presenta la capability correspondiente  
→ IA ejecuta solo trabajo cognitivo cuando aplica  
→ Software valida y materializa el resultado  
→ Software persiste artifacts, estado, lineage y provenance  
→ Software vuelve a resolver la próxima transición  
→ se detiene únicamente ante una parada legítima  
→ reanuda cuando la condición pendiente queda satisfecha  
→ converge todas las validaciones editoriales obligatorias sobre el mismo guion  
→ solicita una decisión humana exacta  
→ Software materializa la aprobación editorial canónica  
→ cierra determinísticamente en EDITORIAL_SCRIPT_APPROVED  
→ expone una única representación CURRENT del guion aprobado.

No hay cumplimiento si el operador debe conocer entrypoints internos, fabricar ExecutionRequest/InputArtifact, copiar IDs o checksums, construir a mano payloads de aprobación/cierre, elegir una misión técnica para continuar un episodio ordinario o inspeccionar el Vault para descubrir el siguiente paso.

4\. ALCANCE

PLAN015 autoriza, una vez auditado y aprobado, los cambios mínimos necesarios para:  
\- crear/reanudar desde la superficie normal;  
\- determinar software-owned la siguiente transición válida desde estado durable;  
\- componer Topic Belonging → Research → B5-I3 → Writing → Editor → validaciones/auditorías obligatorias → decisión humana → cierre;  
\- preservar stops legítimos y reanudación sin replay;  
\- establecer una autoridad ordinaria de producto fuerte y separada de una misión temporal;  
\- preservar preflight, capability registry, routing, perfiles, provenance, lineage y guards;  
\- encapsular el roundtrip AGENT_HARNESS dentro de la interacción normal;  
\- materializar EditorialScriptApproval desde una decisión humana explícita válida;  
\- cerrar por artifact/version/checksum exactos;  
\- exponer una única salida CURRENT aprobada y descubrible;  
\- ejecutar pruebas focales, integración representativa y validación live proporcional.

La superficie exacta de archivos debe decidirla el implementador después del pre-flight y de inspeccionar los contratos vigentes. No se autoriza un refactor amplio por conveniencia.

5\. NO ALCANCE

Queda fuera:  
\- multi-episodio / varios episodios en_progreso — PLAN016;  
\- RETRY general para todas las etapas;  
\- REGENERATE general;  
\- history UI o navegación avanzada;  
\- switching sofisticado, scheduling, colas, prioridades o workers;  
\- supersede downstream general más allá de lo necesario para mantener CURRENT correcto;  
\- defectos independientes no demostrados como bloqueantes del E2E;  
\- rediseño de Research;  
\- nuevos agentes por defecto;  
\- paralelización de Research por defecto;  
\- migración del Vault;  
\- nueva base de datos;  
\- framework externo de orquestación;  
\- refactor amplio no necesario;  
\- packaging/publicación posterior al guion aprobado, salvo materialización mínima necesaria para exponer CURRENT.

6\. ARQUITECTURA E INVARIANTES PROTEGIDOS

6.1 SOFTWARE → IA → SOFTWARE

SOFTWARE  
→ prepara contexto/request  
→ IA ejecuta únicamente cognición  
→ SOFTWARE recibe resultado  
→ materializa  
→ valida  
→ persiste  
→ decide transición.

La IA no decide routing, estado, IDs técnicos, versión, checksum, lineage, provenance, gates, autorización, materialización ni transición del workflow.

6.2 Cognitive Port y rutas

Se preserva CognitiveRequest → CognitivePort → API o Runner → CognitiveResult.  
El producto no se casa con proveedor, modelo ni harness concreto.  
La familia/ruta/modelo siguen resolviéndose mediante contratos existentes.  
Si AGENT_HARNESS es la familia seleccionada, su recorrido completo forma parte de la aceptación.

6.3 Identidad

episode_id sigue siendo identidad raíz.  
No sustituye artifact_id, version, checksum, run_id, request_id, decision_id, approval_id ni handoff_id.

Episodio ≠ misión.

6.4 Independencia editorial

Debe preservarse toda independencia exigida por contracts, perfiles y gates, como productor ≠ editor ≠ auditor.

6.5 Estado durable

Se reutilizan episode_state/workflow_state, artifacts persistidos, decisiones, approvals, checksums, lineage y bindings existentes.  
No se crea un nuevo checkpoint store.  
Si los mecanismos actuales no pueden satisfacer una garantía obligatoria, se activa STOP arquitectónico.

6.6 Fuente única de verdad

La composición general puede descubrir la frontera durable y seleccionar el consumidor/capability canónico, pero no puede reimplementar dentro de sí las reglas editoriales o gates de cada vertical.

Patrón permitido:  
estado durable  
→ resolver frontera  
→ seleccionar consumidor canónico  
→ vertical/gate canónico valida y decide su propia semántica.

Patrón prohibido:  
resolver general  
→ duplicar reglas de Topic  
→ duplicar Research  
→ duplicar Writing/Editor/auditorías.

7\. CONTRATO DE CONTINUIDAD

7.1 Regla principal

Dado un episodio durable válido, Software debe resolver la próxima transición válida a partir de estado, artifacts, gates, decisiones, approvals y autorizaciones persistidas.

Debe existir un único resolver software-owned en la capa application responsable de esta decisión. El plan no prescribe si se implementa extendiendo WorkflowCoordinator o mediante un componente concreto nuevo; sí exige que exista una sola fuente canónica para resolver la frontera E2E y que delegue la semántica de cada vertical a sus contratos/gates existentes.

No se admite stage_number \+ 1 ni “primera etapa incompleta” si ignora gates, stale data, decisiones, rutas alternativas o autoridad.

7.2 Fronteras mínimas

El E2E debe poder atravesar:  
\- intake → Topic Belonging;  
\- TOPIC_BELONGING_TECHNICAL_STOP válido → Research cuando proceda;  
\- Research B2/M4/M5/M6 y sus stops legítimos;  
\- decisión M4 persistida → continuación sin replay;  
\- RESEARCH_READY → B5-I3;  
\- B5-I3 → Writing;  
\- Writing → Editor;  
\- Editor → validaciones/auditorías obligatorias;  
\- validaciones convergentes → `FinalScriptReview` determinista software-owned;  
\- Final Review válido → decisión humana;  
\- aprobación editorial canónica → cierre;  
\- cierre → CURRENT visible.

7.2.1 Matriz normativa mínima de transición

La implementación debe materializar una tabla/contrato equivalente a esta semántica, sin sustituir los gates internos de cada vertical. En cada fila, `persistir` significa validar el contrato antes de escribir artifacts, actualizar atómicamente los estados aplicables y registrar lineage/provenance; un resultado ya committed se reutiliza sin repetir cognición.

\- Intake persistido \+ Topic no resuelto → capability ordinaria `TOPIC_BELONGING_ASSESSMENT`; salida: artifacts Topic y `TOPIC_BELONGING_TECHNICAL_STOP`. Stale, schema inválido, autoridad ausente o binding incorrecto → `BLOCKED`/fail-closed. Persistir Topic input, assessment, decision, gate, lineage y executions.  
\- `TOPIC_BELONGING_TECHNICAL_STOP` con resultado externo pendiente → `LEGITIMATE_STOP/PENDING_EXTERNAL_RESULT`; reanudar solo importa el handoff exacto y pasa a `CONSUMED` mediante el contrato de roundtrip. Resultado ajeno, stale, replayed o de autoridad retirada → rechazo sin cambio de estado.  
\- Topic decision CURRENT efectiva `APPROVE` → Research permitido si `decision_ref`, `decision_checksum`, cadena de reevaluación, lineage, profile binding e input checksum coinciden; salida: preparación Research persistida.  
\- Topic decision CURRENT efectiva `APPROVE_WITH_CONDITIONS` → Research permitido únicamente si cada condición está representada por evidencia durable existente y Software puede verificar y persistir su cumplimiento; si el contrato Topic no ofrece una condición/evidencia resoluble, el resultado obligatorio es `LEGITIMATE_STOP/TOPIC_CONDITIONS_PENDING` y PLAN015 no inventa semántica adicional.  
\- Topic decision CURRENT efectiva `REQUEST_MORE_EVIDENCE` → `READY_FOR_REASSESSMENT/LEGITIMATE_STOP`; no inicia Research. `ESCALATE_TO_OWNER` → `LEGITIMATE_STOP` esperando decisión OWNER. `REJECT` o `BLOCK` → `BLOCKED`; ninguna de estas decisiones inicia Research.  
\- Research B2/M4/M5/M6 con resultado externo pendiente → `LEGITIMATE_STOP/PENDING_EXTERNAL_RESULT`; importación validada persiste el resultado y continúa sin replay. Decisión M4 pendiente → `LEGITIMATE_STOP/WAITING_FOR_HUMAN_DECISION`; decisión persistida válida reanuda sin repetir trabajo confirmado. Partial persistence, stale input, autoridad inválida o commit incompleto → fail-closed.  
\- Research `RESEARCH_READY` o `RESEARCH_READY_WITH_LIMITATIONS` con gate/manifest/handoff vigente y consumible → capability existente `B5_I3_NARRATIVE_ARCHITECTURE`; salida: `ViewerJourney`, `OpeningDesign`, `ClosingDesign` y `NarrativePlan` persistidos, con estado durable `B5_I3_COMPLETE`. `NOT_RESEARCH_READY`, manifest stale, handoff inválido o restricciones sin binding → `BLOCKED`/fail-closed.  
\- `B5_I3_COMPLETE` con esos cuatro artifacts, ResearchReadyManifest/handoff, tesis/refined thesis, ResearchPack, profile y bindings exactos → capability `PLAN013_WRITING_SCRIPT_DRAFT`; salida persistida: `ScriptDraft` y `ScriptVersionManifest`, con `WORKING_CURRENT` de la versión. Falta de input, versión stale o checksum incompatible → no ejecución y `BLOCKED`/fail-closed.  
\- `WORKING_CURRENT` ScriptDraft con `ScriptVersionManifest`, profile, brief y ClaimsLedger exactos → capability `PLAN013_EDITOR_EDITED_SCRIPT`; salida persistida: `EditedScript`, `EditorialEditReport` y nuevo `ScriptVersionManifest`. Cambio en cualquier artifact upstream ligado → salida stale y no continúa.  
\- EditedScript `WORKING_CURRENT` con EditorialEditReport, profile, brief, ClaimsLedger y artifact/version/checksum coincidentes → capability `PLAN013_FINAL_EDITORIAL_AUDIT`; salida persistida: `FinalEditorialAudit` ligado al mismo episodio, artifact, versión y checksum. Input ausente, stale, schema inválido o independencia fallida → `BLOCKED`/correction required.  
\- FinalEditorialAudit con schema válido, `independence_result=PASS`, decisión top-level elegible y bindings exactos → validación determinista software-owned `FinalScriptReview`; salida persistida con checksum del audit consumido. Audit `FAIL`/`BLOCKED`, dimensión obligatoria no elegible o binding stale → no Final Review ni aprobación.  
\- FinalScriptReview `PASS` o `WARN` elegible, ligado al mismo artifact/version/checksum y audit exacto → HumanDecisionRequest de aprobación con `expected_actor_ref` y `expected_approval_role`; salida: decisión humana persistida. Review `BLOCKED`, stale o inconsistente → `LEGITIMATE_STOP/CORRECTION_REQUIRED`.  
\- HumanDecision `APPROVE` con actor, role, request, estado vigente y bindings exactos → Software crea, valida y persiste `EditorialScriptApproval` completo; salida: `APPROVAL_CURRENT`. `CORRECT` → corrección persistida y `IN_REVIEW`; `REJECT` → rechazo persistido y `BLOCKED`; `CANCEL` no infiere aprobación ni rechazo editorial.  
\- `APPROVAL_CURRENT` válida y todas las validaciones finales elegibles → `record_plan013_editorial_closure`, que consume el artifact completo de aprobación y sus bindings; salida: `EDITORIAL_SCRIPT_APPROVED` y `APPROVED_CURRENT`. Aprobación stale, incompleta o validación no elegible → no closure.  
\- `EDITORIAL_SCRIPT_APPROVED` con `APPROVED_CURRENT` único → `COMPLETE`; la superficie normal muestra la referencia exacta del guion aprobado.

Cada transición debe declarar y verificar input contract, output contract, artifacts/refs, estado durable de entrada y salida, condiciones stale/BLOCKED, persistencia e idempotencia. Si su resultado committed exacto ya existe, el resolver reutiliza ese estado y no crea una segunda transición equivalente.

7.2.2 Gate durable Topic → Research

Research no puede comenzar solo porque exista HumanInput. Debe consumir la decisión Topic CURRENT efectiva, obtenida por el binding software-owned existente: `decision_ref`, `decision_checksum` y `source_attempt`, con la cadena original/reevaluaciones revalidada. El binding debe coincidir con episode_id, input Topic, assessment, lineage, profile y checksum del sujeto evaluado; el source attempt más reciente completado sustituye al anterior. Si falta el binding, la cadena es discontinua, el checksum no coincide o la decisión no es vigente, Research no comienza y el resultado es fail-closed. No se crea otro motor Topic ni se duplica su lógica.

7.2.3 Binding Research → B5-I3

`RESEARCH_READY` no se redefine. El bridge obligatorio es: ResearchReadyManifest y `research_v2_b5_i3_handoff` CURRENT, válidos y consumibles según `ResearchV2B5I3Adapter.validate_research_v2_precondition` y sus contratos existentes → capability `B5_I3_NARRATIVE_ARCHITECTURE` → persistencia de `ViewerJourney`, `OpeningDesign`, `ClosingDesign` y `NarrativePlan` mediante el store existente → estado durable `B5_I3_COMPLETE`. `RESEARCH_READY_WITH_LIMITATIONS` solo puede cruzar si sus restricciones están presentes, ligadas y aceptadas por los contratos existentes; `NOT_RESEARCH_READY` no cruza. Deben conservarse episode binding, manifest/checksum, Research lineage, downstream restrictions, profile y `narrative_decisions_not_made` hasta que B5-I3 los produzca. PLAN015 no crea una segunda capability B5-I3 ni convierte Research M7 en ejecutor downstream.

7.2.4 Contratos downstream mínimos

\- **B5-I3 → Writing:** input `B5_I3_VALIDATED_INPUT_SET` con ResearchReadyManifest/handoff, `NarrativePlan`, ThesisArtifact/refined thesis aplicable, `editorial_profile` y `ResearchPack`; output `schemas/script_draft.json` y `schemas/script_version_manifest.json`, con `WORKING_CURRENT` del ScriptDraft. Los cuatro artifacts B5-I3 deben permanecer persistidos y ligados como inputs. Cambios de Research/profile/tesis o checksum ligado invalidan la salida.
\- **Writing → Editor:** input `ScriptDraft` WORKING_CURRENT, `editorial_profile`, brief y ClaimsLedger; output `schemas/edited_script.json`, `schemas/editorial_edit_report.json` y `schemas/script_version_manifest.json`. Todo cambio en ScriptDraft o input upstream deja stale la edición.
\- **Editor → Final Editorial Audit:** input EditedScript WORKING_CURRENT, EditorialEditReport, profile, brief y ClaimsLedger; output `schemas/final_editorial_audit.json`, conservando episode_id, artifact_id, script_version y script_checksum exactos. Falta de cualquier input, cambio de identidad o pérdida de independencia bloquea el paso.
\- **Todos los pasos:** el estado de salida solo se escribe después de validar schema, bindings, lineage y provenance; una salida idéntica ya persistida se recupera idempotentemente y una salida diferente para la misma transición se trata como conflicto/stale, nunca como segunda verdad.

7.3 Paradas legítimas

Pueden detener el E2E:  
\- resultado cognitivo externo pendiente;  
\- decisión humana pendiente;  
\- autorización de coste/proveedor realmente necesaria;  
\- gate editorial BLOCKED;  
\- capability no disponible;  
\- error fail-closed;  
\- finalización.

La parada debe persistirse y ser interpretable desde la superficie normal.

7.4 Reanudación

Cuando la condición pendiente quede satisfecha, reanudar o la operación equivalente debe continuar desde el último estado durable válido.

No se repite cognición ya confirmada y persistida salvo RETRY explícito de esa transición.  
RETRY/REGENERATE generales quedan fuera.

8\. SEMÁNTICA DE COMMIT Y FALLO

Una transición está committed únicamente cuando:  
1\. existe el resultado requerido;  
2\. su contrato está validado;  
3\. el artifact/decision/approval correspondiente está persistido;  
4\. el estado durable reconoce la transición;  
5\. lineage/provenance/bindings críticos están registrados.

Si falla antes del commit, no puede declararse completada.

Si existe evidencia durable suficiente de un resultado válido previo, la recuperación debe reutilizarla y fallar cerrado ante ambigüedad. No se inventa éxito ni se repite cognición a ciegas.

Antes de ejecutar cambios sobre handoff/recovery/anti-replay, el pre-flight debe comprobar si existen defectos vigentes en esas superficies que invaliden esta semántica. Si son separables, permanecen fuera. Si impiden materialmente PLAN015, el agente debe detenerse y elevar el cambio de alcance.

9\. CONTRATO DE AUTORIDAD OPERACIONAL

9.1 Contrato actual y objetivo

El repositorio actual protege ejecución real/controlada mediante MissionAuthorization y execution_preflight.

PLAN015 no autoriza a eliminar ni debilitar MissionAuthorization.

El objetivo es distinguir:  
A. autorización para desarrollar/modificar el repositorio;  
B. madurez/disponibilidad técnica de una capability;  
C. autorización ordinaria para usar una capability ya aprobada dentro del producto.

La operación ordinaria no puede depender exclusivamente de CURRENT_MISSION o de una autorización temporal de desarrollo.

9.2 Propiedades obligatorias de la autoridad ordinaria

La autoridad de producto debe ser:  
\- EXPLÍCITA;  
\- PERSISTENTE;  
\- AUDITABLE;  
\- FAIL-CLOSED;  
\- ACOTADA A CAPABILITY/SCOPE;  
\- REVOCABLE;  
\- NO INFERIDA AUTOMÁTICAMENTE DE IMPLEMENTED;  
\- NO TRANSITIVA A OTRAS CAPABILITIES;  
\- COMPATIBLE CON ROUTING/PERFIL/FAMILIA;  
\- verificable por Software antes de ejecutar.

9.2.1 Contrato machine-readable canónico

PLAN015 establece un registro canónico de autorización ordinaria en `config/product_capability_authorizations.json`, validado por `schemas/product_capability_authorizations.json`. La estructura raíz exacta es `registry_version` y `authorizations[]`; el schema es fail-closed y rechaza campos desconocidos, tipos incompatibles, estados no reconocidos, fechas inválidas, listas vacías donde el scope sea obligatorio y duplicados de `authorization_id` o `authorization_checksum`. Es un registro de autorizaciones, no un subsistema de políticas ni un reemplazo de MissionAuthorization.

Cada autorización debe contener exactamente, además de los campos opcionales indicados, como mínimo: `authorization_id`, `authority_version`, `capability_id`, `allowed_role_ids`, `allowed_execution_families`, `allowed_routes`, `allowed_profiles`, `allowed_interfaces`, `cost_policy`, `authorized_by`, `authorized_role`, `issued_at`, `valid_from`, `valid_until`, `status`, `supersedes`, `revoked_at`, `revoked_by` y `authorization_checksum`. `valid_until`, `supersedes`, `revoked_at`, `revoked_by` y `revocation_reason` pueden ser `null` solo cuando su estado lo permita; `revoked_at`, `revoked_by` y `revocation_reason` son obligatorios para `REVOKED`. Las listas representan scopes cerrados y no se amplían por valores implícitos o comodines no definidos por el schema.

El checksum único de cada autorización es `SHA-256` de su JSON UTF-8 con `sort_keys=true` y `separators=(",", ":")`, excluyendo únicamente `authorization_checksum`. El registro debe conservar el checksum del record utilizado en la request; cualquier diferencia produce stale/tampering y bloqueo.

Los estados del lifecycle son exactamente `ACTIVE`, `SUPERSEDED`, `REVOKED` y `EXPIRED`. Una autorización nueva puede sustituir explícitamente otra mediante `supersedes`; una autorización `SUPERSEDED`, `REVOKED` o `EXPIRED` nunca vuelve a ser efectiva. La emisión, sustitución o revocación pertenece a una identidad OWNER/autorizadora verificable mediante los mecanismos existentes del repositorio; si Software no puede verificarla, debe fallar cerrado. No se crea un registry de identidad adicional.

Para cada ejecución, Software filtra por `capability_id`, role, execution family, route, profile, interface y cost context. El resultado debe ser exactamente una autorización `ACTIVE` compatible y dentro de `valid_from`/`valid_until`: cero coincidencias → `DENY`; una → `ALLOW`; más de una → `CONFLICT/DENY`. No se mezclan scopes de autorizaciones distintas. Requests ordinarios quedan ligados a `authorization_id`, `authority_version` y `authorization_checksum`; una autorización revocada, expirada, reemplazada o cuyo checksum no coincide bloquea ejecución. Reutilizar una autorización válida para la misma ejecución idempotente no crea otra autorización.

El binding de perfil depende de la familia. Para `API_PROVIDER`, `profile_binding` es el `execution_profile` explícito y resoluble, que debe coincidir con `allowed_profiles`. Para `AGENT_HARNESS`, `profile_binding` es literalmente `EXECUTOR_MANAGED`: no se fija provider, model ni execution_profile convencional, y `allowed_profiles` debe contener `EXECUTOR_MANAGED` para autorizar esa modalidad. `NONE_SELECTED` nunca coincide por sí solo y no puede transformarse silenciosamente en una autorización válida. La request y la evidencia persistida deben conservar `execution_family`, `selection_mode`, `profile_binding` y, cuando esté disponible, executor/session identity.

La decisión material de emitir o revocar una autorización ordinaria pertenece al OWNER. En PLAN015, `OWNER APPROVAL` del plan autoriza también materializar exactamente la decisión sucesora de `MD-CI-001` y las product authorities previstas en la matriz de esta sección; no autoriza capabilities, scopes, costes o arquitecturas que no estén enumerados. Software no infiere autorización de `IMPLEMENTED`, `PRODUCT_USE_AUTHORIZED` global ni de otra capability.

PRODUCT_USE_AUTHORIZED global, si existe, no puede convertirse por sí solo en autorización indiscriminada.

Autorizar capability A no puede autorizar capability B salvo relación explícita y canónica.

9.3 Lifecycle de capability

IMPLEMENTED no equivale automáticamente a usable en producto. `ProductCapabilityAuthorization` tampoco convierte automáticamente una capability en `ACTIVE`; la autoridad de producto y la disponibilidad técnica son dimensiones separadas.

El lifecycle de disponibilidad y autoridad se resuelve fail-closed con estas reglas:  
\- `NON_EXECUTABLE_CURRENT`, `SUSPENDED` o `DEPRECATED` → HARD BLOCK, aunque exista cualquier autoridad.  
\- `READY_NOT_AUTHORIZED` sin autoridad válida para el modo solicitado → `DENY`.  
\- `READY_NOT_AUTHORIZED` con `MissionAuthorization` válida y `authorization_mode = MISSION` → permitido únicamente para la ruta mission-bound y sus scopes exactos.  
\- `READY_NOT_AUTHORIZED` con `ProductCapabilityAuthorization` válida y `authorization_mode = PRODUCT` → permitido únicamente para la ruta ordinaria y sus scopes exactos; el registro de capability permanece `READY_NOT_AUTHORIZED`.  
\- `MissionAuthorization` y `ProductCapabilityAuthorization` presentes sin selección inequívoca de modo, o con scopes mezclados → `CONFLICT/DENY`.  
\- `ACTIVE` sin autoridad válida → `DENY` para uso ordinario; `IMPLEMENTED`/`ACTIVE` nunca sustituyen la autorización explícita.  
\- `real_entrypoint_operational = false` → HARD BLOCK técnico hasta que PLAN015 implemente o corrija el entrypoint necesario; no se infiere disponibilidad.

La activación debe ser controlada capability por capability; no se permite promover masivamente `READY_NOT_AUTHORIZED` a `ACTIVE` por conveniencia. La request debe declarar inequívocamente `authorization_mode` y Software no combina scopes entre modos.

La aprobación funcional no es una precondición circular para la primera ejecución de un hito que debe producirla. Para el hito de validación explícitamente vinculado a PLAN015, `OWNER APPROVAL` del plan más una autoridad válida permiten la ejecución necesaria aunque `functional_approval = PENDING`; la request debe estar ligada al hito PLAN015 correspondiente. Después del hito, un resultado `PASS` registra la evidencia/aprobación funcional requerida y un `FAIL` obliga a corregir o dejar `BLOCKED`. La evidencia funcional sigue siendo obligatoria para convergencia, activación posterior y cierre; esta excepción no autoriza uso general sin evidencia.

9.3.1 Matriz capability → authority para PLAN015

\- `TOPIC_BELONGING_ASSESSMENT` → product capability authorization para operación ordinaria únicamente después de una decisión material sucesora que haga `supersede MD-CI-001`; MissionAuthorization sigue válida para la ruta controlada/mission-bound.  
\- EXTEND_01_RESEARCH_V2_REAL_E2E → product capability authorization para operación ordinaria; debe respetar además cost_policy y familia/ruta/perfil seleccionados.  
\- B5_I3_NARRATIVE_ARCHITECTURE → product capability authorization.  
\- PLAN013_WRITING_SCRIPT_DRAFT → product capability authorization.  
\- PLAN013_EDITOR_EDITED_SCRIPT → product capability authorization.  
\- PLAN013_FINAL_EDITORIAL_AUDIT → product capability authorization.  
\- FinalScriptReview → NO requiere product capability authorization separada: se mantiene como validación determinista software-owned sobre inputs ya autorizados y persistidos.  
\- EditorialScriptApproval → NO se autoriza mediante product capability authorization: exige decisión humana válida y APPROVER_REGISTRY/roles permitidos.

`MVP_REAL_E2E_TOPIC_BELONGING` queda preservada como ruta histórica/mission-bound y no puede ser seleccionada como authority ordinaria de PLAN015. La decisión material sucesora de `MD-CI-001` debe ser aprobada por OWNER antes de materializar la autoridad ordinaria, debe conservar el registro histórico y debe declarar expresamente el alcance de uso ordinario. HF-01 valida esa decisión y la autoridad ya concedida; no crea, sustituye ni hace efectiva por primera vez la autorización. Si HF-01 falla, el uso ordinario queda bloqueado, la autoridad se revoca o se impide su ejecución y PLAN015 no puede cerrarse.

La resolución de la decisión material es específica del modo de autorización: `authorization_mode = MISSION` conserva la referencia/binding vigente de `MD-CI-001` para no invalidar MissionAuthorization ni sus contratos históricos; `authorization_mode = PRODUCT` debe validar la decisión sucesora de `MD-CI-001` y su checksum junto con la product authority. No se reemplaza globalmente la referencia histórica compartida si eso rompe la ruta mission-bound. Si el runtime actual solo permite una referencia global, PLAN015 debe introducir la extensión mínima de resolución por modo o detenerse; nunca debe aceptar una autoridad de un modo para completar el otro.

La autorización de una fila no autoriza ninguna otra. Para cada capability, el preflight debe comprobar también registry/madurez/disponibilidad, routing, role, execution family, execution profile e interface aplicables.

9.4 Reutilización

La implementación debe inspeccionar primero capability_registry, execution_preflight, autoridad viva, perfiles, routing y mecanismos existentes de product-use.  
Se prefiere extensión mínima.  
Un nuevo subsistema de políticas requiere STOP \+ OWNER DECISION.

9.5 Compatibilidad

La ruta mission-bound debe seguir funcionando para los casos que legítimamente la usan.

Precedencia: una ejecución explícitamente mission-bound usa MissionAuthorization y sus bindings vigentes; una ejecución ordinaria del producto usa product capability authorization. No se mezclan ambas autoridades para completar artificialmente scopes faltantes. Si una request declara/deriva ambos modos de forma incompatible, fail-closed.

10\. ROUNDTRIP AGENT_HARNESS

Si AGENT_HARNESS está seleccionado, esperar al harness puede ser LEGITIMATE_STOP.

No se permite que para continuar el usuario deba:  
\- localizar IDs internos manualmente;  
\- mover archivos por rutas técnicas no expuestas;  
\- invocar importaciones especializadas que exijan conocimiento interno;  
\- reconstruir bindings/checksums persistidos.

La interfaz normal debe:  
\- mostrar que existe resultado externo pendiente;  
\- aceptar o descubrir el resultado de forma ligada al episodio/handoff correcto;  
\- permitir como UX normal que el usuario seleccione/aporte el archivo externo recibido; no es obligatorio crear un inbox automático;  
\- validar con los mecanismos existentes;  
\- continuar desde estado durable.

La normalización de UX no puede rebajar garantías. Deben preservarse, o existir equivalentes fuertes de:  
\- episode binding;  
\- capability/scope binding;  
\- handoff/request identity;  
\- checksums;  
\- anti-replay;  
\- provenance;  
\- autoridad válida.

Al seleccionar/aportar un archivo, Software debe descubrir episode_id/handoff_id desde el payload, resolver el handoff pendiente correspondiente y validar automáticamente bindings, checksum, authority, freshness y anti-replay. Un resultado de otro episodio/handoff, stale, ya consumido o emitido bajo autoridad retirada se rechaza. Tras importación válida debe quedar una disposición durable CONSUMED/IMPORTED que impida replay; no se exige al usuario mover archivos a rutas internas del Vault.

11\. CONVERGENCIA DE VALIDACIONES DEL GUIÓN FINAL

Antes de EDITORIAL_SCRIPT_APPROVED deben converger todas las validaciones obligatorias exigidas por los contratos canónicos del producto.

En PLAN015 el conjunto obligatorio de cierre se compone de `FinalEditorialAudit` para calidad editorial, identidad del canal, factualidad/interpretación/fidelidad y trazabilidad de las afirmaciones, y `FinalScriptReview` para la adecuación textual a YouTube y sus sensores contractuales. Cada artifact debe conservar el mismo `artifact_id`, `script_version` y `script_checksum`; no se puede omitir uno por considerar que otro lo cubre.

Ninguna validación sustituye a otra.

Todas deben referirse al mismo:  
\- artifact_id;  
\- script_version;  
\- script_checksum.

Si una validación obligatoria falta, está stale, apunta a otra versión/checksum o queda BLOCKED, el cierre debe fallar cerrado.

PLAN015 no obliga a crear nuevos agentes si las capacidades y contratos ya existen; debe reutilizar los mecanismos canónicos.

11.1 FinalScriptReview

PLAN015 decide conservar FinalScriptReview como validación determinista software-owned, no como capability cognitiva nueva. Debe construirse con el contrato existente, validar identidad exacta del script, checksum del FinalEditorialAudit, perfil activo e independencia de runs/actores, y persistirse de forma trazable antes de solicitar aprobación humana.

11.2 Regla mecanizable de WARN

Para PLAN015 se preserva la semántica vigente sin inventar una categoría abstracta de “critical”: `FinalEditorialAudit` es elegible únicamente si su `decision` top-level es `PASS` o `WARN`, `independence_result = PASS`, todos los bindings/schema exigidos son válidos y ninguna dimensión obligatoria tiene `BLOCK` o `REQUEST_CHANGES`. `FAIL` o `BLOCKED` no cierran. `FinalScriptReview` es elegible únicamente con `decision = PASS` o `WARN` y bindings/schema válidos; `BLOCKED` no cierra. Software aplica esta regla directamente al artifact persistido; no interpreta texto libre ni infiere severidad. Cambiar esta semántica requiere decisión material separada.

12\. DECISIÓN HUMANA Y APROBACIÓN CANÓNICA

La interacción final debe reutilizar HumanDecisionRequest/HumanDecision o el mecanismo vigente para obtener una respuesta humana explícita.

La solicitud debe estar ligada exactamente a:  
\- episode_id;  
\- artifact_id;  
\- script_version;  
\- script_checksum;  
\- expected_actor_ref;  
\- expected_approval_role;  
\- actor/canal cuando aplique.

Contrato obligatorio:  
HumanDecisionRequest exacto  
→ respuesta humana explícita  
→ Software valida request/bindings/actor/checksum  
→ Software materializa EditorialScriptApproval canónico  
→ closure.

HumanDecision no se trata automáticamente como EditorialScriptApproval.

El mapper es software-owned y debe reutilizar `APPROVER_REGISTRY` y `validate_editorial_script_approval`. El `HumanDecisionRequest` de aprobación debe incluir explícitamente `expected_actor_ref` y `expected_approval_role`; ambos deben conservarse en el checksum del request. Para `APPROVE`, solo se acepta `actor_ref == expected_actor_ref`, `expected_approval_role` permitido para `EDITORIAL_SCRIPT_APPROVAL`, actor activo registrado con ese rol y canal esperado cuando se haya fijado. Si el actor tiene varios roles elegibles pero el request no identifica inequívocamente uno, se falla cerrado. `local-user` por defecto no es suficiente. Software deriva `approved_by` del actor validado, `approved_role` del rol esperado validado, `approved_at` del evento validado y copia artifact_id/script_version/checksum exclusivamente del subject CURRENT del request ligado al guion exacto.

Mapeo mínimo:  
\- APPROVE válido → EditorialScriptApproval.decision \= APPROVED.  
\- CORRECT → no crea aprobación APPROVED; retorna a REQUEST_CHANGES/IN_REVIEW con la corrección persistida.  
\- REJECT → no crea aprobación APPROVED; registra rechazo y bloquea closure.  
\- CANCEL → no crea aprobación y mantiene/cierra la interacción según contrato sin inferir rechazo editorial.  
\- SELECT_ALTERNATIVE no es una acción válida para aprobar el guion final salvo que exista una alternativa explícitamente incluida en el request y el producto defina su identidad exacta; en ausencia de ello, fail-closed.

El artifact `EditorialScriptApproval` completo debe validarse con schema y `validate_editorial_script_approval`, persistirse con su referencia y checksum, y ser el input vinculante de `record_plan013_editorial_closure`; el objeto reducido `human_approval` no basta. Request_id, request_checksum, episode_id, subject_ref, subject_version, subject_checksum, actor, role o canal inválidos/stale deben producir fallo cerrado y ninguna aprobación canónica.

La IA nunca infiere aprobación.

Si versión/checksum cambian, la aprobación previa queda stale/inválida según la semántica existente.

13\. ENTREGA CURRENT

Debe existir una única identidad CURRENT por episodio aprobado, vinculada a artifact/version/checksum exactos.

Se preserva historia.

Puede existir:  
canónico estructurado  
\+  
materialización humana visible  
si ambos quedan inequívocamente vinculados a la misma identidad.

El usuario debe localizar CURRENT desde la superficie normal sin inspeccionar registros técnicos.

Invariantes observables:  
UNIQUE_CURRENT_POINTER \= PASS  
NO_MULTIPLE_CURRENT_DECLARATIONS \= PASS  
HISTORY_PRESERVED \= YES

Una nueva versión debe invalidar o retirar la condición CURRENT anterior según contratos vigentes; nunca pueden coexistir dos versiones declaradas CURRENT del mismo episodio.

13.1 Autoridad canónica CURRENT

PLAN015 separa `WORKING_CURRENT` de `APPROVED_CURRENT`. `episode_state.current_script` puede continuar representando el script de trabajo vigente que el runtime necesita; no equivale a un guion aprobado. `workflow_state` e índice deben conservar esa semántica si exponen `current_script`. Después de un closure válido debe existir además una referencia inequívoca `approved_current` por episodio con exactamente `artifact_id`, `script_version` y `checksum` del guion aprobado. Solo puede existir un `APPROVED_CURRENT` por episodio y su referencia debe coincidir con closure, approval y artifact persistido.

`plan013_script_versions.json` conserva historial de versiones mediante sus nombres canónicos actuales, incluido `script_artifact_id`, `script_version` y `script_checksum`. En esta estructura `script_artifact_id` es el `artifact_id` del puntero `approved_current`; no se introduce un segundo nombre para la misma identidad. Exactamente una entrada aprobada puede representar `APPROVED_CURRENT`; si el registro usa un estado de puntero, su valor debe coincidir con `approved_current`. Una nueva versión de trabajo no retira automáticamente el APPROVED_CURRENT anterior: lo deja histórico hasta que exista una nueva aprobación/closure válida. Cuando una nueva versión aprobada sustituye la anterior, la actualización del puntero aprobado y la clasificación de la versión anterior como `SUPERSEDED` o `HISTORICAL` debe ser determinista y atómica.

13.2 Legado ambiguo

Si al activar PLAN015 existen múltiples entradas históricas marcadas CURRENT, Software puede normalizarlas únicamente cuando `episode_state.current_script` o `approved_current` y un closure aprobado identifican inequívocamente una versión exacta; esa versión permanece en el estado que corresponda y las demás pasan a `SUPERSEDED`/`HISTORICAL` preservando sus datos. Si falta el puntero, no existe closure aprobada, ninguna entrada coincide exactamente o más de una coincide de forma ambigua, se falla cerrado y se exige reparación explícita: nunca se elige “la última” por conveniencia.

La superficie normal debe ofrecer lectura/consulta de CURRENT por episode_id sin exigir inspección manual del Vault.

14\. INTERFAZ OPERATIVA

Contrato observable mínimo:  
\- iniciar crea episodio y avanza hasta LEGITIMATE_STOP o final;  
\- reanudar \<episode_id\> carga estado durable y continúa hasta el siguiente stop/final;  
\- la decisión humana se solicita/acepta desde la interacción normal;  
\- un resultado externo pendiente se presenta e incorpora sin conocimiento interno;  
\- al completar se informa EDITORIAL_SCRIPT_APPROVED y la referencia CURRENT visible.

Los nombres exactos de comandos pueden conservarse o evolucionar compatible. La semántica es obligatoria.

15\. REUTILIZACIÓN OBLIGATORIA

Debe intentarse reutilizar antes de crear alternativas:  
\- EpisodeApplicationService;  
\- VaultEpisodeStore;  
\- episode_state/workflow_state;  
\- Topic Belonging;  
\- Research canónico;  
\- B5-I3 y contracts downstream;  
\- ai.execution / runtime profiles / Cognitive Port;  
\- capability_registry y routing;  
\- execution_preflight;  
\- HumanDecisionRequest/HumanDecision;  
\- contracts de aprobación editorial existentes;  
\- plan013_script_coordinator solo para su función real;  
\- record_plan013_editorial_closure;  
\- current_script/versionado/stale;  
\- handoff/import/recovery externos.

Duplicar estas capacidades sin incompatibilidad material demostrada es fallo del plan.

16\. HITOS FUNCIONALES

Los hitos no son misiones ni requieren aprobación separada. Son puntos de verificación antes de construir encima.

HF-01 — Continuidad \+ autoridad  
Debe demostrar:  
\- superficie normal → Topic → Research;  
\- autoridad ordinaria correcta;  
\- MissionAuthorization preservada donde corresponde;  
\- LEGITIMATE_STOP persistido;  
\- reanudación;  
\- no replay.

No continuar con integración downstream si HF-01 no pasa.

HF-02 — Cadena editorial downstream  
Debe demostrar:  
\- RESEARCH_READY → B5-I3 → Writing → Editor;  
\- todas las validaciones obligatorias convergen sobre artifact/version/checksum exactos;  
\- no existe ensamblaje técnico manual del operador.

No continuar al cierre final si HF-02 no pasa.

HF-03 — Producto completo  
Debe demostrar:  
\- decisión humana exacta;  
\- EditorialScriptApproval materializado por Software;  
\- closure;  
\- CURRENT único;  
\- E2E representativo desde superficie normal.

17\. PRE-FLIGHT DE EJECUCIÓN

17.1 PRE-FLIGHT INICIAL — antes de modificar código

Después de OWNER APPROVAL y de registrar PLAN015 como autoridad activa, pero antes de modificar código, el agente debe confirmar:  
\- HEAD y working tree esperados;  
\- autoridad temporal previa reconciliada o disposición autorizada para reconciliarla;  
\- PLAN015 activo y scope coherente;  
\- decisión material sucesora de `MD-CI-001`, OWNER grant/intención de activar Topic ordinario y capabilities que se pretende autorizar;  
\- capabilities, contracts, routing, perfiles y superficies compartidas localizables;  
\- ausencia de drift material no auditado;  
\- tests focales identificados;  
\- defectos vigentes en handoff/recovery/commit que puedan bloquear el plan;  
\- Vault y directorios del episodio accesibles y escribibles, y lock operativo;  
\- fuentes de inventario y ubicación/mecanismo de handoff externo accesibles;  
\- familia de ejecución seleccionada y executor/harness disponible;  
\- para `API_PROVIDER`, execution_profile previsto, explícito y resoluble para cada rol cognitivo; para `AGENT_HARNESS`, `selection_mode=EXECUTOR_MANAGED` previsto y compatible con `allowed_profiles`;  
\- credenciales/configuración externa requeridas disponibles sin persistir secretos en el repositorio;  
\- cost_policy resuelta; cualquier ruta/coste que requiera ASK_OWNER debe poseer aprobación explícita antes de la validación live.

Este pre-flight inicial no exige que `product_capability_authorizations.json`, su schema o su consumidor ya estén implementados ni que exista todavía una autorización `ACTIVE`; exige que la decisión OWNER y el alcance previsto estén definidos para materializarlos. Si descubre un cambio material de arquitectura, alcance o contrato, STOP.

17.2 PRE-FLIGHT POST-MATERIALIZACIÓN — antes de HF-01

Después de materializar el registry, schema y consumo de autoridad ordinaria, pero antes de ejecutar HF-01, Software debe confirmar:  
\- registry raíz y cada authorization cumplen el schema fail-closed;  
\- `authorization_checksum` y checksum de la request coinciden con la serialización canónica;  
\- existe exactamente una autorización `ACTIVE` compatible para cada capability/role/family/route/profile-binding/interface/cost context requerido; cero coincidencias bloquea y más de una produce `CONFLICT/DENY`;  
\- `TOPIC_BELONGING_ASSESSMENT` está respaldada por la decisión sucesora de `MD-CI-001` y no por `MVP_REAL_E2E_TOPIC_BELONGING`;  
\- `API_PROVIDER` compara execution_profile explícito y `AGENT_HARNESS` compara `EXECUTOR_MANAGED`; `NONE_SELECTED` no pasa;  
\- `NON_EXECUTABLE_CURRENT`, `SUSPENDED`, `DEPRECATED` y `real_entrypoint_operational=false` permanecen bloqueadas; `READY_NOT_AUTHORIZED` solo se bloquea si falta la autoridad válida del modo declarado, y no se promueve automáticamente a `ACTIVE`;  
\- `functional_approval=PENDING` solo se admite para la primera ejecución del hito PLAN015 explícitamente ligado a producir esa evidencia; no se admite como uso ordinario posterior sin el resultado funcional requerido;  
\- routing, role, family, profile-binding, interface, cost policy y autoridad son coherentes;  
\- MissionAuthorization continúa separado para la ruta mission-bound.

Este pre-flight habilita la ejecución de HF-01, pero no sustituye HF-01 ni convierte una comprobación de configuración en evidencia funcional. Si falla, no se ejecuta HF-01 y el estado es BLOCKED.

18\. ESTRATEGIA DE PRUEBAS PROPORCIONAL

No ejecutar suite completa tras cada microcambio.

Evidencia focal mínima:  
\- resolución de próxima transición desde estados representativos;  
\- Topic STOP → Research;  
\- decisión M4 → continuación sin replay;  
\- RESEARCH_READY → B5-I3;  
\- B5-I3 → Writing → Editor → validaciones;  
\- materialización de aprobación canónica desde decisión humana;  
\- aprobación → closure;  
\- closure → CURRENT único;  
\- nueva versión → CURRENT/approval anterior deja de estar vigente;  
\- authority válida permite solo su capability/scope;  
\- ausencia/invalidación de authority bloquea;  
\- capability A autorizada no autoriza B;  
\- MissionAuthorization sigue funcionando donde corresponde;  
\- AGENT_HARNESS roundtrip normalizado preserva bindings/anti-replay/checksums.

Integración offline/sintética:  
HumanInput → EDITORIAL_SCRIPT_APPROVED/CURRENT  
con cognición fake permitida, pero sin monkeypatch de composición, persistencia, autoridad operacional, decisiones, validaciones, closure o CURRENT.

Regresiones:  
solo las superficies afectadas por la diff y sus contratos.

18.1 Matriz criterio → evidencia

El plan exige trazabilidad por criterio sin fijar nombres rígidos de archivos de test. Cada fila enumera explícitamente los criterios que cubre y exige evidencia automatizada negativa cuando el criterio sea de bloqueo:

\- `E2E_NORMAL_SURFACE`, `NEXT_VALID_TRANSITION_FROM_DURABLE_STATE`, `E2E_TRANSITION_MATRIX_ENFORCED` → integración sobre estados representativos, stops, reanudación y observación live desde `iniciar`/`reanudar`.  
\- `TOPIC_TO_RESEARCH`, `TOPIC_CURRENT_GATE_TO_RESEARCH` → APPROVE positivo y REQUEST_MORE_EVIDENCE, ESCALATE_TO_OWNER, BLOCK, REJECT, stale y cadena de reevaluación inválida negativos, más E2E live.  
\- `RESEARCH_TO_B5_I3`, `RESEARCH_READY_BOUND_TO_EXISTING_B5_I3_CAPABILITY`, `DOWNSTREAM_EDITORIAL_CHAIN` → ResearchReadyManifest/handoff, cuatro artifacts B5-I3, Writing, Editor y sus contratos/bindings, con stale/BLOCKED negativos y E2E live.  
\- `PRODUCT_AUTHORITY_MACHINE_READABLE`, `PRODUCT_AUTHORITY_EXPLICIT`, `PRODUCT_AUTHORITY_FAIL_CLOSED`, `PRODUCT_AUTHORITY_REQUEST_BINDING_AND_STALE` → schema, checksum, selección 0/1/>1, vigencia, revocación, supersede, emisor no verificable y request stale.  
\- `PRODUCT_AUTHORITY_SCOPE_ISOLATION`, `PRODUCT_AUTHORITY_NON_TRANSITIVE`, `IMPLEMENTED_DOES_NOT_IMPLY_PRODUCT_AUTHORIZED`, `MISSION_AUTHORIZATION_PRESERVED_FOR_CONTROLLED_USE`, `PRODUCT_OPERATION_DEPENDS_EXCLUSIVELY_ON_CURRENT_MISSION`, `CAPABILITY_AUTHORIZATION_LIFECYCLE`, `READY_NOT_AUTHORIZED_MODE_SEMANTICS`, `FUNCTIONAL_APPROVAL_NOT_CIRCULAR`, `PRODUCT_MODE_MATERIAL_DECISION_BINDING`, `MISSION_MODE_MATERIAL_DECISION_PRESERVED` → capabilities A/B, scopes incompatibles, `READY_NOT_AUTHORIZED` con modo MISSION/PRODUCT, estados no ejecutables, decisión material sucesora y decisión histórica por modo, autoridad ordinaria y mission-bound en pruebas separadas, y primer hito con aprobación funcional pendiente que produce su propia evidencia.  
\- `AGENT_HARNESS_AUTHORITY_BINDINGS_PRESERVED`, `AGENT_HARNESS_ROUNDTRIP_NORMALIZED` → archivo seleccionado, `EXECUTOR_MANAGED`, bindings válidos, wrong-episode/stale/replay/autoridad retirada negativos y roundtrip live cuando la familia esté seleccionada.  
\- `MANDATORY_FINAL_VALIDATIONS_CONVERGED`, `MANDATORY_VALIDATIONS_SAME_ARTIFACT_VERSION_CHECKSUM`, `FINAL_WARN_RULE_MECHANIZABLE`, `FINAL_APPROVAL_BOUND_TO_EXACT_SCRIPT` → FinalEditorialAudit y FinalScriptReview sobre identidad exacta, WARN con dimensión BLOCK/REQUEST_CHANGES negativo, FAIL/BLOCKED negativo y stale negativo.  
\- `HUMAN_DECISION_TO_CANONICAL_APPROVAL`, `EDITORIAL_SCRIPT_APPROVED`, `APPROVER_REGISTRY_REUSED` → request con actor/role esperado, aprobación completa validada y actor/role/request/checksum inválidos negativos, seguido de closure.  
\- `UNIQUE_CURRENT_POINTER`, `NO_MULTIPLE_CURRENT_DECLARATIONS`, `CURRENT_LEGACY_AMBIGUITY_FAIL_CLOSED`, `HISTORY_PRESERVED` → working versus approved current, nueva aprobación, supersede histórico, legado ambiguo fail-closed y consulta normal CURRENT.  
\- `REAL_EXECUTION_PROFILES_RESOLVED`, `CAPABILITY_TECHNICAL_AVAILABILITY_PRESERVED`, `REAL_ENTRYPOINT_OPERATIONAL_REQUIRED` → API profile resoluble, AGENT_HARNESS executor-managed explícito, capability no operacional y dependencias live ausentes; `real_entrypoint_operational=false` produce HARD BLOCK.  
\- `SOFTWARE_IA_SOFTWARE_INVARIANT`, `PRODUCER_EDITOR_AUDITOR_INDEPENDENCE`, `NO_SECOND_EDITORIAL_SOURCE_OF_TRUTH`, `NO_NEW_CHECKPOINT_STORE_WITHOUT_OWNER_DECISION`, `NO_PARALLEL_RESEARCH_ENGINE`, `NO_UNAUTHORIZED_SCOPE_EXPANSION` → inspección de artifacts, provenance, actores/runs, fuentes de verdad, diff y evidencia de no introducción de capas prohibidas.  
\- `NO_AMBIGUOUS_MISSION_BOUND_HANDOFFS_AT_ACTIVATION` → inventario de todas las fuentes declaradas, disposiciones CONSUMED/CANCELLED/ARCHIVED y assertions `AMBIGUOUS_HANDOFFS=0` y `PENDING_OLD_MISSION_HANDOFFS=0`.

Evidencia live/real:  
antes del cierre debe demostrarse al menos un episodio mediante superficie normal y familia operativa seleccionada.  
Si falta autorización/coste/servicio externo, no se inventa PASS: queda READY_FOR_LIVE_VALIDATION o estado canónico equivalente.

19\. CRITERIOS DE ACEPTACIÓN

E2E_NORMAL_SURFACE \= PASS  
NEXT_VALID_TRANSITION_FROM_DURABLE_STATE \= PASS  
TOPIC_TO_RESEARCH \= PASS  
RESEARCH_TO_B5_I3 \= PASS  
DOWNSTREAM_EDITORIAL_CHAIN \= PASS  
MANDATORY_FINAL_VALIDATIONS_CONVERGED \= PASS  
MANDATORY_VALIDATIONS_SAME_ARTIFACT_VERSION_CHECKSUM \= PASS  
HUMAN_DECISION_TO_CANONICAL_APPROVAL \= PASS  
FINAL_APPROVAL_BOUND_TO_EXACT_SCRIPT \= PASS  
EDITORIAL_SCRIPT_APPROVED \= PASS  
UNIQUE_CURRENT_POINTER \= PASS  
NO_MULTIPLE_CURRENT_DECLARATIONS \= PASS  
HISTORY_PRESERVED \= YES  
VALID_COGNITIVE_WORK_REPLAYED_UNNECESSARILY \= NO  
PRODUCT_OPERATION_DEPENDS_EXCLUSIVELY_ON_CURRENT_MISSION \= NO  
PRODUCT_AUTHORITY_EXPLICIT \= PASS  
PRODUCT_AUTHORITY_FAIL_CLOSED \= PASS  
PRODUCT_AUTHORITY_SCOPE_ISOLATION \= PASS  
PRODUCT_AUTHORITY_NON_TRANSITIVE \= PASS  
IMPLEMENTED_DOES_NOT_IMPLY_PRODUCT_AUTHORIZED \= PASS  
CAPABILITY_AUTHORIZATION_LIFECYCLE \= PASS  
READY_NOT_AUTHORIZED_MODE_SEMANTICS \= PASS  
FUNCTIONAL_APPROVAL_NOT_CIRCULAR \= PASS  
PRODUCT_MODE_MATERIAL_DECISION_BINDING \= PASS  
MISSION_MODE_MATERIAL_DECISION_PRESERVED \= PASS  
MISSION_AUTHORIZATION_PRESERVED_FOR_CONTROLLED_USE \= YES  
CAPABILITY_TECHNICAL_AVAILABILITY_PRESERVED \= YES  
REAL_ENTRYPOINT_OPERATIONAL_REQUIRED \= PASS  
AGENT_HARNESS_AUTHORITY_BINDINGS_PRESERVED \= PASS  
AGENT_HARNESS_ROUNDTRIP_NORMALIZED \= PASS  
E2E_TRANSITION_MATRIX_ENFORCED \= PASS  
TOPIC_CURRENT_GATE_TO_RESEARCH \= PASS  
RESEARCH_READY_BOUND_TO_EXISTING_B5_I3_CAPABILITY \= PASS  
PRODUCT_AUTHORITY_MACHINE_READABLE \= PASS  
PRODUCT_AUTHORITY_REQUEST_BINDING_AND_STALE \= PASS  
NO_AMBIGUOUS_MISSION_BOUND_HANDOFFS_AT_ACTIVATION \= PASS  
FINAL_SCRIPT_REVIEW_SOFTWARE_OWNED \= PASS  
FINAL_WARN_RULE_MECHANIZABLE \= PASS  
APPROVER_REGISTRY_REUSED \= YES  
CURRENT_LEGACY_AMBIGUITY_FAIL_CLOSED \= PASS  
REAL_EXECUTION_PROFILES_RESOLVED \= PASS  
ACCEPTANCE_EVIDENCE_TRACEABILITY \= PASS  
SOFTWARE_IA_SOFTWARE_INVARIANT \= PASS  
PRODUCER_EDITOR_AUDITOR_INDEPENDENCE \= PASS  
NO_SECOND_EDITORIAL_SOURCE_OF_TRUTH \= PASS  
NO_NEW_CHECKPOINT_STORE_WITHOUT_OWNER_DECISION \= YES  
NO_PARALLEL_RESEARCH_ENGINE \= YES  
NO_UNAUTHORIZED_SCOPE_EXPANSION \= YES

20\. STOP CONDITIONS

Detener y reportar BLOCKED si cumplir PLAN015 exige materialmente:  
\- cambiar la tesis del producto;  
\- crear una segunda fuente de verdad editorial;  
\- sustituir Cognitive Port/runtime sin incompatibilidad demostrada;  
\- crear nueva base de datos/checkpoint store/framework;  
\- eliminar o debilitar MissionAuthorization/preflight;  
\- autorizar globalmente capabilities READY_NOT_AUTHORIZED;  
\- cambiar schemas canónicos de forma incompatible no prevista;  
\- reescribir Research como motor nuevo;  
\- introducir multi-episodio;  
\- ampliar a RETRY/REGENERATE general;  
\- saltar una validación obligatoria del cierre;  
\- reducir bindings/anti-replay del harness;  
\- aceptar resultado no verificable como éxito;  
\- modificar una decisión material de producto necesaria para continuar.

Defectos locales necesarios para cumplir el contrato pueden corregirse si no cambian objetivo, arquitectura protegida ni alcance.

21\. GOBERNANZA Y EJECUCIÓN

Estado actual del documento: IN_PROGRESS. OWNER APPROVAL: APPROVED. IMPLEMENTATION_AUTHORIZED: YES. La auditoría previa del PLAN permanece PASS, pero la auditoría independiente final de IMPLEMENTACIÓN es FAIL_WITH_MATERIAL_FINDINGS; por tanto continúan correcciones focales dentro de PLAN015. IMPLEMENTATION_SELF_VERIFICATION: PASS (evidencia del implementador, no cierre). FINAL_INDEPENDENT_AUDIT: FAIL_WITH_MATERIAL_FINDINGS. OWNER_ACCEPTANCE: PENDING. HF-03 permanece NOT_FULLY_DEMONSTRATED hasta demostrar el E2E representativo exigido. La autorización de producto permanece separada y sujeta a las autoridades previstas por este plan.

Secuencia requerida:  
1\. materializar el plan candidato bajo su ruta canónica;  
2\. auditarlo contra HEAD real;  
3\. corregirlo si procede;  
4\. OWNER APPROVAL;  
5\. reconciliar autoridad previa y registrar PLAN015 como CURRENT_PLAN/autoridad vigente según canon;  
6\. PRE-FLIGHT INICIAL;  
7\. ejecución integrada con autonomía técnica dentro del plan, incluyendo la materialización del registry/schema/consumidor de autoridad ordinaria;  
8\. PRE-FLIGHT POST-MATERIALIZACIÓN;  
9\. verificación por HF-01, HF-02 y HF-03;  
10\. auto-verificación;  
11\. READY_FOR_FINAL_INDEPENDENT_AUDIT;  
12\. auditoría independiente contra PLAN \+ diff \+ tests \+ evidencia observable;  
13\. correcciones focales si proceden;  
14\. OWNER ACCEPTANCE;  
15\. cierre canónico.

No se copia el plan completo al estado operativo. El estado solo referencia el plan activo y autorizado.

22\. CIERRE

Al cerrar PLAN015:  
\- el repositorio registra PLAN015 como CLOSED/ACCEPTED según su canon;  
\- CURRENT_PLAN vuelve a NONE salvo nueva autorización explícita;  
\- EXECUTION_AUTHORIZED vuelve a NO salvo nueva autorización explícita;  
\- la autoridad temporal previa no reaparece implícitamente;  
\- la evidencia final conserva pruebas ejecutadas, hitos y validación live/manual necesaria;  
\- Git/repositorio son la autoridad canónica.

PLAN016 no se activa automáticamente por el cierre de PLAN015.
