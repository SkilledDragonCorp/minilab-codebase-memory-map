# Security Policy

**Built by [SkilledDragon LLC](https://skilleddragon.com)**

This is a **SkilledDragon educational minilab**, not a production product. We do **not** maintain these repos on a regular schedule and we do **not** operate a vulnerability response program for them.

## Contact

General questions: **hello@skilleddragon.com**  
Do not use a dedicated security mailbox for this repo — none exists.

## If you find an issue

- Prefer reporting **upstream** when the issue is in [DeusData/codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp).
- For something specific to this minilab's scripts or CI, you may email hello@skilleddragon.com. There is **no SLA**, and we may not patch or reply quickly.

## Supported versions

Only the commit currently on `main` is considered current for this educational lab.

## Secret handling

- Never commit `.env`, API keys, or tokens.
- No API keys are required for the keyless source build + smoke path.
- Set `DISABLE_TELEMETRY=1` and `DO_NOT_TRACK=1` for lab runs.
- Keep the codebase map local; do not upload repository contents to third parties.

## Antivirus note (neutral)

Upstream documents that some **release** binaries may be reported by Microsoft Defender as `Trojan:Script/Wacatac.*!ml`, which they describe as a false positive. See upstream [SECURITY.md](https://github.com/DeusData/codebase-memory-mcp/blob/49424722576191a1309d27ec7279c8676d0b1ec2/SECURITY.md) (Antivirus False Positives). This lab does **not** use the release-binary or `curl` `install.sh` path; it builds from source at the pin. When you verify third-party artifacts outside this lab, use upstream checksum / Sigstore / SLSA guidance from that SECURITY page.

## Tooling pins

| Control | Pin |
| --- | --- |
| Upstream | `DeusData/codebase-memory-mcp` @ `49424722576191a1309d27ec7279c8676d0b1ec2` (short `494247225761`, MIT) |
| gitleaks | `v8.30.1` (pre-commit hook + CI binary with SHA256 verify) |
| Dependency audit | `uv export --frozen --format requirements-txt --no-emit-project > /tmp/req.txt` then `uvx pip-audit --strict -r /tmp/req.txt` |

## Upstream license

`DeusData/codebase-memory-mcp` is MIT. Use at your own risk. Pin versions, review the code, and treat this as sample material.
