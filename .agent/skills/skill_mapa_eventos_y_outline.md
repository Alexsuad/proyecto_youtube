# Skill — Mapa de eventos + Outline (estructura longform)
Objetivo: pasar de "ideas" a estructura clara del episodio.

> **Rol ejecutor actual:** Antigravity (en el futuro puede ser un agente Planner con modelo especializado en estructura narrativa)

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
