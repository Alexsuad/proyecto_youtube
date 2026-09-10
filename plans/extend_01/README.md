# EXTEND-01 — Research V2 REAL E2E

## 1. Qué es

EXTEND-01 es la primera iniciativa del roadmap posterior a PLAN012 que continúa dentro del MVP y de la demostración del producto. No pertenece a PLAN011, no reabre PLAN012 y no crea un plan paralelo.

La ubicación conceptual es:

```text
PLAN-001
→ PLAN012 cerrado
→ roadmap MVP post-PLAN012
→ EXTEND-01
```

Este README es una proyección operativa breve para localizar propósito, horizonte y estado. No sustituye contratos, misiones ni gates.

## 2. Origen y autoridad

EXTEND-01 tiene como origen documental:

- la decisión final del OWNER sobre el cierre de P7 y la portabilidad cognitiva;
- el consolidado final y plan de cambio/no cambio;
- el handoff de Equipo 04 posterior a M4/PLAN012;
- la carpeta externa de reconciliación de investigación web.

Localización de la reconciliación externa:

`G:\Mi unidad\Proyecto YouTube\RECONCILIACION_INVESTIGACION_WEB_2026-09-04`

Drive:

<https://drive.google.com/drive/folders/1dO42ptSTe21TwAOvbS_Dcc8KW-RGoiBF?usp=drive_link>

Documentos de origen principales:

- `10_DECISION_OWNER_CIERRE_P7_PORTABILIDAD_COGNITIVA_2026-09-04`;
- `11_HANDOFF_EQUIPO04_POST_M4_PLAN012_IMPLEMENTACION_MVP_2026-09-04`;
- `09_CONSOLIDADO_FINAL_Y_PLAN_2026-09-04`, cuando sea necesario confirmar secuencia, horizonte o alcance.

La documentación externa fija origen, intención y roadmap. No sobrescribe estados posteriores del repositorio.

Para el estado operativo vivo, la autoridad exclusiva es:

`plans/001_CONTROL_OPERATIVO.md`

## 3. Horizonte

```text
MVP_POST_PLAN012
```

EXTEND-01 todavía forma parte del MVP y de la demostración del producto. No es POST-MVP / Etapa 2.

La portabilidad cognitiva completa, el ciclo YouTube completo, Analytics, publicación y aprendizaje histórico permanecen fuera del alcance actual conforme a las autoridades vigentes.

## 4. Objetivo

Demostrar una operación REAL de Research V2 de extremo a extremo hasta:

```text
RESEARCH_READY
```

La demostración debe reutilizar la arquitectura existente y preservar la frontera:

```text
SOFTWARE → IA → SOFTWARE
```

Una demostración técnica no equivale por sí sola a calidad de investigación demostrada ni a autorización de uso productivo.

## 5. Qué debe demostrar EXTEND-01

De forma integrada y trazable, EXTEND-01 debe demostrar, cuando corresponda al caso:

- entrada real;
- ResearchPlan;
- ejecución Research V2;
- adquisición, búsqueda o fetch real;
- evidencia real;
- persistencia;
- lineage;
- provenance;
- recovery;
- frontera REAL/MOCK fail-closed;
- llegada real a `RESEARCH_READY`;
- controles mínimos de la primera corrida REAL: presupuesto explícito, límite anti-loop/iteraciones, provenance y telemetría mínima.

Esta lista orienta el objetivo y no crea una especificación paralela. Deben reutilizarse y extenderse los contratos, gates, persistencia y bindings existentes.

## 6. Orden autorizado del roadmap

```text
PLAN012
→ EXTEND-01
→ EXTEND-03
→ EXTEND-02
→ EXPERIMENT-01
→ EXTEND-04, solo si el caso requiere audiovisual
→ EXPERIMENT-02, cuando se cumplan sus dependencias
```

La secuencia no autoriza ejecución simultánea ni activa una misión por inferencia. Cada paso conserva sus dependencias, gates y autoridad funcional.

## 7. Estado actual de EXTEND-01

El estado se reconstruye desde `plans/001_CONTROL_OPERATIVO.md`, no desde esta proyección histórica. En la última lectura vigente:

- M1: cerrado técnicamente;
- M2-B1: completado técnicamente;
- M2-B2: completado técnicamente;
- M2-B3: completado técnicamente;
- adaptadores de stages REAL: enlazados;
- entrada REAL: disponible, pero no operacional;
- ejecución REAL E2E: no realizada;
- llamadas IA REAL: `0`;
- uso productivo autorizado: `NO`.

El cierre publicado de B3/R1 permanece en:

`2931e44 feat(extend01): completar binding técnico M2 B3`

Siguiente acción viva, sin ampliar su alcance desde este README:

`NEXT_ALLOWED_ACTION: PREPARE_M2_B4_AUTHORIZED_REAL_RUN`

## 8. Aclaración sobre “M2-B4”

`M2-B4` es una subdivisión operativa interna de `EXTEND-01/M2`.

No es:

```text
PLAN-001 / B4
```

PLAN-001/B4 y M2-B4 son elementos distintos. Si el control operativo mantiene `NEXT_ALLOWED_ACTION: PREPARE_M2_B4_AUTHORIZED_REAL_RUN`, esa cadena se registra únicamente como siguiente acción vigente; no autoriza aquí una corrida REAL ni inventa el alcance de B4.

## 9. Frontera sobre proveedor, modelo y runtime

EXTEND-01 no convierte Proyecto YouTube en un gestor de proveedores o modelos.

- La lógica funcional no queda acoplada a OpenAI, DeepSeek, Codex, OpenCode ni a otra marca.
- Una corrida concreta puede utilizar una capacidad cognitiva elegida manualmente por el OWNER.
- El provider, modelo y runtime usados en una corrida REAL pueden quedar identificados en provenance.
- Esa identificación no implica construir dentro del MVP un selector automático, router, gateway o sistema multi-provider completo.

Debe distinguirse siempre entre:

```text
elección externa/manual para ejecutar una prueba concreta
```

y:

```text
gestión de proveedores/modelos como capacidad del producto
```

La segunda pertenece principalmente a POST-MVP. Para la primera corrida REAL, una selección manual y explícitamente autorizada es válida; no demuestra portabilidad multi-provider.

## 10. Fuera de alcance de EXTEND-01

Esta documentación no introduce como parte de EXTEND-01:

- multi-provider completo;
- multi-modelo completo;
- BYOK;
- gateway propio;
- routing automático;
- selector automático de modelos;
- perfiles comerciales de inferencia;
- Analytics;
- publicación completa;
- aprendizaje histórico.

## 11. Regla de continuidad

Ante dudas sobre EXTEND-01:

1. consultar este README para ubicación y propósito;
2. consultar `plans/001_CONTROL_OPERATIVO.md` para el estado vivo;
3. consultar las fuentes P7/Equipo 04 para autoridad y decisiones originales;
4. no reconstruir la intención desde memoria de chats.

Este archivo no crea un nuevo PLAN, no modifica PLAN011 ni PLAN012, no autoriza B4, no cambia el estado de M2/B4 y no sustituye ninguna autoridad canónica.
