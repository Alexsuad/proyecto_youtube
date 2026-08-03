from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCAN_ROOTS = [
    ROOT / "config",
    ROOT / "prompts",
    ROOT / "src",
    ROOT / "tests",
    ROOT / ".agent",
]
EXCLUDED_DIR_NAMES = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    "workspace",
    "output",
    ".runtime-tmp",
    "tmp",
    "temp",
}
EXCLUDED_PATH_PARTS = {
    "docs",
    "docs_control",
    "plans",
    "workspace",
    "output",
}
TEXT_SUFFIXES = {
    ".py",
    ".json",
    ".md",
    ".yaml",
    ".yml",
    ".txt",
    ".toml",
    ".ini",
    ".cfg",
    ".sh",
    ".ps1",
}
REPLACEMENT_CHAR = chr(0xFFFD)
MOJIBAKE_MARKERS = (
    chr(0x00C3),
    chr(0x00C2),
    chr(0x00E2) + chr(0x20AC),
    chr(0x00E2) + chr(0x20AC) + chr(0x0153),
    chr(0x00E2) + chr(0x20AC) + chr(0x009D),
    chr(0x00E2) + chr(0x20AC) + chr(0x201C),
    chr(0x00E2) + chr(0x20AC) + chr(0x201D),
    chr(0x00E2) + chr(0x20AC) + chr(0x00A6),
)
EMBEDDED_QUESTION_RE = re.compile(r"(?<=\w)\?(?=\w)")


def _should_skip(path: Path) -> bool:
    relative_parts = set(path.relative_to(ROOT).parts)
    if relative_parts & EXCLUDED_PATH_PARTS:
        return True
    return any(part in EXCLUDED_DIR_NAMES for part in path.parts)


def _iter_text_files() -> list[Path]:
    files: list[Path] = []
    for scan_root in SCAN_ROOTS:
        if not scan_root.exists():
            continue
        for path in scan_root.rglob("*"):
            if not path.is_file():
                continue
            if _should_skip(path):
                continue
            if path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            files.append(path)
    return sorted(files)


def test_active_surfaces_have_no_text_integrity_residues() -> None:
    issues: list[str] = []
    for path in _iter_text_files():
        relative = path.relative_to(ROOT)
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            issues.append(f"{relative}: decode_error utf-8 {exc}")
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            if REPLACEMENT_CHAR in line:
                issues.append(f"{relative}:{lineno}: contains U+FFFD")
            if any(marker in line for marker in MOJIBAKE_MARKERS):
                issues.append(f"{relative}:{lineno}: contains mojibake marker")
            if EMBEDDED_QUESTION_RE.search(line):
                issues.append(f"{relative}:{lineno}: contains embedded question mark in word")
    assert not issues, "\n".join(issues)
