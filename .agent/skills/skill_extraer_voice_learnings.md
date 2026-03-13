# Skill — Extraer Voice Learnings (Aprendizaje de Voz)
Objetivo: Identificar discrepancias entre el guion generado por IA y el guion final editado por un humano para refinar el estilo y tono del canal sin contaminar la memoria de investigación.

> **Rol ejecutor actual:** Antigravity (Analista de Estilo)

---

## Entrada mínima OBLIGATORIA
- `<EP_PATH>/06_guion_longform.md` (IA)
- `<EP_PATH>/06_guion_longform_FINAL.md` (Humano - Opcional)

---

## Pasos
1) **Comparación Dialéctica:** Si existe el archivo `_FINAL`, comparar línea a línea o bloque a bloque.
2) **Identificación de Patrones:**
   - **Reemplazos:** ¿Qué palabras técnicas o complejas cambió el humano por algo más sencillo?
   - **Ritmo:** ¿Se acortaron o alargaron las intros/cierres?
   - **Muletillas:** ¿Qué frases "IA-casas" fueron eliminadas repetidamente?
3) **Refinamiento de Reglas:** Traducir los hallazgos en instrucciones negativas (No usar X) o positivas (Preferir Y).
4) **Gate de Aprobación Humana (OBLIGATORIO):**
   - El sistema NO puede actualizar el perfil global automáticamente.
   - El archivo generado siempre debe terminar con el bloque de estado:
     `APROBACION_HUMANA: PENDIENTE`
     `MIGRADO_A_PERFIL_GLOBAL: NO`
   - El humano debe cambiar PENDIENTE por OK para permitir el paso 5.
5) **Sincronización:**
   - **SI APROBACION_HUMANA != OK:** Solo crear/actualizar `<EP_PATH>/12_voice_learnings.md` con estado PENDIENTE. Prohibido tocar el perfil global.
   - **SI APROBACION_HUMANA == OK:** 
     - Actualizar `workspace/05c_voice_profile.md` con los nuevos patrones.
     - Cambiar marcador a `MIGRADO_A_PERFIL_GLOBAL: SI`.

---

## Salida
- `<EP_PATH>/12_voice_learnings.md`
- `workspace/05c_voice_profile.md`
