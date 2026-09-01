"""Human-oriented product entrypoint for the Terminal channel."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from src.application.contracts import EntryMode, HumanInput, InputValidationError
from src.application.interaction import TerminalInteraction, UserCancelled
from src.application.service import EpisodeApplicationService
from src.application.storage import StorageError, VaultEpisodeStore
from src.application.topic_belonging import ExecutionCognitiveBoundary, build_topic_belonging_service
from src.core.p2_real_reporter import build_p2_report, render_p2_report


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SETTINGS = REPO_ROOT / "config" / "local_settings.json"


def _load_synthetic_outputs(path: str | Path | None) -> dict[str, dict[str, Any]] | None:
    if path is None:
        return None
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"SYNTHETIC_OUTPUTS_INVALID:{exc}") from exc
    if not isinstance(payload, dict) or any(
        stage not in payload or not isinstance(payload[stage], dict)
        for stage in ("enrich", "produce", "review")
    ):
        raise ValueError("SYNTHETIC_OUTPUTS_INVALID:required stages are enrich, produce and review")
    return payload


def _service(
    settings: str | Path = DEFAULT_SETTINGS,
    *,
    mission_authorization_path: str | None = None,
    execution_mode: str = "REAL",
    mock_outputs: dict[str, dict[str, Any]] | None = None,
    execution_profile: str | None = None,
    execution_family: str | None = None,
    execution_family_selection_path: str | None = None,
    model_override: str | None = None,
    reasoning_effort: str | None = None,
    paid_cost_approved: bool = False,
    operational_authority_path: str | None = None,
    mission_contract_path: str | None = None,
    completion_gate_result_path: str | None = None,
    mission_repo_root: str | None = None,
) -> EpisodeApplicationService:
    store = VaultEpisodeStore.from_settings(settings)
    return EpisodeApplicationService(
        store,
        workflow=build_topic_belonging_service(
            store,
            boundary=ExecutionCognitiveBoundary(
                repository_root=REPO_ROOT,
                mission_authorization_path=mission_authorization_path,
                execution_mode=execution_mode,
                mock_outputs=mock_outputs,
                execution_profile=execution_profile,
                execution_family=execution_family,
                execution_family_selection_path=execution_family_selection_path,
                operational_authority_path=operational_authority_path,
                model_override=model_override,
                reasoning_effort=reasoning_effort,
                paid_cost_approved=paid_cost_approved,
                mission_contract_path=mission_contract_path,
                completion_gate_result_path=completion_gate_result_path,
                mission_repo_root=mission_repo_root,
            ),
        ),
        interaction=TerminalInteraction(),
    )


def _service_from_args(args: argparse.Namespace) -> EpisodeApplicationService:
    synthetic_outputs = _load_synthetic_outputs(getattr(args, "synthetic_outputs", None))
    return _service(
        args.config,
        mission_authorization_path=getattr(args, "mission_authorization", None),
        execution_mode="SYNTHETIC_TEST" if synthetic_outputs is not None else "REAL",
        mock_outputs=synthetic_outputs,
        execution_profile=getattr(args, "execution_profile", None),
        execution_family=getattr(args, "execution_family", None),
        execution_family_selection_path=getattr(args, "execution_family_selection_path", None),
        model_override=getattr(args, "model_override", None),
        reasoning_effort=getattr(args, "reasoning_effort", None),
        paid_cost_approved=bool(getattr(args, "paid_cost_approved", False)),
        operational_authority_path=getattr(args, "operational_authority_path", None),
        mission_contract_path=getattr(args, "mission_contract_path", None),
        completion_gate_result_path=getattr(args, "completion_gate_result_path", None),
        mission_repo_root=getattr(args, "mission_repo_root", None),
    )


def _interactive_input() -> HumanInput:
    terminal = TerminalInteraction()
    terminal.present("¿Cómo quieres comenzar?\n")
    mode = terminal.choose(
        "Selecciona una modalidad:",
        [(EntryMode.TOPIC_FIRST.value, "Tema"), (EntryMode.ANCHOR_WORK_FIRST.value, "Una obra"), (EntryMode.CORPUS_FIRST.value, "Varias obras")],
    )
    if mode == EntryMode.TOPIC_FIRST:
        content = terminal.free_text("Escribe el tema:")
        works: list[str] = []
    elif mode == EntryMode.ANCHOR_WORK_FIRST:
        content = terminal.free_text("Escribe la obra de partida:")
        works = [content]
    else:
        content = ""
        works = []
        terminal.present("Escribe una obra por línea. Deja una línea vacía para terminar.")
        while True:
            item = terminal.free_text("Obra", optional=True)
            if item is None:
                break
            works.append(item)
    initial_question = terminal.free_text("¿Tienes una pregunta concreta?", optional=True)
    context = terminal.free_text("¿Quieres añadir contexto o explicación adicional?", optional=True)
    instructions: list[dict[str, str]] = []
    while terminal.confirm("¿Quieres añadir una indicación?"):
        category = terminal.choose(
            "Selecciona la categoría de la indicación:",
            [
                ("CONTEXT_ONLY", "Solo contexto"),
                ("MAY_INCLUDE", "Se puede incluir"),
                ("MUST_INCLUDE", "Debe incluirse"),
                ("MUST_INCLUDE_VERBATIM", "Debe incluirse literalmente"),
            ],
        )
        text = terminal.free_text("Escribe la indicación:")
        instructions.append({"category": category, "text": text})
    duration_option = terminal.choose(
        "Selecciona la duración objetivo:",
        [
            ("automatic", "Automática"),
            ("15", "15 minutos"),
            ("20", "20 minutos"),
            ("25", "25 minutos"),
            ("30", "30 minutos"),
            ("custom", "Personalizada"),
        ],
    )
    if duration_option == "custom":
        raw_minutes = terminal.free_text("¿Cuántos minutos debe durar?")
        try:
            duration_minutes = int(raw_minutes)
        except (TypeError, ValueError) as exc:
            raise InputValidationError("La duración personalizada requiere minutos enteros.") from exc
    elif duration_option == "automatic":
        duration_minutes = None
    else:
        duration_minutes = int(duration_option)
    language_option = terminal.choose(
        "Selecciona el idioma objetivo:",
        [
            ("default", "Predeterminado del canal"),
            ("es", "Español"),
            ("en", "Inglés"),
            ("other", "Otro"),
        ],
    )
    target_language = terminal.free_text("¿Cuál es el idioma objetivo?") if language_option == "other" else language_option
    terminal.present(
        "\nResumen:\n"
        f"Modalidad: {mode}\n"
        f"Contenido: {content or '(corpus inicial)'}\n"
        f"Obras: {', '.join(works) if works else '(se determinarán durante el flujo editorial)'}\n"
        f"Pregunta inicial: {initial_question or '(sin pregunta inicial)'}\n"
        f"Contexto: {context or '(sin contexto adicional)'}\n"
        f"Indicaciones: {len(instructions)}\n"
        f"Duración objetivo: {duration_minutes or 'automática'}\n"
        f"Idioma objetivo: {target_language or 'predeterminado del canal'}"
    )
    if not terminal.confirm("¿Iniciar?"):
        raise UserCancelled
    return HumanInput.create(
        mode=mode,
        content=content,
        initial_question=initial_question,
        context=context,
        works=works,
        user_instructions=instructions,
        duration_target_minutes=duration_minutes,
        target_language=target_language,
        channel="TERMINAL",
    )


def _non_interactive_input(args: argparse.Namespace) -> HumanInput:
    mode = args.modo
    if mode == "tema":
        content, works = args.tema, []
    elif mode == "obra":
        content, works = args.obra, [args.obra] if args.obra else []
    else:
        content, works = "", list(args.obras or [])
    duration = getattr(args, "duracion", None)
    custom_duration = getattr(args, "duracion_minutos", None)
    if duration in {"automatico", "automático", "default", "predeterminado", None}:
        if duration is not None and custom_duration is not None:
            raise InputValidationError("Usa --duracion-minutos solo con duración personalizada.")
        duration_minutes = custom_duration if duration is None else None
    elif str(duration).lower() == "personalizada":
        duration_minutes = custom_duration
    else:
        try:
            duration_minutes = int(duration)
        except (TypeError, ValueError) as exc:
            raise InputValidationError("La duración debe ser automática, personalizada o un número de minutos.") from exc
        if custom_duration is not None:
            raise InputValidationError("Usa --duracion-minutos solo con duración personalizada.")
    instructions = []
    for raw_instruction in getattr(args, "indicacion", None) or []:
        separator = next((item for item in (":", "|", "=") if item in raw_instruction), None)
        if separator is None:
            category, text = "CONTEXT_ONLY", raw_instruction
        else:
            category, text = raw_instruction.split(separator, 1)
        instructions.append({"category": category, "text": text})
    return HumanInput.create(
        mode=mode,
        content=content,
        initial_question=getattr(args, "pregunta", None),
        context=getattr(args, "contexto", None),
        works=works,
        user_instructions=instructions,
        duration_target_minutes=duration_minutes,
        target_language=getattr(args, "idioma", None),
        channel="TERMINAL",
    )


def _start(args: argparse.Namespace) -> int:
    try:
        human_input = _interactive_input() if args.modo is None else _non_interactive_input(args)
        result = _service_from_args(args).start(human_input)
    except UserCancelled:
        print("Operación cancelada por el usuario.")
        return 130
    except (InputValidationError, StorageError, PermissionError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 2
    print(f"Episodio creado: {result.episode.episode_id}")
    print("Entrada registrada.")
    if result.workflow.get("status") == "PENDING_EXTERNAL_RESULT":
        print("Primer handoff de Topic Belonging preparado; esperando resultado externo.")
    else:
        print("Topic Belonging alcanzó su gate técnico; el flujo se detuvo antes de investigación y guion.")
    return 0


def _resume(args: argparse.Namespace) -> int:
    try:
        state = _service_from_args(args).resume(args.episodio)
    except (StorageError, PermissionError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 2
    print(f"Episodio reanudado: {args.episodio}")
    print(f"Estado: {state['state'].get('status', 'desconocido')}")
    print(f"Ruta: {state['folder']}")
    return 0


def _import_result(args: argparse.Namespace) -> int:
    try:
        state = _service_from_args(args).import_external_result(args.resultado)
    except (StorageError, PermissionError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 2
    episode_id = state["state"].get("episode_id", "desconocido")
    status = state["state"].get("status", "desconocido")
    print(f"Resultado externo importado: {episode_id}")
    print(f"Estado: {status}")
    return 0


def _report_p2(args: argparse.Namespace) -> int:
    try:
        episode = VaultEpisodeStore.from_settings(args.config).resume(args.episodio)
        if not episode["folder"]:
            raise StorageError("P2_REPORT_UNAVAILABLE: el episodio no tiene carpeta persistida")
        report = build_p2_report(episode["folder"])
    except (StorageError, PermissionError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 2
    print(render_p2_report(report), end="")
    return report.exit_code


def _administrative_close(args: argparse.Namespace) -> int:
    try:
        closure = _service(args.config).administratively_close_irrecoverable_episode(
            args.episodio,
            reason=args.motivo,
            actor=args.actor,
            source=args.source,
        )
    except (StorageError, PermissionError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 2
    print(f"Recovery administrativo registrado: {args.episodio}")
    print(f"Base: {closure['irrecoverability']['basis']}")
    print(f"Actor: {closure['actor']}")
    print("No se borraron artifacts ni se declaró cierre editorial.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="proyecto-youtube", description="Operar un episodio sin conocer los contratos internos.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    start = subparsers.add_parser("iniciar", help="Crear y registrar un episodio")
    start.add_argument("--config", default=DEFAULT_SETTINGS, type=Path, help=argparse.SUPPRESS)
    start.add_argument("--mission-authorization", help=argparse.SUPPRESS)
    start.add_argument("--synthetic-outputs", help=argparse.SUPPRESS)
    start.add_argument("--execution-profile", help=argparse.SUPPRESS)
    start.add_argument("--execution-family", help=argparse.SUPPRESS)
    start.add_argument("--execution-family-selection", dest="execution_family_selection_path", help=argparse.SUPPRESS)
    start.add_argument("--model", dest="model_override", help=argparse.SUPPRESS)
    start.add_argument("--reasoning-effort", help=argparse.SUPPRESS)
    start.add_argument("--paid-cost-approved", action="store_true", help=argparse.SUPPRESS)
    start.add_argument("--operational-authority", dest="operational_authority_path", help=argparse.SUPPRESS)
    start.add_argument("--mission-contract", dest="mission_contract_path", help=argparse.SUPPRESS)
    start.add_argument("--completion-gate", dest="completion_gate_result_path", help=argparse.SUPPRESS)
    start.add_argument("--mission-repo-root", dest="mission_repo_root", help=argparse.SUPPRESS)
    start.add_argument("--modo", choices=["tema", "obra", "corpus"], help="Omitir para usar el flujo interactivo")
    start.add_argument("--tema")
    start.add_argument("--obra")
    start.add_argument("--obras", nargs="+")
    start.add_argument("--contexto")
    start.add_argument("--pregunta")
    start.add_argument("--indicacion", action="append", help="Indicación como CATEGORIA: texto; puede repetirse")
    start.add_argument("--duracion", help="Duración en minutos, automática o personalizada")
    start.add_argument("--duracion-minutos", type=int)
    start.add_argument("--idioma", help="Idioma objetivo; omitir para usar el predeterminado")
    start.set_defaults(handler=_start)
    resume = subparsers.add_parser("reanudar", help="Consultar y reanudar un episodio registrado")
    resume.add_argument("episodio")
    resume.add_argument("--config", default=DEFAULT_SETTINGS, type=Path, help=argparse.SUPPRESS)
    resume.add_argument("--mission-authorization", help=argparse.SUPPRESS)
    resume.add_argument("--synthetic-outputs", help=argparse.SUPPRESS)
    resume.add_argument("--execution-profile", help=argparse.SUPPRESS)
    resume.add_argument("--execution-family", help=argparse.SUPPRESS)
    resume.add_argument("--execution-family-selection", dest="execution_family_selection_path", help=argparse.SUPPRESS)
    resume.add_argument("--model", dest="model_override", help=argparse.SUPPRESS)
    resume.add_argument("--reasoning-effort", help=argparse.SUPPRESS)
    resume.add_argument("--paid-cost-approved", action="store_true", help=argparse.SUPPRESS)
    resume.add_argument("--operational-authority", dest="operational_authority_path", help=argparse.SUPPRESS)
    resume.add_argument("--mission-contract", dest="mission_contract_path", help=argparse.SUPPRESS)
    resume.add_argument("--completion-gate", dest="completion_gate_result_path", help=argparse.SUPPRESS)
    resume.add_argument("--mission-repo-root", dest="mission_repo_root", help=argparse.SUPPRESS)
    resume.set_defaults(handler=_resume)
    import_result = subparsers.add_parser(
        "importar-resultado",
        help="Importar el resultado externo de un trabajo pendiente",
    )
    import_result.add_argument("resultado", type=Path, help="Archivo de resultado entregado por el trabajo externo")
    import_result.add_argument("--config", default=DEFAULT_SETTINGS, type=Path, help=argparse.SUPPRESS)
    import_result.set_defaults(handler=_import_result)
    report_p2 = subparsers.add_parser(
        "reportar-p2",
        help="Mostrar el progreso determinista de un episodio P2",
    )
    report_p2.add_argument("episodio")
    report_p2.add_argument("--config", default=DEFAULT_SETTINGS, type=Path, help=argparse.SUPPRESS)
    report_p2.set_defaults(handler=_report_p2)
    administrative_close = subparsers.add_parser(
        "cerrar-administrativamente",
        help="Liberar un episodio técnicamente irrecuperable sin borrar evidencia",
    )
    administrative_close.add_argument("episodio")
    administrative_close.add_argument("--motivo", required=True)
    administrative_close.add_argument("--actor", required=True)
    administrative_close.add_argument(
        "--source",
        default="APPLICATION_ADMINISTRATIVE_RECOVERY",
        help=argparse.SUPPRESS,
    )
    administrative_close.add_argument("--config", default=DEFAULT_SETTINGS, type=Path, help=argparse.SUPPRESS)
    administrative_close.set_defaults(handler=_administrative_close)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
