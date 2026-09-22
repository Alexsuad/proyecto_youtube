PLAN016 — OPERACIÓN MULTI-EPISODIO MÍNIMA

Versión del plan: 0.5.0
Estado: PREAPPROVED_CONDITIONAL
Baseline de diseño: e6885736e300e7d1543759b577d16a39eb3925be
Ruta canónica materializada en repositorio: plans/plan_016/PLAN016_Operación_multi-episodio_mínima.md
OWNER_PREAPPROVAL: APPROVED
FINAL_OWNER_APPROVAL: PENDING_PLAN015_CLOSED_AND_POST_PLAN015_DRIFT_AUDIT
Ejecución autorizada: NO
Producto autorizado por este documento: NO
Readiness documental: STATIC_AUDIT_PASS_PENDING_POST_PLAN015_DRIFT_AUDIT
Dependencia de activación: PLAN016 puede auditarse, documentarse y recibir preaprobación condicionada mientras PLAN015 se ejecuta. La aprobación final y cualquier ejecución de PLAN016 requieren PLAN015 CLOSED/ACCEPTED y una reauditoría focal contra el HEAD post-PLAN015.

1\. DECISIÓN DE DIRECCIÓN

PLAN016 resuelve una restricción operacional concreta: el almacenamiento actual rechaza crear un nuevo episodio cuando ya existe un episodio con estado `en_progreso`.

La restricción no impide demostrar un único E2E completo, por lo que se mantiene separada de PLAN015. Sí limita una operación cotidiana razonable: un episodio puede quedar detenido legítimamente esperando un resultado externo, una decisión humana, un gate o una autorización, y esa espera no debe monopolizar todo el producto.

PLAN016 define únicamente el mínimo necesario para coexistencia, descubribilidad, selección y reanudación segura de varios episodios de producto abiertos.

No crea scheduler, dashboard completo, prioridades, workers concurrentes, colas ni lifecycle avanzado.

2\. ESTADO INICIAL Y DRIFT OBLIGATORIO

En la baseline de diseño, `VaultEpisodeStore._create_episode_locked()` inspecciona el índice y bloquea una nueva creación si existe cualquier entrada con `estado == "en_progreso"`.

La asignación de episode_id y la actualización del índice ya utilizan protección de índice y escritura atómica. El repositorio ya usa episode_id como identidad raíz y persistencia separada por episodio.

El problema no es ausencia de identidad ni de almacenamiento aislado. Es un guard global que convierte la existencia de cualquier episodio abierto en bloqueo para todos los nuevos episodios.

Hechos verificados en esta baseline que condicionan el diseño:
- `_create_episode_locked()` tiene dos callers directos: `create_episode()` y `create_legacy_episode()`; retirar el guard de forma global cambiaría también el wrapper legacy.
- la CLI normal dispone de `iniciar` y `reanudar <episode_id>`, pero no dispone de una superficie normal de descubrimiento/listado de episodios abiertos.
- `VaultEpisodeStore._entry()` selecciona actualmente la primera coincidencia de `episode_id`; PLAN016 debe convertir una duplicidad de identidad en error fail-closed, nunca en selección silenciosa.
- el cierre legacy sin `--ep-id` ya falla cerrado cuando existen cero o múltiples candidatos `en_progreso`; esa propiedad debe preservarse.
- `gate0_integridad` trata episodios `en_progreso` como warnings y no como un bloqueo de unicidad; no necesita redefinirse salvo drift material.

La auditoría estática y las correcciones documentales de PLAN016 pueden completarse mientras PLAN015 se ejecuta. PLAN016 no puede recibir OWNER APPROVAL definitivo ni entrar en ejecución hasta que PLAN015 haya cerrado y se haya ejecutado la reauditoría focal de drift.

