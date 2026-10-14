# Results

Local ship gate recorded **2026-10-14** (keyless lab suite on macOS). Heavy CBM source build + smoke-invariants run in GitHub Actions job `upstream` (ubuntu-latest) via `bash scripts/upstream-cbm.sh` — native macOS clang of `prod_lsp_all.o` is not part of the ship gate.

## Lab (local)

| Check | Result |
| --- | --- |
| `uv sync --locked --group dev` | pass |
| `uv run ruff check .` | pass |
| `uv run ruff format --check .` | pass |
| `uv run pytest -q` | 7 passed, 1 skipped (binary fixture awaits Linux build) |
| `python3 scripts/check-skills` | pass |
| `python3 scripts/check-banned-phrases` | pass |
| `python3 scripts/check-upstream-parity` | pass |
| `uvx pip-audit --strict` | No known vulnerabilities found |
| `.env` gitignored | yes (after `git init`) |

## Upstream pin

`vendor/codebase-memory-mcp` @ `49424722576191a1309d27ec7279c8676d0b1ec2` (short `494247225761`).

Vendor token multipliers remain **ellos reportan** / **según ellos** — not lab measurements.
