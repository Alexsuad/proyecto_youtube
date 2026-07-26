# PLAN-001 / B10 — Lean/5S, portabilidad, documentación y cierre

**Plan rector:** [`../001_reestructuracion_motor_agentico_editorial_y_harness.md`](../001_reestructuracion_motor_agentico_editorial_y_harness.md)  
**Control operativo:** [`../001_CONTROL_OPERATIVO.md`](../001_CONTROL_OPERATIVO.md)  
**Versión derivada:** `PLAN-001 v1.4`
**Estado inicial:** `PLANNED`  
**Dependencia activa:** `B9` completado para el núcleo de Guion + aprendizaje editorial aplicable de `B9.5`
**Siguiente tramo:** `Cierre del Plan 001`  
**Gate resumido:** Plan cerrado con evidencia

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

- §27 Dependencias
- §28 Política de implementación
- §29–§32 control, riesgos y DoD

---

## 1. Objetivo

Reducir duplicación y contradicciones sin borrar evidencia ni romper compatibilidad, cerrando Lean/5S, portabilidad y deuda técnica de la Etapa 1 sin depender de publicación, analítica de YouTube, Audio o Video. La Etapa 2 tendrá un cierre posterior cuando sea autorizada.

## 2. Misiones

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
- implementar MCP estable de NotebookLM;
- soportar otros canales;
- añadir UI;
- añadir base de datos;
- automatizar publicación;
- integrar analítica automática;
- automatizar experimentos;
- extender a podcast.

## 3. Gate B10

```text
PLAN_STATUS: PASS_FOR_SCRIPT_CORE
SYSTEM_REVIEW: PASS
PRODUCT_REVIEW: PASS
EDITORIAL_SCRIPT_APPROVAL: PASS
CLOSURE_STATE: EDITORIAL_SCRIPT_APPROVED
STAGE_2_CLOSURE: DEFERRED_NOT_AUTHORIZED
```

---
