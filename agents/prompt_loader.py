"""Load per-agent markdown persona packs (SOUL / SYSTEM / OUTPUT / EXAMPLES)."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
PROMPTS_ROOT = _ROOT / "prompts"

_SECTION_FILES = (
    ("SOUL.md", "soul"),
    ("SYSTEM.md", "system"),
    ("OUTPUT.md", "output"),
    ("EXAMPLES.md", "examples"),
)


def prompts_dir(persona: str) -> Path:
    return PROMPTS_ROOT / persona


def load_prompt_file(persona: str, filename: str, *, required: bool = True) -> str:
    path = prompts_dir(persona) / filename
    if not path.is_file():
        if required:
            raise FileNotFoundError(f"Missing persona file: {path}")
        return ""
    text = path.read_text(encoding="utf-8").strip()
    if not text and required:
        raise ValueError(f"Empty persona file: {path}")
    return text


def load_persona_sections(persona: str) -> dict[str, str]:
    """Return soul/system/output/examples markdown bodies."""
    out: dict[str, str] = {}
    for filename, key in _SECTION_FILES:
        # EXAMPLES optional for some agents
        required = filename != "EXAMPLES.md"
        out[key] = load_prompt_file(persona, filename, required=required)
    return out


def build_instructions(persona: str, *, extra: Sequence[str] | None = None) -> list[str]:
    """Compose Agent.instructions from SOUL + SYSTEM (+ optional extras)."""
    sections = load_persona_sections(persona)
    blocks: list[str] = []
    if sections.get("soul"):
        blocks.append("# SOUL (identity & non-negotiables)\n\n" + sections["soul"])
    if sections.get("system"):
        blocks.append("# SYSTEM (operating procedure)\n\n" + sections["system"])
    if extra:
        blocks.extend(list(extra))
    return blocks


def build_expected_output(persona: str) -> str | None:
    sections = load_persona_sections(persona)
    text = sections.get("output") or ""
    return text or None


def build_additional_input(persona: str) -> list[str] | None:
    """Few-shot / examples injected after system message."""
    sections = load_persona_sections(persona)
    ex = sections.get("examples") or ""
    if not ex.strip():
        return None
    return ["# EXAMPLES (few-shot — match quality and structure)\n\n" + ex]


def list_personas() -> list[str]:
    if not PROMPTS_ROOT.is_dir():
        return []
    return sorted(
        p.name
        for p in PROMPTS_ROOT.iterdir()
        if p.is_dir() and (p / "SOUL.md").is_file() and (p / "SYSTEM.md").is_file()
    )
