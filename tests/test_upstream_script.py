"""Parity: upstream-cbm.sh carries the smoke-unix source-build commands."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_check_upstream_parity_script() -> None:
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check-upstream-parity")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout


def test_upstream_script_is_source_build_only() -> None:
    text = (ROOT / "scripts" / "upstream-cbm.sh").read_text(encoding="utf-8")
    assert "scripts/build.sh CC=gcc CXX=g++ TEST_SEAMS=1" in text
    assert "scripts/smoke-invariants.sh build/c/codebase-memory-mcp" in text
    for line in text.splitlines():
        if line.strip().startswith("#"):
            continue
        assert "install.sh" not in line
