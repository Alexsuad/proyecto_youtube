# Política funcional del formato principal — Más Allá del Guion

**Owner funcional:** SCRIPT_PRODUCT
**Owner técnico (implementa y valida):** INFRASTRUCTURE_GOVERNANCE
**Sede canónica de B5_PRE:** `plans/plan_001/B5_PRE_SCRIPT_FOUNDATION.md`
**Estado:** DEFINED (no se aprueban excepciones en esta misión)

---

## 1. Alcance

Esta política gobierna el **formato principal de episodios** de Más Allá del Guion: cuántas obras candidatas y cuántas obras finales sustantivas requiere el formato.

No redefine:

- identidad;
- propósito;
- voz;
- territorios;
- `EditorialProfile`.

La regla pertenece a una política de formato del producto, **no** al `EditorialProfile`.

---

## 2. Regla principal

```text
CANDIDATE_WORKS:
  5–8 como rango operativo normal.

FINAL_SUBSTANTIVE_WORKS:
  3–5 obligatorias para el formato principal.
```

```text
CANDIDATE_WORKS       = 5_TO_8_NORMAL_RANGE
FINAL_SUBSTANTIVE_WORKS:
  minimum = 3
  maximum = 5
```

---

## 3. Qué cuenta como obra sustantiva

Cuenta para el mínimo (3–5) una obra que cumpla **todos**:

- recibe análisis real;
- aporta evidencia narrativa;
- cumple una función diferenciada;
- participa en la progresión argumentativa del episodio.

### 3.1 Criterios positivos

- analizada narrativa y humanamente;
- con evidencia trazable (escena, capítulo, decisión, versión, localizador);
- con función distinguible (introducir, ejemplificar, contrastar, complicar, contradecir, profundizar, revelar consecuencias, cerrar el recorrido).

### 3.2 Criterios negativos (no cuentan para el mínimo)

```text
menciones breves
referencias visuales
citas aisladas
noticias
papers
fuentes académicas
obras nombradas sin análisis
ejemplos incidentales
```

La mera presencia de una obra no la convierte en obra sustantiva para el mínimo.

---

## 4. Excepciones

No se permiten excepciones implícitas. Toda excepción debe declararse explícitamente e incluir:

```text
exception_reason
affected_format
functional_owner
owner_approval
duration_or_scope_impact
argumentative_impact
downstream_gate_effect
```

En esta misión **no** se aprueba ni crea ninguna excepción.

---

## 5. Límites de autoridad

```text
CHANNEL_INTELLIGENCE
→ comprueba compatibilidad con identidad y pertenencia.

SCRIPT_PRODUCT
→ decide candidatas, análisis y curación.

YOUTUBE_ADAPTATION
→ evalúa viabilidad para audiencia y duración.

OWNER
→ aprueba excepciones materiales.

INFRASTRUCTURE_GOVERNANCE
→ implementa y valida la regla técnicamente.
```

El límite se resuelve a `SCRIPT_PRODUCT` para definir candidatas y curación, a `YOUTUBE_ADAPTATION` para viabilidad de plataforma y a `OWNER` para excepciones materiales. Infraestructura implementa y valida, no decide criterio editorial.