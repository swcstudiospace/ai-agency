"""Catalog hygiene and merchandising ops tools."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def catalog_health_scan(
    sku_count: int = 0,
    missing_images: int = 0,
    missing_prices: int = 0,
    drafts_public: int = 0,
    dead_no_sales_90d: int = 0,
) -> Dict[str, Any]:
    """Score catalog health from provided counters (wire live Shopify counts when available)."""
    issues = []
    if missing_images:
        issues.append(f"{missing_images} SKUs missing images")
    if missing_prices:
        issues.append(f"{missing_prices} SKUs missing prices")
    if drafts_public:
        issues.append(f"{drafts_public} draft/junk visible")
    if dead_no_sales_90d:
        issues.append(f"{dead_no_sales_90d} dead SKUs 90d")
    score = 100 - 10 * len(issues) - min(30, dead_no_sales_90d)
    return {
        "ok": True,
        "sku_count": sku_count,
        "health_score_0_to_100": max(0, score),
        "issues": issues,
        "actions": ["complete_fields", "archive_dead", "fix_prices", "feature_winners"],
    }


def catalog_price_audit(
    sku: str,
    list_price: float,
    cogs: float,
    shipping: float = 0.0,
    target_cm_pct: float = 0.25,
) -> Dict[str, Any]:
    """Check if list price clears target contribution margin."""
    cm = float(list_price) - float(cogs) - float(shipping)
    cm_pct = cm / list_price if list_price else 0.0
    ok = cm_pct >= target_cm_pct
    return {
        "ok": True,
        "sku": sku,
        "list_price": list_price,
        "cm_usd": round(cm, 2),
        "cm_pct": round(cm_pct, 4),
        "target_cm_pct": target_cm_pct,
        "passes": ok,
        "action": "ok" if ok else "raise_price_or_cut_cogs",
    }


def catalog_publish_plan(
    publish: Optional[List[str]] = None,
    archive: Optional[List[str]] = None,
    feature: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Plan publish/archive/feature actions (execution via Shopify HITL/API)."""
    return {
        "ok": True,
        "publish_queue": list(publish or []),
        "archive_candidates": list(archive or []),
        "feature": list(feature or []),
        "draft_only": True,
    }


def get_catalog_ops_tools() -> list:
    return [catalog_health_scan, catalog_price_audit, catalog_publish_plan]
