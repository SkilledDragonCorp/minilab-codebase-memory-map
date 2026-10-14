"""Keyless fixture map against the source-built binary."""

from __future__ import annotations

from pathlib import Path

import pytest

from cbm_map.binary import DEFAULT_BIN, PIN
from cbm_map.map_fixture import map_fixture

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "tiny-repo"


@pytest.mark.binary
def test_map_fixture_has_graph_nodes_for_fixture_files() -> None:
    if not DEFAULT_BIN.is_file():
        pytest.skip(
            f"binary unavailable at {DEFAULT_BIN} (pin {PIN}); "
            "run bash scripts/upstream-cbm.sh before this test"
        )
    result = map_fixture(FIXTURE)
    assert result.node_count >= 1
    blob = " ".join(result.hit_files) + result.stdout_search + result.stdout_list
    assert "hello.py" in blob or "mathy.py" in blob


def test_project_name_from_path_mirrors_smoke() -> None:
    from cbm_map.map_fixture import project_name_from_path

    assert project_name_from_path("/tmp/foo/bar") == "tmp-foo-bar"
