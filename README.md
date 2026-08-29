# Proyecto YouTube — MasAllaDelGuion

> Entrada operativa: consultar primero [`AGENTS.md`](AGENTS.md), [`plans/001_CONTROL_OPERATIVO.md`](plans/001_CONTROL_OPERATIVO.md) y [`docs/product/MVP_BASELINE.md`](docs/product/MVP_BASELINE.md). Ante una mejora fuera de misión: localizar MVP y control operativo, comprobar pertenencia y duplicados, capturar problema/valor, mantener `implementation_authorized: false` y no ampliar alcance.

> Repositorio canónico del sistema editorial de **Más Allá del Guion**. La prioridad activa es el núcleo profesional de Guion hasta `EDITORIAL_SCRIPT_APPROVED`.
> La fuente de verdad del contenido operativo del producto está en el perfil editorial activo y en sus contratos versionados; el *Content Vault* externo es un adaptador legacy opcional para trabajo episódico y evidencia operativa.

---

## Autoridad Canónica

```text
Estado operativo
→ plans/001_CONTROL_OPERATIVO.md

Alcance del MVP
→ docs/product/MVP_BASELINE.md

Identidad y voz productivas
→ config/active_editorial_profile.json
→ config/editorial_profile_registry.json

Plan rector del producto
→ plans/001_reestructuracion_motor_agentico_editorial_y_harness.md

Plan 001
→ PLAN_001 = PRODUCT_PLAN_RECTOR

Estado vivo, misión, autorización, fase, incremento y siguiente acción
→ plans/001_CONTROL_OPERATIVO.md (única sede de autoridad)

Contratos ejecutables
→ schemas/ + config/ + src/
```

Los documentos de `workspace/` se conservan como referencia histórica, de migración o apoyo humano. No se debe reconstruir identidad activa ni autoridad ejecutable desde ellos.

## Almacenamiento y portabilidad

La ruta moderna portable usa los contratos y artefactos del checkout. El Content Vault externo se conserva como ruta legacy opcional para trabajo episódico:

```
C:\YT_VAULT\MasAllaDelGuion\
  episodios\
    ep_0001_slug\
      06_guion_longform.md
      08_shorts.md
      ...
  index\
    episodes_index.json
```

La carpeta `output/` de **este repo** se usa para evidencia técnica del runtime:
- Reportes de auditoría y gates
- Logs y diagnósticos de ejecución
- Provenance y estado técnico gobernado

`output/` nunca es sede de contenido editorial canónico; los contratos y registros ejecutables viven en `schemas/`, `config/` y `src/`.

La configuración del Vault está en `config/local_settings.json`; no es una dependencia universal de Gate 0 ni del cierre del MVP.

---

## Pipeline del episodio (scripts)

El orden actual es: identidad y brief → investigación y evidencia → tesis y curación → análisis y diseño editorial → redacción y edición → verificación → aprobación editorial del guion. Packaging, Shorts, SEO y distribución se conservan como Etapa 2 diferida y no autorizada. Audio pertenece a un repositorio externo futuro; Video está fuera del alcance de este repositorio.

El estado operativo vivo (fase, incremento, misión, autorización y siguiente acción) se resuelve exclusivamente en [`plans/001_CONTROL_OPERATIVO.md`](plans/001_CONTROL_OPERATIVO.md), que es la única sede de autoridad. Este README no replica valores operativos mutables. B5-I3 no está autorizado y S5 real está bloqueado.

Los scripts de la tabla son entrypoints de control del episodio, no un inventario exhaustivo del pipeline funcional. La ruta funcional B5-I1/B5-I2 y sus gates se describe en el workflow operativo; los dos gates B5-I2 pertenecen a superficies distintas (`SCRIPT_PRODUCT` y `YOUTUBE_ADAPTATION`).

Los scripts se encuentran en `src/scripts/`. Los entrypoints de control son:

| Paso | Script | Qué hace |
|---|---|---|
| 0a | `gate0_auditoria.py` | Audita coherencia del sistema antes de empezar |
| 0b | `gate0_integridad.py` | Verifica integridad del entorno; usa ruta portable si falta configuración local |
| 1 | `iniciar_episodio.py` | Opcional: crea la carpeta del episodio en el Vault legacy |
| N | `cerrar_episodio.py` | Valida entregables y marca el episodio como completado |

La entrada de producto para personas y automatizaciones es `python -m src.cli iniciar`; su funcionamiento y las tres modalidades están documentados en [`docs/product/CLI_OPERACION.md`](docs/product/CLI_OPERACION.md). `iniciar_episodio.py` permanece como wrapper legacy compatible.

