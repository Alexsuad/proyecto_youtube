PLAN-001 / B3 — Perfil editorial y frontera del canal

Plan rector: ../001_reestructuracion_motor_agentico_editorial_y_harness.mdControl operativo: ../001_CONTROL_OPERATIVO.mdEspecificación funcional obligatoria: ../../docs/specifications/B3_especificacion_funcional_equipo_01.mdVersión derivada: PLAN-001 v1.4Estado del plan de ejecución: READY_FOR_EXTERNAL_AUDITEstado de implementación: IN_PROGRESSDependencia: B1–B2Siguiente misión autorizada: B3-I4 preflight; Gate resumido: producción consume un perfil activo, aprobado, versionado y trazable.

Estado operativo de B3

```text
B3-I1_IMPLEMENTATION: COMPLETED
B3-I1_TECHNICAL_AUDIT: PASS
B3-I2_IMPLEMENTATION: COMPLETED
B3-I2_EXTERNAL_TECHNICAL_AUDIT: PASS
B3-I2_COMMIT: 5872aa8cda6ff65cd2228ff3d681afbb8ff53f53
B3-I3_IMPLEMENTATION: COMPLETED
B3-I3_EXTERNAL_TECHNICAL_AUDIT: PASS
B3-I3_COMMIT: ad306fe46a9d58546369308be10716eea656afae
B3_PROFILE_STATUS: DRAFT
B3_IMPLEMENTATION_STATUS: BLOCKED
B3-I4_AUTHORIZATION: CONDITIONAL
B3-I4_PRIMARY_VOICE_SAMPLE: REQUIRED_AND_NOT_VERIFIED
B3-I4_TEAM_01_FUNCTIONAL_APPROVAL: REQUIRED
B3-I4_PREFLIGHT_IMPLEMENTATION: COMPLETED
B3-I4_PREFLIGHT_EXTERNAL_AUDIT: PASS
B3-I4_PRIMARY_SAMPLE_AVAILABLE: NO
B3-I4_AUTHORIZED_COMPLEMENTARY_SAMPLES: 0
B3-I4_INVALID_OR_INCOMPLETE_SAMPLES: 0
B3-I4_CORPUS_READY: NO
B3-I4_EXECUTION: BLOCKED_MISSING_PRIMARY_REAL_VOICE_SAMPLE
REAL_PROFILE_ACTIVATION: NOT_AUTHORIZED
TEAM_01_PROFILE_APPROVAL: NOT_REQUESTED
TECHNICAL_PROFILE_VALIDATION: NOT_EXECUTED
NEXT_ALLOWED_ACTION: PROVIDE_AUTHORIZED_PRIMARY_REAL_VOICE_SAMPLE
```

Este archivo es la única sede operativa del bloque B3 dentro del Plan 001. No crea autoridad funcional nueva ni sustituye el plan rector. La especificación del Equipo 01 define qué necesita el producto; este plan define cómo materializarlo técnicamente. Ante una contradicción, prevalecen, en este orden, las decisiones posteriores expresas del propietario, el documento rector de equipos, la especificación funcional aprobada del Equipo 01 y el Plan 001. Si la contradicción afecta alcance, autoridad, estados, contratos, gates o ejecución, la misión debe bloquearse hasta resolverla.

0. Uso operativo y decisión de alcance

0.1 Lectura mínima para ejecutar una misión de B3

AGENTS.md, si existe.

docs/ALCANCE_Y_COORDINACION_EQUIPOS.md.

docs/specifications/B3_especificacion_funcional_equipo_01.md.

plans/001_CONTROL_OPERATIVO.md.

plans/plan_001/B3_perfil_editorial_frontera_canal.md.

La misión concreta y los archivos expresamente autorizados.

No leer por defecto el Plan 001 completo, otros bloques, todo workspace/ ni reportes históricos. Consultar documentación adicional solo cuando este plan o la misión la referencien expresamente, o cuando sea necesario resolver una contradicción, dependencia o riesgo real.

0.2 Referencias normativas relacionadas

