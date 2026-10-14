"""Skills live only under .claude/skills/<name>/SKILL.md."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_no_skill_mirrors() -> None:
    assert not (ROOT / ".cursor" / "skills").exists()
    assert not (ROOT / ".agents" / "skills").exists()


def test_canonical_skill_exists() -> None:
    skill = ROOT / ".claude" / "skills" / "codebase-memory-map" / "SKILL.md"
    assert skill.is_file()
    text = skill.read_text(encoding="utf-8")
    assert text.startswith("---")
    assert "name: codebase-memory-map" in text
