"""Community / reputation ops tools."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def community_sentiment_digest(
    positive: int = 0,
    neutral: int = 0,
    negative: int = 0,
    themes: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Summarize sentiment counts into ops digest."""
    total = max(1, positive + neutral + negative)
    return {
        "ok": True,
        "sentiment": {
            "positive_pct": round(100 * positive / total, 1),
            "neutral_pct": round(100 * neutral / total, 1),
            "negative_pct": round(100 * negative / total, 1),
        },
        "themes": themes or [],
        "label": "negative" if negative > positive else ("mixed" if negative else "positive"),
    }


def community_ugc_intake(
    creator: str,
    asset_url: str = "",
    permission: bool = False,
    channel: str = "instagram",
) -> Dict[str, Any]:
    """Log UGC candidate for Creative Ops."""
    return {
        "ok": True,
        "creator": creator,
        "channel": channel,
        "asset_url": asset_url,
        "permission_secured": permission,
        "next": "Request written permission if missing; hand to Ads Creative Ops",
    }


def community_crisis_flag(
    summary: str,
    virality_0_to_1: float = 0.3,
    legal_risk: bool = False,
) -> Dict[str, Any]:
    """Flag reputation crises for Hermes/CX."""
    severity = "low"
    if legal_risk or virality_0_to_1 >= 0.7:
        severity = "critical"
    elif virality_0_to_1 >= 0.4:
        severity = "high"
    elif virality_0_to_1 >= 0.2:
        severity = "medium"
    return {
        "ok": True,
        "severity": severity,
        "summary": summary,
        "route_to": ["cx_escalations", "hermes_ops", "community_manager"],
        "do_not": ["delete_legitimate_criticism", "fake_reviews"],
    }


def get_community_ops_tools() -> list:
    return [community_sentiment_digest, community_ugc_intake, community_crisis_flag]
