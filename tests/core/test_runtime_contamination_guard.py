from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

from src.scripts.runtime_contamination_guard import scan


ROOT = Path(__file__).parents[2]
POLICY = ROOT / "config" / "runtime_contamination_policy.json"
SCRIPT = ROOT / "src/scripts/runtime_contamination_guard.py"


def _write_policy(tmp_path: Path) -> Path:
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    policy["product_roots"] = ["config", "src", "AGENTS.md"]
    policy["generator_roots"] = ["tests", "src/scripts"]
    policy["historical_roots"] = ["workspace", "output", "profiles/editorial/mas_alla_del_guion/1.0.0"]
    policy["allowed_external_coordination"] = []
    policy["live_authority_paths"] = ["plans/001_CONTROL_OPERATIVO.md"]
    policy["optional_executor_catalogs"] = []
    policy["false_positive_paths"] = [
        "tests/core/test_runtime_contamination_guard.py",
        "config/runtime_contamination_policy.json",
    ]
    path = tmp_path / "config" / "runtime_contamination_policy.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(policy, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def test_local_absolute_path_allowed_but_team_reference_in_same_file_fails(tmp_path: Path):
    policy_path = _write_policy(tmp_path)
    local_settings = tmp_path / "config" / "local_settings.json"
    local_settings.write_text(
        json.dumps(
            {
                "vault_root": "C:\\YT_VAULT",
                "channel_id": "MasAllaDelGuion",
                "notes": "TEAM_01 must still be rejected here",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    result = scan(tmp_path, policy_path, collect_all_findings=True)
    labels = {finding["label"] for finding in result["all_findings"]}
    assert "absolute_windows_path" not in labels
    assert "human_team_code" in labels
    assert result["counts"]["ACTIVE_PRODUCT_CONTAMINATION"] == 1


def test_local_absolute_path_alone_is_allowed(tmp_path: Path):
    policy_path = _write_policy(tmp_path)
    local_settings = tmp_path / "config" / "local_settings.json"
    local_settings.write_text(
        json.dumps(
            {
                "vault_root": "C:\\YT_VAULT",
                "channel_id": "MasAllaDelGuion",
                "episode_id_format": "ep_{num:04d}",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    result = scan(tmp_path, policy_path, collect_all_findings=True)
    assert result["counts"]["ACTIVE_PRODUCT_CONTAMINATION"] == 0
    assert result["counts"]["MANUAL_REVIEW"] == 0
    assert not [
        finding for finding in result["all_findings"] if finding["path"] == "config/local_settings.json"
    ]


def test_active_surface_cannot_be_reclassified_as_historical_by_marker_text(tmp_path: Path):
    policy_path = _write_policy(tmp_path)
    active_file = tmp_path / "config" / "active.json"
    active_file.write_text(
        json.dumps(
            {
                "status": "HISTORICAL_REFERENCE",
                "notes": "TEAM_01 should still block because this file is active.",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    result = scan(tmp_path, policy_path, collect_all_findings=True)
    findings = [finding for finding in result["all_findings"] if finding["path"] == "config/active.json"]
    assert findings
    assert {finding["category"] for finding in findings} == {"ACTIVE_PRODUCT_CONTAMINATION"}


def test_overlapping_roots_scan_each_file_only_once(tmp_path: Path):
    policy_path = _write_policy(tmp_path)
    script_path = tmp_path / "src" / "scripts" / "tool.py"
    script_path.parent.mkdir(parents=True, exist_ok=True)
    script_path.write_text('print("TEAM_01")\n', encoding="utf-8")
    result = scan(tmp_path, policy_path, collect_all_findings=True)
    findings = [finding for finding in result["all_findings"] if finding["path"] == "src/scripts/tool.py"]
    assert len(findings) == 1
    assert findings[0]["category"] == "CONTAMINATED_GENERATOR_SOURCE"


def test_default_mode_ignores_scanner_reports_and_hides_historical_details(tmp_path: Path):
    policy_path = _write_policy(tmp_path)
    historical = tmp_path / "workspace" / "legacy.md"
    historical.parent.mkdir(parents=True, exist_ok=True)
    historical.write_text("Historical reference to Equipo 01.\n", encoding="utf-8")
    scanner_report = tmp_path / "output" / "runtime_contamination_final_2026-07-27.json"
    scanner_report.parent.mkdir(parents=True, exist_ok=True)
    scanner_report.write_text(("TEAM_01\n" * 5000), encoding="utf-8")
    default_result = scan(tmp_path, policy_path, include_historical_details=False, sample_limit=2)
    detailed_result = scan(tmp_path, policy_path, include_historical_details=True, sample_limit=2, collect_all_findings=True)
    assert default_result["counts"]["HISTORICAL_REFERENCE"] == 1
    assert all(finding["category"] != "HISTORICAL_REFERENCE" for finding in default_result["findings"])
    assert default_result.get("all_findings") is None
    assert detailed_result["counts"]["HISTORICAL_REFERENCE"] > default_result["counts"]["HISTORICAL_REFERENCE"]
    assert any(finding["path"].startswith("output/runtime_contamination_") for finding in detailed_result["all_findings"])


def test_cli_finishes_quickly_on_realistic_repository_copy(tmp_path: Path):
    policy_path = _write_policy(tmp_path)
    (tmp_path / "AGENTS.md").write_text("Neutral entrypoint.\n", encoding="utf-8")
    active = tmp_path / "config" / "payload.json"
    active.write_text(json.dumps({"owner": "CHANNEL_INTELLIGENCE"}, ensure_ascii=False), encoding="utf-8")
    script_path = tmp_path / "src" / "scripts" / "tool.py"
    script_path.parent.mkdir(parents=True, exist_ok=True)
    script_path.write_text("print('ok')\n", encoding="utf-8")
    historical = tmp_path / "workspace" / "legacy.md"
    historical.parent.mkdir(parents=True, exist_ok=True)
    historical.write_text("TEAM_01\n" * 200, encoding="utf-8")
    report = tmp_path / "output" / "runtime_contamination_final_2026-07-27.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("TEAM_01\n" * 30000, encoding="utf-8")

    start = time.perf_counter()
    done = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(tmp_path), "--policy", str(policy_path), "--sample-limit", "2"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=10,
    )
    elapsed = time.perf_counter() - start
    assert done.returncode == 0, done.stderr
    payload = json.loads(done.stdout)
    assert payload["counts"]["ACTIVE_PRODUCT_CONTAMINATION"] == 0
    assert payload["counts"]["CONTAMINATED_GENERATOR_SOURCE"] == 0
    assert payload["counts"]["MANUAL_REVIEW"] == 0
    assert payload["counts"]["HISTORICAL_REFERENCE"] == 200
    assert payload["runtime_seconds"] < 10
    assert elapsed < 10
    assert not any(finding["path"].startswith("output/runtime_contamination_") for finding in payload["sample_findings"])

def test_temporary_plan_reference_is_allowed_but_active_config_blocks(tmp_path: Path):
    policy_path = _write_policy(tmp_path)
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    policy["historical_roots"] = ["plans/plan_001"]
    policy_path.write_text(json.dumps(policy), encoding="utf-8")
    temporary = tmp_path / "plans" / "plan_001" / "B3.md"
    temporary.parent.mkdir(parents=True, exist_ok=True)
    temporary.write_text("Equipo 01 y Codex son referencias temporales.\n", encoding="utf-8")
    active = tmp_path / "config" / "runtime.json"
    active.parent.mkdir(parents=True, exist_ok=True)
    active.write_text('{"provider": "Codex"}\n', encoding="utf-8")
    result = scan(tmp_path, policy_path, collect_all_findings=True)
    temporary_findings = [item for item in result["all_findings"] if item["path"].startswith("plans/plan_001/")]
    assert temporary_findings and {item["category"] for item in temporary_findings} == {"HISTORICAL_REFERENCE"}
    assert result["counts"]["ACTIVE_PRODUCT_CONTAMINATION"] == 1

def test_optional_executor_catalog_is_visible_but_non_blocking(tmp_path: Path):
    policy_path = _write_policy(tmp_path)
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    policy["optional_executor_catalogs"] = ["config/agent_execution_profiles.json"]
    policy_path.write_text(json.dumps(policy), encoding="utf-8")
    catalog = tmp_path / "config" / "agent_execution_profiles.json"
    catalog.write_text('{"executor": "Codex"}\n', encoding="utf-8")
    active = tmp_path / "config" / "runtime.json"
    active.write_text('{"provider": "Codex"}\n', encoding="utf-8")

    result = scan(tmp_path, policy_path, collect_all_findings=True)

    catalog_findings = [item for item in result["all_findings"] if item["path"] == "config/agent_execution_profiles.json"]
    assert catalog_findings
    assert {item["category"] for item in catalog_findings} == {"OPTIONAL_EXECUTOR_CATALOG"}
    assert result["counts"]["ACTIVE_PRODUCT_CONTAMINATION"] == 1
    assert result["exit_code"] == 1


def test_optional_adapter_surfaces_and_negative_assertions_are_non_blocking(tmp_path: Path):
    policy_path = _write_policy(tmp_path)
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    policy["optional_adapter_test_roots"] = ["tests/opencode"]
    policy["optional_adapter_implementation_roots"] = [".opencode/agents"]
    policy_path.write_text(json.dumps(policy), encoding="utf-8")

    adapter_test = tmp_path / "tests" / "opencode" / "test_adapter.py"
    adapter_test.parent.mkdir(parents=True, exist_ok=True)
    adapter_test.write_text('assert "Codex" not in payload\n', encoding="utf-8")
    adapter_impl = tmp_path / ".opencode" / "agents" / "reviewer.md"
    adapter_impl.parent.mkdir(parents=True, exist_ok=True)
    adapter_impl.write_text("OpenCode adapter integration\n", encoding="utf-8")
    negative_assertion = tmp_path / "tests" / "test_negative.py"
    negative_assertion.write_text('assert "OpenCode" not in payload\n', encoding="utf-8")

    result = scan(tmp_path, policy_path, collect_all_findings=True)
    findings = result["all_findings"]
    assert {item["category"] for item in findings if item["path"] == "tests/opencode/test_adapter.py"} == {"OPTIONAL_ADAPTER_TEST"}
    assert {item["category"] for item in findings if item["path"] == ".opencode/agents/reviewer.md"} == {"OPTIONAL_ADAPTER_IMPLEMENTATION"}
    assert {item["category"] for item in findings if item["path"] == "tests/test_negative.py"} == {"NEGATIVE_CONTAMINATION_ASSERTION"}
    assert result["exit_code"] == 0


def test_negative_provider_regex_is_non_blocking(tmp_path: Path):
    policy_path = _write_policy(tmp_path)
    negative = tmp_path / "tests" / "core" / "test_engineering_skills.py"
    negative.parent.mkdir(parents=True, exist_ok=True)
    negative.write_text('FORBIDDEN_PROVIDER_MARKERS = re.compile(r"codex|opencode|chatgpt|antigravity|notebooklm|laboratorios")\n', encoding="utf-8")
    result = scan(tmp_path, policy_path, collect_all_findings=True)
    findings = [item for item in result["all_findings"] if item["path"] == "tests/core/test_engineering_skills.py"]
    assert findings and {item["category"] for item in findings} == {"NEGATIVE_CONTAMINATION_ASSERTION"}
    assert result["exit_code"] == 0


def test_live_authority_catches_suffixed_human_team_identifier(tmp_path: Path):
    policy_path = _write_policy(tmp_path)
    control = tmp_path / "plans" / "001_CONTROL_OPERATIVO.md"
    control.parent.mkdir(parents=True, exist_ok=True)
    control.write_text(
        "## 10. Historial de próxima decisión\n"
        "HISTORICAL_STATE: YES\n"
        "TEAM_02_B5_I2_FUNCTIONAL_SPECIFICATION: COMPLETE\n",
        encoding="utf-8",
    )
    result = scan(tmp_path, policy_path, collect_all_findings=True)
    findings = [item for item in result["all_findings"] if item["path"] == "plans/001_CONTROL_OPERATIVO.md"]
    assert findings
    assert {item["category"] for item in findings} == {"LIVE_AUTHORITY"}
    assert result["exit_code"] == 1
