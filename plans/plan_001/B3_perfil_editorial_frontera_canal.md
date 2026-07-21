# PLAN-001 / B3 — Perfil editorial y frontera del canal

**Plan rector:** [`../001_reestructuracion_motor_agentico_editorial_y_harness.md`](../001_reestructuracion_motor_agentico_editorial_y_harness.md)  
**Control operativo:** [`../001_CONTROL_OPERATIVO.md`](../001_CONTROL_OPERATIVO.md)  
**Versión derivada:** `PLAN-001 v1.3`  
**Estado inicial:** `PLANNED`  
**Dependencia:** `B1–B2`  
**Siguiente tramo:** `B4`  
**Gate resumido:** Producción consume perfil versionado

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

- §8.1 Capa A — Inteligencia específica
- §8.2 Capa B — Motor profesional
- B1-C1 EditorialProfile

---

## 1. Objetivo

Separar la inteligencia del canal del proceso de producción sin debilitar la identidad de Más Allá del Guion.

## 2. Misiones

### B3-M1 — Matriz canónica de componentes

Clasificar cada archivo como:

```text
CHANNEL_SOURCE
EDITORIAL_PROFILE_SOURCE
SCRIPT_ENGINE
HARNESS
DERIVATIVE
HISTORICAL
TEMPLATE
CONFIGURATION
```

La matriz debe identificar:

- autoridad;
- consumidor;
- estado;
- duplicaciones;
- migración necesaria.

### B3-M2 — Compilador de EditorialProfile

Crear un proceso reproducible que:

- lea fuentes aprobadas del canal;
- valide contradicciones;
- genere versión;
- registre lineage y hashes;
- produzca checksum;
- solicite y registre la aprobación funcional del Equipo 01;
- solicite y registre la validación técnica del Equipo 04;
- no active automáticamente cambios no aprobados.

La aprobación debe quedar separada:

```text
TEAM_01_PROFILE_APPROVAL
→ valida identidad, posicionamiento, audiencia, promesa, territorios,
  personalidad, voz, principios conceptuales y contenido funcional.

TECHNICAL_PROFILE_VALIDATION
→ valida contrato, compilación, lineage, versión, checksum,
  configuración e invalidación.
```

La validación técnica del Equipo 04 no autoriza el contenido funcional. La aprobación del Equipo 01 no sustituye la validación técnica.

### B3-M3 — Perfil activo y selección por configuración

La ejecución debe identificar explícitamente:

```text
ACTIVE_PROFILE_ID
ACTIVE_PROFILE_VERSION
```

No se aceptan lecturas implícitas de “lo último” sin aprobación.

### B3-M4 — Adapter de compatibilidad

Durante la migración, un adapter puede traducir documentos actuales al contrato nuevo sin mover todo de una vez.

### B3-M5 — Prohibición de lectura directa dispersa

Skills de brief, outline, guion y QA deben consumir el perfil, no cinco o seis documentos internos de forma independiente.

Excepciones autorizadas:

- compilación del perfil;
- mantenimiento del perfil;
- auditoría de lineage;
- migración controlada.

### B3-M6 — Política de cambio e invalidación del perfil

Un cambio de perfil se clasifica como:

```text
NO_IMPACT
PARTIAL_INVALIDATION
FULL_INVALIDATION
```

Debe indicar qué episodios o artefactos requieren revisión.

### B3-M7 — Aprendizajes de voz como candidatos

- no escribir directamente en el perfil;
- registrar candidatos;
- acumular evidencia;
- aprobar o rechazar;
- crear nueva versión solo con aprobación funcional del Equipo 01 y validación técnica del Equipo 04.

## 3. Gate B3

```text
PASS si:
- existe EditorialProfile versionado;
- TEAM_01_PROFILE_APPROVAL = PASS;
- TECHNICAL_PROFILE_VALIDATION = PASS;
- la aprobación funcional y la validación técnica corresponden a la misma versión y checksum;
- el lineage está completo;
- el motor no depende de lecturas dispersas del workspace;
- el cambio de perfil invalida correctamente;
- los aprendizajes candidatos no contaminan el perfil;
- las dimensiones estables, editoriales, de formato, transversales y pendientes están diferenciadas;
- un episodio puede identificar exactamente qué perfil usó.
```

---
