# PLAN DETALLADO DE EJECUCIÓN — R0 POST-P08 v4

**Proyecto:** Más Allá del Guion
**Plan maestro vigente:** `plans/plan_001/B0_1_roadmap_implementacion_post_p08.md`
**Bloque autorizado:** `R0 — Cierre documental y recuperación`
**Naturaleza:** plan de ejecución documental y de gobernanza; no es una misión operativa
**Autoridad única de estado vivo:** `plans/001_CONTROL_OPERATIVO.md`
**AUTHORIZED_SCOPE:** `R0_PLANNING_ONLY`
**IMPLEMENTATION_AUTHORIZED:** `NO`
**R1_IMPLEMENTATION:** `NOT_AUTHORIZED`
**R2_TO_R9:** `NOT_AUTHORIZED`
**CODEX_MISSIONS_PREPARED:** `NO`

---

## 1. Objetivo exacto

R0 debe converger y sanear la documentación posterior a P-08 e IR-0 antes de cualquier implementación técnica, de modo que:

1. `plans/001_CONTROL_OPERATIVO.md` sea la única autoridad normativa de estado vivo;
2. el roadmap post-P08 gobierne únicamente planeación, dependencias, gates y criterios de autorización;
3. los artefactos IR-0 gobiernen únicamente trazabilidad y planeación técnica;
4. Plan 003 deje de operar como autoridad temporal y quede histórico, cerrado y no normativo;
5. desaparezcan referencias vigentes a Misión 01E y autorizaciones anteriores incompatibles;
6. se restauren los defectos textuales y estructurales detectados en `AGENTS.md` y `B5_PRE_SCRIPT_FOUNDATION.md` sin alterar requisitos funcionales;
7. la matriz IR-0 v3 y el plan técnico IR-0 se incorporen como copias binarias exactas, con procedencia verificable;
8. el roadmap se incorpore mediante canonicalización controlada, registrando hash de origen y hash canónico;
9. R1 permanezca no autorizado al cerrar R0;
10. la evidencia de cierre demuestre que no se modificaron contratos, schemas, agentes, prompts, skills, gates, workflows, runtime ni pruebas técnicas.

R0 no implementa capacidades de investigación, no activa R1 y no demuestra una vertical editorial.

---

## 2. Resultado normativo esperado

Al cerrar R0, el repositorio debe expresar de forma inequívoca:

```text
CURRENT_LIVE_STATE_AUTHORITY:
plans/001_CONTROL_OPERATIVO.md

MASTER_IMPLEMENTATION_ROADMAP:
plans/plan_001/B0_1_roadmap_implementacion_post_p08.md

ROADMAP_STATE_SNAPSHOT:
NON_NORMATIVE_REFERENCE_ONLY

PLAN_003_AUTHORITY_STATUS:
HISTORICAL_NON_NORMATIVE

IR0_TRACEABILITY_BASELINE:
docs/reconciliation/p08/2026-08-05/ir0_matriz_investigacion_editorial_post_p08_v3_2026-08-05.xlsx

IR0_TECHNICAL_PLANNING_INPUT:
docs/reconciliation/p08/2026-08-05/ir0_plan_tecnico_investigacion_editorial_post_p08_v2_2026-08-05.md

IR0_FUNCTIONAL_DECISIONS_REQUIRED:
0

PARALLEL_LIVE_STATE_SURFACES:
0

R1_IMPLEMENTATION:
REQUIRES_SEPARATE_OWNER_AUTHORIZATION

R2_TO_R9:
NOT_AUTHORIZED

IMPLEMENTATION_AUTHORIZED:
NO
```

El cierre de R0 no autoriza R1. Después de revisar la evidencia de R0, el propietario deberá emitir una autorización separada para preparar o ejecutar R1.

---

## 3. Separación obligatoria de superficies

### 3.1 Documentación de planeación

**Artefacto principal:**

```text
plans/plan_001/B0_1_roadmap_implementacion_post_p08.md
```

Gobierna:

- alcance R0→R9;
- dependencias;
- secuencia;
- gates futuros;
- criterios de autorización;
- owners funcionales y técnicos.

No gobierna:

- misión vigente;
- siguiente acción operativa;
- estado de ejecución actual;
- autorización actual de una fase;
- cierre operativo actual.

