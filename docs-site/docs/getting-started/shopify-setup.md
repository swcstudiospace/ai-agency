# Shopify setup

Store display name: **AI Dropshipping Agency**

Configured myshopify host (best effort): `aidropshipping.myshopify.com`

## Client credentials

Shopify Dev Dashboard apps exchange Client ID + Secret for a 24h Admin token:

```text
POST https://{shop}.myshopify.com/admin/oauth/access_token
grant_type=client_credentials
```

Agency code does this in `tools/shopify_tools.py`.

## Required env

```bash
SHOPIFY_SHOP_NAME=aidropshipping
SHOPIFY_SHOP_DISPLAY_NAME="AI Dropshipping Agency"
SHOPIFY_CLIENT_ID=...
SHOPIFY_CLIENT_SECRET=...
SHOPIFY_API_VERSION=2024-10
```

## Install checklist

1. Dev Dashboard app scopes: read/write products, draft orders, orders as needed
2. **Install the app on the AI Dropshipping Agency store**
3. Confirm subdomain matches `SHOPIFY_SHOP_NAME`
4. Verify:

```bash
PYTHONPATH=. python -c "from tools.shopify_tools import shopify_status; print(shopify_status())"
```

Expect live mode. Draft products stay status=draft under L2.
