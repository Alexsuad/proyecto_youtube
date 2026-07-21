# PLAN-001 / B8 — Plataforma, monetización, copyright y paquete para producción

**Plan rector:** [`../001_reestructuracion_motor_agentico_editorial_y_harness.md`](../001_reestructuracion_motor_agentico_editorial_y_harness.md)  
**Control operativo:** [`../001_CONTROL_OPERATIVO.md`](../001_CONTROL_OPERATIVO.md)  
**Versión derivada:** `PLAN-001 v1.3`  
**Estado inicial:** `PLANNED`  
**Dependencia:** `B7.5`  
**Siguiente tramo:** `B8.5`  
**Gate resumido:** Paquete completo evaluado y compilado

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

- §8.4 Capa D
- B1-C27 a B1-C31
- §7.13 No degradar contenido para superar validadores

---

## 1. Objetivo

Evaluar separadamente los riesgos de plataforma, monetización, copyright, Content ID, contenido reutilizado y producción audiovisual antes de compilar el paquete exacto que podrá someterse a aprobación para producción.

## 2. Misiones

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

## 3. Gate B8

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
