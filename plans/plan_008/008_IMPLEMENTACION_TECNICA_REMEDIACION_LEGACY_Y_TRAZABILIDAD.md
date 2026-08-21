# PLAN 008 — IMPLEMENTACIÓN TÉCNICA DE REMEDIACIÓN LEGACY Y TRAZABILIDAD

Fecha: 2026-08-20
Estado: OWNER_CLOSED
Identificador canónico del repositorio: PLAN-008
Revisión independiente: PASS
Misión activa: NONE
Commit de cierre: REALIZADO
Push: NO AUTORIZADO.

## 1. Propósito

Materializar de forma técnica, mínima y neutral las decisiones ya reconciliadas sobre documentación y reglas legacy, corrigiendo únicamente defectos activos y deuda documental material demostrada, sin restaurar documentos históricos como autoridad, sin reabrir decisiones funcionales y sin adelantar trabajo de fases futuras.

La implementación debe seguir esta cadena:

decisión vigente → requisito técnico → superficie actual → defecto demostrado → cambio mínimo → invalidadores → pruebas.

Este plan no autoriza producción real, uso de producto, R2, B5-I3, B6, B7 ni B7.5. Tampoco modifica por sí mismo el estado de R1_GATE. Es un plan de remediación técnica independiente de esas autorizaciones.

## 2. Principios obligatorios

- Leer primero el control operativo canónico y comprobar el estado vivo del repositorio.
- Si el estado vivo contradice una parte del plan, aplicar STOP_LOCAL solo a esa parte y continuar trabajo independiente.
- Buscar y reutilizar antes de crear.
- Mantener una sola autoridad por concepto; no crear registros paralelos.
- Preservar razón, autoridad, evidencia, estado y sucesión cuando una decisión material cambie o quede sustituida.
- No reconstruir todo el historial Git.
- No convertir documentos legacy en autoridad activa.
- La documentación durable debe usar exclusivamente conceptos nativos del producto y del repositorio; no debe incorporar mecanismos ni nomenclaturas de coordinación externa.
- No introducir identificadores externos de reconciliación como nomenclatura permanente del producto.
- Conservar compatibilidad legacy útil cuando esté demostrada y aislada; retirar solo dependencias activas indebidas.
- No modificar trabajo ajeno o no relacionado.
- No hacer push sin autorización explícita posterior.
- No hacer commit salvo autorización explícita posterior. Si no existe autorización de commits, las misiones deben ejecutarse secuencialmente en un único worktree. La paralelización con worktrees solo se habilita si existe una estrategia de integración autorizada que no viole esta regla.

## 3. Frontera de autoridad

La implementación técnica puede decidir cómo representar, almacenar, validar, integrar y probar los requisitos ya aprobados.

No puede redefinir durante la ejecución:
- qué constituye una decisión material;
- qué autoridad puede sustituir a otra;
- cuándo una decisión queda efectivamente sustituida;
- qué cambios requieren aprobación funcional;
- qué historial material debe conservarse obligatoriamente;
- criterios editoriales de investigación, curación, voz, estructura, spoilers, apertura o redacción.

Si aparece una ambigüedad nueva cuya resolución cambiaría alguna de esas semánticas, detener solo la parte afectada y devolverla al owner funcional o transversal competente. No usar la implementación para inventar criterio de producto.

## 4. Estado de partida que debe verificarse

Antes de comenzar la primera misión, comprobar como mínimo:
- branch y HEAD actuales;
- worktree limpio o identificación precisa de cambios existentes;
- `plans/001_CONTROL_OPERATIVO.md`;
- numeración de `plans/plan_*`;
- estado real de B5-I3/B6/B7/B7.5;
- existencia y estado de los mecanismos citados en este plan;
- que no haya una implementación local no publicada que vuelva obsoleto un supuesto.

En el worktree local se confirmaron `plan_001` a `plan_007` y `plan_p1`; PLAN-008 es el siguiente identificador disponible y queda materializado en esta carpeta, sin colisiones.

## 5. Estrategia de ejecución

El trabajo se divide en cuatro misiones de implementación y una revisión final. La primera misión debe completarse antes de las demás. Tras ella, la misión 2 y la misión 3 son técnicamente independientes salvo cambios reales no previstos; pueden ejecutarse en paralelo únicamente si existe reserva exclusiva de archivos y una estrategia de integración autorizada. En ausencia de autorización de commits, ejecutarlas de forma secuencial.

La misión 4 siempre va al final.

### MISIÓN 1 — Historial material, sucesión e índice legacy

Objetivo:
Cerrar la deuda que permite que una decisión material cambie o desaparezca sin razón, autoridad, estado, evidencia y sucesión localizables, y reconstruir la evidencia documental per-file mínima que hoy falta.

