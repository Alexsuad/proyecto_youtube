# PLAN-001 / B10 — Lean/5S, portabilidad, documentación y cierre

**Plan rector:** [`../001_reestructuracion_motor_agentico_editorial_y_harness.md`](../001_reestructuracion_motor_agentico_editorial_y_harness.md)  
**Control operativo:** [`../001_CONTROL_OPERATIVO.md`](../001_CONTROL_OPERATIVO.md)  
**Versión derivada:** `PLAN-001 v1.3`  
**Estado inicial:** `PLANNED`  
**Dependencia:** `B9.5`  
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

Reducir duplicación y contradicciones sin borrar evidencia ni romper compatibilidad, cerrando formalmente el plan y determinando el camino de portabilidad y evoluciones futuras.

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

1. Ejecutar suite completa.
2. Ejecutar auditoría de arquitectura.
3. Ejecutar auditoría editorial externa.
4. Ejecutar auditoría de Adaptación a YouTube.
5. Revisar seguridad, rutas y configuración.
6. Actualizar README y mapa de arquitectura.
7. Marcar documentos sustituidos.
8. Consolidar changelog.
9. Etiquetar versión estable.
10. Registrar deudas no bloqueantes.
11. Comparar resultados contra benchmarks.
12. Documentar si las capacidades generalizables son realmente extraíbles.

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
PLAN_STATUS: PASS
SYSTEM_REVIEW: PASS
PRODUCT_REVIEW: PASS
YOUTUBE_ADAPTATION_REVIEW: PASS
PLATFORM_AND_RIGHTS_REVIEW: PASS
HUMAN_PRODUCTION_APPROVAL: APPROVED_FOR_PRODUCTION
CLOSURE_STATE: YOUTUBE_PRODUCTION_READY
```

---
