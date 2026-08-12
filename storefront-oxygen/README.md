# ego.engineer storefront (Hydrogen / Oxygen ready)

Headless commerce scaffold for **ego.engineer**, backed by Shopify (AI Dropshipping Agency).

## Stack path

| Phase | What |
|-------|------|
| Now | This Vite + React SPA talks Storefront API (demo catalog fallback) |
| Next | Promote to full **Shopify Hydrogen** (`npm create @shopify/hydrogen@latest`) and deploy on **Oxygen** |
| Domain | Attach `ego.engineer` / `www` in Oxygen + Shopify Domains |

## Local

```bash
cd storefront-oxygen
cp .env.example .env   # add Storefront API token when ready
npm install
npm run dev            # http://127.0.0.1:3456
```

## Env

```bash
PUBLIC_STORE_DOMAIN=aidropshipping.myshopify.com
PUBLIC_STOREFRONT_API_TOKEN=          # Admin → Headless / custom app Storefront API
PUBLIC_STOREFRONT_API_VERSION=2024-10
PUBLIC_PRIMARY_DOMAIN=ego.engineer
PUBLIC_BRAND_NAME=ego.engineer
```

## Oxygen deploy (when ready)

1. Convert or regenerate with official Hydrogen template (preferred for RSC/Oxygen)
2. `npm run build` + `shopify hydrogen deploy` (Shopify CLI)
3. Custom domain: Oxygen dashboard → `ego.engineer`
4. DNS at registrar (see agency `shopify_domain_plan`)

## Agency integration

- Draft products via `tools/shopify_tools.draft_product` (Admin API)
- Storefront reads **published** catalog via Storefront API token
- Keep products `draft` until HITL publish
