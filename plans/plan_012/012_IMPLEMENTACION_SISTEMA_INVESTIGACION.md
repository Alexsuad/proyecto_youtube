# PLAN 012 — Implementación del Sistema de Investigación V2

**Estado:** `B1_CLOSED`
**Versión del roadmap:** `1.3`
**Fecha de revisión:** `2026-09-03`
**Ownership funcional del producto de investigación:** `SCRIPT_PRODUCT / Equipo 02`
**Autoridad especializada/delegada sobre metodología de investigación:** especialista independiente de investigación validado por OWNER
**Autoridad técnica:** `INFRASTRUCTURE_GOVERNANCE / Equipo 04`
**Autoridad final:** `OWNER`

---

## 0. Propósito

Materializar la Guía del Sistema de Investigación V2 dentro de la arquitectura existente del Proyecto YouTube sin crear un segundo sistema, sin reabrir PLAN011 y sin trasladar decisiones deterministas a IA.

PLAN012 debe convertir la vertical de investigación en una cadena técnicamente integrada, persistente, recuperable, trazable y auditable que determine:

- qué debemos investigar;
- qué sabemos y con qué evidencia;
- qué no sabemos;
- qué contradicciones o explicaciones rivales permanecen;
- qué obras son defendibles para el uso previsto;
- qué claims son permitidos, matizables, inciertos o no permitidos;
- qué claims materiales sobre el fenómeno real necesitan profundización adicional y con qué carga probatoria;
- si el conjunto de obras sigue siendo complementario y defendible después de investigarlo profundamente;
- qué tesis sustantiva puede defenderse;
- qué limitaciones y restricciones debe respetar downstream.

La investigación termina en un handoff explícito `RESEARCH_READY` hacia B5-I3. No diseña el video.

Este plan **no autoriza implementación por sí mismo**. Cada bloque requiere misión técnica explícita y autoridad viva materializada antes de modificar código ejecutable.

La versión 1.3 conserva íntegramente la versión 1.2 ya aprobada funcionalmente por Equipo 02 y el especialista de Investigación, y añade seis ajustes exclusivamente técnicos derivados de auditoría externa de software/arquitectura agéntica: frontera formal de adquisición de evidencia, guard operacional anti-loop/no-progress, paralelismo conceptual sin concurrencia obligatoria, modelo de estados ortogonales, compatibilidad contractual explícita con M3/B5-I3 y mapa previo de responsabilidades cognitivas. Estos ajustes no reabren la metodología de investigación.

---

# 1. Principio rector: SOFTWARE → IA → SOFTWARE

La arquitectura obligatoria es:

```text
USUARIO / INPUT
      ↓
SOFTWARE
  normaliza input
  prepara contexto y contratos
  asigna IDs/versiones/bindings
  valida precondiciones y rutas
      ↓
IA
  realiza SOLO trabajo cognitivo autorizado
      ↓
SOFTWARE
  valida el output
  rechaza metadata técnica inventada
  bindea referencias reales
  persiste/versiona
  calcula estados y retornos
  decide routing determinista
      ↓
HUMANO
  solo cuando exista decisión reservada,
  delegación o ambigüedad material
```

PLAN012 prohíbe convertir el pipeline en:

```text
IA → IA → IA → IA → IA
```

sin contratos, persistencia, validación, lineage y control determinista entre etapas.

## 1.1 Patrón operativo repetible

Cuando la investigación necesite varias decisiones cognitivas encadenadas, el patrón debe conservar control del software entre ellas:

```text
SOFTWARE
prepara pregunta / gap / scope / contexto
        ↓
IA
identifica qué debe conocerse o evaluarse
        ↓
SOFTWARE
realiza o enruta recuperación/búsqueda/fetch
registra evidencia real y provenance
        ↓
IA
evalúa evidencia y límites
        ↓
SOFTWARE
valida estructura
bindea referencias
persiste
actualiza estado
        ↓
IA
decide suficiencia / gap / rival / contradicción
        ↓
SOFTWARE
ruta la siguiente acción
```

Puede repetirse:

```text
SOFTWARE → IA → SOFTWARE → IA → SOFTWARE
```

pero no debe existir una cadena autónoma de IA sin control de estado y evidencia entre responsabilidades.

## 1.2 Frontera formal de adquisición de evidencia

Toda fuente que vaya a adquirir estatus investigativo debe atravesar una frontera técnica explícita:

```text
IA
→ solicita búsqueda / fetch mediante estructura controlada
→ SOFTWARE ejecuta la herramienta autorizada
→ SOFTWARE registra recuperación real
   + contenido/locator recuperado
   + provenance
   + timestamp/version cuando aplique
   + checksum o identidad verificable
→ SOFTWARE entrega a IA solo evidencia realmente recuperada
→ IA evalúa su contenido, relevancia, calidad y límites
```

Regla fail-closed:

> **La IA nunca puede declarar una fuente como `CONSULTED`, `VERIFIED`, `EVIDENCE` o equivalente si Software no puede resolver una recuperación real y trazable asociada a esa fuente.**

Por tanto:

- una URL sugerida por el modelo no es una fuente consultada;
- una cita recordada por el modelo no es evidencia recuperada;
- metadata inventada por IA se rechaza;
- un source ref solo adquiere autoridad después del binding software ↔ artefacto de recuperación;
- si una recuperación falla o no puede probarse, la fuente permanece como candidata/no verificada y no puede sostener claims.

La arquitectura debe reutilizar provenance, source registry, storage y tooling existentes antes de crear un subsistema nuevo de adquisición.

## 1.3 Responsabilidad del software

Todo lo verificable de forma exacta debe permanecer en software:

- IDs, timestamps y versiones;
- schemas y validación estructural;
- paths, referencias, lineage y bindings;
- checksums;
- deduplicación exacta;
- persistencia, recovery e invalidación;
- manifests;
- estados y transiciones;
- existencia de inputs;
- conteos y cálculos;
- routing;
- autorizaciones y gates;
- propagación determinista de restricciones ya formalizadas;
- protección de decisiones humanas materializadas;
- detección de artefactos stale/invalidated;
- evidencia de ejecución técnica;
- autoridad sobre el estatus técnico de recuperación de fuentes/evidencia;
- detección operacional de no-progress, ciclos y límites de ejecución.

Regla:

```text
IF DETERMINISTICALLY VERIFIABLE
→ DO NOT SPEND LLM TOKENS TO DECIDE IT
```

## 1.4 Responsabilidad de la IA

La IA se reserva para trabajo cognitivo real:

- descomponer preguntas de investigación;
- proponer dimensiones y subpreguntas pertinentes;
- decidir qué clase de evidencia sería adecuada;
- valorar qué evidencia aporta realmente una fuente;
- valorar calidad y límites de evidencia para un claim;
- interpretar evidencia;
- distinguir hecho, interpretación, lectura especializada e hipótesis;
- detectar contradicciones y explicaciones rivales;
- proponer claims;
- evaluar encaje sustantivo de una obra;
- identificar riesgo de sobreinterpretación;
- identificar gaps materiales;
- decidir qué profundización cognitiva adicional se necesita;
- valorar suficiencia para el uso previsto;
- ajustar la exigencia de evidencia a la fuerza, alcance y controversia del claim sin aplicar una taxonomía rígida universal;
- profundizar claims materiales del fenómeno real además de las obras seleccionadas;
- reevaluar después de la profundización el aporte diferencial, redundancia, cobertura y límites del conjunto de obras;
- sintetizar hallazgos;
- formular tesis provisional y tesis refinada;
- realizar auditoría semántica independiente.

La IA no puede producir como autoridad válida IDs, timestamps, checksums, versiones, estados, lineage, bindings ni decisiones de autorización.

---

# 2. Principios de ingeniería aplicables

Toda misión de PLAN012 debe aplicar, en este orden:

```text
SEARCH BEFORE CREATE
REUSE → EXTEND → CREATE
CONNECT BEFORE REDESIGN
SIMPLIFY BEFORE EXTEND
POLICY FIRST → CODE AFTER
```

Se reutilizarán las skills de ingeniería existentes en `.agents/skills/` cuando sean pertinentes; no se duplicarán como instrucciones largas dentro de cada misión.

Especialmente relevantes:

- `auditar-trazabilidad-input-output`;
- `evidencia-proporcional-git`;
- `harness-determinista`;
- `preparar-paquete-ejecucion-tecnica`;
- `verificar-no-mezcla-de-capas`;
- `tests-validacion-cierre`.

`tests-validacion-cierre` permanece protegido y no se modifica salvo autorización separada y explícita del OWNER.

No crear un agente cuando baste una skill; no crear una skill cuando baste una regla, script o gate; no crear un gate semántico sin política funcional previa.

## 2.1 Regla de arquitectura para agentes, skills y prompts

- Un **agente/rol** se justifica cuando existe responsabilidad diferenciada, criterio propio y, si aplica, capacidad de veto o independencia.
- Una **skill** se justifica para una tarea reutilizable, acotada, recurrente, con inputs/outputs y criterios de parada claros.
- Una **regla** se usa para restricciones transversales.
- Un **gate** bloquea o permite avance sobre condiciones definidas.
- Un **workflow** coordina secuencias.
- Un **script/componente de software** resuelve lógica exacta y repetible.

PLAN012 no presupone un agente permanente por cada responsabilidad cognitiva ni por cada especialidad de investigación.

## 2.2 Revisión dual de skills/prompts de producto

Cuando PLAN012 modifique una skill o prompt de producto relacionado con investigación, el cierre requerirá dos perspectivas distintas:

### Equipo 04 — revisión técnica

Debe validar:

- inputs/outputs;
- integración con contratos;
- routing;
- persistencia;
- recovery;
- compatibilidad;
- tests/harness;
- ausencia de duplicación o responsabilidades cruzadas.