Trabajo:
1. Preflight cumplido: la numeración canónica fue confirmada contra el worktree local y este plan quedó materializado con el identificador PLAN-008 en esta carpeta (ver secciones 4 y 10), con redacción neutral y sin referencias al proceso externo que originó el plan.
2. Inspeccionar los patrones ya existentes en registros especializados de perfiles, lifecycle de obras, iniciativas, control operativo y provenance. Reutilizar sus patrones útiles sin convertir ninguno en autoridad universal.
3. Materializar una representación nativa y pequeña para decisiones materiales que permita conservar como mínimo:
 - identificador estable;
 - decisión vigente;
 - razón;
 - autoridad/owner competente;
 - estado;
 - evidencia o referencias verificables;
 - sucesión cuando una decisión sustituye o es sustituida.
4. Crear una vista per-file derivada para documentación legacy material, con estado, autoridad/sucesor, consumer cuando exista, duplicación material y disposición/migración. Esta vista no puede convertirse en una segunda fuente de verdad.
5. Reconciliar la ausencia de la evidencia per-file exigida por B3-M1 como deuda de trazabilidad, sin reabrir B3 ni invalidar el consumo canónico ya demostrado.

No debe:
- crear una plataforma general de gobernanza;
- duplicar CONTROL_OPERATIVO, provenance, registros de perfiles, lifecycle o iniciativas;
- importar discusiones o artefactos externos;
- reconstruir todo Git;
- redefinir materialidad o autoridad funcional.

Validación mínima:
- tests del mecanismo creado o extendido;
- referencias de sucesión válidas y consistentes;
- razón/autoridad/estado obligatorios;
- unicidad de autoridad donde aplique;
- vista per-file demostrablemente derivada;
- `tests/core/test_runtime_contamination_guard.py`;
- `tests/harness/test_b3_i3_canonical_consumption.py`;
- `tests/core/test_all_schemas.py` si se crea o modifica un schema;
- `git diff --check`;
- revisión final del worktree.

Criterio de cierre:
El mecanismo mínimo existe y tiene pruebas; la vista legacy no duplica autoridad; B3-M1 queda reconciliado documentalmente; ninguna semántica funcional nueva fue inventada.

### MISIÓN 2 — Integridad de investigación y curación

Objetivo:
Cerrar defectos activos que permiten que la progresión de una obra y la madurez de su investigación evolucionen de forma incoherente, y retirar residuos contractuales que ya no representan la arquitectura vigente.

Superficies mínimas a inspeccionar:
- `schemas/work_research_dossier.json`;
- `schemas/work_lifecycle.json`;
- `src/core/contract_validation.py`;
- `.agent/skills/skill_curation_obras.md`;
- `config/skill_catalog.json` solo si el cambio real lo exige;
- tests de lifecycle, dossier y B5-I2.

Trabajo:
1. Cerrar el fail-open por el cual `FINALIST_WORK` o `FINAL_SELECTED_WORK` puede avanzar con un `WorkResearchDossier` por debajo de la madurez funcional requerida.
2. Derivar la relación correcta entre lifecycle de obra y madurez de dossier exclusivamente de las policies, schemas, contratos y decisiones vigentes. Si el repositorio no permite determinar una correspondencia sin introducir criterio funcional nuevo, aplicar STOP_LOCAL a ese mapping y continuar el resto.
3. Reconciliar residuos como `audit_reference = null`, `DEFERRED_TO_R1_M10_R1_M11` y estados transitorios de suficiencia/fidelidad que ya no representan el flujo posterior a M10/M11, reutilizando la arquitectura de auditoría vigente en lugar de crear otra autoridad.
4. Alinear `skill_curation_obras` con el rango normal 5–8 candidatas, 3–5 obras finales sustantivas y excepción editorial explícita, dejando claro que las cantidades no sustituyen suficiencia, función o evidencia.

No debe:
- rediseñar investigación;
- crear artefactos editoriales nuevos por comodidad técnica;
- fijar cuotas universales de fuentes;
- convertir un validator en juez de suficiencia editorial sustantiva.

Validación mínima:
- `tests/core/test_work_lifecycle.py`;
- `tests/core/test_plan007_p2_contracts.py`;
- `tests/core/test_r1_m6_m8.py`;
- `tests/harness/test_b5_i2.py`;
- caso negativo explícito donde un `FINAL_SELECTED_WORK` con dossier `IDENTIFIED` sea rechazado cuando la policy vigente exige mayor madurez;
- casos positivos vigentes de selección y excepción;
- `git diff --check`.

Criterio de cierre:
La progresión obra↔dossier falla cerrado según la semántica ya aprobada, los residuos de fidelidad no contradicen M10/M11 y la skill de curación coincide con la policy vigente.

### MISIÓN 3 — Portabilidad, dependencias legacy activas y duración/cierre vigente

