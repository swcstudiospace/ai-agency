# AI Dropshipping Agency

[![CI](https://github.com/swcstudiospace/ai-agency/actions/workflows/ci.yml/badge.svg)](https://github.com/swcstudiospace/ai-agency/actions/workflows/ci.yml)
[![Backend](https://github.com/swcstudiospace/ai-agency/actions/workflows/ci-backend.yml/badge.svg)](https://github.com/swcstudiospace/ai-agency/actions/workflows/ci-backend.yml)
[![Security](https://github.com/swcstudiospace/ai-agency/actions/workflows/ci-security.yml/badge.svg)](https://github.com/swcstudiospace/ai-agency/actions/workflows/ci-security.yml)

Enterprise multi-agent dropshipping control plane: **Hermes** orchestrates **Agno AgentOS**, **SuperGrok**, **Parallel** research, **Shopify** drafts, **PromptWise/Fal** UGC, and **HITL** ads.

| | |
|--|--|
| **GitHub** | https://github.com/swcstudiospace/ai-agency |
| **Linear** | spectrumwebco · SWC · AI Dropshipping Agency |
| **Brand domain** | **ego.engineer** (headless + DNS plan) |
| **Shopify store** | AI Dropshipping Agency (`aidropshipping.myshopify.com`) |
| **Scale** | **30** agents · **12** teams · **12** workflows |

> **Living README policy:** every feature that changes ports, counts, scripts, env, or operator flow **must** update this file in the same PR. CI enforces it via `python -m scripts.check_readme_freshness`.

---

## What it does

```text
Discover niches → Rank GO/TEST → LOCATE suppliers → Outreach + shipping plan
       → Creatives (PromptWise/Fal) → Shopify DRAFT → Ad DRAFTS → HITL spend → Ops
```

Default autonomy **L2**: research and draft aggressively; **humans** approve money, sample payments, and live publish.

---

## Quick start

```bash
cd ai-agency
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp -n .env.example .env
# PARALLEL_API_KEY required; SuperGrok via OAuth or XAI_API_KEY
python -m tools.xai_oauth_pkce login
./scripts/start_agentos.sh          # http://127.0.0.1:7777 + /mcp
```

### Product pipeline

```bash
export PYTHONPATH=. PYTHONUNBUFFERED=1 AGENCY_GROK_MODEL=grok-4.5

# 1) Discover + rank
python -m scripts.autonomous_product_rank \
  --niche "desk mobility for remote workers" --processor ultra

# 2) Locate suppliers (where to buy)
python -m scripts.autonomous_product_locate --top 3 --processor pro

# 3) Post-locate: seller email drafts + shipping pipeline (HITL send)
python -m scripts.autonomous_post_locate --top-suppliers 2
python -m scripts.autonomous_post_locate --open-gmail   # Gmail compose via bridge

# Full draft lifecycle / E2E scorecard
python -m scripts.autonomous_lifecycle --niche "desk mobility" --processor pro --top 3
E2E_SKIP_RESEARCH=1 python -m scripts.e2e_agency_run
```

### Local CI parity (SOTA — not smoke-only)

```bash
export PYTHONPATH=. XAI_API_KEY=missing-ci-placeholder LINEAR_GITHUB_LINK=0
export AGENCY_DISABLE_HERMES_BRIDGE=1 AGENCY_DISABLE_ANDA_BRAIN=1

ruff check agents app tools teams workflows scripts tests evals
pytest tests/ --cov=tools --cov-report=term-missing
python -m evals.run_agent_evals
python -m scripts.check_readme_freshness
```

---

## Control planes

| Service | Port | Notes |
|---------|-----:|-------|
| AgentOS | **7777** | Agents / teams / workflows / MCP `/mcp` |
| Drop gateway | **7788** | MCP+ACP, Linear, CoT×GoT |
| Hermes bridge | **7790** | Browser, skills, KIP for Agno |
| Anda nexus | **8091** | Shared KIP brain |
| Cockpit UI | **1420** | `agency-cockpit` Vite dev |
| Docs site | **3400** | `docs-site` Docusaurus |
| Storefront | **3456** | `storefront-oxygen` (ego.engineer) |

```bash
systemctl status drop-gateway hermes-bridge anda-nexus
hermes mcp add ai-agency --url 'http://127.0.0.1:7777/mcp'
hermes mcp add drop --url 'http://127.0.0.1:7788/mcp'
```

---

## CI/CD

**SOTA multi-gate pipeline** (not ad-hoc smoke):

| Workflow | Gates |
|----------|--------|
| `ci.yml` | Umbrella → backend + cockpit + docs + storefront + security + **All CI gates green** |
| `ci-backend.yml` | **Ruff** · **Pytest + coverage** · **Agent evals (30/12/12)** · **Living README** |
| `ci-cockpit.yml` | Vite PWA production build (+ optional Tauri) |
| `ci-docs.yml` | Docusaurus production build |
| `ci-storefront.yml` | Oxygen/ego.engineer Vite build |
| `ci-security.yml` | Gitleaks secret scan · pip-audit · npm audit |
| `cd-docs.yml` | Deploy docs-site → GitHub Pages on main |

Details: [`docs/CI_CD.md`](docs/CI_CD.md)

Branch protection: require status **All CI gates green**.

---

## Documentation

| Path | Content |
|------|---------|
| **`docs-site/`** | Themed Docusaurus (`npm start` → :3400) |
| `docs/CI_CD.md` | Full CI/CD map |
| `docs/PRODUCT_LOCATE.md` | Discover + locate |
| `docs/POST_LOCATE_AND_FULFILLMENT.md` | Outreach + shipping |
| `docs/AUTONOMY_AND_KEYS.md` | Keys matrix + L2 |
| `storefront-oxygen/README.md` | Headless Hydrogen/Oxygen path |
| `agency-cockpit/PACKAGING.md` | Desktop/mobile packaging |

```bash
cd docs-site && npm install && npm start
cd storefront-oxygen && NODE_ENV=development npm install --include=dev && npm run dev
cd agency-cockpit && npm install && npm run dev
```

---

## Shopify + ego.engineer

```bash
SHOPIFY_SHOP_NAME=aidropshipping
SHOPIFY_SHOP_DISPLAY_NAME="AI Dropshipping Agency"
SHOPIFY_CLIENT_ID=...
SHOPIFY_CLIENT_SECRET=...
AGENCY_PRIMARY_DOMAIN=ego.engineer
```

- Admin API: client credentials → 24h token (`tools/shopify_tools.py`)
- App must be **installed** on the shop before live drafts
- Domain DNS plan: `shopify_domain_plan` / Settings → Domains
- Headless storefront: `storefront-oxygen/` (Storefront API token)

---

## Cron

Hermes job **`agency-product-discovery-6x`** · `0 */4 * * *` UTC (6×/day):

`rank → locate → post_locate` (no spend, no auto-email send).

---

## Repo layout

```text
agents/ profiles + thin modules     prompts/ SOUL/SYSTEM/OUTPUT/EXAMPLES
teams/  12 coordinate teams         workflows/ 12 pipelines
tools/  Parallel, Shopify, Linear, outreach, shipping, PromptWise, Fal, spend…
scripts/ rank, locate, post_locate, lifecycle, e2e, check_readme_freshness
tests/   pytest unit + registry     evals/ structural agent evals
drop_server/  hermes_bridge/  kip_memory/
agency-cockpit/   docs-site/   storefront-oxygen/
.github/workflows/  SOTA CI/CD
```

---

## Safety

- No unsupervised ad spend or supplier payment  
- Shopify products default to **draft**  
- Outreach emails are **HITL** (Gmail compose — human clicks Send)  
- Secrets only in `.env` (gitignored); never commit tokens  
- Rotate any credential pasted in chat  

---

## Maintainers: keep README current

When you ship a change, update this README in the **same commit** if you touched:

1. Agent/team/workflow **counts**  
2. New **scripts** or pipeline stages  
3. **Ports**, domains, or env vars operators need  
4. CI/CD workflows or quality gates  

CI fails the PR if `scripts/check_readme_freshness.py` detects drift.