Secuencia obligatoria previa a aprobación:
PLAN015 CLOSED/ACCEPTED
→ obtener HEAD post-PLAN015
→ comparar superficies compartidas
→ reauditar focalmente storage/service/CLI/lifecycle afectados
→ corregir PLAN016 si cambió algún supuesto material
→ OWNER APPROVAL PLAN016.

No se repite una auditoría completa si el drift no afecta los contratos de PLAN016.

3\. RESULTADO OBLIGATORIO

Al terminar PLAN016, el producto debe permitir como mínimo:
- crear un nuevo episodio de producto aunque otro episodio de producto permanezca abierto o detenido legítimamente;
- mantener estado, artifacts, decisiones, handoffs, approvals, versiones, WORKING_CURRENT, APPROVED_CURRENT y closure aislados por episode_id;
- identificar desde la superficie normal qué episodios pueden continuarse;
- reanudar explícitamente el episodio elegido sin inspeccionar manualmente el Vault;
- preservar asignación segura y única de IDs;
- cerrar un episodio sin modificar otros episodios abiertos.

No hay cumplimiento si la solución solo elimina el guard global pero introduce selección ambigua, contaminación cruzada o un “episodio activo” implícito global.

4\. ALCANCE

PLAN016 incluye:
- generalizar la restricción global para permitir varios episodios de producto `en_progreso`, preservando los bloqueos legacy/recovery expresamente definidos;
- asegurar creación/indexación con varios episodios no cerrados;
- auditar todos los callers del helper compartido modificado;
- preservar compatibilidad de consumidores legacy salvo cambio expresamente necesario;
- proporcionar descubribilidad mínima de episodios de producto abiertos desde la superficie normal;
- selección/reanudación inequívoca por `episode_id`, que es la única identidad autoritativa para esta operación; slug/título/tema son solo información humana;
- pruebas de aislamiento de estado, decisiones, handoffs, approvals, WORKING_CURRENT, APPROVED_CURRENT y closure;
- pruebas de ID/index integrity;
- pruebas de cierre de un episodio mientras otro permanece abierto;
- documentación canónica mínima del comportamiento observable si la interfaz cambia.

5\. NO ALCANCE

Queda fuera:
- ejecución simultánea de dos pipelines en paralelo;
- workers, colas, scheduler o background processing;
- prioridades entre episodios;
- dashboard completo;
- búsqueda avanzada;
- RETRY/REGENERATE general;
- historial avanzado;
- merge o clonación de episodios;
- colaboración multiusuario;
- locking distribuido nuevo sin necesidad demostrada;
- migración de Vault o nueva base de datos;
- cambios a Research, Writing, Editor o auditorías no necesarios para aislamiento;
- cambios materiales a contratos aprobados por PLAN015.

6\. ARQUITECTURA E INVARIANTES

6.1 Identidad

episode_id es la identidad canónica de cada episodio.
Dos episodios no comparten estado mutable por defecto.

6.2 Aislamiento

Toda lectura/escritura de producto debe quedar vinculada inequívocamente al episode_id seleccionado.

Decisiones, handoffs, approvals, script versions, WORKING_CURRENT/current_script de trabajo, APPROVED_CURRENT/approved_current, closure y artifacts de A no pueden ser consumidos ni modificados por B.

El aislamiento es una propiedad lógica. PLAN016 no autoriza crear un nuevo store/registry por episodio si los bindings existentes ya permiten demostrarla.

6.3 Índice, estado abierto e identidad

`episodes_index.json` continúa siendo la fuente canónica de descubrimiento; PLAN016 no introduce un registro paralelo ni deriva la lista escaneando carpetas del Vault.

En la baseline auditada, un episodio de producto se considera abierto cuando su entrada canónica tiene `estado == "en_progreso"`. Esta regla debe confirmarse en el drift post-PLAN015 y ajustarse únicamente si PLAN015 cambió materialmente el contrato de estado. Estados de cierre editorial o administrativo no son abiertos.

