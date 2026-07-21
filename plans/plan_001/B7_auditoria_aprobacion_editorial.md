# PLAN-001 / B7 — Auditoría independiente, correcciones y aprobación editorial

**Plan rector:** [`../001_reestructuracion_motor_agentico_editorial_y_harness.md`](../001_reestructuracion_motor_agentico_editorial_y_harness.md)  
**Control operativo:** [`../001_CONTROL_OPERATIVO.md`](../001_CONTROL_OPERATIVO.md)  
**Versión derivada:** `PLAN-001 v1.3`  
**Estado inicial:** `PLANNED`  
**Dependencia:** `B6`  
**Siguiente tramo:** `B7.5`  
**Gate resumido:** Guion aprobado editorialmente

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

- §7.5 Separación producción–edición–auditoría
- B1-C10 CorrectionRoutingPolicy
- B1-C23 EditorialScriptApproval

---

## 1. Objetivo

Evaluar el candidato final sin mezclar edición y aprobación, enrutar correctamente los defectos y obtener la aprobación editorial de una versión exacta del guion antes de pasar a Adaptación a YouTube.

## 2. Misiones

### B7-M1 — Auditoría editorial final independiente

El auditor:

- recibe la versión editada;
- trabaja en contexto limpio;
- no modifica el guion;
- evalúa perfil, brief, promesa, evidencia, tesis, recorrido, apertura, progresión, originalidad, oralidad y cierre;
- emite `PASS`, `WARN`, `FAIL` o `BLOCKED`;
- identifica ruta de corrección.

### B7-M2 — Enrutamiento de correcciones

Aplicar `CorrectionRoutingPolicy`.

No se parchea texto final cuando el defecto pertenece a investigación, tesis, promesa o arquitectura.

### B7-M3 — Invalidación y revalidación

Registrar:

- artefactos invalidados;
- nueva versión;
- gates que deben repetirse;
- estado de retorno;
- evidencia de corrección.

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
approved_at
notes
```

Esta decisión se registra mediante `EditorialScriptApproval`. No autoriza producción audiovisual ni publicación y no permite declarar `YOUTUBE_PRODUCTION_READY` ni `YOUTUBE_READY`.

Decisiones:

```text
APPROVE
REQUEST_CHANGES
REJECT
```

Solo `APPROVE` permite iniciar B7.5. No permite todavía declarar `YOUTUBE_PRODUCTION_READY` ni `YOUTUBE_READY`.

## 3. Gate B7

```text
PASS si:
- auditoría editorial final fue independiente;
- defectos se enrutaron a la fase correcta;
- no se superó el máximo de ciclos sin decisión humana;
- EditorialScriptApproval referencia versión y checksum;
- no existen cambios posteriores sin invalidación;
- el guion está autorizado para entrar en Adaptación a YouTube.
```

---
