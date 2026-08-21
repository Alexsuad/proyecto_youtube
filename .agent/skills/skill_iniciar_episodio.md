# Skill — Iniciar Episodio (Gate 0 - Creación de EP_PATH)
> **RUTA:** `LEGACY_VAULT_ADAPTER_ONLY`. La ruta portable moderna recibe `EP_PATH` desde el runtime y no requiere esta skill ni `config/local_settings.json`.
Objetivo: crear la carpeta del nuevo episodio en el Vault y registrarlo en el índice.

> **Rol ejecutor actual:** Python (`src/scripts/iniciar_episodio.py`) — esta es una tarea determinista.
> el runtime operativo actúa como orquestador: solicita los datos y delega la ejecución al script.

---

## Entrada mínima
- `config/local_settings.json` (vault_root + channel_id)
- Número de episodio (ej: 1)
- Slug del episodio (ej: abandono_emocional)

---

## Pasos
1) Leer `config/local_settings.json`.
2) Construir `EP_PATH`:
   `<VAULT_ROOT>/<CHANNEL_ID>/episodios/ep_<ID:04d>_<SLUG>/`
3) **Verificar** que `EP_PATH` NO exista (anti-sobrescritura).
   - Si existe: 🔴 STOP — reportar conflicto, NO crear.
4) **Crear** la carpeta `EP_PATH`.
5) **Registrar** en `<VAULT_ROOT>/<CHANNEL_ID>/index/episodes_index.json`:
   ```json
   {
     "ep_id": "ep_0001",
     "slug": "abandono_emocional",
     "ep_path": "...",
     "estado": "en_progreso",
     "creado": "2026-02-19T18:00:00"
   }
   ```
6) Reportar `EP_PATH` activo para que el pipeline lo use.

---

## Script Python requerido
`src/scripts/iniciar_episodio.py`

---

## Salida
- Carpeta `<EP_PATH>/` creada en el Vault.
- `episodes_index.json` actualizado.
- `EP_PATH` disponible como variable de contexto para el resto del pipeline.
