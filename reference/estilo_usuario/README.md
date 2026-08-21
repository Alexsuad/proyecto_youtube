# `reference/estilo_usuario/` — Biblioteca de Estilo y Voz del Canal

> **METADATA LEGACY — HISTÓRICA / NO EJECUTABLE.** Esta biblioteca es referencia histórica y benchmark; no define la voz activa ni convierte observaciones en reglas. La autoridad vigente procede del `EditorialProfile`, corpus auténtico gobernado y aprendizaje editorial gobernado.

## ¿Qué es esta carpeta?

Aquí viven ejemplos históricos de referencia. No son una fuente ejecutable ni se leen para reconstruir identidad o voz. La autoridad vigente procede exclusivamente de `EditorialProfile`, el corpus auténtico gobernado y el aprendizaje editorial gobernado.

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

- ❌ Investigación de obras o temas → va en el artefacto de investigación del episodio, según el contexto portable o el adaptador seleccionado
- ❌ Guiones de episodios → van en el artefacto de guion del episodio, según el contexto portable o el adaptador seleccionado
- ❌ Outputs del pipeline (shorts, SEO, packaging) → van en sus artefactos contractuales, no en esta biblioteca
- ❌ Fuentes externas o PDFs → solo pasan por un adaptador autorizado; NotebookLM no es requisito ni autoridad
- ❌ Archivos temporales o borradores sin nombre

---

## Importante

> Esta carpeta es parte del **repo (ligera y versionada)** y conserva benchmark histórico.
> Los episodios no van aquí: se resuelven mediante la ruta portable o, de forma opcional, el adaptador Vault legacy.
> `workspace/05_estilo_y_voz.md` es histórico y no constituye consumidor canónico de voz.

---

## Estado actual

Esta carpeta está vacía. Se completará con el primer guion piloto aprobado.
Tareas pendientes:
- [ ] Agregar `glosario_voz.md` con vocabulario real del canal
- [ ] Agregar `frases_prohibidas.md` alineado con `workspace/05_estilo_y_voz.md`
- [ ] Agregar al menos 1 ejemplo de intro aprobado
