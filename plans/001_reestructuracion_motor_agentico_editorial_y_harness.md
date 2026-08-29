# PLAN 001 — Reestructuración del sistema agéntico, del motor editorial y del arnés de control

**Proyecto:** Más Allá del Guion / Proyecto YouTube  
**Repositorio de referencia:** `proyecto_youtube_2026-07-21_10-00-29.zip`  
**Versión del plan:** 1.4
**Fecha de revisión:** 2026-07-22
**Estado del snapshot:** `READY_FOR_EXTERNAL_AUDIT`; el estado vivo se resuelve exclusivamente en el control operativo.
**Estado vivo:** consultar exclusivamente `plans/001_CONTROL_OPERATIVO.md`; los estados y acciones de este documento son históricos/no normativos.
**Auditorías funcionales incorporadas:** `CHANNEL_INTELLIGENCE_APPROVED_WITH_REQUIRED_AMENDMENTS` + `SCRIPT_PRODUCT_APPROVED_WITH_REQUIRED_AMENDMENTS` + `YOUTUBE_ADAPTATION_APPROVED_WITH_REQUIRED_AMENDMENTS` + `PRE-B3-EVOLUTIONARY-ARCHITECTURE-ALIGNMENT`
**Implementación autorizada:** consultar exclusivamente el control operativo vigente.
**Progreso global inicial:** `0 %`  
**Ruta objetivo en el repositorio:** `plans/001_reestructuracion_motor_agentico_editorial_y_harness.md`

---

## 1. Propósito del plan

Este documento gobierna la recuperación, profesionalización y validación del sistema de creación de guiones de **Más Allá del Guion**.

El producto prioritario de este plan no es un generador abstracto para cualquier canal. Es:

> **El motor profesional de guiones de Más Allá del Guion, con capacidades generales identificadas, delimitadas y potencialmente extraíbles en el futuro.**

La identidad del canal debe quedar separada del proceso de producción del guion para mejorar trazabilidad, mantenimiento, pruebas y evolución. Sin embargo, **Más Allá del Guion continúa siendo el contexto funcional rector y el producto que debe demostrar calidad real durante todo el plan**.

Este documento funciona simultáneamente como:

- hoja de ruta de implementación;
- contrato de alcance entre Producto, Desarrollo y Auditoría;
- tablero de avance;
- registro de decisiones;
- sistema de gates por bloque;
- barrera contra desviaciones de la meta;
- referencia para auditar si los cambios mejoran el guion y no solo el repositorio;
- criterio verificable de cierre.

El objetivo no es aumentar el número de agentes, skills, scripts o documentos. El objetivo es que cada responsabilidad necesaria quede representada por la pieza correcta y produzca evidencia comprobable.

## Mapa global de implementación y prioridades

La prioridad activa del producto sigue siendo cerrar el núcleo profesional de Guion hasta `EDITORIAL_SCRIPT_APPROVED`. El estado vivo y la autorización de continuación se resuelven exclusivamente mediante `plans/001_CONTROL_OPERATIVO.md`. La adecuación textual del guion a YouTube forma parte del cierre previo a `EDITORIAL_SCRIPT_APPROVED`; packaging, preparación y distribución posteriores se conservan como segunda etapa diferida y no autorizada.

| Etapa global | Bloques | Objetivo y entregable principal | Dependencia / cierre | Estado |
|---|---|---|---|---|
| Fundaciones | B0–B2 | Gobernanza, contratos, gates y arnés técnico | Cierre técnico de B2; baseline de B0 en revisión de evidencia | B1–B2 completados; B0 abierto por recuperación |
| Inteligencia del canal | B3–B4 | `EditorialProfile`, responsabilidades y portabilidad | Aprobación funcional pendiente y ejecución real no demostrada | Recuperación activa en B3–B4 |
| Diseño editorial | B5-I1, B5-I2, B5-I3 | Evidencia, análisis, curación y tesis | Confirmación funcional pendiente en B5-I1; ejecución real y aprobación funcional pendientes en B5-I2 | Activa; B5-I3 no autorizado |
| Prototipo y escritura | B5.5, B6 | Prototipo, redacción, ensamblaje y edición | Diseño editorial cerrado | Pendiente |
| Aprobación del guion | B7 | Auditoría independiente y aprobación editorial | Guion exacto aprobado | Pendiente |
| Adaptación y distribución | B7.5, parte diferida de B8 y B8.5 | Packaging, plataforma y paquete de distribución | `EDITORIAL_SCRIPT_APPROVED` + autorización expresa | Diferida / no autorizada |
| Validación y aprendizaje | B9, B9.5 | Validar episodios y separar aprendizaje editorial de métricas de publicación | B7 / `EDITORIAL_SCRIPT_APPROVED`; aprendizaje editorial aplicable | Pendiente; publicación futura separada |
| Cierre y portabilidad | B10 | Cierre documental y portabilidad del núcleo de Guion | B9 + aprendizaje editorial aplicable de B9.5 | Pendiente |

La producción de Audio y Video no forma parte de este plan. Solo se contemplan contratos futuros de integración con repositorios o productos externos.

---

## 2. Objetivo de producto

Al finalizar el plan, el repositorio debe demostrar que puede producir guiones largos de Más Allá del Guion que sean:

- fieles a la identidad editorial del canal;
- investigados y trazables;
- estructuralmente sólidos;
- capaces de sostener una tesis no obvia;
- narrativamente progresivos;
- escritos por bloques sin perder coherencia global;
- naturales para locución;
- originales y legítimamente transformativos respecto a sus fuentes;
- auditables antes del cierre;
- aprobados editorialmente en una versión exacta;
- adecuados textualmente a YouTube sin deformar su tesis;
- evaluados separadamente en calidad editorial, adaptación a YouTube y riesgos de plataforma y derechos;
- aprobados editorialmente por un humano sobre una versión exacta del guion;
- preparados para registrar la versión publicada y generar aprendizajes controlados;
- generados mediante un sistema portable y no dependiente de un único IDE o proveedor.

### 2.1 Resultado editorial esperado

El sistema debe permitir que cada episodio responda, con evidencia, a estas preguntas:

```text
¿Qué promete el video?
¿Qué pregunta central intenta resolver?
¿Qué tipo de guion necesita este material?
¿Qué tesis provisional guía la investigación?
¿Existe evidencia suficiente para analizar responsablemente?
¿Por qué se eligieron estas obras o fuentes?
¿Qué aporta cada una y en qué orden?
¿Cómo cambia la comprensión del espectador?
¿Qué función cumple cada bloque?
¿Cómo se entrega la promesa inicial?
¿El guion funciona como una sola obra después del ensamblaje?
¿Suena natural al leerse en voz alta?
¿Transforma las fuentes sin copiar ni imitar?
¿La versión editorial final coincide exactamente con la aprobada?
¿El título, la miniatura, la apertura, el desarrollo y el cierre sostienen la misma promesa?
¿El paquete presenta el contenido sin clickbait engañoso?
¿Los riesgos de plataforma, monetización, copyright y contenido reutilizado están evaluados?
¿Existe una ruta de continuidad hacia otro contenido cuando sea pertinente?
¿La aprobación humana final corresponde al paquete exacto que se pretende publicar?
¿La versión efectivamente publicada puede registrarse y compararse con sus resultados?
```

### 2.2 No objetivo inmediato

Este plan no autoriza todavía:

- extraer el motor a un repositorio independiente;
- convertirlo en producto multicanal;
- crear una plataforma SaaS;
- declarar que sirve para cualquier tipo de canal;
- activar múltiples subagentes por defecto;
- automatizar publicación;
- sustituir la revisión humana final.

La extracción futura solo podrá evaluarse cuando el sistema especializado haya demostrado calidad y estabilidad dentro de Más Allá del Guion.

---

## 3. Flujo objetivo del episodio

El flujo completo esperado es:

```text
IDENTIDAD Y CONOCIMIENTO DEL CANAL
        ↓ compilación, aprobación funcional y validación técnica
EDITORIAL PROFILE ACTIVO
        ↓
EPISODE BRIEF
        ├── tipo de guion
        ├── política de fuentes y citas
        └── duración y alcance
        ↓
INVESTIGACIÓN Y ACCESO A EVIDENCIA
        ↓
EVIDENCE SUFFICIENCY GATE
        ↓
TESIS PROVISIONAL
        ↓
PRESELECCIÓN DE MATERIALES
        ↓
ANÁLISIS NARRATIVO Y HUMANO
        ↓
CURACIÓN FINAL Y FUNCIÓN NARRATIVA
        ↓
AUDIENCIA CONCRETA, PROMESA EDITORIAL E HIPÓTESIS TEMPRANA DE PACKAGING
        ↓
TESIS REFINADA
        ↓
RECORRIDO DEL ESPECTADOR
        ↓
ARQUITECTURA NARRATIVA GLOBAL
        ↓
DISEÑO ESPECÍFICO DE APERTURA Y CIERRE COMO COMPONENTES DE LA ARQUITECTURA
        ↓
OUTLINE DETALLADO Y PRESUPUESTO DE PALABRAS/BLOQUES
        ↓
PROTOTIPO EDITORIAL TEMPRANO, CUANDO CORRESPONDA
        ↓
REDACCIÓN POR BLOQUES CON MEMORIA GLOBAL
        ↓
ENSAMBLAJE DETERMINISTA
        ↓
EDICIÓN DE DESARROLLO
        ↓
EDICIÓN DE LÍNEA Y ORALIDAD
        ↓
READ-ALOUD REVIEW
        ↓
VERIFICACIÓN FACTUAL E INTERPRETATIVA
        ↓
REVISIÓN DE ORIGINALIDAD Y TRANSFORMACIÓN DE FUENTES
        ↓
VALIDACIONES OBLIGATORIAS INDEPENDIENTES SOBRE EL CANDIDATO FINAL:
SCRIPT_PRODUCT · CHANNEL_INTELLIGENCE · FACTUALIDAD/INTERPRETACIÓN/FIDELIDAD · YOUTUBE_ADAPTATION TEXTUAL
        ↓
APROBAR / CORREGIR / BLOQUEAR
        ↓
HALLAZGO Y RUTA DE CORRECCIÓN A LA FASE RESPONSABLE, SI APLICA
        ↓
NUEVA VERSIÓN Y REVALIDACIÓN, SI LA CORRECCIÓN CAMBIA EL CANDIDATO
        ↓
TODAS LAS APROBACIONES OBLIGATORIAS SOBRE LA MISMA VERSIÓN Y CHECKSUM
        ↓
EDITORIAL_SCRIPT_APPROVED
        ↓
PACKAGING FINAL Y PREPARACIÓN/DISTRIBUCIÓN POSTERIOR A YOUTUBE
        ↓
PACKAGING FINAL Y AUDITORÍA DE CORRESPONDENCIA DE PROMESA
        ↓
METADATOS, SHORTS Y CONTINUIDAD DE SESIÓN
        ↓
BRIEF DE PRODUCCIÓN AUDIOVISUAL Y DERECHOS
        ↓
AUDITORÍA DE PLATAFORMA, MONETIZACIÓN, COPYRIGHT Y REUTILIZACIÓN
        ↓
COMPILACIÓN DEL PAQUETE PREVIO A PRODUCCIÓN
        ↓
HUMAN_PRODUCTION_APPROVAL
        ↓
YOUTUBE_PRODUCTION_READY
        ↓
[PRODUCCIÓN AUDIOVISUAL Y REVISIÓN FINAL:
 FUERA DEL ALCANCE INMEDIATO DEL PLAN 001]
        ↓
HUMAN_PUBLICATION_APPROVAL, CUANDO EXISTAN ACTIVOS FINALES
        ↓
YOUTUBE_READY
        ↓
PUBLISHED, CUANDO EXISTA PUBLICACIÓN REAL
        ↓
REGISTRO DE LA VERSIÓN PUBLICADA
        ↓
APRENDIZAJES EDITORIALES Y DE YOUTUBE CANDIDATOS, NO AUTOMÁTICOS
```

La hipótesis temprana de packaging es una interfaz entre `SCRIPT_PRODUCT` y `YOUTUBE_ADAPTATION`. `YOUTUBE_ADAPTATION` define o aprueba su forma visible; `SCRIPT_PRODUCT` valida que la tesis y la arquitectura puedan cumplirla.

`EDITORIAL_SCRIPT_APPROVED`, `YOUTUBE_PRODUCTION_READY`, `YOUTUBE_READY` y `PUBLISHED` son estados distintos y no intercambiables.

El Plan 001 mantiene documentadas las etapas posteriores, pero la prioridad actual demuestra el núcleo profesional de Guion hasta `EDITORIAL_SCRIPT_APPROVED`. No puede declarar `YOUTUBE_READY` sin revisar la pieza audiovisual final exacta.

---

## 4. Fuentes rectoras y jerarquía de autoridad

La autoridad se interpreta por dominio funcional, no como una cadena lineal que permita a un documento invadir la especialidad de otra responsabilidad.

Cuando exista una contradicción, se aplicará esta jerarquía:

1. Decisiones explícitas y posteriores del propietario del proyecto.
2. Decisiones funcionales aprobadas del dominio competente:
   - `CHANNEL_INTELLIGENCE` para identidad, posicionamiento, audiencia, promesa de canal, voz y `EditorialProfile`;
   - `SCRIPT_PRODUCT` para tesis, investigación, curación, diseño, escritura, edición y aprobación editorial del guion;
   - `YOUTUBE_ADAPTATION` para audiencia concreta del episodio, promesa visible, packaging, adaptación a YouTube, plataforma, monetización, derechos y paquete de producción o publicación;
   - `TECHNICAL_GOVERNANCE` para arquitectura, contratos técnicos, schemas, estados, gates, pruebas, portabilidad e implementación.
4. Este Plan 001 versión 1.4, como traducción integrada y gobernada de esas decisiones.
5. Validaciones finales vigentes de las responsabilidades funcionales y técnicas competentes.
6. Auditoría funcional y arquitectónica del repositorio del 2026-07-21.
7. Auditoría editorial de skills y scripts.
8. Política de fraccionamiento de guiones largos.
9. Documento Maestro de Lecciones Aprendidas v1.5.
10. Guía Base para Gobernar Proyectos Agénticos.
11. Documentación vigente del repositorio que no contradiga las fuentes anteriores.
12. Reportes históricos y evidencias de `output/`.

### 4.1 Regla de autoridad

- Cada dominio o responsabilidad funcional decide y aprueba únicamente dentro de su especialidad.
- El Plan 001 coordina y traduce decisiones, pero no puede redefinir unilateralmente una decisión perteneciente a otra responsabilidad o dominio funcional.
- Una auditoría técnica no sustituye una aprobación funcional.
- Una aprobación funcional no sustituye una validación técnica.
- Un documento histórico conserva valor como evidencia, pero no puede gobernar una versión nueva del sistema.
- Un reporte del agente ejecutor no sustituye una auditoría externa.
- El plan no puede modificarse silenciosamente durante la implementación.
- El silencio del usuario no equivale a aprobación.

---

## 5. Baseline verificable

El plan parte del inventario auditado:

| Componente | Estado inicial |
|---|---:|
| Archivos totales | 89 |
| Skills Markdown | 21 |
| Scripts Python | 9 |
| Reglas | 3 |
| Workflows | 3 |
| Roles conceptuales | 11 |
| Agentes operativos reales | 1 |
| Subagentes independientes | 0 |
| Pruebas automatizadas | 0 |
| Schemas formales | 0 |
| Perfil editorial versionado | 0 |

### 5.1 Estado inicial

```text
SYSTEM_REVIEW: FAIL
PRODUCT_REVIEW: BLOCKED
PLAN_STATUS_PREVIOUS: REVISION_REQUIRED
PLAN_STATUS_CURRENT: READY_FOR_EXTERNAL_AUDIT
IMPLEMENTATION_AUTHORIZED: NO
```

### 5.2 Fallos críticos conocidos

El plan debe cerrar, como mínimo:

