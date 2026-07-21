# PLAN-001 / B5 — Profesionalización del diseño editorial

**Plan rector:** [`../001_reestructuracion_motor_agentico_editorial_y_harness.md`](../001_reestructuracion_motor_agentico_editorial_y_harness.md)  
**Control operativo:** [`../001_CONTROL_OPERATIVO.md`](../001_CONTROL_OPERATIVO.md)  
**Versión derivada:** `PLAN-001 v1.3`  
**Estado inicial:** `PLANNED`  
**Dependencia:** `B3–B4`  
**Siguiente tramo:** `B5.5`  
**Gate resumido:** Diseño editorial completo aprobado

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

- §2 Resultado editorial esperado
- §3 Flujo objetivo
- Contratos B1-C2 a B1-C8

---

## 1. Objetivo

Convertir brief, investigación, evidencia, tesis, curación, packaging, recorrido y outline en un diseño profesional antes de redactar.

## 2. Misiones

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

### B5-M6 — Audiencia concreta e hipótesis temprana de promesa y packaging

Antes del outline debe existir una audiencia concreta del episodio derivada del `EditorialProfile` aprobado.

Debe definir:

- qué persona concreta se busca alcanzar;
- qué conocimiento previo se presupone;
- qué tensión reconoce;
- por qué la obra o pregunta le importa;
- qué expectativa no debe generarse;
- qué versión de perfil y brief la sustentan.

La hipótesis temprana debe incluir:

- promesa de clic;
- título de trabajo;
- concepto de miniatura;
- expectativa del espectador;
- diferenciador;
- riesgo de sobrepromesa.

La autoridad funcional se distribuye así:

```text
Equipo 03
→ define o aprueba la audiencia concreta,
  la promesa visible y la hipótesis de packaging.

Equipo 02
→ valida que la tesis, la evidencia y la arquitectura
  puedan cumplir honestamente esa promesa.
```

El Equipo 02 no puede aprobar unilateralmente el packaging. El Equipo 03 no puede modificar unilateralmente la tesis.

Un cambio sustancial en audiencia concreta, promesa visible, tesis o conflicto central invalida los artefactos dependientes.

### B5-M7 — Tesis refinada

Después de evidencia, análisis narrativo y humano, curación final y packaging:

- tesis defendible;
- matiz;
- objeción principal;
- idea que no debe simplificarse;
- transformación final;
- relación con promesa.

### B5-M8 — Recorrido del espectador

Planificar el cambio de conocimiento, emoción y pregunta en cada bloque.

No se usa para fabricar retención artificial, sino para comprobar avance real.

### B5-M9 — Diseño de apertura

Debe revisar:

- punto de máximo interés;
- pregunta central;
- contexto mínimo;
- promesa concreta;
- sustancia en el primer minuto;
- ausencia de introducción larga;
- suspensión no artificial;
- primera transición.

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
- PackagingHypothesis tiene aprobación funcional del Equipo 03;
- Producto Guion confirmó que la tesis y la arquitectura pueden cumplir la promesa;
- PackagingHypothesis no sobrepromete;
- ViewerJourney muestra transformación;
- apertura y cierre tienen contrato;
- outline y presupuesto están aprobados;
- Producto considera que el diseño puede producir un buen guion.
```

---
