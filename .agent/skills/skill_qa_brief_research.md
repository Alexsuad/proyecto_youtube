# Skill — QA Automático: Brief y Research (Momento 1)
Objetivo: Auditar la calidad de los entregables del Momento 1 antes de permitir el Gate Humano, asegurando que se cumplan las reglas de completitud y veracidad de fuentes.

> **Rol ejecutor actual:** Antigravity (apoyado mediante script Python determinista)

---

## Entrada mínima
- `<EP_PATH>/00_brief_episodio.md`
- `<EP_PATH>/01_research_bruto.md`
- ID o nombre de la carpeta del episodio (ej: `ep_0001_miedo_al_rechazo`)

---

## Pasos de Validación

### A) Brief (`00_brief_episodio.md`)
1. **FECHA:** Existe y usa el formato YYYY-MM-DD.
2. **TESIS_CENTRAL:** Existe (1 frase clara).
3. **OBRAS_PRINCIPALES:** Lista de 1 a 5 obras máximas.
4. **5_IDEAS_FUERZA:** Contiene *exactamente* 5 bullets.
5. **PREGUNTAS_GUIA:** Contiene entre 8 y 12 preguntas.
6. **NIVEL_SPOILER:** Está explícitamente indicado.
7. **SPOILERS/SENSIBILIDADES:** La sección está presente y llenada.

### B) Research (`01_research_bruto.md`)
8. **Fuentes web reales:** Mínimo 8 URLs detectables con formato `http` / `https`.
9. **Formato de la fuente:** Cada fuente debe indicar Título + URL + "Por qué sirve".
10. **Riesgos y Sensibilidades:** Una sección dedicada a advertencias debe existir.
11. **Alerta de fuentes débiles:** Marcar advertencias si hay mención a "wiki", "fandom" o indicios de blogs sin autor.

---

## Ejecución Determinista
Se debe invocar el script Python asociado:
```bash
python src/scripts/qa_brief_research.py --ep_path <EP_PATH>
```

## Salida
- Genera el reporte en: `output/auditoria_brief_research_<EP_NAME>.md`
- Extraer `ESTADO_GLOBAL`: `PASS` o `FAIL`.
- Si es `FAIL`, el reporte contendrá la lista exacta de correcciones. Se debe corregir antes de pedir Gate Humano.