Objetivo:
Resolver en una sola misión las superficies que pueden compartir `cerrar_episodio.py` y `test_b2_harness.py`, evitando dos implementaciones en conflicto. Debe dejar provider-neutral la ruta vigente sin romper compatibilidad legacy deliberada y eliminar la autoridad universal de parámetros de duración heredados.

Superficies candidatas:
- `README.md`;
- `.agent/rules/01_formato_outputs.md`;
- `.agent/rules/02_reglas_notebooklm.md` solo si su estado real lo requiere;
- skills `KEEP` realmente acopladas a Vault/configuración local;
- `src/scripts/gate0_auditoria.py` y `src/scripts/gate0_integridad.py` únicamente según evidencia;
- `src/scripts/iniciar_episodio.py` y `src/scripts/cerrar_episodio.py` cuando el cambio real lo exija;
- `src/scripts/qa_duracion_guion.py`;
- superficies que producen o consumen `YT_DURATION_ENVELOPE`;
- `tests/harness/test_b2_harness.py`.

Trabajo de portabilidad:
1. Retirar de documentación vigente la apariencia de NotebookLM como autoridad o gate universal obligatorio.
2. Dejar inequívoco que la ruta portable puede operar sin Vault, `local_settings` o path local obligatorio.
3. Reconciliar reglas y skills activas que todavía presentan Vault como única sede válida.
4. Conservar compatibilidad legacy útil, explícita y aislada.
5. Modificar Gate0 solo si la evidencia demuestra que una comprobación física histórica funciona como dependencia activa indebida; no eliminar compatibilidad por homogeneización cosmética.

Trabajo de duración/cierre:
1. Reconciliar `YT_DURATION_ENVELOPE` con la vía `qa_duracion_guion.py` → `cerrar_episodio.py`.
2. Hacer que el cierre consuma parámetros episódicos aprobados cuando existan o, si la arquitectura vigente lo requiere, retirar `144 WPM / 18–22 min` como autoridad editorial universal de cierre.
3. Un fallback técnico solo puede permanecer si está claramente identificado como fallback técnico y no puede contradecir silenciosamente un envelope episódico válido.
4. No activar B6 ni implementar la futura arquitectura de escritura.

Validación mínima:
- ruta portable sin `local_settings`/Vault;
- compatibilidad legacy donde se conserve;
- pruebas negativas de dependencia universal de NotebookLM/Vault/path local;
- cierre de episodio portable;
- caso que demuestre que un envelope episódico válido prevalece sobre defaults generales;
- caso de fallback técnico cuando proceda;
- tests dirigidos de `tests/harness/test_b2_harness.py`;
- cualquier test específico de duración/cierre afectado;
- `git diff --check`.

Criterio de cierre:
La ruta portable no depende universalmente de una herramienta o path local, la compatibilidad legacy útil sigue disponible y el cierre no impone parámetros universales por encima del criterio episódico.

### MISIÓN 4 — Cierre documental legacy y prerrequisitos futuros

Objetivo:
Cerrar la deuda documental material después de que las superficies activas ya estén corregidas, sin limpiar por antigüedad ni crear una nueva fuente de verdad.

Trabajo:
1. Completar la vista per-file derivada de la Misión 1.
2. Dejar inequívocos estado, sucesor y no ejecutabilidad de los documentos legacy materiales cuando corresponda, preservando su contenido como evidencia histórica.
3. Reconciliar `reference/estilo_usuario/README.md` con la autoridad vigente de perfil/corpus/aprendizaje sin convertir documentación histórica de voz en reglas nuevas.
4. Reconciliar las autodeclaraciones de autoridad de `workspace/00`, `workspace/01`–`05c` y `workspace/07`, preferiblemente mediante metadata/header mínimo y no reescritura histórica del cuerpo.
5. Verificar que `README.md` y `.agent/rules/01_formato_outputs.md` no queden con semánticas divergentes tras la Misión 3.
6. Registrar de forma neutral los siguientes prerrequisitos futuros en los hitos canónicos que realmente los consumirán, sin implementar comportamiento ahora:
 - antes de B5-I3/B6/B7: ninguna futura activación debe reintroducir 80/20 cuantitativo, re-hooks periódicos, resets por cronómetro, tres eventos obligatorios, timeline universal 15–25, "segundo mejor primero", CTA obligatorio ni una plantilla universal Hook→Intro→eventos→clímax→CTA; la sustitución debe usar gramática narrativa funcional, progresión, renovación atencional y variación de ritmo no mecánicas ya aprobadas;
 - antes de consumidores materiales de spoilers en B5-I3/B6/B7.5: integrar la política completa de spoilers en consumidores canónicos —necesidad editorial, minimización, warning proporcional, ubicación y protección de packaging/apertura— sin crear un stack paralelo;
 - voz y referentes: ningún cambio conductual o nuevo `reference_boundary` se añade por simetría; solo mediante gobernanza de identidad cuando exista necesidad material de enforcement.