§8.1 Capa A — Inteligencia específica.

§8.2 Capa B — Motor profesional.

B1-C1 EditorialProfile.

Documento rector de alcance y coordinación de equipos.

Especificación funcional aprobada del Equipo 01 para B3.

0.3 Frontera técnica que debe construir B3

IDENTITY_STABLE
EDITORIAL_POLICY_VERSIONED
PLATFORM_POLICY_VERSIONED
FORMAT_PREFERENCE
EPISODE_DECISION
AUDIENCE_HYPOTHESIS
LEARNING_CANDIDATE

B3 no redefinirá la identidad ni decidirá contenido editorial. Tampoco profesionalizará todavía todo el motor de guion, packaging o aprendizaje pospublicación.

0.4 Resultado esperado

Al terminar B3 debe existir una ruta reproducible para:

especificación funcional aprobada
→ perfil estructurado candidato
→ validación de contrato y lineage
→ aprobación funcional sobre versión y checksum exactos
→ validación técnica sobre la misma versión y checksum
→ activación explícita
→ consumo canónico por las piezas autorizadas
→ invalidación controlada cuando cambie el perfil

1. Objetivo

Separar la inteligencia del canal del proceso de producción sin debilitar la identidad de Más Allá del Guion.

B3 debe permitir que el sistema:

identifique quién es el canal;

seleccione temas compatibles;

oriente briefs, investigación, tesis, guiones y auditorías;

mantenga una voz reconocible;

distinga identidad permanente de políticas configurables;

represente hipótesis y decisiones provisionales sin congelarlas;

incorpore aprendizajes sin contaminación automática;

mantenga compatibilidad con video, podcast y audio;

preserve trazabilidad, versionado, activación explícita e invalidación.

2. Regla contextual para Codex

Codex no dispone del contexto funcional histórico de los equipos. Por tanto:

no debe inferir necesidades del Equipo 01 desde workspace/;

no debe reconstruir la identidad desde documentación antigua;

no debe decidir qué quiso decir el Equipo 01;

no debe ampliar el alcance funcional;

no debe reinterpretar la especificación para conservar código legado;

no debe sustituir decisiones funcionales por decisiones técnicas propias;

si encuentra contradicción, debe aplicar la especificación aprobada y reportar la sede antigua como migración, compatibilidad o deprecación.

No se debe pegar toda la especificación dentro de cada prompt. La ruta canónica es el contexto obligatorio.

3. Capacidades operativas que debe usar Codex

Estas son skills del entorno de desarrollo y no dependencias del producto final.

Antes de crear o modificar una skill de B3, Codex debe usar, cuando estén instaladas:

decidir-tipo-pieza-sistema-agentico
crear-skill-desde-contrato
auditoria-agent-skills
verificar-no-mezcla-de-capas
harness-determinista
auditar-trazabilidad-input-output
tests-validacion-cierre
verificar-evidencia-minima-cierre

Uso requerido

decidir-tipo-pieza-sistema-agentico: antes de crear cualquier pieza nueva.

crear-skill-desde-contrato: solo cuando Equipo 04 ya haya autorizado una skill y definido su contrato.

auditoria-agent-skills: después de crear o modificar una skill.

verificar-no-mezcla-de-capas: comprobar separación entre identidad, guion, plataforma y aprendizaje.

harness-determinista: schemas, checksums, rutas, estados, manifests, activación e invalidación.

auditar-trazabilidad-input-output: comparar misión, alcance y archivos realmente modificados.

tests-validacion-cierre y verificar-evidencia-minima-cierre: antes de declarar READY_FOR_EXTERNAL_AUDIT.

Si una skill no está instalada, Codex debe reportarlo. No debe recrearla dentro del Proyecto YouTube ni sustituirla por documentación improvisada sin autorización.

4. Línea base verificada por Equipo 04

4.1 Matriz canónica de componentes

Antes de migrar o deprecar, cada componente relacionado con B3 debe clasificarse como:

