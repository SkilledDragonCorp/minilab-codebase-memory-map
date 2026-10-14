#!/usr/bin/env bash
# Run scripts/upstream-cbm.sh inside Ubuntu (CI-like), then map the tiny fixture.
# Prefer this on macOS hosts when Docker Desktop is available — avoids native
# x86_64 clang OOM/SIGTERM on the heavy prod_lsp_all.o unity compile.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE="${CBM_DOCKER_IMAGE:-ubuntu:24.04}"

export DISABLE_TELEMETRY=1
export DO_NOT_TRACK=1

if [[ -x /usr/local/Cellar/git/2.39.0/bin/git ]]; then
  export PATH="/usr/local/Cellar/git/2.39.0/bin:$PATH"
elif [[ -x /usr/local/opt/git/bin/git ]]; then
  export PATH="/usr/local/opt/git/bin:$PATH"
elif [[ -x /opt/homebrew/opt/git/bin/git ]]; then
  export PATH="/opt/homebrew/opt/git/bin:$PATH"
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "docker not found; install Docker Desktop or run bash scripts/upstream-cbm.sh on Linux" >&2
  exit 1
fi

for i in $(seq 1 60); do
  if docker info >/dev/null 2>&1; then
    break
  fi
  if [[ "$i" -eq 60 ]]; then
    echo "docker daemon not ready (docker info failed)" >&2
    exit 1
  fi
  sleep 5
done

# Ensure vendor pin exists on the host mount before the container build.
bash "$ROOT/scripts/vendor-upstream.sh"

# Clean a partial native Darwin object tree so the Linux build is not confused.
rm -rf "$ROOT/vendor/codebase-memory-mcp/build/c"

docker pull "$IMAGE"

docker run --rm \
  -e DISABLE_TELEMETRY=1 \
  -e DO_NOT_TRACK=1 \
  -e CBM_IN_DOCKER=1 \
  -e DEBIAN_FRONTEND=noninteractive \
  -v "$ROOT:/work" \
  -w /work \
  "$IMAGE" \
  bash -lc '
set -euo pipefail
apt-get update
apt-get install -y --no-install-recommends \
  sudo ca-certificates curl git gcc g++ make zlib1g-dev python3 python3-venv
# uv for fixture map after smoke
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
bash scripts/upstream-cbm.sh
uv sync --locked --group dev
uv run pytest -q tests/test_map_fixture.py
uv run cbm-map tests/fixtures/tiny-repo --json | tee /work/reports/fixture-map.json
echo "upstream-cbm-docker.sh OK"
'

echo "upstream-cbm-docker.sh host OK"
