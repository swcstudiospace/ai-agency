"""Chargeback / dispute ops tools — evidence packs, win scoring, prevention."""

from __future__ import annotations

import uuid
from typing import Any


def chargeback_evidence_pack(
    order_id: str,
    tracking: str = "",
    delivered: bool = False,
    avs_match: bool = False,
    cvv_match: bool = False,
    customer_emails: int = 0,
    descriptor_clear: bool = True,
) -> dict[str, Any]:
    """Assemble representment evidence checklist status."""
    items = {
        "order_invoice": True,
        "tracking": bool(tracking),
        "delivery_proof": delivered,
        "avs_match": avs_match,
        "cvv_match": cvv_match,
        "customer_contact_log": customer_emails > 0,
        "billing_descriptor_clear": descriptor_clear,
        "product_description_match": True,
    }
    missing = [k for k, v in items.items() if not v]
    return {
        "ok": True,
        "case_draft_id": f"cb_{uuid.uuid4().hex[:10]}",
        "order_id": order_id,
        "evidence": items,
        "missing": missing,
        "strength": "strong" if len(missing) <= 1 else ("medium" if len(missing) <= 3 else "weak"),
    }


def chargeback_win_score(
    reason: str = "fraud",
    delivered: bool = False,
    avs_match: bool = False,
    amount_usd: float = 0.0,
    evidence_missing: int = 0,
) -> dict[str, Any]:
    """Heuristic win probability and FIGHT|ACCEPT|PARTIAL recommendation."""
    score = 0.35
    r = (reason or "").lower()
    if delivered:
        score += 0.25
    if avs_match:
        score += 0.1
    if "fraud" in r and delivered:
        score += 0.15
    if "not_received" in r and not delivered:
        score -= 0.2
    score -= 0.05 * max(0, evidence_missing)
    score = max(0.05, min(0.95, score))
    if score >= 0.55 and amount_usd >= 25:
        rec = "FIGHT"
    elif score < 0.35 or amount_usd < 15:
        rec = "ACCEPT"
    else:
        rec = "PARTIAL"
    return {
        "ok": True,
        "win_probability_0_to_1": round(score, 2),
        "recommend": rec,
        "reason": reason,
        "amount_usd": float(amount_usd),
    }


def chargeback_prevention_checklist(channel: str = "dtc") -> dict[str, Any]:
    """Prevention actions to reduce future chargebacks."""
    return {
        "ok": True,
        "channel": channel,
        "actions": [
            "Clear billing descriptor matching brand site",
            "Honest shipping ETAs on PDP + confirmation email",
            "Tracking uploaded within 24h of ship",
            "Post-purchase 'what's next' email with support link",
            "AVS/CVV enforced at checkout",
            "High-risk order review queue (Risk Fraud Analyst)",
        ],
    }


def get_chargeback_ops_tools() -> list:
    return [chargeback_evidence_pack, chargeback_win_score, chargeback_prevention_checklist]
