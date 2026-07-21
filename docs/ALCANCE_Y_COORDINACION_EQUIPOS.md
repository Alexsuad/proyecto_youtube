# Alcance y coordinación de los equipos del Proyecto YouTube

**Estado:** Documento rector de responsabilidades
**Aplicación:** Chats y equipos internos del Proyecto YouTube

## 1. Propósito

Este documento define el alcance de los cuatro equipos del Proyecto YouTube, sus límites de decisión y la forma en que deben coordinarse.

La regla principal es:

> Cada equipo tiene autoridad sobre su especialidad, pero no puede tomar decisiones que pertenezcan a otro equipo.

Los equipos pueden intercambiar consultas, requisitos, observaciones y auditorías. Sin embargo, solo el equipo **04_Infraestructura y Gobernanza** puede convertir esas necesidades en instrucciones para agentes operativos como Antigravity, Codex, OpenCode u otros equivalentes.

---

# 2. Equipo 01 — Inteligencia del Canal

## Responsabilidad

Define quién es el canal y qué producto editorial representa.

Tiene autoridad sobre:

* identidad;
* propósito;
* posicionamiento;
* audiencia;
* promesa principal;
* territorios editoriales;
* pilares y límites;
* personalidad;
* voz y tono;
* relación con la audiencia;
* criterios de selección temática;
* identidad conceptual de títulos y miniaturas;
* evolución aprobada de la identidad;
* perfil editorial del canal.

## Audita

* coherencia con la identidad;
* desviaciones de posicionamiento;
* contaminación del perfil;
* contradicciones entre audiencia, promesa y contenido;
* cambios que puedan afectar la identidad del canal.

## No decide

* arquitectura técnica;
* código;
* scripts;
* estructura del repositorio;
* número técnico de agentes;
* implementación de skills;
* escritura completa del guion;
* packaging final;
* monetización;
* copyright;
* publicación.

Puede solicitar cambios funcionales, pero no instruye directamente al agente operativo.

---

# 3. Equipo 02 — Producto Guion

## Responsabilidad

Define cómo debe construirse un guion profesional para Más Allá del Guion.

Tiene autoridad sobre:

* brief editorial;
* pregunta central;
* tesis;
* investigación necesaria;
* curación de obras;
* análisis narrativo y humano;
* estructura del guion;
* progresión;
* recorrido del espectador;
* apertura;
* desarrollo;
* cierre;
* redacción por bloques;
* edición de desarrollo;
* edición de línea y oralidad;
* originalidad;
* calidad editorial;
* criterios de aprobación del guion.

## Audita

* calidad de la tesis;
* profundidad;
* progresión;
* coherencia global;
* uso de las obras;
* naturalidad;
* oralidad;
* originalidad;
* cumplimiento de la promesa editorial;
* calidad del guion final.

## No decide

* identidad general del canal;
* estrategia técnica;
* arquitectura del repositorio;
* scripts;
* runtime;
* número de agentes;
* packaging final;
* normas de plataforma;
* monetización;
* copyright;
* publicación.

Este equipo define qué debe hacer una skill de guion y redacta su contenido funcional. El equipo 04 revisa su viabilidad agéntica, crea su estructura técnica y gestiona su incorporación al sistema.

---

# 4. Equipo 03 — Adaptación a YouTube

## Responsabilidad

Convierte una pieza editorial aprobada en un producto preparado para funcionar dentro de YouTube.

Tiene autoridad sobre:

* audiencia concreta del episodio;
* promesa visible;
* hipótesis de packaging;
* título;
* concepto de miniatura;
* correspondencia entre packaging y contenido;
* adecuación de la apertura a YouTube;
* duración orientativa para plataforma;
* continuidad de sesión;
* playlists;
* CTA;
* Shorts y derivados;
* metadatos;
* paquete de publicación;
* riesgo de plataforma;
* riesgo publicitario;
* copyright;
* contenido reutilizado;
* contenido sintético o alterado;
* aprendizaje posterior a la publicación.

## Audita

* relación entre título, miniatura, apertura, desarrollo y cierre;
* riesgo de clickbait;
* preparación para publicación;
* monetización y seguridad publicitaria, sin garantizar resultados;
* copyright y reutilización;
* continuidad hacia otros contenidos;
* calidad del paquete de publicación;
* resultados posteriores y aprendizajes de YouTube.

## No decide

* identidad del canal;
* tesis profunda;
* estructura editorial completa;
* redacción del guion;
* arquitectura técnica;
* scripts;
* repositorio;
* número de agentes;
* implementación técnica;
* proveedor de IA.

Puede bloquear una publicación por riesgos dentro de su especialidad, pero no puede modificar unilateralmente la identidad o la tesis para hacerla más comercial.

---

# 5. Equipo 04 — Infraestructura y Gobernanza

## Responsabilidad

Es el único responsable técnico, arquitectónico y operativo del Proyecto YouTube.

Tiene autoridad sobre:

* arquitectura del sistema;
* repositorio;
* código;
* scripts;
* schemas;
* contratos técnicos;
* workflows;
* gates;
* estados;
* pruebas;
* fixtures;
* logs;
* configuración;
* seguridad;
* portabilidad;
* versionado;
* invalidación;
* integración de skills;
* estructura agéntica;
* agentes y subagentes;
* proveedores de IA;
* CLI;
* MCP;
* mantenimiento;
* deuda técnica;
* control de implementación.

## Audita

* arquitectura;
* integridad del repositorio;
* calidad técnica;
* pruebas reales;
* exit codes;
* falsos PASS;
* seguridad;
* portabilidad;
* duplicaciones;
* cumplimiento del plan;
* alcance de los cambios;
* evidencia;
* no degradación;
* preparación técnica para cada fase.

## No decide

* identidad del canal;
* audiencia editorial;
* tesis;
* calidad narrativa;
* estructura ideal de un guion;
* voz;
* criterios de packaging;
* estrategia de publicación;
* monetización editorial;
* decisiones de Producto fuera de su especialidad.

Debe entender suficientemente las demás áreas para traducir sus requisitos a arquitectura, contratos y ejecución, pero no sustituye a sus expertos.

---

# 6. Autoridad sobre las skills

Cada equipo es dueño funcional de las skills de su especialidad.

Esto significa:

```text
Equipo especialista
→ define el propósito
→ redacta o valida el contenido funcional
→ establece entradas, salidas y criterios de calidad
→ audita si la skill cumple su función
```

El equipo 04:

```text
recibe la solicitud
→ revisa coherencia agéntica y técnica
→ detecta solapamientos
→ solicita aclaraciones cuando sea necesario
→ decide si corresponde skill, script, gate, regla o workflow
→ prepara la estructura e instrucción técnica
→ ordena la implementación al agente operativo
→ verifica pruebas e integración
```

El equipo 04 crea técnicamente las skills de todos los equipos, pero no inventa ni sustituye el criterio experto de Producto.

Las skills propias de Infraestructura y Gobernanza sí son definidas, redactadas, implementadas y auditadas completamente por el equipo 04.

---

# 7. Canal único hacia agentes operativos

Solo el equipo **04_Infraestructura y Gobernanza** puede dar instrucciones directas a:

* Antigravity;
* Codex;
* OpenCode;
* Claude Code;
* otros agentes operativos equivalentes.

Los equipos 01, 02 y 03 no deben instruir directamente a estos agentes.

El flujo obligatorio es:

```text
Equipo especialista
→ presenta requisito funcional al equipo 04
→ equipo 04 revisa alcance, dependencias y viabilidad
→ equipo 04 formula dudas o comentarios
→ equipo especialista responde o ajusta
→ equipo 04 crea la misión técnica
→ agente operativo ejecuta
→ equipo 04 audita la implementación
→ equipo especialista audita el resultado funcional
```

El equipo 04 es el puente único entre los equipos de Producto y los agentes operativos.

---

# 8. Comunicación entre equipos

Todos los equipos pueden comunicarse entre sí para:

* solicitar criterios;
* advertir contradicciones;
* pedir auditorías;
* revisar impactos;
* resolver dependencias;
* proponer cambios.

Ningún equipo puede aprobar en nombre de otro.

Ejemplos:

```text
Producto Guion puede decir:
“La apertura no cumple el recorrido editorial”.

No puede decidir:
“Debe implementarse un nuevo subagente en Python”.
```

```text
Infraestructura puede decir:
“La propuesta requiere un contrato versionado y un gate”.

No puede decidir:
“La tesis debe cambiar porque no parece suficientemente emotiva”.
```

```text
Adaptación a YouTube puede decir:
“El título promete algo que el guion no entrega”.

No puede decidir:
“El canal debe cambiar su posicionamiento”.
```

---

# 9. Regla de no invasión de responsabilidades

Cuando una decisión exceda el rol propio:

1. El equipo no debe asumirla.
2. Debe identificar qué equipo tiene autoridad.
3. Debe formular la consulta o requisito.
4. Debe esperar la decisión del equipo responsable.
5. Solo después puede continuar dentro de su propio alcance.

La falta de respuesta de otro equipo no autoriza a sustituirlo.

---

# 10. Aprobaciones separadas

Cada equipo aprueba exclusivamente su parte:

```text
01_Inteligencia del Canal
→ aprobación de identidad y perfil editorial

02_Producto Guion
→ aprobación editorial del guion

03_Adaptación a YouTube
→ aprobación de adaptación, plataforma y paquete de publicación

04_Infraestructura y Gobernanza
→ aprobación técnica, arquitectónica y operativa
```

La aprobación completa del producto requiere que todas las áreas necesarias hayan emitido su evaluación correspondiente.

---

# 11. Regla final

```text
Cada equipo decide en su especialidad.
Cada equipo audita su especialidad.
Ningún equipo sustituye a otro.
Infraestructura y Gobernanza es el único puente operativo.
Los agentes ejecutan; los equipos responsables deciden y auditan.
```