Cualquier snapshot debe declararse:

```text
NON_NORMATIVE_REFERENCE_ONLY
```

### 3.2 Estado vivo

**Única autoridad:**

```text
plans/001_CONTROL_OPERATIVO.md
```

Gobierna exclusivamente:

- bloque actual;
- misión vigente;
- siguiente acción permitida;
- autorizaciones actuales;
- bloqueos;
- inicio, cierre o reapertura de R0;
- autorización posterior de R1.

Debe modificarse obligatoriamente al iniciar R0 y al cerrarlo.

### 3.3 Artefactos IR-0

**Matriz canónica:**

```text
docs/reconciliation/p08/2026-08-05/ir0_matriz_investigacion_editorial_post_p08_v3_2026-08-05.xlsx
```

**Plan técnico canónico:**

```text
docs/reconciliation/p08/2026-08-05/ir0_plan_tecnico_investigacion_editorial_post_p08_v2_2026-08-05.md
```

Gobiernan:

- los 68 requisitos normalizados;
- clasificación IR-0;
- evidencia y componentes identificados;
- orden técnico por dependencias;
- las tres decisiones definitivas de `SCRIPT_PRODUCT`;
- vínculos de R1, R2 y R3.

No gobiernan estado vivo ni autorizan implementación.

### 3.4 Evidencia de cierre

**Ruta:**

```text
docs/reconciliation/p08/2026-08-05/r0_documentary_convergence_report_2026-08-05.md
```

Registra resultados, hashes y validaciones. No reemplaza el control operativo.

---

## 4. Dependencias reales y verificación previa obligatoria

R0 no puede comenzar hasta resolver las dependencias documentales siguientes.

### 4.1 Roadmap v3 aprobado

```text
SOURCE_NAME:
IMPLEMENTATION_ROADMAP_POST_P08_v3.md

DRIVE_ID:
1wEs_lHbX2deN5wOx6W02yVfugl8Eiofg

LOCAL_SOURCE_SHA256:
99681d9178c9393ec90b8ea73d8a4c1a06e0068368de1dd28b06920435bf7e92

SOURCE_STATUS:
AVAILABLE
```

### 4.2 Matriz IR-0 v3

```text
SOURCE_NAME:
ir0_matriz_investigacion_editorial_post_p08_v3_2026-08-05.xlsx

EXPECTED_DRIVE_FOLDER:
1GVGiO1rsLGt8S6IQTrbc09J-8Bx46LLK

DRIVE_ID:
NOT_FOUND_AT_PLAN_REVIEW

LOCAL_SOURCE_SHA256:
de00e9d8c2ed0b0129e907aec4e7c1015a1279849ca3746ecc38b63c427c0145

SOURCE_STATUS_AT_PLAN_REVIEW:
BLOCKED_UNTIL_UPLOADED_AND_ID_RECORDED

CURRENT_DOCUMENTARY_STATUS:
RESOLVED_AND_HASH_VERIFIED_IN_REPOSITORY
```

Antes de ejecutar R0 debía:

1. subirse a la carpeta de Drive indicada;
2. registrarse su Drive ID real;
3. descargarse o recuperarse desde esa fuente;
4. comprobarse SHA-256 contra el artefacto aprobado;
5. detener R0 si el hash difiere.

### 4.3 Plan técnico IR-0

Nombre exacto exigido:

```text
ir0_plan_tecnico_investigacion_editorial_post_p08_v2_2026-08-05.md
```

```text
EXPECTED_DRIVE_FOLDER:
1GVGiO1rsLGt8S6IQTrbc09J-8Bx46LLK

DRIVE_ID:
NOT_FOUND_AT_PLAN_REVIEW

LOCAL_SOURCE_SHA256:
d7d5e0f6e04d4539ba30b533f3597cf20753e3fc28ed38e9b7bd5c6ead178563

SOURCE_STATUS_AT_PLAN_REVIEW:
BLOCKED_UNTIL_UPLOADED_AND_ID_RECORDED

CURRENT_DOCUMENTARY_STATUS:
RESOLVED_AND_HASH_VERIFIED_IN_REPOSITORY
```

No debe confundirse con:

```text
plan_implementacion_investigacion_editorial_post_p08_v2_2026-08-05.md
DRIVE_ID: 1UXdAqVO-c08Sf-rN0Ey44QiP-Tj_Bt2b
TYPE: FUNCTIONAL_SOURCE_PLAN
```

Ese archivo funcional es una fuente distinta. No es alias, sustituto ni copia equivalente del plan técnico IR-0.

### 4.4 Gate de dependencias

```text
R0_DEPENDENCY_GATE:
PASS
```

solo cuando matriz y plan técnico:

- existan realmente en Drive;
- tengan Drive ID registrado;
- tengan nombre exacto;
- coincidan con los SHA-256 aprobados;
- puedan recuperarse sin conversión de formato.

---

## 5. Archivos afectados y cambios exactos

## 5.1 Archivos obligatorios

### A. `plans/001_CONTROL_OPERATIVO.md`

**Tipo:** estado vivo.
**Modificación:** obligatoria al inicio y al cierre de R0.

#### Al iniciar R0

Registrar, usando el formato canónico ya existente:

```text
CURRENT_BLOCK: R0
R0_STATUS: IN_PROGRESS
CURRENT_MISSION: <misión R0 autorizada posteriormente>
NEXT_ALLOWED_ACTION: EXECUTE_AUTHORIZED_R0_SCOPE
R1_IMPLEMENTATION: NOT_AUTHORIZED
IMPLEMENTATION_AUTHORIZED: R0_DOCUMENTARY_SCOPE_ONLY
```

Eliminar como estado vigente cualquier referencia a:

```text
HISTORICAL_MISSION_01E_PENDING_OWNER_REVIEW_MARKER
HISTORICAL_MISSION_01E_RESULT_MARKER
```

La historia de Misión 01E puede conservarse únicamente en un bloque histórico claramente no normativo.

#### Al cerrar R0

Registrar:

```text
R0_STATUS: COMPLETED_PENDING_OWNER_REVIEW
CURRENT_MISSION: NONE_PENDING_OWNER_REVIEW_OF_R0_RESULT
NEXT_ALLOWED_ACTION: OWNER_REVIEW_OF_R0_EVIDENCE
R1_IMPLEMENTATION: NOT_AUTHORIZED
IMPLEMENTATION_AUTHORIZED: NO
```

No declarar R1 preparado, iniciado ni autorizado.

### B. `plans/plan_001/B0_1_roadmap_implementacion_post_p08.md`

**Tipo:** planeación maestra.
**Acción:** canonicalización controlada desde v3.

Cambios permitidos y obligatorios:

1. usar la ruta canónica sin sufijo de versión;
2. registrar que la fuente aprobada fue v3;
3. marcar el documento como plan maestro aprobado;
4. sustituir cualquier frase que sugiera autorización automática de R1 por:

> El cierre de R0 no autoriza R1.
>
> Después de revisar la evidencia de R0, el propietario deberá emitir una autorización separada para preparar o ejecutar R1.

5. conservar:

```text
OWNER_APPROVAL_EFFECT: AUTHORIZE_R0_ONLY
R1_IMPLEMENTATION: REQUIRES_SEPARATE_OWNER_AUTHORIZATION
R2_TO_R9: NOT_AUTHORIZED
IMPLEMENTATION_AUTHORIZED: NO
```

6. conservar íntegras las tres decisiones de `SCRIPT_PRODUCT`;
7. conservar `IR0_FUNCTIONAL_DECISIONS_REQUIRED: 0`;
8. marcar snapshots como `NON_NORMATIVE_REFERENCE_ONLY`;
9. no copiar misión vigente ni siguiente acción operativa.

### C. `plans/plan_001/README.md`

**Tipo:** índice y recuperación.
**Acción:** saneamiento obligatorio.

Debe:

- enlazar el roadmap canónico;
- enlazar el control operativo como única autoridad de estado;
- enlazar la matriz y el plan técnico IR-0;
- distinguir B5_PRE, B5.5 y R0;
- retirar estados antiguos, autorizaciones activas y “siguiente acción” duplicada;
- no publicar estado vivo propio.

### D. `plans/plan_003/003_RECUPERACION_RECONCILIACION_Y_CIERRE_DE_FALSOS_POSITIVOS.md`

