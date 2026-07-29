from __future__ import annotations

import pytest

from tests.support.workspace_temp import cleanup_path, cleanup_tmp_root, ensure_tmp_root, make_temp_dir


@pytest.fixture(scope="session", autouse=True)
def _controlled_tmp_root():
    cleanup_tmp_root()
    ensure_tmp_root()
    yield
    cleanup_tmp_root()


@pytest.fixture
def tmp_path(request):
    path = make_temp_dir(request.node.name)
    try:
        yield path
    finally:
        cleanup_path(path)
