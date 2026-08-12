"""Unit tests — toolbelts + profiles structural integrity."""

from agents.profiles import PROFILES
from tools.toolbelts import TOOLBELTS, resolve_toolbelt


def test_profiles_count_sota():
    assert len(PROFILES) >= 30


def test_each_profile_has_toolbelts_and_skills():
    for p in PROFILES:
        assert p.key
        assert p.toolbelts, p.key
        assert p.skills is not None


def test_required_belts_exist():
    for name in (
        "parallel_core",
        "supplier",
        "shopify",
        "outreach",
        "shipping_pipeline",
        "logistics",
        "promptwise",
        "spend",
        "linear",
    ):
        assert name in TOOLBELTS
        assert len(TOOLBELTS[name]) >= 1


def test_resolve_toolbelt_dedupes():
    tools = resolve_toolbelt(["supplier", "outreach", "logistics"])
    names = [getattr(t, "__name__", str(t)) for t in tools]
    assert "draft_supplier_outreach_email" in names
    assert "design_shipping_pipeline" in names
    # no exact duplicate function objects
    assert len(tools) == len(set(tools))


def test_supplier_belt_includes_locate_and_outreach():
    names = {getattr(t, "__name__", str(t)) for t in TOOLBELTS["supplier"]}
    assert "locate_suppliers_for_product" in names
    assert "draft_supplier_outreach_email" in names
