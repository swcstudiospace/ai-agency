# Product discovery and locate

## How do we find products?

The agency automates **two** linked stages:

### 1) Discover (what to sell)

```bash
PYTHONPATH=. python -m scripts.autonomous_product_rank \
  --niche "YOUR NICHE" --processor ultra
```

- Parallel Search scans demand/competitors  
- Parallel Task returns structured candidates  
- Unit economics → **GO / TEST / NO-GO**  
- Linear dual-write + report under `tmp/runs/product_rank_*`  
- Bi-daily Hermes cron rotates niches  

### 2) Locate (where to buy)

```bash
PYTHONPATH=. python -m scripts.autonomous_product_locate --top 3 --processor pro
```

- Loads latest GO/TEST from product rank (or `--product "…"` / `--rank-first`)  
- Parallel Search for suppliers (Alibaba, wholesale, CJ-style platforms)  
- Parallel Task builds shortlist: unit cost, ship, MOQ, lead time, red flags  
- `score_supplier` 0–100 + logistics profile  
- Linear `[Locate] …` issues + GitHub `ai-agency`  
- Artifacts: `tmp/runs/product_locate_*.{json,md}`  

### Tools

| Tool | Module |
|------|--------|
| `locate_suppliers_for_product` | `tools/supplier_tools.py` |
| `locate_product_sources_batch` | same |
| `score_supplier` | same |

### Workflow

AgentOS: **Product Discovery & Locate**  
`workflows/product_discovery_locate.py` (registered in `app/main.py`)

### HITL

Locate is **research**. Sample buys and bulk POs require human approval.

## Suggested operating loop

```text
cron / Hermes
  → product_rank (discover)
  → product_locate (suppliers)
  → human picks top supplier + approves sample
  → QA Inspector
  → creative + Shopify draft
  → ads draft + spend HITL
```
