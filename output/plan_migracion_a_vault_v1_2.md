# Plan de Migración a Architecture V1.2 (Vault)

## 1. Resumen del Cambio
Se pasa de un modelo "Monolito" (todo en el repo) a un modelo "Desacoplado" (Agentes en Repo + Contenido en Vault).

## 2. Cambios en Documentación
- Actualizado `.agent/rules/01_formato_outputs.md`: Ahora distingue explícitamente entre Repo y Vault.
- Actualizado `workspace/06_convencion_outputs_y_notebooklm_v1.md`: Refleja que el flujo de archivos ocurre dentro del Vault.
- Creado `workspace/07_arquitectura_storage_repo_vs_vault_v1_2.md`: Documento maestro de la nueva arquitectura.
- Creado `templates/config_vault_checklist.md`: Herramienta para configurar el entorno.

## 3. Impacto en Auditorías
- **Auditoría Estructural (Repo):** Seguirá verificando `.agent/skills` y `.agent/rules`, pero ya no buscará guiones en `output/`.
- **Nueva Auditoría de Vault:** Se necesitará un skill nuevo (futuro) que verifique la integridad dentro de `VAULT_ROOT`.
- **Auditoría de No-Sobrescritura:** El riesgo se mitiga estructuralmente al usar carpetas únicas `ep_xxxx_slug` por diseño en el Vault.

## 4. Cómo evitar sobrescritura (Solución V1.2)
El nuevo estándar impone la creación de una carpeta única por episodio:
`<VAULT_ROOT>/<CHANNEL_ID>/episodios/ep_<ID>_<SLUG>/`

Esto **elimina** el riesgo de colisión de archivos que existía en V1, ya que cada episodio tiene su propio espacio de nombres aislado.

## 5. Próximos Pasos de Implementación
1.  Definir las variables de entorno (`VAULT_ROOT`, `CHANNEL_ID`) en el sistema del usuario.
2.  Actualizar los Skills existentes (Writer, Researcher, etc.) para que lean/escriban en la ruta dinámica del Vault en lugar de `output/`.
