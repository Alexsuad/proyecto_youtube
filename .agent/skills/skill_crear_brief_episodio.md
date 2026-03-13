# Skill — Crear Brief de Episodio
Objetivo: crear el documento base para iniciar el pipeline sin confusiones.

> **Rol ejecutor actual:** Antigravity (en el futuro puede ser un agente independiente con modelo configurable en `config/agents_config.json`)

---

## Entrada mínima
- Tema del episodio
- Intención del episodio (qué debe sentir/entender la audiencia)
- Restricciones (spoilers sí/no, tono, límite de duración si aplica)
- `<EP_PATH>`: ruta del episodio activo en el Vault (viene del `skill_iniciar_episodio`)

---

## Pasos
1) Leer primero:
   - workspace/01_canal_identidad.md
   - workspace/02_reglas_editoriales.md
   - workspace/05_estilo_y_voz.md

2) Crear el archivo:
   - `<EP_PATH>/00_brief_episodio.md`

3) El brief debe incluir:
   - FECHA: Insertar automáticamente la fecha actual (YYYY-MM-DD).
   - Tema
   - Objetivo emocional (qué se busca provocar)
   - Promesa al espectador (qué se lleva)
   - Límites y NO-GO (según reglas del canal)
   - PENDIENTES (si falta info)

---

## Salida
- `<EP_PATH>/00_brief_episodio.md` (listo y claro)