**Tipo:** autoridad temporal anterior.
**Acción:** cierre documental obligatorio.

Debe quedar marcado como:

```text
PLAN_003_STATUS: CLOSED_HISTORICAL
AUTHORITY_STATUS: HISTORICAL_NON_NORMATIVE
IMPLEMENTATION_AUTHORIZED: NO
SUPERSEDED_FOR_LIVE_STATE_BY: plans/001_CONTROL_OPERATIVO.md
```

Debe eliminarse o neutralizarse cualquier `IMPLEMENTATION_AUTHORIZED: YES` activo.

Puede conservarse la historia, evidencia y finalidad original, pero no puede competir con el control operativo ni con el roadmap vigente.

### E. `AGENTS.md`

**Tipo:** reglas permanentes y navegación.
**Acción:** corrección textual y estructural obligatoria y limitada.

Cambios autorizados:

- restaurar UTF-8 y letras dañadas;
- eliminar encabezados o secciones duplicadas;
- retirar estados temporales y autorizaciones históricas activas;
- conservar reglas permanentes;
- conservar rutas de recuperación;
- declarar que el estado vivo se consulta en `plans/001_CONTROL_OPERATIVO.md`;
- declarar que el roadmap gobierna planeación, no estado vivo.

Cambios prohibidos:

- alterar contratos funcionales;
- inventar políticas nuevas;
- redefinir roles;
- introducir criterios de R1.

### F. `plans/plan_001/B5_PRE_SCRIPT_FOUNDATION.md`

**Tipo:** fundamento funcional reconciliado.
**Acción:** corrección textual y estructural obligatoria y limitada.

Cambios autorizados:

- restaurar UTF-8;
- corregir mojibake y signos insertados dentro de palabras;
- reparar fences Markdown huérfanos o duplicados;
- eliminar duplicaciones textuales accidentales;
- conservar íntegros los estados reconciliados y requisitos funcionales.

Cambios prohibidos:

- cambiar lifecycle;
- cambiar reglas 5–8 o 3–5;
- cambiar claims, suficiencia, dossiers, tesis o adaptación;
- cambiar autorizaciones funcionales;
- reinterpretar P-08.

### G. Matriz IR-0 v3

**Destino:**

```text
docs/reconciliation/p08/2026-08-05/ir0_matriz_investigacion_editorial_post_p08_v3_2026-08-05.xlsx
```

**Acción:** copia binaria exacta.

```text
COPY_MODE: BITWISE_COPY
SOURCE_SHA256: de00e9d8c2ed0b0129e907aec4e7c1015a1279849ca3746ecc38b63c427c0145
DESTINATION_SHA256: MUST_EQUAL_SOURCE_SHA256
FORMAT_CONVERSION: FORBIDDEN
CONTENT_EDIT: FORBIDDEN
```

### H. Plan técnico IR-0

**Destino:**

```text
docs/reconciliation/p08/2026-08-05/ir0_plan_tecnico_investigacion_editorial_post_p08_v2_2026-08-05.md
```

**Acción:** copia binaria exacta.

```text
COPY_MODE: BITWISE_COPY
SOURCE_SHA256: d7d5e0f6e04d4539ba30b533f3597cf20753e3fc28ed38e9b7bd5c6ead178563
DESTINATION_SHA256: MUST_EQUAL_SOURCE_SHA256
NOTES_ADDED: NO
CONTENT_EDIT: FORBIDDEN
```

La procedencia se registra en el reporte de cierre, no dentro del archivo.

### I. Reporte de convergencia R0

**Ruta:**

```text
docs/reconciliation/p08/2026-08-05/r0_documentary_convergence_report_2026-08-05.md
```

Debe incluir:

- alcance ejecutado;
- Drive IDs de origen;
- hashes de origen y destino;
- hash de roadmap fuente y roadmap canónico;
- archivos modificados;
- validaciones realizadas;
- defectos textuales corregidos;
- cierre de Plan 003;
- confirmación de autoridad única;
- conteos IR-0 verificados;
- confirmación de R1 no autorizado;
- residuos no bloqueantes;
- prueba de ausencia de cambios técnicos.

---

## 5.2 Archivos condicionales

