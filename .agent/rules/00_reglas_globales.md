---
trigger: always_on
---

# Reglas Globales — Proyecto YouTube (Antigravity)
Versión: 1.0
Fecha: 19/02/2026
Objetivo: Asegurar consistencia, evitar improvisación y mantener entregables limpios.

---

## 1) Perfil editorial canónico (obligatorio)
Todo consumidor productivo debe recibir o resolver una referencia explícita con `profile_id`, `profile_version` y `profile_checksum`. La ausencia de una configuración activa válida devuelve `BLOCKED` y bloquea controladamente la producción; está prohibido inferir identidad o voz desde `workspace/` o seleccionar automáticamente la versión más reciente.

Los documentos `workspace/` son fuentes históricas o de migración, no identidad activa.

---

## 2) No inventar (regla crítica)
Está prohibido inventar datos sobre:
- obras (libros/películas/series)
- autores, fechas, escenas
- estadísticas o “hechos”

Si falta un dato:
- marcarlo como **PENDIENTE**
- indicar qué falta
- pedirlo al usuario o proponer cómo investigarlo (sin inventar)

---

## 3) Trabajo por fases (gates)
Este proyecto se opera por fases. Cada fase deja un archivo.

Regla:
- no se avanza a la siguiente fase si no existe el archivo de salida de la fase actual.

Si el usuario pide saltarse fases, se debe advertir el riesgo.

---

## 4) Entregables obligatorios por episodio
Todo episodio debe terminar con estos 5 outputs:

1) Guion longform
2) Reporte de Veracidad (Gate V - NotebookLM)
3) Shorts derivados
4) Packaging (títulos + miniatura concepto)
5) SEO YouTube (descripción + capítulos + keywords/tags)

Si el usuario pide “solo el guion”, igual se deja nota de los 5 outputs requeridos.

---

## 5) Estilo de escritura (simple y humano)
- lenguaje claro, sin jerga innecesaria
- evitar frases genéricas tipo “en conclusión” repetitivas
- evitar tono de “coach motivacional”
- mantener voz y ética según el perfil editorial exacto referenciado

---

## 6) Anti-clichés (obligatorio)
Antes de considerar final un guion, debe pasar por QA editorial:
- detectar frases “IA”
- detectar clichés
- proponer reescrituras concretas

---

## 7) Orden y limpieza del repo (entrega limpia)
- No duplicar documentos.
- No dejar “borradores” sin marcar.
- Evitar archivos temporales innecesarios.
- No incluir carpetas locales pesadas en entregables (por ejemplo, entornos virtuales).

---

## 8) Cómo reportar resultados
Cada entrega debe incluir:
- qué archivo se creó o actualizó (ruta exacta)
- qué contiene
- qué falta para la siguiente fase (si aplica)

Objetivo: que el usuario siempre sepa “dónde está la verdad” dentro del repo.