### Equipo 02 + especialista de Investigación — revisión metodológica

Debe validar que las instrucciones cognitivas hagan que la IA:

- planifique antes de buscar;
- investigue con suficiente profundidad;
- distinga niveles de afirmación;
- evalúe evidencia y límites;
- busque rivales y contradicciones;
- preserve fidelidad de obra;
- separe obra y realidad;
- aplique correctamente suficiencia y ResearchStop;
- no convierta investigación en diseño narrativo.

La autoridad metodológica sobre la **calidad de la instrucción investigativa** no cambia la autoridad técnica sobre agentización, runtime, schemas, CLI, harness o tests.

---

# 3. Frontera funcional: INVESTIGACIÓN ≠ NARRATIVA

La investigación puede decidir:

- qué sabemos y qué no sabemos;
- qué evidencia existe y qué limita;
- qué dimensión cubre una obra;
- qué aporta, repite o contradice;
- qué claims permite o limita;
- riesgo de sobreinterpretación;
- cuánto contexto necesita para sostener un uso;
- perspectivas o evidencia faltantes;
- suficiencia para el uso investigativo previsto;
- tesis provisional y tesis refinada basadas en evidencia;
- alternativas defendibles y restricciones downstream.

La investigación **no** decide:

- orden de aparición en el video;
- hook;
- viewer journey;
- bloques narrativos;
- re-hooks;
- revelaciones;
- ritmo;
- duración de bloques;
- transiciones;
- clímax;
- cierre emocional;
- CTA;
- título o miniatura.

Estas decisiones pertenecen a B5-I3 o etapas posteriores.

Dentro de investigación deben preferirse términos como:

```text
APORTE
CONTRIBUCIÓN
COMPLEMENTARIEDAD
REDUNDANCIA
CONTRADICCIÓN
PERSPECTIVA FALTANTE
```

Evitar convertir en decisión investigativa:

```text
FUNCIÓN NARRATIVA
OBRA PUENTE
OBRA EMOCIONAL
ORDEN ARGUMENTAL
CLÍMAX
```

---

# 4. Decisiones funcionales cerradas antes de implementación

## 4.1 Obras aportadas por el usuario

Separar dos dimensiones:

```text
research_role
editorial_intent
```

Comportamiento funcional mínimo:

```text
research_role:
  ANCLA
  NORMAL

editorial_intent:
  NO_DECLARADA
  PREFERIDA
  REQUERIDA
```

Reglas:

- `REQUERIDA` nunca se infiere;
- una obra puede actuar como `ANCLA` sin asumir preferencia editorial;
- `NO_DECLARADA` no bloquea investigación;
- solo se solicita aclaración humana cuando la ambigüedad vaya a cambiar una decisión material.

## 4.2 Número de obras finales

No existe todavía una tabla automática duración→cantidad de obras.

El objetivo final permitido permanece dentro del rango funcional previsto:

```text
target_final_works ∈ {3, 4, 5}
```

Pero **no existe un default silencioso**.

La cantidad debe resolverse mediante:

```text
duración objetivo
+
complejidad del fenómeno
+
profundidad necesaria
+
contexto requerido
        ↓
recomendación razonada 3 / 4 / 5
        ↓
usuario acepta / modifica
O
delega explícitamente la decisión
```

Reglas:

- no introducir `15 min → 3`, `20 min → 4`, `25 min → 5` ni fórmula equivalente;
- si el usuario delega, la IA puede recomendar/escoger 3, 4 o 5 con razonamiento cualitativo;
- software registra la decisión y su provenance, pero no inventa la cifra;
- si falta información material, puede solicitarse aclaración;
- la calibración futura deberá salir de episodios reales.

## 4.3 Discovery y objetivo de candidatas base

La heurística `≈3 candidatas profesionales por plaza final` se aplica al **BASE_RESEARCH_POOL**, no al discovery bruto.

```text
DISCOVERY_POOL
  amplio y dinámico
        ↓
filtro preliminar
        ↓
BASE_RESEARCH_POOL
  ≈ 3 candidatas viables
  por plaza final
        ↓
selección
        ↓
DEEP_RESEARCH_POOL
```

Orientación normal:

```text
3 obras finales → ≈9 candidatas con investigación base profesional
4 obras finales → ≈12
5 obras finales → ≈15
```

Esto es una **heurística blanda**, no una cuota ni un gate rígido.

Puede cerrarse con menos o ampliarse por:

- calidad;
- diversidad útil;
- redundancia;
- estrechez del tema;
- gaps;
- suficiencia determinada por `ResearchStopDecision`.

La regla histórica `5–8 candidatas` no gobierna el flujo V2 y solo se preservará donde sea necesaria para compatibilidad legacy.

## 4.4 Fidelidad preliminar

Estados funcionales:

```text
APTA
APTA_CON_RIESGOS
NO_APTA
```

Pregunta semántica:

> ¿Existe evidencia suficiente para recomendar responsablemente invertir investigación profunda en esta candidata?

`APTA_CON_RIESGOS` debe registrar riesgos concretos que la investigación profunda esté obligada a resolver o revalidar.

## 4.5 Fidelidad profunda

Estados funcionales:

```text
APROBADA
APROBADA_CON_LIMITES
MAS_INVESTIGACION_REQUERIDA
NO_APROBADA
```

`APROBADA_CON_LIMITES` debe propagar restricciones explícitas hacia downstream, por ejemplo:

- claim permitido;
- claim que requiere matiz;
- claim no permitido;
- atribución prohibida;
- lectura que debe presentarse como interpretación;
- intención autoral no afirmable;
- condición bajo la cual un claim puede usarse.

## 4.6 Criterio de materialidad

Definición transversal:

> Un elemento es MATERIAL cuando puede cambiar significativamente la pregunta o alcance real de investigación, la validez de un claim importante, la tesis, la selección o uso de una obra, o las restricciones que debe respetar la fase siguiente.

Esta definición debe reutilizarse en:

- ResearchPlan;
- gaps;
- ResearchStop;
- claims;
- fidelidad;
- especialistas;
- auditoría;
- invalidación;
- cierre.

## 4.7 Contradicciones y controversias

PLAN012 no exige que toda contradicción tenga un ganador artificial.

Una contradicción material puede terminar como:

```text
RESUELTA
PRESERVADA_COMO_CONTROVERSIA
REGISTRADA_COMO_LECTURA_RIVAL
DELIMITADA_COMO_INCERTIDUMBRE
CONVERTIDA_EN_RESTRICCION_DE_CLAIM
MAS_INVESTIGACION_REQUERIDA
BLOCKED_FOR_INTENDED_USE
```

Lo que bloquea es:

> una contradicción material sin tratamiento suficiente.

No bloquea por sí misma una controversia legítima correctamente investigada, representada y delimitada.

## 4.8 RESEARCH_READY

`RESEARCH_READY` no significa ausencia total de incertidumbre.

Puede existir incertidumbre si está identificada, delimitada y controlada. No puede existir incertidumbre material no controlada.

Semánticamente deben distinguirse:

```text
RESEARCH_READY
RESEARCH_READY_WITH_LIMITATIONS
NOT_RESEARCH_READY
```

La representación técnica exacta se decidirá en B1, evitando duplicar estados existentes sin necesidad.

`LIMITED_BUT_USABLE` puede cerrar investigación solo cuando la limitación identifica:

- qué no se sabe;
- qué afecta;
- qué no afecta;
- qué restricción obligatoria recibe downstream.

Pueden coexistir con `RESEARCH_READY_WITH_LIMITATIONS`, según el caso:

- controversia legítima correctamente documentada;
- limitación secundaria;
- fuente deseable pero no imprescindible inaccesible;
- claim retirado;
- lectura rival viva;
- incertidumbre delimitada;
- limitación de acceso compensada por evidencia suficiente para el uso previsto.

Bloquean cierre, entre otros:

- claim crítico sin evidencia suficiente;
- obra final sin fidelidad profunda suficiente;
- contradicción material sin tratamiento suficiente;
- rival fuerte material ignorado o insuficientemente estudiado;
- provenance material desconocida;
- dimensión crítica del ResearchPlan pendiente;
- tesis que dependa de hipótesis presentada como hecho;
- decisión humana material pendiente que modifique el conjunto;
- obra manualmente elegida que falle sin resolución de sustitución o delegación;
- blocker de auditoría independiente;
- `MORE_RESEARCH_REQUIRED` material;
- `BLOCKED_BY_EVIDENCE` en un elemento necesario para sostener el episodio.

---

# 5. Estándar funcional del ResearchPlan

`ResearchPlan` debe ser un plan real de investigación, no un contenedor superficial de tema y alcance.

Antes de abrir búsquedas sustantivas debe representar o referenciar de forma estructurada, sin duplicar datos canónicos innecesariamente:

| Elemento | Contenido esperado |
|---|---|
| Pregunta central | Qué queremos entender o comprobar |
| Uso previsto | Para qué decisión, tesis o claim necesitamos la respuesta |
| Alcance | Qué entra y qué queda fuera |
| Dimensiones | Áreas reales del fenómeno relevantes al caso |
| Subpreguntas | Preguntas investigables dentro de cada dimensión |
| Evidencia necesaria | Qué clase de evidencia permitiría responder cada pregunta y qué nivel de respaldo sería razonable según la fuerza del claim previsto |
| Estrategia/fuentes preferidas | Tipos de fuentes apropiados según el claim |
| Claims críticos previstos | Afirmaciones cuya falla puede cambiar tesis, alcance o uso de obras |
| Rivales / refutación | Explicaciones o hechos que podrían contradecir hipótesis iniciales |
| Riesgos / gaps | Qué puede debilitar o impedir la investigación |
| Especialistas potenciales | Conocimiento especializado que podría ser necesario si se vuelve material |
| Criterios de suficiencia | Qué tendría que saberse para avanzar responsablemente por línea |
| Objetivo de obras | Plazas finales previstas y política de competencia/base research |
| Obras aportadas | Rol de investigación e intención editorial declarada/no declarada |

