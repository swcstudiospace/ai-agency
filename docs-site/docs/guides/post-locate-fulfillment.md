# Post-locate: outreach and shipping

After locate, do **both**: contact top sellers for samples, and design the order→ship pipeline.

## Commands

```bash
PYTHONPATH=. python -m scripts.autonomous_post_locate --top-suppliers 2
PYTHONPATH=. python -m scripts.autonomous_post_locate --open-gmail
```

Gmail compose opens via Hermes bridge — you send manually.

## Headless storefront

`storefront-oxygen/` targets **ego.engineer** on Shopify Hydrogen/Oxygen.

See monorepo `docs/POST_LOCATE_AND_FULFILLMENT.md`.