CHANNEL_SOURCE
EDITORIAL_PROFILE_SOURCE
SCRIPT_ENGINE
HARNESS
DERIVATIVE
HISTORICAL
TEMPLATE
CONFIGURATION

La matriz debe indicar, como mínimo:

ruta;

tipo;

autoridad;

consumidor;

estado actual;

duplicaciones o solapamientos;

migración necesaria;

decisión KEEP | MODIFY | SPLIT | CONSOLIDATE | DEPRECATE | DO_NOT_TOUCH.

4.2 Componentes reutilizables

schemas/editorial_profile.json: base inicial de contrato, insuficiente y con estados de episodio.

schemas/editorial_learning_candidate.json: base de candidatos, insuficiente en evidence, lineage y fuente.

src/core/version_manifest.py: checksum y prevención de sobrescritura silenciosa.

src/core/invalidation.py: invalidación en memoria y bloqueo básico de candidatos.

schemas/gate_result.json: puede representar la validación técnica de un perfil exacto.

docs/contracts/README.md: sede de catálogo y reglas técnicas.

4.3 Mezclas o conflictos que B3 debe corregir

.agent/rules/00_reglas_globales.md obliga a leer directamente varias fuentes de workspace/.

.agent/skills/skill_crear_brief_episodio.md consume identidad y reglas dispersas.

.agent/skills/skill_guion_longform.md mezcla identidad, formato, plataforma y voz acumulada.

.agent/skills/skill_qa_editorial.md depende directamente de workspace/05c_voice_profile.md.

.agent/skills/skill_extraer_voice_learnings.md permite escribir directamente en el perfil acumulado tras una aprobación ambigua.

.agent/skills/skill_mapa_eventos_y_outline.md, .agent/workflows/piloto-outline.md y .agent/workflows/01_pipeline_episodio.md mantienen lecturas directas de fuentes antiguas.

workspace/03_formato_longform.md contiene decisiones de formato y YouTube que no pertenecen a identidad estable.

workspace/05c_voice_profile.md contiene aprendizajes sin muestra, checksum, confidence, lineage ni aprobación contractual suficiente.

reference/estilo_usuario/ no contiene todavía el corpus real principal aprobado.

4.4 Consecuencia de migración

Los documentos de workspace/ se conservarán inicialmente como fuentes de migración. No seguirán funcionando como fuente canónica directa para producción una vez activado el perfil nuevo.

Durante la transición podrá existir un adapter temporal que traduzca fuentes actuales al contrato nuevo. Ese adapter:

no se convertirá en sede permanente;

no reinterpretará decisiones funcionales;

no ocultará contradicciones;

deberá quedar identificado como compatibilidad temporal;

se retirará cuando los consumidores hayan migrado.

5. Decisiones técnicas cerradas por Equipo 04

5.1 EditorialProfile

schemas/editorial_profile.json se actualizará como contrato específico de perfil, no como artefacto de episodio.

Debe representar al menos:

identidad, propósito, posicionamiento y promesa;

mapa editorial sin cuotas automáticas;

territorios activos, experimentales, excluidos y pendientes;

audiencia como AUDIENCE_HYPOTHESIS_INITIAL, no como restricción rígida;

persona autoral y reglas de primera persona verdadera;

voz aprobada y referencias al corpus;

límites permanentes;

compatibilidad con video, podcast y audio;

decisiones pendientes;

referencias versionadas a políticas externas;

lineage de fuentes;

versión y checksum.

No debe incorporar como identidad estable:

duración;

estructura universal de guion;

número de obras;

cuotas por formato;

reglas del algoritmo de YouTube;

frecuencia de actualidad;

presencia en cámara;

grado fijo de exposición personal;

packaging, CTA o monetización.

5.2 Aprobación funcional separada

Crear schemas/editorial_profile_approval.json.

Debe ligar obligatoriamente:

profile_id;

profile_version;

profile_checksum;

decisión;

autoridad funcional TEAM_01;

identidad del aprobador;

fecha;

observaciones o condiciones.

La validación técnica utilizará GateResult con gate_id=B3_TECHNICAL_PROFILE_VALIDATION y evidencia que incluya el mismo checksum.