El propósito es que, antes de abrir búsquedas sustantivas, el sistema pueda responder:

> qué debe investigar, por qué, con qué evidencia y qué podría refutar la explicación inicial.

Los IDs, versiones, timestamps, checksums y bindings son añadidos por software.

`ResearchPlan` no necesita imponer una taxonomía universal de claims. Sí debe permitir que, cuando sea material y previsible, la estrategia de evidencia distinga entre una afirmación limitada y otra más fuerte, causal, general o controvertida. La representación técnica exacta se decidirá en B1 sin convertir esta regla metodológica en un score numérico ni en un gate rígido.

La implementación técnica de `ResearchPlan` debe evitar un mega-schema innecesario. B1 decidirá qué información vive directamente en el contrato, qué se referencia desde contratos existentes y qué permanece como output cognitivo estructurado.

---

# 6. Estándares de investigación profesional

## 6.1 Investigación base profesional del fenómeno

No puede consistir en unos pocos resultados de búsqueda y un resumen del modelo.

Antes de considerar que existe una base profesional del fenómeno debe haber cobertura razonable de, según relevancia:

- pregunta central;
- dimensiones principales;
- conceptos relevantes;
- evidencia importante;
- fuentes primarias u originales cuando existan y sean adecuadas;
- literatura especializada cuando corresponda;
- datos relevantes cuando existan;
- explicaciones rivales;
- contradicciones;
- gaps;
- límites de generalización;
- nivel de confianza;
- qué no demuestra la evidencia disponible.

No existe cuota fija de fuentes.

```text
SUFICIENCIA PARA EL USO PREVISTO
≠
NÚMERO DE FUENTES
```

Diez páginas derivadas del mismo origen no representan diez evidencias independientes.

## 6.2 Investigación base profesional de una obra

Una obra no puede llegar a comparación/selección solo porque “parece encajar”.

Antes debe conocerse razonablemente:

### Identidad

- obra exacta;
- autor/director/creador;
- año;
- versión/adaptación/edición/episodio cuando sea material.

### Contexto factual

- sinopsis factual breve;
- personajes relevantes;
- conflicto relacionado;
- acontecimientos, decisiones y consecuencias relevantes.

### Relación con el fenómeno

- qué dimensión toca;
- por qué parece encajar;
- qué podría aportar;
- qué parece repetir;
- qué aporta diferencialmente frente a otras candidatas.

### Evidencia

- qué evidencia real apoya la conexión;
- qué fuentes o representaciones fueron consultadas;
- qué calidad y límites tienen.

### Riesgos

- qué puede estar siendo sobreinterpretado;
- qué contradicciones existen;
- qué no está verificado;
- qué limitaciones de acceso existen;
- qué partes son interpretación y no hecho.

### Conclusión preliminar

```text
APTA
APTA_CON_RIESGOS
NO_APTA
```

No constituye por sí sola investigación base profesional:

- memoria del modelo;
- Wikipedia;
- IMDb;
- FilmAffinity;
- una sinopsis genérica;
- agregadores;
- coincidencia semántica superficial entre sinopsis y tema.

Estos recursos pueden ser útiles en `DISCOVERY`, pero no son suficientes por sí solos para recomendar profesionalmente una obra.

## 6.3 Investigación profunda orientada a claims y uso previsto

“Profunda” no significa encontrar más enlaces ni investigar absolutamente todo lo relacionado con una obra o con el fenómeno.

Significa:

> investigar con profundidad suficiente todo aquello que se haya vuelto material para la tesis provisional y para los claims que pretendemos sostener, independientemente de si pertenece al fenómeno real o a una obra.

Después de la tesis provisional deben existir dos líneas de profundización que pueden avanzar parcialmente en paralelo y volver a cruzarse antes de la tesis refinada.

### A. Profundización del fenómeno real

Debe profundizar los claims externos que se hayan vuelto materiales, por ejemplo:

- mecanismos explicativos;
- datos relevantes;
- estudios primarios/originales y literatura especializada pertinente;
- condiciones de aplicación;
- límites de generalización;
- diferencia entre descripción, asociación, explicación y causalidad cuando sea material;
- explicaciones rivales;
- contradicciones;
- limitaciones metodológicas;
- contexto que pueda cambiar la interpretación;
- qué evidencia apoya, limita o refuta el claim.

No puede cerrarse una investigación con obras profundamente estudiadas mientras los claims centrales sobre personas, sociedad, historia, psicología u otro fenómeno real permanecen sostenidos solo por una exploración inicial superficial.

### B. Profundización de las obras seleccionadas

Según disponibilidad, materialidad y claim, puede requerir revisar:

- obra original;
- escenas/pasajes;
- arco necesario;
- acciones;
- decisiones;
- consecuencias;
- motivaciones explícitas;
- motivaciones inferidas;
- contexto;
- guion/transcripción;
- fuentes oficiales;
- declaraciones de autores/directores cuando sean pertinentes;
- crítica especializada;
- lecturas rivales;
- contradicciones;
- límites de fidelidad para el uso previsto.

Ambas líneas deben permitir responder:

```text
¿podemos afirmar esto?
¿qué exactamente estamos afirmando?
¿qué parte es hecho?
¿qué parte es interpretación?
¿es descripción, asociación, explicación, causalidad o generalización materialmente distinta?
¿qué nivel de evidencia exige esa fuerza de claim?
¿qué matiz necesita?
¿qué rival o contradicción existe?
¿qué no podemos afirmar?
¿qué condición o límite debe propagarse?
```

La profundidad se gobierna por materialidad, fuerza del claim, riesgo y suficiencia para el uso previsto, no por cuota de fuentes.

La profundización del fenómeno real y de las obras debe volver a cruzarse antes de la tesis refinada para comprobar que la explicación sobre la realidad y el uso de las obras siguen siendo mutuamente compatibles sin confundir sus evidencias.

---

# 7. Calidad e independencia de fuentes

PLAN012 debe dejar explícito que “tener fuentes” no equivale a “tener buena evidencia”.

Como orientación funcional, cuando corresponda al tipo de claim:

```text
FUENTE PRIMARIA / OBRA ORIGINAL
        ↓
FUENTE OFICIAL / DATOS ORIGINALES
        ↓
INVESTIGACIÓN ACADÉMICA O ESPECIALIZADA
        ↓
FUENTE SECUNDARIA DE CALIDAD
        ↓
FUENTE GENERAL
        ↓
AGREGADORES / WIKIS / REDES
  principalmente discovery/orientación
```

Esta jerarquía no se convierte en un score rígido universal.

Reglas obligatorias:

> Más fuentes no compensan fuentes inadecuadas.

> Varias páginas que derivan del mismo origen no constituyen evidencia independiente.

## 7.1 Qué puede determinar software

- identidad técnica de fuente;
- URL/provider;
- timestamp;
- contenido recuperado;
- hash;
- duplicado exacto;
- source type declarado;
- provenance;
- relaciones conocidas entre artefactos;
- si la fuente fue realmente recuperada o solo mencionada.

## 7.2 Qué requiere valoración cognitiva

- si la fuente es adecuada para un claim concreto;
- si dos fuentes aparentemente distintas dependen materialmente del mismo origen;
- si la evidencia es independiente en sentido sustantivo;
- si la fuente primaria basta o requiere contexto especializado;
- si una secundaria especializada es necesaria para interpretación;
- qué limitaciones de metodología o contexto afectan el claim.

No se implementará un gate falso del tipo:

```text
academic = high_quality
blog = low_quality
```

sin considerar claim y contexto.

## 7.3 Exigencia de evidencia proporcional a la fuerza del claim

La suficiencia de evidencia debe evaluarse después de preguntar:

> ¿Qué exactamente estamos afirmando y con qué fuerza?

Cuando sea relevante, la investigación puede distinguir entre formas como:

- descripción;
- asociación;
- explicación;
- causalidad;
- prevalencia;
- generalización;
- interpretación;
- intención;
- predicción.

Esta lista es orientativa, no una taxonomía rígida universal.

Regla metodológica:

> Cuanto más fuerte, causal, universal, predictivo o controvertido sea un claim, mayor debe ser la exigencia de evidencia adecuada, contraste, independencia, condiciones de validez y explicaciones rivales antes de considerarlo defendible.

Una asociación observada no autoriza automáticamente causalidad; un resultado contextual no autoriza generalización universal; una interpretación plausible no autoriza atribuir intención explícita.

La regla también protege eficiencia:

> No sobreinvestigar afirmaciones sencillas y bien establecidas como si todas fueran claims extraordinarios.

La IA realiza la valoración semántica de la carga probatoria. El software puede registrar la naturaleza declarada del claim, sus evidencias, límites, provenance y decisiones de suficiencia, pero no debe convertir esta regla en un score numérico universal ni inferir automáticamente calidad a partir de una etiqueta.

---

# 8. Separación obligatoria: evidencia de obra ≠ evidencia de realidad

PLAN012 conserva explícitamente:

```text
WORK / NARRATIVE EVIDENCE
≠
EXTERNAL REALITY EVIDENCE
```

Una obra puede demostrar:

> “La obra representa X.”

No puede demostrar por sí sola:

> “Las personas reales funcionan como X.”

Del mismo modo, evidencia externa sobre un fenómeno real no autoriza a atribuir automáticamente a un personaje una motivación que la obra no establece.

Esta separación debe estar representada en:

- ResearchPlan;
- ResearchPack/hallazgos;
- ClaimsLedger;
- SourceAccessAndEvidenceReport cuando aplique;
- WorkResearchDossier;
- auditoría independiente;
- criterios de `RESEARCH_READY`.