1. Gates que declaran `FAIL` y devuelven código de salida `0`.
2. Gates que producen `PASS` sin entradas obligatorias.
3. Cierre de episodios con entregables vacíos.
4. Parser del Gate V que puede interpretar un `FAIL` como `OK`.
5. Gate post-guion ejecutado antes de disponer de todos sus inputs.
6. Contratos incompatibles entre skill, template y script.
7. Lectura directa y acumulativa de documentos de `workspace/` durante la producción.
8. Rigidez de tres obras, tres eventos o marcadores literales como obligación universal.
9. Falta de edición de desarrollo, coherencia global y oralidad real.
10. Ausencia de pruebas automatizadas y schemas.
11. Duplicación de QA y documentos normativos.
12. Rutas locales, dependencia del CWD y portabilidad incompleta.
13. Aprobación humana situada antes de correcciones posteriores.
14. Falta de gate explícito de suficiencia de evidencia.
15. Falta de clasificación del tipo de guion y estrategia narrativa.
16. Falta de hipótesis de packaging antes del outline.
17. Mezcla funcional entre edición y auditoría final.
18. Falta de diseño formal del recorrido del espectador.
19. Falta de contratos propios para apertura y cierre.
20. Falta de política de originalidad, no copia y transformación de fuentes.
21. Falta de política de citas, atribuciones y visibilidad de fuentes.
22. Falta de enrutamiento de correcciones e invalidación de artefactos.
23. Falta de versionado completo del ciclo editorial del guion.
24. Aprendizaje de voz sin gobernanza suficiente.
25. Entregable final insuficientemente definido.
26. Validación editorial real demasiado tardía.

---

## 6. Cambios acumulados hasta la versión 1.2

Esta versión sustituye al borrador 1.0 e incorpora las correcciones obligatorias de Producto.

| Cambio | Estado en v1.1 |
|---|---|
| Sustituir “motor general” por motor especializado con capacidades extraíbles | Incorporado |
| Hipótesis de promesa y packaging antes del outline | Incorporado |
| Separación funcional entre Editor y Auditor | Incorporado |
| Gate de suficiencia de evidencia | Incorporado |
| Clasificación del tipo de guion | Incorporado |
| Recorrido del espectador | Incorporado |
| Contratos de apertura y cierre | Incorporado |
| Enrutamiento de correcciones e invalidación | Incorporado |
| Originalidad y transformación de fuentes | Incorporado |
| Versionado de todas las transformaciones del guion | Incorporado |
| Aprendizaje editorial gobernado | Incorporado |
| Contrato detallado de entregables finales | Incorporado |
| Benchmarks editoriales desde el baseline | Incorporado |
| Prototipo editorial controlado antes de la redacción completa | Incorporado |
| Política de citas y referencias | Incorporado |
| Read-aloud review real | Incorporado |

### 6.1 Cambios incorporados en la versión 1.2

| Cambio | Estado en v1.2 |
|---|---|
| Adaptación a YouTube como capa completa | Incorporado |
| Separación entre aprobación editorial y aprobación de publicación | Incorporado |
| Auditoría de correspondencia de promesa | Incorporado |
| Packaging final versionado | Incorporado |
| Plataforma y monetización contextual | Incorporado |
| Copyright, Content ID y reutilización | Incorporado |
| Brief audiovisual y de derechos | Incorporado |
| Continuidad de sesión | Incorporado |
| Paquete de publicación | Incorporado |
| Registro publicado y aprendizaje controlado | Incorporado |

El Plan 001 v1.0 queda marcado como `SUPERSEDED_BY_PLAN_001_V1_1`.

El Plan 001 v1.1 queda marcado como `SUPERSEDED_BY_PLAN_001_V1_2`.

La versión 1.4 es la versión rectora vigente del Plan 001. Su continuación de implementación y autorización se resuelven exclusivamente mediante el control operativo.

---

## 7. Principios no negociables

### 7.1 Más Allá del Guion sigue siendo el producto rector

La separación de identidad y proceso no autoriza a diluir la fórmula, la voz o la propuesta editorial del canal. Las abstracciones se justifican solo si mejoran el producto real.

### 7.2 Conservar y corregir antes de reconstruir

No se autoriza crear un repositorio nuevo ni reescribir todo el sistema durante los primeros bloques.

### 7.3 El repositorio es la fuente de verdad

Ninguna decisión estable puede vivir únicamente en un chat, una herramienta de investigación externa o la memoria de un IDE agéntico.

### 7.4 La identidad se separa del proceso, pero no se elimina

Los documentos internos del canal alimentan un perfil editorial versionado. El proceso de guion consume ese perfil y conserva trazabilidad a las fuentes que lo originaron.

### 7.5 Producción, edición y aprobación son responsabilidades distintas

```text
GUIONISTA → produce y corrige bajo instrucción
EDITOR → diagnostica y mejora
AUDITOR → evalúa la versión editada y aprueba o bloquea
```

El Editor no emite el dictamen editorial final sobre su propia intervención.

### 7.6 Evidencia insuficiente bloquea la escritura

El sistema no puede fingir acceso directo a una obra, escena o fuente. Debe declarar límites y bloquear cuando no exista material responsablemente utilizable.

### 7.7 Un archivo ausente o vacío nunca puede producir PASS

La ausencia de una entrada obligatoria produce `BLOCKED` o `FAIL`, según la causa documentada.

### 7.8 Los gates deben bloquear de verdad

Estado, código de salida, reporte y estado del episodio deben ser coherentes.

### 7.9 La estructura habitual es preferencia fuerte, no obligación universal

La fórmula reconocible de Más Allá del Guion se conserva cuando funciona. Solo se modifica cuando el tema, la tesis, el material o la experiencia del espectador lo justifican.

### 7.10 El guion se diseña completo antes de fraccionarse

No se redactan bloques sin tesis refinada, recorrido del espectador, outline, presupuesto y contratos aprobados.

### 7.11 Fraccionar la escritura no fragmenta la memoria

Cada bloque debe conocer el plan completo, los bloques previos, lo pendiente, las fuentes autorizadas y lo que no puede repetir.

### 7.12 La IA no sustituye controles deterministas

Estados, rutas, hashes, existencia, vacíos, manifest, presupuestos, ensamblaje, versiones e invalidaciones se controlan determinísticamente cuando sea razonable.

### 7.13 No se degrada contenido para superar un validador

Un gate automático no puede forzar simplificaciones editoriales incorrectas.

### 7.14 No se crean componentes por entusiasmo

No se crea un agente si basta una responsabilidad o modo. No se crea una skill si basta un script, gate, regla o checklist.

### 7.15 El adaptador de investigación externo es opcional, no el runtime

El pipeline debe conservar un camino local, auditable y portable.

### 7.16 La aprobación humana se aplica a una versión exacta

Cualquier cambio posterior invalida la aprobación y obliga a repetir los gates correspondientes.

### 7.17 Una corrección humana no se convierte automáticamente en regla

Los aprendizajes de voz pasan por evidencia, clasificación y aprobación.

### 7.18 El sistema es evolutivo, no cerrado

El núcleo técnico permanece separado de decisiones editoriales variables.
Identidad, políticas de YouTube, proveedores de IA, canales de entrada, formatos y auditorías deben poder cambiar por configuración, contratos versionados o adaptadores.

Añadir una nueva capacidad no debe obligar a reconstruir el motor.
Los cambios deben invalidar únicamente artefactos dependientes.
Debe conservarse historial, lineage, razón del cambio y posibilidad de rollback cuando aplique.

Las decisiones editoriales, las políticas de plataforma, los canales de entrada, las auditorías y los proveedores de IA son componentes versionados y reemplazables.

---

## 8. Arquitectura objetivo por capas

### 8.1 Capa A — Inteligencia específica de Más Allá del Guion

Contiene:

- identidad;
- propósito;
- posicionamiento;
- audiencia;
- promesa principal y beneficios secundarios;
- relación con la audiencia;
- personalidad de marca;
- rol del narrador;
- territorios editoriales;
- pilares;
- exclusiones;
- criterios de selección temática;
- tono y voz;
- principios conceptuales de títulos y miniaturas;
- política de spoilers;
- límites éticos;
- política de análisis psicológico no clínico;
- preferencias narrativas;
- reglas de formatos;
- criterios de calidad;
- lentes editoriales;
- política anti-clichés;
- política de citas y atribuciones;
- aprendizajes aprobados;
- decisiones pendientes;
- confianza y razón de los cambios.

Salida canónica:

```text
EditorialProfile
```

Los documentos de `workspace/` se mantienen inicialmente como fuentes de mantenimiento, no como dependencias directas dispersas durante cada ejecución.

### 8.2 Capa B — Motor profesional de guiones de Más Allá del Guion

Contiene las capacidades de:

- brief;
- clasificación del tipo de guion;
- investigación;
- evaluación de acceso y evidencia;
- tesis provisional;
- curación;
- hipótesis de packaging;
- tesis refinada;
- recorrido del espectador;
- apertura y cierre;
- arquitectura narrativa;
- presupuesto;
- redacción por bloques;
- ensamblaje;
- edición de desarrollo;
- edición de línea y oralidad;
- verificación factual e interpretativa;
- originalidad y transformación;
- auditoría final;
- enrutamiento de correcciones.

Estas capacidades pueden contener elementos generalizables, pero durante este plan se validan exclusivamente como parte del producto Más Allá del Guion.

### 8.3 Capa C — Arnés, gobernanza e infraestructura

Contiene:

- orquestación;
- máquina de estados;
- gates;
- códigos de salida;
- schemas;
- validación contractual;
- manifest de versiones;
- invalidación;
- evidencia;
- fixtures;
- pruebas;
- rutas y configuración;
- logs;
- portabilidad;
- recuperación ante bloqueo.

### 8.4 Capa D — Adaptación a YouTube, publicación y aprendizaje

La adecuación textual del guion a YouTube se valida antes de `EDITORIAL_SCRIPT_APPROVED`. Esta capa continúa después de esa aprobación con packaging, publicación y aprendizaje posteriores; no desplaza la validación textual al tramo post-aprobación.

Su responsabilidad es convertir una pieza editorial aprobada en un producto publicable, descubrible, coherente y conectado dentro de YouTube, sin deformar la identidad del canal ni la tesis del contenido.

Incluye:

- audiencia concreta del episodio;
- promesa visible;
- hipótesis de packaging previa;
- adecuación de la apertura a la expectativa del clic;
- adecuación de la duración a la propuesta;
- correspondencia entre título, miniatura, apertura, desarrollo y cierre;
- packaging definitivo;
- metadatos y paquete de publicación;
- capítulos provisionales y capítulos finales cuando exista edición audiovisual;
- Shorts y otros derivados con función estratégica;
- continuidad de sesión;
- pantalla final, playlist, comentario fijado y video siguiente;
- evaluación contextual de riesgo de plataforma y monetización;
- copyright, Content ID y contenido reutilizado;
- contenido sintético o alterado, cuando corresponda;
- brief de producción audiovisual y derechos;
- compilación del paquete exacto que se pretende publicar;
- aprobación humana final del paquete;
- registro manual de la versión publicada;
- captura inicial de desempeño;
- aprendizajes de YouTube candidatos y gobernados.

La hipótesis temprana de packaging se produce durante el diseño editorial, pero su autoridad funcional corresponde a `YOUTUBE_ADAPTATION` en coordinación con `SCRIPT_PRODUCT`. `SCRIPT_PRODUCT` valida su entregabilidad editorial; `YOUTUBE_ADAPTATION` valida su forma visible y adecuación a YouTube. El packaging final y los paquetes de producción o publicación pertenecen a `YOUTUBE_ADAPTATION`.

Esta capa no garantiza monetización, distribución ni rendimiento. Evalúa riesgos, coherencia y preparación con la evidencia disponible.

Quedan fuera del alcance inmediato:

- publicación automática por API;
- descarga automática de analíticas;
- gestión automática de experimentos;
- edición audiovisual;
- generación física de miniaturas;
- integración avanzada con YouTube Studio.

---

## 9. Modelo funcional y agéntico objetivo

### 9.1 Responsabilidades operativas base y familias funcionales transversales

| Responsabilidad | Función principal | Capacidad de veto |
|---|---|---:|
| Orquestación | Coordina estados, gates, reintentos, versiones y evidencia | Sí, por sistema |
| Investigación y curación | Investiga, clasifica, contrasta y selecciona materiales | Sí, por evidencia insuficiente |
| Arquitectura narrativa | Define tesis, promesa, recorrido, apertura, cierre, outline y presupuesto | Sí, antes de redactar |
| Escritura | Redacta bloques y aplica correcciones autorizadas | No aprueba |
| Edición | Mejora desarrollo, continuidad, línea y oralidad | No aprueba su propia edición |
| Auditoría editorial independiente | Evalúa la versión editada y emite PASS/WARN/FAIL/BLOCKED | Sí |

### 9.1.1 Inteligencia del Canal como familia funcional transversal

Inteligencia del Canal no se convierte automáticamente en un agente adicional.

Su contenido funcional pertenece a `CHANNEL_INTELLIGENCE` y debe incluir capacidades para:

- construir o actualizar el `EditorialProfile`;
- auditar coherencia de identidad;
- detectar contaminación del perfil;
- comprobar pertenencia temática;
- revisar la coherencia entre posicionamiento, audiencia y promesa;
- clasificar cambios de identidad;
- controlar la evolución de voz;
- registrar decisiones pendientes;
- validar aprendizajes antes de activarlos;
- bloquear versiones funcionalmente no aprobadas.

`TECHNICAL_GOVERNANCE` decidirá si cada capacidad se materializa como skill, regla, gate, workflow, compilador, auditoría o checklist.

La implementación técnica no puede sustituir la aprobación funcional de `CHANNEL_INTELLIGENCE`.

### 9.1.2 Adaptación a YouTube como capa funcional transversal

Adaptación a YouTube no se convierte automáticamente en un séptimo agente.

Sus capacidades se materializarán mediante:

- contratos;
- skills especializadas;
- workflows;
- gates independientes;
- revisiones en contexto separado;
- artefactos versionados;
- aprobación humana del paquete de publicación.

La implementación debe preservar estas separaciones:

```text
Auditoría editorial
≠
Auditoría de adaptación a YouTube
≠
Auditoría de plataforma, monetización y derechos
```

La responsabilidad que evalúe riesgos de plataforma o derechos no puede sustituir la aprobación editorial, y la adaptación no puede alterar unilateralmente la tesis para aumentar el clic.

### 9.2 Esto no obliga a crear un agente por responsabilidad o familia

Durante este plan:

```text
AGENTES OPERATIVOS REQUERIDOS: 1
SUBAGENTES REALES REQUERIDOS: 0
RESPONSABILIDADES OPERATIVAS BASE: 6
FAMILIAS FUNCIONALES TRANSVERSALES:
- INTELIGENCIA_DEL_CANAL
- ADAPTACION_A_YOUTUBE
```

Las responsabilidades pueden implementarse con:

- modos operativos;
- prompts oficiales;
- skills;
- ejecuciones separadas;
- contextos limpios;
- artefactos independientes;
- reinicio de sesión para auditoría final.

### 9.3 Mapeo desde los once roles actuales

| Rol actual | Destino propuesto |
|---|---|
| Orquestador | Mantener como responsabilidad de Orquestación |
| Investigador | Integrar en Investigación y curación |
| Curador | Integrar en Investigación y curación |
| Planner | Integrar en Arquitectura narrativa |
| Analista | Integrar en Arquitectura narrativa |
| Sintetizador | Integrar en Arquitectura narrativa |
| Guionista | Mantener como Escritura |
| QA Editorial | Dividir en Edición y Auditoría editorial independiente |
| Shorts Writer | Skill de Adaptación a YouTube posterior a aprobación editorial, clasificada por función |
| Packaging | Hipótesis editorial previa + decisión final de packaging + auditoría de correspondencia |
| SEO | Integrar en la capacidad de Metadatos y paquete de publicación |

### 9.4 Criterios para autorizar subagentes futuros

Solo después de la validación final podrá justificarse un subagente por:

- necesidad de aislamiento real;
- contexto excesivo;
- ejecución paralela útil;
- especialización de proveedor;
- evidencia propia;
- capacidad de veto no garantizable en modo único;
- mejora demostrada frente al coste añadido.

---

## 10. Estados canónicos

### 10.1 Estados de gates

```text
PASS
WARN
FAIL
BLOCKED
```

- `PASS`: cumple y puede continuar.
- `WARN`: puede continuar solo si la política específica lo permite y queda registrado.
- `FAIL`: se evaluó y el resultado incumple el contrato.
- `BLOCKED`: no puede evaluarse por falta de entrada, evidencia, dependencia o autorización.

### 10.2 Códigos de salida

```text
PASS    -> 0
WARN    -> 0
FAIL    -> 1
BLOCKED -> 2
ERROR   -> 3
```

