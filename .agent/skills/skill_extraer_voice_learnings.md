# Skill — Extraer Voice Learnings (Aprendizaje de Voz)
Objetivo: Identificar discrepancias entre el guion generado por IA y el guion final editado por un humano para refinar el estilo y tono del canal sin contaminar la memoria de investigación.

> **Rol ejecutor actual:** Antigravity (Analista de Estilo)

---

## Entrada mínima OBLIGATORIA
- `<EP_PATH>/06_guion_longform.md` (IA)
- `<EP_PATH>/06_guion_longform_FINAL.md` (Humano - Opcional)
- `profile_id`, `profile_version`, `profile_checksum` del perfil objetivo

Si la referencia no corresponde a un perfil activo válido, devolver `BLOCKED`; no usar fuentes históricas como sustituto.

---

## Pasos
1) **Comparación Dialéctica:** Si existe el archivo `_FINAL`, comparar línea a línea o bloque a bloque.
2) **Identificación de Patrones:**
   - **Reemplazos:** ¿Qué palabras técnicas o complejas cambió el humano por algo más sencillo?
   - **Ritmo:** ¿Se acortaron o alargaron las intros/cierres?
   - **Muletillas:** ¿Qué frases "IA-casas" fueron eliminadas repetidamente?
3) **Refinamiento de Reglas:** Traducir los hallazgos en instrucciones negativas (No usar X) o positivas (Preferir Y).
4) **Salida gobernada (obligatoria):** producir exclusivamente un `EditorialLearningCandidate` JSON validado contra `schemas/editorial_learning_candidate.json`. Incluir los campos obligatorios `learning_id`, `target_profile_id`, `target_profile_version`, `observed_change`, `scope`, `lineage`, `evidence_items`, `confidence`, `examples`, `counterexamples`, `exceptions`, `functional_decision` y `status_history`; cada evidencia incluye `source_id`, `locator`, `checksum` y `observation`.
5) **Estado inicial:** toda salida nueva usa `functional_decision.status: PENDING`; no puede aprobarse ni integrarse desde esta skill.
6) **No integración:** nunca escribir un perfil editorial ni fuentes históricas de voz. La aprobación e integración se realizan en una misión posterior.

---

## Salida
- `<EP_PATH>/12_editorial_learning_candidate.json`
