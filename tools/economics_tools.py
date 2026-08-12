"""Unit economics and pricing helpers."""

from __future__ import annotations

from typing import Any


def contribution_margin(
    sell_price: float,
    cogs: float,
    shipping: float,
    payment_fee_pct: float = 0.029,
    payment_fee_fixed: float = 0.30,
    ad_spend_per_order: float = 0.0,
    returns_pct: float = 0.05,
    other_variable: float = 0.0,
) -> dict[str, Any]:
    """Compute contribution margin after ads and expected returns."""
    fees = sell_price * payment_fee_pct + payment_fee_fixed
    returns_cost = sell_price * returns_pct
    variable = cogs + shipping + fees + ad_spend_per_order + returns_cost + other_variable
    cm = sell_price - variable
    cm_pct = (cm / sell_price) if sell_price else 0.0
    breakeven_roas = (sell_price / ad_spend_per_order) if ad_spend_per_order > 0 else None
    # Min ROAS to stay CM-positive if ads are the lever
    min_roas = None
    if ad_spend_per_order > 0:
        # Rough: need CM before ads > 0 at target
        cm_before_ads = sell_price - (cogs + shipping + fees + returns_cost + other_variable)
        min_roas = (sell_price / cm_before_ads) if cm_before_ads > 0 else None
    return {
        "sell_price": sell_price,
        "variable_cost": round(variable, 2),
        "contribution_margin": round(cm, 2),
        "contribution_margin_pct": round(cm_pct, 4),
        "breakeven_roas_at_current_cpa": round(breakeven_roas, 2) if breakeven_roas else None,
        "suggested_min_roas": round(min_roas, 2) if min_roas else None,
        "healthy": cm_pct >= 0.25 and cm > 0,
    }


def price_ladder(
    cogs: float,
    shipping: float,
    target_cm_pct: float = 0.35,
    ad_cpa: float = 15.0,
) -> dict[str, Any]:
    """Suggest sell prices for target contribution margin after ads."""
    base_variable = cogs + shipping + 0.30  # rough fixed fee
    # price - base_variable - 0.029*price - ad_cpa = target_cm_pct * price
    # price * (1 - 0.029 - target_cm_pct) = base_variable + ad_cpa
    denom = 1 - 0.029 - target_cm_pct
    if denom <= 0:
        return {"error": "target_cm_pct too high"}
    price = (base_variable + ad_cpa) / denom
    return {
        "suggested_price": round(price, 2),
        "target_cm_pct": target_cm_pct,
        "assumed_cpa": ad_cpa,
        "cogs": cogs,
        "shipping": shipping,
    }


def get_economics_tools() -> list:
    return [contribution_margin, price_ladder]