### 10.3 Estados de misión

```text
PLANNED
IN_PROGRESS
BLOCKED
READY_FOR_AUDIT
PASS
SUPERSEDED
```

Una misión no alcanza `PASS` por el reporte del ejecutor. Requiere auditoría externa.

### 10.4 Estados mínimos del episodio

```text
CREATED
BRIEF_APPROVED
RESEARCH_READY
EVIDENCE_REVIEWED
THESIS_PROVISIONAL_READY
CURATION_APPROVED
PACKAGING_HYPOTHESIS_APPROVED
THESIS_REFINED_READY
VIEWER_JOURNEY_APPROVED
OUTLINE_APPROVED
PROTOTYPE_VALIDATED
DRAFTING
ASSEMBLED
DEVELOPMENT_EDITED
LINE_EDITED
READ_ALOUD_REVIEWED
FACT_CHECKED
ORIGINALITY_REVIEWED
FINAL_EDITORIAL_AUDITED
EDITORIAL_SCRIPT_APPROVED
YOUTUBE_ADAPTED
PLATFORM_AND_RIGHTS_REVIEWED
PUBLICATION_PACKAGE_READY
YOUTUBE_PRODUCTION_READY
YOUTUBE_READY
PUBLISHED
PERFORMANCE_RECORDED
COMPLETED
```

No se puede saltar de `CREATED` a `COMPLETED` por existencia de archivos.

Las fronteras son:

```text
YOUTUBE_PRODUCTION_READY
→ guion, packaging, briefs, metadatos provisionales y riesgos
  aprobados para producción.

YOUTUBE_READY
→ archivo audiovisual final, miniatura final, título final,
  descripción final, capítulos reales, clips, música, contenido
  sintético y derechos reales de la versión exacta fueron auditados.

PUBLISHED
→ esa versión exacta fue publicada y registrada.
```

El Plan 001 no puede declarar `YOUTUBE_READY` utilizando únicamente guion, briefs y metadatos provisionales.

### 10.5 Estados de aprendizaje editorial

```text
CANDIDATE
RECURRING
APPROVED
REJECTED
SUPERSEDED
```

---

## 11. Modelo de artefactos y versionado

### 11.1 Versiones mínimas del ciclo editorial

```text
brief_v1
research_pack_v1
evidence_report_v1
thesis_provisional_v1
curation_v1
packaging_hypothesis_v1
thesis_refined_v1
viewer_journey_v1
outline_v1
draft_blocks_v1
assembled_script_v1
development_edit_v1
line_edit_v1
fact_checked_v1
originality_reviewed_v1
final_candidate_v1
human_approved_v1
```

Una corrección sustancial genera una nueva versión:

```text
final_candidate_v2
```

### 11.2 Regla de inmutabilidad

- Un artefacto aprobado no se sobrescribe silenciosamente.
- Una nueva versión registra su origen y motivo.
- La aprobación humana referencia `artifact_id`, versión y checksum.
- Cualquier modificación posterior invalida la aprobación.

### 11.3 Manifest de versión

Debe registrar:

```text
artifact_id
artifact_type
version
parent_artifact
created_at
created_by_role
source_artifacts
source_versions
checksum
change_summary
invalidation_reason
invalidated_artifacts
required_revalidation
status
```

---

## 12. Tablero maestro de avance

| Bloque | Nombre | Dependencia | Estado inicial | Gate de cierre |
|---:|---|---|---|---|
| B0 | Gobernanza, baseline y benchmarks | Ninguna | `OPEN` | `EVIDENCE_REVIEW_REQUIRED` |
| B1 | Contratos, schemas, estados y versionado | B0 | `PASS` | Contratos canónicos aprobados |
| B2 | Reparación del arnés y gates críticos | B1 | `PASS` | Cero falsos PASS conocidos |
| B3 | Perfil editorial y frontera del canal | B1–B2 | `OPEN` | `FUNCTIONAL_APPROVAL_PENDING` |
| B4 | Responsabilidades, skills, prompts y portabilidad | B3 | `OPEN` | `CONTRACTUAL_FOUNDATION_PASS / OPERATIONAL_EXECUTION_PENDING` |
| B5 | Profesionalización del diseño editorial | B3–B4 | `IN_PROGRESS` | `B5-I1 = TECHNICAL_PASS / FUNCTIONAL_CONFIRMATION_PENDING`; `B5-I2 = IMPLEMENTED_AND_MOCK_TESTED / REAL_EXECUTION_AND_FUNCTIONAL_APPROVAL_PENDING`; B5-I3 no autorizado |
| B5.5 | Prototipo editorial controlado | B5 | `PLANNED` | Mejora editorial temprana demostrada |
| B6 | Redacción, ensamblaje, edición y verificación | B5.5 | `PLANNED` | Candidato final coherente y trazable |
| B7 | Auditoría editorial independiente y candidato aprobado | B6 | `PLANNED` | Guion aprobado editorialmente |
| B7.5 | Adaptación profesional a YouTube | B7 | `DEFERRED_NOT_AUTHORIZED` | Packaging y distribución futuras |
| B8 | Plataforma, monetización, copyright y paquete para producción | B7.5 | `DEFERRED_NOT_AUTHORIZED` | Plataforma y derechos futuros |
| B8.5 | Aprobación para producción y cierre `YOUTUBE_PRODUCTION_READY` | B8 | `DEFERRED_NOT_AUTHORIZED` | Producción futura |
| B9 | Validación con tres episodios completos | B7 / `EDITORIAL_SCRIPT_APPROVED` | `PLANNED` | Validación del núcleo profesional de Guion |
| B9.5 | Aprendizaje editorial controlado | B9 | `PLANNED` | Aprendizaje editorial; distribución diferida |
| B10 | Lean/5S, portabilidad, documentación y cierre | B9 + aprendizaje editorial B9.5 | `PLANNED` | Cierre de Etapa 1 y portabilidad |

---

# 13. Bloque B0 — Gobernanza, baseline y benchmarks editoriales

## 13.1 Objetivo

Congelar el comportamiento actual, reproducir los fallos conocidos, crear el sistema de seguimiento y establecer referencias de calidad antes de modificar el motor.

## 13.2 Misiones

### B0-M1 — Incorporar el plan y su seguimiento

**Acciones:**

- crear `plans/` si no existe;
- incorporar la versión vigente del Plan 001;
- crear o actualizar `plans/plan_001/README.md`;
- marcar el borrador 1.0 como sustituido, si se conserva;
- registrar estados y jerarquía documental;
- crear tablero de avance con responsable, fecha y evidencia por misión.

**Criterios de aceptación:**

- solo existe una versión activa del Plan 001;
- el plan identifica claramente qué está autorizado y qué no;
- cada bloque tiene gate de cierre;
- ningún reporte histórico se presenta como normativa activa.

### B0-M2 — Baseline técnico reproducible

**Acciones:**

- ejecutar compilación de scripts;
- registrar árbol del repositorio;
- registrar versiones de Python y sistema;
- reproducir todos los fallos críticos conocidos;
- crear fixtures sintéticos sin datos reales;
- registrar comandos y códigos de salida;
- capturar dependencia del CWD y rutas locales.

**Ruta propuesta:**

```text
reports/implementation/plan_001/B0_baseline/
```

### B0-M3 — Pruebas de caracterización

Deben reproducir:

- `FAIL` con exit `0`;
- PASS sin inputs;
- cierre con entregables vacíos;
- parser ambiguo del Gate V;
- output dependiente del CWD;
- orden incorrecto del gate post-guion;
- aprobación humana invalidada por cambios posteriores, si el flujo actual lo permite.

Pueden comenzar como `xfail`, pero deben demostrar el defecto de forma estable.

### B0-M4 — Benchmarks editoriales

Crear un conjunto protegido y trazable con:

1. un guion humano aprobado del canal;
2. un guion actual del sistema con problemas conocidos;
3. un ejemplo negativo genérico;
4. un ejemplo con buena estructura y mala redacción;
5. un ejemplo de buena oralidad;
6. un caso de análisis psicológicamente irresponsable;
7. un ejemplo de dependencia excesiva o copia estructural de una fuente.

Cada benchmark debe incluir:

```text
benchmark_id
purpose
source
approval_status
known_strengths
known_failures
allowed_use
privacy_level
```

### B0-M5 — Rubric editorial inicial

La rubric debe medir, como mínimo:

- interés;
- profundidad;
- tesis;
- progresión;
- naturalidad;
- voz;
- oralidad;
- originalidad;
- rigor;
- cumplimiento de promesa;
- calidad de apertura;
- calidad de cierre;
- necesidad de reescritura humana;
- claridad;
- densidad informativa;
- coherencia local;
- coherencia entre bloques;
- suficiencia de contexto narrativo;
- resonancia emocional sin manipulación;

No se fijarán umbrales arbitrarios sin observar el baseline.

Cuando sea viable, los benchmarks se compararán mediante evaluación ciega, sin revelar si el texto procede del sistema antiguo, del sistema nuevo o de una referencia humana.

## 13.3 Archivos propuestos

```text
plans/001_reestructuracion_motor_agentico_editorial_y_harness.md
plans/plan_001/README.md
reports/implementation/plan_001/B0_baseline/
tests/characterization/
benchmarks/editorial/
docs/evaluation/editorial_rubric.md
```

## 13.4 Gate B0

```text
PASS si:
- los fallos conocidos se reproducen o documentan con fixture;
- la compilación base queda registrada;
- los benchmarks están disponibles y clasificados;
- la rubric inicial está aprobada por Producto;
- no se ha modificado aún la semántica del pipeline;
- existe evidencia de comandos y Git.
```

---

# 14. Bloque B1 — Contratos, schemas, estados y versionado

## 14.1 Objetivo

Definir una única fuente de verdad para entradas, salidas, estados, versiones, correcciones y entregables antes de modificar scripts o skills.

## 14.2 Contratos obligatorios

### B1-C1 — EditorialProfile

Campos mínimos:

```text
profile_id
channel_id
version
status
created_at
updated_at

functional_owner
functional_approval_status
functional_approved_by
functional_approved_at

identity
purpose
positioning
primary_promise
secondary_benefits

audience
audience_relationship
brand_personality
narrator_role

editorial_territories
pillars
exclusions
topic_selection_criteria

tone
language
voice_rules

conceptual_title_principles
conceptual_thumbnail_principles

ethical_limits
psychological_analysis_policy
spoiler_policy
citation_style
attribution_policy
quotation_policy
source_visibility

themes
formats
narrative_preferences
quality_criteria
required_elements
forbidden_elements

stable_brand_core
editorial_preferences
format_rules
transversal_policies
approved_learnings

decision_confidence
pending_identity_decisions
change_rationale

source_lineage
source_hashes
checksum
```

El contenido debe conservar diferenciadas estas dimensiones, aunque se compile en un solo artefacto:

```text
NÚCLEO_ESTABLE_DE_MARCA
PREFERENCIAS_EDITORIALES
REGLAS_DE_FORMATO
POLÍTICAS_TRANSVERSALES
APRENDIZAJES_APROBADOS
DECISIONES_PENDIENTES
```

La aprobación funcional del contenido corresponde a `CHANNEL_INTELLIGENCE`. La validación técnica del contrato, compilación, lineage, versionado, checksum e invalidación corresponde a `TECHNICAL_GOVERNANCE`.

### B1-C2 — EpisodeBrief

```text
episode_id
profile_id
profile_version
tema
pregunta_central
conflicto_o_tension
tesis_provisional
objetivo
transformacion_esperada
audiencia_concreta
angulo_diferencial
alcance
fuera_de_alcance
spoilers
tono
duracion_objetivo
ritmo_locucion
nivel_investigacion
fuentes_requeridas
obra_o_fuente_principal
tipo_de_guion_principal
tipo_de_guion_secundario
estructura_candidata
razon_de_eleccion
citation_style
attribution_policy
quotation_policy
source_visibility
salida_esperada
```

No se imponen cantidades arbitrarias sin política editorial aprobada.

### B1-C3 — SourceAccessAndEvidenceReport

```text
material_principal_disponible
tipo_de_acceso
fuentes_primarias
fuentes_secundarias
escenas_verificadas
escenas_descritas_indirectamente
claims_sostenibles
claims_pendientes
limitaciones
nivel_de_confianza
can_proceed
required_disclosures
```

### B1-C4 — PackagingHypothesis

```text
episode_audience
audience_profile_ref
audience_knowledge_assumption
recognized_tension
relevance_reason
expectation_to_avoid

promesa_de_clic
titulo_de_trabajo
concepto_de_miniatura
pregunta_que_el_espectador_espera_resolver
diferenciador_del_video
riesgo_de_sobrepromesa

functional_owner_role
authorized_approval_status
authorized_approved_by
authorized_approved_at

alignment_with_thesis
alignment_with_opening
version
checksum
```

La audiencia concreta debe derivarse del `EditorialProfile` aprobado. No puede utilizarse para redefinir silenciosamente la audiencia general del canal.

La autoridad funcional se divide así:

```text
YOUTUBE_ADAPTATION
→ define o aprueba audiencia concreta, promesa visible
  e hipótesis temprana de packaging.

SCRIPT_PRODUCT
→ valida que la tesis y la arquitectura puedan cumplir
  honestamente la promesa.

SCRIPT_PRODUCT no aprueba unilateralmente el packaging.
YOUTUBE_ADAPTATION no modifica unilateralmente la tesis.
```

### B1-C5 — ViewerJourney

```text
estado_inicial_del_espectador
creencia_inicial_probable
pregunta_que_lo_mantiene
primer_descubrimiento
complicacion
cambio_de_perspectiva
tension_principal
revelacion_o_payoff
estado_final_del_espectador
```

Cada bloque incluye:

```text
que_sabe_antes
que_sabe_despues
que_siente_o_cuestiona
por_que_quiere_continuar
promesa_parcial_resuelta
pregunta_abierta
```

### B1-C6 — OpeningDesign

```text
hook_function
opening_question
initial_tension
minimum_context
early_payoff
promise
first_transition
estimated_words
estimated_time
risks
```

### B1-C7 — ClosingDesign

```text
central_question_answer
thesis_payoff
opening_callback
final_image_or_idea
emotional_resolution
cta_strategy
new_ideas_prohibited
estimated_words
estimated_time
```

El CTA puede ser inexistente si perjudica el cierre.

### B1-C8 — NarrativePlan

```text
script_plan_id
episode_id
script_type
thesis_provisional
thesis_refined
main_objection
nuance
promise
packaging_hypothesis_ref
viewer_journey_ref
opening_design_ref
closing_design_ref
blocks
climax
word_budget_total
wpm_target
```

Cada bloque:

```text
block_id
function
central_question
new_information
emotional_or_intellectual_change
source_refs
word_budget
entry_transition
exit_transition
must_not_repeat
prepares_next
viewer_state_before
viewer_state_after
partial_payoff
open_question
```

### B1-C9 — ScriptBlockContract

```text
block_id
plan_version
context_pack_version
required_sources
forbidden_repetitions
required_transition
word_budget_min
word_budget_max
narrative_function
previous_block_summary
next_block_purpose
output_path
```

### B1-C10 — CorrectionRoutingPolicy

El reporte de defecto debe incluir:

```text
defect_type
severity
origin_artifact
invalidated_artifacts
return_state
required_revalidation
suggested_owner
```

Rutas canónicas:

```text
Problema de datos                 -> investigación
Problema de acceso o evidencia    -> evidencia
Problema de selección             -> curación
Problema de tesis                 -> tesis refinada
Problema de promesa               -> packaging hypothesis
Problema de recorrido             -> viewer journey
Problema de estructura            -> outline
Problema de continuidad           -> edición de desarrollo
Problema de frase u oralidad       -> edición de línea
Problema factual                  -> verificación
Problema de originalidad          -> transformación de fuentes
Problema de identidad             -> perfil o aplicación del perfil
```

### B1-C11 — ScriptVersionManifest

Incluye los campos definidos en la sección 11.3 y controla invalidación y checksum.

### B1-C12 — GateResult

```text
gate_id
artifact_id
artifact_version
status
summary
violations
warnings
evidence
checked_at
checker_version
exit_code
```

### B1-C13 — EditorialEditReport

```text
input_version
output_version
edit_type
changes_by_category
continuity_findings
redundancy_findings
line_findings
orality_findings
unresolved_issues
invalidated_artifacts
```

### B1-C14 — FinalEditorialAudit