La representación técnica exacta se decidirá reutilizando contratos existentes antes de crear campos o contratos paralelos.

---

# 9. Hipótesis, tesis provisional y tesis refinada

La vertical debe distinguir:

```text
HIPÓTESIS INICIAL
        ↓
INVESTIGACIÓN INICIAL
        ↓
TESIS PROVISIONAL
        ↓
PROFUNDIZACIÓN DE LO MATERIAL
├─ FENÓMENO REAL / CLAIMS EXTERNOS
└─ OBRAS SELECCIONADAS
        ↓
RIVALES + CONTRADICCIONES + LÍMITES
        ↓
REEVALUACIÓN DEL CONJUNTO DE OBRAS
        ↓
TESIS REFINADA
```

## 9.1 Hipótesis inicial

Explicación tentativa que orienta preguntas y puede ser refutada.

No puede convertirse en objetivo de confirmación.

## 9.2 Tesis provisional

> Explicación que, después de investigación inicial suficiente del fenómeno, parece mejor sustentada por la evidencia disponible, pero todavía debe ponerse a prueba durante profundización.

Debe poder evolucionar como:

```text
CONFIRMADA
MODIFICADA
LIMITADA
RECHAZADA
```

No es una frase narrativa, hook ni promesa de video.

No debe nacer antes de existir una base suficiente de investigación.

## 9.3 Tesis refinada

Conclusión sustantiva defendible después de cruzar:

- fenómeno real profundizado en sus claims materiales;
- evidencia externa y su carga probatoria;
- obras seleccionadas profundamente investigadas;
- reevaluación post-profundización del conjunto de obras;
- fidelidad profunda;
- claims;
- contradicciones;
- rivales;
- límites.

Puede coexistir con una tesis alternativa defendible cuando la evidencia no autoriza una única conclusión excluyente.

## 9.4 Trazabilidad de evolución

El sistema debe poder representar:

```text
TESIS PROVISIONAL
        ↓
qué se confirmó
qué se modificó
qué se rechazó
qué se limitó
qué evidencia produjo el cambio
qué rival afectó la conclusión
        ↓
TESIS REFINADA
```

La auditoría independiente debe poder revisar esa evolución para detectar sesgo de confirmación.

PLAN012 no presupone un contrato nuevo `ProvisionalThesis`. B1 debe aplicar `SEARCH BEFORE CREATE` y evaluar primero si `RefinedThesis` puede evolucionarse/versionarse para representar etapas y lineage sin duplicación.

---

# 10. Selección humana y selección delegada

## 10.1 Selección delegada optimiza el conjunto

Cuando el usuario delega “elige por mí”, el sistema no debe escoger automáticamente las primeras obras de un ranking individual.

Debe seleccionar el mejor **conjunto**, considerando cognitivamente:

```text
encaje real con el fenómeno
+
calidad de evidencia
+
fidelidad
+
aporte diferencial
+
cobertura de dimensiones
+
complementariedad
+
diversidad útil
-
redundancia
-
riesgo de sobreinterpretación
-
limitaciones materiales
```

No se crea por defecto un score numérico tipo `91.7%`.

Regla:

> La selección delegada optimiza el conjunto, no el ranking individual.

## 10.2 Protección de selección manual

Cualquier selección manual materializada debe quedar protegida contra sustitución silenciosa.

Ejemplo:

```text
Usuario selecciona A + C + F
↓
F falla investigación profunda
↓
NO sustituir automáticamente F por D
```

Debe ocurrir:

```text
F falla
↓
explicar motivo
↓
presentar alternativas
↓
usuario elige sustituta
O
delega explícitamente la sustitución
```

Si el usuario delegó completamente la selección desde el inicio, el sistema puede gestionar sustituciones dentro del alcance exacto de esa delegación, con trazabilidad.

Software debe proteger bindings y alcance de la decisión humana/delegada. La valoración de qué sustituta es mejor sigue siendo cognitiva.

## 10.3 Reevaluación post-profundización del conjunto de obras

La comparación realizada antes de la selección no se considera definitiva. Después de investigar profundamente las obras elegidas y conocer mejor sus límites, interpretaciones defendibles y aporte real, Research debe reevaluar el **conjunto**.

Debe comparar de nuevo, sin diseñar el video:

- cobertura real de dimensiones;
- aporte diferencial;
- complementariedad;
- redundancia descubierta durante profundización;
- contraste entre perspectivas;
- límites de fidelidad;
- perspectivas faltantes;
- relación de cada obra con los claims y la tesis provisional ya profundizados.

La reevaluación puede concluir conceptualmente:

```text
CONJUNTO_SE_MANTIENE
RECOMENDAR_ELIMINAR_UNA_OBRA
RECOMENDAR_SUSTITUIR_UNA_OBRA
RECOMENDAR_REDUCIR_CANTIDAD
REABRIR_AMBITO_POR_PERSPECTIVA_FALTANTE
```

Los nombres técnicos exactos no quedan fijados por este roadmap. B1/B3 deberán representar el comportamiento reutilizando decisiones, dossiers y lineage existentes antes de crear un contrato adicional.

Si la selección fue manual, ninguna recomendación cambia el conjunto por sí sola: el usuario decide o delega explícitamente. Si la selección fue completamente delegada, el sistema puede gestionar cambios dentro del alcance materializado de esa delegación, dejando trazabilidad y asegurando que cualquier sustituta complete la investigación y fidelidad necesarias antes del cierre.

Esta reevaluación sigue siendo investigación. Puede afirmar que dos obras terminaron aportando prácticamente la misma perspectiva o que falta una dimensión sustantiva. No puede decidir orden, hook, función emocional, obra puente, clímax ni otra decisión de B5-I3.

---

# 11. ResearchStopDecision iterativo y focal

`ResearchStopDecision` no es un único checkpoint final.

La lógica conceptual es:

```text
INVESTIGAR
        ↓
¿SUFICIENTE PARA ESTA DECISIÓN / CLAIM / ÁMBITO?
        │
        ├── NO
        │   ↓
        │ investigar gap específico
        │
        └── SÍ
            ↓
          avanzar
```

Puede aplicarse a:

- pregunta;
- dimensión;
- claim;
- candidata;
- fidelidad;
- contradicción;
- investigación profunda del fenómeno real;
- investigación profunda de obras;
- reevaluación post-profundización del conjunto de obras;
- tesis;
- paquete agregado.

Estados conceptuales existentes a reutilizar:

```text
SUFFICIENT_FOR_INTENDED_USE
LIMITED_BUT_USABLE
MORE_RESEARCH_REQUIRED
BLOCKED_BY_EVIDENCE
```

Si aparece nueva evidencia:

```text
nuevo hallazgo
↓
afecta claim X
↓
reabrir X y dependencias materiales
```

No reiniciar automáticamente toda la investigación.

La invalidación focal y los return routes deben ser software; la decisión semántica de suficiencia pertenece a la capa cognitiva/auditoría autorizada.

## 11.1 Guard operacional anti-loop / no-progress

La suficiencia metodológica y la seguridad operacional son conceptos distintos:

```text
ResearchStopDecision
→ ¿sabemos suficiente para el uso previsto?

Iteration / No-Progress Guard
→ ¿el sistema está progresando de forma operacional?
```

Software debe poder detectar, con señales deterministas o reproducibles cuando existan:

- mismo gap reabierto repetidamente sin evidencia nueva material;
- mismo estado/return route repetido;
- mismo conjunto de evidencia;
- mismo resultado cognitivo o fingerprint equivalente cuando sea técnicamente razonable;
- ciclo de estados, por ejemplo `A → B → A`;
- agotamiento de un presupuesto operativo autorizado de iteraciones/tiempo/acciones.

El guard **no puede declarar suficiencia investigativa** por llegar a un límite. Su única función es impedir ejecución indefinida.

Cuando se active:

```text
NO_PROGRESS / ITERATION_GUARD
        ↓
STOP_LOCAL o HUMAN/OWNER REVIEW
```

según autoridad y contexto materializados.

La implementación exacta debe reutilizar run state, manifests, events o trazabilidad existentes antes de crear un contrato independiente. B1 definirá las señales mínimas; B2/B3 las aplicarán; B5 demostrará que un loop sintético se detiene sin convertir el guard en un criterio semántico de `SUFFICIENT_FOR_INTENDED_USE`.

---

# 12. Especialistas temporales

Los especialistas pueden activarse en cualquier fase material:

- ResearchPlan;
- investigación del fenómeno;
- discovery;
- investigación base de obras;
- fidelidad;
- selección/comparativa;
- investigación profunda;
- claims;
- síntesis;
- auditoría, cuando corresponda.

Criterio funcional:

> activar conocimiento especializado cuando pueda cambiar materialmente una pregunta, interpretación, validez, evidencia, límite, suficiencia, claim o tesis.

Esto **no** autoriza crear automáticamente:

```text
agent_psychologist
agent_historian
agent_sociologist
agent_economist
...
```

La infraestructura decidirá si la necesidad se resuelve mediante:

- skill cognitiva;
- prompt especializado;
- capability temporal;
- subagente temporal;
- mismo rol con contexto experto;
- otra pieza ya existente.

Solo una brecha arquitectónica demostrada justificaría otro agente estable.

---

# 13. Arquitectura objetivo de la vertical

