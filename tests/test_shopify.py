"""Unit tests — Shopify offline stubs + domain plan."""


from tools.shopify_tools import (
    draft_product,
    shopify_bootstrap_checklist,
    shopify_domain_plan,
    shopify_status,
)


def test_shopify_status_without_shop(monkeypatch):
    monkeypatch.delenv("SHOPIFY_SHOP_NAME", raising=False)
    monkeypatch.delenv("SHOPIFY_SHOP", raising=False)
    monkeypatch.delenv("SHOPIFY_ACCESS_TOKEN", raising=False)
    st = shopify_status()
    assert st["ok"] is False
    assert st["mode"] == "stub"


def test_draft_product_stubs_offline(monkeypatch):
    monkeypatch.delenv("SHOPIFY_SHOP_NAME", raising=False)
    monkeypatch.delenv("SHOPIFY_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("SHOPIFY_CLIENT_ID", raising=False)
    d = draft_product(title="T", body_html="<p>x</p>", price="9.99", status="draft")
    assert d.get("stub") is True
    assert d.get("status") == "draft"


def test_domain_plan_ego():
    d = shopify_domain_plan("ego.engineer")
    assert d["primary_domain"] == "ego.engineer"
    assert any(r.get("type") == "A" for r in d["dns_records_typical"])
    assert any(r.get("type") == "CNAME" for r in d["dns_records_typical"])


def test_bootstrap_checklist_shape():
    b = shopify_bootstrap_checklist()
    assert b.get("checklist")
    assert b.get("headless", {}).get("repo_path") == "storefront-oxygen/"
    assert "shopify_status" in b