```text
profile_compliance
brief_compliance
packaging_promise_compliance
evidence_sufficiency
thesis_quality
viewer_journey
opening_quality
progression
coherence
originality
source_transformation
voice
orality
closing_quality
factual_traceability
platform_risk
production_readiness
system_review
product_review
decision
correction_route
```

El auditor no modifica el guion auditado.

### B1-C15 — FinalDeliveryManifest

Debe identificar:

```text
final_script_clean
final_script_annotated
claims_ledger
metrics
known_limitations
final_candidate_version
human_approved_version
checksums
approval_record
```

### B1-C16 — EditorialLearningCandidate

```text
learning_id
observed_change
reason
scope
evidence_count
contexts
exceptions
confidence
status
approved_by
source_episode_versions
```

### B1-C17 — ResearchPack

```text
research_id
episode_id
brief_version
scope
facts
interpretations
hypotheses
contradictions
alternative_views
scene_evidence
source_registry
claims_candidates
unsupported_claims
narrative_opportunities
narrative_human_analysis_by_material
limitations
created_at
```

Cada entrada de `narrative_human_analysis_by_material` debe poder representar, cuando aplique:

```text
material_id
character_or_subject
desire
feared_loss
avoidance
self_and_world_beliefs
stated_vs_observed_contradiction
revealing_decision
decision_cost
change_and_persistence
environment_role
supporting_scene_or_behavior
alternative_reading
fact_interpretation_or_hypothesis
real_life_analogy_limits
unique_contribution
thesis_support_tension_or_contradiction
confidence
```

### B1-C18 — CurationDecision

```text
curation_id
research_version
narrative_human_analysis_ref
preselected_materials
selected_materials
rejected_materials
narrative_function_by_material
sequence_rationale
perspective_diversity
context_cost
redundancy_risk
climax_contribution
unique_contribution_by_material
thesis_support_tension_or_contradiction
spoiler_requirements
decision
```

### B1-C19 — ThesisArtifact

Debe admitir dos estados diferenciados:

```text
THESIS_PROVISIONAL
THESIS_REFINED
```

Campos mínimos:

```text
thesis_id
stage
statement
supporting_reasoning
main_objection
nuance
simplification_risk
open_questions
source_refs
packaging_alignment
viewer_transformation
version
```

### B1-C20 — ReadAloudReview

```text
input_version
method
reviewer_or_tool
pronunciation_issues
breathing_issues
syntax_issues
subject_clarity_issues
pause_issues
monotony_issues
density_issues
transition_issues
recommended_changes
status
```

### B1-C21 — ClaimsLedger y FactCheckReport

`ClaimsLedger` registra:

```text
claim_id
script_location
claim_text
claim_type
source_refs
evidence_excerpt
attribution_required
verification_status
confidence
limitations
```

`FactCheckReport` registra:

```text
input_version
verified_claims
corrected_claims
blocked_claims
interpretations_reclassified
unresolved_claims
required_disclosures
output_version
status
```

### B1-C22 — SourceTransformationAndOriginalityReview

```text
input_version
source_dependency_map
distinctive_phrases
idea_order_similarity
reused_examples
single_source_dependency
interpretation_attribution
structural_similarity
voice_imitation_risk
transformative_value
required_corrections
status
```

### B1-C23 — EditorialScriptApproval

```text
artifact_id
script_version
checksum
decision
approved_by
approved_role
approved_at
notes
invalidated_at
invalidation_reason
```

Este contrato registra la aprobación editorial humana de una versión exacta. Para cerrar el MVP, la decisión `APPROVED` de `EditorialScriptApproval` es la decisión editorial aplicable a `EDITORIAL_SCRIPT_APPROVED`; no debe sustituirse por `APPROVED_FOR_PRODUCTION`, que pertenece a `HumanProductionApproval` y al cierre posterior de B8.5. No es, por sí solo, un manifest que consolide las aprobaciones independientes de calidad editorial, identidad, factualidad/interpretación/fidelidad y adecuación textual a YouTube. El requisito funcional de que todas esas evidencias correspondan al mismo `artifact_id`, versión y checksum está definido en B7, pero el schema actual solo demuestra la aprobación individual y no la consolidación técnica completa: `IMPLEMENTATION_GAP` documental pendiente de implementación/demostración. Esta aprobación no autoriza producción ni publicación.

### B1-C24 — HumanProductionApproval

```text
publication_package_id
publication_package_version
script_version
packaging_version
platform_and_rights_review_version
checksum
decision
approved_by
approved_at
notes
invalidated_at
invalidation_reason
```

Decisiones permitidas:

```text
APPROVED_FOR_PRODUCTION
REQUEST_CHANGES
REJECT
```

Solo `APPROVED_FOR_PRODUCTION` permite declarar `YOUTUBE_PRODUCTION_READY`.

Esta aprobación no autoriza publicar.

### B1-C24A — HumanPublicationApproval

Contrato reservado para la futura revisión de la pieza audiovisual final:

```text
final_candidate_id
audiovisual_version
thumbnail_version
title_version
description_version
chapters_version
clips_and_music_manifest_version
synthetic_or_altered_content_review_version
final_rights_review_version
checksum
decision
approved_by
approved_at
notes
invalidated_at
invalidation_reason
```

Decisiones permitidas:

```text
APPROVED_FOR_PUBLICATION
REQUEST_CHANGES
REJECT
```

Solo `APPROVED_FOR_PUBLICATION` permite declarar `YOUTUBE_READY`.

Este contrato no puede aprobarse antes de existir y auditarse la pieza audiovisual final exacta.

### B1-C25 — PromiseCorrespondenceReport

```text
input_version
episode_audience
visible_promise
title
thumbnail_concept
opening_alignment
central_question_alignment
development_alignment
conclusion_alignment
promise_delivered
overpromise_risk
misleading_risk
required_corrections
status
```

### B1-C26 — YouTubePackagingDecision

```text
input_version
episode_audience
visible_promise
central_conflict
recommended_option
alternative_options
discarded_options
title_thumbnail_complementarity
script_evidence
clickbait_risk
platform_risk
visual_rights_risk
confidence
status
```

### B1-C27 — PlatformAndMonetizationRiskReport

Este contrato evalúa riesgo; no certifica monetización.

```text
input_version
policy_version
advertiser_friendly_risk
sensitive_topics
context_and_treatment
graphic_level
central_or_incidental
glorification_or_criticism
metadata_risk
repetitive_content_risk
reused_content_risk
synthetic_or_altered_content_review
required_corrections
limitations
status
```

Estados funcionales permitidos:

```text
LOW_IDENTIFIED_RISK
LOW_RISK_WITH_NOTES
LIMITED_ADS_RISK
HIGH_PLATFORM_RISK
BLOCKED
```

Estos estados son internos de este reporte y no sustituyen los estados canónicos del gate.

### B1-C28 — CopyrightAndReuseReport

```text
input_version
third_party_materials
source_or_license
editorial_function
expected_duration
original_audio_required
transformative_context
plot_reconstruction_risk
content_id_risk
reuse_policy_risk
alternative_without_asset
required_corrections
limitations
status
```

### B1-C29 — AudiovisualProductionRightsBrief

```text
input_version
block_id
suggested_visual_material
editorial_function
minimum_necessary_use
original_audio_policy
alternative_visual
graphics_or_original_assets
rights_notes
risk_level
status
```

### B1-C30 — SessionContinuityPlan

```text
input_version
recommended_next_video
alternative_video
playlist
continuity_reason
bridge_phrase
end_screen
pinned_comment
no_available_video_justification
future_content_opportunity
status
```

### B1-C31 — PublicationPackage

```text
package_id
package_version
script_version
approved_title
approved_thumbnail_or_brief
description
chapters_status
attributions
links
cta
end_screen
playlist
next_video
pinned_comment
shorts
promise_correspondence_report_version
platform_risk_report_version
copyright_and_reuse_report_version
audiovisual_rights_brief_version
known_limitations
publication_checklist
status
```

### B1-C32 — PublishedVersionManifest

```text
video_id
publication_date
script_version
audiovisual_version
title_version
thumbnail_version
description_version
end_screen_version
pinned_comment_version
playlist_version
publication_package_version
change_history
status
```

Cada entrada de `change_history` debe incluir:

```text
element
previous_version
new_version
changed_at
change_reason
observation_window_start
observation_window_end
```

Elementos mínimos trazables:

```text
title
thumbnail
description
end_screen
pinned_comment
playlist
```

### B1-C33 — PerformanceSnapshot

Puede alimentarse manualmente durante este plan.

```text
published_version
observation_window
active_title_version
active_thumbnail_version
active_description_version
active_end_screen_version
active_pinned_comment_version
active_playlist_version
mixed_version_window
attribution_status
impressions
ctr_with_context
initial_retention
average_view_duration
retention_by_block
traffic_sources
new_and_returning_viewers
end_screen_results
comment_signals
subscriber_signals
device_context
data_limitations
status
```

Si la ventana contiene más de una versión de un elemento, debe:

* dividirse;
* cerrarse en la fecha del cambio;
* o marcarse como `MIXED_VERSION_WINDOW`.

No puede atribuirse un resultado a un título, miniatura u otro elemento concreto cuando la ventana mezcla versiones sin declararlo.

### B1-C34 — YouTubeLearningReport

```text
published_version
packaging_findings
audience_findings
topic_findings
opening_findings
duration_findings
continuity_findings
confirmed_findings
inconclusive_findings
next_experiment
profile_change_candidate
status
```

Ningún hallazgo modifica automáticamente el `EditorialProfile`.

## 14.3 Implementación propuesta

```text
docs/contracts/
schemas/
src/core/status.py
src/core/gate_result.py
src/core/contract_validation.py
src/core/version_manifest.py
src/core/invalidation.py
```

## 14.4 Pruebas mínimas

- estado desconocido se rechaza;
- estados contradictorios se rechazan;
- falta de campo obligatorio produce `BLOCKED`;
- contrato inválido no avanza;
- exit code coincide con estado;
- cambio de artefacto aprobado invalida su aprobación;
- versión no puede sobrescribirse silenciosamente;
- auditoría final no puede señalarse como edición;
- ResearchPack distingue hecho, interpretación e hipótesis;
- ResearchPack contiene análisis narrativo y humano trazable por material;
- CurationDecision asigna función narrativa a cada material;
- CurationDecision referencia el análisis previo y diferencia preselección de selección final;
- ClaimsLedger rechaza claims sin estado y fuente;
- EditorialScriptApproval queda ligada a versión y checksum;
- HumanProductionApproval queda ligada al paquete de producción, versión y checksum;
- HumanPublicationApproval queda ligada a la pieza audiovisual final, activos definitivos, versión y checksum;
- HumanProductionApproval no puede declarar YOUTUBE_READY;
- HumanPublicationApproval no puede emitirse sin activos audiovisuales finales;
- PlatformAndMonetizationRiskReport no puede sustituir la auditoría editorial ni la auditoría de adaptación a YouTube;
- aprendizaje `CANDIDATE` no puede modificar el perfil activo.

## 14.5 Gate B1

```text
PASS si:
- todos los contratos están documentados y versionados;
- las responsabilidades funcionales pertinentes validan los campos editoriales;
- Desarrollo aprueba su implementabilidad;
- existe un módulo único de estados;
- versionado e invalidación tienen tests;
- ejemplos válidos e inválidos están cubiertos;
- no se han inventado requisitos editoriales fuera de autoridad.
```

---

# 15. Bloque B2 — Reparación del arnés y gates críticos

## 15.1 Objetivo

Eliminar falsos positivos y hacer que el pipeline se detenga cuando faltan entradas, evidencia, contenido, aprobación o coherencia de estado.

## 15.2 Misiones

### B2-M1 — Exit codes y parser canónico

**Archivos iniciales afectados:**

```text
src/scripts/gate0_auditoria.py
src/scripts/gate0_integridad.py
src/scripts/qa_brief_research.py
src/scripts/qa_momento_1.py
src/scripts/qa_duracion_guion.py
src/scripts/qa_lenguaje_youtube.py
src/scripts/qa_lenguaje_youtube_ultra.py
src/scripts/cerrar_episodio.py
```

**Cambios:**

- usar estados y códigos canónicos;
- eliminar decisiones por substring;
- parsear un único resultado estructurado;
- rechazar estados múltiples o ambiguos;
- distinguir `FAIL`, `BLOCKED` y `ERROR`.

### B2-M2 — Validación de entradas

Cada gate declara inputs obligatorios y valida:

- existencia;
- tipo;
- contenido no vacío;
- contrato;
- versión esperada;
- checksum cuando aplique;
- aprobación previa;
- estado del episodio.

### B2-M3 — Cierre fuerte del episodio

`cerrar_episodio.py` debe comprobar:

- entregables obligatorios no vacíos;
- gates finales en PASS o WARN permitido;
- versión humana aprobada exacta;
- ausencia de cambios posteriores;
- manifest completo;
- limitaciones declaradas;
- derivados requeridos, cuando correspondan;
- transición de estado válida.

### B2-M4 — Orden correcto del workflow

- separar gates por artefacto cuando sea necesario;
- no auditar packaging definitivo antes de generarlo;
- no realizar auditoría final antes de edición, fact-check y originalidad;
- no cerrar antes de aprobación humana final.

### B2-M5 — Evidence Sufficiency Gate

Implementar el gate que produce:

```text
PASS    -> evidencia suficiente
WARN    -> se puede continuar con límites explícitos
BLOCKED -> análisis responsable imposible
FAIL    -> evidencia contradice o incumple contrato
```

No puede existir PASS sin `SourceAccessAndEvidenceReport` válido.

### B2-M6 — Gate de aprobación e inmutabilidad

- aprobación humana referencia versión y checksum;
- cambio posterior invalida la aprobación;
- el cierre detecta mismatch;
- no se permiten artefactos huérfanos o versiones sin manifest.

## 15.3 Suite mínima

Debe cubrir:

- inputs ausentes;
- inputs vacíos;
- dos estados en el mismo reporte;
- estado desconocido;
- exit code incoherente;
- cierre con guion vacío;
- cierre con aprobación de otra versión;
- evidencia insuficiente;
- gate post-guion antes de inputs;
- ejecución desde otro CWD;
- compatibilidad de rutas.

## 15.4 Gate B2

```text
PASS si:
- todos los FAIL devuelven 1;
- todos los BLOCKED devuelven 2;
- no existen falsos PASS reproducibles;
- cierre inválido no puede completar episodio;
- evidencia insuficiente bloquea;
- aprobación de versión distinta se rechaza;
- suite de regresión pasa.
```

---

# 16. Bloque B3 — Perfil editorial y frontera del canal

## 16.1 Objetivo

Separar la inteligencia del canal del proceso de producción sin debilitar la identidad de Más Allá del Guion.

## 16.2 Misiones

### B3-M1 — Matriz canónica de componentes

Clasificar cada archivo como:

```text
CHANNEL_SOURCE
EDITORIAL_PROFILE_SOURCE
SCRIPT_ENGINE
HARNESS
DERIVATIVE
HISTORICAL
TEMPLATE
CONFIGURATION
```

La matriz debe identificar:

- autoridad;
- consumidor;
- estado;
- duplicaciones;
- migración necesaria.

### B3-M2 — EditorialProfile extensible

El perfil debe diferenciar explícitamente:

- núcleo estable de identidad;
- decisiones editoriales modificables;
- territorios activos;
- territorios experimentales;
- territorios excluidos;
- territorios pendientes;
- promesa principal;
- audiencia prioritaria;
- personalidad y persona autoral;
- voz y tono;
- uso permitido de primera persona;
- límites de humanización;
- decisiones pendientes;
- referencias a políticas externas versionadas.

La lista de territorios no debe quedar cerrada de forma rígida. Debe ser posible incorporar en el futuro, mediante nueva versión aprobada, territorios como economía, tecnología, historia, instituciones, cultura, actualidad u otros compatibles con la identidad. No activar automáticamente ningún territorio nuevo sin aprobación funcional.

### B3-M2A — Compilador de EditorialProfile

Crear un proceso reproducible que:

- lea fuentes aprobadas del canal;
- valide contradicciones;
- genere versión;
- registre lineage y hashes;
- produzca checksum;
- solicite y registre la aprobación funcional de `CHANNEL_INTELLIGENCE`;
- solicite y registre la validación técnica de `TECHNICAL_GOVERNANCE`;
- no active automáticamente cambios no aprobados.

