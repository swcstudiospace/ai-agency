"""Unit tests — logistics DIM weight footgun + SLA."""

from tools.logistics_tools import estimate_shipping_profile, fulfillment_sla_copy


def test_estimate_shipping_profile_dim_weight_not_kg_bug():
    """billable_g must use cm³/5, never ×1000 on dim weight again."""
    p = estimate_shipping_profile(
        origin_country="CN",
        dest_country="US",
        weight_g=300,
        length_cm=20,
        width_cm=15,
        height_cm=5,
    )
    # vol=1500 → dim_weight_g=300
    assert p["dim_weight_g"] == 300.0
    assert p["billable_g"] == 300.0
    assert 4 < p["estimated_ship_cost_usd"] < 30
    assert p["shipping_risk"] in {"low", "medium", "high"}


def test_domestic_cheaper_than_intl():
    us = estimate_shipping_profile(origin_country="US", dest_country="US", weight_g=400)
    cn = estimate_shipping_profile(origin_country="CN", dest_country="US", weight_g=400)
    assert us["estimated_ship_cost_usd"] < cn["estimated_ship_cost_usd"]


def test_fulfillment_sla_copy_fields():
    s = fulfillment_sla_copy(processing_hours=24, transit_guidance="5-10 days")
    assert "24 hours" in s["pdp_shipping_blurb"]
    assert "tracking" in s["email_shipped_template"].lower() or "Tracking" in s["email_shipped_template"]
