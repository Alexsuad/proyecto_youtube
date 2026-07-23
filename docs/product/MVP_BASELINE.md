# MVP baseline — Proyecto YouTube

```yaml
mvp_baseline:
  mvp_id: PROYECTO-YOUTUBE-MVP
  canonical_artifact: docs/product/MVP_BASELINE.md
  version: "1.0.0"
  status: DEFINED
  approved_by: OWNER
  approved_at: 2026-07-23
  supersedes: []
  related_delivery_plan:
    artifact: plans/001_reestructuracion_motor_agentico_editorial_y_harness.md
    version: "1.4"
```

## Producto, problema y usuario

El MVP es el motor profesional de guiones de Más Allá del Guion: un sistema portable que deja evidencia de un guion y su paquete previo a producción, sin diluir la identidad del canal ni depender de un único proveedor. Entrega casos `YOUTUBE_PRODUCTION_READY`, no publicación automática ni una pieza audiovisual final.

Resuelve entradas incompletas, evidencia insuficiente, falsos PASS, contratos incompatibles, aprobaciones sobre una versión distinta y pérdida de coherencia entre bloques. Lo usan el propietario y operadores autorizados; los equipos 01, 02 y 03 consumen o auditan salidas en su especialidad, y el Equipo 04 gobierna contratos, integración, pruebas y evidencia. La audiencia final del canal no es usuaria del sistema.

## Promesa, capacidades y aceptación

La promesa mínima es completar un flujo trazable desde identidad y brief hasta guion aprobado, adaptación profesional y paquete exacto autorizado para producción. La evidencia exigida son los tres casos B9 y sus contratos, gates, aprobaciones e invalidaciones.

| ID | Capacidad obligatoria | Criterio de aceptación y bloques |
| --- | --- | --- |
| MVP-CAP-001 | Consumir EditorialProfile versionado, trazable y aprobado funcionalmente. | MVP-AC-001: identidad preservada y sin documentos sueltos en producción. B3–B4. |
| MVP-CAP-002 | Diseñar brief, tipo, investigación, evidencia, tesis y recorrido trazables. | MVP-AC-002: evidencia insuficiente, vacíos y estados contradictorios no hacen PASS. B1–B2, B5. |
| MVP-CAP-003 | Redactar por bloques con memoria global, ensamblaje reproducible y edición separada. | MVP-AC-003: diseño, redacción, edición y auditoría trazables. B5–B7. |
| MVP-CAP-004 | Auditar evidencia, factualidad, originalidad, oralidad y coherencia. | MVP-AC-003. B5–B7. |
| MVP-CAP-005 | Adaptar a YouTube sin deformar tesis, evaluando packaging, plataforma y derechos. | MVP-AC-004: versiones y aprobaciones exactas, estados no confundidos. B7.5–B8.5. |
| MVP-CAP-006 | Versionar, aprobar humanamente e invalidar ante cambios posteriores. | MVP-AC-004. B1–B2, B7–B8.5. |
| MVP-CAP-007 | Operar con contratos, gates y pruebas deterministas, portable y configurable por contrato. | MVP-AC-005: tres casos B9 con evidencia de cierre. B1–B2, B9. |

Esta tabla normaliza, sin sustituir, la Definition of Done del Plan 001 §32. El cierre además requiere aprobación de Producto, Sistema y Humano, que un agente no puede emitir.

## Alcance, restricciones y dependencias

Se conserva el fuera de alcance del Plan 001 §31: repositorio nuevo, motor multicanal, SaaS, UI completa, publicación automática, base de datos, analítica avanzada, producción visual, podcast, skills externas, subagentes por defecto, cambio de proveedor como objetivo, MCP obligatorio y fine-tuning.

Post-MVP conocido (§31A): Telegram, voz, aplicación web, múltiples proveedores reales, auditoría cruzada entre modelos, evaluación ciega avanzada, análisis estadístico de estilo, aprendizaje automatizado supervisado, métricas avanzadas de YouTube y experimentación A/B. Esta referencia no autoriza su implementación.

Restricciones: portabilidad, independencia de proveedores, aprobaciones humanas, trazabilidad/versionado/invalidation, ausencia de publicación automática y límites de plataforma/runtime. Dependencias críticas: EditorialProfile, contratos, gates, pruebas, aprobaciones funcionales y validación B9.

## Autoridad, estado y trazabilidad

El Equipo 01 define identidad, audiencia editorial, promesa, voz y perfil; el 02 producto guion; el 03 adaptación a YouTube; el 04 valida técnicamente contratos, pruebas e integración. El propietario y las responsabilidades funcionales aprueban este MVP y cualquier cambio de producto, alcance o aceptación.

Estado: definido mediante esta consolidación; en implementación solo por bloques autorizados; validado tras B9; aceptado solo tras aprobación del propietario. Permanece `DEFINED` tras aprobación expresa del propietario.

Fuentes: Plan 001 v1.4 (§2, §4, §7, §31, §31A, §32), `docs/ALCANCE_Y_COORDINACION_EQUIPOS.md`, B0, B9, B9.5 y especificación B3 del Equipo 01. No hay contradicción material: §31A condensa el mínimo y §32 detalla el cierre. Se registra `NEEDS_PRODUCT_CONFIRMATION` sobre la equivalencia exacta con todos los entregables del plan; no se eliminó ninguno. Pendiente: aprobación del propietario y equipos funcionales de esta consolidación y del límite MVP/futuro.