La aprobación debe quedar separada:

```text
CHANNEL_INTELLIGENCE_PROFILE_APPROVAL
→ valida identidad, posicionamiento, audiencia, promesa, territorios,
  personalidad, voz, principios conceptuales y contenido funcional.

TECHNICAL_PROFILE_VALIDATION
→ valida contrato, compilación, lineage, versión, checksum,
  configuración e invalidación.
```

La validación técnica de `TECHNICAL_GOVERNANCE` no autoriza el contenido funcional. La aprobación de `CHANNEL_INTELLIGENCE` no sustituye la validación técnica.

### B3-M3 — Perfil activo y selección por configuración

La ejecución debe identificar explícitamente:

```text
ACTIVE_PROFILE_ID
ACTIVE_PROFILE_VERSION
```

No se aceptan lecturas implícitas de “lo último” sin aprobación.

### B3-M4 — Adapter de compatibilidad

Durante la migración, un adapter puede traducir documentos actuales al contrato nuevo sin mover todo de una vez.

### B3-M5 — Prohibición de lectura directa dispersa

Skills de brief, outline, guion y QA deben consumir el perfil, no cinco o seis documentos internos de forma independiente.

Excepciones autorizadas:

- compilación del perfil;
- mantenimiento del perfil;
- auditoría de lineage;
- migración controlada.

### B3-M6 — Política de cambio e invalidación del perfil

Un cambio de perfil se clasifica como:

```text
NO_IMPACT
PARTIAL_INVALIDATION
FULL_INVALIDATION
```

Debe indicar qué episodios o artefactos requieren revisión.

### B3-M7 — Aprendizajes de voz como candidatos

- no escribir directamente en el perfil;
- registrar candidatos;
- acumular evidencia;
- aprobar o rechazar;
- crear nueva versión solo con aprobación funcional de `CHANNEL_INTELLIGENCE` y validación técnica de `TECHNICAL_GOVERNANCE`.

### B3-M8 — Corpus y voz inicial

El alcance mínimo de B3 debe incluir:

- registro de muestras reales del usuario;
- origen de la muestra;
- tipo de texto;
- autorización de uso;
- versión;
- lineage;
- extracción de patrones como candidatos;
- nivel de confianza;
- ejemplos y contraejemplos;
- aprobación humana antes de incorporarlos al VoiceProfile.

Los textos actuales son un punto de partida, no una definición definitiva de voz. Una corrección aislada no se convierte automáticamente en regla. El perfil de voz debe poder mejorar con nuevas muestras y correcciones. No se entrenará un modelo propio en B3.

## 16.3 Gate B3

```text
PASS si:
- existe EditorialProfile versionado;
- CHANNEL_INTELLIGENCE_PROFILE_APPROVAL = PASS;
- TECHNICAL_PROFILE_VALIDATION = PASS;
- la aprobación funcional y la validación técnica corresponden a la misma versión y checksum;
- el lineage está completo;
- el motor no depende de lecturas dispersas del workspace;
- el cambio de perfil invalida correctamente;
- los aprendizajes candidatos no contaminan el perfil;
- las dimensiones estables, editoriales, de formato, transversales y pendientes están diferenciadas;
- un episodio puede identificar exactamente qué perfil usó.
```

---

# 17. Bloque B4 — Responsabilidades, skills, prompts y portabilidad

## 17.1 Objetivo

Alinear los once roles actuales con seis responsabilidades funcionales claras, sin crear subagentes innecesarios y sin acoplar el sistema a una herramienta externa.

## 17.2 Misiones

### B4-M1 — Contratos oficiales de responsabilidad

Definir para cada responsabilidad:

```text
role_id
purpose
when_used
inputs
outputs
read_permissions
write_permissions
forbidden_actions
veto_conditions
evidence
handoff
prompt_version
```

### B4-M2 — Separar Editor y Auditor

Crear dos contratos distintos:

- `EDITOR`: modifica y produce `EditorialEditReport`.
- `FINAL_EDITORIAL_AUDITOR`: no modifica el guion y produce `FinalEditorialAudit`.

La auditoría final debe ejecutarse en contexto limpio o sesión separada.

### B4-M3 — Catálogo de skills por responsabilidad

#### Investigación y curación

- investigar por cobertura;
- clasificar fuentes;
- evaluar acceso;
- producir evidence report;
- curar por función narrativa.

#### Arquitectura narrativa

- clasificar tipo de guion;
- tesis provisional/refinada;
- packaging hypothesis;
- viewer journey;
- opening/closing design;
- outline y presupuesto.

#### Escritura

- redactar bloques;
- mantener memoria global;
- aplicar correcciones enrutadas.

#### Edición

- edición de desarrollo;
- edición de línea;
- oralidad;
- read-aloud review.

#### Auditoría

- contrato y perfil;
- evidencia;
- coherencia;
- originalidad;
- calidad final;
- ruta de corrección.

#### Adaptación a YouTube

- packaging final;
- Shorts;
- metadatos y paquete de publicación.

### B4-M4 — Prompts oficiales

Cada responsabilidad estable debe contar con prompt oficial versionado. No se permiten prompts improvisados en el workflow activo.

### B4-M5 — Proyección a un entorno de agente externo

Los archivos `.agent/` actúan como adapter operativo, no como única sede de la arquitectura.

### B4-M6 — Configuración agnóstica

Separar:

```text
role
provider
model
tools
permissions
```

El cambio de proveedor debe ocurrir por configuración.

### B4-M8 — Puntos de extensión

La arquitectura debe poder incorporar, sin modificar el core:

- nuevo proveedor de IA;
- nuevo modelo;
- nuevo canal de entrada;
- nueva skill;
- nueva auditoría;
- nueva política de plataforma;
- nuevo formato;
- nuevo territorio editorial;
- nuevo mecanismo de verificación.

Definir conceptualmente interfaces o adapters, sin diseñar todavía implementación concreta. Ejemplos válidos:

```text
AIProvider o equivalente
InputAdapter o equivalente
ReviewModule o equivalente
PolicyPack o equivalente
```

No imponer nombres técnicos definitivos si el bloque aún no los ha decidido.

Los agentes operativos externos son herramientas de desarrollo opcionales, no dependencias obligatorias del producto. Los proveedores deben seleccionarse por configuración. Telegram, voz, web o API serán futuras entradas que normalicen hacia un contrato canónico. No implementar esos adaptadores en B4 si están fuera del MVP.

### B4-M7 — Política de subagentes

Mantener `0` subagentes reales hasta que exista evidencia de necesidad.

## 17.3 Gate B4

```text
PASS si:
- todas las responsabilidades operativas y familias funcionales canónicas tienen contrato;
- cada capacidad tiene dueño funcional identificado;
- `CHANNEL_INTELLIGENCE` está representada y conserva la aprobación funcional de su dominio;
- `YOUTUBE_ADAPTATION` está representada y conserva la autoridad funcional de su dominio;
- Editor y Auditor están separados;
- cada skill tiene dueño funcional;
- prompts oficiales están versionados;
- el sistema funciona en modo single-agent;
- la arquitectura no depende de una marca de IDE o modelo;
- no se crearon subagentes sin justificación.
```

---

# 18. Bloque B5 — Profesionalización del diseño editorial

## 18.1 Objetivo

Convertir brief, investigación, evidencia, tesis, curación, promesa editorial, hipótesis temprana de packaging, recorrido y outline en un diseño profesional antes de redactar. La hipótesis temprana no equivale a packaging final.

## 18.2 Misiones

### B5-M1 — Brief unificado y tipo de guion

Unificar skill, template y QA.

Debe decidir:

- pregunta central;
- conflicto;
- transformación;
- ángulo;
- alcance;
- tipo principal y secundario;
- estructura candidata;
- duración;
- política de citas y fuentes.

La estructura se elige por adecuación, no por costumbre.

### B5-M2 — Investigación por cobertura

La investigación debe distinguir:

```text
hechos
interpretaciones
hipótesis
contradicciones
límites
escenas o evidencia concreta
perspectivas alternativas
claims utilizables
claims no sostenibles
oportunidades narrativas
```

No se mide calidad por número bruto de URLs.

### B5-M3 — Acceso y suficiencia de evidencia

Producir `SourceAccessAndEvidenceReport` y ejecutar el gate.

Debe impedir:

- fingir haber visto una obra;
- atribuir escenas no verificadas;
- confundir adaptación y obra original;
- presentar interpretación como hecho;
- escribir análisis fuerte con material insuficiente.

### B5-M4 — Tesis provisional

Debe existir antes de curar y puede cambiar con la investigación.

Incluye:

- hipótesis inicial;
- objeción prevista;
- riesgo de simplificación;
- preguntas abiertas.

### B5-M5 — Análisis narrativo y humano y curación final por función

Después de la tesis provisional se realiza una preselección de materiales.

Antes de cerrar la selección definitiva, cada material preseleccionado debe analizarse narrativamente y humanamente con evidencia suficiente.

El análisis debe responder, cuando aplique:

- qué desea el personaje o sujeto;
- qué teme perder;
- qué evita;
- qué cree sobre sí mismo y sobre el mundo;
- qué contradicción existe entre lo que declara y lo que hace;
- qué decisión revela el patrón central;
- qué coste produce esa decisión;
- qué cambia y qué permanece;
- qué papel desempeña el entorno;
- qué escena o comportamiento sostiene la lectura;
- qué lectura alternativa existe;
- qué parte es hecho narrativo, interpretación o hipótesis;
- qué límites tiene la analogía con la vida real;
- qué aporta el material que no aporta otro;
- cómo sostiene, tensiona, matiza o contradice la tesis.

Después del análisis, la curación final debe justificar por cada material:

- función;
- perspectiva;
- orden;
- novedad;
- evidencia;
- coste de contexto;
- riesgo de repetición;
- contribución única;
- relación con la tesis;
- aporte al clímax.

La fórmula habitual del canal se mantiene como preferencia fuerte, no obligación universal.

No se aprueba una selección basada únicamente en afinidad temática.

### B5-M6 — Audiencia concreta e hipótesis temprana de promesa y packaging

Antes del outline debe existir una audiencia concreta del episodio derivada del `EditorialProfile` aprobado.

Debe definir:

- qué persona concreta se busca alcanzar;
- qué conocimiento previo se presupone;
- qué tensión reconoce;
- por qué la obra o pregunta le importa;
- qué expectativa no debe generarse;
- qué versión de perfil y brief la sustentan.

La hipótesis temprana debe incluir:

- promesa de clic;
- título de trabajo;
- concepto de miniatura;
- expectativa del espectador;
- diferenciador;
- riesgo de sobrepromesa.

La autoridad funcional se distribuye así:

```text
YOUTUBE_ADAPTATION
→ define o aprueba la audiencia concreta,
  la promesa visible y la hipótesis de packaging.

SCRIPT_PRODUCT
→ valida que la tesis, la evidencia y la arquitectura
  puedan cumplir honestamente esa promesa.
```

`SCRIPT_PRODUCT` no puede aprobar unilateralmente el packaging. `YOUTUBE_ADAPTATION` no puede modificar unilateralmente la tesis.

Un cambio sustancial en audiencia concreta, promesa visible, tesis o conflicto central invalida los artefactos dependientes.

### B5-M7 — Tesis refinada

Después de evidencia, análisis narrativo y humano, curación final y la hipótesis temprana de promesa y packaging:

- tesis defendible;
- matiz;
- objeción principal;
- idea que no debe simplificarse;
- transformación final;
- relación con promesa.

### B5-M8 — Recorrido del espectador

Planificar el cambio de conocimiento, emoción y pregunta en cada bloque.

No se usa para fabricar retención artificial, sino para comprobar avance real.

### B5-M9 — OPENING_UNIT y diseño de apertura

La apertura se trata como unidad prioritaria con diseño propio. OpeningDesign actúa como antecedente o parte de OPENING_UNIT con funciones obligatorias, no duración rígida.

Debe cumplir:

- confirmación del clic;
- tensión;
- sustancia temprana;
- contexto mínimo;
- promesa del recorrido;
- transición al primer bloque;
- contribución autoral.

Además debe revisar:

- punto de máximo interés;
- pregunta central;
- contexto mínimo;
- promesa concreta;
- sustancia en el primer minuto;
- ausencia de introducción larga;
- suspensión no artificial;
- primera transición.

No exigir siempre exactamente 90 segundos. La estructura narrativa puede variar; el diseño debe compararse contra patrones repetidos para evitar aperturas mecánicas.

### B5-M10 — Diseño de cierre

Debe:

- responder la pregunta central;
- demostrar la tesis;
- transformar o recuperar la apertura;
- no introducir tesis nueva;
- evitar moraleja genérica;
- cerrar con idea o imagen memorable;
- integrar CTA solo si mejora el cierre.

### B5-M11 — Arquitectura y presupuesto

Por cada bloque:

```text
pregunta que abre
información nueva
cambio del espectador
función narrativa
tensión
promesa parcial
pregunta abierta
transición
presupuesto
fuentes
no repetir
```

### B5-M12 — Auditoría de outline

Debe comprobar:

- progresión;
- causalidad;
- contraste;
- acumulación;
- ritmo;
- clímax;
- cierre;
- cumplimiento de promesa;
- coherencia con tipo de guion;
- fidelidad al canal.

## 18.3 Gate B5

```text
PASS si:
- brief y tipo de guion están aprobados;
- evidencia permite continuar;
- tesis provisional y refinada son trazables;
- existe análisis narrativo y humano suficiente por cada material seleccionado;
- hechos narrativos, interpretaciones e hipótesis están diferenciados;
- los límites de las analogías con la vida real están declarados;
- curación asigna funciones y contribuciones distintas;
- PackagingHypothesis tiene aprobación funcional de `YOUTUBE_ADAPTATION`;
- Producto Guion confirmó que la tesis y la arquitectura pueden cumplir la promesa;
- PackagingHypothesis no sobrepromete;
- ViewerJourney muestra transformación;
- apertura y cierre tienen contrato;
- outline y presupuesto están aprobados;
- Producto considera que el diseño puede producir un buen guion.
```

---

# 19. Bloque B5.5 — Prototipo editorial controlado

## 19.1 Objetivo

Obtener evidencia editorial temprana antes de implementar o ejecutar la redacción completa del episodio.

## 19.2 Alcance

El prototipo debe producir:

- brief;
- investigación parcial suficiente;
- evidence report;
- tesis provisional;
- curación;
- packaging hypothesis;
- tesis refinada;
- viewer journey;
- outline;
- apertura;
- uno o dos bloques representativos.

No necesita completar el episodio.

## 19.3 Evaluación

Comparar contra benchmarks en:

- tesis;
- progresión;
- originalidad;
- naturalidad;
- voz;
- promesa;
- calidad de apertura;
- utilidad de curación;
- ausencia de plantilla mecánica.

## 19.4 Criterio de decisión

```text
PASS:
la dirección editorial mejora de forma observable y B6 puede comenzar.

WARN:
la dirección es prometedora, pero requiere ajustes concretos en B5.

FAIL:
el nuevo diseño no mejora o empeora el producto.

BLOCKED:
no existe evidencia o benchmark suficiente para evaluar.
```

Si B5.5 no obtiene PASS, se regresa a la misión de B5 que originó el defecto. No se avanza a redacción completa.

---

# 20. Bloque B6 — Redacción, ensamblaje, edición y verificación

## 20.1 Objetivo

Producir un candidato final coherente mediante redacción fraccionada con memoria global, ensamblaje reproducible, edición profesional y controles de evidencia y originalidad.

## 20.2 Misiones

### B6-M1 — Presupuesto de duración y palabras

Debe considerar:

- duración objetivo;
- ritmo configurable;
- pausas;
- complejidad;
- apertura y cierre;
- notas no narradas;
- tolerancia permitida.

El reparto no será uniforme por defecto.

### B6-M2 — Context pack global

Cada bloque recibe:

- perfil y versión;
- brief;
- tesis;
- packaging hypothesis;
- viewer journey;
- outline;
- opening/closing design;
- presupuesto;
- fuentes autorizadas;
- referencia al análisis narrativo y humano de los materiales;
- claims;
- bloques previos resumidos;
- repeticiones prohibidas;
- función del bloque siguiente.

### B6-M3 — Redacción por bloques con edición separada

La redacción de apertura se realiza separadamente y se revalida después del ensamblaje. Cada bloque recibe contexto global. El editor está separado del redactor.

