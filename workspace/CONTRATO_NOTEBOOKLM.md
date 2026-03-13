# CONTRATO DE USO — NotebookLM (MasAllaDelGuion) — V1

## 1) Propósito de este cuaderno
Este cuaderno define las reglas para usar NotebookLM como **memoria limpia** del canal **MasAllaDelGuion**.

NotebookLM aquí cumple una sola función:
- **Conservar conocimiento final y verificable** de cada episodio y del ADN del canal.
- Servir como base para que otro sistema (equipo Antigravity) pueda **consultar y producir** guiones y piezas sin confusión.

> NotebookLM NO es el lugar para borradores ni para investigación cruda.

---

## 2) Cómo se usa NotebookLM dentro del proyecto
NotebookLM se alimenta con:
- Piezas finales del episodio (entregables terminados).
- Reglas del canal (ADN, tono, estructura).
- Plantillas oficiales del sistema.

Y se consulta para:
- Recuperar tesis, ideas fuerza, enfoques y decisiones.
- Generar variantes (títulos, hooks, shorts) basadas en episodios cerrados.
- Mantener consistencia del tono del canal.

---

## 3) Qué se sube (permitido)
Solo se suben **verdades terminadas**.

### Entregables del episodio (finales)
- `06_guion_longform.md`
- `08_shorts.md`
- `09_packaging.md`
- `10_seo.md`
- `99_notebooklm_pack.md`

### Documentación del sistema (reglas y plantillas)
- Convenciones y reglas oficiales del repo relacionadas con outputs y NotebookLM.
- Plantillas oficiales (por ejemplo, la plantilla del pack).

---

## 4) Qué NO se sube (prohibido)
No se sube nada que convierta NotebookLM en un basurero.

### Prohibido subir:
- Borradores, versiones a medias, ideas sueltas sin cierre.
- Investigación cruda (links sin procesar, notas desordenadas).
- Prompts internos, conversaciones largas, logs.
- Reportes temporales que cambian constantemente.
- Archivos duplicados (subir lo mismo con nombres distintos).

---

## 5) Convención de nombres al subir fuentes (obligatorio)
Cada archivo subido a NotebookLM debe renombrarse con este patrón:

`EPI_<EP_ID>__<SLUG>__<TIPO>`

Donde `<TIPO>` puede ser:
- `GUION`
- `SHORTS`
- `PACKAGING`
- `SEO`
- `PACK`

### Ejemplos
- `EPI_ep_0007__duelo_y_culpa__GUION`
- `EPI_ep_0007__duelo_y_culpa__SHORTS`
- `EPI_ep_0007__duelo_y_culpa__PACKAGING`
- `EPI_ep_0007__duelo_y_culpa__SEO`
- `EPI_ep_0007__duelo_y_culpa__PACK`

---

## 6) Checklist de carga por episodio (V1)
Cuando un episodio esté cerrado, antes de considerarlo “memoria disponible”, se debe cumplir:

- [ ] Existe `99_notebooklm_pack.md` completo (incluye OBRAS_PRINCIPALES).
- [ ] Existen los entregables finales: `06`, `08`, `09`, `10`.
- [ ] Se subieron a NotebookLM los 5 archivos finales.
- [ ] Todos fueron renombrados con la convención `EPI_<EP_ID>__<SLUG>__<TIPO>`.
- [ ] No se subió investigación cruda ni borradores.

---

## 7) Formato de respuesta esperado (para consistencia)
Cuando se consulte este cuaderno, NotebookLM debe responder usando:

1) **Resumen corto (3–5 bullets)**
2) **Tesis central (1 frase)**
3) **Ideas fuerza (lista)**
4) **Obras principales (lista)**
5) **Checklist accionable (si aplica)**

> Si falta información en las fuentes, NotebookLM debe decirlo claramente y no inventar.

---

## 8) Prueba mínima de calidad (post-carga)
Después de subir un episodio, ejecutar estas 3 consultas dentro de NotebookLM:

1) **Tesis + ideas fuerza**
  - “Dame la tesis central y las 5 ideas fuerza del episodio `<EP_ID>`.”

2) **Packaging**
  - “Dame 10 títulos y 5 hooks basados en el episodio `<EP_ID>`, manteniendo el ADN del canal.”

3) **Shorts**
  - “Propón 8 shorts derivados del episodio `<EP_ID>` con gancho en la primera frase.”

Si las respuestas son coherentes y consistentes, el episodio queda listo como “memoria útil”.

---

## 9) Regla final (la más importante)
NotebookLM solo conserva lo que ya está listo para usarse.

**Si no está terminado, no entra.**
