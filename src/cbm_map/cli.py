"""CLI: map a local fixture with the source-built CBM binary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cbm_map.map_fixture import map_fixture

DEFAULT_FIXTURE = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "tiny-repo"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="cbm-map",
        description="Index a local fixture with source-built codebase-memory-mcp (keyless).",
    )
    parser.add_argument(
        "fixture",
        nargs="?",
        default=str(DEFAULT_FIXTURE),
        help="Path to fixture repository root",
    )
    parser.add_argument(
        "--project",
        default=None,
        help="Optional CBM project name override (default: derived from fixture path)",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON report")
    args = parser.parse_args(argv)

    result = map_fixture(Path(args.fixture), project=args.project)
    payload = {
        "project": result.project,
        "node_count": result.node_count,
        "hit_files": result.hit_files,
        "note": (
            "Lab fixture measurements only. Vendor token claims are ellos reportan / según ellos."
        ),
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(
            f"OK map project={result.project} nodes={result.node_count} "
            f"hits={len(result.hit_files)}"
        )
        for path in result.hit_files:
            print(f"  hit {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