Antes de redactar el bloque de apertura debe ejecutarse un preflight contra `OpeningDesign`. Una apertura que contradiga la promesa, retrase el interés o carezca de sustancia temprana no puede continuar al ensamblaje.

Cada bloque debe:

- cumplir su función;
- aportar información nueva;
- respetar presupuesto;
- usar solo evidencia autorizada;
- utilizar el análisis narrativo y humano aprobado;
- preparar el siguiente;
- mantener voz y oralidad;
- no incluir marcadores técnicos visibles en la entrega final.

La redacción debe convertir el diseño en narración y argumentación orgánicas mediante, cuando el material lo justifique:

- escenas concretas;
- acciones reveladoras;
- detalles significativos;
- contradicción;
- subtexto;
- causalidad;
- revelación progresiva;
- variación de ritmo;
- alternancia natural entre relato, análisis y reflexión;
- transiciones orgánicas;
- síntesis sin simplificación;
- emoción sin dramatismo prefabricado;
- reflexión sin falsa profundidad.

No se permite que todos los bloques repitan mecánicamente una secuencia fija como:

```text
escena
→ explicación
→ pregunta
→ ejemplo
→ reflexión
```

La cantidad de contexto narrativo debe ser suficiente para comprender el argumento sin convertir el guion en un resumen extenso de la obra.

Tras el ensamblaje debe ejecutarse:

- revalidación de apertura;
- revisión de oralidad;
- alineación con VoiceProfile;
- reducción de señales de escritura artificial;
- prohibición de inventar experiencias personales.

Se permiten múltiples iteraciones limitadas.

Señales de artificialidad a revisar:

- frases intercambiables;
- solemnidad artificial;
- falsa profundidad;
- preguntas retóricas automáticas;
- transiciones formularias;
- simetría excesiva;
- ritmo uniforme;
- conclusión predecible;
- metáforas decorativas;
- entusiasmo no ganado.

No prometer detección infalible de texto de IA.

### B6-M4 — Ensamblaje determinista

El ensamblaje debe:

- usar orden del manifest;
- verificar versiones y hashes;
- detectar bloques ausentes o duplicados;
- separar texto narrado de notas;
- generar candidato reproducible;
- producir manifest de ensamblaje.

### B6-M5 — Edición de desarrollo

Debe detectar y corregir:

- repetición conceptual;
- bloque sin función;
- secuencia débil;
- obra redundante;
- causalidad rota;
- promesa incumplida;
- clímax prematuro;
- cierre no preparado;
- desequilibrio de duración;
- pérdida de tesis.

Produce `EditorialEditReport` y nueva versión.

### B6-M6 — Edición de línea y oralidad

Debe revisar:

- claridad;
- concreción;
- musicalidad;
- longitud de frases;
- respiración;
- muletillas;
- lenguaje inflado;
- transiciones;
- tono;
- facilidad de locución.

### B6-M7 — Read-Aloud Review

Debe identificar:

- frases difíciles de pronunciar;
- subordinadas acumuladas;
- sujetos confusos;
- términos que requieren pronunciación;
- pausas antinaturales;
- párrafos sin respiración;
- monotonía;
- densidad excesiva;
- transiciones que fallan al escucharse.

Puede ejecutarse mediante lectura humana, TTS de prueba o revisión especializada. La evidencia debe declarar el método.

### B6-M8 — Verificación factual e interpretativa

Debe controlar:

- hechos;
- nombres y fechas;
- citas y paráfrasis;
- escenas;
- intención atribuida;
- causalidad psicológica;
- diagnósticos implícitos;
- diferencias entre hecho, lectura e hipótesis;
- claims sin respaldo;
- citas textuales fuera de política;
- atribuciones que deberían aparecer en narración;
- ideas de terceros presentadas como propias;
- referencias innecesariamente académicas que dañen la oralidad.

La verificación debe aplicar `citation_style`, `attribution_policy`, `quotation_policy` y `source_visibility` sin convertir el guion en un artículo académico.

### B6-M9 — Originalidad y transformación de fuentes

Producir `SourceTransformationAndOriginalityReview` con:

- frases distintivas;
- orden de ideas;
- ejemplos reutilizados;
- dependencia de una fuente;
- atribución de interpretaciones;
- similitud estructural;
- imitación de voz;
- legitimidad transformativa.

El objetivo no es evadir detectores. Es proteger autoría editorial legítima.

### B6-M10 — Candidato final y entregables

Generar, como mínimo:

```text
final_script_clean.md
final_script_annotated.md
claims_ledger.json
metrics.json
known_limitations.md
final_delivery_manifest.json
system_review.json
product_review.json
owner_report.md
```

`final_script_clean.md` no contiene:

- gates;
- etiquetas del outline;
- instrucciones de agentes;
- metadatos;
- marcadores de retención visibles;
- comentarios técnicos.

## 20.3 Gate B6

```text
PASS si:
- todos los bloques cumplen contrato;
- ensamblaje es reproducible;
- edición de desarrollo y línea tienen reportes separados;
- read-aloud review se ejecutó;
- claims están trazados;
- originalidad fue revisada;
- candidato final y entregables están completos;
- no existe aprobación humana todavía sobre una versión anterior.
```

---

# 21. Bloque B7 — Auditoría independiente, correcciones y aprobación editorial

## 21.1 Objetivo

Cerrar de forma integrada el candidato final del guion sin mezclar producción y auditoría: ejecutar las validaciones obligatorias independientes, enrutar correctamente los defectos, revalidar las versiones corregidas y obtener la aprobación editorial humana de una versión exacta. La adecuación textual a YouTube participa en este cierre; packaging final y producción permanecen fuera del MVP.

## 21.2 Misiones

### B7-M1 — Validaciones obligatorias separadas

El candidato final debe recibir, como mínimo, estas validaciones independientes, sin convertirlas en cuatro agentes ni en cuatro estados runtime:

- `SCRIPT_PRODUCT`: calidad editorial, estructura, progresión, tesis, escritura, edición, oralidad y cumplimiento del brief;
- `CHANNEL_INTELLIGENCE`: coherencia con el `EditorialProfile`, propósito, posicionamiento, audiencia, promesa, voz, persona autoral y ausencia de deriva material;
- responsabilidades existentes de investigación/evidencia y auditoría editorial: claims, soporte, interpretación, fidelidad, sobreinterpretación y contradicciones materiales;
- `YOUTUBE_ADAPTATION`: adecuación textual del guion a audiencia, promesa, apertura, duración orientativa, sobrepromesa y riesgos de plataforma, copyright o reutilización originados en el texto.

El redactor no debe autoaprobarse como único auditor. Las auditorías avanzadas adicionales son opcionales y no crean requisitos nuevos del MVP.

### B7-M1A — Auditoría final independiente

El auditor:

- recibe la versión editada;
- trabaja en contexto limpio;
- no modifica el guion;
- emite únicamente su propia auditoría editorial dentro de su autoridad; las demás autoridades funcionales emiten sus propias validaciones, y el gate de cierre reúne esas evidencias separadas, todas sobre la misma versión y checksum, antes de `EDITORIAL_SCRIPT_APPROVED`;
- emite `PASS`, `WARN`, `FAIL` o `BLOCKED`;
- identifica ruta de corrección.

Una validación no aprobada no se oculta con otra aprobación: produce hallazgo, ruta de corrección y revalidación.

### B7-M2 — Enrutamiento de correcciones

Aplicar `CorrectionRoutingPolicy`.

El auditor detecta y enruta; la responsabilidad productora corrige. No se parchea silenciosamente el texto final cuando el defecto pertenece a investigación, evidencia, tesis, promesa, recorrido o arquitectura.

### B7-M3 — Invalidación y revalidación

Registrar:

- artefactos invalidados;
- nueva versión;
- gates que deben repetirse;
- estado de retorno;
- evidencia de corrección.

Una corrección que cambie el candidato invalida las aprobaciones de la versión anterior para el cierre. Todas las validaciones obligatorias deben repetirse sobre la versión exacta nueva.

### B7-M4 — Control de ciclos

Máximo general:

```text
3 ciclos editoriales completos
```

Después:

```text
BLOCKED_FOR_HUMAN_DECISION
```

Una corrección menor de línea no se cuenta igual que un retorno completo a tesis. La política debe definir el tipo de ciclo.

### B7-M5 — Aprobación editorial del guion

Debe registrar:

```text
artifact_id
version
checksum
decision
approved_by
approved_role
approved_at
notes
```

Esta decisión se registra mediante `EditorialScriptApproval`. Para cerrar el MVP, la decisión `APPROVED` de este contrato es la decisión editorial aplicable a `EDITORIAL_SCRIPT_APPROVED`; no debe sustituirse por `APPROVED_FOR_PRODUCTION`, que pertenece a `HumanProductionApproval` y al cierre posterior de B8.5. Es la aprobación editorial humana de una versión exacta; no equivale a aprobación de producción, publicación, `YOUTUBE_PRODUCTION_READY` ni `YOUTUBE_READY`. El requisito de consolidar todas las evidencias obligatorias sobre esa versión está definido funcionalmente, pero su implementación debe comprobarse contra B1 y el código.

Decisiones:

```text
APPROVED
REQUEST_CHANGES
REJECT
```

Solo `APPROVED`, con todas las validaciones obligatorias vigentes sobre el mismo checksum, permite pasar a etapas posteriores. No permite todavía declarar `YOUTUBE_PRODUCTION_READY` ni `YOUTUBE_READY`.

## 21.3 Gate B7

```text
PASS si:
- las validaciones obligatorias fueron independientes y están aprobadas sobre el mismo `artifact_id`, versión y checksum;
- defectos se enrutaron a la fase correcta;
- las correcciones generaron invalidación y revalidación de la versión actual;
- no se superó el máximo de ciclos sin decisión humana;
- EditorialScriptApproval referencia versión y checksum;
- no existen cambios posteriores sin invalidación;
- el guion queda cerrado editorialmente en `EDITORIAL_SCRIPT_APPROVED` y puede continuar a etapas posteriores autorizadas.
```
El gate consume evidencias separadas de cada dominio obligatorio y las reúne solo para el cierre de una versión exacta. Sus etiquetas documentales no crean estados, enums ni contratos nuevos del runtime.

---

# 22. Bloque B7.5 — Adaptación profesional a YouTube

## 22.1 Objetivo

Gestionar, después de `EDITORIAL_SCRIPT_APPROVED`, packaging final, correspondencia, continuidad y preparación posterior para YouTube sin alterar la tesis ni la identidad del canal. B7.5 no es el primer lugar donde se determina la adecuación textual necesaria para cerrar el MVP: esa validación participa en B7.

## 22.2 Misiones

### B7.5-M1 — Correspondencia de packaging posterior

Generar `PromiseCorrespondenceReport`.

Auditar:

```text
Título
↕
Miniatura
↕
Apertura
↕
Pregunta central
↕
Desarrollo
↕
Conclusión
```

Un incumplimiento grave devuelve el episodio a la fase correspondiente.

Esta misión trata la correspondencia entre packaging final y guion aprobado. Si un cambio de packaging revela un problema textual del guion, se solicita revalidación o corrección mediante la ruta de B7; no se sustituye la validación textual inicial del cierre.

### B7.5-M2 — Decisión final de packaging

Rediseñar funcionalmente `skill_packaging.md` para que produzca `YouTubePackagingDecision`.

Debe incluir:

* opción recomendada;
* alternativas;
* opciones descartadas;
* complementariedad título-miniatura;
* evidencia de cumplimiento en el guion;
* riesgo de clickbait;
* riesgo visual y de derechos.

No se implementa todavía la miniatura física.

### B7.5-M3 — Políticas de YouTube versionadas

Apertura, packaging, riesgo publicitario, copyright, contenido sintético, duración, Shorts, metadatos y continuidad pueden estar gobernados por políticas versionadas. Los cambios de YouTube no deben requerir reconstruir el motor editorial. Una OpeningPolicy futura podrá evolucionar independientemente del EditorialProfile. Packaging, apertura y guion deben mantener correspondencia. `YOUTUBE_ADAPTATION` conserva autoridad funcional sobre estas políticas.

No incorporar como verdad permanente afirmaciones no verificadas sobre el algoritmo.

### B7.5-M3A — Revalidación posterior de apertura y duración

Validar:

* confirmación temprana de la promesa;
* ausencia de preámbulo innecesario;
* relevancia para la audiencia concreta;
* densidad inicial;
* duración justificada por el valor y el tipo de pieza.

No imponer una duración universal.

La validación textual inicial de apertura y duración orientativa que puede afectar al cierre del MVP se realiza en B7. Aquí solo se revalida cuando una decisión posterior de YouTube lo exige o cuando cambia el paquete posterior.

### B7.5-M4 — Continuidad de sesión

Generar `SessionContinuityPlan`.

La CTA no es obligatoria si perjudica el cierre. Cuando exista, debe dirigir a un contenido real y coherente.

### B7.5-M5 — Shorts y derivados por función

Rediseñar la capacidad de Shorts para clasificarlos como:

```text
DISCOVERY
BRIDGE_TO_LONGFORM
STANDALONE_IDEA
COMMUNITY_RESPONSE
EMOTIONAL_MOMENT
CURRENT_OPPORTUNITY
CATALOG_RECOVERY
```

Cada derivado debe:

* funcionar con su propio contexto;
* no tergiversar el longform;
* no convertir un tema sensible en shock;
* registrar su relación con el video principal.

### B7.5-M6 — Metadatos y paquete preliminar

Sustituir conceptualmente `SEO YouTube` por:

```text
Metadatos y paquete de publicación
```

Debe preparar:

* título público;
* descripción fiel;
* nombres oficiales de obras;
* entidades;
* atribuciones;
* enlaces;
* comentario fijado;
* playlist;
* video siguiente;
* capítulos provisionales.

Los timestamps finales quedan `BLOCKED` hasta existir edición audiovisual real.

## 22.3 Gate B7.5

```text
PASS si:
- `EDITORIAL_SCRIPT_APPROVED` ya existe y no se usa B7.5 para aprobar por primera vez la adecuación textual del MVP;
- existe correspondencia verificable entre promesa y contenido;
- packaging recomendado no es engañoso;
- apertura confirma la expectativa;
- duración está justificada;
- continuidad está definida o su ausencia justificada;
- derivados tienen función explícita;
- metadatos son correctos;
- ningún cambio altera el guion aprobado sin invalidarlo.
```

Este gate es posterior al cierre del MVP y no convierte packaging, títulos, miniaturas, Shorts, SEO, metadatos o producción audiovisual en requisitos de `EDITORIAL_SCRIPT_APPROVED`.

---

# 23. Bloque B8 — Plataforma, monetización, copyright y paquete para producción

## 23.1 Objetivo

Evaluar separadamente los riesgos de plataforma, monetización, copyright, Content ID, contenido reutilizado y producción audiovisual antes de compilar el paquete exacto que podrá someterse a aprobación para producción.

## 23.2 Misiones

### B8-M1 — Consolidar QA de lenguaje

- conservar una única herramienta de detección auxiliar;
- retirar `qa_lenguaje_youtube_ultra.py` como gate autoritativo;
- eliminar sustituciones automáticas que degraden precisión;
- separar palabra detectada de riesgo contextual;
- hacer que inputs obligatorios ausentes produzcan `BLOCKED`.

La herramienta auxiliar no decide monetización.

### B8-M2 — Gate contextual de plataforma y monetización

Generar `PlatformAndMonetizationRiskReport`.

Evaluar:

- lenguaje;
- violencia;
- sexualidad;
- drogas;
- armas;
- actos peligrosos;
- temas sensibles;
- menores;
- tragedias;
- contenido degradante o impactante;
- contexto educativo, documental, analítico o artístico;
- nivel gráfico;
- foco central o incidental;
- glorificación o crítica;
- metadatos;
- contenido repetitivo;
- contenido reutilizado;
- contenido sintético o alterado.

Eliminar cualquier promesa de “100 % monetizable”.

### B8-M3 — Copyright, Content ID y reutilización

Generar `CopyrightAndReuseReport`.

Distinguir:

```text
copyright
Content ID
contenido reutilizado
transformación editorial
dependencia de material de terceros
```

### B8-M4 — Brief de producción audiovisual y derechos

Generar `AudiovisualProductionRightsBrief` por bloque.

Debe indicar:

* material sugerido;
* función editorial;
* uso mínimo necesario;
* política de audio original;
* alternativa sin clip;
* gráficos o recursos propios;
* riesgos.

