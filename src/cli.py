"""Human-oriented product entrypoint for the Terminal channel."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.application.contracts import EntryMode, HumanInput, InputValidationError
from src.application.interaction import TerminalInteraction, UserCancelled
from src.application.service import EpisodeApplicationService
from src.application.storage import StorageError, VaultEpisodeStore


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SETTINGS = REPO_ROOT / "config" / "local_settings.json"


def _service(settings: str | Path = DEFAULT_SETTINGS) -> EpisodeApplicationService:
    return EpisodeApplicationService(
        VaultEpisodeStore.from_settings(settings),
        interaction=TerminalInteraction(),
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
        result = _service(args.config).start(human_input)
    except UserCancelled:
        print("Operación cancelada por el usuario.")
        return 130
    except (InputValidationError, StorageError, PermissionError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 2
    print(f"Episodio creado: {result.episode.episode_id}")
    print("Entrada registrada.")
    print("La entrada quedó lista para el workflow editorial autorizado; no se ejecutó una vertical editorial.")
    return 0


def _resume(args: argparse.Namespace) -> int:
    try:
        state = _service(args.config).resume(args.episodio)
    except (StorageError, PermissionError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 2
    print(f"Episodio reanudado: {args.episodio}")
    print(f"Estado: {state['state'].get('status', 'desconocido')}")
    print(f"Ruta: {state['folder']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="proyecto-youtube", description="Operar un episodio sin conocer los contratos internos.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    start = subparsers.add_parser("iniciar", help="Crear y registrar un episodio")
    start.add_argument("--config", default=DEFAULT_SETTINGS, type=Path, help=argparse.SUPPRESS)
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
    resume.set_defaults(handler=_resume)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
