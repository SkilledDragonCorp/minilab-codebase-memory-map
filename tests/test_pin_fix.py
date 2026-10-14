"""apply-smoke-invariants-pin-fix patches vendor smoke script at the pin."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_apply_pin_fix_on_pristine_vendor() -> None:
    vendor = ROOT / "vendor" / "codebase-memory-mcp"
    if not (vendor / ".git").is_dir():
        subprocess.run(["bash", str(ROOT / "scripts" / "vendor-upstream.sh")], check=True, cwd=ROOT)
    # Reset script to pin, then patch
    subprocess.run(
        ["git", "-C", str(vendor), "checkout", "--", "scripts/smoke-invariants.sh"],
        check=True,
    )
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "apply-smoke-invariants-pin-fix.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    text = (vendor / "scripts" / "smoke-invariants.sh").read_text(encoding="utf-8")
    assert "--quiet --json index_status --project" in text
    assert "inv_crasher_skipped_cli" not in text
    assert "OMITTED at this pin" in text
