"""Workflow helpers — encourage Warp bottom-layer offload in every pipeline step."""

from __future__ import annotations

from typing import Any

WARP_WORKFLOW_PREAMBLE = (
    "[Warp bottom layer] For multi-step shell, coding, or long terminal work, "
    "agents MUST prefer warp_agent_run / warp_orchestrate_agency_task / warp_offload_shell "
    "over inventing loops. Stack: Hermes → Agno workflow → Warp Oz CLI."
)


def with_warp_guidance(description: str) -> str:
    """Append Warp offload guidance to a workflow step description."""
    d = (description or "").strip()
    if "warp_" in d.lower() or "Warp bottom" in d:
        return d
    return f"{d}\n\n{WARP_WORKFLOW_PREAMBLE}"


def warp_step_note() -> dict[str, Any]:
    return {
        "layer": "warp",
        "preference": "offload multi-step execution to oz agent run",
        "tools": [
            "warp_status",
            "warp_agent_run",
            "warp_agent_run_cloud",
            "warp_offload_shell",
            "warp_orchestrate_agency_task",
        ],
    }
