# PLAN-001 / B6 — Redacción, ensamblaje, edición y verificación

**Plan rector:** [`../001_reestructuracion_motor_agentico_editorial_y_harness.md`](../001_reestructuracion_motor_agentico_editorial_y_harness.md)  
**Control operativo:** [`../001_CONTROL_OPERATIVO.md`](../001_CONTROL_OPERATIVO.md)  
**Versión derivada:** `PLAN-001 v1.3`  
**Estado inicial:** `PLANNED`  
**Dependencia:** `B5.5`  
**Siguiente tramo:** `B7`  
**Gate resumido:** Candidato final coherente y trazable

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

- §7.10–7.13 Principios de escritura y control
- §11 Versionado
- Contratos B1-C9 a B1-C22

---

## 1. Objetivo

Producir un candidato final coherente mediante redacción fraccionada con memoria global, ensamblaje reproducible, edición profesional y controles de evidencia y originalidad.

## 2. Misiones

### B6-M1 — Presupuesto de duración y palabras

Debe considerar:

- duración objetivo;
- ritmo configurable;
- pausas;
- complejidad;
- apertura y cierre;
- notas no narradas;
- tolerancia permitida.

El reparto no será uniforme por defecto.

### B6-M2 — Context pack global

Cada bloque recibe:

- perfil y versión;
- brief;
- tesis;
- packaging hypothesis;
- viewer journey;
- outline;
- opening/closing design;
- presupuesto;
- fuentes autorizadas;
- referencia al análisis narrativo y humano de los materiales;
- claims;
- bloques previos resumidos;
- repeticiones prohibidas;
- función del bloque siguiente.

### B6-M3 — Redacción por bloques

Antes de redactar el bloque de apertura debe ejecutarse un preflight contra `OpeningDesign`. Una apertura que contradiga la promesa, retrase el interés o carezca de sustancia temprana no puede continuar al ensamblaje.

Cada bloque debe:

- cumplir su función;
- aportar información nueva;
- respetar presupuesto;
- usar solo evidencia autorizada;
- utilizar el análisis narrativo y humano aprobado;
- preparar el siguiente;
- mantener voz y oralidad;
- no incluir marcadores técnicos visibles en la entrega final.

La redacción debe convertir el diseño en narración y argumentación orgánicas mediante, cuando el material lo justifique:

- escenas concretas;
- acciones reveladoras;
- detalles significativos;
- contradicción;
- subtexto;
- causalidad;
- revelación progresiva;
- variación de ritmo;
- alternancia natural entre relato, análisis y reflexión;
- transiciones orgánicas;
- síntesis sin simplificación;
- emoción sin dramatismo prefabricado;
- reflexión sin falsa profundidad.

No se permite que todos los bloques repitan mecánicamente una secuencia fija como:

```text
escena
→ explicación
→ pregunta
→ ejemplo
→ reflexión
```

La cantidad de contexto narrativo debe ser suficiente para comprender el argumento sin convertir el guion en un resumen extenso de la obra.

### B6-M4 — Ensamblaje determinista

El ensamblaje debe:

- usar orden del manifest;
- verificar versiones y hashes;
- detectar bloques ausentes o duplicados;
- separar texto narrado de notas;
- generar candidato reproducible;
- producir manifest de ensamblaje.

### B6-M5 — Edición de desarrollo

Debe detectar y corregir:

- repetición conceptual;
- bloque sin función;
- secuencia débil;
- obra redundante;
- causalidad rota;
- promesa incumplida;
- clímax prematuro;
- cierre no preparado;
- desequilibrio de duración;
- pérdida de tesis.

Produce `EditorialEditReport` y nueva versión.

### B6-M6 — Edición de línea y oralidad

Debe revisar:

- claridad;
- concreción;
- musicalidad;
- longitud de frases;
- respiración;
- muletillas;
- lenguaje inflado;
- transiciones;
- tono;
- facilidad de locución.

### B6-M7 — Read-Aloud Review

Debe identificar:

- frases difíciles de pronunciar;
- subordinadas acumuladas;
- sujetos confusos;
- términos que requieren pronunciación;
- pausas antinaturales;
- párrafos sin respiración;
- monotonía;
- densidad excesiva;
- transiciones que fallan al escucharse.

Puede ejecutarse mediante lectura humana, TTS de prueba o revisión especializada. La evidencia debe declarar el método.

### B6-M8 — Verificación factual e interpretativa

Debe controlar:

- hechos;
- nombres y fechas;
- citas y paráfrasis;
- escenas;
- intención atribuida;
- causalidad psicológica;
- diagnósticos implícitos;
- diferencias entre hecho, lectura e hipótesis;
- claims sin respaldo;
- citas textuales fuera de política;
- atribuciones que deberían aparecer en narración;
- ideas de terceros presentadas como propias;
- referencias innecesariamente académicas que dañen la oralidad.

La verificación debe aplicar `citation_style`, `attribution_policy`, `quotation_policy` y `source_visibility` sin convertir el guion en un artículo académico.

### B6-M9 — Originalidad y transformación de fuentes

Producir `SourceTransformationAndOriginalityReview` con:

- frases distintivas;
- orden de ideas;
- ejemplos reutilizados;
- dependencia de una fuente;
- atribución de interpretaciones;
- similitud estructural;
- imitación de voz;
- legitimidad transformativa.

El objetivo no es evadir detectores. Es proteger autoría editorial legítima.

### B6-M10 — Candidato final y entregables

Generar, como mínimo:

```text
final_script_clean.md
final_script_annotated.md
claims_ledger.json
metrics.json
known_limitations.md
final_delivery_manifest.json
system_review.json
product_review.json
owner_report.md
```

`final_script_clean.md` no contiene:

- gates;
- etiquetas del outline;
- instrucciones de agentes;
- metadatos;
- marcadores de retención visibles;
- comentarios técnicos.

## 3. Gate B6

```text
PASS si:
- todos los bloques cumplen contrato;
- ensamblaje es reproducible;
- edición de desarrollo y línea tienen reportes separados;
- read-aloud review se ejecutó;
- claims están trazados;
- originalidad fue revisada;
- candidato final y entregables están completos;
- no existe aprobación humana todavía sobre una versión anterior.
```

---
