# Results

Local ship gate recorded **2026-10-14** (keyless lab suite on macOS). Heavy CBM source build + smoke-invariants run in GitHub Actions job `upstream` (ubuntu-latest) via `bash scripts/upstream-cbm.sh` — native macOS clang of `prod_lsp_all.o` is not part of the ship gate.

Pin note: after the verbatim `TEST_SEAMS=1` build, `scripts/apply-smoke-invariants-pin-fix.py` adapts vendor `smoke-invariants.sh` for daemon-side CLI (`index_status` flag form) and omits crasher/hanger vacuity guards that gating upstream `pr-smoke` never runs (`smoke-local.sh` instead of `smoke-invariants.sh`).

## Lab (local)

| Check | Result |
| --- | --- |
| `uv sync --locked --group dev` | pass |
| `uv run ruff check .` | pass |
| `uv run ruff format --check .` | pass |
| `uv run pytest -q` | 9 passed, 1 skipped (binary fixture awaits Linux CI build) |
| `python3 scripts/check-skills` | pass |
| `python3 scripts/check-banned-phrases` | pass |
| `python3 scripts/check-upstream-parity` | pass |
| `uvx pip-audit --strict` | No known vulnerabilities found |
| `.env` gitignored | yes (after `git init`) |

## Upstream pin

`vendor/codebase-memory-mcp` @ `49424722576191a1309d27ec7279c8676d0b1ec2` (short `494247225761`).

Vendor token multipliers remain **ellos reportan** / **según ellos** — not lab measurements.

## CI

Green ship run: https://github.com/SkilledDragonCorp/minilab-codebase-memory-map/actions/runs/38519292875 (SHA `f5f4075696e2a034501708a0e6d954198d1c6279`).

## CI (green)

- Run: https://github.com/SkilledDragonCorp/minilab-codebase-memory-map/actions/runs/38518919231
- SHA: `5cd0167` — jobs `lab`, `upstream` (build + smoke-invariants + fixture map), `security` all pass.

