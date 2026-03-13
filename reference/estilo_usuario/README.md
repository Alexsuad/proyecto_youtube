# `reference/estilo_usuario/` — Biblioteca de Estilo y Voz del Canal

## ¿Qué es esta carpeta?

Aquí viven los **ejemplos de referencia** que definen cómo suena y se escribe este canal.
Antigravity los lee cuando no existe un guion piloto aprobado, y los usa como guía de tono, ritmo y vocabulario.

---

## ¿Qué tipo de archivos van aquí?

| Archivo | Contenido |
|---|---|
| `ejemplo_intro_01.md` | Introducciones que funcionaron (primeros 60 segundos) |
| `ejemplo_transicion_01.md` | Frases puente entre segmentos |
| `ejemplo_cierre_01.md` | Cierres y CTAs que suenan naturales |
| `glosario_voz.md` | Vocabulario propio del canal: palabras frecuentes, giros, muletillas permitidas |
| `frases_prohibidas.md` | Anti-clichés y frases "IA" a evitar en cualquier guion |

### Convención de nombres

- `ejemplo_<tipo>_<numero>.md` → ejemplos concretos de guion
- `glosario_voz.md` → vocabulario único del canal
- `frases_prohibidas.md` → lista negra de frases

---

## ¿Qué NO va aquí?

- ❌ Investigación de obras o temas → va en `<EP_PATH>/01_research_bruto.md` (Vault)
- ❌ Guiones de episodios → van en `<EP_PATH>/06_guion_longform.md` (Vault)
- ❌ Outputs del pipeline (shorts, SEO, packaging) → van en el Vault
- ❌ Fuentes externas o PDFs → van en NotebookLM
- ❌ Archivos temporales o borradores sin nombre

---

## Importante

> Esta carpeta es parte del **repo (ligera y versionada)**.
> Los episodios NO van aquí: siempre en el Vault (`C:\YT_VAULT\MasAllaDelGuion\episodios\`).
>
> Referenciada por: `workspace/05_estilo_y_voz.md` → sección 8 "Entrenamiento por guion ejemplo".

---

## Estado actual

Esta carpeta está vacía. Se completará con el primer guion piloto aprobado.
Tareas pendientes:
- [ ] Agregar `glosario_voz.md` con vocabulario real del canal
- [ ] Agregar `frases_prohibidas.md` alineado con `workspace/05_estilo_y_voz.md`
- [ ] Agregar al menos 1 ejemplo de intro aprobado