```text
INPUT
 tema | obra | corpus | combinación
        ↓
SOFTWARE: NORMALIZACIÓN
        ↓
PERTENENCIA
        ↓
RESEARCH PLAN
 pregunta
 alcance
 dimensiones
 subpreguntas
 evidencia requerida
 estrategia de fuentes
 rivales/refutación
 suficiencia
 objetivo de obras
        ↓
MAPA INICIAL DEL FENÓMENO
        ↓
┌─────────────────────────────┐
│                             │
▼                             ▼
INVESTIGACIÓN BASE        DISCOVERY_POOL
DEL FENÓMENO              amplio/dinámico
│                             │
│                             ↓
│                    filtro preliminar
│                             │
│                             ↓
│                    BASE_RESEARCH_POOL
│                    ≈3 viables/plaza
│                             │
│                    investigación base
│                             │
│                    fidelidad preliminar
│                             │
└──────────────┬──────────────┘
               ↓
       SUFICIENCIA INICIAL
               ↓
       TESIS PROVISIONAL
               ↓
     COMPARACIÓN DE OBRAS
               ↓
        USUARIO ELIGE
               O
        DELEGA SELECCIÓN
               ↓
   SELECTED_FOR_DEEP_RESEARCH
               ↓
┌───────────────────────────────┐
│                               │
▼                               ▼
PROFUNDIZAR                 PROFUNDIZAR
FENÓMENO REAL               OBRAS ELEGIDAS
claims externos             escenas/pasajes
mecanismos/datos            decisiones/consecuencias
estudios/rivales            interpretaciones/rivales
límites/contradicciones     límites de fidelidad
│                               │
└───────────────┬───────────────┘
                ↓
       FIDELIDAD PROFUNDA
          DE LAS OBRAS
                ↓
    CLAIMS / RIVALES / LÍMITES
      Y CARGA PROBATORIA
                ↓
  REEVALUACIÓN POST-DEEP DEL
       CONJUNTO DE OBRAS
                ↓
   ¿CAMBIO MATERIAL DEL SET?
        │              │
       SÍ             NO
        │              │
 decisión humana/      │
 delegación válida     │
 + reabrir solo        │
 ámbito afectado       │
        └──────┬───────┘
               ↓
     ¿GAPS MATERIALES?
         │           │
        SÍ          NO
         │           │
 reabrir solo        ↓
 ámbito afectado  SÍNTESIS
                     ↓
              TESIS REFINADA
                     ↓
          AUDITORÍA INDEPENDIENTE
                     ↓
              RESEARCH_READY
════════════════════════════════════
          FIN DE INVESTIGACIÓN
════════════════════════════════════
                     ↓
                  B5-I3
                     ↓
             VIEWER JOURNEY
                     ↓
               ARQUITECTURA
                     ↓
                  GUION
```

Después del mapa inicial, investigación del fenómeno y discovery pueden avanzar parcialmente en paralelo. Tras la tesis provisional, la profundización del fenómeno real y de las obras seleccionadas también puede avanzar parcialmente en paralelo. La reevaluación post-deep puede reabrir únicamente la obra, claim, dimensión o decisión afectada. El flujo es iterativo; los gaps no obligan a reiniciar toda la vertical.

Cada salto cognitivo debe quedar enmarcado por software: input/contrato → invocación cognitiva → herramientas/evidencia real cuando aplique → validación/binding/persistencia → estado/return route.

## 13.1 Paralelismo funcional ≠ concurrencia técnica obligatoria

Las ramas paralelas de los diagramas expresan **independencia o posibilidad de avance parcial**, no una obligación de ejecutar tareas simultáneamente.

Regla por defecto:

> **PLAN012 puede implementarse secuencialmente cuando ello simplifique el runtime y preserve corrección, trazabilidad y coste.**

No se introducirá concurrencia real solo porque dos líneas aparezcan en paralelo en el modelo funcional.

Si una misión futura decide implementar concurrencia real, deberá demostrar antes:

- versiones exactas de inputs compartidos;
- join explícito;
- detección de resultados stale;
- reglas deterministas de merge;
- invalidación de ramas dependientes;
- manejo de carreras/reintentos;
- idempotencia o estrategia equivalente;
- tests de ordering y race conditions.

Sin esa evidencia, la ejecución secuencial es la implementación preferida.

---

# 14. Reutilización obligatoria del sistema existente

La auditoría previa mantiene esta disposición, actualizada por la revisión funcional:

| Artefacto actual | Disposición PLAN012 |
|---|---|
| `ResearchPack` | `REUSE + EXTEND` |
| `ClaimsLedger` | `REUSE + EXTEND` |
| `SourceAccessAndEvidenceReport` | `REUSE + EXTEND IF NEEDED`, priorizando reuse |
| `ResearchStopDecision` | `REUSE` como mecanismo iterativo/focal |
| `WorkResearchDossier` | `REUSE + EXTEND` |
| `WorkLifecycle` | `REUSE + EXTEND SOLO SU DIMENSIÓN PROPIA`; no absorber fidelidad, suficiencia, selección o validez en un mega-enum |
| `IndependentResearchAudit` | `REUSE + EXTEND CRITERIA` |
| `RefinedThesis` | `REUSE + EXTEND`; evaluar soporte de etapa provisional antes de crear otro contrato |
| `HumanEpisodeInput` | `EXTEND` |
| intake/application/CLI | `REUSE + EXTEND` |
| `MaterialCuration` | `EXTEND + MOVE` responsabilidades narrativas |
| `NarrativeHumanAnalysis` | `EXTEND + MOVE` campos narrativos |
| `CurationDecision` | `DEPRECATE` como output activo V2; preservar compatibilidad necesaria |
| auditoría semántica B5-I2 | reutilizar patrón técnico; separar criterios legacy |
| skill de research | `EXTEND` |
| skill de curation | `RECONCILE / MOVE` narrativa |
| skill de síntesis de tesis | `REUSE + MOVE` autoridad hacia investigación |
| skill QA research | `EXTEND` |
| workflow research | `EXTEND` |
| prompt `RESEARCH_AND_CURATION` | `EXTEND` |
| runtime/provenance/harness | `REUSE` |
| storage/recovery/invalidation | `REUSE + EXTEND` |
| `ResearchPlan` | `CREATE` — requisito aprobado; definir forma mediante SEARCH BEFORE CREATE |
| `ResearchReadyManifest` | `CREATE` — requisito aprobado; definir forma mediante SEARCH BEFORE CREATE |
| tesis provisional | `REUSE/EXTEND FIRST`; nuevo contrato solo si B1 demuestra brecha |

No se crea un segundo ledger, segundo dossier, segundo runtime, segundo sistema de autorización, segundo storage, segundo provenance o segundo lifecycle general.

---

# 15. Contratos nuevos justificados

## 15.1 `ResearchPlan`

Contrato de intención, preguntas, evidencia y cobertura de investigación. Debe existir antes de búsquedas sustantivas.

Debe representar o referenciar, sin duplicar información canónica:

- input/origen;
- pregunta central;
- uso previsto;
- alcance;
- dimensiones;
- subpreguntas;
- evidencia requerida;
- estrategia/tipos de fuente;
- claims críticos previstos;
- rivales/refutación;
- gaps/riesgos;
- especialistas potenciales;
- criterios de suficiencia;
- objetivo de obras finales o estado de decisión/delegación;
- intención/rol de obras aportadas;
- política de selección humana/delegada aplicable;
- referencias a artefactos de origen.

Los IDs, versiones, timestamps, checksums y bindings los añade software.

B1 decidirá qué vive directamente en el schema y qué se referencia, evitando un mega-schema.

## 15.2 `ResearchReadyManifest`

Contrato final ligero de cierre y handoff. No copia el contenido de la investigación.

Debe referenciar versiones/checksums exactos de los artefactos que sustentan el cierre, como mínimo según aplique:

- ResearchPlan;
- ResearchPack;
- ClaimsLedger;
- SourceAccessAndEvidenceReport;
- WorkResearchDossiers de las obras finales;
- decisiones de selección/delegación;
- fidelity results;
- tesis provisional y lineage hacia tesis refinada, en la representación técnica elegida;
- RefinedThesis;
- ResearchStopDecision(s) material(es);
- IndependentResearchAudit;
- limitaciones/restricciones downstream.

El manifest debe fallar cerrado cuando un artefacto material esté ausente, stale, invalidado o no trazable.

---

# 16. Auditoría independiente

La auditoría independiente no se limita a comprobar que existen citas y claims.

Debe valorar semánticamente, sin convertirse en una segunda investigación completa:

- cobertura razonable del ResearchPlan;
- calidad de fuentes;
- independencia material de evidencia cuando corresponda;
- gaps materiales ignorados;
- sesgo de confirmación;
- contradicciones y rivales;
- separación obra / realidad;
- fidelidad de obras finales;
- cumplimiento de restricciones;
- evolución tesis provisional → refinada;
- selección delegada como conjunto y no solo ranking;
- protección de selección manual frente a sustitución silenciosa;
- suficiencia para intended use;
- claims críticos y sus límites.

## 16.1 Qué verifica software

- auditor actor/run distinto cuando el contrato lo exige;
- artefactos exactos auditados;
- checksums/versiones;
- bindings y provenance;
- findings y return routes formalizados;
- blockers abiertos;
- dependencias stale/invalidated.

## 16.2 Qué verifica cognición auditora

- metodología razonable;
- suficiencia;
- fidelidad;
- adecuación de evidencia;
- rivales/contradicciones;
- sesgo;
- límites;
- calidad de la evolución de tesis.

No se codificará una falsa certeza semántica como un `if` determinista cuando la evaluación requiera juicio experto.

---

# 17. Bloques de implementación

## B1 — Contratos, estados y frontera Research → Narrative

### Objetivo

Crear la base contractual V2 y reconciliar contratos existentes sin ejecutar todavía la vertical completa.

### Dependencias

- versión funcional 1.2 aprobada por Equipo 02 y especialista de Investigación;
- seis ajustes técnicos de v1.3 incorporados y aprobados en revisión técnica final;
- decisiones funcionales de investigación permanecen cerradas salvo contradicción material demostrada;
- PLAN011 M1–M3 permanecen cerrados;
- no se autoriza B5.5/B6/B7, IA real ni P2 real.

