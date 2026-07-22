# PLAN-001 / B4 — Responsabilidades, skills, prompts y portabilidad

**Plan rector:** [`../001_reestructuracion_motor_agentico_editorial_y_harness.md`](../001_reestructuracion_motor_agentico_editorial_y_harness.md)  
**Control operativo:** [`../001_CONTROL_OPERATIVO.md`](../001_CONTROL_OPERATIVO.md)  
**Versión derivada:** `PLAN-001 v1.4`
**Estado inicial:** `PLANNED`  
**Dependencia:** `B3`  
**Siguiente tramo:** `B5`  
**Gate resumido:** Responsabilidades y familias funcionales operables sin crear subagentes innecesarios

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

- §9 Modelo funcional y agéntico
- §7.14 No crear componentes por entusiasmo
- docs/ALCANCE_Y_COORDINACION_EQUIPOS.md

---

## 1. Objetivo

Alinear los once roles actuales con responsabilidades operativas base y familias funcionales canónicas, asignando dueño funcional, contrato, veto y evidencia sin crear subagentes innecesarios ni acoplar el sistema a Antigravity.

## 2. Misiones

### B4-M1 — Contratos oficiales de responsabilidad

Definir para cada responsabilidad:

```text
role_id
purpose
when_used
inputs
outputs
read_permissions
write_permissions
forbidden_actions
veto_conditions
evidence
handoff
prompt_version
```

### B4-M2 — Separar Editor y Auditor

Crear dos contratos distintos:

- `EDITOR`: modifica y produce `EditorialEditReport`.
- `FINAL_EDITORIAL_AUDITOR`: no modifica el guion y produce `FinalEditorialAudit`.

La auditoría final debe ejecutarse en contexto limpio o sesión separada.

### B4-M3 — Catálogo de skills por responsabilidad

#### Inteligencia del Canal y gobernanza del perfil

- construir o actualizar el `EditorialProfile`;
- auditar coherencia de identidad;
- detectar contaminación;
- comprobar pertenencia temática;
- clasificar cambios;
- controlar evolución de voz;
- gestionar decisiones pendientes;
- validar aprendizajes antes de activarlos;
- registrar aprobación funcional del Equipo 01.

Estas capacidades son propiedad funcional del Equipo 01. El Equipo 04 decide su forma técnica.

#### Investigación, análisis narrativo y humano, y curación

- investigar por cobertura;
- clasificar fuentes;
- evaluar acceso;
- producir evidence report;
- analizar narrativamente y humanamente cada material con evidencia y límites;
- curar por función narrativa.

#### Arquitectura narrativa

- clasificar tipo de guion;
- tesis provisional/refinada;
- consumir la PackagingHypothesis aprobada funcionalmente por el Equipo 03;
- validar que la tesis y la arquitectura puedan cumplirla honestamente;
- viewer journey;
- opening/closing design;
- outline y presupuesto.

#### Escritura

- redactar bloques;
- mantener memoria global;
- aplicar correcciones enrutadas.
- convertir funciones estructurales en narración y argumentación orgánicas;

#### Edición

- edición de desarrollo;
- edición de línea;
- oralidad;
- read-aloud review.

#### Auditoría

- contrato y perfil;
- evidencia;
- coherencia;
- originalidad;
- calidad final;
- ruta de corrección.

#### Adaptación a YouTube

- definir la audiencia concreta del episodio;
- definir o aprobar la hipótesis temprana de promesa y packaging;
- auditar correspondencia entre promesa y contenido;
- decidir packaging final;
- adaptar apertura y duración a plataforma;
- planificar continuidad;
- producir Shorts y derivados;
- preparar metadatos y paquete;
- evaluar plataforma, monetización y derechos;
- separar aprobación para producción de aprobación para publicación.

### B4-M4 — Prompts oficiales

Cada responsabilidad estable debe contar con prompt oficial versionado. No se permiten prompts improvisados en el workflow activo.

### B4-M5 — Proyección al entorno Antigravity

Los archivos `.agent/` actúan como adapter operativo, no como única sede de la arquitectura.

### B4-M6 — Configuración agnóstica

Separar:

```text
role
provider
model
tools
permissions
```

El cambio de proveedor debe ocurrir por configuración.

### B4-M8 — Puntos de extensión

La arquitectura debe poder incorporar, sin modificar el core:

- nuevo proveedor de IA;
- nuevo modelo;
- nuevo canal de entrada;
- nueva skill;
- nueva auditoría;
- nueva política de plataforma;
- nuevo formato;
- nuevo territorio editorial;
- nuevo mecanismo de verificación.

Definir conceptualmente interfaces o adapters, sin diseñar todavía implementación concreta. Ejemplos válidos: AIProvider, InputAdapter, ReviewModule, PolicyPack o equivalentes.

Antigravity, Codex y OpenCode son agentes operativos de desarrollo, no dependencias obligatorias del producto. Los proveedores deben seleccionarse por configuración. Telegram, voz, web o API serán futuras entradas que normalicen hacia un contrato canónico. No implementar esos adaptadores en B4 si están fuera del MVP.

### B4-M7 — Política de subagentes

Mantener `0` subagentes reales hasta que exista evidencia de necesidad.

## 3. Gate B4

```text
PASS si:
- todas las responsabilidades operativas y familias funcionales canónicas tienen contrato;
- cada capacidad tiene dueño funcional identificado;
- Inteligencia del Canal está representada y conserva la aprobación funcional del Equipo 01;
- Adaptación a YouTube está representada y conserva la autoridad funcional del Equipo 03;
- Editor y Auditor están separados;
- cada skill tiene dueño funcional;
- prompts oficiales están versionados;
- el sistema funciona en modo single-agent;
- la arquitectura no depende de una marca de IDE o modelo;
- los puntos de extensión para proveedor, entrada, auditoría y política están definidos conceptualmente;
- Antigravity, Codex y OpenCode no son dependencias obligatorias del producto;
- no se crearon subagentes sin justificación;
- los adaptadores de entrada adicionales (Telegram, voz, web, API) no se implementaron en MVP.
```

---