TEAM_01_PROFILE_APPROVAL
→ valida identidad, posicionamiento, audiencia, promesa, territorios,
  personalidad, voz, principios conceptuales y contenido funcional.

TECHNICAL_PROFILE_VALIDATION
→ valida contrato, compilación, lineage, versión, checksum,
  configuración e invalidación.

La validación técnica del Equipo 04 no autoriza el contenido funcional. La aprobación del Equipo 01 no sustituye la validación técnica.

5.3 Perfil activo y selección explícita

Crear schemas/active_editorial_profile.json y un archivo de configuración explícito:

config/active_editorial_profile.json

Debe referenciar una versión exacta y exigir:

ACTIVE_PROFILE_ID;

ACTIVE_PROFILE_VERSION;

checksum exacto;

aprobación funcional válida;

validación técnica PASS sobre el mismo checksum;

activación explícita;

actor autorizado;

fecha de activación.

Está prohibido seleccionar automáticamente “la última versión”.

5.4 Corpus de voz

Crear schemas/voice_sample.json.

Cada muestra debe registrar:

sample_id;

ruta o localizador;

checksum;

autoría;

tipo de texto;

clasificación CANONICAL | COMPLEMENTARY | EXCLUDED;

autorización de uso;

representatividad;

fecha y lineage;

razón de inclusión o exclusión.

El contenido bruto puede vivir fuera del perfil. El perfil solo referencia muestras aprobadas y patrones aprobados.

5.5 Aprendizajes de voz como candidatos

Modificar schemas/editorial_learning_candidate.json para exigir:

fuente y checksum;

evidence items concretos;

alcance;

confidence;

ejemplos y contraejemplos;

excepciones;

perfil objetivo;

decisión funcional;

historial de estados.

Reglas:

no escribir directamente en el perfil;

registrar candidatos;

acumular evidencia;

aprobar o rechazar;

crear nueva versión solo con aprobación funcional del Equipo 01 y validación técnica del Equipo 04;

una corrección aislada no se convierte automáticamente en regla;

CANDIDATE nunca puede alterar el perfil activo.

5.6 Política de cambio e invalidación

Un cambio de perfil se clasifica como:

NO_IMPACT
PARTIAL_INVALIDATION
FULL_INVALIDATION

Debe indicar qué episodios o artefactos requieren revisión.

Crear o modificar:

src/core/editorial_profile_registry.py
src/core/invalidation.py
src/scripts/compile_editorial_profile.py
src/scripts/validate_editorial_profile.py
src/scripts/activate_editorial_profile.py

Responsabilidades:

validación de schemas;

cálculo canónico de checksum;

registro de versión;

prevención de sobrescritura;

verificación de aprobaciones;

selección explícita del perfil activo;

persistencia del mapa de dependencias necesario para invalidación;

rechazo de activación si falta corpus mínimo o approvals.

El compilador no interpreta libremente documentos. Recibe un payload estructurado preparado a partir de decisiones funcionales aprobadas, valida, normaliza y registra.

5.7 Sede de perfiles

Crear una estructura mínima:

profiles/
  editorial/
    mas_alla_del_guion/
      1.0.0/
        profile_payload.json
        editorial_profile.json
        functional_approval.json
        technical_validation.json
  voice/
    samples/
    corpus_manifest.json

profile_payload.json es el candidato estructurado. editorial_profile.json es el artefacto compilado y con checksum. Ninguno se activa automáticamente.

5.8 Prohibición de lectura directa dispersa

Skills de brief, outline, guion y QA deben consumir el perfil activo exacto, no cinco o seis documentos internos de forma independiente.

Excepciones autorizadas:

compilación del perfil;

mantenimiento del perfil;

auditoría de lineage;

migración controlada.

5.9 Capacidades semánticas de B3

Se autorizan como candidatas estas capacidades, sujetas a auditoría de las meta-skills antes de materializarlas:

Capacidad

Pieza principal decidida

Apoyo determinista

Construir o actualizar un payload de perfil desde decisiones aprobadas