La superficie normal no debe presentar como episodio de producto reanudable una entrada técnica legacy (`input_origin == "LEGACY_SCRIPT_TECHNICAL"` o equivalente canónico post-drift). Esos registros permanecen bajo sus flujos legacy/recovery vigentes.

El índice puede contener múltiples episodios de producto abiertos y debe mostrar su estado resumido sin introducir un “activo” global implícito.

Toda operación de producto que resuelva una identidad —incluidas descubribilidad/selección, reanudación, escritura de estado, aprobación y cierre— exige exactamente una coincidencia de `episode_id` en el índice. Cero coincidencias → NOT_FOUND. Más de una coincidencia → `INDEX_EPISODE_ID_AMBIGUOUS`/fail-closed. Nunca se selecciona la primera coincidencia, se actualizan varias coincidencias ni se repara una duplicidad por conveniencia. La creación también debe bloquear si el índice preexistente ya contiene cualquier `episode_id` duplicado.

6.4 Concurrencia

PLAN016 no exige pipelines concurrentes.
Sí exige que creaciones próximas no dupliquen episode_id ni corrompan el índice.
Debe reutilizarse `_index_lock()` y la asignación actual salvo defecto demostrado.

6.5 Compatibilidad legacy

Antes de modificar `_create_episode_locked()` o cualquier helper equivalente, el implementador debe inventariar todos sus callers.

La ruta moderna `create_episode()` es la que PLAN016 habilita para coexistencia entre varios episodios de producto abiertos. Esa habilitación NO elimina por implicación los bloqueos de recovery de una entrada técnica legacy. Mientras exista una entrada `LEGACY_SCRIPT_TECHNICAL` —o equivalente canónico post-drift— con `estado == "en_progreso"`, `create_episode()` moderno continúa bloqueado hasta que esa entrada sea recuperada o cerrada por los mecanismos legacy/recovery vigentes. PLAN016 no autoriza convivencia entre un legacy técnico abierto y un nuevo episodio moderno.
`create_legacy_episode()` conserva su semántica técnica actual de compatibilidad y no hereda automáticamente el permiso de múltiples episodios abiertos. Si ambas rutas siguen compartiendo helper, la política debe quedar diferenciada por caller sin duplicar storage ni crear un segundo índice.

El wrapper legacy conserva su `episode_number` explícito, sus marcadores técnicos y sus fallos cerrados actuales. En particular, los flujos legacy que requieren un episodio único o selección explícita deben continuar bloqueando ante ambigüedad; PLAN016 no moderniza el wrapper legacy.

7\. CONTRATO DE CREACIÓN

Crear un episodio nuevo por la ruta moderna debe:
1\. adquirir la protección de índice existente;
2\. cargar y validar el índice dentro del lock;
3\. calcular un `episode_id` único con la asignación canónica vigente;
4\. rechazar identidad duplicada o índice ambiguo antes de persistir;
5\. crear persistencia inicial aislada;
6\. añadir únicamente la nueva entrada al índice, sin alterar otras;
7\. liberar el lock;
8\. continuar según el workflow normal.

La existencia de otros episodios de producto abiertos no es error para `create_episode()`. En cambio, una entrada técnica legacy abierta que siga siendo recovery-blocking bajo el contrato vigente sí bloquea la creación moderna hasta su recuperación/cierre explícitos. No cambia por sí sola el contrato de `create_legacy_episode()`.

Un conflicto real de ID, corrupción del índice o fallo de persistencia sigue siendo fail-closed.

8\. CONTRATO DE DESCUBRIBILIDAD Y SELECCIÓN

La superficie normal de descubrimiento queda fijada como `python -m src.cli listar-episodios`. No se delega a BUILD escoger otra interfaz primaria. `reanudar <episode_id>` continúa siendo la única acción normal de continuidad de un episodio existente. La implementación interna puede variar, pero estos contratos observables son obligatorios.

