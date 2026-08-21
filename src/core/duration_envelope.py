"""Shared technical handling for the episodic YT_DURATION_ENVELOPE contract."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from src.ai.registry import load_registry
from src.core.contract_validation import validate_against_schema
from src.core.editorial_profile_registry import load_active_profile_authority
from src.core.path_resolution import REPO_ROOT
from src.core.status import GateStatus
from src.scripts.youtube_adaptation_b5_i2_gate import evaluate as evaluate_youtube_adaptation


_RANGE_PATTERN = re.compile(
    r"(?:entre\s+(\d+(?:[.,]\d+)?)\s+y\s+(\d+(?:[.,]\d+)?)|"
    r"(\d+(?:[.,]\d+)?)\s*[-–—]\s*(\d+(?:[.,]\d+)?))",
    re.IGNORECASE,
)
_APPROVALS_KEY = "duration_envelope_approvals"
_CAPABILITY_ID = "YT_DURATION_ENVELOPE"
_GATE_ID = "youtube_adaptation_b5_i2_gate"


def canonical_duration_registry_path() -> Path:
    return (REPO_ROOT / "output" / "execution_provenance_registry.json").resolve()


def canonical_active_profile_path() -> Path:
    return (REPO_ROOT / "config" / "active_editorial_profile.json").resolve()


def _active_profile_path(
    requested: Path | None,
    *,
    private_override: Path | None = None,
) -> Path:
    canonical = canonical_active_profile_path()
    load_active_profile_authority(requested, _profile_path_override=private_override)
    selected = Path(private_override).resolve() if private_override is not None else canonical
    return selected


def duration_assessment(envelope: dict[str, Any]) -> dict[str, Any]:
    """Return the assessment from a package, review, or already extracted value."""
    value: Any = envelope
    if not isinstance(value, dict):
        raise ValueError("YT_DURATION_ENVELOPE debe contener un objeto duration_assessment.")
    if isinstance(value.get("youtube_design_constraints"), dict):
        value = value["youtube_design_constraints"]
    if isinstance(value, dict) and isinstance(value.get("duration_assessment"), dict):
        value = value["duration_assessment"]
    if not isinstance(value, dict):
        raise ValueError("YT_DURATION_ENVELOPE debe contener un objeto duration_assessment.")
    return value


def parse_recommended_range(value: Any) -> tuple[int, int]:
    if not isinstance(value, str):
        raise ValueError("YT_DURATION_ENVELOPE requiere recommended_range.")
    match = _RANGE_PATTERN.search(value)
    if not match:
        raise ValueError("YT_DURATION_ENVELOPE.recommended_range no contiene un rango numérico interpretable.")
    minimum_value = match.group(1) or match.group(3)
    maximum_value = match.group(2) or match.group(4)
    minimum = int(float(minimum_value.replace(",", ".")))
    maximum = int(float(maximum_value.replace(",", ".")))
    if minimum <= 0 or maximum < minimum:
        raise ValueError("YT_DURATION_ENVELOPE contiene un rango inválido.")
    return minimum, maximum


def _artifact_shape(value: dict[str, Any]) -> tuple[str, str, str]:
    if "package_id" in value:
        return "youtube_adaptation_b5_i2_package", "package_id", str(value.get("package_id"))
    if "review_id" in value:
        return "youtube_adaptation_review", "review_id", str(value.get("review_id"))
    raise ValueError("El envelope debe ser un YouTubeAdaptationB5I2Package o YouTubeAdaptationReview canónico.")


def _registry_root(registry_path: Path) -> Path:
    resolved = registry_path.resolve()
    return (resolved.parent.parent if resolved.parent.name == "output" else resolved.parent).resolve()


def _relative_repo_path(path: Path, repository_root: Path) -> str:
    resolved = path.resolve()
    try:
        relative = resolved.relative_to(repository_root.resolve())
    except ValueError as exc:
        raise ValueError("Los artifacts de YT_DURATION_ENVELOPE deben estar dentro del repositorio.") from exc
    return relative.as_posix()


def _resolve_repo_path(raw_path: Any, repository_root: Path, label: str) -> Path:
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise ValueError(f"{label} no tiene artifact_path verificable.")
    candidate = Path(raw_path)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError(f"{label} contiene un artifact_path inseguro.")
    resolved = (repository_root / candidate).resolve()
    try:
        resolved.relative_to(repository_root.resolve())
    except ValueError as exc:
        raise ValueError(f"{label} escapa del repositorio.") from exc
    if not resolved.is_file():
        raise ValueError(f"{label} no existe: {raw_path}")
    return resolved


def _checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run_output(registry: dict[str, Any], run_id: str, artifact_kind: str, artifact_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    runs = [item for item in registry.get("runs", []) if isinstance(item, dict) and item.get("run_id") == run_id]
    if len(runs) != 1:
        if not runs:
            raise ValueError(f"Provenance ausente para {run_id}.")
        raise ValueError(f"Provenance duplicada para {run_id}.")
    run = runs[0]
    if not isinstance(run, dict):
        raise ValueError(f"Provenance ausente para {run_id}.")
    output = next(
        (
            item for item in run.get("outputs", [])
            if isinstance(item, dict) and item.get("artifact_kind") == artifact_kind and item.get("artifact_id") == artifact_id
        ),
        None,
    )
    if not isinstance(output, dict):
        raise ValueError(f"Provenance no vincula {artifact_kind}:{artifact_id} con {run_id}.")
    return run, output


def _gate_checksum(gate_result: Any) -> str:
    payload = gate_result.to_dict()
    payload.pop("checked_at", None)
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _validate_registry(registry: dict[str, Any]) -> None:
    violations = validate_against_schema(registry, "execution_provenance_registry")
    if violations:
        raise ValueError("ExecutionProvenanceRegistry inválido: " + "; ".join(violations))


def load_duration_envelope(
    path: Path,
    expected_episode_id: str | None = None,
    *,
    package_path: Path | None = None,
    review_path: Path | None = None,
    registry_path: Path | None = None,
    active_profile_path: Path | None = None,
    _active_profile_path_override: Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Load an authorized episodic envelope through the existing YA gate.

    A package or review that is merely schema-valid is not an authority. The
    caller must provide the package, its independent review, and the execution
    registry so the existing provenance gate can be reused. The returned value
    is the approved review, not the producer package, because the auditor owns
    the duration decision.
    """
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"YT_DURATION_ENVELOPE ausente: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"YT_DURATION_ENVELOPE JSON inválido: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise ValueError("YT_DURATION_ENVELOPE debe ser un objeto JSON.")
    source_schema, _, _ = _artifact_shape(value)
    if source_schema == "youtube_adaptation_b5_i2_package":
        package_path = path if package_path is None else package_path
    elif package_path is None:
        raise ValueError(
            "YT_DURATION_ENVELOPE requiere package_path cuando la fuente es una review."
        )
    if review_path is None or registry_path is None:
        raise ValueError(
            "YT_DURATION_ENVELOPE requiere review_path y registry_path para demostrar autoridad y provenance."
        )
    package_path = Path(package_path)
    review_path = Path(review_path)
    registry_path = Path(registry_path)
    try:
        review_value = json.loads(review_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise ValueError("La review de YT_DURATION_ENVELOPE no es un JSON válido y existente.") from exc
    if not isinstance(review_value, dict):
        raise ValueError("La review de YT_DURATION_ENVELOPE debe ser un objeto JSON.")
    review_schema, review_id_field, review_id = _artifact_shape(review_value)
    if review_schema != "youtube_adaptation_review":
        raise ValueError("La autoridad de YT_DURATION_ENVELOPE debe ser una review canónica.")

    profile_path = _active_profile_path(active_profile_path, private_override=_active_profile_path_override)
    gate_result = evaluate_youtube_adaptation(
        package_path,
        review_path,
        registry_path,
        None if _active_profile_path_override is not None else profile_path,
        expected_episode_id or str(review_value.get("episode_id") or "YT-R3"),
        _active_profile_path_override=_active_profile_path_override,
    )
    if gate_result.status is not GateStatus.PASS:
        details = list(gate_result.violations) + list(gate_result.evidence.get("blocked_reasons", []))
        raise ValueError(
            "YT_DURATION_ENVELOPE no tiene autoridad aprobada por el gate de YouTube Adaptation: "
            + ("; ".join(details) if details else gate_result.summary)
        )

    package_value = json.loads(package_path.read_text(encoding="utf-8"))
    package_schema, package_id_field, package_id = _artifact_shape(package_value)
    if package_schema != "youtube_adaptation_b5_i2_package":
        raise ValueError("package_path no contiene un YouTubeAdaptationB5I2Package canónico.")
    package_episode_id = package_value.get("episode_id")
    review_episode_id = review_value.get("episode_id")
    if expected_episode_id and (package_episode_id != expected_episode_id or review_episode_id != expected_episode_id):
        raise ValueError("YT_DURATION_ENVELOPE pertenece a otro episodio.")
    if package_episode_id != review_episode_id:
        raise ValueError("package y review de YT_DURATION_ENVELOPE pertenecen a episodios distintos.")
    package_assessment = duration_assessment(package_value)
    review_assessment = duration_assessment(review_value)
    package_range = parse_recommended_range(package_assessment.get("recommended_range"))
    review_range = parse_recommended_range(review_assessment.get("recommended_range"))
    if package_range != review_range:
        raise ValueError("package y review declaran rangos de duración distintos.")
    if review_assessment.get("decision") != "PASS":
        raise ValueError("La review no aprueba YT_DURATION_ENVELOPE.")
    assessment = review_assessment
    episode_id = review_episode_id
    metadata = {
        "duration_envelope_schema": package_schema,
        "duration_envelope_id": package_id,
        "duration_envelope_id_field": package_id_field,
        "duration_envelope_episode_id": episode_id,
        "duration_envelope_checksum": hashlib.sha256(package_path.read_bytes()).hexdigest(),
        "duration_review_schema": review_schema,
        "duration_review_id": review_id,
        "duration_review_id_field": review_id_field,
        "duration_review_checksum": hashlib.sha256(review_path.read_bytes()).hexdigest(),
        "duration_policy_source": "EPISODIC_YT_DURATION_ENVELOPE",
        "duration_authority": "YOUTUBE_ADAPTATION_AUDITOR",
        "duration_gate_status": gate_result.status.value,
    }
    return {"duration_assessment": assessment}, metadata


def _write_registry(path: Path, registry: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def register_approved_duration_envelope(
    package_path: Path,
    review_path: Path,
    registry_path: Path,
    *,
    active_profile_path: Path | None = None,
    _active_profile_path_override: Path | None = None,
) -> dict[str, Any]:
    """Materialize an already approved B5-I2 duration decision in the same registry.

    The record is derived from the existing B5-I2 gate. It is not a second
    authority: resolution re-runs the gate and rechecks the referenced files.
    """
    package_path = Path(package_path).resolve()
    review_path = Path(review_path).resolve()
    registry_path = Path(registry_path).resolve()
    repository_root = _registry_root(registry_path)
    package, metadata = load_duration_envelope(
        package_path,
        review_path=review_path,
        registry_path=registry_path,
        active_profile_path=active_profile_path,
        _active_profile_path_override=_active_profile_path_override,
    )
    package_value = json.loads(package_path.read_text(encoding="utf-8"))
    review_value = json.loads(review_path.read_text(encoding="utf-8"))
    episode_id = str(review_value.get("episode_id") or "")
    if not episode_id or package_value.get("episode_id") != episode_id:
        raise ValueError("package y review de YT_DURATION_ENVELOPE no comparten episode_id.")
    registry = load_registry(registry_path)
    _validate_registry(registry)
    package_id = str(package_value.get("package_id") or "")
    review_id = str(review_value.get("review_id") or "")
    package_checksum = _checksum(package_path)
    review_checksum = _checksum(review_path)
    producer_run_id = str(package_value.get("producer_run_id") or "")
    auditor_run_id = str(review_value.get("auditor_run_id") or "")
    producer_run, producer_output = _run_output(
        registry, producer_run_id, "youtube_adaptation_b5_i2_package", package_id
    )
    auditor_run, auditor_output = _run_output(
        registry, auditor_run_id, "youtube_adaptation_review", review_id
    )
    package_relative = _relative_repo_path(package_path, repository_root)
    review_relative = _relative_repo_path(review_path, repository_root)
    for label, run, output, actual_path, actual_checksum, relative_path in (
        ("package", producer_run, producer_output, package_path, package_checksum, package_relative),
        ("review", auditor_run, auditor_output, review_path, review_checksum, review_relative),
    ):
        if output.get("checksum") != actual_checksum:
            raise ValueError(f"Checksum de provenance no coincide con el {label} real.")
        registered_path = output.get("artifact_path")
        if registered_path is not None:
            candidate = Path(str(registered_path))
            if candidate.is_absolute():
                try:
                    normalized_path = _relative_repo_path(candidate, repository_root)
                except ValueError as exc:
                    raise ValueError(f"artifact_path de provenance no coincide con el {label} real.") from exc
                output["artifact_path"] = normalized_path
                resolved_path = (repository_root / normalized_path).resolve()
            else:
                resolved_path = _resolve_repo_path(registered_path, repository_root, label)
            if resolved_path != actual_path:
                raise ValueError(f"artifact_path de provenance no coincide con el {label} real.")
        else:
            output["artifact_path"] = relative_path

    gate_result = evaluate_youtube_adaptation(
        package_path,
        review_path,
        registry_path,
        None if _active_profile_path_override is not None else _active_profile_path(active_profile_path),
        episode_id,
        _active_profile_path_override=_active_profile_path_override,
    )
    if gate_result.status is not GateStatus.PASS:
        raise ValueError("No se puede materializar un envelope sin gate B5-I2 PASS.")
    _validate_registry(registry)
    approval = {
        "approval_id": f"{_CAPABILITY_ID}:{episode_id}:{review_id}",
        "capability_id": _CAPABILITY_ID,
        "episode_id": episode_id,
        "status": "APPROVED",
        "decision": "PASS",
        "authority": "YOUTUBE_ADAPTATION_AUDITOR",
        "package": {
            "artifact_kind": "youtube_adaptation_b5_i2_package",
            "artifact_id": package_id,
            "artifact_ref": f"youtube_adaptation_b5_i2_package:{package_id}",
            "artifact_path": package_relative,
            "checksum": package_checksum,
        },
        "review": {
            "artifact_kind": "youtube_adaptation_review",
            "artifact_id": review_id,
            "artifact_ref": f"youtube_adaptation_review:{review_id}",
            "artifact_path": review_relative,
            "checksum": review_checksum,
        },
        "provenance": {
            "producer_run_id": producer_run_id,
            "auditor_run_id": auditor_run_id,
            "registry_ref": _relative_repo_path(registry_path, repository_root),
        },
        "gate": {
            "gate_id": _GATE_ID,
            "status": gate_result.status.value,
            "review_decision": review_value.get("decision"),
            "result_checksum": _gate_checksum(gate_result),
        },
        "duration_metadata": metadata,
    }
    registry.setdefault(_APPROVALS_KEY, [])
    existing = next((item for item in registry[_APPROVALS_KEY] if item.get("approval_id") == approval["approval_id"]), None)
    if existing is not None:
        if existing != approval:
            raise ValueError("La aprobación de YT_DURATION_ENVELOPE ya existe con contenido distinto.")
        return existing
    registry[_APPROVALS_KEY].append(approval)
    _validate_registry(registry)
    _write_registry(registry_path, registry)
    return approval


def resolve_approved_duration_envelope(
    episode_id: str,
    registry_path: Path | None = None,
    *,
    active_profile_path: Path | None = None,
    _allow_registry_override: bool = False,
    _active_profile_path_override: Path | None = None,
) -> dict[str, Any] | None:
    """Resolve one approved duration decision from the canonical provenance registry.

    No candidate means no registered episodic decision. Any malformed matching
    candidate is an error so the caller cannot silently fall back.
    """
    canonical_registry = canonical_duration_registry_path()
    registry_path = (Path(registry_path).resolve() if registry_path else canonical_registry)
    if registry_path != canonical_registry and not _allow_registry_override:
        raise ValueError("El resolver de aprobaciones solo admite el registry canónico.")
    _active_profile_path(active_profile_path, private_override=_active_profile_path_override)
    if not registry_path.is_file():
        raise ValueError(f"El registry canónico de aprobaciones de duración no puede leerse: {registry_path}")
    registry = load_registry(registry_path)
    _validate_registry(registry)
    candidates = [
        item for item in registry.get(_APPROVALS_KEY, [])
        if isinstance(item, dict)
        and item.get("episode_id") == episode_id
        and item.get("capability_id") == _CAPABILITY_ID
    ]
    if not candidates:
        return None
    if len(candidates) != 1:
        raise ValueError("Existen múltiples aprobaciones YT_DURATION_ENVELOPE para el mismo episodio.")
    approval = candidates[0]
    if approval.get("status") != "APPROVED" or approval.get("decision") != "PASS":
        raise ValueError("La aprobación YT_DURATION_ENVELOPE aplicable no está aprobada.")
    repository_root = _registry_root(registry_path)
    package_entry = approval.get("package")
    review_entry = approval.get("review")
    if not isinstance(package_entry, dict) or not isinstance(review_entry, dict):
        raise ValueError("La aprobación YT_DURATION_ENVELOPE carece de package o review trazables.")
    package_path = _resolve_repo_path(package_entry.get("artifact_path"), repository_root, "package")
    review_path = _resolve_repo_path(review_entry.get("artifact_path"), repository_root, "review")
    if _checksum(package_path) != package_entry.get("checksum") or _checksum(review_path) != review_entry.get("checksum"):
        raise ValueError("Checksum de package o review no coincide con la aprobación registrada.")
    package_value = json.loads(package_path.read_text(encoding="utf-8"))
    review_value = json.loads(review_path.read_text(encoding="utf-8"))
    if package_value.get("episode_id") != episode_id or review_value.get("episode_id") != episode_id:
        raise ValueError("La aprobación YT_DURATION_ENVELOPE pertenece a otro episodio.")
    if package_value.get("package_id") != package_entry.get("artifact_id") or review_value.get("review_id") != review_entry.get("artifact_id"):
        raise ValueError("Los IDs de los artifacts no coinciden con la aprobación registrada.")
    provenance = approval.get("provenance")
    if not isinstance(provenance, dict):
        raise ValueError("La aprobación YT_DURATION_ENVELOPE carece de provenance.")
    producer_run, producer_output = _run_output(
        registry, str(provenance.get("producer_run_id") or ""), "youtube_adaptation_b5_i2_package", str(package_entry.get("artifact_id"))
    )
    auditor_run, auditor_output = _run_output(
        registry, str(provenance.get("auditor_run_id") or ""), "youtube_adaptation_review", str(review_entry.get("artifact_id"))
    )
    for label, run, output, entry in (
        ("producer", producer_run, producer_output, package_entry),
        ("auditor", auditor_run, auditor_output, review_entry),
    ):
        if run.get("episode_id") != episode_id or run.get("status") != "SUCCEEDED" or str(run.get("execution_mode")).upper() != "REAL" or run.get("provider_kind") != "REAL":
            raise ValueError(f"Provenance {label} no demuestra una ejecución real aprobada.")
        if output.get("artifact_path") != entry.get("artifact_path") or output.get("checksum") != entry.get("checksum"):
            raise ValueError(f"Provenance {label} no coincide con la aprobación registrada.")
    gate_result = evaluate_youtube_adaptation(
        package_path,
        review_path,
        registry_path,
        None if _active_profile_path_override is not None else _active_profile_path(active_profile_path),
        episode_id,
        _active_profile_path_override=_active_profile_path_override,
    )
    gate = approval.get("gate")
    if gate_result.status is not GateStatus.PASS or not isinstance(gate, dict) or gate.get("gate_id") != _GATE_ID or gate.get("status") != GateStatus.PASS.value or gate.get("result_checksum") != _gate_checksum(gate_result):
        raise ValueError("La aprobación YT_DURATION_ENVELOPE no conserva un gate B5-I2 PASS verificable.")
    _, metadata = load_duration_envelope(
        package_path,
        episode_id,
        review_path=review_path,
        registry_path=registry_path,
        active_profile_path=active_profile_path,
        _active_profile_path_override=_active_profile_path_override,
    )
    if approval.get("duration_metadata") != metadata:
        raise ValueError("La metadata de duración no coincide con la aprobación registrada.")
    return {"package_path": package_path, "review_path": review_path, "metadata": metadata, "approval": approval}
