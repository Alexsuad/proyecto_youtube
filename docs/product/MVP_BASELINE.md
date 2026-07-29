# MVP baseline — Proyecto YouTube

```yaml
mvp_baseline:
  mvp_id: PROYECTO-YOUTUBE-MVP
  canonical_artifact: docs/product/MVP_BASELINE.md
  version: "1.1.0"
  status: DEFINED
  approved_by: OWNER
  approved_at: 2026-07-26
  supersedes: []
  related_delivery_plan:
    artifact: plans/001_reestructuracion_motor_agentico_editorial_y_harness.md
    version: "1.4"
```

## Producto, problema y usuario

El MVP es el núcleo profesional de guiones de Más Allá del Guion: un sistema portable que deja evidencia de un guion hasta `EDITORIAL_SCRIPT_APPROVED`, sin diluir la identidad del canal ni depender de un único proveedor. No incluye el paquete de distribución, publicación automática ni una pieza audiovisual final.

Resuelve entradas incompletas, evidencia insuficiente, falsos PASS, contratos incompatibles, aprobaciones sobre una versión distinta y pérdida de coherencia entre bloques. Lo usan el propietario y operadores autorizados; Inteligencia del Canal, Producto Guion y Adaptación a YouTube consumen o auditan salidas en su especialidad, y Gobernanza Técnica gobierna contratos, integración, pruebas y evidencia. La audiencia final del canal no es usuaria del sistema.

## Promesa, capacidades y aceptación

La promesa mínima es completar un flujo trazable desde identidad y brief hasta guion aprobado, incluyendo su adecuación textual a YouTube. Packaging final, Shorts, SEO y distribución se conservan para una segunda etapa que requiere autorización expresa.

| ID | Capacidad obligatoria | Criterio de aceptación y bloques |
| --- | --- | --- |
| MVP-CAP-001 | Consumir EditorialProfile versionado, trazable y aprobado funcionalmente. | MVP-AC-001: identidad preservada y sin documentos sueltos en producción. B3–B4. |
| MVP-CAP-002 | Diseñar brief, tipo, investigación, evidencia, tesis y recorrido trazables. | MVP-AC-002: evidencia insuficiente, vacíos y estados contradictorios no hacen PASS. B1–B2, B5. |
| MVP-CAP-003 | Redactar por bloques con memoria global, ensamblaje reproducible y edición separada. | MVP-AC-003: diseño, redacción, edición y auditoría trazables. B5–B7. |
| MVP-CAP-004 | Auditar evidencia, factualidad, originalidad, oralidad y coherencia. | MVP-AC-003. B5–B7. |
| MVP-CAP-005 | Adecuar textualmente el guion a YouTube, sin deformar la tesis, considerando apertura, duración orientativa, monetización, seguridad publicitaria, copyright y riesgos originados en el texto. | MVP-AC-004: versión editorial exacta y aprobación del guion. B5–B7. |
| MVP-CAP-006 | Versionar, aprobar editorialmente e invalidar ante cambios posteriores. | MVP-AC-004. B1–B2, B7. |
| MVP-CAP-007 | Operar con contratos, gates y pruebas deterministas, portable y configurable por contrato. | MVP-AC-005: tres casos B9 con evidencia de cierre. B1–B2, B9. |

Esta tabla normaliza, sin sustituir, la Definition of Done del Plan 001 §32. El cierre además requiere aprobación de Producto, Sistema y Humano, que un agente no puede emitir.

## Alcance, restricciones y dependencias

El MVP activo termina en `EDITORIAL_SCRIPT_APPROVED`. Packaging final, títulos, miniatura conceptual, Shorts, SEO, metadatos y paquete de distribución pertenecen a la Etapa 2, diferida y no autorizada. Audio se desarrolla en un repositorio independiente y se integrará mediante un contrato futuro versionado. Video queda fuera del alcance de este repositorio.

Se conserva el fuera de alcance del Plan 001 §31: repositorio nuevo, motor multicanal, SaaS, UI completa, publicación automática, base de datos, analítica avanzada, producción visual, podcast, skills externas, subagentes por defecto, cambio de proveedor como objetivo, MCP obligatorio y fine-tuning.

Post-MVP conocido (§31A): Telegram, voz, aplicación web, múltiples proveedores reales, auditoría cruzada entre modelos, evaluación ciega avanzada, análisis estadístico de estilo, aprendizaje automatizado supervisado, métricas avanzadas de YouTube y experimentación A/B. Esta referencia no autoriza su implementación.

Restricciones: portabilidad, independencia de proveedores, aprobaciones humanas, trazabilidad/versionado/invalidation, ausencia de publicación automática y límites de plataforma/runtime. Dependencias críticas: EditorialProfile, contratos, gates, pruebas, aprobaciones funcionales y validación B9.

## Autoridad, estado y trazabilidad

Inteligencia del Canal define identidad, audiencia editorial, promesa, voz y perfil; Producto Guion define el producto narrativo; Adaptación a YouTube define la adecuación textual a plataforma; Gobernanza Técnica valida contratos, pruebas e integración. El propietario y las responsabilidades funcionales aprueban este MVP y cualquier cambio de producto, alcance o aceptación.

Estado: definido mediante esta consolidación; la etapa activa es el núcleo profesional de Guion. El estado operativo vigente, el incremento activo, las auditorías pendientes y la siguiente acción autorizada se mantienen exclusivamente en `plans/001_CONTROL_OPERATIVO.md`. La Etapa 2 requiere autorización expresa del propietario. El cierre principal del MVP es `EDITORIAL_SCRIPT_APPROVED`.

```text
ACTIVE_PRODUCT_STAGE: SCRIPT_CORE
STAGE_2_YOUTUBE_DISTRIBUTION: DEFERRED_NOT_AUTHORIZED
AUDIO_INTEGRATION: EXTERNAL_REPOSITORY_FUTURE_CONTRACT
VIDEO_PRODUCTION: OUT_OF_REPOSITORY_SCOPE
```

Fuentes: Plan 001 v1.4 (§2, §4, §7, §31, §31A, §32), `docs/ALCANCE_Y_COORDINACION_EQUIPOS.md`, B0, B9, B9.5 y `docs/specifications/B3_editorial_profile_functional_specification.md`. La decisión de alcance fue aprobada por el propietario; la validación funcional y técnica de la implementación permanece separada.

Nota de cambio v1.1.0: el MVP activo termina en `EDITORIAL_SCRIPT_APPROVED`; la adaptación y distribución quedan diferidas; Audio y Video se tratan como productos externos o fuera del repositorio.
