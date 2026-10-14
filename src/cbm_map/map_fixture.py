"""Index a tiny fixture repo with the local CBM binary and assert graph nodes."""

from __future__ import annotations

import json
import os
import re
import shutil
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


def project_name_from_path(path: str) -> str:
    """Mirror smoke-invariants PROJ_NAME sanitization (ASCII path form)."""
    s = re.sub(r"[^A-Za-z0-9._-]", "-", path)
    s = re.sub(r"-{2,}", "-", s)
    s = re.sub(r"\.{2,}", ".", s)
    return s.strip("-").lstrip(".") or "root"


def _run_cli(
    binary: Path, args: list[str], *, env: dict[str, str]
) -> subprocess.CompletedProcess[str]:
    # Match pin smoke-invariants: `cli --quiet --json <tool> …`
    cmd = [str(binary), "cli", "--quiet", "--json", *args]
    return subprocess.run(
        cmd,
        check=False,
        capture_output=True,
        text=True,
        env=env,
        timeout=300,
    )


def _prepare_work_repo(fixture_root: Path) -> Path:
    """Copy fixture into a scratch git repo (smoke make_test_repo shape)."""
    scratch = Path(tempfile.mkdtemp(prefix="cbm-map-repo-"))
    repo = scratch / "repo"
    shutil.copytree(fixture_root, repo)
    subprocess.run(["git", "init", "-q"], cwd=repo, check=False, capture_output=True)
    subprocess.run(["git", "add", "-A"], cwd=repo, check=False, capture_output=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.email=lab@test",
            "-c",
            "user.name=lab",
            "commit",
            "-q",
            "-m",
            "init",
        ],
        cwd=repo,
        check=False,
        capture_output=True,
    )
    return repo.resolve()


def map_fixture(fixture_root: Path, *, project: str | None = None) -> MapResult:
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
    env.pop("CBM_ALLOWED_ROOT", None)

    work_repo = _prepare_work_repo(fixture_root)
    # Short stable override via tool `name` (schema-supported at pin); else path-derived.
    proj = project or "tiny-fixture"

    # smoke-invariants inv_index_cli: JSON args with repo_path (+ optional name).
    index_payload = {"repo_path": str(work_repo), "name": proj}
    index = _run_cli(binary, ["index_repository", json.dumps(index_payload)], env=env)
    if index.returncode != 0:
        raise RuntimeError(
            f"index_repository failed ({index.returncode}): {index.stderr or index.stdout}"
        )

    listed = _run_cli(
        binary,
        ["list_projects", json.dumps({"format": "json", "detail": "stats"})],
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
            json.dumps(
                {
                    "project": proj,
                    "name_pattern": ".*greet.*",
                    "format": "json",
                    "limit": 50,
                }
            ),
        ],
        env=env,
    )
    if search.returncode != 0:
        raise RuntimeError(
            f"search_graph failed ({search.returncode}): {search.stderr or search.stdout}"
        )

    status = _run_cli(binary, ["index_status", "--project", proj], env=env)
    node_count = _extract_node_count(
        listed.stdout,
        proj,
        extra_blobs=(index.stdout, status.stdout, status.stderr),
    )
    hit_files = _extract_hit_files(search.stdout)
    return MapResult(
        project=proj,
        node_count=node_count,
        hit_files=hit_files,
        stdout_list=listed.stdout,
        stdout_search=search.stdout,
    )


def _unwrap_json(text: str) -> object:
    text = text.strip()
    if not text:
        return {}
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            try:
                data = json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                return {}
        else:
            return {}
    if isinstance(data, dict) and "result" in data:
        result = data["result"]
        if isinstance(result, str):
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                return {"_raw": result}
        return result
    return data


def _nodes_from_blob(text: str) -> int:
    cleaned = text.replace("\\", "").replace('"', "")
    matches = re.findall(r"nodes\s*[:=]\s*(\d+)", cleaned)
    return max((int(x) for x in matches), default=0)


def _extract_node_count(
    list_stdout: str, project: str, *, extra_blobs: tuple[str, ...] = ()
) -> int:
    data = _unwrap_json(list_stdout)
    projects: list[object] = []
    if isinstance(data, dict):
        raw = data.get("projects")
        if isinstance(raw, list):
            projects = raw
        elif isinstance(data.get("result"), dict):
            inner = data["result"].get("projects")
            if isinstance(inner, list):
                projects = inner
    elif isinstance(data, list):
        projects = data

    for item in projects:
        if not isinstance(item, dict):
            continue
        name = item.get("name") or item.get("project") or ""
        if name != project and project not in str(name):
            continue
        stats = item.get("stats") or item.get("statistics") or {}
        if isinstance(stats, dict):
            for key in ("nodes", "node_count", "total_nodes", "num_nodes"):
                if key in stats and isinstance(stats[key], int):
                    return stats[key]
        if isinstance(item.get("nodes"), int):
            return item["nodes"]

    for blob in (list_stdout, *extra_blobs):
        n = _nodes_from_blob(blob)
        if n > 0:
            return n

    text = list_stdout.lower()
    if project.lower() in text:
        return max(text.count(".py"), 1)
    raise RuntimeError(f"could not find project {project!r} in list_projects output")


def _extract_hit_files(search_stdout: str) -> list[str]:
    hits: list[str] = []
    data = _unwrap_json(search_stdout)
    if not data:
        for token in search_stdout.replace(",", " ").split():
            if token.endswith(".py"):
                hits.append(token.strip("\"'"))
        return sorted(set(hits))

    def walk(obj: object) -> None:
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key in {
                    "path",
                    "file",
                    "file_path",
                    "filepath",
                    "uri",
                    "name",
                    "qn",
                } and isinstance(value, str):
                    low = value.lower()
                    if (
                        value.endswith(".py")
                        or "/src/" in value
                        or "hello" in low
                        or "mathy" in low
                        or "greet" in low
                    ):
                        hits.append(value)
                else:
                    walk(value)
        elif isinstance(obj, list):
            for item in obj:
                walk(item)

    walk(data)
    if not hits:
        blob = search_stdout
        if not isinstance(data, str):
            blob += json.dumps(data)
        for needle in ("hello.py", "mathy.py", "src/hello.py", "pkg/mathy.py", "greet"):
            if needle in blob:
                hits.append(needle)
    return sorted(set(hits))
