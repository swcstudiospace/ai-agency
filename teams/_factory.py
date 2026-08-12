"""Team builders with scoped skills, markdown instructions, and Warp bottom layer."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

from agno.agent import Agent
from agno.team import Team
from agno.team.mode import TeamMode
from tools.skills_loader import skills_for
from tools.xai_model import get_grok_model

_ROOT = Path(__file__).resolve().parents[1]
_TEAM_PROMPTS = _ROOT / "prompts" / "teams"

_WARP_TEAM_BLURB = """
## Warp bottom layer (teams)
Coordinate members so multi-step shell/coding work is **offloaded to Warp Oz** via
`warp_agent_run` / `warp_orchestrate_agency_task` / `warp_offload_shell`.
Stack: Hermes → Agno team → Warp CLI. Do not reinvent orchestration loops.
""".strip()


def _team_instructions(key: str, fallback: Sequence[str]) -> list[str]:
    path = _TEAM_PROMPTS / key / "SYSTEM.md"
    if path.is_file():
        base = [path.read_text(encoding="utf-8").strip()]
    else:
        base = list(fallback)
    base.append(_WARP_TEAM_BLURB)
    return base


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
    tools: list[Any] | None = None
    try:
        from tools.toolbelts import resolve_toolbelt

        tools = resolve_toolbelt(["warp", "coderabbit", "linear"])
    except Exception:
        tools = None

    return Team(
        name=name,
        mode=TeamMode.coordinate,
        model=get_grok_model(model_id, temperature=temperature),
        members=members,
        skills=skills_for(*skill_names),
        instructions=_team_instructions(key, fallback_instructions),
        tools=tools,
        markdown=True,
        add_datetime_to_context=True,
    )
