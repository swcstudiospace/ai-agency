"""Supplier / marketplace research helpers (stubs + Parallel-friendly shapes)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def score_supplier(
    name: str,
    lead_time_days: int,
    moq: int,
    unit_cost: float,
    shipping_cost: float,
    rating: float = 0.0,
    notes: str = "",
) -> Dict[str, Any]:
    """Heuristic supplier score 0-100 for agency ranking."""
    score = 50.0
    if lead_time_days <= 7:
        score += 15
    elif lead_time_days <= 14:
        score += 8
    elif lead_time_days > 25:
        score -= 15
    if moq <= 1:
        score += 10
    elif moq <= 10:
        score += 5
    elif moq > 50:
        score -= 10
    landed = unit_cost + shipping_cost
    if landed < 8:
        score += 10
    elif landed > 40:
        score -= 10
    if rating >= 4.5:
        score += 10
    elif rating and rating < 3.5:
        score -= 15
    score = max(0.0, min(100.0, score))
    return {
        "name": name,
        "score": round(score, 1),
        "landed_cost": round(landed, 2),
        "lead_time_days": lead_time_days,
        "moq": moq,
        "notes": notes,
        "recommend": score >= 65,
    }


def compare_suppliers(candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    ranked = sorted(candidates, key=lambda c: c.get("score", 0), reverse=True)
    return {"ranked": ranked, "top": ranked[0] if ranked else None}


def get_supplier_tools() -> list:
    return [score_supplier, compare_suppliers]
