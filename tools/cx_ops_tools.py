"""CX escalation ops tools."""

from __future__ import annotations

from typing import Any


def cx_severity_score(
    public_threat: bool = False,
    influencer: bool = False,
    amount_usd: float = 0.0,
    legal_language: bool = False,
    repeat_contacts: int = 1,
) -> dict[str, Any]:
    """Score escalation severity."""
    score = 20 + min(40, repeat_contacts * 8)
    if amount_usd >= 100:
        score += 10
    if influencer:
        score += 20
    if public_threat:
        score += 25
    if legal_language:
        score += 25
    score = min(100, score)
    if score >= 80:
        sev = "critical"
    elif score >= 55:
        sev = "high"
    elif score >= 30:
        sev = "medium"
    else:
        sev = "low"
    return {"ok": True, "severity": sev, "score_0_to_100": score}


def cx_resolution_options(
    severity: str = "medium",
    order_value_usd: float = 0.0,
    policy_refund_ok: bool = True,
) -> dict[str, Any]:
    """List resolution options with HITL flags."""
    opts: list[dict[str, Any]] = [
        {"option": "proactive_tracking_update", "hitl": False, "cm_impact": "low"},
        {"option": "partial_goodwill_credit", "hitl": order_value_usd > 25, "cm_impact": "medium"},
        {"option": "full_refund", "hitl": not policy_refund_ok or order_value_usd > 50, "cm_impact": "high"},
        {"option": "replacement_ship", "hitl": order_value_usd > 40, "cm_impact": "medium"},
    ]
    if severity in {"high", "critical"}:
        opts.append({"option": "executive_apology_call_script", "hitl": True, "cm_impact": "low"})
    return {"ok": True, "severity": severity, "options": opts}


def cx_draft_reply(
    customer_name: str = "there",
    situation: str = "",
    resolution: str = "",
) -> dict[str, Any]:
    """Draft empathetic escalation reply (human sends)."""
    body = (
        f"Hi {customer_name},\n\n"
        f"Thank you for your patience — I'm personally looking into this"
        f"{': ' + situation if situation else ''}.\n\n"
        f"{resolution or 'Here is what I can do next:'}\n\n"
        f"I'll update you as soon as the next step completes.\n\n"
        f"Best regards,\nCustomer Experience"
    )
    return {"ok": True, "draft_only": True, "body": body}


def get_cx_ops_tools() -> list:
    return [cx_severity_score, cx_resolution_options, cx_draft_reply]
