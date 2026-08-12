"""Workflow helpers — encourage Grok Build bottom-layer offload in every pipeline step."""

from __future__ import annotations

from typing import Any

GROK_BUILD_WORKFLOW_PREAMBLE = (
    "[Grok Build bottom layer] For multi-step shell, coding, or long terminal work, "
    "agents MUST prefer grok_build_run / grok_build_orchestrate_agency_task / "
    "grok_build_offload_shell over inventing loops. "
    "Stack: Hermes → Agno workflow → Grok Build (SuperGrok)."
)


def with_grok_build_guidance(description: str) -> str:
    """Append Grok Build offload guidance to a workflow step description."""
    d = (description or "").strip()
    if "grok_build" in d.lower() or "Grok Build bottom" in d:
        return d
    return f"{d}\n\n{GROK_BUILD_WORKFLOW_PREAMBLE}"


# Back-compat alias if anything still imports old name during transition
with_warp_guidance = with_grok_build_guidance


def grok_build_step_note() -> dict[str, Any]:
    return {
        "layer": "grok_build",
        "preference": "offload multi-step execution to grok -p headless",
        "tools": [
            "grok_build_status",
            "grok_build_run",
            "grok_build_offload_shell",
            "grok_build_orchestrate_agency_task",
            "grok_build_inspect",
        ],
    }
