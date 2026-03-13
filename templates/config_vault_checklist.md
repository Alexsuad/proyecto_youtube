# Checklist de Validación: Configuración Vault V1.2

Este checklist asegura que el entorno local esté correctamente configurado para conectar el Repositorio con el Vault.

## 1. Verificación de Archivos de Configuración
- [ ] Existe `config/local_settings.json` (no versionado).
- [ ] Existe `config/local_settings.example.json` (versionado).
- [ ] `.gitignore` incluye `config/local_settings.json`.

## 2. Validación del Content Vault
- [ ] La ruta raíz existe: `C:\YT_VAULT`
- [ ] La carpeta del canal existe: `C:\YT_VAULT\MasAllaDelGuion\`
- [ ] La carpeta de episodios existe: `C:\YT_VAULT\MasAllaDelGuion\episodios\`
- [ ] Permisos de escritura verificados (intentar crear un archivo de prueba).

## 3. Prueba de Conexión (Simulada)
- [ ] `VAULT_ROOT` es correcto: `C:\YT_VAULT`
- [ ] `CHANNEL_ID` es correcto: `MasAllaDelGuion`
- [ ] Formato de episodio esperado: `ep_0001`

Si alguna verificación falla, revisar `config/local_settings.json` y los permisos del sistema operativo.
