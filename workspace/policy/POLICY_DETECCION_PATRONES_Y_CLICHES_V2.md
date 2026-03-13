# POLICY — Detección de Patrones y Clichés (V2)
**Proyecto:** Proyecto YouTube  
**Propósito:** Reducir huellas típicas de “texto de IA” y elevar naturalidad + voz del canal  
**Aplicación:** Obligatoria en guion por eventos y en guion final (GO/NO-GO)

---

## 0) Filosofía de esta policy
Esta policy no busca “borrar estilo”, busca **evitar patrones artificiales** y mantener una voz humana, íntima y reflexiva.

**Regla central:** No solo importan “palabras prohibidas”, también importan:
- patrones repetidos,
- estructura mecánica,
- cierres que suenan a plantilla,
- tono “coach” o “terapia” que no es el canal.

---

## 1) Cómo se usa (programación híbrida)
Este sistema se ejecuta en 2 pasos:

### Paso 1 — Detección (determinista)
- Marcar frases/palabras/patrones con el formato:
  - `[[ELIMINAR: ...]]` o `[[REVISAR: ...]]`
- Generar un reporte corto:
  - Conteo total
  - Top 10 repetidos
  - En qué sección aparece

### Paso 2 — Reescritura (IA controlada)
- Reescribir manteniendo:
  - idea central
  - tono del canal
  - claridad
- Reglas:
  - No inventar información
  - No meter “cierre de plantilla”
  - No meter diagnóstico o terapia

---

## 2) Clasificación por severidad (A/B/C)

### Nivel A — PROHIBIDO SIEMPRE (NO-GO)
Frases/recursos que casi siempre delatan IA o texto corporativo.  
Si aparece cualquiera de estos, **se debe eliminar o reescribir**.

**A.1 Aperturas “de plantilla”**
- “En el vasto mundo de…”
- “En el dinámico panorama de…”
- “En la era actual…”
- “En un mundo donde… (si suena genérico)”

**A.2 Metáforas cliché (huella IA)**
- “un tapiz de…”
- “oro puro”
- “un faro”
- “joya escondida”
- “una montaña rusa de emociones” (si se usa como plantilla)

**A.3 Conectores de ensayo robótico**
- “En última instancia…”
- “Cabe destacar que…”
- “En términos generales…”
- “No cabe duda de que…”

**A.4 Cierres de plantilla (prohibidos)**
- “En resumen…”
- “Para concluir…”
- “Eso sería todo…”
- “Espero que te haya servido…”

> Reglas: El final debe ser **transición** a la siguiente idea/video, no cierre.

---

### Nivel B — CONDICIONAL (REVISAR Y LIMITAR)
Palabras que no son “malas”, pero suenan a IA si:
- se repiten,
- se usan como comodín,
- reemplazan pensamiento real por palabras grandes.

**B.1 Verbos inflados**
- “optimizar”, “maximizar”, “potenciar”, “fomentar”, “facilitar”, “impulsar”
- “empoderar”, “dinamizar”, “transformar” (si suena a marketing)

**B.2 Adjetivos vacíos**
- “increíble”, “impactante”, “poderoso”, “revolucionario”
- “profundo” (si no se demuestra con una idea concreta)

**B.3 Estructuras repetitivas**
- “Primero… segundo… tercero…” en muchos bloques seguidos
- “No solo X, sino también Y…” repetido

**Regla B:** Permitido si aparece 1 vez y suena natural.  
Si se repite o suena “plantilla”, se reescribe.

---

### Nivel C — PERMITIDO (SI ES TU VOZ)
Elementos que pueden sonar humanos y naturales si están bien usados:
- preguntas retóricas reales
- frases cortas con ritmo
- silencios (“…”) si no se abusa
- metáforas personales (no genéricas)

**Regla C:** Si suena a ti, se queda. Si suena “copypaste emocional”, se ajusta.

---

## 3) Patrones estructurales a evitar (más importante que palabras)
Estos patrones delatan IA aunque no haya “palabras prohibidas”.

### P1 — Ensayo académico disfrazado
- definición formal → contexto → lista → mini conclusión
**Reemplazo:** idea directa + ejemplo humano + giro + pregunta.

