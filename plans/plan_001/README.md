# PLAN-001 — Índice operativo por bloques

**Plan rector:** [`../001_reestructuracion_motor_agentico_editorial_y_harness.md`](../001_reestructuracion_motor_agentico_editorial_y_harness.md)  
**Control operativo:** [`../001_CONTROL_OPERATIVO.md`](../001_CONTROL_OPERATIVO.md)  
**Versión:** `1.3`  
**Implementación autorizada:** `NO`

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

## 3. Índice de bloques

| Bloque | Archivo | Dependencia | Estado | Gate resumido |
|---|---|---|---|---|
| `B0` | [B0_gobernanza_baseline_benchmarks.md](B0_gobernanza_baseline_benchmarks.md) | Ninguna | `PLANNED` | Baseline y benchmarks aprobados |
| `B1` | [B1_contratos_schemas_estados_versionado.md](B1_contratos_schemas_estados_versionado.md) | B0 | `PLANNED` | Contratos canónicos aprobados |
| `B2` | [B2_reparacion_harness_gates.md](B2_reparacion_harness_gates.md) | B1 | `PLANNED` | Cero falsos PASS conocidos |
| `B3` | [B3_perfil_editorial_frontera_canal.md](B3_perfil_editorial_frontera_canal.md) | B1–B2 | `PLANNED` | Producción consume perfil versionado |
| `B4` | [B4_responsabilidades_skills_portabilidad.md](B4_responsabilidades_skills_portabilidad.md) | B3 | `PLANNED` | Responsabilidades y familias funcionales operables sin crear subagentes innecesarios |
| `B5` | [B5_diseno_editorial.md](B5_diseno_editorial.md) | B3–B4 | `PLANNED` | Diseño editorial completo aprobado |
| `B5.5` | [B5_5_prototipo_editorial.md](B5_5_prototipo_editorial.md) | B5 | `PLANNED` | Mejora editorial temprana demostrada |
| `B6` | [B6_redaccion_edicion_verificacion.md](B6_redaccion_edicion_verificacion.md) | B5.5 | `PLANNED` | Candidato final coherente y trazable |
| `B7` | [B7_auditoria_aprobacion_editorial.md](B7_auditoria_aprobacion_editorial.md) | B6 | `PLANNED` | Guion aprobado editorialmente |
| `B7.5` | [B7_5_adaptacion_youtube.md](B7_5_adaptacion_youtube.md) | B7 | `PLANNED` | Packaging, correspondencia y continuidad aprobados |
| `B8` | [B8_plataforma_derechos_paquete.md](B8_plataforma_derechos_paquete.md) | B7.5 | `PLANNED` | Paquete completo evaluado y compilado |
| `B8.5` | [B8_5_aprobacion_youtube_ready.md](B8_5_aprobacion_youtube_ready.md) | B8 | `PLANNED` | Paquete exacto autorizado para producción |
| `B9` | [B9_validacion_tres_episodios.md](B9_validacion_tres_episodios.md) | B2–B8.5 | `PLANNED` | Tres casos aprobados |
| `B9.5` | [B9_5_aprendizaje_controlado.md](B9_5_aprendizaje_controlado.md) | B9 | `PLANNED` | Ciclo manual de aprendizaje demostrado |
| `B10` | [B10_lean_portabilidad_cierre.md](B10_lean_portabilidad_cierre.md) | B9.5 | `PLANNED` | Plan cerrado con evidencia |

## 4. Regla de sincronización

Cuando cambie el Plan 001:

1. registrar la modificación en el control de cambios del plan rector;
2. identificar qué bloques quedan afectados;
3. actualizar únicamente sus proyecciones operativas;
4. actualizar `../001_CONTROL_OPERATIVO.md` si cambian estado, dependencia o siguiente acción;
5. comprobar que ningún archivo operativo introduce requisitos nuevos;
6. registrar evidencia de sincronización.

Una modificación aislada de un archivo de bloque no cambia el plan rector.

## 5. Estado actual

```text
PLAN_STATUS: READY_FOR_TEAM_REVALIDATION
IMPLEMENTATION_AUTHORIZED: NO
CURRENT_BLOCK: NONE
NEXT_ALLOWED_ACTION: TARGETED_REVALIDATION_TEAMS_01_02_03
NEXT_IMPLEMENTATION_BLOCK_IF_APPROVED: B0
```
