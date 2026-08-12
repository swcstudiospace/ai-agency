"""Unit tests — supplier scoring + locate helpers (offline)."""

from tools.supplier_tools import compare_suppliers, score_supplier


def test_score_supplier_recommend_band():
    s = score_supplier(
        name="Good Co",
        lead_time_days=5,
        moq=1,
        unit_cost=3.0,
        shipping_cost=4.0,
        rating=4.8,
    )
    assert s["score"] >= 65
    assert s["recommend"] is True
    assert s["landed_cost"] == 7.0


def test_score_supplier_penalize_slow_high_moq():
    s = score_supplier(
        name="Slow Co",
        lead_time_days=40,
        moq=200,
        unit_cost=50.0,
        shipping_cost=20.0,
        rating=2.0,
    )
    assert s["score"] < 50
    assert s["recommend"] is False


def test_compare_suppliers_ranks_by_score():
    a = score_supplier("A", 5, 1, 3, 4, rating=4.9)
    b = score_supplier("B", 30, 100, 40, 15, rating=3.0)
    out = compare_suppliers([b, a])
    assert out["top"]["name"] == "A"
    assert out["ranked"][0]["score"] >= out["ranked"][1]["score"]
