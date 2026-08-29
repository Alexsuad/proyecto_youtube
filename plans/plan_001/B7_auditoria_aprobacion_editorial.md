# PLAN-001 / B7 — Auditoría independiente, correcciones y aprobación editorial

**Plan rector:** [`../001_reestructuracion_motor_agentico_editorial_y_harness.md`](../001_reestructuracion_motor_agentico_editorial_y_harness.md)  
**Control operativo:** [`../001_CONTROL_OPERATIVO.md`](../001_CONTROL_OPERATIVO.md)  
**Versión derivada:** `PLAN-001 v1.4`
**Estado inicial:** `PLANNED`  
**Dependencia:** `B6`  
**Siguiente tramo:** `B7.5`  
**Gate resumido:** Guion aprobado editorialmente

> Este archivo es una proyección operativa del Plan 001. No crea autoridad nueva ni sustituye el plan rector. Ante una contradicción, prevalece el plan rector y debe bloquearse la misión hasta resolverla.

## Prerrequisitos antes de activar B7

Antes de activar este bloque deberá verificarse que ningún consumidor reintroduce 80/20 cuantitativo, re-hooks periódicos obligatorios, resets por cronómetro, tres eventos obligatorios, timeline universal 15–25, “segundo mejor primero”, CTA obligatorio o la estructura universal Hook → Intro → Evento 1 → Evento 2 → Evento 3 → Clímax → CTA. La auditoría deberá revisar función narrativa, progresión, renovación atencional, ritmo no mecánico y función argumentativa, sin convertir estas dimensiones en una cuota nueva.

También deberá estar integrada la política de spoilers por necesidad editorial, mínimo detalle necesario, nivel declarado, warning proporcional y aviso previo a revelaciones materiales inesperadas. B7 no queda activado por este registro.

## 0. Uso operativo

Lectura mínima para ejecutar una misión de este bloque:

1. `AGENTS.md` del repositorio, si existe.
2. `plans/001_CONTROL_OPERATIVO.md`.
4. Este archivo.
5. La misión concreta y los archivos expresamente autorizados.

No leer por defecto el Plan 001 completo, otros bloques, todo `workspace/` ni reportes históricos. Consultar el plan rector únicamente para resolver una contradicción, una autoridad, una dependencia o una referencia expresa.

### Referencias normativas relacionadas

- §7.5 Separación producción–edición–auditoría
- B1-C10 CorrectionRoutingPolicy
- B1-C23 EditorialScriptApproval

---

## 1. Objetivo

Cerrar de forma integrada el candidato final del guion sin mezclar producción y auditoría: ejecutar las validaciones obligatorias independientes, enrutar correctamente los defectos, revalidar las versiones corregidas y obtener la aprobación editorial humana de una versión exacta. La adecuación textual a YouTube participa en este cierre; packaging final y producción permanecen fuera del MVP.

## 2. Misiones

### B7-M1 — Validaciones obligatorias separadas

El candidato final debe recibir, como mínimo, estas validaciones independientes, sin convertirlas en cuatro agentes ni en cuatro estados runtime:

- `SCRIPT_PRODUCT`: calidad editorial, estructura, progresión, tesis, escritura, edición, oralidad y cumplimiento del brief;
- `CHANNEL_INTELLIGENCE`: coherencia con el `EditorialProfile`, propósito, posicionamiento, audiencia, promesa, voz, persona autoral y ausencia de deriva material;
- responsabilidades existentes de investigación/evidencia y auditoría editorial: claims, soporte, interpretación, fidelidad, sobreinterpretación y contradicciones materiales;
- `YOUTUBE_ADAPTATION`: adecuación textual del guion a audiencia, promesa, apertura, duración orientativa, sobrepromesa y riesgos de plataforma, copyright o reutilización originados en el texto.

El redactor no debe autoaprobarse como único auditor. Las auditorías avanzadas adicionales son opcionales y no crean requisitos nuevos del MVP.

### B7-M1A — Auditoría final independiente

El auditor:

- recibe la versión editada;
- trabaja en contexto limpio;
- no modifica el guion;
- emite únicamente su propia auditoría editorial dentro de su autoridad; las demás autoridades funcionales emiten sus propias validaciones, y B7 reúne esas evidencias separadas, todas sobre la misma versión y checksum, antes de `EDITORIAL_SCRIPT_APPROVED`;
- emite `PASS`, `WARN`, `FAIL` o `BLOCKED`;
- identifica ruta de corrección.

Una validación no aprobada no se oculta con otra aprobación: produce hallazgo, ruta de corrección y revalidación.

### B7-M2 — Enrutamiento de correcciones

Aplicar `CorrectionRoutingPolicy`.

El auditor detecta y enruta; la responsabilidad productora corrige. No se parchea silenciosamente el texto final cuando el defecto pertenece a investigación, evidencia, tesis, promesa, recorrido o arquitectura.

### B7-M3 — Invalidación y revalidación

Registrar:

- artefactos invalidados;
- nueva versión;
- gates que deben repetirse;
- estado de retorno;
- evidencia de corrección.

Una corrección que cambie el candidato invalida las aprobaciones de la versión anterior para el cierre. Todas las validaciones obligatorias deben repetirse sobre la versión exacta nueva.

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
approved_role
approved_at
notes
```

Esta decisión se registra mediante `EditorialScriptApproval`. Para cerrar el MVP, la decisión `APPROVED` de este contrato es la decisión editorial aplicable a `EDITORIAL_SCRIPT_APPROVED`; `APPROVED_FOR_PRODUCTION` pertenece a `HumanProductionApproval` y al cierre posterior de B8.5, no al cierre editorial del MVP. Es la aprobación editorial humana de una versión exacta; no equivale a aprobación de producción, publicación, `YOUTUBE_PRODUCTION_READY` ni `YOUTUBE_READY`. El requisito de consolidar todas las evidencias obligatorias sobre esa versión está definido funcionalmente, pero su implementación debe comprobarse contra B1 y el código.

Decisiones:

```text
APPROVED
REQUEST_CHANGES
REJECT
```

Solo `APPROVED`, con todas las validaciones obligatorias vigentes sobre el mismo checksum, permite pasar a etapas posteriores. No permite todavía declarar `YOUTUBE_PRODUCTION_READY` ni `YOUTUBE_READY`.

## 3. Gate B7

```text
PASS si:
- las validaciones obligatorias fueron independientes y están aprobadas sobre el mismo `artifact_id`, versión y checksum;
- defectos se enrutaron a la fase correcta;
- las correcciones generaron invalidación y revalidación de la versión actual;
- no se superó el máximo de ciclos sin decisión humana;
- EditorialScriptApproval referencia versión y checksum;
- no existen cambios posteriores sin invalidación;
- el guion queda cerrado editorialmente en `EDITORIAL_SCRIPT_APPROVED` y puede continuar a etapas posteriores autorizadas.
```
El gate consume evidencias separadas de cada dominio obligatorio y las reúne solo para el cierre de una versión exacta. Sus etiquetas documentales no crean estados, enums ni contratos nuevos del runtime.

---
