---
name: codebase-memory-map
description: Index a repo into a local DeusData/codebase-memory-mcp knowledge graph before long-horizon Argon work; hedge vendor token claims; local-only map.
---

# Codebase memory map (local)

Build and use [DeusData/codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp) from **source at the lab pin** so agents can query a local knowledge graph instead of re-walking the tree on every turn.

## Claim discipline (required)

Vendor marketing numbers (10× / 99% / 120× token savings and similar) are **ellos reportan** / **según ellos**. This lab only reports its own measured fixture numbers. Never paste vendor percentages as lab results.

## Privacy / telemetry

```bash
export DISABLE_TELEMETRY=1
export DO_NOT_TRACK=1
```

Upstream documents local indexing and graph queries with no source upload for those paths. Keep the map on the machine; do not pipe repo contents to third parties.

## Source build only

Do **not** use release binaries or `curl … install.sh` for this lab. Clone the pin and build:

```bash
bash scripts/vendor-upstream.sh
bash scripts/upstream-cbm.sh
```

Pin: `49424722576191a1309d27ec7279c8676d0b1ec2` (short `494247225761`).

Upstream `.github/workflows/smoke.yml` is **opt-in / non-gating** (`workflow_dispatch` + push to `qa/smoke-**` only). This lab still copies that verified smoke-unix path.

## Before long-horizon Argon / Gemini work

1. Ensure the binary exists at `vendor/codebase-memory-mcp/build/c/codebase-memory-mcp`.
2. Index the working tree (or the lab fixture) locally:

```bash
uv run cbm-map tests/fixtures/tiny-repo --json
```

3. Prefer graph queries (`search_graph`, `query_graph`, `trace_path`) over blind recursive file reads for structural questions.
4. Re-index after large refactors (`cli index_repository --repo-path <abs>`).

## Antivirus note (neutral)

Some upstream **release** artifacts have been labeled by Microsoft Defender as `Trojan:Script/Wacatac.*!ml`. Upstream treats that as a false positive and documents verification in their [SECURITY.md](https://github.com/DeusData/codebase-memory-mcp/blob/49424722576191a1309d27ec7279c8676d0b1ec2/SECURITY.md). This lab builds from source at the pin and recommends checksum / provenance verify when using any third-party binary outside the lab path.
