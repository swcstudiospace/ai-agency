"""Agent factory — markdown personas, scoped skills, toolbelts, schemas, memory."""

from __future__ import annotations

import os
from collections.abc import Sequence
from typing import Any

from agno.agent import Agent
from pydantic import BaseModel
from tools.guardrails import default_tool_hooks
from tools.skills_loader import skills_for
from tools.toolbelts import resolve_toolbelt
from tools.xai_model import get_grok_model

from agents.prompt_loader import (
    build_additional_input,
    build_expected_output,
    build_instructions,
)


def build_agent(
    *,
    name: str,
    role: str,
    persona: str,
    toolbelts: Sequence[str] | None = None,
    skill_names: Sequence[str] | None = None,
    extra_tools: list[Any] | None = None,
    output_schema: type[BaseModel] | dict | None = None,
    model_id: str = "grok-4.5",
    temperature: float = 0.3,
    markdown: bool = True,
    add_history_to_context: bool = False,
    num_history_runs: int | None = None,
    add_datetime_to_context: bool = True,
    use_json_mode: bool = False,
    tool_hooks: list[Any] | None = None,
    extra_instructions: Sequence[str] | None = None,
    id: str | None = None,
) -> Agent:
    """Compose an Agent from persona markdown + scoped skills + toolbelts."""
    tools: list[Any] = []
    belts = list(toolbelts or [])
    # Always attach Hermes reverse bridge (browser/skills/KIP) unless explicitly disabled
    if "hermes_bridge" not in belts and os.getenv("AGENCY_DISABLE_HERMES_BRIDGE", "").lower() not in {
        "1",
        "true",
        "yes",
    }:
        belts.append("hermes_bridge")
    # Grok Build bottom CLI layer — all agents can offload shell + coding agents
    if "grok_build" not in belts and os.getenv("AGENCY_DISABLE_GROK_BUILD", "").lower() not in {
        "1",
        "true",
        "yes",
    }:
        belts.append("grok_build")
    # CodeRabbit review tools (optional belt — always on unless disabled)
    if "coderabbit" not in belts and os.getenv("AGENCY_DISABLE_CODERABBIT", "").lower() not in {
        "1",
        "true",
        "yes",
    }:
        belts.append("coderabbit")
    # Anda Brain formation/recall/sleep + docs grep
    if "anda_brain" not in belts and os.getenv("AGENCY_DISABLE_ANDA_BRAIN", "").lower() not in {
        "1",
        "true",
        "yes",
    }:
        belts.append("anda_brain")
    # Ops analytics (SKU/ads metrics) — not brain memory
    if "analytics" not in belts and os.getenv("AGENCY_DISABLE_ANALYTICS", "").lower() not in {
        "1",
        "true",
        "yes",
    }:
        belts.append("analytics")
    if belts:
        tools.extend(resolve_toolbelt(belts))
    if extra_tools:
        tools.extend(extra_tools)

    # Grok Build offload guidance injected into every agent
    gb_extra: list[str] = []
    try:
        from tools.grok_build_tools import GROK_BUILD_OFFLOAD_INSTRUCTIONS

        if "grok_build" in belts:
            gb_extra.append(GROK_BUILD_OFFLOAD_INSTRUCTIONS)
    except Exception:
        pass
    merged_extra = list(extra_instructions or []) + gb_extra
    instructions = build_instructions(persona, extra=merged_extra or None)
    expected_output = build_expected_output(persona)
    additional_input = build_additional_input(persona)

    hooks = tool_hooks if tool_hooks is not None else default_tool_hooks()

    kwargs: dict = {
        "name": name,
        "role": role,
        "model": get_grok_model(model_id or None, temperature=temperature),
        "tools": tools or None,
        "instructions": instructions,
        "markdown": markdown,
        "add_datetime_to_context": add_datetime_to_context,
        "add_history_to_context": add_history_to_context,
        "tool_hooks": hooks or None,
    }
    if id:
        kwargs["id"] = id
    if expected_output:
        kwargs["expected_output"] = expected_output
    if additional_input:
        kwargs["additional_input"] = additional_input
    if output_schema is not None:
        kwargs["output_schema"] = output_schema
        kwargs["use_json_mode"] = use_json_mode
    if num_history_runs is not None:
        kwargs["num_history_runs"] = num_history_runs
    if skill_names is not None:
        sk = skills_for(*list(skill_names))
        if sk is not None:
            kwargs["skills"] = sk

    # Shared Anda/KIP documentation knowledge (FileSystemKnowledge)
    if os.getenv("AGENCY_DISABLE_ANDA_KNOWLEDGE", "").lower() not in {"1", "true", "yes"}:
        try:
            from tools.anda_knowledge import get_anda_filesystem_knowledge

            fs_k = get_anda_filesystem_knowledge()
            if fs_k is not None:
                kwargs["knowledge"] = fs_k
                kwargs["search_knowledge"] = True
        except Exception:
            pass

    return Agent(**kwargs)
