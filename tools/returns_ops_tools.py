"""Returns / RMA ops tools — policy checks, cost estimates, RMA drafts."""

from __future__ import annotations

import uuid
from typing import Any, Dict, Optional


def returns_policy_check(
    days_since_delivery: int = 0,
    reason_code: str = "unknown",
    opened: bool = True,
    has_photos: bool = False,
    window_days: int = 30,
) -> Dict[str, Any]:
    """Evaluate RMA eligibility against default policy (override per brand later)."""
    in_window = days_since_delivery <= window_days
    eligible = in_window
    notes = []
    if not in_window:
        notes.append("Outside return window")
        eligible = False
    if reason_code in {"changed_mind"} and opened and days_since_delivery > 14:
        notes.append("Changed-mind late/opened — partial or deny per policy")
    if reason_code in {"defect", "wrong_item"} and not has_photos:
        notes.append("Request photos before final disposition")
    disposition_hint = "refund" if eligible and reason_code in {"defect", "wrong_item"} else (
        "exchange" if eligible else "deny"
    )
    if not has_photos and reason_code == "defect":
        disposition_hint = "request_evidence"
    return {
        "ok": True,
        "eligible": eligible,
        "in_window": in_window,
        "disposition_hint": disposition_hint,
        "notes": notes,
        "window_days": window_days,
    }


def returns_cost_estimate(
    item_cogs_usd: float = 0.0,
    reverse_ship_usd: float = 8.0,
    restockable: bool = False,
    refund_usd: float = 0.0,
) -> Dict[str, Any]:
    """Estimate CM impact of a return path."""
    recovered = float(item_cogs_usd) if restockable else 0.0
    cost = float(refund_usd) + float(reverse_ship_usd) - recovered
    return {
        "ok": True,
        "refund_usd": float(refund_usd),
        "reverse_ship_usd": float(reverse_ship_usd),
        "cogs_recovered_usd": recovered,
        "net_cost_usd": round(cost, 2),
        "restockable": restockable,
    }


def returns_draft_rma(
    order_id: str,
    disposition: str,
    reason_code: str = "",
    customer_message: str = "",
) -> Dict[str, Any]:
    """Create an internal RMA draft record (Shopify execution is HITL/API when configured)."""
    rid = f"rma_{uuid.uuid4().hex[:10]}"
    msg = customer_message or (
        f"We've opened RMA {rid} for order {order_id}. Disposition: {disposition}. "
        "Reply to this email if you need help with the next step."
    )
    return {
        "ok": True,
        "rma_id": rid,
        "order_id": order_id,
        "disposition": disposition,
        "reason_code": reason_code,
        "customer_message": msg,
        "draft_only": True,
        "next": "Human/Shopify integration confirms refund/label; dual-write Linear.",
    }


def get_returns_ops_tools() -> list:
    return [returns_policy_check, returns_cost_estimate, returns_draft_rma]