### P2 — Bloques simétricos perfectos
- todos los párrafos con misma longitud y mismo ritmo
**Reemplazo:** variar ritmo: frase corta → pausa → frase larga → ejemplo.

### P3 — Transiciones mecánicas sin re-hook
- “por otro lado”, “ahora bien”, “además” como muleta
**Reemplazo:** transición con curiosidad:
- “Lo raro es que…”
- “Y aquí viene el problema…”
- “Pero lo que nadie te dice es…”

### P4 — “Valor prometido” sin pago real
- prometer muchas veces sin mostrar un insight claro
**Reemplazo:** pagar valor cada 2–4 minutos (en longform).

### P5 — Cierre moralista o “mensaje bonito”
- termina en frase de póster
**Reemplazo:** termina con:
- una pregunta incómoda,
- una tensión abierta,
- o un puente a otro video.

---

## 4) Anti-coaching y anti-terapia (alineado al canal)
El canal es reflexión y análisis humano, **no terapia**.

### Prohibido (NO-GO o REVISAR fuerte)
- “Esto te va a sanar”
- “Esto te cambiará la vida”
- “Todo pasa por algo”
- “Solo tienes que…”
- “Si te pasa esto, es porque…” (sentencia)

### Reemplazos seguros (permitidos)
- “Puede que…”
- “A veces…”
- “Una lectura posible…”
- “En algunas personas pasa que…”
- “No es una verdad absoluta, pero mira esto…”

**Regla:** hipótesis + humanidad, no diagnóstico ni receta universal.

---

## 5) Reglas de spoilers (para no romper el formato)
- Spoilers permitidos **solo si son necesarios**.
- Spoilers **NO** van en sinopsis.
- Si hay spoiler:
  - aviso claro en 1 frase
  - se coloca en el bloque de análisis

**Marcado recomendado:**
- `[[SPOILER: aviso breve aquí]]`

---

## 6) Checklist GO/NO-GO (para QA)
Antes de aprobar cualquier evento o guion final:

### A) Clichés y huella IA
- [ ] No hay elementos Nivel A
- [ ] Los elementos Nivel B están limitados y suenan naturales
- [ ] No hay 3 conectores mecánicos seguidos
- [ ] No hay cierre de plantilla

### B) Patrones estructurales
- [ ] No hay bloques simétricos repetitivos
- [ ] Hay variación de ritmo
- [ ] Hay re-hook real entre bloques

### C) Ética y tono
- [ ] No hay diagnóstico ni terapia
- [ ] No hay “coach emocional” genérico
- [ ] Mantiene voz íntima y reflexiva

### D) Formato del canal por evento
- [ ] “Obra” (ficha+sinopsis) está entre 10–20%
- [ ] “Análisis humano” está entre 80–90%

**Si falla cualquier punto crítico → NO-GO.**

---

## 7) Modo de actualización (semi-automático con aprobación)
Para mantener control y evitar “ruido”:

### Proceso recomendado (mensual o por cada 5 guiones)
1) El sistema propone nuevas frases sospechosas (candidatas).
2) Se guardan en una lista “pendientes”:
   - `workspace/policy/pending_cliches.md`
3) El usuario aprueba o rechaza.
4) Solo lo aprobado se integra a esta policy.

**Regla:** no se actualiza la lista negra automáticamente sin revisión humana.

---

## 8) Entregables obligatorios cuando se aplica esta policy
Cada vez que se audita texto, se deben producir 2 salidas:

1) `..._marcado.md`  
   Texto con `[[ELIMINAR]] / [[REVISAR]] / [[SPOILER]]`

2) `..._reporte_policy.md`  
   - Conteo de marcas
   - Nivel A/B
   - Top repeticiones
   - Recomendaciones en órdenes (no opiniones)

---

## 9) Nota final (intención del canal)
Este canal no busca sonar “perfecto”, busca sonar **humano**.
Si el texto queda “muy pulido”, probablemente perdió verdad.

**La meta es: claridad + emoción + honestidad + curiosidad.**
