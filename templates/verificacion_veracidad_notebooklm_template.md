# Template: Verificación de Veracidad NotebookLM

---

## Encabezado del Episodio

- **ep_id:** `ep_XXXX`
- **slug:** `nombre-del-episodio`
- **fecha:** `YYYY-MM-DD`
- **fuente_verificacion:** NotebookLM
- **documentos_usados:**
  - `<EP_PATH>/01_research_bruto.md`
  - `<EP_PATH>/02_curation_obras.md`
  - `<EP_PATH>/06_guion_longform.md`

---

## ESTADO_GLOBAL: ` OK | WARN | FAIL `

> Reglas:
> - `OK` → todos los claims verificados, sin fallos.
> - `WARN` → hay afirmaciones dudosas; corregir antes de continuar.
> - `FAIL` → hay afirmaciones incorrectas bloqueantes; volver al guion.
>
> **¿Puede avanzar a cierre DONE?**
> - FAIL → ❌ No
> - WARN → ❌ No (salvo justificación explícita firmada por el usuario)
> - OK → ✅ Sí

---

## Tabla de Afirmaciones Verificables (Claims)

| claim_id | frase_del_guion | tipo | estado | soporte_en_fuentes | correccion_sugerida |
|---|---|---|---|---|---|
| C01 | "..." | dato/fecha/filmografía/cita/estadística/contexto | OK / WARN / FAIL | Ref. a fuente en NotebookLM | — |
| C02 | "..." | | | | |
| C03 | "..." | | | | |

> **Tipos de claims a verificar:**
> - `dato` → nombre, lugar, personaje real
> - `fecha` → año de estreno, publicación, acontecimiento
> - `filmografía` → director, actores, duración, estudio
> - `cita` → frase atribuida a persona real
> - `estadística` → cifras, porcentajes, estudios
> - `contexto` → contexto histórico, cultural, institucional
>
> **NO verificar:** interpretaciones emocionales, análisis subjetivos, opiniones del narrador.

---

## WARNINGS

> Afirmaciones dudosas que requieren ajuste antes de continuar.

- [ ] **WARN-01:** ...

---

## FALLOS CRÍTICOS

> Afirmaciones incorrectas que bloquean el avance. El guion debe corregirse.

- [ ] **FAIL-01:** ...

---

## Conclusión

| Criterio | Resultado |
|---|---|
| Claims con FAIL | **0** / Total |
| Claims con WARN | **0** / Total |
| Claims con OK | **0** / Total |
| **¿Puede avanzar a DONE?** | **✅ Sí / ❌ No** |

---

> _Generado por: `skill_verificacion_veracidad_notebooklm.md`_
> _Template: `templates/verificacion_veracidad_notebooklm_template.md`_
