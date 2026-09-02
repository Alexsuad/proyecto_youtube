---
description: Genera diseño narrativo B5-I3 mediante contratos modernos y referencia editorial canónica explícita.
status: AVAILABLE_ONLY_IN_AUTHORIZED_B5_I3_MISSION
current_execution: SOFTWARE_VALIDATES_AND_PERSISTS_AI_COGNITIVE_PROPOSALS
---

> La ejecución requiere una misión B5-I3 activa y autorizada. No aplicar fórmulas de re-hook, timeline, número de eventos, CTA o estructura universal.

## Objetivo

Convertir el diseño editorial validado en recorrido, apertura, cierre y NarrativePlan antes de redactar el guion.

## Entradas obligatorias

- EpisodeBrief y artefactos B5-I1/B5-I2 validados por Software.
- `profile_id`, `profile_version`, `profile_checksum` del perfil editorial activo.
- instrucciones del usuario, duración objetivo y lenguaje objetivo.

## Procedimiento

1. Software verifica contratos, perfil, bindings y checksums.
2. IA decide contenido, función narrativa, progresión y distribución semántica por bloque.
3. Software calcula el presupuesto total y valida la suma de bloques.
4. Software valida schemas, referencias, lineage, persistencia, recuperación e invalidación.

## Salidas contractuales

- ViewerJourney.
- OpeningDesign.
- ClosingDesign.
- NarrativePlan, que incluye los bloques del outline.

## Límites

- No hay re-hook obligatorio, tres eventos obligatorios, CTA obligatorio, Hook → Intro → Evento1 → Evento2 → Evento3 → Clímax → CTA ni 15–25 como estructura universal.
- Cada bloque debe agregar, complicar, contrastar, limitar o transformar la comprensión.
- El CTA puede ser `NONE`; Software no decide si mejora narrativamente el cierre.
