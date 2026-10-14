#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PIN="49424722576191a1309d27ec7279c8676d0b1ec2"
DEST="$ROOT/vendor/codebase-memory-mcp"

if [[ -x /usr/local/Cellar/git/2.39.0/bin/git ]]; then
  export PATH="/usr/local/Cellar/git/2.39.0/bin:$PATH"
elif [[ -x /usr/local/opt/git/bin/git ]]; then
  export PATH="/usr/local/opt/git/bin:$PATH"
elif [[ -x /opt/homebrew/opt/git/bin/git ]]; then
  export PATH="/opt/homebrew/opt/git/bin:$PATH"
fi

mkdir -p "$ROOT/vendor"

if [[ -d "$DEST/.git" ]]; then
  git -C "$DEST" fetch --depth 1 origin "$PIN" || git -C "$DEST" fetch origin "$PIN"
  git -C "$DEST" checkout --force "$PIN"
else
  rm -rf "$DEST"
  git clone https://github.com/DeusData/codebase-memory-mcp.git "$DEST"
  git -C "$DEST" checkout "$PIN"
fi

HEAD="$(git -C "$DEST" rev-parse HEAD)"
if [[ "$HEAD" != "$PIN" ]]; then
  echo "vendor pin mismatch: expected $PIN got $HEAD" >&2
  exit 1
fi

echo "vendor/codebase-memory-mcp @ $HEAD"
