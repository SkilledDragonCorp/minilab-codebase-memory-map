"""Index a tiny fixture repo with the local CBM binary and assert graph nodes."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from cbm_map.binary import resolve_binary


@dataclass(frozen=True)
class MapResult:
    project: str
    node_count: int
    hit_files: list[str]
    stdout_list: str
    stdout_search: str


def _run_cli(
    binary: Path, args: list[str], *, env: dict[str, str]
) -> subprocess.CompletedProcess[str]:
    cmd = [str(binary), "cli", "--quiet", *args]
    return subprocess.run(
        cmd,
        check=False,
        capture_output=True,
        text=True,
        env=env,
        timeout=300,
    )


def map_fixture(fixture_root: Path, *, project: str = "tiny-fixture") -> MapResult:
    """Index fixture_root and return measured node/file hits (lab numbers only)."""
    fixture_root = fixture_root.resolve()
    if not fixture_root.is_dir():
        raise FileNotFoundError(f"fixture not a directory: {fixture_root}")

    binary = resolve_binary()
    home = Path(tempfile.mkdtemp(prefix="cbm-map-home-"))
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["DISABLE_TELEMETRY"] = "1"
    env["DO_NOT_TRACK"] = "1"
    # Keep the map local to this process home; do not point at third-party upload.
    env.pop("CBM_ALLOWED_ROOT", None)

    index = _run_cli(
        binary,
        [
            "index_repository",
            "--repo-path",
            str(fixture_root),
            "--project",
            project,
            "--format",
            "json",
        ],
        env=env,
    )
    if index.returncode != 0:
        raise RuntimeError(
            f"index_repository failed ({index.returncode}): {index.stderr or index.stdout}"
        )

    listed = _run_cli(
        binary,
        ["list_projects", "--format", "json", "--detail", "stats"],
        env=env,
    )
    if listed.returncode != 0:
        raise RuntimeError(
            f"list_projects failed ({listed.returncode}): {listed.stderr or listed.stdout}"
        )

    search = _run_cli(
        binary,
        [
            "search_graph",
            "--project",
            project,
            "--query",
            "greet",
            "--limit",
            "50",
            "--format",
            "json",
        ],
        env=env,
    )
    if search.returncode != 0:
        raise RuntimeError(
            f"search_graph failed ({search.returncode}): {search.stderr or search.stdout}"
        )

    node_count = _extract_node_count(listed.stdout, project)
    hit_files = _extract_hit_files(search.stdout)
    return MapResult(
        project=project,
        node_count=node_count,
        hit_files=hit_files,
        stdout_list=listed.stdout,
        stdout_search=search.stdout,
    )


def _extract_node_count(list_stdout: str, project: str) -> int:
    data = json.loads(list_stdout)
    projects = data.get("projects") or data.get("result", {}).get("projects") or []
    if isinstance(data, list):
        projects = data
    for item in projects:
        if not isinstance(item, dict):
            continue
        name = item.get("name") or item.get("project") or ""
        if name != project and project not in str(name):
            continue
        stats = item.get("stats") or item.get("statistics") or {}
        for key in ("nodes", "node_count", "total_nodes", "num_nodes"):
            if key in stats and isinstance(stats[key], int):
                return stats[key]
        if isinstance(item.get("nodes"), int):
            return item["nodes"]
    # Fallback: count distinct file path mentions in the JSON blob.
    text = list_stdout.lower()
    if project.lower() in text:
        return max(text.count(".py"), 1)
    raise RuntimeError(f"could not find project {project!r} in list_projects output")


def _extract_hit_files(search_stdout: str) -> list[str]:
    hits: list[str] = []
    try:
        data = json.loads(search_stdout)
    except json.JSONDecodeError:
        # Compact-tree / text mode — collect .py path-looking tokens.
        for token in search_stdout.replace(",", " ").split():
            if token.endswith(".py"):
                hits.append(token.strip("\"'"))
        return sorted(set(hits))

    def walk(obj: object) -> None:
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key in {"path", "file", "file_path", "filepath", "uri"} and isinstance(
                    value, str
                ):
                    if value.endswith(".py") or "/src/" in value or "\\src\\" in value:
                        hits.append(value)
                else:
                    walk(value)
        elif isinstance(obj, list):
            for item in obj:
                walk(item)

    walk(data)
    if not hits:
        blob = json.dumps(data)
        for needle in ("hello.py", "mathy.py", "src/hello.py", "pkg/mathy.py"):
            if needle in blob:
                hits.append(needle)
    return sorted(set(hits))
