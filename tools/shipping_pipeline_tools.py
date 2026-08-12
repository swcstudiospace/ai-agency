"""Shipping / fulfillment pipeline setup for dropshipping.

After locate + sample approval, configure HOW orders move:

  Shopify order → (webhook/app) → supplier portal or 3PL → tracking → CX

This module builds a pipeline plan, SLA copy, carrier profile, and optional
Shopify draft shipping settings notes. Live carrier contracts stay HITL.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from tools.envutil import env
from tools.logistics_tools import estimate_shipping_profile, fulfillment_sla_copy


def design_shipping_pipeline(
    product_name: str,
    origin_country: str = "CN",
    dest_markets: Optional[List[str]] = None,
    fulfillment_mode: str = "supplier_dropship",
    processing_hours: int = 48,
    weight_g: float = 450,
) -> Dict[str, Any]:
    """Design fulfillment routing for a SKU (planning artifact, not carrier booking).

    fulfillment_mode:
      - supplier_dropship: supplier ships per order (classic DS)
      - platform_cj: CJ/Zendrop/Doba style
      - stock_3pl: hold inventory in regional 3PL
      - hybrid: samples/local + overseas bulk
    """
    markets = dest_markets or ["US", "CA", "GB", "AU"]
    mode = (fulfillment_mode or "supplier_dropship").lower()
    lanes = []
    for m in markets:
        prof = estimate_shipping_profile(
            origin_country=origin_country,
            dest_country=m,
            weight_g=weight_g,
        )
        lanes.append(prof)

    sla = fulfillment_sla_copy(
        processing_hours=processing_hours,
        transit_guidance=lanes[0].get("eta_guidance") if lanes else "7-18 days",
    )

    steps = {
        "supplier_dropship": [
            "1. Customer pays on Shopify (ego.engineer headless or online store)",
            "2. Order webhook → agency fulfillment agent / Zapier / custom app",
            "3. Push order to supplier (email/API/portal) with customer ship-to",
            "4. Supplier dispatches; paste tracking into Shopify fulfillment",
            "5. 17track/AfterShip monitor + WISMO macros",
        ],
        "platform_cj": [
            "1. Connect CJ/Doba/Zendrop app to Shopify",
            "2. Map product variants to supplier SKUs",
            "3. Auto-fulfill on paid orders",
            "4. Tracking sync back to Shopify",
            "5. Agency monitors exceptions only",
        ],
        "stock_3pl": [
            "1. Bulk PO → inbound to 3PL (US/EU)",
            "2. Shopify inventory location = 3PL",
            "3. Faster domestic ship; higher capital",
            "4. Returns to 3PL address",
        ],
        "hybrid": [
            "1. Soft launch via supplier_dropship",
            "2. After velocity proof, inbound top SKU to 3PL",
            "3. Split routing by geo / stock",
        ],
    }.get(mode, [])

    shopify_settings = {
        "shipping_profiles": [
            {
                "name": f"{product_name[:40]} — Standard international",
                "rate_name": "Standard",
                "price_usd_hint": lanes[0].get("estimated_ship_cost_usd") if lanes else 9.99,
                "countries": markets,
            }
        ],
        "checkout_promise": sla.get("pdp_shipping_blurb"),
        "locations": [
            {"name": "Supplier / Origin", "country": origin_country, "fulfills_online": True},
            {"name": "Returns — brand", "country": markets[0], "fulfills_online": False},
        ],
        "apps_recommended": [
            "Official Shopify Email or Klaviyo",
            "17TRACK / AfterShip",
            "CJDropshipping or Doba (if platform mode)",
            "Shopify Flow for paid→notify sourcing",
        ],
    }

    domain = env("AGENCY_PRIMARY_DOMAIN") or "ego.engineer"
    payload = {
        "ok": True,
        "product_name": product_name,
        "fulfillment_mode": mode,
        "origin_country": origin_country,
        "dest_markets": markets,
        "lanes": lanes,
        "sla": sla,
        "pipeline_steps": steps,
        "shopify_settings": shopify_settings,
        "webhooks": [
            {
                "topic": "orders/paid",
                "target": f"https://api.{domain}/webhooks/shopify/orders-paid",
                "purpose": "Trigger supplier order push / Flow",
            },
            {
                "topic": "fulfillments/create",
                "target": f"https://api.{domain}/webhooks/shopify/fulfillments",
                "purpose": "Sync tracking to CX + KIP",
            },
        ],
        "hitl": True,
        "note": "Planning only — do not book paid labels or auto-push supplier POs without human OK",
    }

    out = Path("tmp/shipping")
    out.mkdir(parents=True, exist_ok=True)
    stamp = int(time.time())
    jp = out / f"pipeline_{stamp}.json"
    jp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    payload["artifact"] = str(jp)
    return payload


def setup_order_routing_playbook(
    mode: str = "supplier_dropship",
    brand_domain: str = "",
) -> Dict[str, Any]:
    """Operator checklist for connecting Shopify → fulfillment."""
    domain = brand_domain or env("AGENCY_PRIMARY_DOMAIN") or "ego.engineer"
    checklist = [
        f"Point storefront domain {domain} in Shopify + DNS (A/AAAA/CNAME per Shopify docs)",
        "Enable Shopify payments / payout account (HITL — human bank)",
        "Create shipping profile: free over $X or flat international",
        "Add store policies: shipping, refund, privacy, TOS (required for paid ads)",
        "Install tracking app (17track/AfterShip) when SEVENTEENTRACK_TOKEN ready",
        "Configure orders/paid webhook or Shopify Flow → notify sourcing channel",
        "Map SKU → supplier SKU in locate sheet / KIP",
        "Test order with draft product (bogus checkout in Shopify test mode)",
        "Only then: real sample from top supplier (HITL payment)",
    ]
    if mode == "platform_cj":
        checklist.insert(4, "Install CJ/Doba and authorize product import")
    return {
        "ok": True,
        "mode": mode,
        "domain": domain,
        "checklist": checklist,
        "hitl_items": ["payments", "domain DNS", "sample payment", "live app installs"],
    }


def get_shipping_pipeline_tools() -> list:
    return [design_shipping_pipeline, setup_order_routing_playbook]