No debe:
- reescribir skills diferidas como si estuvieran activas;
- activar B5-I3/B6/B7/B7.5;
- borrar documentos porque sean antiguos;
- convertir observaciones de `05c` en reglas;
- crear un boundary de referentes sin decisión funcional.

Validación mínima:
- `src/scripts/check_b3_canonical_consumption.py`;
- `tests/harness/test_b3_i3_canonical_consumption.py`;
- `tests/core/test_runtime_contamination_guard.py`;
- búsquedas negativas dirigidas de autodeclaraciones o consumos stale materiales;
- verificación de que los prerrequisitos futuros quedaron documentados en su sede canónica sin comportamiento adelantado;
- `git diff --check`;
- revisión completa del worktree.

Criterio de cierre:
Los documentos legacy materiales ya no pueden confundirse razonablemente con autoridad vigente, la vista per-file está completa y derivada, y los requisitos futuros están anclados a sus hitos sin implementación prematura.

## 6. Orden, dependencias y paralelización

Orden obligatorio:
1. Misión 1.
2. Misión 2 y Misión 3 después de Misión 1.
3. Misión 4 al final.

Misión 2 y Misión 3 pueden ejecutarse en paralelo solo si:
- usan worktrees separados;
- existe reserva exclusiva de archivos;
- no comparten `config`/tests/superficies reales no previstas;
- existe una estrategia de integración autorizada.

Si commits locales no están autorizados, ejecutar secuencialmente en un solo worktree. No usar worktrees paralelos que luego requieran commits no autorizados para integrar.

## 7. Política de ejecución por misión

Cada misión debe comenzar comprobando estado vivo, archivos afectados y cambios preexistentes. El ejecutor puede revisar, corregir e iterar dentro del alcance hasta que las pruebas dirigidas pasen y el cambio sea coherente.

No se solicitan plantillas de autodeclaración ni respuestas `CLAVE=VALOR`. La evidencia válida es el contenido real del repositorio, diffs, tests, comandos y estado Git.

Al terminar cada misión, la entrega debe ser concisa y describir:
- cambios reales realizados;
- decisiones técnicas tomadas dentro de la autoridad permitida;
- pruebas ejecutadas y resultados;
- límites o STOP_LOCAL encontrados;
- archivos modificados y cualquier interacción con trabajo preexistente.

No commit ni push salvo autorización posterior.

## 8. Validación global y revisión independiente

Tras completar las cuatro misiones:
1. ejecutar todos los tests dirigidos definidos por las misiones;
2. ejecutar una regresión adicional proporcional sobre componentes compartidos que hayan cambiado;
3. ejecutar `git diff --check`;
4. revisar el diff completo y el estado Git;
5. buscar residuos de las contradicciones activas que este plan debía resolver;
6. confirmar que no se introdujo una segunda autoridad ni nomenclatura externa;
7. someter el resultado a revisión independiente del repositorio real antes de cualquier cierre, commit o promoción.

Una suite amplia no es obligatoria por defecto; debe ejecutarse si la amplitud real de los cambios o fallos encontrados demuestra que los tests dirigidos no dan cobertura suficiente.

## 9. Criterios globales de cierre

El plan se considera técnicamente implementado únicamente cuando:
- existe un mecanismo mínimo y probado de historial/sucesión material;
- existe una vista legacy per-file derivada y localizable;
- la deuda de evidencia B3-M1 está reconciliada sin reabrir B3;
- la progresión WorkLifecycle↔WorkResearchDossier falla cerrado donde corresponde;
- los residuos de fidelidad/audit posterior a M10/M11 ya no contradicen el flujo vigente;
- la curación activa coincide con los rangos y excepciones aprobados sin convertir cantidades en suficiencia;
- la ruta portable no depende universalmente de NotebookLM/Vault/path local;
- la duración de cierre no impone defaults universales por encima del envelope episódico;
- documentos legacy materiales tienen estado/sucesor/no ejecutabilidad inequívocos;
- los prerrequisitos futuros quedan registrados sin activar sus fases;
- tests dirigidos, regresión proporcional y `git diff --check` pasan;
- una revisión independiente confirma el estado real del repositorio.

El cierre técnico de este plan NO implica por sí mismo autorización de producto, R2, producción real, B5-I3, B6, B7, B7.5, commit o push.

## 10. Estado documental de implementación

Las Misiones 1–4 quedan reflejadas como técnicamente implementadas con evidencia en el control operativo. La cadena técnica de PLAN-008 fue confirmada como `PASS` por la revisión independiente, por lo que el plan queda `OWNER_CLOSED` y sin misión activa. Este cierre no autoriza producto, R2, B5-I3, B6, B7, B7.5 ni producción real; el push permanece no autorizado.
