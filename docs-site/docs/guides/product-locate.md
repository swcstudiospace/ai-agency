# Product locate

After rank: **who supplies this SKU, at what landed cost?**

## Commands

```bash
PYTHONPATH=. python -m scripts.autonomous_product_locate --top 3 --processor pro

PYTHONPATH=. python -m scripts.autonomous_product_locate \
  --product "Fold-Flat Adjustable Aluminum Laptop Stand"

PYTHONPATH=. python -m scripts.autonomous_product_locate \
  --rank-first --niche "desk mobility" --processor pro
```

## Pipeline

1. Parallel Search (Alibaba / wholesale / CJ-style)
2. Parallel Task supplier shortlist
3. score_supplier 0-100
4. Logistics profile
5. Linear `[Locate]` issue + GitHub ai-agency
6. Artifacts `tmp/runs/product_locate_*.{json,md}`

## Tools

- `locate_suppliers_for_product`
- `locate_product_sources_batch`

Workflow: **Product Discovery and Locate**

HITL: locate is research only — no unsupervised sample/PO payments.