Contrato observable de `python -m src.cli listar-episodios`:
- leer la proyección desde `episodes_index.json` sin escanear carpetas como fuente alternativa;
- mostrar `episode_id` canónico;
- mostrar descripción humana suficiente, como slug/título/tema disponible, sin usarla como identidad;
- mostrar `application_status`/estado operativo relevante;
- si no existen episodios de producto abiertos, terminar con código 0 y una salida explícita de conjunto vacío/no hay episodios abiertos;
- si el índice contiene duplicidad de `episode_id`, corrupción estructural o una entrada cuya identidad no puede resolverse de forma inequívoca, terminar con código distinto de 0 y error claro, sin listar una selección parcial como si fuera válida;
- excluir de la lista normal las entradas técnicas legacy no reanudables como producto;
- no ocultar silenciosamente corrupción: una identidad duplicada o una entrada seleccionada cuyo folder/state no corresponde debe producir estado bloqueado/error claro;
- mostrar el `episode_id` necesario para que el usuario continúe mediante `python -m src.cli reanudar <episode_id>`; la salida de listado no reanuda ni elige automáticamente un episodio.

`listar-episodios` no cambia la identidad ni el estado de ningún episodio. Incluso si existe un único episodio de producto abierto, la continuidad se realiza mediante `reanudar <episode_id>` con el identificador exacto. Si existen varios episodios de producto abiertos, nunca se elige silenciosamente uno arbitrario.

9\. CONTRATO DE REANUDACIÓN

`python -m src.cli reanudar <episode_id>` debe resolver exactamente una entrada del índice, validar su binding de folder/state y cargar únicamente el episodio seleccionado antes de aplicar la semántica de continuidad vigente tras PLAN015. PLAN016 no introduce una segunda acción normal de reanudación.

Un ID inexistente, inválido, duplicado, cerrado o no reanudable como producto debe bloquear con error claro. Un registro técnico legacy no se convierte en episodio de producto reanudable por aparecer `en_progreso`.

Reanudar A no puede consumir decisions, results, handoffs o state de B aunque existan nombres de artifacts similares.

10\. CONTRATO DE CIERRE

Cerrar/aprobar A solo puede modificar:
- su episode_state/workflow_state;
- su closure, WORKING_CURRENT/current_script de trabajo, APPROVED_CURRENT/approved_current y versionado;
- su entrada de índice;
- artifacts vinculados a A.

B y C conservan su estado previo.

Cerrar A no convierte automáticamente B en activo ni dispara su ejecución.

Los mecanismos legacy que requieren selección explícita cuando hay varios episodios deben seguir fallando cerrado ante ambigüedad.

11\. COMPATIBILIDAD CON PARADAS LEGÍTIMAS

Un episodio puede permanecer abierto esperando:
- resultado AGENT_HARNESS;
- decisión humana;
- gate desbloqueable;
- autorización legítima;
- cualquier parada soportada por la continuidad vigente.

Ese estado, cuando corresponde a un episodio de producto, no debe impedir crear o reanudar otros episodios de producto. Esta regla no elimina el bloqueo histórico de recovery de una entrada técnica legacy `en_progreso`, que se conserva según 6.5 y 7\. Pueden coexistir handoffs pendientes de episodios distintos en superficies compartidas, pero toda importación, archivado o consumo debe discriminar por los bindings existentes de `episode_id` + `handoff_id`/checksum; queda prohibido resolver por “último”, “primero” o nombre parecido.

PLAN016 no redefine las paradas ni los contratos de handoff establecidos por PLAN015; elimina el bloqueo global entre episodios de producto abiertos, preserva los bloqueos legacy/recovery expresamente definidos y demuestra que los bindings siguen aislando correctamente cuando hay más de un episodio de producto abierto.

12\. REUTILIZACIÓN OBLIGATORIA

Se reutiliza antes de crear alternativas:
- VaultEpisodeStore;
- episodes_index.json y su lock;
- EpisodeHandle;
- episode_id/slug/folder existentes;
- EpisodeApplicationService;
- CLI/superficie iniciar/reanudar;
- estados y contratos de cierre vigentes;
- bindings existentes de handoffs/decisions/approvals.

