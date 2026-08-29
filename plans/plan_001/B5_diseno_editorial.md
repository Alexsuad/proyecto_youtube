# PLAN-001 / B5 — Profesionalización del diseño editorial

**Plan rector:** [`../001_reestructuracion_motor_agentico_editorial_y_harness.md`](../001_reestructuracion_motor_agentico_editorial_y_harness.md)  
**Control operativo:** [`../001_CONTROL_OPERATIVO.md`](../001_CONTROL_OPERATIVO.md)  
**Versión derivada:** `PLAN-001 v1.4`
**Estado inicial:** `PLANNED`  
**Dependencia:** `B3–B4`  
**Siguiente tramo:** `B5.5`  
**Gate resumido:** Diseño editorial completo aprobado

> Este archivo es una proyección operativa del Plan 001. No crea autoridad nueva ni sustituye el plan rector. Ante una contradicción, prevalece el plan rector y debe bloquearse la misión hasta resolverla.

## R1. Estado reconciliado

``text
STATUS_RECONCILED: PASS
FINAL_CLOSURE_STATUS: OPEN
EVIDENCE_REFS: Ver control operativo y contratos actuales
```

## 0. Uso operativo

Lectura mínima para ejecutar una misión de este bloque:

1. `AGENTS.md` del repositorio, si existe.
2. `plans/001_CONTROL_OPERATIVO.md`.
4. Este archivo.
5. La misión concreta y los archivos expresamente autorizados.

No leer por defecto el Plan 001 completo, otros bloques, todo `workspace/` ni reportes históricos. Consultar el plan rector únicamente para resolver una contradicción, una autoridad, una dependencia o una referencia expresa.

### Referencias normativas relacionadas

- §2 Resultado editorial esperado
- §3 Flujo objetivo
- Contratos B1-C2 a B1-C8

---

## 1. Objetivo

Convertir brief, investigación, evidencia, tesis, curación, promesa editorial del guion, recorrido y outline en un diseño profesional antes de redactar.

## 2. Misiones

La secuencia funcional se mantiene separada de la numeración histórica de las misiones: `B5-M8` diseña el recorrido del espectador; después `B5-M11` consolida la arquitectura narrativa global, incluyendo el cierre cuando corresponda; `B5-M9` desarrolla la apertura específica; y `B5-M12` detalla y audita el outline. No se renumeran IDs ni se crean agentes o estados por cada paso.

### B5-M1 — Brief unificado y tipo de guion

Unificar skill, template y QA.

Debe decidir:

- pregunta central;
- conflicto;
- transformación;
- ángulo;
- alcance;
- tipo principal y secundario;
- estructura candidata;
- duración;
- política de citas y fuentes.

La estructura se elige por adecuación, no por costumbre.

### B5-M2 — Investigación por cobertura

La investigación debe distinguir:

```text
hechos
interpretaciones
hipótesis
contradicciones
límites
escenas o evidencia concreta
perspectivas alternativas
claims utilizables
claims no sostenibles
oportunidades narrativas
```
No se mide calidad por número bruto de URLs.

### B5-M3 — Acceso y suficiencia de evidencia

Producir `SourceAccessAndEvidenceReport` y ejecutar el gate.

Debe impedir:

- fingir haber visto una obra;
- atribuir escenas no verificadas;
- confundir adaptación y obra original;
- presentar interpretación como hecho;
- escribir análisis fuerte con material insuficiente.

### B5-M4 — Tesis provisional

Debe existir antes de curar y puede cambiar con la investigación.

Incluye:

- hipótesis inicial;
- objeción prevista;
- riesgo de simplificación;
- preguntas abiertas.

### B5-M5 — Análisis narrativo y humano y curación final por función

Después de la tesis provisional se realiza una preselección de materiales.

Antes de cerrar la selección definitiva, cada material preseleccionado debe analizarse narrativamente y humanamente con evidencia suficiente.

El análisis debe responder, cuando aplique:

- qué desea el personaje o sujeto;
- qué teme perder;
- qué evita;
- qué cree sobre sí mismo y sobre el mundo;
- qué contradicción existe entre lo que declara y lo que hace;
- qué decisión revela el patrón central;
- qué coste produce esa decisión;
- qué cambia y qué permanece;
- qué papel desempeña el entorno;
- qué escena o comportamiento sostiene la lectura;
- qué lectura alternativa existe;
- qué parte es hecho narrativo, interpretación o hipótesis;
- qué límites tiene la analogía con la vida real;
- qué aporta el material que no aporta otro;
- cómo sostiene, tensiona, matiza o contradice la tesis.

Después del análisis, la curación final debe justificar por cada material:

- función;
- perspectiva;
- orden;
- novedad;
- evidencia;
- coste de contexto;
- riesgo de repetición;
- contribución única;
- relación con la tesis;
- aporte al clímax.

La fórmula habitual del canal se mantiene como preferencia fuerte, no obligación universal.

No se aprueba una selección basada únicamente en afinidad temática.

### B5-M6 — Audiencia concreta y promesa editorial del guion

Antes del outline debe existir una audiencia concreta del episodio derivada del `EditorialProfile` aprobado.

Debe definir:

- qué persona concreta se busca alcanzar;
- promesa editorial necesaria para escribir el guion;
- tensión central;
- expectativas legítimas;
- expectativas que deben evitarse;
- alineación con la tesis refinada;
- riesgo textual de sobrepromesa y su mitigación, si aplica;
- obligaciones de apertura;
- restricciones heredadas de B5-I1.

Esta promesa no produce ni exige título, miniatura, promesa de clic, complementariedad título-miniatura, Shorts, SEO ni aprobación de packaging. El packaging permanece diferido a B7.5.

Un cambio sustancial en audiencia, promesa editorial, tesis o tensión central invalida los artefactos dependientes.

### B5-M7 — Tesis refinada

Después de evidencia, análisis narrativo y humano, curación final y promesa editorial temprana del guion:

- tesis defendible;
- matiz;
- objeción principal;
- idea que no debe simplificarse;
- transformación final;
- relación con promesa.

### B5-M8 — Recorrido del espectador

Planificar el cambio de conocimiento, emoción y pregunta en cada bloque.

No se usa para fabricar retención artificial, sino para comprobar avance real.

### B5-M9 — OPENING_UNIT y diseño de apertura

La apertura se trata como unidad prioritaria con diseño propio. OpeningDesign actúa como antecedente o parte de OPENING_UNIT con funciones obligatorias, no duración rígida.

Debe cumplir:

- confirmación del clic;
- tensión;
- sustancia temprana;
- contexto mínimo;
- promesa del recorrido;
- transición al primer bloque;
- contribución autoral.

Además debe revisar:

- punto de máximo interés;
- pregunta central;
- contexto mínimo;
- promesa concreta;
- sustancia en el primer minuto;
- ausencia de introducción larga;
- suspensión no artificial;
- primera transición.

No exigir siempre exactamente 90 segundos. La estructura narrativa puede variar; el diseño debe compararse contra patrones repetidos para evitar aperturas mecánicas.

### B5-M10 — Diseño de cierre

Debe:

- responder la pregunta central;
- demostrar la tesis;
- transformar o recuperar la apertura;
- no introducir tesis nueva;
- evitar moraleja genérica;
- cerrar con idea o imagen memorable;
- integrar CTA solo si mejora el cierre.

### B5-M11 — Arquitectura y presupuesto

Por cada bloque:

```text
pregunta que abre
información nueva
cambio del espectador
función narrativa
tensión
promesa parcial
pregunta abierta
transición
presupuesto
fuentes
no repetir
```
### B5-M12 — Auditoría de outline

Debe comprobar:

- progresión;
- causalidad;
- contraste;
- acumulación;
- ritmo;
- clímax;
- cierre;
- cumplimiento de promesa;
- coherencia con tipo de guion;
- fidelidad al canal.

## 3. Gate B5

```text
PASS si:
- brief y tipo de guion están aprobados;
- evidencia permite continuar;
- tesis provisional y refinada son trazables;
- existe análisis narrativo y humano suficiente por cada material seleccionado;
- hechos narrativos, interpretaciones e hipótesis están diferenciados;
- los límites de las analogías con la vida real están declarados;
- curación asigna funciones y contribuciones distintas;
- EditorialScriptPromise conserva audiencia, tesis, restricciones y riesgo textual de sobrepromesa;
- Producto Guion confirmó que la tesis y la arquitectura pueden cumplir la promesa;
- ViewerJourney muestra transformación;
- apertura (OPENING_UNIT) y cierre tienen contrato;
- la apertura cumple funciones obligatorias sin duración rígida;
- outline y presupuesto están aprobados;
- Producto considera que el diseño puede producir un buen guion.
```

---

## 4. Relación con la planeación previa al guion (B5_PRE)

B5 (este diseño editorial) se apoya en la planeación previa al guion consolidada en:

- [`B5_PRE_SCRIPT_FOUNDATION.md`](B5_PRE_SCRIPT_FOUNDATION.md) — plan canónico de la fase previa.
- `policies/script_product/main_episode_format_policy.md` — regla de obras del formato principal.
- `policies/script_product/episode_discovery_and_material_curation_policy.md` — descubrimiento, investigación, verificación, análisis y curación.
- `policies/channel_intelligence/topic_belonging_policy.md` — criterio funcional de pertenencia.

B5 reconoce y asume como fundamento previo:

- **B5_PRE** como base de la fase previa al guion;
- **cinco a ocho obras candidatas** como rango normal;
- **tres a cinco obras finales** como requisito del formato principal;
- **análisis antes de curación** (la curación final no puede preceder al análisis sustantivo);
- **especialistas adaptativos** (capacidad configurable, sin agente permanente por disciplina);
- **verificación de obras** (acceso directo vs. indirecto; no fingir visionado);
- **tres modalidades de entrada** (`TOPIC_FIRST`, `ANCHOR_WORK_FIRST`, `CORPUS_FIRST`);
- **separación respecto de B5-I3 y B5.5**: esta fase previa no diseña outline, arquitectura, apertura ni guion (eso pertenece a B5/B5.5 en adelante).

Ninguna regla activa de este bloque contradice las reglas de la fase previa; si apareciera una contradicción, prevalece la política canónica de formato y debe bloquearse la misión hasta resolverla.

---