### Trabajo de software

- crear `ResearchPlan`;
- crear `ResearchReadyManifest`;
- extender `HumanEpisodeInput` para separar rol de investigación e intención editorial;
- representar recomendación/confirmación/delegación de `target_final_works` sin default silencioso;
- antes de extender estados, producir una **matriz de estados ortogonales** y asignar cada dimensión a su contrato/owner técnico;
- mantener `WorkLifecycle` limitado a la progresión investigativa que realmente le corresponda, sin absorber en un único mega-enum selección, fidelidad, suficiencia, validez o tesis;
- como mínimo, B1 debe separar conceptualmente estas dimensiones, ajustando nombres exactos tras inventario:

```text
research_stage
selection_state
preliminary_fidelity
deep_fidelity
research_sufficiency
artifact_validity
thesis_stage
```

- definir transiciones e invalidaciones entre dimensiones sin crear estados cartesianos combinados como `DEEP_SELECTED_APPROVED_SUFFICIENT_CURRENT`;
- extender `WorkResearchDossier` para investigación base, profunda, riesgos y fidelidad;
- hacer `ClaimsLedger` utilizable antes del guion, eliminando obligatoriedad activa de `script_version/script_location` en flujo V2 sin romper histórico;
- representar de forma stage-neutral la fuerza/naturaleza relevante del claim y la base de suficiencia de evidencia, sin taxonomía rígida universal ni score numérico;
- evaluar si `RefinedThesis` puede representar `PROVISIONAL/REFINED` mediante etapa/version/lineage antes de crear contrato adicional;
- reconciliar `MaterialCuration`, `NarrativeHumanAnalysis` y `CurationDecision` para que research no tenga que producir orden, función narrativa, progresión o clímax;
- representar separación work evidence / external reality evidence reutilizando contratos antes de crear otros;
- representar restricciones downstream de fidelidad profunda;
- representar de forma auditable la reevaluación post-profundización del conjunto y cualquier cambio derivado, reutilizando decisiones/dossiers existentes antes de crear contrato nuevo;
- definir validadores/migración/compatibilidad necesarios;
- conservar autorización, provenance, storage y lifecycle existentes salvo brecha demostrada;
- formalizar binding `source request → tool execution → retrieved artifact → source ref → cognitive use` para que ninguna fuente no recuperada pueda adquirir estatus de evidencia;
- definir señales mínimas del guard operacional anti-loop/no-progress sin confundirlo con suficiencia semántica;
- auditar consumidores actuales de M3/B5-I3 y producir una **consumer-contract matrix** que relacione cada artefacto V2 con lo que B5-I3 espera hoy;
- especificar versionado/adaptador/migración explícita cuando B5-I3 necesite cambios; queda prohibido modificar silenciosamente contratos cerrados de M3;
- producir antes de cerrar B1 un **mapa de responsabilidades cognitivas** que asigne cada responsabilidad V2 a rol + unidad cognitiva concreta (skill/prompt/capability) existente o a una brecha técnicamente demostrada; queda prohibido cerrar el mapa usando solo `RESEARCH_AND_CURATION` como contenedor genérico.

### Trabajo de IA

Ninguno necesario para completar el núcleo contractual salvo fixtures cognitivos sintéticos mínimos de prueba.

### Trabajo humano

Resolver solo una decisión funcional que aparezca como material y no esté ya cerrada.

### Tests

- schemas nuevos y extendidos;
- compatibilidad histórica;
- validación de estados/transiciones V2;
- ausencia de default silencioso `target_final_works=3`;
- protección de selección manual/bindings;
- impedir cambio post-deep del conjunto manual sin nueva decisión o delegación válida;
- exigir que cualquier sustituta complete estados de investigación/fidelidad requeridos antes del cierre;
- rechazo de campos técnicos producidos como autoridad por IA;
- prueba de separación Research/Narrative;
- separación estructural obra/realidad;
- protección del path `.agents/skills/tests-validacion-cierre/`;
- fuente sugerida por IA sin recuperación real no puede pasar a `CONSULTED/VERIFIED/EVIDENCE`;
- matriz de estados ortogonales sin mega-enum combinado;
- guard anti-loop/no-progress detiene un ciclo sintético sin declarar suficiencia;
- consumer-contract tests o fixtures que demuestren compatibilidad explícita Research V2 → B5-I3 legacy/versionado;
- mapa de responsabilidades cognitivas completo y sin necesidad no justificada de nuevos agentes.

### Revisión funcional requerida

Si B1 modifica contratos que cambian significado metodológico, Equipo 02/Investigación revisan semántica; Equipo 04 mantiene decisión de implementación técnica.

### Cierre

`B1_CONTRACT_BOUNDARY=PASS` con estados ortogonales definidos, frontera de evidencia formalizada, guard operacional especificado, mapa de responsabilidades cognitivas cerrado y compatibilidad histórica + consumer-contract con B5-I3 demostrados, sin activar ejecución de producto.

---

## B2 — Plan, fenómeno, discovery e investigación base profesional

### Objetivo

Implementar de forma persistente y recuperable:

```text
ResearchPlan
→ mapa inicial
→ investigación base profesional del fenómeno
↕
DiscoveryPool
→ filtro
→ BaseResearchPool
→ investigación base profesional de obras
→ fidelidad preliminar
→ suficiencia inicial
→ tesis provisional
→ comparativa investigativa
```

### Trabajo de software

- preparar payloads cognitivos por etapa;
- resolver IDs, versions, lineage y bindings;
- persistir artefactos por etapa;
- validar outputs cognitivos;
- registrar risks/gaps/preliminary fidelity;
- separar y trazar evidence types;
- registrar provenance de fuentes recuperadas;
- soportar detección determinista de duplicados exactos;
- calcular siguiente estado;
- soportar recovery e invalidación focal;
- materializar `ResearchStopDecision` iterativo por ámbito;
- usar `target_final_works × 3` solo como objetivo orientativo del BaseResearchPool, nunca como quota gate;
- preservar discovery como pool dinámico separado;
- no avanzar a selección si investigación base profesional no cumple criterios funcionales de suficiencia;
- toda búsqueda/fetch solicitada cognitivamente debe ejecutarse mediante software y producir artefacto/provenance antes de poder ser consumida como evidencia;
- aplicar guard anti-loop/no-progress a scopes iterativos y detener en `STOP_LOCAL/HUMAN_REVIEW` cuando no exista progreso operacional;
- permitir implementación secuencial de fenómeno/discovery; ninguna concurrencia real es requisito de B2.

### Trabajo de IA

- descomposición cognitiva del ResearchPlan;
- mapa inicial del fenómeno;
- investigación base profesional del fenómeno;
- discovery sustantivo de obras;
- filtro cognitivo de posibilidades;
- investigación base profesional de obras;
- evaluación preliminar de fidelidad;
- evaluación de calidad/adecuación de fuentes para claims;
- detección de rivales, contradicciones y gaps;
- evaluación de suficiencia por ámbito;
- formulación de tesis provisional después de base suficiente;
- identificación de claims externos y obras que se vuelven materiales para profundización;
- comparativa investigativa no narrativa.

### Especialistas temporales

Pueden activarse aquí si una pregunta, claim, contexto o interpretación material lo requiere. No esperar a B3.

### Trabajo humano

- aceptar/modificar recomendación 3/4/5 o delegar explícitamente;
- resolver ambigüedad de intención solo si cambia materialmente una decisión.

### Skills/prompts de producto

Las skills/prompts afectados deben recibir revisión metodológica del Equipo 02/Investigación sobre calidad de instrucciones antes del cierre del bloque.

### Cierre

La investigación base puede interrumpirse y reanudarse sin perder lineage ni repetir trabajo válido; produce:

- fenómeno suficientemente mapeado para esta fase;
- candidatas defendibles con base profesional;
- fidelidad preliminar trazable;
- ResearchStop por ámbitos;
- tesis provisional sustentada y abierta a refutación;
- targets de profundización identificados tanto para fenómeno real como para obras;
- comparativa sin decisiones narrativas.

---

## B3 — Selección, investigación profunda y cierre cognitivo

### Objetivo

Implementar:

```text
selección humana/delegada
→ profundización de claims materiales del fenómeno real
  + profundización de obras seleccionadas
→ fidelidad profunda de obras
→ claims/evidencia/rivales/límites + carga probatoria proporcional
→ reevaluación post-deep del conjunto de obras
→ resolución o tratamiento suficiente de gaps
→ síntesis
→ tesis refinada
```

### Trabajo de software

- materializar `HumanDecision`/`DelegationDecision` según flujo existente;
- bindear exactamente las obras seleccionadas;
- impedir sustitución silenciosa de obras seleccionadas manualmente;
- registrar alcance exacto de delegación y permitir sustitución automática solo dentro de él;
- abrir solo dossiers de obras elegidas para profundización y scopes de claims externos materiales;
- rutear por separado profundización de fenómeno real y profundización de obras, manteniendo sus evidencias diferenciadas;
- rutear riesgos de `APTA_CON_RIESGOS` a investigación profunda;
- propagar restricciones de `APROBADA_CON_LIMITES`;
- persistir claims, naturaleza/fuerza relevante, base de suficiencia y source refs de forma stage-neutral;
- materializar que la carga probatoria fue evaluada sin convertirla en score determinista;
- registrar reevaluación post-deep del conjunto y sus recomendaciones/decisiones;
- impedir que una reevaluación cambie una selección manual sin nueva decisión o delegación;
- si entra una sustituta, reabrir solo los estados de investigación/fidelidad que esa sustituta necesite;
- soportar invalidación focal si cambia obra, claim, fuente, decisión, conjunto o tesis;
- controlar retorno de `MAS_INVESTIGACION_REQUERIDA` al gap concreto;
- materializar ResearchStop iterativo/focal;
- trazar cambios entre tesis provisional y refinada;
- mantener separadas evidencias de obra y realidad;
- aplicar la misma frontera formal de adquisición para cualquier evidencia nueva de profundización;
- aplicar guard anti-loop/no-progress a reaperturas focales;
- permitir ejecución secuencial de deep fenómeno/deep obras; concurrencia real solo con versionado/join/stale/merge/invalidation explícitos.