No se crea un nuevo episode registry paralelo si el índice actual puede cumplir mediante generalización mínima.

13\. RIESGOS Y MITIGACIONES

Riesgo: colisión de IDs.
Mitigación: preservar asignación bajo lock y probar creaciones sucesivas/solapables dentro del alcance reproducible.

Riesgo: contaminación cruzada.
Mitigación: tests con episodios distintos y asserts de aislamiento en decisions/handoffs/approvals/WORKING_CURRENT/APPROVED_CURRENT/closure.

Riesgo: reanudación ambigua.
Mitigación: selección inequívoca; nunca “primero en progreso”.

Riesgo: romper consumidores legacy del helper compartido.
Mitigación: inventario de callers + regresión focal de cada consumidor afectado.

Riesgo: convertir el plan en scheduler.
Mitigación: no autorizar ejecución paralela, colas, prioridades ni workers.

Riesgo: duplicar índice/store.
Mitigación: reutilización obligatoria y STOP ante infraestructura nueva no demostrada.

Riesgo: selección silenciosa ante `episode_id` duplicado o índice corrupto.
Mitigación: lookup exige exactamente una coincidencia; 0 o >1 bloquea y no se autoriza autorreparación implícita.

Riesgo: exponer un registro técnico legacy como episodio normal reanudable.
Mitigación: la superficie normal filtra según el contrato de producto y conserva los registros legacy bajo sus rutas de compatibilidad/recovery.

Riesgo: drift por PLAN015.
Mitigación: reauditoría focal obligatoria contra HEAD post-PLAN015 antes de OWNER APPROVAL.

14\. HITO FUNCIONAL REPRESENTATIVO

HF-01 — Operación multi-episodio mínima

Debe demostrar en una sola secuencia representativa:
A queda en parada legítima
→ crear B
→ A y B aparecen abiertos en la superficie normal; una entrada técnica legacy solo puede coexistir en este hito si no está en condición recovery-blocking, y en ningún caso se presenta como episodio de producto reanudable
→ seleccionar/reanudar A por su `episode_id` exacto y usar solo estado de A
→ seleccionar/reanudar B por su `episode_id` exacto y usar solo estado de B
→ decision/handoff/approval/WORKING_CURRENT/APPROVED_CURRENT de A no cruza a B
→ una duplicidad sintética de `episode_id` en el índice bloquea la selección en vez de escoger una coincidencia
→ cerrar A
→ B permanece intacto
→ crear C
→ IDs e índice permanecen válidos.

HF-01 no es una misión ni requiere aprobación separada.
Si falla, no se continúa hacia cierre del PLAN.

15\. PRE-FLIGHT DE EJECUCIÓN

Después de OWNER APPROVAL y activación canónica, pero antes de modificar código, el agente debe confirmar:
- HEAD post-PLAN015 coincide con el auditado;
- working tree y autoridad son coherentes;
- PLAN016 está activo;
- callers de helpers compartidos están identificados y se confirma si `create_episode()` y `create_legacy_episode()` siguen compartiendo implementación;
- todos los lectores y escritores directos de `episodes_index.json` que resuelvan o muten una entidad por `episode_id` están inventariados, incluidos consumidores fuera de `VaultEpisodeStore`; para toda superficie alcanzada por PLAN016, la resolución/mutación debe exigir exactamente una coincidencia o reutilizar una resolución canónica equivalente; no basta auditar únicamente `_create_episode_locked()` o `_entry()`;
- semántica vigente post-PLAN015 de `en_progreso`, cierre editorial/administrativo, WORKING_CURRENT y APPROVED_CURRENT está comprendida;
- la superficie CLI vigente y los flujos legacy/recovery que leen `episodes_index.json` están inventariados;
- tests focales y de integración están identificados;
- no existe drift material no auditado.

