---
description:  Genera mapa de eventos y outline del episodio usando el brief y las fuentes de verdad (sin inventar). scope: workspace
---



## Objetivo
Crear el plan del episodio (mapa de eventos + outline con tiempos) sin escribir todavía el guion completo.

## Entradas obligatorias (leer antes de actuar)
- `<EP_PATH>/00_brief_episodio.md` ← **Fuente primaria (Vault V1.2)**
- `input/brief_capitulo.md` ← Fuente legado (usar solo si no hay EP_PATH activo)
- workspace/01_canal_identidad.md
- workspace/02_reglas_editoriales.md
- workspace/03_formato_longform.md
- workspace/04_politica_spoilers.md
- workspace/05_estilo_y_voz.md
- workspace/policy/POLICY_DETECCION_PATRONES_Y_CLICHES_V2.md
- templates/evento_template_v2.md

## Reglas duras
- No inventar datos (obras, años, directores, actores, detalles de trama).
- Si falta información: escribir "PENDIENTE" y listar preguntas concretas al final.
- Cumplir estructura longform y reglas editoriales.
- Re-hook obligatorio entre eventos (solo planificado, no guion).

## Salidas (crear en Vault)
1) `<EP_PATH>/03_mapa_eventos.md`
   - Concepto del episodio
   - Lista de eventos (obras) con objetivo emocional de cada uno
   - Riesgos (spoilers, sensibilidad)
2) `<EP_PATH>/05_outline_escenas.md`
   - Timeline con bloques y tiempos sugeridos para 15–25 min:
     Hook → Intro → Evento 1 → Evento 2 → Evento 3 → (opcional) → Clímax → CTA

## Paso a paso
1) Lee el brief y detecta si faltan obras o variables.
2) Si faltan obras: no propongas datos como hechos. Solo pregunta qué obras usar.
3) Si el brief está completo, genera el mapa de eventos.
4) Genera outline con tiempos y “re-hook” planeado entre eventos.
5) Entrega una sección final: "Pendientes por confirmar" (si aplica).