### Trabajo de IA

- selección delegada como optimización del conjunto, cuando exista delegación válida;
- profundización de claims materiales del fenómeno real;
- profundización de obras seleccionadas orientada al uso previsto;
- evaluación de evidencia proporcional a la fuerza/alcance del claim;
- fidelidad profunda;
- claims sustantivos;
- valoración de calidad e independencia material de fuentes;
- contradicciones y explicaciones rivales;
- determinación de tratamiento suficiente de controversias;
- reevaluación post-profundización del conjunto por aporte diferencial, cobertura, redundancia, contraste, límites y perspectivas faltantes;
- recomendación investigativa de mantener/eliminar/sustituir/reducir cuando corresponda, sin diseñar narrativa;
- especialistas temporales cuando una brecha concreta lo justifique;
- síntesis;
- tesis refinada y, cuando exista, alternativa defendible;
- explicación de qué cambió respecto a la tesis provisional.

### Trabajo humano

- selección cuando el modo sea USER_SELECTION;
- resolución cuando una obra manualmente elegida falle o cuando la reevaluación post-deep recomiende cambiar el conjunto;
- confirmación de eliminación/sustituta/reducción o delegación explícita de esa decisión;
- ninguna microaprobación innecesaria.

### Skills/prompts de producto

Revisión metodológica obligatoria cuando se cambien instrucciones de profundización del fenómeno real, investigación profunda de obras, carga probatoria de claims, fidelidad, reevaluación del conjunto, selección delegada, síntesis o tesis.

### Cierre

Paquete investigativo profundo completo y trazable: claims materiales del fenómeno real profundizados proporcionalmente, obras profundamente investigadas, conjunto post-deep reevaluado y cualquier cambio debidamente decidido; preparado para auditoría independiente sin decisiones narrativas B5-I3.

---

## B4 — Auditoría independiente y RESEARCH_READY

### Objetivo

Cerrar investigación con independencia verificable y handoff técnico explícito.

### Trabajo de software

- reutilizar `IndependentResearchAudit` y su verificación de independencia;
- verificar artefactos/versiones/checksums auditados;
- consolidar ResearchStopDecision material sin reducirlo a un único checkpoint histórico;
- crear y validar ResearchReadyManifest;
- impedir cierre ante blockers;
- propagar limitaciones estructuradas hacia B5-I3;
- rechazar dependencias stale/invalidated;
- habilitar handoff de solo lectura hacia narrativa;
- conservar audit trail de decisiones humanas/delegadas y sustituciones.

### Trabajo de IA

Auditoría semántica independiente sobre:

- cobertura del ResearchPlan;
- suficiencia;
- fidelidad;
- claims/evidencia;
- calidad/independencia de fuentes;
- correspondencia entre fuerza del claim y exigencia de evidencia;
- suficiencia de profundización de claims materiales del fenómeno real;
- gaps materiales;
- sesgo de confirmación;
- contradicciones/rivales;
- separación obra/realidad;
- evolución tesis provisional→refinada;
- selección delegada como conjunto;
- reevaluación post-deep del conjunto de obras y tratamiento de redundancias/perspectivas faltantes;
- ausencia de sustitución silenciosa en selección manual;
- límites y restricciones;
- razonabilidad metodológica para intended use.

### Trabajo humano

Revisar únicamente blockers o decisiones reservadas que la metodología no permita delegar.

### Cierre

Uno de estos resultados semánticos queda materializado y sustentado:

```text
RESEARCH_READY
RESEARCH_READY_WITH_LIMITATIONS
NOT_RESEARCH_READY
```

sin que el resultado autorice por sí mismo uso productivo, IA real o publicación.

---

## B5 — Integración, CLI, harness, E2E y documentación

### Objetivo

Demostrar la vertical completa con software real y cognición sintética controlada.

### Trabajo de software

- extender CLI existente; no crear una CLI paralela;
- reutilizar harness existente;
- probar persistencia/recovery/invalidation/lineage/bindings/checksums;
- probar ResearchStop iterativo y reopening focal;
- probar protección de selección manual;
- probar delegación y sustitución dentro de scope;
- probar separación work/external evidence;
- probar thesis lineage;
- ejecutar E2E sintético desde intake hasta ResearchReadyManifest;
- verificar handoff válido a B5-I3 sin ejecutar guion;
- ejecutar consumer-contract tests Research V2 → B5-I3, incluyendo restricciones downstream, lineage y ausencia de dependencias narrativas retiradas;
- demostrar que cualquier adaptación de B5-I3 usa versionado/adaptador/migración explícitos y no modificación silenciosa de M3;
- probar que IA A → Software validate/persist → IA B es obligatorio en harness y que no existe pase directo IA→IA entre etapas;
- probar que una fuente no recuperada realmente no puede adquirir estatus de evidencia;
- probar que un loop/no-progress sintético termina por guard operacional;
- si se usa concurrencia real, probar join/versiones/stale/merge/race handling; si no, documentar ejecución secuencial válida;
- actualizar workflow/documentación y diagramas solo después de que el flujo ejecutable coincida con ellos.

### Trabajo de IA

Fixtures/respuestas cognitivas sintéticas suficientemente realistas para demostrar contratos y routing. No IA real.

### Trabajo humano

OWNER review de evidencia final.

### Cierre técnico esperado

```text
RESEARCH_VERTICAL_E2E=PASS
```

Este resultado demuestra **integración técnica**, no calidad metodológica real de investigación.

No equivale a:

```text
REAL_AI_EXECUTION=YES
AUTHORIZED_FOR_PRODUCT_USE=YES
REAL_RESEARCH_VERTICAL=DEMONSTRATED_REAL
REAL_RESEARCH_QUALITY=DEMONSTRATED
P2_REAL_EXECUTION_NOW=YES
PLAN011_M7=COMPLETED
```

La calidad metodológica real deberá validarse posteriormente mediante al menos una ejecución de investigación real y evaluación humana independiente, en una misión futura separadamente autorizada.

---

# 17.1 Descomposición operativa de PLAN012

La ejecución de PLAN012 se materializa en siete misiones secuenciales. Esta descomposición organiza el trabajo técnico sin modificar la metodología funcional aprobada ni autorizar por sí misma ninguna misión:

```text
M1 — B1
Inventario + diseño contractual + estados ortogonales + responsabilidades cognitivas.

M2 — B1
Contratos mínimos + frontera Research/B5-I3 + compatibilidad/versionado.

M3 — B2
ResearchPlan + investigación base fenómeno + discovery + base research obras + fidelidad preliminar.

M4 — B3
Selección humana/delegada + deep research fenómeno/obras + fidelidad profunda.

M5 — B3
Claims + evidencia + rivales + gaps + reevaluación del conjunto + tesis refinada.

M6 — B4
Auditoría independiente + ResearchReadyManifest + gate RESEARCH_READY.

M7 — B5
CLI + persistence/recovery/invalidation + harness + E2E sintético + compatibilidad B5-I3 + documentación + cierre.
```

En la materialización actual solo quedan definidos documentalmente B1, M1 y M2. M1 debe cerrar el inventario real antes de que M2 pueda proponer contratos o adaptaciones concretas. Ninguna misión se considera ejecutable sin autorización expresa y materializada en la autoridad viva.

# 18. Estrategia de agentes y skills

PLAN012 no parte de crear más agentes.

Regla de decisión:

```text
¿es determinista/repetible?
→ software / script / gate

¿es procedimiento técnico reutilizable?
→ skill de ingeniería existente o extensión justificada

¿es cognición recurrente dentro de responsabilidad existente?
→ skill/prompts de producto existentes o extendidos

¿es especialidad temporal por claim/gap?
→ capability/contexto/skill/subagente temporal según brecha real

¿requiere autoridad realmente diferenciada y veto independiente?
→ evaluar rol/agente separado solo con brecha demostrada y autorización
```

La auditoría independiente reutiliza la infraestructura y contratos de auditoría existentes salvo brecha demostrada.

Los especialistas de investigación son temporales por necesidad cognitiva y no implican crear un agente permanente por cada especialidad.

## 18.1 Mapa de responsabilidades cognitivas obligatorio antes de B2

B1 debe cerrar una tabla de asignación explícita antes de autorizar B2. La disposición inicial a comprobar contra registries, prompts y skills canónicos es:

| Responsabilidad V2 | Reutilización prevista antes de crear nada |
|---|---|
| Research planning | `RESEARCH_AND_CURATION` + extender/reconciliar `skill_research_tema_y_obras` |
| Investigación base/profunda del fenómeno real | `RESEARCH_AND_CURATION` + `skill_research_tema_y_obras` |
| Discovery y base research de obras | `RESEARCH_AND_CURATION` + `skill_research_tema_y_obras` |
| Comparativa/selección investigativa | reconciliar `skill_curation_obras` retirando decisiones narrativas |
| Fidelidad preliminar/profunda | responsabilidad de investigación usando skills/prompts existentes extendidos; crear skill separada solo si B1 demuestra brecha reutilizable real |
| Síntesis / tesis provisional-refinada | reutilizar `skill_sintesis_tesis`, moviendo/reconciliando su autoridad hacia investigación sin duplicarla |
| QA/suficiencia semántica | reutilizar/extender `skill_qa_brief_research` y/o `skill_auditar_suficiencia_semantica_b5_i2` según inventario de alcance |
| Auditoría independiente final | reutilizar infraestructura `IndependentResearchAudit` y rol/auditor existente que pueda preservar independencia; no crear auditor nuevo sin brecha demostrada |
| Especialista temporal | reutilizar runtime/capability/contexto temporal autorizado; no agente permanente por especialidad |

