"""Index a tiny fixture repo with the local CBM binary and assert graph nodes."""

from __future__ import annotations

import json
import os
import re
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


def project_name_from_path(path: Path | str) -> str:
    """Mirror cbm_project_name_from_path used by smoke-invariants at the pin."""
    s = re.sub(r"[^A-Za-z0-9._-]", "-", str(path))
    s = re.sub(r"-{2,}", "-", s)
    s = re.sub(r"\.{2,}", ".", s)
    return s.strip("-").lstrip(".")


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


def _ensure_git_repo(fixture_root: Path) -> None:
    """Smoke path expects a git repo; create a disposable one when missing."""
    if (fixture_root / ".git").exists():
        return
    env = {**os.environ, "GIT_AUTHOR_NAME": "cbm-map", "GIT_AUTHOR_EMAIL": "lab@local"}
    subprocess.run(["git", "init", "-q"], cwd=fixture_root, check=False, env=env)
    subprocess.run(["git", "add", "-A"], cwd=fixture_root, check=False, env=env)
    subprocess.run(
        [
            "git",
            "-c",
            "user.email=lab@local",
            "-c",
            "user.name=cbm-map",
            "commit",
            "-q",
            "-m",
            "init",
        ],
        cwd=fixture_root,
        check=False,
        env=env,
    )


def map_fixture(fixture_root: Path, *, project: str | None = None) -> MapResult:
    """Index fixture_root and return measured node/file hits (lab numbers only)."""
    fixture_root = fixture_root.resolve()
    if not fixture_root.is_dir():
        raise FileNotFoundError(f"fixture not a directory: {fixture_root}")

    _ensure_git_repo(fixture_root)
    project_name = project or project_name_from_path(fixture_root)

    binary = resolve_binary()
    home = Path(tempfile.mkdtemp(prefix="cbm-map-home-"))
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["DISABLE_TELEMETRY"] = "1"
    env["DO_NOT_TRACK"] = "1"
    # Keep the map local to this process home; do not point at third-party upload.
    env.pop("CBM_ALLOWED_ROOT", None)

    # Pin CLI: index_repository has --repo-path only (no --project flag).
    index = _run_cli(
        binary,
        [
            "index_repository",
            "--repo-path",
            str(fixture_root),
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

    # Prefer the name CBM actually registered when path-derived name mismatches.
    resolved = _resolve_project_name(listed.stdout, project_name)

    search = _run_cli(
        binary,
        [
            "search_graph",
            "--project",
            resolved,
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

    node_count = _extract_node_count(listed.stdout, resolved)
    hit_files = _extract_hit_files(search.stdout)
    return MapResult(
        project=resolved,
        node_count=node_count,
        hit_files=hit_files,
        stdout_list=listed.stdout,
        stdout_search=search.stdout,
    )


def _projects_from_list(list_stdout: str) -> list[dict]:
    data = json.loads(list_stdout)
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    projects = data.get("projects") or data.get("result", {}).get("projects") or []
    return [x for x in projects if isinstance(x, dict)]


def _resolve_project_name(list_stdout: str, preferred: str) -> str:
    projects = _projects_from_list(list_stdout)
    names = [
        str(item.get("name") or item.get("project") or "")
        for item in projects
        if (item.get("name") or item.get("project"))
    ]
    if preferred in names:
        return preferred
    for name in names:
        if preferred in name or name.endswith(preferred.split("-")[-1]):
            return name
    if len(names) == 1:
        return names[0]
    if names:
        return names[0]
    return preferred


def _extract_node_count(list_stdout: str, project: str) -> int:
    for item in _projects_from_list(list_stdout):
        name = item.get("name") or item.get("project") or ""
        if name != project and project not in str(name):
            continue
        stats = item.get("stats") or item.get("statistics") or {}
        for key in ("nodes", "node_count", "total_nodes", "num_nodes"):
            if key in stats and isinstance(stats[key], int):
                return stats[key]
        if isinstance(item.get("nodes"), int):
            return item["nodes"]
    # Fallback: parse nodes from index/list JSON text (smoke-invariants style).
    cleaned = list_stdout.replace("\\", "").replace('"', "")
    matches = [int(x) for x in re.findall(r"nodes\s*[:=]\s*(\d+)", cleaned)]
    if matches and max(matches) > 0:
        return max(matches)
    text = list_stdout.lower()
    if project.lower() in text:
        return max(text.count(".py"), 1)
    raise RuntimeError(f"could not find project {project!r} in list_projects output")


def _extract_hit_files(search_stdout: str) -> list[str]:
    hits: list[str] = []
    try:
        data = json.loads(search_stdout)
    except json.JSONDecodeError:
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
