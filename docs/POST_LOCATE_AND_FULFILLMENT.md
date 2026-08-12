# Post-locate: contact sellers + shipping pipeline

## Answer: do both

After **product locate**, the agency needs:

| Track | Why | Automation |
|-------|-----|------------|
| **Contact seller** | Sample + dropship terms, MOQ, branding | `tools/seller_outreach_tools.py` + Gmail compose (HITL send) |
| **Shipping pipeline** | Paid orders must route to fulfillment | `tools/shipping_pipeline_tools.py` + Shopify shipping/policies |

Classic dropshipping = supplier ships each order. Platforms (CJ/Doba) reduce email; factories need outreach.

## Commands

```bash
# After locate artifact exists
PYTHONPATH=. python -m scripts.autonomous_post_locate --top-suppliers 2

# Also open first email in Gmail via Hermes bridge browser (you login once)
PYTHONPATH=. python -m scripts.autonomous_post_locate --open-gmail
```

Artifacts:
- `tmp/outreach/email_*.md` — ready-to-send sample inquiries
- `tmp/shipping/pipeline_*.json` — lanes, SLA, webhooks
- `tmp/runs/post_locate_*.{json,md}`
- Linear `[Post-locate] …`

## Gmail

1. Ensure hermes-bridge is up (`:7790`)
2. First time: log into Gmail in the bridge browser profile when compose opens
3. Review body → click **Send** yourself (agency never auto-sends)

## Shipping modes

- `supplier_dropship` (default) — email/API push per order  
- `platform_cj` — CJ/Doba app auto-fulfill  
- `stock_3pl` — bulk inbound later  
- `hybrid` — soft launch DS → 3PL after velocity  

## Shopify bare account → ego.engineer

```bash
PYTHONPATH=. python -c "from tools.shopify_tools import shopify_bootstrap_checklist; import json; print(json.dumps(shopify_bootstrap_checklist(), indent=2)[:2000])"
```

1. Install Dev Dashboard app on shop (scopes for products/orders/fulfillments)  
2. Confirm `SHOPIFY_SHOP_NAME`  
3. Payments test mode  
4. Shipping profiles + policies  
5. Connect domain **ego.engineer** (DNS at registrar — see `shopify_domain_plan`)  
6. Storefront API token for headless  
7. Draft product → test order  

## Headless Oxygen

Scaffold: `storefront-oxygen/` (Vite React, Storefront API ready).  
Promote to full Hydrogen + `shopify hydrogen deploy` when ready. Domain: ego.engineer.

## Cron (6×/day)

Hermes job `agency-product-discovery-6x` · `0 */4 * * *` UTC  
rank → locate → post_locate (no spend).
