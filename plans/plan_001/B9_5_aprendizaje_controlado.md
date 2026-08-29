# PLAN-001 / B9.5 — Aprendizaje editorial controlado

**Plan rector:** [`../001_reestructuracion_motor_agentico_editorial_y_harness.md`](../001_reestructuracion_motor_agentico_editorial_y_harness.md)  
**Control operativo:** [`../001_CONTROL_OPERATIVO.md`](../001_CONTROL_OPERATIVO.md)  
**Versión derivada:** `PLAN-001 v1.4`
**Estado inicial:** `PLANNED`  
**Dependencia activa:** `B9 / núcleo de Guion validado`
**Siguiente tramo:** `B10`  
**Gate resumido:** Ciclo manual de aprendizaje demostrado

> Este archivo es una proyección operativa del Plan 001. No crea autoridad nueva ni sustituye el plan rector. Ante una contradicción, prevalece el plan rector y debe bloquearse la misión hasta resolverla.

## 0. Uso operativo

Lectura mínima para ejecutar una misión de este bloque:

1. `AGENTS.md` del repositorio, si existe.
2. `plans/001_CONTROL_OPERATIVO.md`.
4. Este archivo.
5. La misión concreta y los archivos expresamente autorizados.

No leer por defecto el Plan 001 completo, otros bloques, todo `workspace/` ni reportes históricos. Consultar el plan rector únicamente para resolver una contradicción, una autoridad, una dependencia o una referencia expresa.

### Referencias normativas relacionadas

- B1-C32 a B1-C34
- §7.17 Aprendizaje gobernado
- §8.4 Capa D

---

## 1. Objetivo

Demostrar un ciclo inicial y manual de aprendizaje editorial del Guion sin requerir publicación real. La analítica posterior de distribución queda diferida.

## 2. Misiones

### B9.5-M1 — Aprendizaje editorial de episodios

Recoger observaciones de episodios de validación, correcciones humanas, resultados de benchmarks editoriales e hipótesis sobre tesis, estructura, apertura, redacción, edición y oralidad. Los estados permitidos son `SUPPORTED`, `NOT_SUPPORTED` e `INCONCLUSIVE`, con `EditorialLearningCandidate`, acumulación de evidencia y revisión humana. No requiere publicación real.

### Validación futura de Etapa 2 — Registro de versión publicada (`DEFERRED_NOT_AUTHORIZED`)

Generar `PublishedVersionManifest` para al menos un caso cuando exista publicación real.

Si no existe publicación real autorizada, usar un fixture claramente marcado como:

```text
SYNTHETIC_PUBLICATION_FIXTURE
```

No presentarlo como publicación real.

El manifest debe registrar de forma cronológica cualquier cambio posterior en:

- título;
- miniatura;
- descripción;
- pantallas finales;
- comentario fijado;
- playlist.

Cada cambio debe indicar versión anterior, versión nueva, fecha, razón y ventanas métricas afectadas.

### B9.5-M2 — Captura manual de desempeño (`DEFERRED_NOT_AUTHORIZED`)

Generar `PerformanceSnapshot`.

Toda métrica debe incluir:

* ventana de observación;
* contexto;
* tamaño de muestra;
* limitaciones.

Cada `PerformanceSnapshot` debe identificar las versiones activas de título, miniatura, descripción, pantalla final, comentario fijado y playlist durante la ventana observada.

Una ventana con cambios de versión debe dividirse o marcarse como mezclada e inconclusa para atribución causal.

### B9.5-M3 — Aprendizaje de YouTube gobernado (`DEFERRED_NOT_AUTHORIZED`)

Generar `YouTubeLearningReport`.

Separar:

* hallazgo confirmado;
* hipótesis;
* resultado inconcluso;
* aprendizaje candidato;
* experimento siguiente.

No modificar automáticamente:

* `EditorialProfile`;
* identidad;
* fórmula editorial;
* política de packaging.

### B9.5-M4 — Aprendizaje editorial gobernado

Mover aquí el contenido anteriormente previsto en `B7-M7 — Aprendizaje editorial gobernado`.

El aprendizaje contempla fuentes desde:

- correcciones humanas;
- comparación entre borrador y versión aprobada;
- resultados editoriales de episodios de validación;
- correcciones humanas y comparación entre borrador y versión aprobada;
- resultados de apertura y edición;
- cambios de perfil o nuevas políticas cuando estén aprobados;
- resultados inconclusos.

Las fuentes de publicación, packaging y métricas de YouTube pertenecen al tramo diferido `DEFERRED_NOT_AUTHORIZED`.

Flujo de aprendizaje:

```text
evidencia
→ candidato
→ acumulación
→ revisión humana
→ aprobación
→ nueva versión
```

Prohibido:

- actualizar automáticamente la identidad;
- convertir una sola corrección en regla;
- mezclar hallazgos de plataforma con identidad sin aprobación;
- generalizar desde muestras pequeñas.

Una sola corrección no se convierte en regla estable.

## 3. Gate B9.5

```text
PASS si:
- observaciones y correcciones editoriales están identificadas sin ambigüedad;
- candidatos de aprendizaje tienen evidencia y revisión humana;
- hallazgos e hipótesis están separados;
- ningún aprendizaje modificó el perfil automáticamente;
- existe siguiente experimento o decisión explícita de no experimentar.

El registro publicado, `PerformanceSnapshot` y el aprendizaje de distribución quedan fuera de este gate activo y permanecen `DEFERRED_NOT_AUTHORIZED`.
```

---
