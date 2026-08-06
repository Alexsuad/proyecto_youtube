# PLAN-001 — Índice operativo por bloques

**Plan rector:** [`../001_reestructuracion_motor_agentico_editorial_y_harness.md`](../001_reestructuracion_motor_agentico_editorial_y_harness.md)  
**Control operativo:** [`../001_CONTROL_OPERATIVO.md`](../001_CONTROL_OPERATIVO.md)  
**Versión:** `1.4`

## 1A. Prioridad y etapas

La fuente canónica del estado vivo es `../001_CONTROL_OPERATIVO.md`. Este README funciona solo como índice estable de navegación de `plans/plan_001/` y no publica misiones activas, autorizaciones ni siguiente acción.

## 1. Propósito

Esta carpeta reduce el contexto que deben cargar los agentes operativos. Cada archivo contiene únicamente la especificación derivada de un bloque del Plan 001.

La jerarquía es:

```text
Plan rector completo
→ Control operativo vigente
→ Archivo del bloque activo
→ Misión técnica autorizada
→ Archivos reales afectados
```

Los archivos de esta carpeta:

- no sustituyen el plan rector;
- no pueden ampliar su alcance;
- no autorizan por sí mismos una implementación;
- no deben editarse sin comprobar si el plan rector también requiere cambio;
- deben mantenerse sincronizados cuando cambie la parte correspondiente del plan rector.

## 2. Política de lectura

### Leer siempre

1. `AGENTS.md`, cuando exista.
2. docs/ALCANCE_Y_COORDINACION_EQUIPOS.md.
3. `plans/001_CONTROL_OPERATIVO.md`.
4. El archivo del bloque activo.
5. La misión concreta.
6. Solo los archivos expresamente indicados o necesarios para ejecutar esa misión.

### No leer por defecto

- el Plan 001 completo;
- bloques no activos;
- todo `workspace/`;
- todos los reportes históricos;
- todo `output/`;
- fuentes de Producto no vinculadas a la misión.

### Consultar el plan rector completo solo cuando

- exista una contradicción;
- falte una autoridad;
- se proponga cambiar alcance, dependencias o estados;
- el archivo del bloque remita a una sección concreta;
- una corrección pueda afectar a más de un bloque.

## 3. Documentos de integración post-P08

| Documento | Archivo | Descripción |
|---|---|---|
| `B0_1` | [B0_1_roadmap_implementacion_post_p08.md](B0_1_roadmap_implementacion_post_p08.md) | roadmap maestro de implementación posterior a P-08 |
| `B0_2` | [B0_2_cierre_documental_recuperacion_post_p08.md](B0_2_cierre_documental_recuperacion_post_p08.md) | plan detallado para el cierre documental y la recuperación R0 |

## 4. Índice de bloques

| Bloque | Archivo | Dependencia | Estado | Gate resumido |
|---|---|---|---|---|
| `B0` | [B0_gobernanza_baseline_benchmarks.md](B0_gobernanza_baseline_benchmarks.md) | Ninguna | `OPEN` | EVIDENCE_REVIEW_REQUIRED |
| `B1` | [B1_contratos_schemas_estados_versionado.md](B1_contratos_schemas_estados_versionado.md) | B0 | `PASS` | Contratos canónicos aprobados |
| `B2` | [B2_reparacion_harness_gates.md](B2_reparacion_harness_gates.md) | B1 | `PASS` | Cero falsos PASS conocidos |
| `B3` | [B3_perfil_editorial_frontera_canal.md](B3_perfil_editorial_frontera_canal.md) | B1–B2 | `PASS` | PROFILE_1_2_1_ACTIVE |
| `B4` | [B4_responsabilidades_skills_portabilidad.md](B4_responsabilidades_skills_portabilidad.md) | B3 | `OPEN` | CONTRACTUAL_FOUNDATION_PASS / REAL_EXECUTION_NOT_DEMONSTRATED |
| `B5` | [B5_diseno_editorial.md](B5_diseno_editorial.md) | B3–B4 | `IN_PROGRESS` | B5-I1_FUNCTIONAL_CONFIRMATION_PENDING / B5-I2_OPEN / B5-I3 `NOT_AUTHORIZED` |
| `B5_PRE` | [B5_PRE_SCRIPT_FOUNDATION.md](B5_PRE_SCRIPT_FOUNDATION.md) | B5 | `FUNCTIONAL_FOUNDATION` | Planeación previa al guion: pertenencia, investigación, 5–8 candidatas, 3–5 finales, tesis, promesa |
| `B5.5` | [B5_5_prototipo_editorial.md](B5_5_prototipo_editorial.md) | B5 | `PLANNED` | Mejora editorial temprana demostrada |
| `B6` | [B6_redaccion_edicion_verificacion.md](B6_redaccion_edicion_verificacion.md) | B5.5 | `PLANNED` | Candidato final coherente y trazable |
| `B7` | [B7_auditoria_aprobacion_editorial.md](B7_auditoria_aprobacion_editorial.md) | B6 | `PLANNED` | Guion aprobado editorialmente |
| `B7.5` | [B7_5_adaptacion_youtube.md](B7_5_adaptacion_youtube.md) | B7 | `DEFERRED_NOT_AUTHORIZED` | Adaptación y packaging futuros |
| `B8` | [B8_plataforma_derechos_paquete.md](B8_plataforma_derechos_paquete.md) | B7.5 | `DEFERRED_NOT_AUTHORIZED` | Componentes de texto pueden evaluarse en Etapa 1; plataforma y distribución son futuras |
| `B8.5` | [B8_5_aprobacion_youtube_production_ready.md](B8_5_aprobacion_youtube_production_ready.md) | B8 | `DEFERRED_NOT_AUTHORIZED` | Producción futura |
| `B9` | [B9_validacion_tres_episodios.md](B9_validacion_tres_episodios.md) | B7 / `EDITORIAL_SCRIPT_APPROVED` | `PLANNED` | Validación del núcleo profesional de Guion |
| `B9.5` | [B9_5_aprendizaje_controlado.md](B9_5_aprendizaje_controlado.md) | B9 | `PLANNED` | Aprendizaje editorial; distribución diferida |
| `B10` | [B10_lean_portabilidad_cierre.md](B10_lean_portabilidad_cierre.md) | B9 + aprendizaje editorial B9.5 | `PLANNED` | Cierre de Etapa 1 y portabilidad |

## 5. Versiones derivadas

La versión derivada de cada bloque indica la última versión del plan que modificó materialmente su contenido. Un bloque puede conservar v1.3 si v1.4 no lo afectó.

## 6. Regla de sincronización

Cuando cambie el Plan 001:

1. registrar la modificación en el control de cambios del plan rector;
2. identificar qué bloques quedan afectados;
3. actualizar únicamente sus proyecciones operativas;
4. actualizar `../001_CONTROL_OPERATIVO.md` si cambian estado, dependencia o siguiente acción;
5. comprobar que ningún archivo operativo introduce requisitos nuevos;
6. registrar evidencia de sincronización.

Una modificación aislada de un archivo de bloque no cambia el plan rector.

Estado vivo, autorizaciones y siguiente acción: consultar exclusivamente `../001_CONTROL_OPERATIVO.md`.
