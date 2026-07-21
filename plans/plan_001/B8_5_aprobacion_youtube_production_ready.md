# PLAN-001 / B8.5 — Aprobación para producción y cierre YOUTUBE_PRODUCTION_READY

**Plan rector:** [`../001_reestructuracion_motor_agentico_editorial_y_harness.md`](../001_reestructuracion_motor_agentico_editorial_y_harness.md)  
**Control operativo:** [`../001_CONTROL_OPERATIVO.md`](../001_CONTROL_OPERATIVO.md)  
**Versión derivada:** `PLAN-001 v1.3`  
**Estado inicial:** `PLANNED`  
**Dependencia:** `B8`  
**Siguiente tramo:** `B9`  
**Gate resumido:** Paquete exacto autorizado para producción

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

- B1-C24 HumanProductionApproval
- B1-C24A HumanPublicationApproval
- B1-C31 PublicationPackage
- §10.4 Estados del episodio

---

## 1. Objetivo

Autorizar, solicitar cambios o rechazar el paquete exacto que se pretende llevar a producción audiovisual.

Este bloque no autoriza publicación y no puede declarar `YOUTUBE_READY`.

## 2. Misiones

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

## 3. Gate B8.5

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
