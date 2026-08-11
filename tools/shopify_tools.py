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
from typing import Any, Dict, List, Optional, Tuple

import httpx

from tools.envutil import env

API_VERSION = env("SHOPIFY_API_VERSION", "2024-10") or "2024-10"
_TOKEN_CACHE = Path("tmp/secrets/shopify_token.json")


def _shop_host() -> Optional[str]:
    shop = (env("SHOPIFY_SHOP_NAME") or env("SHOPIFY_SHOP") or "").strip()
    if not shop:
        return None
    return shop if shop.endswith(".myshopify.com") else f"{shop}.myshopify.com"


def _load_cached_token(host: str) -> Optional[str]:
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


def _client_credentials_token(host: str) -> Optional[str]:
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


def _shop_config() -> Optional[Tuple[str, str]]:
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


def shopify_status() -> Dict[str, Any]:
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
        data = resp.json() if resp.content else {}
    product = data.get("product") if isinstance(data, dict) else None
    if product:
        product["stub"] = False
        return product
    return {"error": data, "status_code": resp.status_code, "stub": False}


def update_product(product_id: str, **fields: Any) -> Dict[str, Any]:
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
        data = resp.json() if resp.content else {}
    if isinstance(data, dict):
        data["stub"] = False
        data["status_code"] = resp.status_code
    return data


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