SKILL

schema + compilador

Auditar coherencia de un perfil candidato con la especificación funcional

SKILL + GATE

schema + checksum

Clasificar fuentes y muestras de voz

SKILL + SCRIPT

voice_sample + checksum

Bloquear contaminación y lecturas no autorizadas

REGLA + GATE

búsqueda/test determinista

Activar una versión exacta

GATE + SCRIPT

registry + approvals

Registrar e invalidar dependencias

SCRIPT

tests

Nombres definitivos recomendados, solo si la auditoría previa confirma que no existe una skill equivalente:

skill_construir_actualizar_editorial_profile
skill_auditar_coherencia_identidad
skill_clasificar_fuentes_y_muestras_voz

No crear una skill independiente para checksum, activación, estados o invalidación.

5.10 Frontera con B4, B5, B6, B7, B7.5 y B9.5

B3 crea las capacidades mínimas para construir, validar, activar y consumir el perfil.

B4 revisará responsabilidades, prompts, familias de skills y portabilidad del motor.

B5 consumirá el perfil para brief y diseño de pieza, sin decidir identidad.

B6 recibirá el perfil exacto en el context pack y mantendrá voz sin escribir aprendizajes.

B7 auditará la versión exacta usada y enviará cambios de identidad fuera de las correcciones de guion.

B7.5 consumirá políticas de plataforma externas a IDENTITY_STABLE.

B9.5 gobernará aprendizaje pospublicación y acumulación longitudinal. B3 solo define contratos y barreras para evitar contaminación.

6. Plan de implementación por misiones

No dividir en micromisiones. Máximo dos intentos agénticos para corregir el mismo error.

Misión B3-I1 — Contratos, estructura y payload inicial

Objetivo: dejar definido y validable el modelo de perfil, aprobación, activación, corpus y aprendizaje.

Archivos principales:

schemas/editorial_profile.json
schemas/editorial_profile_approval.json
schemas/active_editorial_profile.json
schemas/voice_sample.json
schemas/editorial_learning_candidate.json
docs/contracts/README.md
profiles/editorial/mas_alla_del_guion/1.0.0/profile_payload.json
profiles/voice/corpus_manifest.json
tests/core/test_all_schemas.py
tests/fixtures/synthetic_contracts.py

Trabajo:

Ajustar y crear schemas según la especificación funcional.

Crear estructura de perfiles y corpus.

Transcribir la especificación del Equipo 01 al payload inicial sin inventar decisiones.

Marcar como pendientes los datos no disponibles, especialmente la muestra real principal.

Actualizar catálogo de contratos.

Crear fixtures y pruebas de schema.

No hacer: runtime, activación, migración de consumidores, deprecación ni perfil activo.

Cierre: READY_FOR_EXTERNAL_AUDIT, nunca PASS autónomo.

Misión B3-I2 — Registro, compilación, validación, activación e invalidación

Dependencia: B3-I1 auditada y aprobada técnicamente.

Archivos principales:

src/core/editorial_profile_registry.py
src/core/invalidation.py
src/core/version_manifest.py, solo si es imprescindible
src/scripts/compile_editorial_profile.py
src/scripts/validate_editorial_profile.py
src/scripts/activate_editorial_profile.py
config/active_editorial_profile.json.example
tests/core/test_editorial_profile_registry.py
tests/core/test_invalidation.py
tests/harness/test_b3_profile_pipeline.py

Trabajo:

Compilar y validar determinísticamente un perfil candidato.

Registrar versión y checksum sin sobrescritura silenciosa.

Verificar aprobación funcional y validación técnica sobre el mismo artefacto.

Rechazar activación implícita o incompleta.

Persistir dependencias mínimas perfil→artefactos.

Clasificar invalidación como NO_IMPACT | PARTIAL_INVALIDATION | FULL_INVALIDATION.

Probar errores, exit codes y estados.

No hacer: activar el perfil real sin aprobación del Equipo 01 y autorización del propietario.

Misión B3-I3 — Skills mínimas y migración de consumidores

