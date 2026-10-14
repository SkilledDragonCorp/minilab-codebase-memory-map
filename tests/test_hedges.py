"""Vendor token claims must stay hedged; README notes smoke.yml opt-in."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

HEDGE_MARKERS = ("según ellos", "ellos reportan")


def test_skill_or_readme_hedges_vendor_claims() -> None:
    skill = (ROOT / ".claude" / "skills" / "codebase-memory-map" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    blob = f"{skill}\n{readme}".lower()
    assert any(marker in blob for marker in HEDGE_MARKERS), (
        "expected 'según ellos' or 'ellos reportan' in skill or README"
    )


def test_readme_notes_smoke_yml_opt_in() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8").lower()
    assert "smoke.yml" in readme
    assert "opt-in" in readme or "non-gating" in readme


def test_no_unhedged_vendor_multipliers_as_lab_fact() -> None:
    """Bare '120x' / '10×' / '99%' as lab facts are forbidden outside hedge context."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    # Allow lines that mention vendor claims only when hedge language is nearby.
    for line in readme.splitlines():
        lower = line.lower()
        looks_vendor = any(
            token in lower for token in ("120x", "120×", "10×", "10x", "99%", "99.2%")
        )
        if not looks_vendor:
            continue
        hedged = any(marker in lower for marker in HEDGE_MARKERS) or "vendor" in lower
        assert hedged, f"unhedged vendor claim line: {line}"
