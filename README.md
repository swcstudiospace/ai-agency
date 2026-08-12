# AI Dropshipping Agency

Enterprise multi-agent dropshipping control plane: **Hermes** orchestrates **Agno AgentOS**, **SuperGrok**, **Parallel** research, **Shopify** drafts, **PromptWise/Fal** UGC, and **HITL** ads.

**GitHub:** https://github.com/swcstudiospace/ai-agency  
**Linear:** spectrumwebco · SWC · [AI Dropshipping Agency](https://linear.app/spectrumwebco/project/ai-dropshipping-agency-e61fc9b53cae)  
**Docs site:** `docs-site/` (Docusaurus) · monorepo guides in `docs/`

---

## What it does

```text
Discover niches  →  Rank GO/TEST  →  LOCATE suppliers  →  Creatives
       →  Shopify DRAFT  →  Ad DRAFTS  →  HITL spend  →  Ops
```

| Scale | Count |
|-------|------:|
| Agents | **30** |
| Teams | **12** |
| Workflows | **11** |

Default autonomy **L2**: research and draft aggressively; **humans** approve money and live publish.

---

## Quick start

```bash
cd ai-agency
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp -n .env.example .env
# PARALLEL_API_KEY required; SuperGrok via OAuth or XAI_API_KEY
python -m tools.xai_oauth_pkce login
./scripts/start_agentos.sh          # http://127.0.0.1:7777 + /mcp
```

### Discover products

```bash
PYTHONPATH=. python -m scripts.autonomous_product_rank \
  --niche "desk mobility for remote workers" --processor ultra
```

### Locate suppliers (next step after rank)

```bash
PYTHONPATH=. python -m scripts.autonomous_product_locate --top 3 --processor pro
# or single SKU:
PYTHONPATH=. python -m scripts.autonomous_product_locate \
  --product "Fold-Flat Adjustable Aluminum Laptop Stand"
```


### Post-locate (outreach + shipping)

```bash
PYTHONPATH=. python -m scripts.autonomous_post_locate --top-suppliers 2
# optional Gmail compose (HITL send):
PYTHONPATH=. python -m scripts.autonomous_post_locate --open-gmail
```

Contact top sellers **and** set up shipping/order routing. Domain: **ego.engineer**. Headless: `storefront-oxygen/`.

Discovery cron: **every 4 hours** (`0 */4 * * *` UTC) — rank → locate → post_locate.

### Full draft lifecycle / E2E smoke

```bash
PYTHONPATH=. python -m scripts.autonomous_lifecycle --niche "desk mobility" --processor pro --top 3
PYTHONPATH=. E2E_SKIP_RESEARCH=1 python -m scripts.e2e_agency_run
```

---

## Control planes

| Service | Port | Notes |
|---------|-----:|-------|
| AgentOS | 7777 | Agents / teams / workflows / MCP |
| Drop gateway | 7788 | MCP+ACP, Linear, CoT×GoT |
| Hermes bridge | 7790 | Browser, skills, KIP for Agno |
| Anda nexus | 8091 | Shared KIP brain |
| Cockpit UI | 1420 | `agency-cockpit` Vite dev |
| Docs site | 3400 | `docs-site` Docusaurus |

```bash
systemctl status drop-gateway hermes-bridge anda-nexus
hermes mcp add ai-agency --url 'http://127.0.0.1:7777/mcp'
hermes mcp add drop --url 'http://127.0.0.1:7788/mcp'
```

---

## How product finding works

1. **Discover** — Parallel Search + Task builds candidate SKUs; unit economics → GO/TEST/NO-GO  
2. **Locate** — Parallel finds supplier leads (Alibaba/CJ/wholesale style), scores MOQ/landed cost  
3. **Dual-write** — Linear SWC issues + GitHub `ai-agency` links  
4. **Create** — PromptWise/Fal UGC briefs; Shopify **draft** products  
5. **Grow** — Meta/TikTok campaign **drafts**; spend vault HITL before live ads  

Bi-daily discovery cron: `agency-product-discovery-bidaily` (08:00 + 20:00 UTC).

Deep guides: [docs-site](docs-site/) · `docs/PRODUCT_LOCATE.md` · `docs/AUTONOMY_AND_KEYS.md`

---

## Shopify (AI Dropshipping Agency store)

```bash
SHOPIFY_SHOP_NAME=aidropshipping          # myshopify subdomain
SHOPIFY_SHOP_DISPLAY_NAME="AI Dropshipping Agency"
SHOPIFY_CLIENT_ID=...
SHOPIFY_CLIENT_SECRET=...                 # Dev Dashboard secret
```

App must be **installed** on the shop; tokens are minted via client credentials (24h).  
See `docs-site/docs/getting-started/shopify-setup.md`.

---

## Documentation

| Path | Content |
|------|---------|
| **`docs-site/`** | Themed **Docusaurus** site (`npm start` → :3400) |
| `docs/` | Operator markdown (autonomy, bridge, CI, enterprise tools) |
| `agency-cockpit/README.md` | Desktop/web UI packaging |

```bash
cd docs-site && npm install && npm start
cd docs-site && npm run build    # static build/
```

---

## Repo layout

```text
agents/ profiles + thin modules     prompts/ SOUL/SYSTEM/OUTPUT/EXAMPLES
teams/  12 coordinate teams         workflows/ 11 pipelines
tools/  Parallel, Shopify, Linear, PromptWise, Fal, spend, ops…
scripts/ rank, locate, lifecycle, e2e
drop_server/  hermes_bridge/  kip_memory/
agency-cockpit/   docs-site/
```

---

## CI

GitHub Actions: backend structure smoke + cockpit PWA build on every push.  
https://github.com/swcstudiospace/ai-agency/actions

---

## Safety

- No unsupervised ad spend or supplier payment  
- Shopify products default to **draft**  
- Secrets only in `.env` (gitignored)  
- Rotate any credential pasted in chat
