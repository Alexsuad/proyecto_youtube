from __future__ import annotations

import argparse
import json
import re
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class Finding:
    path: str
    line: int
    pattern: str
    label: str
    severity: str
    category: str
    excerpt: str


DEFAULT_TEXT_EXTENSIONS = {
    ".md", ".json", ".yaml", ".yml", ".py", ".txt", ".toml", ".ini", ".cfg", ".csv"
}
SKIP_DIR_NAMES = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".pytest_tmp",
    ".uv-cache-b5",
    ".uv-cache-b5-i2",
    "tmp_test_subagent_foundation",
    ".runtime-tmp",
}
CATEGORY_PRIORITIES = {
    "FALSE_POSITIVE": 0,
    "OPTIONAL_EXECUTOR_CATALOG": 1,
    "OPTIONAL_ADAPTER_TEST": 1,
    "OPTIONAL_ADAPTER_IMPLEMENTATION": 1,
    "NEGATIVE_CONTAMINATION_ASSERTION": 1,
    "ALLOWED_EXTERNAL_COORDINATION": 2,
    "HISTORICAL_REFERENCE": 3,
    "CONTAMINATED_GENERATOR_SOURCE": 4,
    "ACTIVE_PRODUCT_CONTAMINATION": 5,
}


def _load_policy(policy_path: Path) -> dict[str, Any]:
    return json.loads(policy_path.read_text(encoding="utf-8"))


