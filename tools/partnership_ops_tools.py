"""Partnership / affiliate ops tools."""

from __future__ import annotations

from typing import Any


def partnership_score_fit(
    name: str,
    audience_size: int = 0,
    niche_overlap_0_to_1: float = 0.5,
    brand_safety_0_to_1: float = 0.8,
) -> dict[str, Any]:
    """Score partner fit."""
    reach = min(1.0, audience_size / 100_000) if audience_size else 0.3
    score = 100 * (0.4 * niche_overlap_0_to_1 + 0.4 * brand_safety_0_to_1 + 0.2 * reach)
    return {
        "ok": True,
        "name": name,
        "fit_score_0_to_100": round(score, 1),
        "tier": "priority" if score >= 70 else ("nurture" if score >= 45 else "pass"),
    }


def partnership_revshare_model(
    aov_usd: float,
    cogs_ship_usd: float,
    revshare_pct: float = 0.15,
    expected_cvr: float = 0.02,
) -> dict[str, Any]:
    """Model contribution after affiliate revshare on AOV."""
    revshare = aov_usd * revshare_pct
    cm = aov_usd - cogs_ship_usd - revshare
    return {
        "ok": True,
        "aov_usd": aov_usd,
        "revshare_pct": revshare_pct,
        "revshare_usd": round(revshare, 2),
        "cm_after_revshare_usd": round(cm, 2),
        "cm_positive": cm > 0,
        "note": f"At CVR={expected_cvr}, ensure partner CAC still clears targets.",
    }


def partnership_outreach_sequence(
    partner_name: str,
    product: str,
    revshare_pct: float = 0.15,
) -> dict[str, Any]:
    """3-step outreach sequence drafts."""
    return {
        "ok": True,
        "partner": partner_name,
        "sequence": [
            f"Day 0: Soft intro — why {product} fits their audience; no hard ask.",
            f"Day 3: Value kit — sample offer + {int(revshare_pct*100)}% revshare outline.",
            "Day 7: Breakup / bump with case study or social proof.",
        ],
        "draft_only": True,
    }


def get_partnership_ops_tools() -> list:
    return [partnership_score_fit, partnership_revshare_model, partnership_outreach_sequence]
