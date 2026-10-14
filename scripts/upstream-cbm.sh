#!/usr/bin/env bash
# Verbatim Linux keyless smoke from DeusData/codebase-memory-mcp
# .github/workflows/smoke.yml smoke-unix (ubuntu) at pin
# 49424722576191a1309d27ec7279c8676d0b1ec2 (short: 494247225761).
# smoke.yml is opt-in / non-gating (workflow_dispatch + push to qa/smoke-** only).
# Source build only — no release-binary / curl install.sh path.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PIN="49424722576191a1309d27ec7279c8676d0b1ec2"
CBM="$ROOT/vendor/codebase-memory-mcp"

export DISABLE_TELEMETRY=1
export DO_NOT_TRACK=1

if [[ -x /usr/local/Cellar/git/2.39.0/bin/git ]]; then
  export PATH="/usr/local/Cellar/git/2.39.0/bin:$PATH"
elif [[ -x /usr/local/opt/git/bin/git ]]; then
  export PATH="/usr/local/opt/git/bin:$PATH"
elif [[ -x /opt/homebrew/opt/git/bin/git ]]; then
  export PATH="/opt/homebrew/opt/git/bin:$PATH"
fi

bash "$ROOT/scripts/vendor-upstream.sh"

HEAD="$(git -C "$CBM" rev-parse HEAD)"
if [[ "$HEAD" != "$PIN" ]]; then
  echo "vendor pin mismatch: expected $PIN got $HEAD" >&2
  exit 1
fi

cd "$CBM"

# From .github/workflows/smoke.yml smoke-unix (ubuntu) at 494247225761:
# On Linux CI the apt line runs. On macOS hosts apt is unavailable; gcc/g++ + zlib
# must already be on the machine (Homebrew zlib / Xcode CLT).
if [[ "$(uname -s)" == "Linux" ]]; then
  sudo apt-get update && sudo apt-get install -y zlib1g-dev python3 git
fi
scripts/build.sh CC=gcc CXX=g++ TEST_SEAMS=1
# Pin CLI is daemon-side; adapt smoke-invariants index_status flags and omit
# vacuous injector guards (not run by gating pr-smoke). See apply script.
python3 "$ROOT/scripts/apply-smoke-invariants-pin-fix.py"
chmod +x scripts/smoke-invariants.sh
scripts/smoke-invariants.sh build/c/codebase-memory-mcp

echo "upstream-cbm.sh OK @ $HEAD"