def _normalize(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _line_excerpt(text: str, line: int) -> str:
    return text.splitlines()[line - 1].strip()[:240]


def _is_scanner_generated_report(rel: str) -> bool:
    normalized = rel.replace("\\", "/")
    return normalized.startswith("output/runtime_contamination_") and normalized.endswith(".json")


def _path_matches(rel: str, candidate: str) -> bool:
    return rel == candidate or rel.startswith(candidate + "/")


def _path_category(rel: str, policy: dict[str, Any]) -> str:
    matches: list[tuple[int, int, str]] = []
    for item in policy.get("false_positive_paths", []):
        if rel == item:
            matches.append((len(item.split("/")), CATEGORY_PRIORITIES["FALSE_POSITIVE"], "FALSE_POSITIVE"))
    for category, key in (
        ("OPTIONAL_EXECUTOR_CATALOG", "optional_executor_catalogs"),
        ("OPTIONAL_ADAPTER_TEST", "optional_adapter_test_roots"),
        ("OPTIONAL_ADAPTER_IMPLEMENTATION", "optional_adapter_implementation_roots"),
        ("ALLOWED_EXTERNAL_COORDINATION", "allowed_external_coordination"),
        ("HISTORICAL_REFERENCE", "historical_roots"),
        ("CONTAMINATED_GENERATOR_SOURCE", "generator_roots"),
        ("ACTIVE_PRODUCT_CONTAMINATION", "product_roots"),
    ):
        for item in policy.get(key, []):
            if _path_matches(rel, item):
                matches.append((len(item.split("/")), CATEGORY_PRIORITIES[category], category))
    if not matches:
        return "MANUAL_REVIEW"
    matches.sort(key=lambda item: (-item[0], item[1]))
    return matches[0][2]


def _has_structured_historical_marker(text: str, markers: list[str]) -> bool:
    if not markers:
        return False
    for line in text.splitlines()[:5]:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped in markers:
            return True
        if any(stripped.startswith(prefix) for prefix in ('"status":', 'status:', '# status:')):
            if any(marker in stripped for marker in markers):
                return True
    return False


def _classify(rel: str, text: str, policy: dict[str, Any]) -> str:
    category = _path_category(rel, policy)
    if category != "MANUAL_REVIEW":
        return category
    if _has_structured_historical_marker(text, policy.get("historical_markers", [])):
        return "HISTORICAL_REFERENCE"
    return "MANUAL_REVIEW"


def _iter_policy_paths(root: Path, policy: dict[str, Any], *, include_historical_details: bool) -> list[Path]:
    ordered: list[Path] = []
    seen: set[Path] = set()
    groups = [
        *policy.get("product_roots", []),
        *policy.get("generator_roots", []),
        *policy.get("allowed_external_coordination", []),
        *policy.get("optional_executor_catalogs", []),
        *policy.get("optional_adapter_test_roots", []),
        *policy.get("optional_adapter_implementation_roots", []),
        *policy.get("false_positive_paths", []),
    ]
    if include_historical_details:
        groups.extend(policy.get("historical_roots", []))
    else:
        groups.extend(item for item in policy.get("historical_roots", []) if not item.startswith("output"))
    for item in groups:
        candidate = root / item
        if candidate.exists() and candidate not in seen:
            ordered.append(candidate)
            seen.add(candidate)
    return ordered


def _iter_unique_files(root: Path, policy: dict[str, Any], *, include_historical_details: bool):
    seen: set[Path] = set()
    for base in _iter_policy_paths(root, policy, include_historical_details=include_historical_details):
        candidates = [base] if base.is_file() else base.rglob("*")
        for path in candidates:
            if not path.exists() or not path.is_file():
                continue
            resolved = path.resolve()
            if resolved in seen:
                continue
            relative_parts = resolved.relative_to(root.resolve()).parts
            if any(part in SKIP_DIR_NAMES for part in relative_parts):
                continue
            if any(part.startswith(".tmp_") for part in relative_parts):
                continue
            if any(part.startswith("tmppytest-") for part in relative_parts):
                continue
            rel = "/".join(relative_parts) if relative_parts else path.name
            if not include_historical_details and _is_scanner_generated_report(rel):
                continue
            if path.suffix.lower() not in DEFAULT_TEXT_EXTENSIONS and path.name not in {"AGENTS.md", "README.md"}:
                continue
            seen.add(resolved)
            yield path, rel


def _is_field_level_exception(rel: str, label: str, excerpt: str, policy: dict[str, Any]) -> bool:
    for rule in policy.get("field_level_exceptions", []):
        if rel != rule.get("path"):
            continue
        if label not in set(rule.get("labels", [])):
            continue
        for field in rule.get("fields", []):
            if f'"{field}"' in excerpt:
                return True
    return False


def _finding_category(rel: str, excerpt: str, category: str, policy: dict[str, Any]) -> str:
    if category != "CONTAMINATED_GENERATOR_SOURCE":
        return category
    for pattern in policy.get("negative_contamination_assertion_patterns", []):
        if re.search(pattern, excerpt, re.IGNORECASE):
            return "NEGATIVE_CONTAMINATION_ASSERTION"
    return category


def _limited_samples(findings: list[Finding], sample_limit: int, *, include_historical_details: bool) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for finding in findings:
        if finding.category == "HISTORICAL_REFERENCE" and not include_historical_details:
            continue
        bucket = grouped[finding.category]
        if len(bucket) < sample_limit:
            bucket.append(finding.__dict__)
    ordered: list[dict[str, Any]] = []
    for category in (
        "ACTIVE_PRODUCT_CONTAMINATION",
        "CONTAMINATED_GENERATOR_SOURCE",
        "MANUAL_REVIEW",
        "HISTORICAL_REFERENCE",
        "OPTIONAL_EXECUTOR_CATALOG",
        "OPTIONAL_ADAPTER_TEST",
        "OPTIONAL_ADAPTER_IMPLEMENTATION",
        "NEGATIVE_CONTAMINATION_ASSERTION",
        "ALLOWED_EXTERNAL_COORDINATION",
        "FALSE_POSITIVE",
    ):
        ordered.extend(grouped.get(category, []))
    return ordered


def scan(
    root: Path,
    policy_path: Path,
    *,
    include_historical_details: bool = False,
    sample_limit: int = 5,
    collect_all_findings: bool = False,
) -> dict[str, Any]:
    policy = _load_policy(policy_path)
    compiled = [
        {
            "regex": re.compile(item["pattern"], re.IGNORECASE),
            "pattern": item["pattern"],
            "label": item["label"],
            "severity": item["severity"],
        }
        for item in policy.get("patterns", [])
    ]
    visible_findings: list[Finding] = []
    detailed_findings: list[Finding] = []
    blocked: list[str] = []
    counts = {
        "ACTIVE_PRODUCT_CONTAMINATION": 0,
        "CONTAMINATED_GENERATOR_SOURCE": 0,
        "HISTORICAL_REFERENCE": 0,
        "OPTIONAL_EXECUTOR_CATALOG": 0,
        "OPTIONAL_ADAPTER_TEST": 0,
        "OPTIONAL_ADAPTER_IMPLEMENTATION": 0,
        "NEGATIVE_CONTAMINATION_ASSERTION": 0,
        "ALLOWED_EXTERNAL_COORDINATION": 0,
        "FALSE_POSITIVE": 0,
        "MANUAL_REVIEW": 0,
    }
    started = time.perf_counter()

    for path, rel in _iter_unique_files(root, policy, include_historical_details=include_historical_details):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        except OSError as exc:
            blocked.append(f"{path}: {exc}")
            continue

        category = _classify(rel, text, policy)
        for item in compiled:
            for match in item["regex"].finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                excerpt = _line_excerpt(text, line)
                if _is_field_level_exception(rel, item["label"], excerpt, policy):
                    continue
                finding_category = _finding_category(rel, excerpt, category, policy)
                finding = Finding(rel, line, item["pattern"], item["label"], item["severity"], finding_category, excerpt)
                counts[finding_category] += 1
                if finding_category != "HISTORICAL_REFERENCE" or include_historical_details:
                    visible_findings.append(finding)
                if collect_all_findings or include_historical_details:
                    detailed_findings.append(finding)

    exit_code = 2 if blocked else (
        1
        if counts["ACTIVE_PRODUCT_CONTAMINATION"]
        or counts["CONTAMINATED_GENERATOR_SOURCE"]
        or counts["MANUAL_REVIEW"]
        else 0
    )
    result = {
        "policy_version": policy.get("policy_version"),
        "root": str(root),
        "counts": counts,
        "blocked": blocked,
        "exit_code": exit_code,
        "runtime_seconds": round(time.perf_counter() - started, 6),
        "include_historical_details": include_historical_details,
        "findings": [finding.__dict__ for finding in visible_findings],
        "sample_findings": _limited_samples(
            visible_findings,
            sample_limit,
            include_historical_details=include_historical_details,
        ),
    }
    if collect_all_findings or include_historical_details:
        result["all_findings"] = [finding.__dict__ for finding in detailed_findings]
    return result


def _build_summary(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "policy_version": result["policy_version"],
        "root": result["root"],
        "counts": result["counts"],
        "blocked": result["blocked"],
        "exit_code": result["exit_code"],
        "runtime_seconds": result["runtime_seconds"],
        "include_historical_details": result["include_historical_details"],
        "sample_findings": result["sample_findings"],
        "visible_findings": result["findings"],
    }


def _build_report(result: dict[str, Any]) -> dict[str, Any]:
    payload = _build_summary(result)
    payload["findings"] = result.get("all_findings", result["findings"])
    payload["full_findings_included"] = bool(result.get("all_findings"))
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Canonical runtime contamination scanner")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument(
        "--policy",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "config" / "runtime_contamination_policy.json",
    )
    parser.add_argument("--report", type=Path)
    parser.add_argument("--include-historical-details", action="store_true")
    parser.add_argument("--sample-limit", type=int, default=5)
    args = parser.parse_args()
    result = scan(
        args.root,
        args.policy,
        include_historical_details=args.include_historical_details,
        sample_limit=max(1, args.sample_limit),
        collect_all_findings=bool(args.report and args.include_historical_details),
    )
    summary_payload = json.dumps(_build_summary(result), ensure_ascii=False, indent=2)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(_build_report(result), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(summary_payload)
    return int(result["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
