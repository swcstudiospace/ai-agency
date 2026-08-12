"""Fraud / risk scoring tools."""

from __future__ import annotations

from typing import Any


def fraud_score_order(
    order_id: str,
    amount_usd: float = 0.0,
    velocity_24h: int = 1,
    geo_mismatch: bool = False,
    new_account: bool = False,
    rush_shipping: bool = False,
    bin_reuse: int = 0,
) -> dict[str, Any]:
    """Heuristic fraud risk score and action."""
    score = 10.0
    signals: list[str] = []
    if amount_usd >= 150:
        score += 15
        signals.append("high_aov")
    if velocity_24h >= 3:
        score += 25
        signals.append("velocity")
    if geo_mismatch:
        score += 20
        signals.append("geo_mismatch")
    if new_account:
        score += 10
        signals.append("new_account")
    if rush_shipping:
        score += 10
        signals.append("rush_ship")
    if bin_reuse >= 2:
        score += 20
        signals.append("bin_reuse")
    score = min(100.0, score)
    if score >= 70:
        action = "HOLD"
    elif score >= 45:
        action = "REVIEW"
    elif score >= 85:
        action = "CANCEL"
    else:
        action = "ALLOW"
    if score >= 90:
        action = "CANCEL"
    return {
        "ok": True,
        "order_id": order_id,
        "risk_score_0_to_100": score,
        "signals": signals,
        "action": action,
        "notes": "Heuristic only — pair with Shopify risk + human for CANCEL.",
    }


def fraud_velocity_check(email_domain: str = "", ip_orders_24h: int = 0, card_orders_24h: int = 0) -> dict[str, Any]:
    """Simple velocity flags."""
    flags = []
    if ip_orders_24h >= 3:
        flags.append("ip_velocity")
    if card_orders_24h >= 3:
        flags.append("card_velocity")
    if email_domain.lower() in {"mailinator.com", "guerrillamail.com", "tempmail.com"}:
        flags.append("disposable_email")
    return {"ok": True, "flags": flags, "elevated": bool(flags)}


def fraud_allowlist_denylist(action: str = "status", value: str = "") -> dict[str, Any]:
    """Stub allow/deny list manager (persist via KIP/Linear in production)."""
    return {
        "ok": True,
        "action": action,
        "value": value,
        "store": "use KIP Commitment/Insight or Linear for durable lists",
        "draft_only": True,
    }


def get_fraud_ops_tools() -> list:
    return [fraud_score_order, fraud_velocity_check, fraud_allowlist_denylist]
