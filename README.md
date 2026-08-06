# Proyecto YouTube — MasAllaDelGuion

> Entrada operativa: consultar primero [`AGENTS.md`](AGENTS.md), [`plans/001_CONTROL_OPERATIVO.md`](plans/001_CONTROL_OPERATIVO.md) y [`docs/product/MVP_BASELINE.md`](docs/product/MVP_BASELINE.md). Ante una mejora fuera de misión: localizar MVP y control operativo, comprobar pertenencia y duplicados, capturar problema/valor, mantener `implementation_authorized: false` y no ampliar alcance.

> Repositorio canónico del sistema editorial de **Más Allá del Guion**. La prioridad activa es el núcleo profesional de Guion hasta `EDITORIAL_SCRIPT_APPROVED`.
> La fuente de verdad del contenido operativo del producto está en el perfil editorial activo y en sus contratos versionados; el *Content Vault* externo contiene trabajo episódico y evidencia operativa.

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

Plan 001 / Plan 003
→ PLAN_001 = PRODUCT_PLAN_RECTOR
→ PLAN_003 = HISTORICAL_CLOSED_NON_NORMATIVE

Estado vivo, misión, autorización, fase, incremento y siguiente acción
→ plans/001_CONTROL_OPERATIVO.md (única sede de autoridad)

PLAN_002
→ sustituido por la arquitectura aprobada; sin autoridad operativa

Contratos ejecutables
→ schemas/ + config/ + src/
```

Los documentos de `workspace/` se conservan como referencia histórica, de migración o apoyo humano. No se debe reconstruir identidad activa ni autoridad ejecutable desde ellos.

## Arquitectura: Vault Externo

Todo el trabajo de un episodio vive **fuera de este repo**, en el Content Vault:

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

La carpeta `output/` de **este repo** se usa exclusivamente para:
- Reportes de auditoría del sistema (Gate 0)
- Logs de ejecución

La configuración del Vault está en `config/local_settings.json`.

---

## Pipeline del episodio (scripts)

El orden actual es: identidad y brief → investigación y evidencia → tesis y curación → análisis y diseño editorial → redacción y edición → verificación → aprobación editorial del guion. Packaging, Shorts, SEO y distribución se conservan como Etapa 2 diferida y no autorizada. Audio pertenece a un repositorio externo futuro; Video está fuera del alcance de este repositorio.

El estado operativo vivo (fase, incremento, misión, autorización y siguiente acción) se resuelve exclusivamente en [`plans/001_CONTROL_OPERATIVO.md`](plans/001_CONTROL_OPERATIVO.md), que es la única sede de autoridad. Este README no replica valores operativos mutables. B5-I3 no está autorizado y S5 real está bloqueado.

Los scripts se encuentran en `src/scripts/`. Se ejecutan en este orden:

| Paso | Script | Qué hace |
|---|---|---|
| 0a | `gate0_auditoria.py` | Audita coherencia del sistema antes de empezar |
| 0b | `gate0_integridad.py` | Verifica integridad del entorno (config, Vault) |
| 1 | `iniciar_episodio.py` | Crea la carpeta del episodio en el Vault y registra en el índice |
| N | `cerrar_episodio.py` | Valida entregables y marca el episodio como completado |

### Uso básico

```powershell
# Auditar antes de empezar
python src/scripts/gate0_auditoria.py

# Iniciar un episodio nuevo
python src/scripts/iniciar_episodio.py

# Cerrar el episodio activo
python src/scripts/cerrar_episodio.py

# Cerrar forzando (pasa los WARN de entregables deseables)
python src/scripts/cerrar_episodio.py --forzar
```

---

## Entregables por episodio

Dentro de la carpeta del episodio en el Vault (`ep_XXXX_slug/`):

| Archivo | Tipo | Descripción |
|---|---|---|
| `00_brief_episodio.md` | Deseable | Semilla del episodio |
| `01_research_bruto.md` | Deseable | Investigación bruta. **NO subir a NotebookLM** |
| `02_curation_obras.md` | Deseable | Obras seleccionadas |
| `06_guion_longform.md` | **Obligatorio** | Guion final aprobado |
| `07_verificacion_veracidad_notebooklm.md` | **Obligatorio** | Gate V — debe tener `ESTADO_GLOBAL: OK` |
| `08_shorts.md` | Futuro / Etapa 2 | Guiones de shorts |
| `09_packaging.md` | Futuro / Etapa 2 | Títulos y concepto de miniatura |
| `10_seo.md` | Futuro / Etapa 2 | Metadatos para YouTube |
| `99_notebooklm_pack.md` | Deseable* | Índice de subida a NotebookLM |

> *`99_notebooklm_pack.md` puede convertirse en obligatorio activando `notebooklm_pack_required: true` en `config/local_settings.json`.

---

## Regla NotebookLM

**NotebookLM es la memoria limpia del canal. Solo recibe "verdades terminadas".**

### ✅ Qué se subirá en la Etapa 2 autorizada
- `06_guion_longform.md` — guion final aprobado
- `08_shorts.md` — shorts finales
- `09_packaging.md` — packaging final
- `10_seo.md` — SEO final
- `99_notebooklm_pack.md` — resumen del episodio

### ❌ Qué NO se sube
- `01_research_bruto.md` — investigación cruda
- Borradores o versiones intermedias
- Archivos de QA o notas de revisión

### Convención de nombres al subir

Renombrar cada archivo con el patrón:

```
EPI_<EP_ID>__<SLUG>__<TIPO>
```

Ejemplo: `EPI_ep_0007__duelo_y_culpa__GUION`

---

## Cómo usar el pack (`99_notebooklm_pack.md`)

1. Al finalizar el episodio, el runtime operativo genera `99_notebooklm_pack.md` usando `templates/99_notebooklm_pack_template.md`.
2. El pack incluye: tesis central, obras principales, 5 ideas fuerza, notas de sensibilidad y la lista de archivos a subir.
3. Subir los 4-5 archivos finales a NotebookLM, renombrados con la convención de nombres.
4. Hacer una pregunta de prueba en NotebookLM para verificar que "entiende" el nuevo contenido.
5. Preguntar: *"¿Existe algún episodio anterior con tesis similar o que use las mismas obras?"* para evitar repetición.

---

## Documentos del workspace

La documentación de `workspace/` ya no es fuente ejecutable única. Su uso actual debe clasificarse así:

- `workspace/00_sistema_agentes_v1.md`: `SUPERSEDED_NON_EXECUTABLE`
- `workspace/01_canal_identidad.md`, `workspace/02_reglas_editoriales.md`, `workspace/03_formato_longform.md`, `workspace/05_estilo_y_voz.md`: `MIGRATION_SOURCE`
- `workspace/06_convencion_outputs_y_notebooklm_v1.md` y contratos auxiliares de operación humana: `HISTORICAL_REFERENCE` o `CANONICAL_REFERENCE` según su función específica

Si una misión necesita un documento concreto de `workspace/`, debe declararlo explícitamente y verificar antes que no haya sido sustituido por una sede canónica más reciente.
