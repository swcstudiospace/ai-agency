"""Unit tests — seller outreach drafts (offline, no browser)."""

from pathlib import Path

from tools.seller_outreach_tools import draft_supplier_outreach_email, gmail_compose_url


def test_draft_supplier_outreach_writes_artifacts():
    d = draft_supplier_outreach_email(
        product_name="Fold-Flat Laptop Stand",
        supplier_name="Yocaxn",
        supplier_url="https://example.com/x",
        unit_cost_usd=2.2,
        moq=2,
        brand_name="ego.engineer",
    )
    assert d["ok"] is True
    assert "Sample" in d["subject"] or "sample" in d["subject"].lower()
    assert "dropship" in d["body"].lower()
    assert Path(d["artifact_md"]).is_file()
    assert Path(d["artifact_json"]).is_file()
    assert d["hitl"] is True


def test_gmail_compose_url_encodes():
    u = gmail_compose_url(to="a@b.com", subject="Hi there", body="Line1\nLine2")
    assert u.startswith("https://mail.google.com/mail/?")
    assert "su=" in u
    assert "body=" in u
