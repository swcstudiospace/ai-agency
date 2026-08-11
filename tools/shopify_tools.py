"""Shopify Admin API tools — drafts by default; publish is HITL/L3."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx

from tools.envutil import env


API_VERSION = env("SHOPIFY_API_VERSION", "2024-10")


def _shop_config() -> Optional[tuple[str, str]]:
    shop = env("SHOPIFY_SHOP_NAME")
    token = env("SHOPIFY_ACCESS_TOKEN")
    if not shop or not token:
        return None
    host = shop if shop.endswith(".myshopify.com") else f"{shop}.myshopify.com"
    return host, token


def shopify_status() -> Dict[str, Any]:
    cfg = _shop_config()
    if not cfg:
        return {"ok": False, "mode": "stub", "reason": "SHOPIFY_SHOP_NAME or SHOPIFY_ACCESS_TOKEN missing"}
    host, token = cfg
    try:
        with httpx.Client(timeout=30.0) as client:
            r = client.get(
                f"https://{host}/admin/api/{API_VERSION}/shop.json",
                headers={"X-Shopify-Access-Token": token},
            )
            data = r.json()
        return {"ok": r.status_code == 200, "mode": "live", "shop": data.get("shop") or data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def draft_product(
    title: str,
    body_html: str,
    price: str,
    tags: Optional[List[str]] = None,
    vendor: str = "Agency",
    status: str = "draft",
    product_type: str = "",
    images: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Create a product (default status=draft). status=active blocked at L2 by guardrails."""
    payload: Dict[str, Any] = {
        "product": {
            "title": title,
            "body_html": body_html,
            "vendor": vendor,
            "product_type": product_type,
            "tags": ", ".join(tags or []),
            "status": status or "draft",
            "variants": [{"price": str(price)}],
        }
    }
    if images:
        payload["product"]["images"] = [{"src": u} for u in images[:10]]

    cfg = _shop_config()
    if not cfg:
        print(f"[Shopify STUB] draft product: {title} @ {price}")
        return {
            "id": "shopify-stub-product",
            "title": title,
            "status": status,
            "price": price,
            "stub": True,
        }

    host, token = cfg
    url = f"https://{host}/admin/api/{API_VERSION}/products.json"
    headers = {"X-Shopify-Access-Token": token, "Content-Type": "application/json"}
    with httpx.Client(timeout=45.0) as client:
        resp = client.post(url, headers=headers, json=payload)
        data = resp.json()
    return data.get("product") or data


def update_product(product_id: str, **fields: Any) -> Dict[str, Any]:
    cfg = _shop_config()
    if not cfg:
        return {"stub": True, "id": product_id, "updated": fields}
    host, token = cfg
    url = f"https://{host}/admin/api/{API_VERSION}/products/{product_id}.json"
    headers = {"X-Shopify-Access-Token": token, "Content-Type": "application/json"}
    with httpx.Client(timeout=45.0) as client:
        resp = client.put(url, headers=headers, json={"product": {"id": product_id, **fields}})
        data = resp.json()
    return data.get("product") or data


def list_products(limit: int = 10, status: str = "") -> Dict[str, Any]:
    cfg = _shop_config()
    if not cfg:
        print("[Shopify STUB] list_products")
        return {"products": [], "stub": True}
    host, token = cfg
    params = f"limit={max(1, min(250, limit))}"
    if status:
        params += f"&status={status}"
    url = f"https://{host}/admin/api/{API_VERSION}/products.json?{params}"
    headers = {"X-Shopify-Access-Token": token}
    with httpx.Client(timeout=30.0) as client:
        resp = client.get(url, headers=headers)
        return resp.json()


def list_orders(limit: int = 10, status: str = "any") -> Dict[str, Any]:
    cfg = _shop_config()
    if not cfg:
        return {"orders": [], "stub": True}
    host, token = cfg
    url = f"https://{host}/admin/api/{API_VERSION}/orders.json?limit={limit}&status={status}"
    headers = {"X-Shopify-Access-Token": token}
    with httpx.Client(timeout=30.0) as client:
        return client.get(url, headers=headers).json()


def create_draft_order(
    line_items: List[Dict[str, Any]],
    email: str = "",
    note: str = "agency draft",
) -> Dict[str, Any]:
    """Create a Shopify draft order (not a paid order)."""
    cfg = _shop_config()
    payload = {"draft_order": {"line_items": line_items, "note": note}}
    if email:
        payload["draft_order"]["email"] = email
    if not cfg:
        return {"stub": True, "draft_order": payload["draft_order"]}
    host, token = cfg
    url = f"https://{host}/admin/api/{API_VERSION}/draft_orders.json"
    headers = {"X-Shopify-Access-Token": token, "Content-Type": "application/json"}
    with httpx.Client(timeout=45.0) as client:
        return client.post(url, headers=headers, json=payload).json()


def get_shopify_tools() -> list:
    return [
        shopify_status,
        draft_product,
        update_product,
        list_products,
        list_orders,
        create_draft_order,
    ]
