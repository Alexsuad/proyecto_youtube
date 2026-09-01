from __future__ import annotations

import contextlib
import os
import shutil
from pathlib import Path
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[2]
TMP_ROOT = ROOT / ".runtime-tmp" / "pytest" / f"pid_{os.getpid()}"
PYTEST_TMP_ROOT = ROOT / ".runtime-tmp" / "pytest"
PRESERVED_RUNTIME_DIRS = {"plan010-m4-m5"}


def _slug(value: str) -> str:
    cleaned = []
    for char in value.lower():
        cleaned.append(char if char.isalnum() else "_")
    collapsed = "".join(cleaned).strip("_")
    return (collapsed[:40] or "case")


def ensure_tmp_root() -> Path:
    TMP_ROOT.mkdir(parents=True, exist_ok=True)
    return TMP_ROOT


def make_temp_dir(prefix: str = "case") -> Path:
    base = ensure_tmp_root()
    path = base / f"{_slug(prefix)}_{uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    return path


def cleanup_path(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)


def cleanup_tmp_root() -> None:
    runtime_root = ROOT / ".runtime-tmp"
    if not runtime_root.exists():
        return
    for child in runtime_root.iterdir():
        if child.name not in PRESERVED_RUNTIME_DIRS:
            shutil.rmtree(child, ignore_errors=True)


def root_tmp_artifacts() -> list[Path]:
    patterns = (".tmp_*", ".pytest_tmp*", "tmp_test_subagent_foundation")
    found: list[Path] = []
    for pattern in patterns:
        found.extend(sorted(ROOT.glob(pattern)))
    return found


@contextlib.contextmanager
def temporary_directory(prefix: str = "case"):
    path = make_temp_dir(prefix)
    try:
        yield path
    finally:
        cleanup_path(path)
