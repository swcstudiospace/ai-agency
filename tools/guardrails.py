"""Autonomy / safety tool hooks for L2 agency defaults."""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any

# Hard blocks at L2 — true irreversible money movement without dedicated HITL tools.
_BLOCKED_EXACT = {
    "place_order",
    "charge_card",
    "wire_transfer",
    "delete_store",
    "publish_product",
    "confirm_spend_approval",  # humans only — agents must not self-confirm
}

# Soft: these require approval_id + spend_token args (HITL path)
_HITL_LAUNCH = {
    "meta_launch_campaign",
    "tiktok_launch_campaign",
}


def _tool_name(fn: Any) -> str:
    return (
        getattr(fn, "__name__", None)
        or getattr(fn, "name", None)
        or getattr(getattr(fn, "entrypoint", None), "__name__", None)
        or ""
    ).lower()


def autonomy_tool_hook(
    function_name: str = "",
    function: Any = None,
    arguments: dict[str, Any] | None = None,
    **kwargs: Any,
) -> dict[str, Any] | None:
    """L2 defaults: drafts OK; live spend only via spend_vault tokens; no self-confirm."""
    level = (os.getenv("AGENCY_AUTONOMY", "L2") or "L2").upper().strip()
    name = (function_name or _tool_name(function) or "").lower()
    args = arguments or kwargs.get("args") or {}

    # Agents must never confirm their own spend codes
    if name == "confirm_spend_approval" and level not in {"L4"}:
        return {
            "error": (
                "confirm_spend_approval is human-only. "
                "Surface approval_id + human_confirm_code to the operator."
            ),
            "blocked_by": "autonomy_tool_hook",
            "autonomy": level,
        }

    # Soft guard: draft-only shopify unless L3+
    if name in {"draft_product", "update_product"}:
        status = str(args.get("status", "draft")).lower()
        if status == "active" and level not in {"L3", "L4"}:
            return {
                "error": "Blocked publish: autonomy L2 requires status=draft.",
                "blocked_by": "autonomy_tool_hook",
                "autonomy": level,
            }

    if name in _BLOCKED_EXACT and level not in {"L3", "L4"}:
        return {
            "error": f"Blocked tool '{name}' under autonomy {level}.",
            "blocked_by": "autonomy_tool_hook",
            "autonomy": level,
        }

    # Launch tools: must carry approval credentials (vault still verifies)
    if name in _HITL_LAUNCH:
        if not args.get("approval_id") or not args.get("spend_token"):
            return {
                "error": (
                    "Ad launch requires HITL: request_spend_approval → human "
                    "confirm_spend_approval → pass approval_id + spend_token."
                ),
                "blocked_by": "autonomy_tool_hook",
                "autonomy": level,
            }

    return None


def default_tool_hooks() -> list[Callable[..., Any]]:
    return [autonomy_tool_hook]
