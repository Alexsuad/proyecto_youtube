"""QA estructurado del EpisodeBrief y ResearchPack para B5-I1."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

from src.core.contract_validation import validate_against_schema, validate_research_pack
from src.core.gate_result import GateResult
from src.core.gate_runtime import run_gate
from src.core.input_validation import InputRequirement, validate_inputs
from src.core.status import GateStatus
from src.core.editorial_semantic_memory import current_artifacts_from_paths, run_memory_checkpoint

DEFAULT_ACTIVE_PROFILE = Path("config/active_editorial_profile.json")


def _load_json(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, [f"{path.name}: JSON inválido: {exc}"]
    if not isinstance(data, dict):
        return None, [f"{path.name}: la raíz debe ser un objeto JSON"]
    return data, []


def _profile_mismatch(brief: dict[str, Any], active: dict[str, Any]) -> list[str]:
    expected = {
        "profile_id": active.get("ACTIVE_PROFILE_ID"),
        "profile_version": active.get("ACTIVE_PROFILE_VERSION"),
        "profile_checksum": active.get("profile_checksum"),
    }
    return [
        f"{key} no coincide con el perfil activo"
        for key, value in expected.items()
        if not value or brief.get(key) != value
    ]


def _substantive_research_violations(research: dict[str, Any]) -> list[str]:
    violations: list[str] = []
    if not research.get("source_registry"):
        violations.append("ResearchPack requiere al menos una fuente trazable")
    if not research.get("facts"):
        violations.append("ResearchPack requiere al menos un hecho respaldado")
    if not (research.get("interpretations") or research.get("hypotheses")):
        violations.append("ResearchPack requiere al menos una interpretación o hipótesis trazable")
    if not research.get("narrative_evidence"):
        violations.append("ResearchPack requiere evidencia narrativa diferenciada")
    if not research.get("external_reality_evidence"):
        violations.append("ResearchPack requiere evidencia externa sobre la realidad diferenciada")
    return violations


def _brief_and_coverage_violations(brief: dict[str, Any], research: dict[str, Any]) -> list[str]:
    violations: list[str] = []
    hypothesis = brief.get("initial_editorial_hypothesis", {})
    if not isinstance(hypothesis, dict) or hypothesis.get("status") != "HYPOTHESIS_UNAPPROVED":
        violations.append("EpisodeBrief requiere una hipótesis inicial no aprobada.")
    if not brief.get("narrative_materials"):
        violations.append("EpisodeBrief sin material narrativo de partida bloquea el avance.")
    if brief.get("audience_status") != "INITIAL_HYPOTHESIS":
        violations.append("La audiencia concreta debe declararse como hipótesis inicial.")
    if brief.get("structure_status") != "INITIAL_HYPOTHESIS_REVISABLE_AFTER_RESEARCH":
        violations.append("La estructura candidata debe declararse revisable tras investigar.")
    coverage = {item.get("dimension_id"): item for item in research.get("coverage", []) if isinstance(item, dict)}
    alternative = coverage.get("ALTERNATIVE_PERSPECTIVES", {})
    if brief.get("nivel_investigacion") in ("PROFUNDO", "CRITICO") and not (research.get("alternative_views") or research.get("contradictions")):
        if not alternative.get("limitation_or_pending"):
            violations.append("Investigación profunda o crítica requiere rival, contradicción o justificación trazable.")
    return violations


def _coverage_disposition(brief: dict[str, Any], research: dict[str, Any]) -> tuple[list[str], list[str]]:
    warnings: list[str] = []
    blocked: list[str] = []
    for entry in research.get("coverage", []):
        if not isinstance(entry, dict) or entry.get("status") != "PARTIALLY_COVERED":
            continue
        if entry.get("editorial_impact") == "CRITICAL" and entry.get("mitigation_status") != "MITIGATED":
            blocked.append(f"Cobertura parcial crítica sin mitigación suficiente: {entry.get('dimension_id')}")
        else:
            warnings.append(f"Cobertura parcial limitada: {entry.get('dimension_id')}")
    claims = research.get("critical_claims_assessment", {})
    if brief.get("nivel_investigacion") in ("PROFUNDO", "CRITICO") and isinstance(claims, dict) and claims.get("status") == "NONE_JUSTIFIED":
        warnings.append("Claims críticos aún no identificados: ausencia justificada e impacto declarado")
    return warnings, blocked


def evaluate(
    ep_path: Path,
    episode_id: str | None = None,
    active_profile_path: Path = DEFAULT_ACTIVE_PROFILE,
    semantic_memory_path: Path | None = None,
    memory_current_artifacts: Mapping[str, Mapping[str, str]] | None = None,
    memory_candidate_ref: Mapping[str, Any] | None = None,
) -> GateResult:
    artifact_id = episode_id or ep_path.name
    brief_path = ep_path / "episode_brief.json"
    research_path = ep_path / "research_pack.json"

    blocked, failures, evidence = validate_inputs(
        [
            InputRequirement(brief_path, brief_path.name),
            InputRequirement(research_path, research_path.name),
            InputRequirement(active_profile_path, "active_editorial_profile"),
        ]
    )
    if blocked:
        return GateResult(
            "qa_brief_research",
            artifact_id,
            "2.0.0",
            GateStatus.BLOCKED,
            "Faltan entradas canónicas",
            blocked,
            evidence=evidence,
        )
    if failures:
        return GateResult(
            "qa_brief_research",
            artifact_id,
            "2.0.0",
            GateStatus.FAIL,
            "Entradas canónicas inválidas",
            failures,
            evidence=evidence,
        )

    brief, brief_errors = _load_json(brief_path)
    research, research_errors = _load_json(research_path)
    active, active_errors = _load_json(active_profile_path)
    json_errors = brief_errors + research_errors + active_errors
    if json_errors or brief is None or research is None or active is None:
        return GateResult(
            "qa_brief_research",
            artifact_id,
            "2.0.0",
            GateStatus.FAIL,
            "No se pudieron leer los contratos JSON",
            json_errors or ["Contrato JSON no disponible"],
            evidence=evidence,
        )

    memory_warnings: list[str] = []
    memory_path = semantic_memory_path or (ep_path / "editorial_semantic_memory.json")
    candidate_ref = memory_candidate_ref or {"artifact_ref": f"episode:{brief.get('episode_id')}", "version": brief.get("brief_version"), "checksum": current_artifacts_from_paths({f"episode:{brief.get('episode_id')}": brief_path}, {f"episode:{brief.get('episode_id')}": brief.get("brief_version")}).get(f"episode:{brief.get('episode_id')}", {}).get("checksum", "")}
    try:
        memory_result = run_memory_checkpoint(memory_path, candidate_ref, "PROPOSAL", memory_current_artifacts, {f"episode:{brief.get('episode_id')}": brief_path, f"research:{research.get('research_id')}": research_path}, {f"episode:{brief.get('episode_id')}": brief.get("brief_version"), f"research:{research.get('research_id')}": brief.get("brief_version")})
    except (OSError, ValueError) as exc:
        memory_result = {"status": "INVALIDATED", "violations": [f"MEMORY_CHECKPOINT_ERROR:{exc}"]}
    if memory_result is not None:
        evidence["memory_checkpoint_PROPOSAL"] = memory_result
        if memory_result.get("status") == "INVALIDATED":
            violations = list(memory_result.get("violations", []))
        else:
            violations = []
            if memory_result.get("status") == "INSUFFICIENT_HISTORY":
                memory_warnings.append("EditorialSemanticMemory: INSUFFICIENT_HISTORY requiere revisión funcional.")
    else:
        violations = []

    violations.extend(validate_against_schema(brief, "episode_brief"))
    violations.extend(validate_research_pack(research))
    violations.extend(_profile_mismatch(brief, active))
    if research.get("episode_id") != brief.get("episode_id"):
        violations.append("ResearchPack.episode_id no coincide con EpisodeBrief.episode_id")
    if research.get("brief_version") != brief.get("brief_version"):
        violations.append("ResearchPack.brief_version no coincide con EpisodeBrief.brief_version")
    violations.extend(_substantive_research_violations(research))
    violations.extend(_brief_and_coverage_violations(brief, research))
    coverage_warnings, coverage_blocked = _coverage_disposition(brief, research)

    evidence.update(
        {
            "inputs_reviewed": [brief_path.name, research_path.name],
            "active_profile": {
                "profile_id": active.get("ACTIVE_PROFILE_ID"),
                "profile_version": active.get("ACTIVE_PROFILE_VERSION"),
                "profile_checksum": active.get("profile_checksum"),
            },
            "source_count": len(research.get("source_registry", [])),
        }
    )
    if violations:
        return GateResult(
            "qa_brief_research",
            artifact_id,
            "2.0.0",
            GateStatus.FAIL,
            "Brief o investigación no superan B5-I1",
            violations,
            evidence=evidence,
        )

    if coverage_blocked:
        return GateResult(
            "qa_brief_research", artifact_id, "2.1.0", GateStatus.BLOCKED,
            "La cobertura crítica no permite continuar", coverage_blocked, evidence=evidence,
        )

    warnings: list[str] = memory_warnings + coverage_warnings
    if research.get("limitations"):
        warnings.extend([f"Limitación declarada: {item}" for item in research["limitations"]])
    if research.get("unsupported_claims"):
        warnings.append("Existen claims no sostenibles correctamente declarados")
    status = GateStatus.WARN if warnings else GateStatus.PASS
    return GateResult(
        "qa_brief_research",
        artifact_id,
        "2.0.0",
        status,
        "Brief e investigación canónicos validados",
        warnings=warnings,
        evidence=evidence,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ep_path", required=True)
    parser.add_argument("--ep-id")
    parser.add_argument("--active-profile", default=str(DEFAULT_ACTIVE_PROFILE))
    parser.add_argument("--semantic-memory")
    parser.add_argument("--output-root")
    args = parser.parse_args()
    return run_gate(
        lambda: evaluate(Path(args.ep_path), args.ep_id, Path(args.active_profile), Path(args.semantic_memory) if args.semantic_memory else None),
        output_root=args.output_root,
    )


if __name__ == "__main__":
    import sys

    sys.exit(main())
