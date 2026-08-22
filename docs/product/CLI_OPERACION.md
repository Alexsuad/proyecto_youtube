# Entrada de la aplicación por Terminal

La entrada de producto para pruebas se ejecuta desde la raíz del repositorio:

```powershell
python -m src.cli iniciar
```

También acepta una entrada automatizable con el mismo núcleo:

```powershell
python -m src.cli iniciar --modo tema --tema "Por qué nos cuesta abandonar una vida que ya no queremos" --pregunta "¿Por qué seguimos en trabajos, relaciones, ciudades o proyectos que sabemos que ya no nos hacen bien?" --contexto "Contexto adicional opcional"
python -m src.cli iniciar --modo obra --obra "Her" --pregunta "¿Qué quiero explorar?" --contexto "Contexto opcional"
python -m src.cli iniciar --modo corpus --obras "Her" "Lost in Translation" "Black Mirror"
```

Las modalidades son `TOPIC_FIRST`, `ANCHOR_WORK_FIRST` y `CORPUS_FIRST`. La obra o el corpus de entrada son puntos de partida y no selección final.

## Reanudar

```powershell
python -m src.cli reanudar ep_0001
```

La aplicación consulta el índice del Vault, reconstruye la entrada persistida y vuelve a entregar el episodio al coordinador controlado. La entrada humana original queda en `00_human_input.json` y el handoff hacia `topic_belonging_input` en `01_editorial_intake_handoff.json`. Las solicitudes pendientes se guardan en `human_decision_requests.json`; una respuesta se guarda en `human_decisions.json` y su consecuencia idempotente en `workflow_transitions.json`.

## Fronteras

`src.cli` solo presenta preguntas y normaliza respuestas del canal `TERMINAL`. `src/application` coordina contratos, workflow y persistencia. `VaultEpisodeStore` escribe en el `vault_root` y `channel_id` de `config/local_settings.json`; la ruta puede ser local, montada o sincronizada con Drive sin añadir Google OAuth ni una dependencia de Drive.

El handoff no inventa ángulo, territorio, evidencia ni decisiones editoriales. `CHANNEL_INTELLIGENCE`, `SCRIPT_PRODUCT` y `YOUTUBE_ADAPTATION` continúan siendo responsables de sus decisiones y gates. La preparación registra la frontera autorizada de B5-I1, pero no ejecuta B5-I2, B5-I3, producción ni publicación.

Las aprobaciones futuras usan el puerto `HumanInteraction`. El adaptador Terminal presenta las opciones y convierte `A/E/C/R` en decisiones normalizadas. La solicitud inmutable conserva el prompt, las opciones, la recomendación, el episodio, el workflow y el checksum del sujeto; la respuesta solo referencia el request por `request_id` y `request_checksum`. Telegram podrá implementar el mismo puerto sin añadir lógica editorial.

`src/scripts/iniciar_episodio.py` solo conserva compatibilidad técnica con el formato antiguo `--num/--slug`. Sus registros quedan marcados como `LEGACY_TECHNICAL_INITIALIZATION` y no crean una entrada humana ni una modalidad editorial.