Esta tabla es un **punto de partida técnico**, no una orden de crear o renombrar assets. B1 debe verificar registries y contratos reales y emitir para cada fila:

```text
REUSE
EXTEND
MOVE/RECONCILE
CREATE_ONLY_IF_GAP
```

No basta con escribir `RESEARCH_AND_CURATION` en todas las filas. Aunque varias responsabilidades compartan el mismo rol/runtime, B1 debe identificar para cada una la **unidad cognitiva concreta** que la instruye y limita: skill existente, sección/version de prompt, capability o paquete temporal. El objetivo es reutilizar infraestructura sin convertir `RESEARCH_AND_CURATION` en un prompt monolítico que haga planificación, discovery, fidelidad, síntesis y auditoría sin fronteras explícitas.

Compartir rol/runtime **sí está permitido**. Compartir una instrucción cognitiva indiferenciada para responsabilidades materialmente distintas **no**.

Además, el harness debe demostrar el patrón:

```text
IA etapa A
↓
SOFTWARE valida / bindea / persiste
↓
IA etapa B
```

y bloquear cualquier ruta donde outputs cognitivos pasen directamente:

```text
IA A → IA B → IA C
```

sin retorno al control del software.

---

# 19. Tests y validación: qué es software y qué es semántica

Equipo 04 decide la estrategia técnica de tests.

## 19.1 Casos deterministas aptos para tests automáticos

Ejemplos:

- schema válido/inválido;
- transición permitida/prohibida;
- decisión manual que no puede sustituirse silenciosamente;
- cambio post-deep de conjunto manual sin nueva decisión/delegación;
- sustituta que intenta cerrar sin completar investigación/fidelidad requerida;
- ausencia de reevaluación post-deep requerida antes del cierre;
- binding stale;
- checksum incorrecto;
- dependencia invalidada;
- ausencia de manifest requerido;
- `target_final_works` sin default automático;
- separación de tipos de evidencia en contrato;
- return route focal;
- auditor no independiente cuando el contrato exige independencia;
- source ref sin artefacto de recuperación real;
- loop A→B→A o repetición sin evidencia nueva;
- estados ortogonales incompatibles o intento de mega-enum combinado;
- consumer contract B5-I3 incompatible;
- ruta cognitiva IA→IA sin persistencia/validación software intermedia.

## 19.2 Casos semánticos

Ejemplos:

- si una interpretación es demasiado fuerte;
- si una candidata merece `APTA_CON_RIESGOS`;
- si una fuente es suficiente para un claim controvertido;
- si la evidencia permite asociación pero no causalidad/generalización;
- si la profundización del fenómeno real es suficiente para un claim material;
- si una selección delegada es complementaria;
- si el conjunto sigue siendo complementario después de profundización;
- si una controversia recibió tratamiento suficiente.

No deben fingirse como verdad universal mediante `assert` puramente determinista.

Los equipos funcionales pueden definir **casos de aceptación semántica y resultados esperados**; Equipo 04 decide si se prueban mediante fixtures, evaluación de capability, harness, auditoría semántica u otro mecanismo técnico apropiado.

---

# 20. Gates y evidencia

Cada bloque debe cerrar con evidencia proporcional al riesgo.

Mínimo:

- misión/alcance autorizado;
- `git status --short`;
- `git diff --name-status` y diff relevante;
- validaciones de schema afectadas;
- tests focales;
- compatibilidad histórica cuando se toquen contratos existentes;
- revisión metodológica cuando se toquen skills/prompts de investigación;
- `git diff --check`;
- verificación de paths protegidos;
- trazabilidad input → cambios → tests → conclusión;
- para B1/B5, evidencia de consumer-contract Research V2 → B5-I3;
- para B2/B3/B5, evidencia de frontera de adquisición y guard anti-loop;
- para B1, mapa de estados ortogonales y mapa de responsabilidades cognitivas.

No declarar `PASS` por descripción del agente. El reporte no sustituye el diff ni los tests.

Cuando una revisión encuentre defecto material debe aplicarse doble RCA:

```text
causa de producción
+
causa de escape
```

antes de considerar la corrección cerrada.

---

# 21. Límites y no-objetivos

PLAN012 no autoriza:

- IA real;
- P2 real;
- producto real;
- publicación;
- B5.5/B6/B7;
- reabrir PLAN011 M1/M2/M3;
- crear otro runtime de IA;
- crear un nuevo framework de agentes;
- crear un agente permanente por cada especialidad;
- crear otro sistema de autorización;
- crear storage/provenance/observability paralelos;
- crear un lifecycle general paralelo;
- crear una base vectorial o embeddings sin brecha demostrada;
- crear memoria compleja anticipada;
- imponer cantidades rígidas de fuentes;
- imponer una tabla minutos→obras sin calibración real;
- imponer `target_final_works=3` por omisión;
- convertir `target_final_works × 3` en quota gate;
- convertir calidad de fuentes en score rígido universal;
- convertir fuerza del claim o carga probatoria en score rígido universal;
- imponer una taxonomía universal cerrada de claims;
- crear un segundo motor de selección solo para la reevaluación post-deep;
- meter decisiones de Viewer Journey/arquitectura narrativa dentro de investigación;
- sustituir silenciosamente una obra seleccionada manualmente;
- obligar a resolver artificialmente toda controversia;
- degradar semántica para satisfacer tests automáticos;
- tratar una fuente generada/recordada por IA como consultada sin recuperación software real;
- introducir concurrencia real por defecto solo porque el flujo funcional tenga ramas paralelas;
- construir un mega-enum que mezcle lifecycle, selección, fidelidad, suficiencia, validez y tesis;
- modificar silenciosamente contratos cerrados de M3/B5-I3 bajo la etiqueta de “compatibilidad”.

---

# 22. Orden de ejecución y autoridad

PLAN012 queda como roadmap v1.3: funcionalmente aprobado por Equipo 02/Investigación y técnicamente aprobado por auditoría externa de software/arquitectura agéntica. B1, M1 y M2 quedan cerrados con aprobación del OWNER. La siguiente acción requiere autorización expresa del OWNER para M3.

La secuencia será:

```text
Auditoría técnica externa / Equipo 04
revisión final de ajustes v1.3
↓
OWNER aprueba roadmap técnico
↓
OWNER autoriza bloque concreto
↓
se materializa misión + authority + MissionAuthorization + scope
↓
preflight
↓
implementación
↓
validación proporcional
↓
revisión funcional/técnica requerida por riesgo
↓
OWNER decide cierre/continuación
```

No se autoriza automáticamente B2 por cerrar B1, ni B3 por cerrar B2.

---

# 23. Estado del roadmap tras cierre de B1

```yaml
FUNCTIONAL_REVIEW: APPROVED
TECHNICAL_REVIEW: APPROVED
PLAN_012_STATUS: B1_CLOSED
PLAN_012_VERSION: 1.3
PLAN_012_CURRENT_BLOCK: B1
PLAN_012_CURRENT_MISSION: NONE
PLAN_012_IMPLEMENTATION_AUTHORIZED: NO
PLAN_012_REAL_AI_EXECUTION: NO
PLAN_012_PRODUCT_USE_AUTHORIZED: NO
PLAN_012_P2_REAL_EXECUTION: NO
PLAN_012_B5_5_AUTHORIZED: NO
PLAN_012_B6_AUTHORIZED: NO
PLAN_012_B7_AUTHORIZED: NO
B1: CLOSED
B1_M1: CLOSED_OWNER_APPROVED
B1_M2: CLOSED_OWNER_APPROVED
PLAN_012_M3_STATUS: NOT_AUTHORIZED
PLAN_012_RESEARCH_VERTICAL_E2E: NOT_DEMONSTRATED
PLAN_012_REAL_RESEARCH_QUALITY: NOT_DEMONSTRATED
```

Estado operativo de B1:

```text
B1_STATUS = CLOSED
B1_M1_STATUS = CLOSED_OWNER_APPROVED
B1_M2_STATUS = CLOSED_OWNER_APPROVED
IMPLEMENTATION = NOT_AUTHORIZED
REAL_AI = NO
PRODUCT_USE = NO
P2_REAL = NO
B5_5 = NO
B6 = NO
B7 = NO
COMMIT = NO
PUSH = NO
```

Siguiente acción permitida:

```text
OWNER_AUTHORIZATION_REQUIRED_FOR_M3
```

sin iniciar implementación hasta que dicha misión exista en la autoridad viva.

---

# 24. Criterio final de coherencia

Cada decisión de implementación de PLAN012 debe poder responder correctamente estas tres preguntas:

### Investigación

> ¿El sistema profundiza proporcionalmente lo material tanto en el fenómeno real como en las obras, ajusta la evidencia a la fuerza de cada claim y confirma después de la profundización que el conjunto de obras sigue siendo defendible, complementario y trazable?

### Frontera

> ¿B5-I3 recibe conocimiento investigado y restricciones, pero conserva la autoridad de decidir cómo convertir ese conocimiento en un video?

### Arquitectura técnica

> ¿Toda evidencia usada fue realmente recuperada y bindeada por software, cada salto cognitivo vuelve al control de software, los loops pueden detenerse sin falsear suficiencia, los estados permanecen ortogonales y el handoff V2→B5-I3 está versionado y probado?

Si una modificación permite investigación superficial, traslada decisiones narrativas a Research o rompe estas garantías técnicas, no cumple PLAN012 aunque el resto de los tests pase.
