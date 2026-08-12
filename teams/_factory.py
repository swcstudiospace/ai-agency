"""Team builders with scoped skills and markdown instructions."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from agno.agent import Agent
from agno.team import Team
from agno.team.mode import TeamMode
from tools.skills_loader import skills_for
from tools.xai_model import get_grok_model

_ROOT = Path(__file__).resolve().parents[1]
_TEAM_PROMPTS = _ROOT / "prompts" / "teams"


def _team_instructions(key: str, fallback: Sequence[str]) -> list[str]:
    path = _TEAM_PROMPTS / key / "SYSTEM.md"
    if path.is_file():
        return [path.read_text(encoding="utf-8").strip()]
    return list(fallback)


def build_team(
    *,
    key: str,
    name: str,
    members: list[Agent],
    skill_names: Sequence[str],
    fallback_instructions: Sequence[str],
    model_id: str = "grok-4.5",
    temperature: float = 0.3,
) -> Team:
    return Team(
        name=name,
        mode=TeamMode.coordinate,
        model=get_grok_model(model_id, temperature=temperature),
        members=members,
        skills=skills_for(*skill_names),
        instructions=_team_instructions(key, fallback_instructions),
        markdown=True,
        add_datetime_to_context=True,
    )
