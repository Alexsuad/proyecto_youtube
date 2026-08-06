# IR-0 — Plan técnico de implementación de investigación editorial post-P08 v2

**Modo:** READ_ONLY
**Implementación autorizada:** NO
**Fuente funcional:** `plan_implementacion_investigacion_editorial_post_p08_v2_2026-08-05.md`
**Repositorio auditado:** `proyecto_youtube_2026-08-05_18-23-01.zip`

## Dictamen

La base moderna del repositorio debe conservarse: `EpisodeBrief`, `ResearchPack`, `SourceAccessAndEvidenceReport`, `ClaimsLedger`, análisis narrativo y humano, curación, tesis refinada, auditorías semánticas, invalidación y separación de responsabilidades.

No existe todavía una capacidad completa de investigación editorial. Las brechas principales son: `PhenomenonResearchPack` diferenciado, `WorkResearchDossier`, lifecycle progresivo, provenance de fuentes derivadas, decisiones de suficiencia por objeto, memoria semántica interepisódica, contribuciones especialistas y vertical real auditada.

## Orden técnico por dependencias

### 1. Gobernanza y trazabilidad IR-0

- Incorporar la matriz IR-0 como fuente técnica de requisitos.
- Preservar `IMPLEMENTATION_AUTHORIZED = NO` y `REAL_EPISODE_AUTHORIZED = NO`.
- Separar explícitamente `IMPLEMENTATION_WORKSTREAM` y `EDITORIAL_RESEARCH_WORKFLOW` sin crear una segunda autoridad de estado vivo.
- No activar capacidades.

**Salida técnica futura:** mapa requisito → contrato/componente → prueba → evidencia → owner.

### 2. Contratos base de investigación

- Completar o versionar `ResearchPack` como `PhenomenonResearchPack` sin duplicar conceptos ya válidos.
- Crear `WorkResearchDossier` progresivo y versionado.
- Normalizar el registro de fuentes y su relación con claims.
- Conectar dossier, análisis narrativo, curación y evidencia.

**Dependencia:** paquete 1.

### 3. Lifecycle y provenance

- Crear lifecycle canónico de obras y transiciones.
- Aplicar profundidad mínima por estado.
- Integrar rangos 5–8 y 3–5 como política normal, no cuota rígida universal.
- Crear taxonomía de fuente original y representaciones derivadas.
- Representar audiovisual, idioma, versión, timestamps y método de obtención.

**Dependencia:** contratos base.

### 4. Claims, suficiencia y contradicciones

- Normalizar `CLAIM_ALLOWED`, `CLAIM_LIMITED` y `CLAIM_BLOCKED`.
- Crear `ResearchStopDecision` para fenómeno, obra, claim material y paquete agregado.
- Implementar los cuatro estados de suficiencia.
- Añadir disposition de contradicciones y prohibir selección silenciosa de evidencia conveniente.

**Dependencia:** contracts + lifecycle + provenance.

### 5. Memoria y responsabilidades especializadas

- Crear memoria semántica interepisódica de `SCRIPT_PRODUCT`.
- Integrar consultas en los cinco hitos aprobados.
- Representar decisiones de novedad y reutilización sin bloqueo automático.
- Crear contrato de contribución especializada y política adaptativa de activación.
- Mantener a `SCRIPT_PRODUCT` como owner de suficiencia editorial.

**Dependencia:** claims y objetos versionados estables.

### 6. Auditoría, adapters y activación técnica

- Separar auditorías de suficiencia, fidelidad, interpretación, claims/fuentes, curación y paquete final.
- Extender independencia productor–auditor a toda la investigación.
- Completar rutas de corrección e invalidación dependientes de P-07.
- Materializar `SOURCE_GROUNDED_RESEARCH_ADAPTER` como interfaz opcional, agnóstica y no autoritativa.
- Mantener separados aprobación funcional, activación técnica y autorización interequipos.

**Dependencia:** paquetes 2–5.

### 7. Vertical real y casos obligatorios

- Ejecutar una vertical real `TOPIC_FIRST` solo después de autorización expresa.
- Cubrir casos aprobados, rechazados, bloqueados, limitados y negativos.
- Demostrar productor y auditor distintos.
- Conservar evidencia de inputs, outputs, decisiones, rutas de retorno y limitaciones.
- La suite técnica no sustituye la aprobación funcional de `SCRIPT_PRODUCT`.

**Dependencia:** todos los paquetes anteriores y autorización separada.

## Decisiones funcionales pendientes

Antes de materializar los requisitos correspondientes, `SCRIPT_PRODUCT` debe cerrar únicamente:

1. Qué constituye una duda crítica suficiente para profundizar una obra antes de `FINALIST_WORK`.
2. Qué umbral operativo activa multilingüismo por cobertura insuficiente o controversia lingüística.
3. Qué se considera `claim material` para exigir una `ResearchStopDecision` específica.

Estas decisiones no bloquean el diseño de contratos base, pero sí los gates finales afectados.

## Prohibiciones

- No crear misiones para Codex todavía.
- No modificar el repositorio.
- No activar B5-I1, B5-I2, B5-I3, B5.5 o B6.
- No declarar vertical real demostrada.
- No convertir NotebookLM en dependencia obligatoria.
- No prescribir un agente por responsabilidad investigativa.

## Estado

```text
IR0_STATUS: COMPLETED_READ_ONLY
IMPLEMENTATION_AUTHORIZED: NO
NEXT_ACTION: OWNER_REVIEW_OF_IR0_MATRIX_AND_TECHNICAL_ORDER
```