No debe prescribir que una duración concreta de clip sea legal o segura.

### B8-M5 — Compilar paquete previo a producción

Generar `PublicationPackage`.

Debe referenciar versiones exactas de:

* guion;
* packaging;
* correspondencia de promesa;
* metadatos;
* continuidad;
* Shorts;
* riesgo de plataforma;
* copyright y reutilización;
* brief audiovisual;
* limitaciones.

Dentro del Plan 001, `PublicationPackage` representa un paquete planificado y versionado previo a producción. Su nombre contractual no implica que la pieza audiovisual final esté lista para publicarse.

## 23.3 Gate B8

```text
PASS si:
- riesgos de plataforma y monetización fueron evaluados contextualmente;
- no se prometió monetización;
- copyright, Content ID y reutilización están diferenciados;
- existe alternativa para materiales de riesgo alto;
- paquete previo a producción está completo y versionado;
- ninguna entrada obligatoria fue omitida silenciosamente.
```

El PASS de B8 no permite declarar `YOUTUBE_READY`. Solo permite solicitar `HumanProductionApproval` en B8.5.

---

# 24. Bloque B8.5 — Aprobación para producción y cierre `YOUTUBE_PRODUCTION_READY`

## 24.1 Objetivo

Autorizar, solicitar cambios o rechazar el paquete exacto que se pretende llevar a producción audiovisual.

Este bloque no autoriza publicación y no puede declarar `YOUTUBE_READY`.

## 24.2 Misiones

### B8.5-M1 — Aprobación humana para producción

Registrar `HumanProductionApproval`.

Decisiones:

```text
APPROVED_FOR_PRODUCTION
REQUEST_CHANGES
REJECT
```

La aprobación debe referenciar:

* versión del paquete;
* versión del guion;
* versión del packaging;
* versión de los reportes de plataforma y derechos;
* checksum.

`APPROVED_FOR_PRODUCTION` autoriza únicamente la producción audiovisual sobre ese paquete exacto.

Cualquier cambio posterior en guion, packaging, briefs, metadatos provisionales, riesgos o materiales previstos invalida la aprobación cuando afecte el paquete autorizado.

### B8.5-M2 — Cierre verificable de preproducción

El cierre solo puede declarar:

```text
YOUTUBE_PRODUCTION_READY
```

cuando:

* el paquete está completo;
* los artefactos obligatorios no están vacíos;
* los gates requeridos están en PASS;
* `HumanProductionApproval = APPROVED_FOR_PRODUCTION`;
* la aprobación humana corresponde a la misma versión y checksum;
* riesgos y limitaciones están declarados;
* no existe cambio posterior sin invalidación.

`YOUTUBE_PRODUCTION_READY` no significa `YOUTUBE_READY` ni `PUBLISHED`.

### B8.5-M3 — Reserva del estado YOUTUBE_READY

`YOUTUBE_READY` queda reservado para una revisión posterior sobre la pieza audiovisual final exacta.

Requerirá, como mínimo:

* archivo audiovisual final;
* miniatura final exportada;
* título final;
* descripción final;
* capítulos y timestamps reales;
* inventario real de clips;
* inventario real de música;
* revisión de contenido sintético o alterado;
* revisión de derechos de los materiales efectivamente utilizados;
* correspondencia con el paquete autorizado;
* `HumanPublicationApproval = APPROVED_FOR_PUBLICATION`.

La producción audiovisual y esta revisión final permanecen fuera del alcance inmediato del Plan 001.

## 24.3 Gate B8.5

```text
PASS si:
- HumanProductionApproval = APPROVED_FOR_PRODUCTION;
- versión y checksum coinciden;
- paquete previo a producción está completo;
- riesgos y limitaciones están declarados;
- el cierre rechaza artefactos ausentes, vacíos o ambiguos;
- el resultado declarado es YOUTUBE_PRODUCTION_READY;
- no se declara YOUTUBE_READY sin activos audiovisuales finales.
```

---

# 25. Bloque B9 — Validación con tres episodios completos

## 25.1 Objetivo

Demostrar que el sistema produce y valida episodios completos del núcleo profesional de Guion y que el arnés bloquea cierres inválidos. B9 no requiere packaging final, Shorts, SEO, publicación, Audio ni Video.

## 25.2 Casos obligatorios

### Cobertura de validación del sistema vivo

Los episodios de prueba deben validar, además de calidad:

- más de un territorio editorial;
- al menos una estructura narrativa diferente;
- variedad de aperturas;
- ausencia de repetición mecánica;
- uso correcto de VoiceProfile;
- cambio de configuración o política sin reconstrucción del core;
- compatibilidad con proveedor simulado o alternativo cuando corresponda.

No ampliar innecesariamente el número de episodios exigidos.

### Caso 1 — Episodio representativo del canal

- tema emocional;
- varias obras;
- estructura compatible con la fórmula habitual;
- objetivo: fidelidad a Más Allá del Guion.

### Caso 2 — Estructura justificada distinta

- número distinto de obras o bloques;
- desviación documentada de la fórmula habitual;
- objetivo: demostrar flexibilidad sin convertir el resultado en contenido genérico.

La estructura habitual es preferencia fuerte. La desviación debe mejorar el episodio.

### Caso 3 — Tema sensible y factual

- alta carga de claims;
- interpretaciones controvertidas;
- fuentes de distinta naturaleza;
- objetivo: comprobar evidencia, límites, verificación y bloqueo.

### Cobertura transversal de los tres casos

El conjunto de validación debe cubrir, sin necesidad de asignar una sola categoría a cada caso:

```text
ADECUACIÓN TEXTUAL Y RIESGOS ORIGINADOS EN EL GUION
- al menos un caso con tratamiento sensible;
- verificación factual e interpretativa;
- evaluación de copyright, reutilización y seguridad publicitaria cuando se originen en el texto.

TIPO DE OPORTUNIDAD
- al menos un episodio evergreen;
- al menos un episodio híbrido;
- al menos un episodio de oportunidad o actualidad.
```

Los tres casos deben comprobar también que el argumento puede seguirse sin exigir que el espectador recuerde exhaustivamente la obra.

## 25.3 Salidas obligatorias por caso

```text
EditorialProfile reference
EpisodeBrief
SourceAccessAndEvidenceReport
ResearchPack
Análisis narrativo y humano por material
Tesis provisional
Curación
PackagingHypothesis
Tesis refinada
ViewerJourney
OpeningDesign
ClosingDesign
NarrativePlan + presupuesto
Bloques versionados
AssemblyManifest
Guion ensamblado
EditorialEditReport de desarrollo
EditorialEditReport de línea/oralidad
ReadAloudReview
ClaimsLedger
FactCheckReport
SourceTransformationAndOriginalityReview
FinalEditorialAudit
EditorialScriptApproval
PromiseCorrespondenceReport
YouTubePackagingDecision
SessionContinuityPlan
Metadatos y paquete preliminar
Adecuación textual a YouTube
PlatformAndMonetizationRiskReport cuando el riesgo se origine en el texto
CopyrightAndReuseReport del material usado en el guion
```

La validación de títulos, miniatura, Shorts, SEO, metadatos de distribución, aprobación audiovisual y publicación queda clasificada como `VALIDACIÓN FUTURA DE ETAPA 2`, `DEFERRED_NOT_AUTHORIZED`, y no es requisito de B9 activo.

## 25.4 Rubric de producto

Cada caso debe evaluar:

- interés;
- profundidad;
- tesis no obvia y defendible;
- funciones distintas de materiales;
- progresión;
- recorrido del espectador;
- cumplimiento de promesa;
- apertura;
- cierre;
- naturalidad;
- ritmo;
- voz;
- oralidad;
- rigor;
- originalidad;
- transformación de fuentes;
- necesidad de reescritura humana;
- claridad;
- densidad informativa;
- coherencia local;
- coherencia entre bloques;
- profundidad del análisis narrativo y humano;
- suficiencia de contexto narrativo;
- comprensión sin conocimiento exhaustivo de la obra;
- resonancia emocional sin manipulación;

Cuando sea viable, al menos una evaluación comparativa se realizará de forma ciega.

## 25.5 Criterios mínimos

```text
0 falsos PASS en gates críticos
0 cierres con archivos vacíos
0 claims críticos sin tratamiento
0 aprobaciones aplicadas a otra versión
0 cambios posteriores a `EditorialScriptApproval` sin invalidación
3/3 EDITORIAL_SCRIPT_APPROVAL = APPROVED
```

Las métricas de edición se comparan contra el baseline. No se inventa un porcentaje de mejora sin datos.

## 25.6 Gate B9

```text
PASS solo si los tres casos cumplen:
- SYSTEM_REVIEW;
- PRODUCT_REVIEW;
- EDITORIAL_SCRIPT_APPROVAL;
- trazabilidad y checksums del núcleo de Guion;
- adecuación textual a YouTube y riesgos originados en el texto.

La validación futura de adaptación y distribución no forma parte de este gate activo.

Un caso bloqueado o fallido impide avanzar.
```

---

# 25A. Bloque B9.5 — Aprendizaje editorial controlado

## 25A.1 Objetivo

Demostrar un ciclo inicial y manual de aprendizaje editorial del Guion sin requerir publicación real. La analítica posterior de distribución queda diferida.

### B9.5-M1 — Aprendizaje editorial de episodios

Recoger observaciones de episodios de validación, correcciones humanas, resultados de benchmarks editoriales e hipótesis sobre tesis, estructura, apertura, redacción, edición y oralidad. Los estados permitidos son `SUPPORTED`, `NOT_SUPPORTED` e `INCONCLUSIVE`, con `EditorialLearningCandidate`, acumulación de evidencia y revisión humana. No requiere publicación real.

El registro publicado, las métricas de YouTube y el aprendizaje de distribución se conservan como `DEFERRED_NOT_AUTHORIZED`.

## 25A.2 Misiones

### Validación futura de Etapa 2 — Registro de versión publicada (`DEFERRED_NOT_AUTHORIZED`)

Generar `PublishedVersionManifest` para al menos un caso cuando exista publicación real.

Si no existe publicación real autorizada, usar un fixture claramente marcado como:

```text
SYNTHETIC_PUBLICATION_FIXTURE
```

No presentarlo como publicación real.

El manifest debe registrar de forma cronológica cualquier cambio posterior en:

- título;
- miniatura;
- descripción;
- pantallas finales;
- comentario fijado;
- playlist.

Cada cambio debe indicar versión anterior, versión nueva, fecha, razón y ventanas métricas afectadas.

### B9.5-M2 — Captura manual de desempeño (`DEFERRED_NOT_AUTHORIZED`)

Generar `PerformanceSnapshot`.

Toda métrica debe incluir:

* ventana de observación;
* contexto;
* tamaño de muestra;
* limitaciones.

Cada `PerformanceSnapshot` debe identificar las versiones activas de título, miniatura, descripción, pantalla final, comentario fijado y playlist durante la ventana observada.

Una ventana con cambios de versión debe dividirse o marcarse como mezclada e inconclusa para atribución causal.

### B9.5-M3 — Aprendizaje de YouTube gobernado (`DEFERRED_NOT_AUTHORIZED`)

Generar `YouTubeLearningReport`.

Separar:

* hallazgo confirmado;
* hipótesis;
* resultado inconcluso;
* aprendizaje candidato;
* experimento siguiente.

No modificar automáticamente:

* `EditorialProfile`;
* identidad;
* fórmula editorial;
* política de packaging.

### B9.5-M4 — Aprendizaje editorial gobernado

Mover aquí el contenido anteriormente previsto en `B7-M7 — Aprendizaje editorial gobernado`.

El aprendizaje contempla fuentes desde:

- correcciones humanas;
- comparación entre borrador y versión aprobada;
- resultados editoriales de episodios de validación;
- correcciones humanas y comparación entre borrador y versión aprobada;
- resultados de apertura y edición;
- cambios de perfil o nuevas políticas cuando estén aprobados;
- resultados inconclusos.

Las fuentes de publicación, packaging y métricas de YouTube pertenecen al tramo diferido `DEFERRED_NOT_AUTHORIZED`.

Flujo de aprendizaje:

```text
evidencia
→ candidato
→ acumulación
→ revisión humana
→ aprobación
→ nueva versión
```

Prohibido:

- actualizar automáticamente la identidad;
- convertir una sola corrección en regla;
- mezclar hallazgos de plataforma con identidad sin aprobación;
- generalizar desde muestras pequeñas.

Una sola corrección no se convierte en regla estable.

## 25A.3 Gate B9.5

```text
PASS si:
- observaciones y correcciones editoriales están identificadas sin ambigüedad;
- candidatos de aprendizaje tienen evidencia y revisión humana;
- hallazgos e hipótesis están separados;
- ningún aprendizaje modificó el perfil automáticamente;
- existe siguiente experimento o decisión explícita de no experimentar.

El registro publicado, `PerformanceSnapshot` y el aprendizaje de distribución quedan fuera de este gate activo y permanecen `DEFERRED_NOT_AUTHORIZED`.
```

---

# 26. Bloque B10 — Lean/5S, portabilidad, documentación y cierre

## 26.1 Objetivo

Reducir duplicación y contradicciones sin borrar evidencia ni romper compatibilidad, cerrando Lean/5S, portabilidad y deuda técnica de la Etapa 1 sin depender de publicación, analítica de YouTube, Audio o Video. La Etapa 2 tendrá un cierre posterior cuando sea autorizada.

## 26.2 Misiones

### B10-M1 — Consolidar QA duplicados

Revisar y consolidar:

- `qa_brief_research.py` / `qa_momento_1.py`;
- QA de lenguaje normal / ultra;
- skills duplicadas de QA;
- reglas de riesgo de plataforma dispersas.

Antes de retirar algo:

- pruebas de caracterización;
- mapa de reglas conservadas;
- adapter o deprecación;
- evidencia de no pérdida.

### B10-M2 — Separar tipos de QA

Distinguir:

```text
CONTRACT_QA
PLATFORM_RISK_QA
EDITORIAL_EDIT
FINAL_EDITORIAL_AUDIT
FACTUAL_VERIFICATION
ORIGINALITY_REVIEW
```

### B10-M3 — Clasificar documentos

Estados documentales:

```text
ACTIVE
NORMATIVE
TEMPLATE
EVIDENCE
HISTORICAL
SUPERSEDED
DEPRECATED
```

### B10-M4 — Sedes documentales

Separar:

- identidad;
- contratos;
- workflows;
- configuración;
- evidencia;
- histórico;
- outputs temporales;
- perfiles;
- episodios.

### B10-M5 — Portabilidad

- settings locales fuera de Git;
- configuración de ejemplo portable;
- rutas POSIX y Windows;
- root del repositorio como referencia;
- no depender del CWD;
- pruebas de rutas;
- proveedor de IA por adapter.

### B10-M6 — `.gitignore` y seguridad básica

Asegurar que:

- documentación activa se versiona;
- secretos y settings locales no;
- Vault y datos privados no;
- caches y entornos virtuales no;
- fixtures privados no;
- evidencia pública y privada se diferencian.

### B10-M7 — README operativo

Documentar:

- instalación;
- configuración;
- perfil activo;
- creación de episodio;
- workflow;
- gates;
- estados;
- pruebas;
- aprobación humana;
- evidencias;
- modo single-agent;
- provider adapters;
- recuperación ante bloqueo.

### B10-M8 — Limpieza de nomenclatura

Corregir:

- mezcla `OK/PASS`;
- fases mal numeradas;
- Acto/Fase/Momento sin contrato;
- contradicciones Vault/output;
- nombres que presentan el sistema como general antes de tiempo.

### B10-M9 — Cierre, versión y decisiones futuras

Acciones:

1. Ejecutar las validaciones de la Etapa 1.
2. Ejecutar auditoría de arquitectura y portabilidad.
3. Ejecutar auditoría editorial del Guion.
4. Revisar seguridad, rutas y configuración.
5. Actualizar README y mapa de arquitectura.
6. Marcar documentos sustituidos.
7. Consolidar changelog.
8. Etiquetar versión estable del núcleo de Guion.
9. Registrar deudas no bloqueantes.
10. Comparar resultados contra benchmarks editoriales.
11. Documentar si las capacidades generalizables son realmente extraíbles.

Las auditorías de adaptación, derechos de publicación, producción audiovisual, Audio, Video y analítica de YouTube pertenecen a la Etapa 2 `DEFERRED_NOT_AUTHORIZED`.

