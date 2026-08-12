"""Unit tests — shipping pipeline design (offline)."""

from pathlib import Path

from tools.shipping_pipeline_tools import design_shipping_pipeline, setup_order_routing_playbook


def test_design_shipping_pipeline_supplier_dropship():
    p = design_shipping_pipeline(
        product_name="Laptop Stand",
        fulfillment_mode="supplier_dropship",
        dest_markets=["US", "CA"],
    )
    assert p["ok"] is True
    assert p["fulfillment_mode"] == "supplier_dropship"
    assert len(p["lanes"]) == 2
    assert p["pipeline_steps"]
    assert Path(p["artifact"]).is_file()
    assert p["hitl"] is True


def test_order_routing_playbook_includes_domain():
    pb = setup_order_routing_playbook(mode="platform_cj", brand_domain="ego.engineer")
    assert pb["domain"] == "ego.engineer"
    assert any("ego.engineer" in c or "domain" in c.lower() for c in pb["checklist"])
    assert any("CJ" in c or "Doba" in c for c in pb["checklist"])
