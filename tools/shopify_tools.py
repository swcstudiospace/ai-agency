"""Shopify Admin API tools — drafts by default; publish is HITL/L3.

Auth (in order):
  1. ``SHOPIFY_ACCESS_TOKEN`` + ``SHOPIFY_SHOP_NAME`` (static Admin token)
  2. Dev Dashboard **client credentials** grant using
     ``SHOPIFY_CLIENT_ID`` + ``SHOPIFY_CLIENT_SECRET`` + ``SHOPIFY_SHOP_NAME``
     (tokens expire ~24h; auto-refreshed and cached under tmp/secrets/)

Never log secrets. Products default to status=draft.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import httpx

from tools.envutil import env

API_VERSION = env("SHOPIFY_API_VERSION", "2024-10") or "2024-10"
_TOKEN_CACHE = Path("tmp/secrets/shopify_token.json")


def _shop_host() -> str | None:
    shop = (env("SHOPIFY_SHOP_NAME") or env("SHOPIFY_SHOP") or "").strip()
    if not shop:
        return None
    return shop if shop.endswith(".myshopify.com") else f"{shop}.myshopify.com"


def _load_cached_token(host: str) -> str | None:
    try:
        if not _TOKEN_CACHE.is_file():
            return None
        data = json.loads(_TOKEN_CACHE.read_text(encoding="utf-8"))
        if data.get("host") != host:
            return None
        exp = float(data.get("expires_at") or 0)
        if exp and time.time() < exp - 120:
            tok = data.get("access_token")
            return str(tok) if tok else None
    except Exception:
        return None
    return None


def _save_cached_token(host: str, access_token: str, expires_in: int = 86399) -> None:
    try:
        _TOKEN_CACHE.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "host": host,
            "access_token": access_token,
            "expires_at": time.time() + max(60, int(expires_in)),
            "obtained_at": time.time(),
        }
        _TOKEN_CACHE.write_text(json.dumps(payload), encoding="utf-8")
        _TOKEN_CACHE.chmod(0o600)
    except Exception:
        pass


def _client_credentials_token(host: str) -> str | None:
    """Exchange Dev Dashboard client id/secret for a short-lived Admin token."""
    client_id = env("SHOPIFY_CLIENT_ID") or env("SHOPIFY_API_KEY")
    client_secret = env("SHOPIFY_CLIENT_SECRET") or env("SHOPIFY_API_SECRET")
    if not client_id or not client_secret:
        return None
    cached = _load_cached_token(host)
    if cached:
        return cached
    url = f"https://{host}/admin/oauth/access_token"
    try:
        with httpx.Client(timeout=30.0) as client:
            r = client.post(
                url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": client_id,
                    "client_secret": client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            data = r.json() if r.content else {}
        tok = data.get("access_token")
        if not tok:
            return None
        _save_cached_token(host, str(tok), int(data.get("expires_in") or 86399))
        return str(tok)
    except Exception:
        return None


def _shop_config() -> tuple[str, str] | None:
    host = _shop_host()
    if not host:
        return None
    token = (env("SHOPIFY_ACCESS_TOKEN") or "").strip()
    if token:
        return host, token
    tok = _client_credentials_token(host)
    if tok:
        return host, tok
    return None


def shopify_status() -> dict[str, Any]:
    host = _shop_host()
    cfg = _shop_config()
    if not host:
        return {
            "ok": False,
            "mode": "stub",
            "reason": "SHOPIFY_SHOP_NAME missing (need your-store.myshopify.com)",
            "client_id_set": bool(env("SHOPIFY_CLIENT_ID") or env("SHOPIFY_API_KEY")),
            "client_secret_set": bool(env("SHOPIFY_CLIENT_SECRET") or env("SHOPIFY_API_SECRET")),
        }
    if not cfg:
        return {
            "ok": False,
            "mode": "stub",
            "reason": "No access token — set SHOPIFY_ACCESS_TOKEN or client credentials failed",
            "shop": host,
            "client_id_set": bool(env("SHOPIFY_CLIENT_ID") or env("SHOPIFY_API_KEY")),
            "hint": "Install/deploy the Dev Dashboard app on this shop, grant scopes, then retry",
        }
    host, token = cfg
    try:
        with httpx.Client(timeout=30.0) as client:
            r = client.get(
                f"https://{host}/admin/api/{API_VERSION}/shop.json",
                headers={"X-Shopify-Access-Token": token},
            )
            data = r.json() if r.content else {}
        shop = data.get("shop") if isinstance(data, dict) else None
        return {
            "ok": r.status_code == 200,
            "mode": "live",
            "shop_host": host,
            "shop_name": (shop or {}).get("name") if isinstance(shop, dict) else None,
            "shop_domain": (shop or {}).get("domain") if isinstance(shop, dict) else None,
            "shop_email": (shop or {}).get("email") if isinstance(shop, dict) else None,
            "currency": (shop or {}).get("currency") if isinstance(shop, dict) else None,
            "status_code": r.status_code,
            "auth": "access_token" if env("SHOPIFY_ACCESS_TOKEN") else "client_credentials",
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "shop_host": host}


def draft_product(
    title: str,
    body_html: str,
    price: str,
    tags: list[str] | None = None,
    vendor: str = "Agency",
    status: str = "draft",
    product_type: str = "",
    images: list[str] | None = None,
) -> dict[str, Any]:
    """Create a product (default status=draft). status=active blocked at L2 by guardrails."""
    payload: dict[str, Any] = {
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
        data = resp.json() if resp.content else {}
    product = data.get("product") if isinstance(data, dict) else None
    if product:
        product["stub"] = False
        return product
    return {"error": data, "status_code": resp.status_code, "stub": False}


def update_product(product_id: str, **fields: Any) -> dict[str, Any]:
    cfg = _shop_config()
    if not cfg:
        return {"stub": True, "id": product_id, "updated": fields}
    host, token = cfg
    url = f"https://{host}/admin/api/{API_VERSION}/products/{product_id}.json"
    headers = {"X-Shopify-Access-Token": token, "Content-Type": "application/json"}
    with httpx.Client(timeout=45.0) as client:
        resp = client.put(url, headers=headers, json={"product": {"id": product_id, **fields}})
        data = resp.json() if resp.content else {}
    return data.get("product") or data


def list_products(limit: int = 10, status: str = "") -> dict[str, Any]:
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
        data = resp.json() if resp.content else {}
    if isinstance(data, dict):
        data["stub"] = False
        data["status_code"] = resp.status_code
    return data


def list_orders(limit: int = 10, status: str = "any") -> dict[str, Any]:
    cfg = _shop_config()
    if not cfg:
        return {"orders": [], "stub": True}
    host, token = cfg
    url = f"https://{host}/admin/api/{API_VERSION}/orders.json?limit={limit}&status={status}"
    headers = {"X-Shopify-Access-Token": token}
    with httpx.Client(timeout=30.0) as client:
        return client.get(url, headers=headers).json()


def create_draft_order(
    line_items: list[dict[str, Any]],
    email: str = "",
    note: str = "agency draft",
) -> dict[str, Any]:
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


def shopify_domain_plan(primary_domain: str = "") -> dict[str, Any]:
    """DNS + Shopify domain attach plan for brand domain (e.g. ego.engineer)."""
    domain = (primary_domain or env("AGENCY_PRIMARY_DOMAIN") or env("SHOPIFY_PRIMARY_DOMAIN") or "ego.engineer").strip()
    host = _shop_host() or "YOUR-STORE.myshopify.com"
    return {
        "ok": True,
        "primary_domain": domain,
        "myshopify_host": host,
        "shopify_admin_path": "Settings → Domains → Connect existing domain",
        "dns_records_typical": [
            {
                "type": "A",
                "host": "@",
                "value": "23.227.38.65",
                "note": "Shopify apex IPv4 (confirm in admin — Shopify may update)",
            },
            {
                "type": "AAAA",
                "host": "@",
                "value": "2620:0127:f00f:5::",
                "note": "Shopify apex IPv6 if offered",
            },
            {
                "type": "CNAME",
                "host": "www",
                "value": "shops.myshopify.com",
                "note": "www → Shopify",
            },
            {
                "type": "CNAME",
                "host": "shop",
                "value": host,
                "note": "optional shop subdomain",
            },
        ],
        "oxygen_notes": [
            "Headless Hydrogen on Oxygen uses its own deploy domain first",
            f"Then attach {domain} (or store.{domain}) as custom domain in Oxygen/Shopify",
            "Storefront API + Customer Account API tokens required for headless",
        ],
        "hitl": True,
        "note": "DNS at registrar for ego.engineer is human-owned — agency cannot change DNS without credentials",
    }


def shopify_bootstrap_checklist() -> dict[str, Any]:
    """Bare-account → launch checklist for AI Dropshipping Agency / ego.engineer."""
    status = shopify_status()
    domain = env("AGENCY_PRIMARY_DOMAIN") or "ego.engineer"
    return {
        "ok": True,
        "shopify_status": {
            "ok": status.get("ok"),
            "mode": status.get("mode"),
            "shop": status.get("shop") or status.get("shop_host"),
            "reason": status.get("reason"),
        },
        "checklist": [
            "1. Dev Dashboard: install app on the shop with write_products, write_draft_orders, read_orders, write_fulfillments",
            "2. Confirm SHOPIFY_SHOP_NAME matches admin URL subdomain",
            "3. Settings → Payments: enable test mode first",
            "4. Settings → Shipping: general profile + international rates",
            "5. Settings → Policies: refund, privacy, TOS, shipping",
            f"6. Settings → Domains: connect {domain} (see shopify_domain_plan)",
            "7. Settings → Checkout: customer contact email + order notifications",
            "8. Online Store OR headless: create Storefront API token for Oxygen/Hydrogen",
            "9. Create draft product via agency E2E (status=draft)",
            "10. Place test order in Bogus Gateway before live ads",
        ],
        "headless": {
            "stack": "Shopify Hydrogen + Oxygen",
            "repo_path": "storefront-oxygen/",
            "env": [
                "PUBLIC_STORE_DOMAIN",
                "PUBLIC_STOREFRONT_API_TOKEN",
                "PRIVATE_STOREFRONT_API_TOKEN",
                "PUBLIC_STOREFRONT_API_VERSION",
            ],
        },
        "domain_plan": shopify_domain_plan(domain),
        "hitl": True,
    }


def shopify_create_policy_pages(
    shipping_html: str = "",
    refund_html: str = "",
    privacy_html: str = "",
) -> dict[str, Any]:
    """Create basic policy pages as drafts (live requires auth + HITL publish)."""
    brand = env("SHOPIFY_SHOP_DISPLAY_NAME") or "AI Dropshipping Agency"
    domain = env("AGENCY_PRIMARY_DOMAIN") or "ego.engineer"
    defaults = {
        "Shipping Policy": shipping_html
        or f"<p>{brand} ships internationally. Processing within 48 hours. Delivery estimates shown at checkout. Tracking provided when available. Domain: {domain}</p>",
        "Refund Policy": refund_html
        or f"<p>Contact support within 14 days of delivery for damaged/defective items. Opened consumables may be non-returnable. {brand}</p>",
        "Privacy Policy": privacy_html
        or f"<p>{brand} collects order and contact data to fulfill purchases. We do not sell personal data. Contact privacy@{domain}</p>",
    }
    created = []
    cfg = _shop_config()
    for title, body in defaults.items():
        if not cfg:
            created.append({"title": title, "stub": True, "body_html": body[:120]})
            continue
        host, token = cfg
        payload = {"page": {"title": title, "body_html": body, "published": False}}
        url = f"https://{host}/admin/api/{API_VERSION}/pages.json"
        headers = {"X-Shopify-Access-Token": token, "Content-Type": "application/json"}
        with httpx.Client(timeout=45.0) as client:
            r = client.post(url, headers=headers, json=payload)
            data = r.json() if r.content else {}
        created.append(data.get("page") or {"error": data, "status_code": r.status_code, "title": title})
    return {"ok": True, "pages": created, "stub": not bool(cfg), "hitl_publish": True}


def get_shopify_tools() -> list:
    return [
        shopify_status,
        draft_product,
        update_product,
        list_products,
        list_orders,
        create_draft_order,
        shopify_domain_plan,
        shopify_bootstrap_checklist,
        shopify_create_policy_pages,
    ]