### B10-M10 — Decisiones futuras permitidas

Solo después de la validación podrán evaluarse:

- extraer el motor a otro repositorio;
- convertir responsabilidades en subagentes;
- implementar un adaptador de investigación estable;
- soportar otros canales;
- añadir UI;
- añadir base de datos;
- automatizar publicación;
- integrar analítica automática;
- automatizar experimentos;
- extender a podcast.

## 26.3 Gate B10

```text
PLAN_STATUS: PASS_FOR_SCRIPT_CORE
SYSTEM_REVIEW: PASS
PRODUCT_REVIEW: PASS
EDITORIAL_SCRIPT_APPROVAL: PASS
CLOSURE_STATE: EDITORIAL_SCRIPT_APPROVED
STAGE_2_CLOSURE: DEFERRED_NOT_AUTHORIZED
```

---

## 27. Dependencias entre bloques

```text
B0
 └── B1
      ├── B2
      └── B3
           └── B4
                └── B5
                     └── B5.5
                          └── B6
                               └── B7
                                    └── B9 (NÚCLEO DE GUION)
                                                        └── B9.5 (APRENDIZAJE EDITORIAL)
                                                             └── B10 (CIERRE ETAPA 1)
```

Cadena activa de la Etapa 1:

```text
B7 / EDITORIAL_SCRIPT_APPROVED
  → B9 / validación del núcleo de Guion
  → B9.5 / aprendizaje editorial aplicable
  → B10 / cierre de Etapa 1
```

Cadena diferida de la Etapa 2:

```text
autorización futura → B7.5 → componentes diferidos de B8 → B8.5 → validación futura de adaptación y distribución
```

No se inicia B6 sin PASS de B5.5.

No se inicia B7.5 sin `EditorialScriptApproval = APPROVED`; esta condición habilita únicamente la etapa posterior autorizada y no amplía el MVP.

No se declara `YOUTUBE_PRODUCTION_READY` sin PASS de B8, HumanProductionApproval y Gate B8.5.

No se declara `YOUTUBE_READY` sin pieza audiovisual final, activos definitivos, revisión final de derechos y HumanPublicationApproval.

No se presenta un fixture como publicación real.

No se cierre el plan mientras existan falsos PASS conocidos.

---

## 28. Política de implementación por misiones

Para evitar misiones gigantes y cadenas de micromisiones:

- cada misión agrupa dos o tres cambios relacionados;
- cada misión tiene un objetivo verificable;
- no mezcla cambios editoriales, infraestructura y limpieza;
- no obliga al ejecutor a rediagnosticar fallos ya probados;
- define archivos autorizados y prohibidos;
- define pruebas y evidencias;
- no autoriza commit o push salvo indicación expresa;
- exige revisar el diff real y el estado de Git cuando se modifican archivos;
- el reporte del agente no sustituye la inspección del diff;
- termina en `READY_FOR_AUDIT`, no en `PASS` automático.

### 28.1 Plantilla de reporte

```text
MISSION_ID:
BLOCK_ID:
STATUS:
OBJECTIVE:
FILES_READ:
FILES_MODIFIED:
FILES_CREATED:
COMMANDS_EXECUTED:
TESTS_EXECUTED:
TEST_RESULTS:
GIT_STATUS:
DIFF_SUMMARY:
STAGED_FILES:
EVIDENCE_PATHS:
RISKS:
BLOCKERS:
SELF_AUDIT:
READY_FOR_EXTERNAL_AUDIT: YES/NO
```

---

## 29. Control de cambios del plan

| Versión | Fecha | Cambio | Motivo | Impacto | Estado |
|---|---|---|---|---|---|
| 1.0 | 2026-07-21 | Borrador inicial | Consolidar auditorías técnicas y editoriales | Base del plan | `SUPERSEDED` |
| 1.1 | 2026-07-21 | Reescritura integral con auditoría de Producto | Completar el producto editorial y evitar generalización prematura | Cambia arquitectura funcional, contratos y bloques | `READY_FOR_FINAL_APPROVAL` |
| 1.2 | 2026-07-21 | Incorporación de Adaptación profesional a YouTube | Completar packaging, correspondencia, plataforma, derechos, publicación y aprendizaje | Amplía contratos y tramo final sin cambiar el producto rector | `READY_FOR_FINAL_APPROVAL` |
| 1.3 | 2026-07-21 | Incorporación consolidada de validaciones finales funcionales | Corregir autoridad funcional, EditorialProfile, análisis narrativo y humano, oficio de escritura, interfaces funcionales, aprobación para producción, reserva de YOUTUBE_READY y trazabilidad pospublicación | Modifica contratos y estados sin cambiar bloques ni autorizar implementación | `READY_FOR_REVALIDATION` |
| 1.4 | 2026-07-22 | PRE-B3 evolutionary architecture alignment | Principio de evolucionabilidad, EditorialProfile extensible, corpus y voz, puntos de extensión en B4, OPENING_UNIT en B5, antiartificialidad en B6, auditorías separadas en B7, políticas YouTube versionadas en B7.5, validación de sistema vivo en B9, aprendizaje extendido en B9.5, MVP/post-MVP | Documentación exclusiva; no cambia bloques, contratos, schemas ni autorización | `READY_FOR_EXTERNAL_AUDIT` |

### 29.1 Regla de modificación

- corrección menor: versión de parche;
- nuevo bloque o dependencia: versión menor;
- cambio de objetivo: versión mayor y nueva aprobación;
- toda modificación registra motivo, impacto y autoridad;
- el silencio no equivale a aprobación.

---

## 30. Registro de riesgos

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---:|---:|---|
| Diluir la identidad al generalizar | Media | Alta | Mantener MADG como producto rector |
| Sobrediseñar contratos | Media | Media | Implementación incremental y fixtures |
| Crear demasiados agentes | Alta | Media | Single-agent hasta validación |
| Mezclar Editor y Auditor | Media | Alta | Contratos y ejecuciones separadas |
| Gates demasiado laxos | Alta | Alta | Pruebas negativas |
| Gates demasiado rígidos | Media | Alta | Separar contrato, plataforma y juicio editorial |
| Degradar contenido para pasar scripts | Media | Alta | Auditoría editorial independiente |
| Escribir sin evidencia suficiente | Alta | Alta | Evidence Sufficiency Gate |
| Fingir acceso a obras | Media | Alta | SourceAccessAndEvidenceReport |
| Packaging sobreprometido | Media | Alta | PackagingHypothesis + gate de promesa |
| Estructura flexible se vuelve genérica | Media | Alta | Fórmula como preferencia fuerte + auditoría de identidad |
| Redacción por bloques fragmentada | Alta | Alta | Context pack + edición integral |
| Editor aprueba su propio trabajo | Media | Alta | Auditor final independiente |
| Corrección superficial de defecto estructural | Alta | Alta | CorrectionRoutingPolicy |
| Pérdida de trazabilidad por sobrescritura | Media | Alta | Manifest, checksum e inmutabilidad |
| Copia o imitación de fuentes | Media | Alta | Originality Review |
| Perfil contaminado por una corrección | Alta | Alta | LearningCandidate gobernado |
| Dependencia de un adaptador de investigación externo | Media | Alta | Camino local y adapters |
| Borrar evidencia en limpieza | Media | Alta | Archivar antes de eliminar |
| Validación editorial demasiado tardía | Media | Alta | B5.5 prototipo controlado |
| Loops infinitos | Media | Media | Máximo tres ciclos y bloqueo humano |
| Romper episodios antiguos | Alta | Media | Adapter de compatibilidad |

---

## 31. Elementos fuera de alcance

Durante este plan no se prioriza:

- repositorio nuevo;
- motor general multicanal;
- SaaS;
- UI completa;
- publicación automática;
- base de datos;
- analítica avanzada;
- segundo canal;
- producción visual;
- podcast;
- instalación de skills externas;
- múltiples subagentes por defecto;
- cambio de proveedor como objetivo;
- mutation testing de contenido editorial;
- MCP obligatorio;
- entrenamiento o fine-tuning de modelos;
- eliminación de la fórmula del canal.

Cualquier incorporación requiere cambio formal del plan.

---

## 31A. MVP y post-MVP

### MVP activo — núcleo profesional de Guion

- EditorialProfile versionado;
- territorios extensibles;
- corpus inicial;
- VoiceProfile inicial;
- patrones candidatos;
- redacción por bloques;
- editor separado;
- auditoría antiartificialidad básica;
- aprobación humana;
- proveedor configurable al menos por contrato;
- entrada canónica única.

El cierre principal del MVP de Guion es `EDITORIAL_SCRIPT_APPROVED`. La adecuación textual a YouTube, incluida la evaluación de riesgos de plataforma, monetización y copyright originados en el texto, pertenece a esta etapa.

### Etapa 2 — adaptación y distribución (diferida / no autorizada)

Packaging final, títulos, miniatura conceptual, Shorts, SEO, metadatos, continuidad y paquete de distribución se conservan en B7.5, B8 y B8.5, pero no se desarrollan, amplían ni ejecutan ahora ni bloquean la aprobación del guion.

Audio se desarrolla en otro repositorio y solo se integrará mediante un contrato futuro versionado. Video queda fuera del alcance de este repositorio; no se implementan edición, montaje, visuales, animación, render ni exportación.

### Post-MVP (no implementar ahora)

- Telegram;
- voz;
- aplicación web;
- múltiples proveedores reales;
- auditoría cruzada entre modelos;
- evaluación ciega avanzada;
- análisis estadístico de estilo;
- aprendizaje automatizado supervisado;
- métricas avanzadas de YouTube;
- experimentación A/B.

---

## 32. Definition of Done

### Definition of Done activa — Núcleo de Guion

La Etapa 1 se considera completada cuando el núcleo profesional de Guion alcanza `EDITORIAL_SCRIPT_APPROVED`, B9 valida tres episodios y B9.5 deja aprendizaje editorial aplicable para B10:

- [ ] Más Allá del Guion sigue siendo el producto rector;
- [ ] existe un EditorialProfile versionado y trazable;
- [ ] el motor no lee documentos sueltos del canal durante producción normal;
- [ ] brief y tipo de guion tienen contrato único;
- [ ] existe PackagingHypothesis antes del outline;
- [ ] existe SourceAccessAndEvidenceReport;
- [ ] evidencia insuficiente bloquea;
- [ ] viewer journey está modelado;
- [ ] apertura y cierre tienen contrato;
- [ ] estados y exit codes son únicos;
- [ ] no existen falsos PASS conocidos;
- [ ] el cierre rechaza vacíos, versiones distintas o aprobación ausente;
- [ ] el workflow tiene orden correcto;
- [ ] existen pruebas automatizadas;
- [ ] los roles, responsabilidades operativas y familias funcionales están mapeados, tienen dueño, contrato, veto y evidencia;
- [ ] el sistema funciona con un solo agente operativo;
- [ ] Editor y Auditor final están separados;
- [ ] curación, análisis, arquitectura, escritura y edición están profesionalizados;
- [ ] el análisis narrativo y humano está trazado por material y limita explícitamente sus inferencias;
- [ ] B5.5 demuestra mejora editorial temprana;
- [ ] los guiones se redactan por bloques con memoria global;
- [ ] la redacción demuestra oficio narrativo y no repite una plantilla expositiva fija;
- [ ] ensamblaje es reproducible;
- [ ] existe edición de desarrollo;
- [ ] existe edición de línea y oralidad;
- [ ] se ejecuta Read-Aloud Review;
- [ ] claims y escenas están trazados;
- [ ] existe auditoría de originalidad y transformación;
- [ ] defectos se enrutan a la fase correcta;
- [ ] artefactos y aprobaciones están versionados e invalidados correctamente;
- [ ] aprobación editorial del guion ocurre sobre una versión exacta;
- [ ] Adaptación a YouTube está separada de auditoría editorial;
- [ ] QA de lenguaje funciona solo como detector auxiliar;
- [ ] ningún componente promete “100 % monetizable”;
- [ ] riesgo de plataforma se evalúa con contexto;
- [ ] copyright, Content ID y contenido reutilizado están diferenciados;
- [ ] `EDITORIAL_SCRIPT_APPROVED`, `YOUTUBE_PRODUCTION_READY`, `YOUTUBE_READY` y `PUBLISHED` son estados distintos;
- [ ] aprendizajes editoriales están gobernados;
- [ ] entregable final incluye guion limpio, anotado, claims y limitaciones;
- [ ] QA contractual, plataforma, edición y auditoría están separados;
- [ ] documentos históricos están clasificados;
- [ ] rutas, configuración y README son portables;
- [ ] los tres episodios de validación obtienen PASS;
- [ ] las validaciones funcionales obligatorias están aprobadas para la misma versión y checksum;
- [ ] el sistema verifica contratos, invariantes, versionado y consistencia del cierre;
- [ ] la aprobación editorial humana correspondiente está registrada por separado y no se confunde con aprobación de producción o publicación.

### Definition of Done futura — Etapa 2 (`DEFERRED_NOT_AUTHORIZED`)

Los siguientes requisitos pertenecen a la Etapa 2 y no bloquean el cierre de la Etapa 1. Solo podrán activarse mediante autorización explícita:

- [ ] existe auditoría de correspondencia entre título, miniatura, apertura, desarrollo y cierre;
- [ ] packaging final contiene opción recomendada, alternativas y descartes;
- [ ] existe brief de producción audiovisual y derechos;
- [ ] Shorts tienen función estratégica explícita;
- [ ] SEO fue sustituido por Metadatos y paquete de publicación;
- [ ] continuidad de sesión está definida o su ausencia justificada;
- [ ] existe PublicationPackage versionado;
- [ ] HumanProductionApproval corresponde al paquete exacto autorizado para producción;
- [ ] HumanPublicationApproval está reservado para la pieza audiovisual final exacta;
- [ ] existe registro de versión publicada o fixture inequívocamente sintético;
- [ ] métricas, hipótesis y aprendizajes de distribución están separados y gobernados.

---

## 33. Próximo paso tras la auditoría externa

B0, B3 y B4 permanecen abiertos en recuperación; B1 y B2 conservan cierre `PASS`. B5-I1 mantiene pase técnico pendiente de confirmación funcional y B5-I2 sigue implementado con validación mock, pero pendiente de ejecución real y confirmación funcional.

La siguiente acción permitida se resuelve exclusivamente mediante el control operativo vigente.

B5-I3 no está autorizado. La Etapa 2 permanece diferida y no puede iniciarse automáticamente.

---

## 34. Estado de aprobación

```text
PLAN_ID: PLAN-001
PLAN_VERSION: 1.4
PLAN_STATUS: READY_FOR_EXTERNAL_AUDIT
FUNCTIONAL_AUDIT_SOURCES:
- CHANNEL_INTELLIGENCE_APPROVED_WITH_REQUIRED_AMENDMENTS
- SCRIPT_PRODUCT_APPROVED_WITH_REQUIRED_AMENDMENTS
- YOUTUBE_ADAPTATION_APPROVED_WITH_REQUIRED_AMENDMENTS
- PRE-B3-EVOLUTIONARY-ARCHITECTURE-ALIGNMENT
CONSOLIDATION_OWNER: TECHNICAL_GOVERNANCE
REQUIRED_AMENDMENTS_INCORPORATED: YES
IMPLEMENTATION_AUTHORIZED: SEE_LIVE_OPERATIONAL_CONTROL
PLAN_001_STATUS: SEE_LIVE_OPERATIONAL_CONTROL
CURRENT_ACTIVE_PHASE: SEE_LIVE_OPERATIONAL_CONTROL
B5_I2_IMPLEMENTATION: COMPLETED
B5_I2_TECHNICAL_CORRECTION: PASS_WITH_RESIDUAL_RISK
B5_I2_REAL_SEMANTIC_AUDIT: NOT_DEMONSTRATED
B5_I2_SCRIPT_PRODUCT_FUNCTIONAL_REAUDIT: PENDING
B5_I3: NOT_AUTHORIZED
STAGE_2_YOUTUBE_DISTRIBUTION: DEFERRED_NOT_AUTHORIZED
AUDIO_INTEGRATION: EXTERNAL_REPOSITORY_FUTURE_CONTRACT
VIDEO_PRODUCTION: OUT_OF_REPOSITORY_SCOPE
NEXT_ALLOWED_ACTION: PREPARE_R2_CANONICAL_SANITATION_AND_ENFORCEMENT
```
