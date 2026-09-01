# Skill — Crear Brief de Episodio

## Objetivo
Preparar el `EpisodeBrief` canónico que gobierna B5-I1. La skill coordina
entradas y validación; no delega a la IA la generación de IDs, fechas, perfil,
paths, checksums, lineage, persistencia o estados.

## Entradas
- tema e intención del episodio;
- restricciones editoriales;
- `<EP_PATH>`;
- referencia exacta del perfil activo: `profile_id`, `profile_version`, `profile_checksum`.

## Frontera de responsabilidad
- Software resuelve y valida el perfil activo, contratos, IDs, fechas, rutas,
  checksums, lineage y persistencia.
- La IA puede proponer conflicto, transformación, ángulo, hipótesis, alcance,
  estructura y pregunta solo cuando falte y el contrato lo permita.
- La persona conserva restricciones explícitas, cambios de alcance y decisiones
  reservadas.

## Procedimiento
1. Resolver el perfil editorial activo. Si falta o no coincide exactamente ID, versión y checksum, devolver `BLOCKED`.
2. Conservar la pregunta, obra, corpus, restricciones y contexto proporcionados
   por la persona; solo solicitar una propuesta cognitiva para los campos que
   falten y cuyo contrato permita completarlos.
3. Formular `initial_editorial_hypothesis`: no aprobada, revisable y orientadora. Debe pedir evidencia favorable, evidencia adversarial y lecturas alternativas; no es una tesis provisional.
4. Declarar audiencia concreta y estructura candidata como hipótesis iniciales revisables después de investigar.
3. Definir duración, ritmo y políticas de investigación, citas, atribución, citas textuales y visibilidad de fuentes.
4. Escribir `<EP_PATH>/episode_brief.json` y validarlo contra `schemas/episode_brief.json`.
5. Un Markdown opcional solo puede ser una vista derivada identificada como no canónica.

## Salida
- `<EP_PATH>/episode_brief.json` como única fuente de verdad.

## Bloqueos
- perfil activo ausente o divergente;
- decisión funcional necesaria no disponible;
- contrato inválido o campos sustantivos vacíos.
- ausencia de material narrativo de partida.
