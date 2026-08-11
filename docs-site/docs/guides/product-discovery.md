# Product discovery

## How we find products

Discovery is automated end-to-end.

```text
Niche / seed
   -> Parallel Search
   -> Parallel Task pro/ultra (structured candidates)
   -> Unit economics (CM%, CPA)
   -> GO / TEST / NO-GO
   -> Linear dual-write
   -> LOCATE suppliers
```

## Commands

```bash
PYTHONPATH=. python -m scripts.autonomous_product_rank \
  --niche "kitchen organizers under $40" --processor ultra
```

Bi-daily cron: `agency-product-discovery-bidaily` at 08:00 and 20:00 UTC.

## Quality gates

| Signal | Target |
|--------|--------|
| CM after ~$18 CPA | 25-30%+ for GO |
| Ship risk | low/medium weight |
| Angle | demo-friendly UGC |
| Compliance | no disease claims |
