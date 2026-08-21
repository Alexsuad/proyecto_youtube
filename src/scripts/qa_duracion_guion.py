"""Gate de duración con entradas y salida canónicas."""
import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.core.duration_envelope import duration_assessment, load_duration_envelope, parse_recommended_range
from src.core.gate_result import GateResult
from src.core.gate_runtime import run_gate
from src.core.input_validation import InputRequirement, validate_inputs
from src.core.status import GateStatus


def count_words(text: str) -> int:
    return len(re.findall(r"\b\w+\b", re.sub(r"#+\s+|\*+", "", text)))


def _duration_assessment(envelope: dict[str, Any]) -> dict[str, Any]:
    return duration_assessment(envelope)


def resolve_duration_parameters(envelope: dict[str, Any] | None, fallback_wpm: int, fallback_minimum: int, fallback_maximum: int) -> tuple[int, int, int, str]:
    if envelope is None:
        return fallback_wpm, fallback_minimum, fallback_maximum, "TECHNICAL_FALLBACK"
    assessment = _duration_assessment(envelope)
    recommended_range = assessment.get("recommended_range")
    if not isinstance(recommended_range, str):
        raise ValueError("YT_DURATION_ENVELOPE requiere recommended_range para prevalecer sobre el fallback.")
    minimum, maximum = parse_recommended_range(recommended_range)
    envelope_wpm = assessment.get("wpm", assessment.get("target_wpm", fallback_wpm))
    if not isinstance(envelope_wpm, int) or envelope_wpm <= 0:
        raise ValueError("YT_DURATION_ENVELOPE.wpm debe ser un entero positivo cuando se declara.")
    return envelope_wpm, minimum, maximum, "EPISODIC_YT_DURATION_ENVELOPE"


def evaluate(ep_path: Path, wpm: int, minimum: int, maximum: int, episode_id: str | None = None, duration_envelope: dict[str, Any] | None = None, duration_envelope_metadata: dict[str, Any] | None = None) -> GateResult:
    artifact_id = episode_id or ep_path.name
    script = ep_path / "06_guion_longform.md"
    blocked, failures, evidence = validate_inputs([InputRequirement(script, "06_guion_longform.md")])
    if blocked:
        return GateResult("qa_duracion_guion", artifact_id, "1.0.0", GateStatus.BLOCKED, "No se puede medir la duración", blocked, evidence=evidence)
    if failures:
        return GateResult("qa_duracion_guion", artifact_id, "1.0.0", GateStatus.FAIL, "Entrada inválida", failures, evidence=evidence)
    try:
        wpm, minimum, maximum, duration_policy_source = resolve_duration_parameters(duration_envelope, wpm, minimum, maximum)
    except ValueError as exc:
        return GateResult("qa_duracion_guion", artifact_id, "1.0.0", GateStatus.FAIL, "Envelope de duración inválido", [str(exc)], evidence=evidence)
    words = count_words(script.read_text(encoding="utf-8"))
    minutes = words / wpm
    evidence.update({"words": words, "wpm": wpm, "estimated_minutes": minutes, "target": [minimum, maximum], "duration_policy_source": duration_policy_source})
    if duration_envelope_metadata and duration_policy_source == "EPISODIC_YT_DURATION_ENVELOPE":
        evidence.update(duration_envelope_metadata)
    if minimum <= minutes <= maximum:
        return GateResult("qa_duracion_guion", artifact_id, "1.0.0", GateStatus.PASS, "Duración dentro del objetivo", evidence=evidence)
    return GateResult("qa_duracion_guion", artifact_id, "1.0.0", GateStatus.FAIL, "Duración fuera del objetivo", [f"Duración estimada {minutes:.2f} min; objetivo {minimum}-{maximum}"], evidence=evidence)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ep_path", required=True)
    parser.add_argument("--wpm", type=int, default=144, help="Fallback técnico de palabras por minuto")
    parser.add_argument("--min_target", type=int, default=18, help="Fallback técnico mínimo en minutos")
    parser.add_argument("--max_target", type=int, default=22, help="Fallback técnico máximo en minutos")
    parser.add_argument("--duration-envelope", help="Paquete canónico que contiene el envelope episódico")
    parser.add_argument("--duration-review", help="Review canónica independiente del paquete episódico")
    parser.add_argument("--duration-execution-registry", help="Registro de ejecución que demuestra provenance del paquete y la review")
    parser.add_argument("--duration-active-profile", help="Perfil activo explícito; por defecto se usa el puntero canónico")
    parser.add_argument("--ep-id")
    parser.add_argument("--output-root")
    args = parser.parse_args()
    envelope = None
    envelope_metadata = None
    if args.duration_envelope:
        try:
            envelope, envelope_metadata = load_duration_envelope(
                Path(args.duration_envelope),
                args.ep_id,
                review_path=Path(args.duration_review) if args.duration_review else None,
                registry_path=Path(args.duration_execution_registry) if args.duration_execution_registry else None,
                active_profile_path=Path(args.duration_active_profile) if args.duration_active_profile else None,
            )
        except ValueError as exc:
            artifact_id = args.ep_id or Path(args.ep_path).name
            return run_gate(
                lambda: GateResult(
                    "qa_duracion_guion", artifact_id, "1.0.0", GateStatus.FAIL,
                    "Envelope de duración inválido", [str(exc)], evidence={},
                ),
                output_root=args.output_root,
            )
    elif args.duration_review or args.duration_execution_registry or args.duration_active_profile:
        artifact_id = args.ep_id or Path(args.ep_path).name
        return run_gate(
            lambda: GateResult(
                "qa_duracion_guion", artifact_id, "1.0.0", GateStatus.FAIL,
                "Referencias de autoridad de duración incompletas",
                ["duration-envelope, duration-review y duration-execution-registry deben declararse juntas."], evidence={},
            ),
            output_root=args.output_root,
        )
    return run_gate(lambda: evaluate(Path(args.ep_path), args.wpm, args.min_target, args.max_target, args.ep_id, envelope, envelope_metadata), output_root=args.output_root)


if __name__ == "__main__":
    import sys
    sys.exit(main())