El pre-flight es breve y no sustituye la auditoría.
Drift material → STOP.

16\. PRUEBAS PROPORCIONALES

Focales obligatorias y reproducibles:

Comando funcional principal de PLAN016:
`python -m pytest tests/application/test_plan016_multi_episode.py -q`

Ese módulo nuevo debe cubrir HF-01 y la superficie CLI `listar-episodios`/`reanudar`, incluidos 0/1/múltiples episodios de producto abiertos, legacy técnico recovery-blocking, duplicidad de `episode_id`, cierre de A sin mutar B y creación posterior de C.

Regresiones existentes mínimas después de tocar indexación/selección/cierre/recovery:
`python -m pytest tests/core/test_application_intake.py tests/application/test_plan013_closure.py tests/harness/test_plan010_m2_m3.py -q`

Si el inventario de consumidores directos de `episodes_index.json` identifica otro módulo existente realmente afectado por el diff, se añade únicamente su regresión focal. No se exige por defecto la suite completa.

Escenarios que deben estar cubiertos:
- crear A;
- dejar A abierto/esperando;
- crear B sin cerrar A;
- IDs A \!= B y persistencia separada;
- ambos visibles como abiertos desde la superficie normal;
- una entrada técnica legacy no aparece como episodio normal reanudable;
- una entrada técnica legacy `en_progreso` que sea recovery-blocking conserva el bloqueo histórico sobre `create_episode()` moderno; tras su recovery/cierre explícito, la creación moderna puede continuar;
- reanudar A usa A por `episode_id`;
- reanudar B usa B por `episode_id`;
- un `episode_id` duplicado/corrupto bloquea en vez de seleccionar la primera coincidencia;
- al menos un lector o escritor directo del índice fuera de `_entry()` se cubre con negativo focal para demostrar que una identidad duplicada no provoca selección de la primera coincidencia ni actualización de todas las coincidencias;
- decision/handoff/approval de A no aparece en B;
- WORKING_CURRENT/APPROVED_CURRENT/versiones/closure no se cruzan;
- cerrar A no cambia B;
- crear C después mantiene ID único;
- ID inexistente bloquea;
- índice permanece válido;
- consumidores legacy afectados conservan su contrato o fallan cerrado según corresponda.

Regresiones:
storage, application service, CLI y cualquier recovery/cierre cuya diff toque indexación o selección.

No se exigen suites completas de Research/Writing si sus contratos no cambian.

Integración:
al menos dos episodios de producto abiertos en estados durables distintos y reanudación alternada, con una parada legítima representativa y coexistencia de bindings/handoffs cuando aplique.
No es obligatoria cognición real si fixtures/estados representativos demuestran aislamiento, pero HF-01 debe recorrer la superficie normal de descubrimiento/selección y no limitarse a llamar métodos internos del store.

17\. CRITERIOS DE ACEPTACIÓN

MULTIPLE_OPEN_PRODUCT_EPISODES = PASS
EPISODE_ID_UNIQUENESS = PASS
INDEX_INTEGRITY = PASS
NORMAL_SURFACE_DISCOVERS_OPEN_PRODUCT_EPISODES = PASS
EXPLICIT_RESUME_SELECTION = PASS
NO_SILENT_ACTIVE_EPISODE_AMBIGUITY = PASS
STATE_ISOLATION = PASS
HUMAN_DECISION_ISOLATION = PASS
HANDOFF_ISOLATION = PASS
APPROVAL_ISOLATION = PASS
WORKING_CURRENT_ISOLATION = PASS
APPROVED_CURRENT_ISOLATION = PASS
CLOSURE_ISOLATION = PASS
CLOSING_A_DOES_NOT_MUTATE_B = PASS
EXACT_ONE_EPISODE_ID_LOOKUP = PASS
DUPLICATE_EPISODE_ID_FAIL_CLOSED = PASS
LEGACY_TECHNICAL_ENTRIES_NOT_EXPOSED_AS_PRODUCT = PASS
SHARED_HELPER_CALLERS_AUDITED = PASS
LEGACY_COMPATIBILITY_PRESERVED = PASS
LEGACY_OPEN_RECOVERY_BLOCK_PRESERVED = PASS
DIRECT_INDEX_EPISODE_ID_CONSUMERS_AUDITED = PASS
CANONICAL_PLAN_PATH = PASS
POST_PLAN015_DRIFT_AUDIT = PASS
NO_NEW_DATABASE = YES
NO_PARALLEL_EPISODE_REGISTRY = YES
NO_SCHEDULER_OR_QUEUE = YES
NO_LIFECYCLE_SCOPE_EXPANSION = YES

