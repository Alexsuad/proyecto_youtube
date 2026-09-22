"""Deterministic terminal reporting for persisted P2 roundtrip evidence."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from src.application.storage import EpisodeHandle
from src.application.topic_belonging import TopicBelongingTechnicalWorkflow


STAGES = ("ENRICHMENT", "PRODUCER", "REVIEWER")
FINAL_STATUS = "TOPIC_BELONGING_TECHNICAL_STOP"
PENDING_STATUSES = {"PENDING_EXTERNAL_RESULT", "PERSISTED"}
REASSESSMENT_READY_STATUS = "READY_FOR_REASSESSMENT"


@dataclass(frozen=True)
class P2ReportStep:
    name: str
    status: str
    evidence: tuple[str, ...] = ()
    error: str | None = None
    expected: str | None = None
    obtained: str | None = None


@dataclass(frozen=True)
class P2Report:
    episode_id: str
    steps: tuple[P2ReportStep, ...]
    maximum_reached: str
    result: str
    failed_step: str | None = None
    error: str | None = None
    expected: str | None = None
    obtained: str | None = None

    @property
    def exit_code(self) -> int:
        return {"PASS": 0, "PARTIAL": 1, "FAIL": 2}[self.result]


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{label}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{label}: se esperaba un objeto JSON")
    return data


def _step_pass(name: str, *evidence: Path) -> P2ReportStep:
    return P2ReportStep(name=name, status="PASS", evidence=tuple(str(path) for path in evidence))


def _step_pending(name: str, expected: str, obtained: str) -> P2ReportStep:
    return P2ReportStep(name=name, status="PENDING", expected=expected, obtained=obtained)


def _step_fail(name: str, error: str, expected: str, obtained: str) -> P2ReportStep:
    return P2ReportStep(name=name, status="FAIL", error=error, expected=expected, obtained=obtained)


def _reassessment_record_index(folder: Path) -> dict[int, dict[str, Any]]:
    path = folder / "topic_belonging_reassessments.json"
    if not path.is_file():
        return {}
    data = _read_json(path, "topic_belonging_reassessments.json")
    entries = data.get("reassessments")
    if not isinstance(entries, list):
        raise ValueError("topic_belonging_reassessments.json: reassessments no es una lista")
    indexed: dict[int, dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("topic_belonging_reassessments.json: registro inválido")
        try:
            attempt = int(entry["attempt_number"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("topic_belonging_reassessments.json: attempt_number inválido") from exc
        if attempt in indexed:
            raise ValueError("topic_belonging_reassessments.json: attempt duplicado")
        indexed[attempt] = entry
    return dict(sorted(indexed.items()))


def _result_record_index(folder: Path) -> tuple[dict[str, Any] | None, list[P2ReportStep]]:
    path = folder / "roundtrip_results.json"
    if not path.is_file():
        return None, []
    try:
        data = _read_json(path, "roundtrip_results.json")
    except ValueError as exc:
        return None, [_step_fail("RESULT_INDEX", str(exc), "JSON persistido válido", "JSON inválido")]
    results = data.get("results")
    if not isinstance(results, list):
        return None, [_step_fail("RESULT_INDEX", "results no es una lista", "results: lista", repr(results))]
    if any(not isinstance(item, dict) for item in results):
        return None, [_step_fail("RESULT_INDEX", "results contiene un registro que no es objeto", "registros JSON objeto", repr(results))]
    if any(str(item.get("stage") or "") not in STAGES for item in results):
        return None, [_step_fail("RESULT_INDEX", "etapa desconocida en el índice", repr(STAGES), repr(results))]

    attempts: dict[int, list[dict[str, Any]]] = {}
    for item in results:
        try:
            attempt = int(item.get("attempt_number") or 1)
        except (TypeError, ValueError) as exc:
            return None, [_step_fail("RESULT_INDEX", "attempt_number inválido", "attempt entero", repr(item.get("attempt_number")))]
        attempts.setdefault(attempt, []).append(item)

    try:
        reassessments = _reassessment_record_index(folder)
        workflow = _read_json(folder / "workflow_state.json", "workflow_state.json")
    except ValueError as exc:
        return None, [_step_fail("RESULT_INDEX", str(exc), "lineage de reassessment válido", "lineage inválido")]

    def stage_map(records: list[dict[str, Any]], *, expected_kind: str | None = None) -> dict[str, Any]:
        stages = [str(item.get("stage") or "") for item in records]
        if len(stages) != len(set(stages)):
            raise ValueError("etapas duplicadas dentro del attempt")
        if expected_kind == "STRUCTURAL_REASSESSMENT" and stages != list(STAGES):
            raise ValueError("attempt estructural incompleto u orden inválido")
        if expected_kind == "REVIEWER_ONLY_REASSESSMENT" and stages != ["REVIEWER"]:
            raise ValueError("attempt reviewer-only contiene etapas inválidas")
        if expected_kind is None and stages != list(STAGES)[: len(stages)]:
            raise ValueError("attempt inicial incompleto u orden inválido")
        return {stage: item for stage, item in zip(stages, records)}

    try:
        orphan_attempts = sorted(set(attempts) - ({1} | set(reassessments)))
        if orphan_attempts:
            raise ValueError(f"attempts no declarados: {orphan_attempts}")
        effective = stage_map(attempts.get(1, []))
        for attempt, reassessment in reassessments.items():
            records = attempts.get(attempt, [])
            kind = reassessment.get("reassessment_kind", "REVIEWER_ONLY_REASSESSMENT")
            reassessment_id = reassessment.get("reassessment_id")
            if reassessment.get("status") != "COMPLETED":
                if (
                    workflow.get("attempt_number") == attempt
                    and kind == "STRUCTURAL_REASSESSMENT"
                ):
                    raise ValueError("attempt estructural incompleto")
                continue
            if not reassessment_id or any(item.get("reassessment_id") != reassessment_id for item in records):
                raise ValueError("reassessment_id no coincide con los resultados del attempt")
            if kind == "STRUCTURAL_REASSESSMENT":
                effective = stage_map(records, expected_kind=kind)
            elif kind == "REVIEWER_ONLY_REASSESSMENT":
                reviewer = stage_map(records, expected_kind=kind)
                if set(effective) != {"ENRICHMENT", "PRODUCER", "REVIEWER"}:
                    raise ValueError("reviewer-only no tiene bundle padre completo")
                effective = {**effective, "REVIEWER": reviewer["REVIEWER"]}
            else:
                raise ValueError("reassessment_kind inválido")
    except ValueError as exc:
        return None, [_step_fail("RESULT_INDEX", str(exc), "attempts coherentes por reassessment", "índice inconsistente")]

    return effective, []


def _canonical_probe(mission_id: str | None) -> TopicBelongingTechnicalWorkflow:
    probe = object.__new__(TopicBelongingTechnicalWorkflow)
    probe._mission_id = mission_id
    return probe


def _stage_step(
    folder: Path,
    episode_id: str,
    mission_id: str | None,
    stage: str,
    record: dict[str, Any] | None,
    workflow_status: str,
) -> P2ReportStep:
    if record is None:
        if workflow_status == FINAL_STATUS:
            return _step_fail(stage, "falta el resultado persistido de una etapa finalizada", "resultado persistido para la etapa", "resultado ausente")
        return _step_pending(stage, "resultado persistido para la etapa", "resultado aún no persistido")
    try:
        handle = EpisodeHandle(
            episode_id,
            folder.name,
            folder,
            folder.parent.parent / "index" / "episodes_index.json",
        )
        _canonical_probe(mission_id)._revalidate_roundtrip_record(handle, record)
    except Exception as exc:
        return _step_fail(stage, str(exc), "resultado persistido compatible con su handoff", "evidencia incompatible")
    return _step_pass(stage, folder / "roundtrip_results.json", folder / str(record.get("result_path") or ""))


def build_p2_report(episode_folder: str | Path) -> P2Report:
    folder = Path(episode_folder).resolve()
    episode_id = "_".join(folder.name.split("_")[:2]) if folder.name else "UNKNOWN"
    steps: list[P2ReportStep] = []

    try:
        episode_state_path = folder / "episode_state.json"
        workflow_path = folder / "workflow_state.json"
        episode_state = _read_json(episode_state_path, "episode_state.json")
        workflow = _read_json(workflow_path, "workflow_state.json")
        episode_id = str(episode_state.get("episode_id") or workflow.get("episode_id") or episode_id)
        if episode_state.get("episode_id") != episode_id or workflow.get("episode_id") != episode_id:
            raise ValueError("episode_id inconsistente entre los estados persistidos")
        steps.append(_step_pass("EPISODE_REGISTERED", episode_state_path, workflow_path))
    except ValueError as exc:
        steps.append(_step_fail("EPISODE_REGISTERED", str(exc), "estados persistidos y consistentes", "estado ausente o inválido"))
        return P2Report(
            episode_id=episode_id,
            steps=tuple(steps),
            maximum_reached="NONE",
            result="FAIL",
            failed_step=steps[-1].name,
            error=steps[-1].error,
            expected=steps[-1].expected,
            obtained=steps[-1].obtained,
        )

    workflow_status = str(workflow.get("status") or "")
    episode_status = str(episode_state.get("status") or "")
    result_records, index_errors = _result_record_index(folder)
    steps.extend(index_errors)
    if episode_status != workflow_status:
        steps.append(
            _step_fail(
                "STATE_CONSISTENCY",
                "episode_state.status y workflow_state.status no coinciden",
                f"status={workflow_status}",
                f"status={episode_status}",
            )
        )
    else:
        completed = workflow.get("completed_stages", [])
        indexed_stages = list((result_records or {}).keys())
        completed_is_consistent = (
            completed == indexed_stages
            if workflow_status != FINAL_STATUS
            else completed in ([], list(STAGES)) and indexed_stages == list(STAGES)
        )
        if not completed_is_consistent:
            steps.append(
                _step_fail(
                    "STATE_CONSISTENCY",
                    "completed_stages no coincide con el índice persistido",
                    repr(indexed_stages),
                    repr(completed),
                )
            )
        else:
            steps.append(_step_pass("STATE_CONSISTENCY", episode_state_path, workflow_path))
    if workflow_status == FINAL_STATUS and not any(step.status == "FAIL" for step in steps):
        terminal_expectations = (
            ("run_id", episode_state.get("run_id")),
            ("stop_boundary", "TOPIC_BELONGING_GATE"),
            ("downstream_execution_started", False),
            ("next_stage", None),
        )
        for field, expected in terminal_expectations:
            if workflow.get(field) != expected:
                steps.append(
                    _step_fail(
                        "STATE_CONSISTENCY",
                        f"{field} contradice el estado terminal",
                        f"{field}={expected}",
                        f"{field}={workflow.get(field)}",
                    )
                )
                break
    if workflow_status in PENDING_STATUSES:
        steps.append(_step_pass("PENDING_EXTERNAL_RESULT", workflow_path))
    elif workflow_status == REASSESSMENT_READY_STATUS:
        reassessments_path = folder / "topic_belonging_reassessments.json"
        reassessment_id = workflow.get("reassessment_id")
        try:
            reassessments = _read_json(reassessments_path, "topic_belonging_reassessments.json")
            ready = next(
                item for item in reassessments.get("reassessments", [])
                if isinstance(item, dict)
                and item.get("reassessment_id") == reassessment_id
                and item.get("status") == "EVIDENCE_RECEIVED"
            )
            if not ready:
                raise ValueError("no hay evidencia de reevaluación pendiente")
        except (StopIteration, ValueError) as exc:
            steps.append(
                _step_fail(
                    "READY_FOR_REASSESSMENT",
                    str(exc),
                    "evidencia persistida para la reevaluación pendiente",
                    "estado READY sin evidencia compatible",
                )
            )
        else:
            steps.append(_step_pass("READY_FOR_REASSESSMENT", workflow_path, reassessments_path))
            steps.append(_step_pending("PENDING_EXTERNAL_RESULT", "handoff de reevaluación preparado", "aún no preparado"))
    elif workflow_status == FINAL_STATUS and result_records:
        steps.append(_step_pass("PENDING_EXTERNAL_RESULT", folder / "roundtrip_results.json"))
    else:
        steps.append(
            _step_fail(
                "PENDING_EXTERNAL_RESULT",
                "el workflow no acredita espera o roundtrip persistido",
                "PENDING_EXTERNAL_RESULT o roundtrip persistido",
                workflow_status or "estado ausente",
            )
        )

    for stage in STAGES:
        steps.append(_stage_step(folder, episode_id, episode_state.get("mission_id"), stage, (result_records or {}).get(stage), workflow_status))

    failed = next((step for step in steps if step.status == "FAIL"), None)
    passed_stages = [stage for stage in STAGES if any(step.name == stage and step.status == "PASS" for step in steps)]
    if failed is not None:
        maximum = passed_stages[-1] if passed_stages else "PENDING_EXTERNAL_RESULT"
        result = "FAIL"
    elif len(passed_stages) == len(STAGES) and workflow_status == FINAL_STATUS:
        maximum = STAGES[-1]
        result = "PASS"
    else:
        maximum = passed_stages[-1] if passed_stages else "PENDING_EXTERNAL_RESULT"
        result = "PARTIAL"
    return P2Report(
        episode_id=episode_id,
        steps=tuple(steps),
        maximum_reached=maximum,
        result=result,
        failed_step=failed.name if failed else None,
        error=failed.error if failed else None,
        expected=failed.expected if failed else None,
        obtained=failed.obtained if failed else None,
    )


def render_p2_report(report: P2Report) -> str:
    lines = ["🧪 P2 REAL", ""]
    for step in report.steps:
        marker = {"PASS": "☑", "PENDING": "☐", "FAIL": "❌"}[step.status]
        lines.append(f"{marker} {step.name}: {step.status}")
        if step.status == "PASS" and step.evidence:
            lines.append(f"  Evidencia: {'; '.join(step.evidence)}")
    lines.extend(["", f"Punto máximo: {report.maximum_reached}"])
    if report.failed_step:
        lines.extend([
            f"Paso fallido: {report.failed_step}",
            f"Error: {report.error}",
            f"Esperado: {report.expected}",
            f"Obtenido: {report.obtained}",
        ])
    else:
        lines.append("Error: ninguno")
    lines.append(f"RESULTADO: {report.result}")
    return "\n".join(lines) + "\n"
