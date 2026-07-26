# PLAN-001 / B9 — Validación con tres episodios completos

**Plan rector:** [`../001_reestructuracion_motor_agentico_editorial_y_harness.md`](../001_reestructuracion_motor_agentico_editorial_y_harness.md)  
**Control operativo:** [`../001_CONTROL_OPERATIVO.md`](../001_CONTROL_OPERATIVO.md)  
**Versión derivada:** `PLAN-001 v1.4`
**Estado inicial:** `PLANNED`  
**Dependencia activa:** `B7 / EDITORIAL_SCRIPT_APPROVED`
**Siguiente tramo:** `B9.5`  
**Gate resumido:** Tres casos aprobados

> Este archivo es una proyección operativa del Plan 001. No crea autoridad nueva ni sustituye el plan rector. Ante una contradicción, prevalece el plan rector y debe bloquearse la misión hasta resolverla.

## 0. Uso operativo

Lectura mínima para ejecutar una misión de este bloque:

1. `AGENTS.md` del repositorio, si existe.
2. docs/ALCANCE_Y_COORDINACION_EQUIPOS.md.
3. `plans/001_CONTROL_OPERATIVO.md`.
4. Este archivo.
5. La misión concreta y los archivos expresamente autorizados.

No leer por defecto el Plan 001 completo, otros bloques, todo `workspace/` ni reportes históricos. Consultar el plan rector únicamente para resolver una contradicción, una autoridad, una dependencia o una referencia expresa.

### Referencias normativas relacionadas

- B0 benchmarks y rubric
- Todos los controles de la Etapa 1 hasta `EDITORIAL_SCRIPT_APPROVED`
- §32 Definition of Done global

---

## 1. Objetivo

Demostrar que el sistema produce y valida episodios completos del núcleo profesional de Guion y que el arnés bloquea cierres inválidos. B9 no requiere packaging final, Shorts, SEO, publicación, Audio ni Video.

## 2. Casos obligatorios

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

## 3. Salidas obligatorias por caso

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
Adecuación textual a YouTube
PlatformAndMonetizationRiskReport cuando el riesgo se origine en el texto
CopyrightAndReuseReport del material usado en el guion
```

La validación de títulos, miniatura, Shorts, SEO, metadatos de distribución, aprobación audiovisual y publicación queda clasificada como `VALIDACIÓN FUTURA DE ETAPA 2`, `DEFERRED_NOT_AUTHORIZED`, y no es requisito de B9 activo.

## 4. Rubric de producto

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

## 5. Criterios mínimos

```text
0 falsos PASS en gates críticos
0 cierres con archivos vacíos
0 claims críticos sin tratamiento
0 aprobaciones aplicadas a otra versión
0 cambios posteriores a `EditorialScriptApproval` sin invalidación
3/3 EDITORIAL_SCRIPT_APPROVAL = APPROVE
```

Las métricas de edición se comparan contra el baseline. No se inventa un porcentaje de mejora sin datos.

## 6. Gate B9

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
