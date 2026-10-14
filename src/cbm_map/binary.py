"""Resolve the source-built codebase-memory-mcp binary under vendor/."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BIN = ROOT / "vendor" / "codebase-memory-mcp" / "build" / "c" / "codebase-memory-mcp"
PIN = "49424722576191a1309d27ec7279c8676d0b1ec2"


def resolve_binary() -> Path:
    env = os.environ.get("CBM_BIN", "").strip()
    if env:
        path = Path(env).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"CBM_BIN not a file: {path}")
        return path
    if DEFAULT_BIN.is_file():
        return DEFAULT_BIN.resolve()
    raise FileNotFoundError(
        f"missing binary at {DEFAULT_BIN}; run: bash scripts/upstream-cbm.sh "
        f"(or set CBM_BIN). Pin {PIN}."
    )
