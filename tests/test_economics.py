"""Unit tests — economics (critical footguns)."""

from tools.economics_tools import contribution_margin, price_ladder


def test_contribution_margin_healthy_go_band():
    r = contribution_margin(49.99, 14.0, 5.5, ad_spend_per_order=18.0)
    assert r["sell_price"] == 49.99
    assert 0.15 < r["contribution_margin_pct"] < 0.45
    assert r["contribution_margin"] > 0


def test_contribution_margin_positional_fee_is_not_cpa():
    """Regression: bare 4th arg is payment_fee_pct, not CPA — must not look healthy."""
    wrong = contribution_margin(49.99, 14.0, 5.5, 18.0)
    assert wrong["contribution_margin_pct"] < -1.0


def test_contribution_margin_keyword_cpa():
    good = contribution_margin(49.99, 14.0, 5.5, ad_spend_per_order=18.0)
    assert good["healthy"] is True or good["contribution_margin_pct"] >= 0.15


def test_price_ladder_positive():
    r = price_ladder(cogs=12.0, shipping=5.0, target_cm_pct=0.30, ad_cpa=15.0)
    assert "suggested_price" in r
    assert r["suggested_price"] > 20
