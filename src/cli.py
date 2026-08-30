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
    terminal.present(
        "\nResumen:\n"
        f"Modalidad: {mode}\n"
        f"Contenido: {content or '(corpus inicial)'}\n"
        f"Obras: {', '.join(works) if works else '(se determinarán durante el flujo editorial)'}\n"
        f"Pregunta inicial: {initial_question or '(sin pregunta inicial)'}\n"
        f"Contexto: {context or '(sin contexto adicional)'}"
    )
    if not terminal.confirm("¿Iniciar?"):
        raise UserCancelled
    return HumanInput.create(mode=mode, content=content, initial_question=initial_question, context=context, works=works, channel="TERMINAL")


def _non_interactive_input(args: argparse.Namespace) -> HumanInput:
    mode = args.modo
    if mode == "tema":
        content, works = args.tema, []
    elif mode == "obra":
        content, works = args.obra, [args.obra] if args.obra else []
    else:
        content, works = "", list(args.obras or [])
    return HumanInput.create(
        mode=mode,
        content=content,
        initial_question=getattr(args, "pregunta", None),
        context=getattr(args, "contexto", None),
        works=works,
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
    start.add_argument("--mission-contract", dest="mission_contract_path", help=argparse.SUPPRESS)
    start.add_argument("--completion-gate", dest="completion_gate_result_path", help=argparse.SUPPRESS)
    start.add_argument("--mission-repo-root", dest="mission_repo_root", help=argparse.SUPPRESS)
    start.add_argument("--modo", choices=["tema", "obra", "corpus"], help="Omitir para usar el flujo interactivo")
    start.add_argument("--tema")
    start.add_argument("--obra")
    start.add_argument("--obras", nargs="+")
    start.add_argument("--contexto")
    start.add_argument("--pregunta")
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
    resume.add_argument("--mission-contract", dest="mission_contract_path", help=argparse.SUPPRESS)
    resume.add_argument("--completion-gate", dest="completion_gate_result_path", help=argparse.SUPPRESS)
    resume.add_argument("--mission-repo-root", dest="mission_repo_root", help=argparse.SUPPRESS)
    resume.set_defaults(handler=_resume)
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
