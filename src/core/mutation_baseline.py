"""Portable, evidence-bearing TH-08 mutation probes for context resolution."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASELINE_VALID = "BASELINE_VALID"
KILLED = "KILLED"
SURVIVED = "SURVIVED"
INFRASTRUCTURE_ERROR = "INFRASTRUCTURE_ERROR"
EQUIVALENT_MUTANT = "EQUIVALENT_MUTANT"

PROBE = """import hashlib, json, sys
from pathlib import Path
from src.core import context_resolution
from src.core.context_resolution import ContextResolutionError, resolve_context
root = Path(sys.argv[1]); path_mode = sys.argv[2]; checksum_mode = sys.argv[3]; expected = sys.argv[4]
root.mkdir(parents=True, exist_ok=True)
(root / 'config').mkdir(exist_ok=True); (root / 'policies').mkdir(exist_ok=True)
(root / 'config/context_resolution_policy.json').write_text(json.dumps({'normative_allowed_roots':['policies'],'evidentiary_allowed_roots':[],'historical_allowed_roots':[]}))
inside = root / 'policies/rule.md'; inside.write_text('rule')
outside = root.parent / 'outside.md'; outside.write_text('outside')
untrusted = root / 'untrusted.md'; untrusted.write_text('untrusted')
target = outside if path_mode == 'outside' else (untrusted if path_mode == 'untrusted' else inside)
digest = hashlib.sha256(target.read_bytes()).hexdigest()
if checksum_mode == 'bad': digest = '0' * 64
ref = {'ref_id':'x','context_class':'NORMATIVE','artifact_path':str(target) if path_mode == 'outside' else ('untrusted.md' if path_mode == 'untrusted' else 'policies/rule.md'),'artifact_type':'markdown','artifact_sha256':digest,'authority_domain':'D','required':True}
try:
    resolve_context([ref], root=root, capability_id='C', role_id='R', run_id='RUN')
    observed = 'ALLOWED'
except ContextResolutionError:
    observed = 'BLOCKED'