Ninguno debe modificarse por defecto fuera de la lista obligatoria.

Una referencia adicional solo puede cambiarse si una validación determinista demuestra que publica estado vivo paralelo o una autorización activa incompatible. Debe registrarse en evidencia y requerir aprobación específica dentro de R0 antes de editarse.

---

## 5.3 Archivos y componentes fuera de alcance

No modificar:

- contratos;
- schemas;
- agentes ejecutables;
- prompts;
- skills;
- gates;
- workflows;
- runtime;
- tests;
- configuración activa;
- outputs de R6;
- corpus o referencias editoriales;
- componentes de R1;
- contenido funcional de P-08.

---

## 6. Orden de ejecución

### Unidad R0-0 — Resolver dependencias de origen

1. comprobar presencia en Drive de matriz y plan técnico;
2. registrar Drive ID exacto;
3. recuperar archivos sin conversión;
4. calcular SHA-256;
5. comparar con hashes aprobados;
6. bloquear si falta un archivo o hay divergencia.

**Gate:** `R0_DEPENDENCY_GATE`.

### Unidad R0-1 — Abrir R0 en estado vivo

1. actualizar `plans/001_CONTROL_OPERATIVO.md`;
2. retirar referencias vigentes a Misión 01E;
3. registrar R0 en progreso;
4. mantener R1 no autorizado.

**Gate:** `R0_LIVE_STATE_OPEN_GATE`.

### Unidad R0-2 — Sanear autoridad y recuperación

1. cerrar Plan 003 como histórico no normativo;
2. sanear `plans/plan_001/README.md`;
3. reparar `AGENTS.md`;
4. reparar `B5_PRE_SCRIPT_FOUNDATION.md`;
5. verificar que no queden superficies paralelas de estado.

**Gate:** `R0_AUTHORITY_CONVERGENCE_GATE`.

### Unidad R0-3 — Incorporar artefactos canónicos

1. copiar matriz IR-0 bit a bit;
2. copiar plan técnico IR-0 bit a bit;
3. canonicalizar roadmap v3;
4. registrar hashes de fuente y destino;
5. corregir la frase de autorización de R1.

**Gate:** `R0_ARTIFACT_INTEGRITY_GATE`.

### Unidad R0-4 — Evidencia y cierre

1. ejecutar validaciones completas;
2. crear reporte de convergencia;
3. actualizar control operativo a cierre pendiente de revisión;
4. confirmar R1 no autorizado;
5. entregar evidencia al propietario.

**Gate:** `R0_CLOSURE_GATE`.

No se preparan misiones para Codex hasta que este plan v4 sea aprobado.

---

## 7. Validaciones deterministas

## 7.1 Alcance Git

```bash
git status --short
git diff --name-only
git diff --check
```

La lista final de archivos debe corresponder únicamente a los autorizados por R0.

Debe existir una comprobación negativa sobre directorios técnicos, por ejemplo mediante comparación de nombres modificados contra una allowlist cerrada.

## 7.2 Integridad binaria

```text
MATRIZ_IR0_SOURCE_SHA256 == MATRIZ_IR0_DESTINATION_SHA256
PLAN_TECNICO_IR0_SOURCE_SHA256 == PLAN_TECNICO_IR0_DESTINATION_SHA256
```

El roadmap usa canonicalización controlada:

```text
ROADMAP_SOURCE_SHA256:
RECORDED

ROADMAP_CANONICAL_SHA256:
RECORDED

SOURCE_SHA256 != CANONICAL_SHA256:
ALLOWED_AND_EXPECTED_WHEN_CANONICALIZATION_CHANGES_CONTENT
```

## 7.3 Conteos IR-0

Validar en la matriz:

```text
REQUIREMENT_COUNT: 68
IMPLEMENTED_COUNT: 4
PARTIAL_COUNT: 31
MISSING_COUNT: 32
IR0_FUNCTIONAL_DECISIONS_REQUIRED: 0
OUT_OF_SCOPE_TECHNICAL: 1
```

Validar que la suma sea 68.

## 7.4 Autoridad de estado

Buscar en Markdown y archivos de planeación expresiones activas como:

```text
current_mission
NEXT_ALLOWED_ACTION
IMPLEMENTATION_AUTHORIZED: YES
APPROVED_ACTIVE
HISTORICAL_MISSION_01E_PENDING_OWNER_REVIEW_MARKER
HISTORICAL_MISSION_01E_RESULT_MARKER
```

Resultado esperado:

- estado vivo activo solo en `plans/001_CONTROL_OPERATIVO.md`;
- Plan 003 histórico no normativo;
- roadmap sin estado vivo;
- README sin estado vivo;
- R1 no autorizado.

## 7.5 Integridad textual específica

No buscar ni bloquear por cualquier signo `?`.

Detectar específicamente:

1. carácter de reemplazo Unicode `U+FFFD`;
2. secuencias conocidas de mojibake, incluyendo patrones como `Ã`, `Â`, `â€™`, `â€œ`, `â€`;
3. signo `?` insertado dentro de palabras alfabéticas;
4. términos dañados conocidos, entre ellos:

```text
?nica
?nicos
misi?n
recuperaci?n
Planeaci?n
investigaci?n
autorizaci?n
implementaci?n
demostraci?n
hist?rica
t?cnicas
can?nicas
```

Los signos de interrogación legítimos al inicio o cierre de preguntas no son defectos.

Debe informarse por archivo:

- número de U+FFFD;
- número de patrones de mojibake;
- número de `?` dentro de palabras;
- términos dañados encontrados;
- resultado antes y después.

## 7.6 Estructura Markdown

Validar:

- fences balanceados;
- encabezados no duplicados accidentalmente;
- secciones obligatorias no vacías;
- enlaces internos existentes;
- ausencia de párrafos duplicados consecutivos;
- estructura de `AGENTS.md` y `B5_PRE_SCRIPT_FOUNDATION.md` coherente.

## 7.7 Separación B5_PRE / B5.5 / R0 / R1

Comprobar expresamente:

```text
B5_PRE != B5.5
R0 = DOCUMENTARY_CONVERGENCE
R1 = TECHNICAL_IMPLEMENTATION_NOT_AUTHORIZED
```

## 7.8 Ausencia de implementación técnica

Comprobar que no cambien archivos bajo superficies de:

- `contracts/`;
- `schemas/`;
- agentes;
- skills;
- prompts;
- gates;
- workflows;
- runtime;
- tests.

---

## 8. Evidencia esperada

El paquete de evidencia de R0 debe contener:

1. Drive IDs de roadmap, matriz y plan técnico;
2. SHA-256 de las tres fuentes;
3. SHA-256 de los tres destinos;
4. explicación de canonicalización del roadmap;
5. comprobación bit a bit de matriz y plan técnico;
6. lista exacta de archivos modificados;
7. resultados de `git diff --check`;
8. conteos IR-0;
9. reporte de detección de mojibake;
10. reporte de estructura Markdown;
11. prueba de cierre de Plan 003;
12. prueba de eliminación de referencias vigentes a Misión 01E;
13. prueba de autoridad única del control operativo;
14. confirmación de R1 no autorizado;
15. confirmación de ausencia de cambios técnicos;
16. limitaciones y residuos no bloqueantes.

---

## 9. Criterio de cierre

R0 solo puede declararse listo para revisión del propietario cuando todos los criterios siguientes sean verdaderos:

1. las dependencias de Drive existen y tienen IDs reales;
2. los hashes de origen coinciden con los artefactos aprobados;
3. la matriz IR-0 es copia binaria exacta;
4. el plan técnico IR-0 es copia binaria exacta y no tiene notas añadidas;
5. el roadmap canónico registra hash de origen y destino;
6. el roadmap no autoriza R1 al cerrar R0;
7. `plans/001_CONTROL_OPERATIVO.md` no conserva Misión 01E como acción vigente;
8. Plan 003 está cerrado, histórico y no normativo;
9. `AGENTS.md` no contiene corrupción ni duplicaciones materiales;
10. `B5_PRE_SCRIPT_FOUNDATION.md` no contiene corrupción ni estructura rota;
11. `plans/plan_001/README.md` es solo índice y recuperación;
12. `PARALLEL_LIVE_STATE_SURFACES: 0` está demostrado;
13. los conteos IR-0 son correctos;
14. no se modificaron componentes técnicos;
15. el reporte de convergencia está completo;
16. el control operativo registra R0 cerrado pendiente de revisión;
17. R1 permanece no autorizado;
18. no existe commit ni push fuera de una autorización posterior específica.