Dependencia: B3-I2 auditada y aprobada técnicamente.

Antes de tocar cada skill, usar las meta-skills indicadas en la sección 3.

Skills nuevas candidatas: solo las confirmadas por auditoría previa.

Skills, reglas y workflows existentes que deben migrarse:

.agent/rules/00_reglas_globales.md
.agent/skills/skill_crear_brief_episodio.md
.agent/skills/skill_guion_longform.md
.agent/skills/skill_qa_editorial.md
.agent/skills/skill_extraer_voice_learnings.md
.agent/skills/skill_mapa_eventos_y_outline.md
.agent/workflows/piloto-outline.md
.agent/workflows/01_pipeline_episodio.md

Trabajo:

Sustituir lecturas directas de identidad y voz por el perfil activo exacto.

Mantener políticas de formato y YouTube fuera de IDENTITY_STABLE.

Prohibir actualización directa de workspace/05c_voice_profile.md.

Enrutar aprendizajes a EditorialLearningCandidate.

Añadir gate de coherencia de identidad y gate anticonsumo disperso.

Crear pruebas deterministas que fallen si consumidores autorizados vuelven a leer fuentes antiguas directamente.

Mantener adapter temporal solo donde sea imprescindible.

Límite: no reescribir todavía la arquitectura completa de guion de B5/B6 ni la adaptación de B7.5.

Misión B3-I4 — Perfil real, corpus inicial y cierre del gate

Dependencia: infraestructura y consumidores aprobados.

Trabajo:

Incorporar la muestra real principal y muestras complementarias autorizadas.

Clasificarlas con lineage y checksum.

Producir patrones candidatos con ejemplos y contraejemplos.

Compilar el perfil real 1.0.0.

Obtener aprobación funcional del Equipo 01 sobre versión y checksum exactos.

Ejecutar validación técnica de Equipo 04.

Activar únicamente tras autorización expresa.

Ejecutar smoke del consumo canónico.

Bloqueo conocido: la muestra real principal mencionada por el Equipo 01 no está presente actualmente en el repositorio. Su ausencia no bloquea B3-I1–I3, pero sí impide cerrar B3-I4 y el gate completo.

7. Pruebas obligatorias

7.1 Contratos

perfil sin identidad estable falla;

audiencia rígida no puede presentarse como verdad confirmada;

políticas de plataforma no pueden incrustarse en el núcleo estable;

una muestra sin autoría, autorización o checksum falla;

un candidato sin evidencia o lineage falla;

schemas rechazan campos desconocidos cuando corresponda.

7.2 Aprobación y activación

no se activa sin aprobación funcional;

no se activa sin validación técnica PASS;

no se activa si checksums difieren;

no se selecciona “última versión” automáticamente;

no se sobrescribe una versión con contenido distinto;

un candidato CANDIDATE no modifica el perfil;

la activación deja evidencia del actor y la versión exacta.

7.3 Invalidación

cambio sin impacto no invalida artefactos;

cambio parcial identifica dependientes concretos;

cambio crítico de identidad produce invalidación completa;

ciclos de dependencias no producen bucles;

el registro de dependencias persiste entre ejecuciones.

7.4 Consumo canónico

brief, outline, guion y QA identifican profile_id, version y checksum;

los consumidores autorizados no leen directamente identidad o voz desde workspace/;

reglas YouTube permanecen separadas del perfil estable;

video, podcast y audio pueden compartir el mismo núcleo identitario;

el adapter de compatibilidad no se convierte en sede permanente.

7.5 Skills

pruebas de activación y no activación;

revisión de alcance y entradas/salidas;

no duplicación con skills existentes;

no mezcla de capas;

auditoría posterior con auditoria-agent-skills.

8. Evidencia mínima por misión

Codex debe entregar únicamente:

estado final;

archivos creados y modificados;

resumen breve de decisiones aplicadas;

comandos y pruebas ejecutados;

resultado de tests;

resumen de diff;

riesgos o bloqueos reales;

autoauditoría;

confirmación de no commit/push, salvo autorización posterior.