17.1 MATRIZ MÍNIMA DE EVIDENCIA

La aceptación no se demuestra repitiendo suites indiscriminadamente. Cada criterio debe quedar cubierto por evidencia proporcional y vigente:

- `MULTIPLE_OPEN_PRODUCT_EPISODES`, `EPISODE_ID_UNIQUENESS`, `INDEX_INTEGRITY`, `EXACT_ONE_EPISODE_ID_LOOKUP`, `DUPLICATE_EPISODE_ID_FAIL_CLOSED` → pruebas focales de creación bajo lock + HF-01 con A/B/C; incluye índice preexistente con identidad duplicada y verifica que selección/escritura/cierre no escojan ni actualicen coincidencias ambiguas.
- `NORMAL_SURFACE_DISCOVERS_OPEN_PRODUCT_EPISODES`, `EXPLICIT_RESUME_SELECTION`, `NO_SILENT_ACTIVE_EPISODE_AMBIGUITY` → prueba de la superficie normal con 0/1/múltiples abiertos, selección exacta por `episode_id` y caso de identidad duplicada fail-closed.
- `STATE_ISOLATION`, `HUMAN_DECISION_ISOLATION`, `HANDOFF_ISOLATION`, `APPROVAL_ISOLATION` → dos episodios con estados/artifacts distintos, operaciones alternadas y asserts de no contaminación; handoffs compartidos se validan por bindings exactos.
- `WORKING_CURRENT_ISOLATION`, `APPROVED_CURRENT_ISOLATION`, `CLOSURE_ISOLATION`, `CLOSING_A_DOES_NOT_MUTATE_B` → cierre/aprobación de A con snapshot verificable de B antes/después.
- `LEGACY_TECHNICAL_ENTRIES_NOT_EXPOSED_AS_PRODUCT`, `SHARED_HELPER_CALLERS_AUDITED`, `LEGACY_COMPATIBILITY_PRESERVED`, `LEGACY_OPEN_RECOVERY_BLOCK_PRESERVED` → inventario real de callers + regresiones focales del wrapper/recovery/cierre legacy afectados; incluye legacy técnico `en_progreso` bloqueando creación moderna y desbloqueo posterior solo tras recovery/cierre explícito.
- `DIRECT_INDEX_EPISODE_ID_CONSUMERS_AUDITED`, `EXACT_ONE_EPISODE_ID_LOOKUP`, `DUPLICATE_EPISODE_ID_FAIL_CLOSED` → inventario de lectores/escritores directos de `episodes_index.json` por `episode_id` y negativos focales en superficies representativas, incluidas fuera de `_entry()`, para demostrar que 0 o >1 coincidencias no producen lectura, escritura, aprobación o cierre ambiguos.
- `CANONICAL_PLAN_PATH` → antes de declarar formalmente auditado PLAN016 debe existir exactamente una copia autoritativa en `plans/plan_016/PLAN016_Operación_multi-episodio_mínima.md`; ninguna referencia canónica puede apuntar a otra ruta o nombre.
- `POST_PLAN015_DRIFT_AUDIT` → comparación focal del HEAD post-PLAN015 con las superficies compartidas; solo invalida la evidencia afectada.
- `NO_NEW_DATABASE`, `NO_PARALLEL_EPISODE_REGISTRY`, `NO_SCHEDULER_OR_QUEUE`, `NO_LIFECYCLE_SCOPE_EXPANSION` → diff/convergencia demuestra ausencia de infraestructura no autorizada.

