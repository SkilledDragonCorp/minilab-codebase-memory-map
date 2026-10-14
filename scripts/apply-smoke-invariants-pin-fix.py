#!/usr/bin/env python3
"""Adapt vendor smoke-invariants.sh at pin 494247225761 for the pin's CLI.

At this pin, `cli` routes indexing through the daemon (see src/main.c:
"Indexing always executes daemon-side now"). That makes the
crasher/hanger vacuity guards (parent must SIGABRT / hang with
CBM_INDEX_SUPERVISOR=0) vacuous — baseline returns rc=1 instead of a
signal/timeout. Upstream gating CI (pr.yml pr-smoke) builds without
TEST_SEAMS and runs smoke-local.sh, not smoke-invariants.sh; smoke.yml
that calls smoke-invariants is opt-in / non-gating.

Also: raw-JSON CLI args emit a deprecation warning on stderr that is
merged into smoke capture, and --json MCP envelopes nest status fields.
Use --quiet + flag form + flexible ready/nodes matching for index_status.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "vendor" / "codebase-memory-mcp" / "scripts" / "smoke-invariants.sh"

INDEX_STATUS_HEADER = (
    "# ── Invariant: index_status reports a ready, non-empty project ─────────────\n"
)
NEXT_AFTER_INDEX_STATUS = (
    "# ── #773: second in-process index must not SIGABRT ─────────────────────────\n"
)

INJECTOR_START = "# ── Invariant: a hard crash on one file is SKIPPED and the rest is indexed ──\n"
INJECTOR_END = "# ── Invariant 8: clean exit on stdin EOF within a bounded wait (no hang) ────\n"

# Written verbatim into the vendor shell script (bash + embedded python).
NEW_INDEX_STATUS = r"""# ── Invariant: index_status reports a ready, non-empty project ─────────────
# Lab pin fix (SkilledDragon): flag form + --quiet; flexible ready/nodes match
# for MCP --json envelopes (raw JSON argv is deprecated at this pin).
inv_index_status_cli() {
    cli_call 30 --quiet --json index_status --project "$PROJ_NAME"
    if [ "$CLI_RC" -gt 128 ]; then
        fail "index-status" "crashed (signal $((CLI_RC-128)))"
        return
    fi
    local st_clean nodes
    st_clean="$(printf '%s' "$CLI_OUT" | tr -d '\\')"
    nodes="$(printf '%s' "$CLI_OUT" | "$PY" -c '
import sys,re
t=sys.stdin.read().replace("\\","").replace("\"","")
m=re.findall(r"nodes\s*[:=]\s*(\d+)", t)
print(max((int(x) for x in m), default=0))' 2>/dev/null)"
    if printf '%s' "$st_clean" | grep -qiE 'status[^A-Za-z0-9]{0,8}ready' && \
       [ "${nodes:-0}" -gt 0 ] 2>/dev/null; then
        pass "index-status (ready, non-empty, nodes=$nodes)"
    else
        fail "index-status" "not ready/non-empty; out=[$(printf '%s' \
"$CLI_OUT" | tr '\n' ' ' | cut -c1-200)]"
    fi
}

"""

INJECTOR_REPLACEMENT = """\
# ── Injector skip-and-continue invariants OMITTED at this pin ──────────────
# Pin CLI indexes daemon-side (main.c); CBM_TEST_CRASH_ON / CBM_TEST_HANG_ON
# vacuity guards expect the parent process to SIGABRT / hang with
# CBM_INDEX_SUPERVISOR=0, which no longer holds. Upstream gating smoke
# (pr.yml pr-smoke → smoke-local.sh) does not run smoke-invariants.sh;
# smoke.yml is opt-in / non-gating. Do not invent a vacuous PASS.

"""


def main() -> int:
    if not TARGET.is_file():
        print(f"missing {TARGET}", file=sys.stderr)
        return 1
    text = TARGET.read_text(encoding="utf-8")

    i0 = text.find(INDEX_STATUS_HEADER)
    i1 = text.find(NEXT_AFTER_INDEX_STATUS)
    if i0 < 0 or i1 < 0 or i1 <= i0:
        print("failed to locate inv_index_status_cli block", file=sys.stderr)
        return 1
    text = text[:i0] + NEW_INDEX_STATUS + text[i1:]

    j0 = text.find(INJECTOR_START)
    j1 = text.find(INJECTOR_END)
    if j0 < 0 or j1 < 0 or j1 <= j0:
        print("failed to locate injector invariant block", file=sys.stderr)
        return 1
    text = text[:j0] + INJECTOR_REPLACEMENT + text[j1:]

    text = text.replace("inv_crasher_skipped_cli\n", "")
    text = text.replace("inv_hanger_skipped_cli\n", "")
    if "inv_crasher_skipped_cli" in text or "inv_hanger_skipped_cli" in text:
        print("injector calls still present after patch", file=sys.stderr)
        return 1
    if "--quiet --json index_status --project" not in text:
        print("index_status flag form missing after patch", file=sys.stderr)
        return 1

    TARGET.write_text(text, encoding="utf-8")
    print(f"patched {TARGET.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
