"""Logistics helpers — tracking, ETA estimates, 17track/AfterShip-style hooks."""

from __future__ import annotations

from typing import Any

import httpx

from tools.envutil import env


def estimate_shipping_profile(
    origin_country: str = "CN",
    dest_country: str = "US",
    weight_g: float = 300,
    length_cm: float = 20,
    width_cm: float = 15,
    height_cm: float = 5,
) -> dict[str, Any]:
    """Heuristic shipping risk/cost profile for dropshipping planning."""
    vol = max(float(length_cm) * float(width_cm) * float(height_cm), 1.0)
    # Courier-style DIM: kg ≈ cm³/5000 → grams ≈ cm³/5
    dim_weight_g = vol / 5.0
    billable_g = max(float(weight_g), dim_weight_g)
    # very rough lane costs for planning only
    base = 4.5 if dest_country.upper() in {"US", "CA", "GB", "AU", "DE", "FR"} else 6.5
    cost = base + (billable_g / 1000.0) * 3.2
    if origin_country.upper() == dest_country.upper():
        cost *= 0.55
        eta = "2-6 days"
        risk = "low"
    else:
        eta = "7-18 days" if dest_country.upper() in {"US", "CA", "GB", "EU", "DE", "FR", "AU"} else "10-25 days"
        risk = "medium" if billable_g < 800 else "high"
    return {
        "origin_country": origin_country,
        "dest_country": dest_country,
        "weight_g": weight_g,
        "dim_weight_g": round(dim_weight_g, 1),
        "billable_g": round(billable_g, 1),
        "estimated_ship_cost_usd": round(cost, 2),
        "eta_guidance": eta,
        "shipping_risk": risk,
        "notes": "Planning heuristic only — replace with carrier quotes before scale.",
    }


def track_shipment(tracking_number: str, carrier: str = "") -> dict[str, Any]:
    """Track via 17track if SEVENTEENTRACK_TOKEN set; else stub."""
    tracking_number = (tracking_number or "").strip()
    if not tracking_number:
        return {"error": "tracking_number required"}
    token = env("SEVENTEENTRACK_TOKEN") or env("TRACK17_TOKEN")
    if not token:
        return {
            "stub": True,
            "tracking_number": tracking_number,
            "carrier": carrier or "unknown",
            "status": "unknown",
            "events": [],
            "next": "Set SEVENTEENTRACK_TOKEN for live tracking",
        }
    # 17track v2 style
    headers = {"17token": token, "Content-Type": "application/json"}
    body = [{"number": tracking_number}]
    if carrier:
        body[0]["carrier"] = carrier
    try:
        with httpx.Client(timeout=45.0) as client:
            # register
            client.post("https://api.17track.net/track/v2.2/register", headers=headers, json=body)
            r = client.post(
                "https://api.17track.net/track/v2.2/gettrackinfo",
                headers=headers,
                json=body,
            )
            return {"stub": False, "data": r.json()}
    except Exception as e:
        return {"error": str(e), "tracking_number": tracking_number}


def fulfillment_sla_copy(
    processing_hours: int = 48,
    transit_guidance: str = "6-14 days",
) -> dict[str, Any]:
    return {
        "pdp_shipping_blurb": (
            f"Orders typically process within {processing_hours} hours. "
            f"Estimated delivery {transit_guidance} after dispatch depending on destination. "
            "Tracking is provided when available."
        ),
        "email_shipped_template": (
            "Your order is on the way. Tracking: {{tracking}}. "
            f"Most customers receive packages within {transit_guidance}."
        ),
        "wismo_macro": (
            "Thanks for reaching out — I checked your order. "
            "Current tracking status: {{status}}. "
            "If there's no scan update within 48 hours, reply here and we'll escalate."
        ),
    }


def get_logistics_tools() -> list:
    return [estimate_shipping_profile, track_shipment, fulfillment_sla_copy]