HF-01 es la evidencia funcional representativa principal y debe quedar materializado en `tests/application/test_plan016_multi_episode.py`, ejecutable mediante `python -m pytest tests/application/test_plan016_multi_episode.py -q`. Las regresiones existentes cubren contratos históricos afectados; no sustituyen HF-01.

18\. STOP CONDITIONS

Detener y pedir OWNER DECISION si cumplir PLAN016 exige:
- migrar Vault o introducir base de datos;
- crear locking distribuido sin necesidad demostrada;
- añadir scheduler/colas/workers;
- cambiar identidad canónica de episode_id;
- modificar arquitectura cognitiva o verticales editoriales;
- introducir multiusuario;
- cambiar materialmente contratos aprobados por PLAN015;
- romper compatibilidad legacy sin necesidad dentro de alcance;
- ampliar a lifecycle avanzado.

Defectos locales en storage/index/CLI necesarios para satisfacer el contrato pueden corregirse si no cambian la frontera del plan.

19\. GOBERNANZA Y DEPENDENCIA CON PLAN015

PLAN016 tiene OWNER_PREAPPROVAL condicionada para alcance y diseño documental, pero no tiene aprobación final ni autoriza implementación. Su auditoría estática y corrección documental pueden completarse en paralelo con la ejecución de PLAN015; esto no activa PLAN016 ni modifica el alcance de PLAN015.
Antes de declarar formalmente auditado el PLAN canónico del repositorio, PLAN016 v0.5.0 debe materializarse en una única ruta exacta: `plans/plan_016/PLAN016_Operación_multi-episodio_mínima.md`. No pueden coexistir dos PLAN016 competidores y no se crean sufijos `v2`, `final` ni copias paralelas.

El objetivo de la auditoría estática es dejar cerradas todas las decisiones independientes de PLAN015. La preaprobación OWNER condicionada deja aprobado el alcance documental, no sustituye el cierre de PLAN015 ni la reauditoría focal post-PLAN015. Tras la reauditoría focal de las correcciones v0.5.0, si no aparecen contradicciones materiales nuevas, el documento queda estáticamente listo y pendiente únicamente del drift focal post-PLAN015. La aprobación final sigue esta secuencia:
1\. PLAN015 CLOSED/ACCEPTED;
2\. obtener HEAD post-PLAN015;
3\. reauditoría focal de drift;
4\. corregir PLAN016 si procede;
5\. OWNER APPROVAL específico;
6\. registrar PLAN016 como autoridad activa;
7\. PRE-FLIGHT;
8\. ejecución integrada;
9\. HF-01;
10\. auto-verificación;
11\. auditoría independiente;
12\. correcciones focales si proceden;
13\. OWNER ACCEPTANCE;
14\. cierre.

La auditoría documental paralela ya forma parte de esta gobernanza y no requiere una autorización adicional. Ejecutar PLAN016 antes de cerrar PLAN015, o solapar implementación material de ambos, sí requeriría decisión explícita del OWNER y auditoría de interacción entre alcances.

20\. CIERRE

Al cerrar PLAN016:
- múltiples episodios de producto abiertos son operación soportada;
- el repositorio registra PLAN016 como CLOSED/ACCEPTED según su canon;
- CURRENT_PLAN vuelve a NONE salvo nueva autorización;
- EXECUTION_AUTHORIZED vuelve a NO salvo nueva autorización;
- la evidencia final conserva solo lo necesario para demostrar aislamiento, integridad y compatibilidad;
- Git/repositorio son la autoridad canónica.

PLAN016 no autoriza ninguna iniciativa posterior por quedar cerrado.
