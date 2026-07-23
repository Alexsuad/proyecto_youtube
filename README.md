# Proyecto YouTube — MasAllaDelGuion

> Alcance y mejoras: consultar [`docs/product/MVP_BASELINE.md`](docs/product/MVP_BASELINE.md) y [`docs/initiatives/README.md`](docs/initiatives/README.md). Ante una mejora fuera de la misión: localizar MVP y Plan 001, comprobar pertenencia y duplicados, capturar problema/valor, clasificar proporcionalmente, evaluar extensión, mantener `implementation_authorized: false`, no ampliar el alcance y continuar el trabajo autorizado. Si falta baseline suficiente, registrar `UNDECIDED` sin inventar alcance ni declarar bloqueo operativo.

> Repositorio de scripts, plantillas y documentación del canal **Más Allá del Guion**.
> La fuente de verdad del *contenido* vive en en el **Content Vault** externo.

---

## Arquitectura: Vault externo

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
| `08_shorts.md` | **Obligatorio** | Guiones de shorts |
| `09_packaging.md` | **Obligatorio** | Títulos y concepto de miniatura |
| `10_seo.md` | **Obligatorio** | Metadatos para YouTube |
| `99_notebooklm_pack.md` | Deseable* | Índice de subida a NotebookLM |

> *`99_notebooklm_pack.md` puede convertirse en obligatorio activando `notebooklm_pack_required: true` en `config/local_settings.json`.

---

## Regla NotebookLM

**NotebookLM es la memoria limpia del canal. Solo recibe "verdades terminadas".**

### ✅ Qué se sube
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

1. Al finalizar el episodio, Antigravity genera `99_notebooklm_pack.md` usando `templates/99_notebooklm_pack_template.md`.
2. El pack incluye: tesis central, obras principales, 5 ideas fuerza, notas de sensibilidad y la lista de archivos a subir.
3. Subir los 4-5 archivos finales a NotebookLM, renombrados con la convención de nombres.
4. Hacer una pregunta de prueba en NotebookLM para verificar que "entiende" el nuevo contenido.
5. Preguntar: *"¿Existe algún episodio anterior con tesis similar o que use las mismas obras?"* para evitar repetición.

---

## Documentos del workspace

La documentación del canal (identidad, voz, reglas editoriales) vive en `workspace/`:

- `workspace/01_canal_identidad.md`
- `workspace/02_reglas_editoriales.md`
- `workspace/03_formato_longform.md`
- `workspace/05_estilo_y_voz.md`
- `workspace/06_convencion_outputs_y_notebooklm_v1.md`
