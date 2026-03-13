# Arquitectura de Almacenamiento: Repo vs Vault (V1.2 - Configuración Activa)

## Introducción
Este documento detalla la implementación específica de la arquitectura V1.2 para el canal **"MasAllaDelGuion"**.
La clave es separar el **Cerebro (Repo)** del **Cuerpo (Vault)**.

---

## 1. El Repositorio (Lightweight)
**Ruta:** `.../proyecto_youtube/` (Donde estás ahora)

### ¿Qué se guarda aquí?
Solo la lógica, reglas y configuración base.
- 🧠 **Agentes & Skills:** `.agent/skills/`
- 📏 **Reglas & Protocolos:** `.agent/rules/`, `workspace/`
- 📋 **Plantillas:** `templates/`
- 📝 **Auditorías:** `output/` (Reportes de estado, logs de ejecución)
- ⚙️ **Config:** `config/local_settings.example.json` (Plantilla)

**NO se guarda aquí:** Videos, imágenes pesadas, guiones de episodios terminados.

---

## 2. El Content Vault (Heavyweight)
**Ruta Activa:** `C:\YT_VAULT\MasAllaDelGuion\`

### ¿Qué se guarda aquí?
Todo el contenido real del canal.
- 🎬 **Episodios:** Cada uno en su carpeta única.
- 🎨 **Assets:** Recursos multimedia.
- 📚 **Biblioteca:** Referencias permanentes.

### Estructura Real
```text
C:\YT_VAULT\
  └── MasAllaDelGuion\
      ├── episodios\
      │   ├── ep_0001_intro_al_caos\
      │   │   ├── 00_brief.md
      │   │   ├── 06_guion_longform.md
      │   │   └── ...
      │   └── ep_0002_el_viaje\
      └── biblioteca\
          └── (Investigación acumulada)
```

---

## 3. ¿Por qué esto escala a 1000 episodios?
1.  **Velocidad:** El repositorio de código siempre pesará pocos megabytes, sin importar cuántos terabytes de video tengas.
2.  **Seguridad:** Puedes borrar y clonar el repo mil veces para actualizar los agentes, y tu contenido en `C:\YT_VAULT` permanecerá intacto.
3.  **Portabilidad:** `local_settings.json` permite que otro miembro del equipo tenga su Vault en `D:\OtroDisco\Vault`, sin romper el código.

---

## 4. Configuración Técnica
El archivo `config/local_settings.json` (no versionado) conecta ambos mundos:
```json
{
    "vault_root": "C:\\YT_VAULT",
    "channel_id": "MasAllaDelGuion",
    "episode_id_format": "ep_{num:04d}"
}
```
