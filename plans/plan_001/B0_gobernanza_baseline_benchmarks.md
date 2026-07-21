# PLAN-001 / B0 — Gobernanza, baseline y benchmarks editoriales

**Plan rector:** [`../001_reestructuracion_motor_agentico_editorial_y_harness.md`](../001_reestructuracion_motor_agentico_editorial_y_harness.md)  
**Control operativo:** [`../001_CONTROL_OPERATIVO.md`](../001_CONTROL_OPERATIVO.md)  
**Versión derivada:** `PLAN-001 v1.3`  
**Estado inicial:** `PLANNED`  
**Dependencia:** `Ninguna`  
**Siguiente tramo:** `B1`  
**Gate resumido:** Baseline y benchmarks aprobados

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

- §5 Baseline verificable
- §7 Principios no negociables
- §28 Política de implementación por misiones

---

## 1. Objetivo

Congelar el comportamiento actual, reproducir los fallos conocidos, crear el sistema de seguimiento y establecer referencias de calidad antes de modificar el motor.

## 2. Misiones

### B0-M1 — Incorporar el plan y su seguimiento

**Acciones:**

- crear `plans/` si no existe;
- incorporar este Plan 001 v1.3;
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

## 3. Archivos propuestos

```text
plans/001_reestructuracion_motor_agentico_editorial_y_harness.md
plans/plan_001/README.md
reports/implementation/plan_001/B0_baseline/
tests/characterization/
benchmarks/editorial/
docs/evaluation/editorial_rubric.md
```

## 4. Gate B0

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
