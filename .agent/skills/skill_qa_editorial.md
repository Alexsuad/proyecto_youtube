# Skill — QA Editorial (Auditoría Estructural y de Voz)
Objetivo: auditar el guion asegurando que cumple **exactamente** la arquitectura MADG y no contiene lenguaje IA o clichés de coaching.

> **Rol ejecutor actual:** Antigravity

---

## Entrada mínima
- `<EP_PATH>/06_guion_longform.md`
- `profile_id`, `profile_version`, `profile_checksum` del perfil usado

---

## Pasos
1) **Gate de perfil:** validar `profile_id`, `profile_version`, `profile_checksum`. Si no corresponde a un perfil activo válido, devolver `BLOCKED`.

2) **Filtro Técnico Estructural:** Auditar el guion midiendo lo siguiente (si falta, el guion reprueba):
   - [ ] ¿Hay exactamente **3 headers** nivel 2 (`## EVENTO 1`, `## EVENTO 2`, `## EVENTO 3`)?
   - [ ] ¿Aparecen exactamente **3** instancias de `**Presentación de la obra:**` y **3** de `**Mini sinopsis breve:**`?
   - [ ] ¿Aparecen al menos **3** instancias de cada marcador conversado: `**Pausa:**`, `**Pregunta al espectador:**` y `**Micro-reacción:**`?
   - [ ] ¿Aparecen exactamente **3** instancias de `**Ejemplo:**` y **3** de `**Herramienta:**`?
   - [ ] ¿Existen exactamente **3** instancias de `**Re-hook:**` al final de los bloques?
   - [ ] ¿Existe un **Puente explícito** conectando el Evento 2 con el Evento 3?
   - [ ] ¿Se cumple la proporción **80/20**?

3) **Filtro de Voz (Poética y Lenguaje):** Revisar si el guion rompió las reglas:
   - [ ] Cero "sonido coaching genérico" y etiquetas psiquiátricas sin matiz.
   - [ ] Cero frases IA cliché ("En resumen", "En conclusión", "Este viaje nos enseña").
   - [ ] Referencia exacta de perfil registrada; coherencia con `IDENTITY_STABLE` y sin políticas de plataforma incrustadas.
   - [ ] Tono humano, directo, conversado.

4) **Reportar y Corregir:**
   - Si el guion Falla en el **Filtro Técnico**, NO RECHACES SIMPLEMENTE. Devuelve una lista de **correcciones concretas operativas** (Ej: "Falta herramienta en bloque 2, insertar X en la línea Y").
   - Si Falla en el **Filtro de Voz**, propone reescrituras de los párrafos exactos.
   
5) **Crear / Sustituir:**
   - `<EP_PATH>/07_qa_revisiones.md`

---

## Salida
- `<EP_PATH>/07_qa_revisiones.md`

Los cambios de identidad se escalan al Equipo 01; esta auditoría no los aprueba.
