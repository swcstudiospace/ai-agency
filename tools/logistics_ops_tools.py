"""Logistics exception ops tools (on top of core logistics_tools)."""

from __future__ import annotations

from typing import Any, Dict, List


def logistics_exception_triage(
    exception_type: str,
    days_since_ship: int = 0,
    carrier: str = "",
) -> Dict[str, Any]:
    """Triage shipping exception and recommend recovery ladder step."""
    et = (exception_type or "unknown").lower()
    actions: List[str] = []
    if "no_scan" in et or "noscan" in et or et == "no-scan":
        actions = ["carrier_inquiry", "proactive_cs", "day12_replace_rule"]
        urgency = "high" if days_since_ship >= 7 else "medium"
    elif "lost" in et:
        actions = ["fraud_check", "replace_or_refund", "supplier_pack_audit"]
        urgency = "high"
    elif "customs" in et:
        actions = ["docs_check", "honest_eta", "cs_update"]
        urgency = "medium"
    elif "delay" in et:
        actions = ["eta_revision", "cs_update"]
        urgency = "medium" if days_since_ship >= 5 else "low"
    else:
        actions = ["investigate", "cs_update"]
        urgency = "medium"
    return {
        "ok": True,
        "exception_type": exception_type,
        "carrier": carrier,
        "days_since_ship": days_since_ship,
        "urgency": urgency,
        "recovery_actions": actions,
    }


def logistics_recovery_plan(
    tracking: str,
    exception_type: str,
    customer_facing: bool = True,
) -> Dict[str, Any]:
    """Draft recovery plan + optional customer blurb."""
    blurb = ""
    if customer_facing:
        blurb = (
            f"We're actively working with the carrier on package {tracking or '(pending)'} "
            f"({exception_type}). We'll share a revised ETA as soon as we have a scan update."
        )
    return {
        "ok": True,
        "tracking": tracking,
        "exception_type": exception_type,
        "steps": [
            "Confirm last mile carrier event",
            "Open carrier investigation if eligible",
            "Update customer with honest ETA band",
            "Schedule replacement decision checkpoint",
            "Linear dual-write + analytics exception metric",
        ],
        "customer_comms": blurb,
        "never": "Do not invent tracking scans",
    }


def get_logistics_ops_tools() -> list:
    return [logistics_exception_triage, logistics_recovery_plan]
