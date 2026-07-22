# PLAN-001 / B7.5 — Adaptación profesional a YouTube

**Plan rector:** [`../001_reestructuracion_motor_agentico_editorial_y_harness.md`](../001_reestructuracion_motor_agentico_editorial_y_harness.md)  
**Control operativo:** [`../001_CONTROL_OPERATIVO.md`](../001_CONTROL_OPERATIVO.md)  
**Versión derivada:** `PLAN-001 v1.4`
**Estado inicial:** `PLANNED`  
**Dependencia:** `B7`  
**Siguiente tramo:** `B8`  
**Gate resumido:** Packaging, correspondencia y continuidad aprobados

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
- B1-C25 PromiseCorrespondenceReport
- B1-C26 YouTubePackagingDecision
- B1-C30 SessionContinuityPlan

---

## 1. Objetivo

Convertir el guion aprobado editorialmente en una propuesta coherente para YouTube sin alterar la tesis ni la identidad del canal.

### 1.1 Interfaz temprana con B5

La audiencia concreta y la `PackagingHypothesis` se originan antes del outline, dentro del flujo de B5, pero son decisiones funcionales del Equipo 03 coordinadas con el Equipo 02.

```text
Equipo 03:
define o aprueba audiencia, promesa visible e hipótesis de packaging.

Equipo 02:
valida que tesis y arquitectura puedan cumplirla.

Equipo 03:
no modifica unilateralmente la tesis.

Equipo 02:
no aprueba unilateralmente el packaging.
```

B7.5 recibe esa hipótesis versionada, comprueba su correspondencia con el guion aprobado y produce la decisión final de packaging.

## 2. Misiones

### B7.5-M1 — Correspondencia de promesa

Generar `PromiseCorrespondenceReport`.

Auditar:

```text
Título
↕
Miniatura
↕
Apertura
↕
Pregunta central
↕
Desarrollo
↕
Conclusión
```

Un incumplimiento grave devuelve el episodio a la fase correspondiente.

### B7.5-M2 — Decisión final de packaging

Rediseñar funcionalmente `skill_packaging.md` para que produzca `YouTubePackagingDecision`.

Debe incluir:

* opción recomendada;
* alternativas;
* opciones descartadas;
* complementariedad título-miniatura;
* evidencia de cumplimiento en el guion;
* riesgo de clickbait;
* riesgo visual y de derechos.

No se implementa todavía la miniatura física.

### B7.5-M3 — Políticas de YouTube versionadas

Apertura, packaging, riesgo publicitario, copyright, contenido sintético, duración, Shorts, metadatos y continuidad pueden estar gobernados por políticas versionadas. Los cambios de YouTube no deben requerir reconstruir el motor editorial. Una OpeningPolicy futura podrá evolucionar independientemente del EditorialProfile. Packaging, apertura y guion deben mantener correspondencia. El Equipo 03 conserva autoridad funcional sobre estas políticas.

No incorporar como verdad permanente afirmaciones no verificadas sobre el algoritmo.

### B7.5-M3A — Adecuación de apertura y duración

Validar:

* confirmación temprana de la promesa;
* ausencia de preámbulo innecesario;
* relevancia para la audiencia concreta;
* densidad inicial;
* duración justificada por el valor y el tipo de pieza.

No imponer una duración universal.

La frontera funcional es:

```text
APERTURA
Equipo 02 → calidad narrativa y argumental.
Equipo 03 → adecuación a la experiencia de YouTube.

DURACIÓN
Equipo 02 → duración necesaria para desarrollar el argumento.
Equipo 03 → adecuación orientativa al consumo en plataforma.
```

### B7.5-M4 — Continuidad de sesión

Generar `SessionContinuityPlan`.

La CTA no es obligatoria si perjudica el cierre. Cuando exista, debe dirigir a un contenido real y coherente.

### B7.5-M5 — Shorts y derivados por función

Rediseñar la capacidad de Shorts para clasificarlos como:

```text
DISCOVERY
BRIDGE_TO_LONGFORM
STANDALONE_IDEA
COMMUNITY_RESPONSE
EMOTIONAL_MOMENT
CURRENT_OPPORTUNITY
CATALOG_RECOVERY
```

Cada derivado debe:

* funcionar con su propio contexto;
* no tergiversar el longform;
* no convertir un tema sensible en shock;
* registrar su relación con el video principal.

### B7.5-M6 — Metadatos y paquete preliminar

Sustituir conceptualmente `SEO YouTube` por:

```text
Metadatos y paquete de publicación
```

Debe preparar:

* título público;
* descripción fiel;
* nombres oficiales de obras;
* entidades;
* atribuciones;
* enlaces;
* comentario fijado;
* playlist;
* video siguiente;
* capítulos provisionales.

Los timestamps finales quedan `BLOCKED` hasta existir edición audiovisual real.

## 3. Gate B7.5

```text
PASS si:
- la audiencia concreta deriva del EditorialProfile aprobado;
- PackagingHypothesis tiene aprobación funcional del Equipo 03;
- Producto Guion validó que el guion puede cumplir la promesa;
- existe correspondencia verificable entre promesa y contenido;
- packaging recomendado no es engañoso;
- apertura confirma la expectativa;
- duración está justificada;
- las políticas de YouTube aplicables están versionadas;
- continuidad está definida o su ausencia justificada;
- derivados tienen función explícita;
- metadatos son correctos;
- ningún cambio altera el guion aprobado sin invalidarlo.
```

---
