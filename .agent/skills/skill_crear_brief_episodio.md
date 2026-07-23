# Skill — Crear Brief de Episodio

## Objetivo
Crear el `EpisodeBrief` canónico que gobierna B5-I1.

## Entradas
- tema e intención del episodio;
- restricciones editoriales;
- `<EP_PATH>`;
- referencia exacta del perfil activo: `profile_id`, `profile_version`, `profile_checksum`.

## Procedimiento
1. Resolver el perfil editorial activo. Si falta o no coincide exactamente ID, versión y checksum, devolver `BLOCKED`.
2. Definir pregunta central, conflicto, transformación, ángulo, alcance, fuera de alcance, tipo de guion y estructura candidata.
3. Definir duración, ritmo y políticas de investigación, citas, atribución, citas textuales y visibilidad de fuentes.
4. Escribir `<EP_PATH>/episode_brief.json` y validarlo contra `schemas/episode_brief.json`.
5. Un Markdown opcional solo puede ser una vista derivada identificada como no canónica.

## Salida
- `<EP_PATH>/episode_brief.json` como única fuente de verdad.

## Bloqueos
- perfil activo ausente o divergente;
- decisión funcional necesaria no disponible;
- contrato inválido o campos sustantivos vacíos.