### Uso básico

```powershell
# Entrada de producto interactiva
python -m src.cli iniciar

# Entrada de producto no interactiva
python -m src.cli iniciar --modo tema --tema "Tema del episodio"

# Entrada no interactiva con pregunta y contexto separados
python -m src.cli iniciar --modo tema --tema "Tema del episodio" --pregunta "Pregunta concreta" --contexto "Contexto adicional"

# Auditar antes de empezar
python src/scripts/gate0_auditoria.py

# Iniciar un episodio nuevo en Vault (opcional, solo ruta legacy)
python src/scripts/iniciar_episodio.py

# Cerrar una ruta portable del episodio
python src/scripts/cerrar_episodio.py --episode-path <EP_PATH> --ep-id <EP_ID>
```

---

## Entregables por episodio

Dentro de `<EP_PATH>` —checkout portable o adaptador Vault legacy— (`ep_XXXX_slug/` cuando aplica):

| Archivo | Tipo | Descripción |
|---|---|---|
| `00_brief_episodio.md` | Deseable | Semilla del episodio |
| `01_research_bruto.md` | Deseable | Investigación bruta. **NO subir a NotebookLM** |
| `02_curation_obras.md` | Deseable | Obras seleccionadas |
| `06_guion_longform.md` | **Obligatorio** | Guion final aprobado |
| `07_verificacion_veracidad_notebooklm.md` | Adaptador legacy opcional | Verificación externa histórica; no es gate universal ni autoridad |
| `08_shorts.md` | Futuro / Etapa 2 | Guiones de shorts |
| `09_packaging.md` | Diferido / Etapa 2 | Títulos y concepto de miniatura; no requerido para cerrar el MVP |
| `10_seo.md` | Diferido / Etapa 2 | Metadatos para YouTube; no requerido para cerrar el MVP |
| `99_notebooklm_pack.md` | Opcional | Índice para un adaptador externo, si se decide usarlo |

> La ausencia de archivos Markdown legacy u otros artefactos opcionales no bloquea la ruta portable moderna. Los entregables obligatorios del cierre y sus contratos deben existir y superar sus validaciones; una configuración local no puede convertir un adaptador en autoridad universal.

---

## Regla NotebookLM

**NotebookLM es un adaptador opcional y no autoritativo.** Su ausencia no impide el pipeline portable; la autoridad permanece en los contratos, el perfil editorial activo y los artefactos gobernados del episodio.

### Uso opcional, cuando exista un adaptador autorizado
- `08_shorts.md` — shorts finales
- `09_packaging.md` — packaging final
- `10_seo.md` — SEO final
- `99_notebooklm_pack.md` — resumen del episodio

### ❌ Qué NO se sube
- `01_research_bruto.md` — investigación cruda
- Borradores o versiones intermedias
- Archivos de QA o notas de revisión

### Convención de nombres del adaptador

Renombrar cada archivo con el patrón:

```
EPI_<EP_ID>__<SLUG>__<TIPO>
```

Ejemplo: `EPI_ep_0007__duelo_y_culpa__GUION`

---

## Cómo usar el pack (`99_notebooklm_pack.md`)

1. Si se habilita el adaptador, puede generarse `99_notebooklm_pack.md` usando `templates/99_notebooklm_pack_template.md`.
2. El pack incluye: tesis central, obras principales, 5 ideas fuerza, notas de sensibilidad y la lista de archivos a subir.
3. Transferir los archivos solo si la ruta opcional está disponible y autorizada.
4. No usar el adaptador como fuente de verdad ni como condición para cerrar el episodio.

---

## Documentos del workspace

La documentación de `workspace/` ya no es fuente ejecutable única. Su uso actual debe clasificarse así:

- `workspace/00_sistema_agentes_v1.md`: `SUPERSEDED_NON_EXECUTABLE`
- `workspace/01_canal_identidad.md`, `workspace/02_reglas_editoriales.md`, `workspace/03_formato_longform.md`, `workspace/05_estilo_y_voz.md`: `MIGRATION_SOURCE`
- `workspace/06_convencion_outputs_y_notebooklm_v1.md` y contratos auxiliares de operación humana: `HISTORICAL_REFERENCE` o `CANONICAL_REFERENCE` según su función específica

Si una misión necesita un documento concreto de `workspace/`, debe declararlo explícitamente y verificar antes que no haya sido sustituido por una sede canónica más reciente.