Estado de salida previsto:

```text
R0_EXECUTION_STATUS:
COMPLETED_PENDING_OWNER_REVIEW

R0_GATE:
PASS

R1_IMPLEMENTATION:
NOT_AUTHORIZED

IMPLEMENTATION_AUTHORIZED:
NO
```

---

## 10. Riesgos y controles

### Riesgo 1 — Alias falso del plan técnico

**Control:** nombre exacto, Drive ID real y SHA-256. No usar el plan funcional como sustituto.

### Riesgo 2 — Duplicación de estado vivo

**Control:** búsqueda global y allowlist; solo el control operativo puede publicar estado actual.

### Riesgo 3 — Autorización implícita de R1

**Control:** frase normativa obligatoria y búsqueda de expresiones incompatibles.

### Riesgo 4 — Alteración del contenido funcional

**Control:** limitar `AGENTS.md` y B5_PRE a reparación textual/estructural; revisar diff semántico.

### Riesgo 5 — Corrupción de encoding

**Control:** validación específica de U+FFFD, mojibake y `?` dentro de palabras; no usar búsqueda genérica.

### Riesgo 6 — Modificación accidental de binarios

**Control:** copia bit a bit y SHA-256 idéntico.

### Riesgo 7 — Ampliación hacia R1

**Control:** allowlist de archivos y ausencia total de cambios técnicos.

### Riesgo 8 — Plan 003 sigue activo por redacción residual

**Control:** búsqueda de `APPROVED_ACTIVE` e `IMPLEMENTATION_AUTHORIZED: YES`, más declaración histórica explícita.

---

## 11. Rollback

### 11.1 Principio

Cada unidad de R0 debe ser reversible de manera independiente antes de commit.

### 11.2 Rollback por unidad

- **R0-0:** no inicia cambios de repositorio; si falla una dependencia, detener.
- **R0-1:** restaurar únicamente `plans/001_CONTROL_OPERATIVO.md` al estado previo.
- **R0-2:** restaurar Plan 003, README, AGENTS y B5_PRE desde el snapshot anterior si una validación semántica falla.
- **R0-3:** eliminar copias incorporadas y restaurar roadmap canónico si hashes o procedencia fallan.
- **R0-4:** retirar reporte de cierre y restaurar el control operativo a R0 en progreso si el gate no pasa.

### 11.3 Prohibiciones de rollback

No usar:

- `git reset --hard` sobre cambios preexistentes;
- limpieza global de archivos no rastreados;
- restauración de directorios completos;
- reescritura automática de encoding de todo el repositorio.

El rollback debe limitarse a los archivos de R0 y preservar cambios preexistentes no relacionados.

---

## 12. Orden futuro de misiones

Este plan define cinco unidades conceptuales:

```text
R0-0 DEPENDENCY_RESOLUTION
R0-1 LIVE_STATE_OPENING
R0-2 AUTHORITY_AND_TEXTUAL_CONVERGENCE
R0-3 CANONICAL_ARTIFACT_INTEGRATION
R0-4 VALIDATION_EVIDENCE_AND_CLOSURE
```

No son todavía misiones para Codex.

Solo podrán convertirse en misiones operativas después de:

```text
R0_DETAILED_PLAN_OWNER_APPROVAL:
YES
```

---

## 13. Estado de este plan

```text
R0_DETAILED_PLAN_REVIEW:
APPROVED

PLAN_BLOCKERS_REMAINING:
0

PRE_R0_GATE:
PASS

R0_EXECUTION:
NOT_STARTED

R1_IMPLEMENTATION:
NOT_AUTHORIZED

P0_BLOCKERS_ADDRESSED_IN_PLAN:
4

P1_CORRECTIONS_ADDRESSED_IN_PLAN:
2

READY_FOR_R0_EXECUTION:
REQUIRES_SEPARATE_LIVE_STATE_OPENING

REPOSITORY_MODIFIED:
NO

R1_PREPARED:
NO

CODEX_MISSIONS_PREPARED:
NO

IMPLEMENTATION_AUTHORIZED:
NO
```
