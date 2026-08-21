# Skill — Mapa de eventos + Outline (estructura longform)
> **ESTADO: NO EJECUTABLE ACTUALMENTE.** `config/skill_catalog.json` la difiere a B5-I3; sus reglas históricas no deben reactivarse hasta completar los prerrequisitos canónicos de B5-I3/B6/B7/B7.5.
Objetivo: pasar de "ideas" a estructura clara del episodio.

> **Rol ejecutor actual:** el runtime operativo (en el futuro puede ser un agente Planner con modelo especializado en estructura narrativa)

---

## Entrada mínima
- `<EP_PATH>/00_brief_episodio.md`
- `<EP_PATH>/02_curation_obras.md`
- `profile_id`, `profile_version`, `profile_checksum` del perfil editorial activo

---

## Pasos
1) Verificar el perfil editorial exacto y usar el brief del episodio. Si el perfil está ausente, devolver `BLOCKED`.
   - `<EP_PATH>/02_curation_obras.md`

2) Usar el workflow existente:
   - .agent/workflows/piloto-outline.md

3) Crear:
   - `<EP_PATH>/03_mapa_eventos.md`
   - (si aplica) `<EP_PATH>/05_outline_escenas.md`

---

## Salida
- `<EP_PATH>/03_mapa_eventos.md` (obligatorio)
- `<EP_PATH>/05_outline_escenas.md` (si el flujo ya lo usa)
