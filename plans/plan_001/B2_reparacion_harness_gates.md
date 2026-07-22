# PLAN-001 / B2 — Reparación del arnés y gates críticos

**Plan rector:** [`../001_reestructuracion_motor_agentico_editorial_y_harness.md`](../001_reestructuracion_motor_agentico_editorial_y_harness.md)  
**Control operativo:** [`../001_CONTROL_OPERATIVO.md`](../001_CONTROL_OPERATIVO.md)  
**Versión derivada:** `PLAN-001 v1.3`  
**Estado:** `COMPLETED`
**Dependencia:** `B1`  
**Siguiente tramo:** `B3`  
**Gate resumido:** Cero falsos PASS conocidos

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

- §5.2 Fallos críticos conocidos
- §10 Estados canónicos
- B1 contratos canónicos

---

## 1. Objetivo

Eliminar falsos positivos y hacer que el pipeline se detenga cuando faltan entradas, evidencia, contenido, aprobación o coherencia de estado.

## 2. Misiones

### B2-M1 — Exit codes y parser canónico

**Archivos iniciales afectados:**

```text
src/scripts/gate0_auditoria.py
src/scripts/gate0_integridad.py
src/scripts/qa_brief_research.py
src/scripts/qa_momento_1.py
src/scripts/qa_duracion_guion.py
src/scripts/qa_lenguaje_youtube.py
src/scripts/qa_lenguaje_youtube_ultra.py
src/scripts/cerrar_episodio.py
```

**Cambios:**

- usar estados y códigos canónicos;
- eliminar decisiones por substring;
- parsear un único resultado estructurado;
- rechazar estados múltiples o ambiguos;
- distinguir `FAIL`, `BLOCKED` y `ERROR`.

### B2-M2 — Validación de entradas

Cada gate declara inputs obligatorios y valida:

- existencia;
- tipo;
- contenido no vacío;
- contrato;
- versión esperada;
- checksum cuando aplique;
- aprobación previa;
- estado del episodio.

### B2-M3 — Cierre fuerte del episodio

`cerrar_episodio.py` debe comprobar:

- entregables obligatorios no vacíos;
- gates finales en PASS o WARN permitido;
- versión humana aprobada exacta;
- ausencia de cambios posteriores;
- manifest completo;
- limitaciones declaradas;
- derivados requeridos, cuando correspondan;
- transición de estado válida.

### B2-M4 — Orden correcto del workflow

- separar gates por artefacto cuando sea necesario;
- no auditar packaging definitivo antes de generarlo;
- no realizar auditoría final antes de edición, fact-check y originalidad;
- no cerrar antes de aprobación humana final.

### B2-M5 — Evidence Sufficiency Gate

Implementar el gate que produce:

```text
PASS    -> evidencia suficiente
WARN    -> se puede continuar con límites explícitos
BLOCKED -> análisis responsable imposible
FAIL    -> evidencia contradice o incumple contrato
```

No puede existir PASS sin `SourceAccessAndEvidenceReport` válido.

### B2-M6 — Gate de aprobación e inmutabilidad

- aprobación humana referencia versión y checksum;
- cambio posterior invalida la aprobación;
- el cierre detecta mismatch;
- no se permiten artefactos huérfanos o versiones sin manifest.

## 3. Suite mínima

Debe cubrir:

- inputs ausentes;
- inputs vacíos;
- dos estados en el mismo reporte;
- estado desconocido;
- exit code incoherente;
- cierre con guion vacío;
- cierre con aprobación de otra versión;
- evidencia insuficiente;
- gate post-guion antes de inputs;
- ejecución desde otro CWD;
- compatibilidad de rutas.

## 4. Gate B2

```text
PASS si:
- todos los FAIL devuelven 1;
- todos los BLOCKED devuelven 2;
- no existen falsos PASS reproducibles;
- cierre inválido no puede completar episodio;
- evidencia insuficiente bloquea;
- aprobación de versión distinta se rechaza;
- suite de regresión pasa.
```

---

## 5. Registro de implementación B2

- Entorno oficial: Windows nativo. No se exige compatibilidad, ejecución ni reproducción de pruebas en Linux o WSL; un fallo exclusivo de dichos entornos no bloquea B2.
- Validación oficial desde PowerShell o terminal Windows: `python -m unittest discover -s tests -p "test_*.py"`, `python -m compileall -q src` y `git diff --check -- .agent/workflows plans schemas src tests`.
- Los `subprocess.run()` de la matriz B2 usan timeout para evitar bloqueos indefinidos también en Windows.
- Correcciones finales: evidencia sin soporte falla; ausencia de material y alternativas bloquea; identidad de manifests, aprobaciones y gates es exacta; FinalDeliveryManifest valida scripts distintos, ClaimsLedger, versiones y checksums; cierre exige los gates obligatorios de B2 y separa QA ultra pre/post-guion.
- Archivos creados: runtime, validación de entradas, resolución de rutas, adaptador estricto Gate V, schema y gate de evidencia, y pruebas en `tests/harness/`.
- Archivos modificados: scripts autorizados, workflows, contratos y control operativo.
- Pruebas ejecutadas: `python -m unittest discover -s tests -p "test_*.py"` (46 tests, matriz B2 y regresiones, PASS) y `python -m compileall -q src` (PASS).
- Defectos B0 corregidos: C-01 a C-08 quedan cubiertos por códigos de salida, inputs bloqueantes, parser exacto, portabilidad y regresiones B2.
- Limitaciones: Gate V continúa textual por compatibilidad y se adapta una sola vez a `GateResult`; políticas editoriales y producción/publicación permanecen fuera de B2.
- Auditoría externa: `PASS`.
- Pruebas oficiales Windows: `46/46 PASS`.
- Pendientes reales: B3 no iniciado.