No pedir documentos narrativos extensos. Equipo 04 realizará auditorías, planes y correcciones documentales.

9. Política de eficiencia y recuperación

máximo dos iteraciones de Codex para corregir el mismo error;

si persiste, detener el ciclo y resolver por terminal con el propietario o entregar el código/archivo completo;

no repetir auditorías funcionales ya realizadas;

no pedir a Codex planes largos;

no usar varios subagentes leyendo los mismos archivos;

no corregir redacción de documentos temporales si no afecta ejecución, contrato, estado o seguridad;

preferir cambios agrupados y verificables a micromisiones.

10. Archivos fuera de alcance inmediato

No modificar en B3 salvo dependencia técnica demostrada:

planes B5–B10
skills de packaging, SEO, Shorts o copyright
producción audiovisual
publicación real
integraciones NotebookLM
configuración sensible
credenciales
output/ histórico

No borrar todavía los documentos workspace/. Primero se migra, se prueba y después se depreca de forma explícita.

11. Gate B3

PASS si:
- la especificación funcional canónica está registrada;
- existe EditorialProfile versionado;
- el perfil diferencia núcleo estable, políticas, preferencias, decisiones e hipótesis;
- los territorios activos, experimentales, excluidos y pendientes están clasificados;
- existe corpus inicial aprobado con lineage, checksum y nivel de confianza;
- el VoiceProfile contiene patrones aprobados o candidatos controlados con ejemplos y contraejemplos;
- TEAM_01_PROFILE_APPROVAL = PASS;
- TECHNICAL_PROFILE_VALIDATION = PASS;
- ambas evaluaciones corresponden a la misma versión y checksum;
- ACTIVE_PROFILE_ID y ACTIVE_PROFILE_VERSION son explícitos;
- no existe activación automática de la última versión;
- consumidores autorizados usan el perfil activo;
- un episodio puede identificar exactamente qué perfil usó;
- no hay actualización directa del VoiceProfile desde una corrección aislada;
- candidatos de aprendizaje no contaminan el perfil;
- invalidación y dependencias funcionan de forma persistente;
- el núcleo identitario sirve para video, podcast y audio;
- tests y smoke de B3 pasan.

BLOCKED si:
- falta la muestra real principal necesaria para cerrar el corpus;
- falta aprobación funcional del Equipo 01;
- falta validación técnica;
- checksums no coinciden;
- persisten lecturas dispersas no autorizadas;
- la solución mezcla identidad con YouTube o decisiones de episodio;
- Codex amplía el alcance funcional;
- una contradicción de autoridad o contrato permanece sin resolver.

12. Estado actual y siguiente decisión

B3_FUNCTIONAL_SPECIFICATION: AVAILABLE_AND_CANONICALIZED
B3_EXECUTION_PLAN_STATUS: READY_FOR_EXTERNAL_AUDIT
B3_IMPLEMENTATION_STATUS: BLOCKED
B3-I4_PREFLIGHT_IMPLEMENTATION: COMPLETED
B3-I4_PREFLIGHT_EXTERNAL_AUDIT: PASS
PRIMARY_SAMPLE_AVAILABLE: NO
AUTHORIZED_COMPLEMENTARY_SAMPLES: 0
INVALID_OR_INCOMPLETE_SAMPLES: 0
CORPUS_READY_FOR_B3-I4: NO
B3-I4_EXECUTION: BLOCKED_MISSING_PRIMARY_REAL_VOICE_SAMPLE
B3_PROFILE_STATUS: DRAFT
TEAM_01_PROFILE_APPROVAL: NOT_REQUESTED
TECHNICAL_PROFILE_VALIDATION: NOT_EXECUTED
REAL_PROFILE_ACTIVATION: NOT_AUTHORIZED
B3_KNOWN_CLOSURE_BLOCKER: PRIMARY_REAL_VOICE_SAMPLE_NOT_IN_REPOSITORY
NEXT_ALLOWED_ACTION: PROVIDE_AUTHORIZED_PRIMARY_REAL_VOICE_SAMPLE
