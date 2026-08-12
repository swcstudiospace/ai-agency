"""Tax / fiscal expansion gate tools (briefs for human CPA — not filings)."""

from __future__ import annotations

from typing import Any


def tax_nexus_checklist(regions: list[str] | None = None) -> dict[str, Any]:
    """High-level nexus/VAT checklist by region code (research starting point)."""
    regions = regions or ["US-CA", "US-NY", "US-TX"]
    rows = []
    for r in regions:
        ru = r.upper()
        if ru.startswith("US"):
            rows.append({"region": r, "theme": "sales_tax_economic_nexus", "action": "confirm_registration_and_collection"})
        elif ru in {"EU", "DE", "FR", "IE"} or ru.startswith("EU"):
            rows.append({"region": r, "theme": "vat_ioss_or_local", "action": "BLOCK_SHIP until VAT path chosen"})
        else:
            rows.append({"region": r, "theme": "research", "action": "ATTENTION — Parallel research + CPA"})
    return {"ok": True, "regions": rows, "disclaimer": "Not legal advice; human CPA required."}


def tax_geo_expansion_gate(region: str, collection_configured: bool = False, cpa_reviewed: bool = False) -> dict[str, Any]:
    """Gate geo expansion: OK | ATTENTION | BLOCK_SHIP."""
    r = (region or "").upper()
    if r.startswith("EU") and not collection_configured:
        verdict = "BLOCK_SHIP"
    elif not cpa_reviewed:
        verdict = "ATTENTION"
    elif collection_configured:
        verdict = "OK"
    else:
        verdict = "ATTENTION"
    return {
        "ok": True,
        "region": region,
        "verdict": verdict,
        "collection_configured": collection_configured,
        "cpa_reviewed": cpa_reviewed,
    }


def tax_document_pack(regions: list[str] | None = None) -> dict[str, Any]:
    """Documents to assemble for human tax counsel."""
    return {
        "ok": True,
        "regions": regions or [],
        "documents": [
            "Entity formation docs",
            "Sales by state/country last 12 months",
            "Shopify tax settings export",
            "Marketplace vs DTC split",
            "Nexus questionnaire answers",
            "Prior returns/filings if any",
        ],
        "disclaimer": "Agent prepares pack only — does not file.",
    }


def get_tax_ops_tools() -> list:
    return [tax_nexus_checklist, tax_geo_expansion_gate, tax_document_pack]