print(json.dumps({'module': str(Path(context_resolution.__file__).resolve()), 'observed': observed}))
raise SystemExit(0 if observed == expected else 1)
"""


@dataclass(frozen=True)
class ProbeExecution:
    status: str
    returncode: int | None
    stdout: str
    stderr: str
    imported_module: str | None
    observed: str | None
    reason: str | None = None


@dataclass(frozen=True)
class MutationSpec:
    mutant_id: str
    source: str
    replacement: str
    path_mode: str
    checksum_mode: str
    equivalent: bool = False


MUTATIONS = (
    MutationSpec(
        "ALLOWED_ROOT_POLICY_BYPASS",
        "    return False\n\n\ndef _artifact_digests",
        "    return True\n\n\ndef _artifact_digests",
        "untrusted", "valid",
    ),
    MutationSpec(
        "CHECKSUM_GUARD_BYPASS",
        "if expected_raw and expected_raw != raw_digest.lower():",
        "if False:",
        "inside", "bad",
    ),
    MutationSpec(
        "ERROR_TOKEN_TEXT_ONLY",
        '"CONTEXT_JSON_CANONICALIZATION_FAILED"',
        '"CONTEXT_JSON_CANONICALIZATION_FAILED_V2"',
        "inside", "bad",
    ),
    MutationSpec(
        "EMPTY_PATH_BOOLEAN_EQUIVALENT",
        "or not relative:",
        "or not bool(relative):",
        "inside", "bad", equivalent=True,
    ),
)


def _run_probe(module_source: str, *, path_mode: str, checksum_mode: str, expected: str, force_error: bool = False) -> ProbeExecution:
    try:
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            package = temp / "src/core"
            package.mkdir(parents=True)
            (temp / "src/__init__.py").write_text("", encoding="utf-8")
            (package / "__init__.py").write_text("", encoding="utf-8")
            (package / "plan_005_invariants.py").write_text((ROOT / "src/core/plan_005_invariants.py").read_text(encoding="utf-8"), encoding="utf-8")
            module = package / "context_resolution.py"
            if force_error:
                return ProbeExecution(INFRASTRUCTURE_ERROR, None, "", "forced probe infrastructure error", None, None, "FORCED_INFRASTRUCTURE_ERROR")
            module.write_text(module_source, encoding="utf-8")
            case = temp / "case"
            case.mkdir(parents=True, exist_ok=True)
            result = subprocess.run(
                [sys.executable, "-c", PROBE, str(case), path_mode, checksum_mode, expected],
                cwd=temp, env={**os.environ, "PYTHONPATH": str(temp)}, capture_output=True, text=True,
                timeout=30,
            )
            try:
                payload = json.loads(result.stdout.strip())
                imported = str(Path(payload["module"]).resolve())
                observed = str(payload["observed"])
            except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                return ProbeExecution(INFRASTRUCTURE_ERROR, result.returncode, result.stdout, result.stderr, None, None, "PROBE_OUTPUT_INVALID")
            if Path(imported) != module.resolve():
                return ProbeExecution(INFRASTRUCTURE_ERROR, result.returncode, result.stdout, result.stderr, imported, observed, "MUTATED_MODULE_NOT_IMPORTED")
            if result.returncode not in {0, 1}:
                return ProbeExecution(INFRASTRUCTURE_ERROR, result.returncode, result.stdout, result.stderr, imported, observed, "PROBE_CRASHED")
            return ProbeExecution(BASELINE_VALID if result.returncode == 0 else SURVIVED, result.returncode, result.stdout, result.stderr, imported, observed)
    except (OSError, subprocess.SubprocessError) as exc:
        return ProbeExecution(INFRASTRUCTURE_ERROR, None, "", str(exc), None, None, "HARNESS_EXCEPTION")


def evaluate_mutation(spec: MutationSpec, *, original: str | None = None) -> dict:
    original = original or (ROOT / "src/core/context_resolution.py").read_text(encoding="utf-8")
    baseline = _run_probe(original, path_mode=spec.path_mode, checksum_mode=spec.checksum_mode, expected="BLOCKED")
    row = {"mutant_id": spec.mutant_id, "baseline": asdict(baseline)}
    if baseline.status != BASELINE_VALID:
        row.update({"status": INFRASTRUCTURE_ERROR, "classification": None, "reason": "BASELINE_NOT_VALID"})
        return row
    if spec.source not in original:
        row.update({"status": INFRASTRUCTURE_ERROR, "classification": None, "reason": "MUTATION_SOURCE_NOT_FOUND"})
        return row
    mutated = original.replace(spec.source, spec.replacement, 1)
    if mutated == original:
        row.update({"status": INFRASTRUCTURE_ERROR, "classification": None, "reason": "MUTATION_NOT_APPLIED"})
        return row
    mutation = _run_probe(mutated, path_mode=spec.path_mode, checksum_mode=spec.checksum_mode, expected="BLOCKED")
    row["mutation"] = asdict(mutation)
    if mutation.status == INFRASTRUCTURE_ERROR:
        row.update({"status": INFRASTRUCTURE_ERROR, "classification": None, "reason": mutation.reason})
    elif mutation.status == BASELINE_VALID:
        row.update({"status": EQUIVALENT_MUTANT if spec.equivalent else SURVIVED, "classification": "EQUIVALENT_MUTANT" if spec.equivalent else "LOW_VALUE_MUTATION", "reason": "MUTANT_PRESERVED_BASELINE_BEHAVIOR"})
    else:
        row.update({"status": KILLED, "classification": None, "reason": "MUTANT_CHANGED_PROBE_BEHAVIOR"})
    return row


def build_mutation_report(root: Path = ROOT) -> dict:
    original = (root / "src/core/context_resolution.py").read_text(encoding="utf-8")
    records = [evaluate_mutation(spec, original=original) for spec in MUTATIONS]
    killed = [record for record in records if record["status"] == KILLED]
    survivors = [record for record in records if record["status"] == SURVIVED]
    infrastructure = [record for record in records if record["status"] == INFRASTRUCTURE_ERROR]
    equivalents = [record for record in records if record["status"] == EQUIVALENT_MUTANT]
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    return {
        "schema_version": "1.0.0", "plan_id": "PLAN_004", "mission_id": "TH-08", "repository_revision": revision,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_inputs": [{"path": "src/core/context_resolution.py", "sha256": hashlib.sha256((root / "src/core/context_resolution.py").read_bytes()).hexdigest()}],
        "evidence_refs": ["reports/implementation/plan_004/TH07_quality_baseline.json"], "limitations": [],
        "result": "PASS" if not survivors and not infrastructure else "COMPLETED_WITH_FINDINGS",
        "artifact_type": "MUTATION_TESTING", "scope": {"modules": ["src/core/context_resolution.py"], "budget": "4 isolated mutations; no network or paid execution"},
        "mutants_generated": len(records), "baseline_valid": sum(record["baseline"]["status"] == BASELINE_VALID for record in records),
        "mutants_killed": len(killed), "survivors": survivors, "equivalent_mutants": equivalents,
        "infrastructure_errors": infrastructure, "mutation_records": records, "runtime": "local isolated subprocess", "cost": "0",
        "useful_findings": [], "noisy_findings": [record["mutant_id"] for record in survivors if record["classification"] == "LOW_VALUE_MUTATION"],
        "recommendation": "KEEP_SELECTIVELY",
    }


def write_th08_artifact(root: Path = ROOT) -> Path:
    path = root / "reports/implementation/plan_004/TH08_mutation_testing.json"
    path.write_text(json.dumps(build_mutation_report(root), indent=2) + "\n", encoding="utf-8")
    return path
