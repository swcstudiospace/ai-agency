# Agency readiness — API keys, services, autonomy

**Org:** spectrumwebco · **Team:** SWC · **Project:** [AI Dropshipping Agency](https://linear.app/spectrumwebco/project/ai-dropshipping-agency-e61fc9b53cae)

Linear is **live** (issues dual-write to this project). Bootstrap: **SWC-60**, schedule track: **SWC-61**.

> **Security:** A Linear API key was pasted in chat. It is stored in local `.env` / `~/.config/hermes-linear/connector.env` (chmod 600). **Rotate that key in Linear** when convenient — chat logs are not a secret store. Never commit `.env`.

---

## How autonomy works (dropshipping loop)

Default autonomy is **L2**: agents research, draft, dual-write Linear, and prepare assets. **Humans** approve money (ads, supplier POs, large refunds).

```text
┌─────────────────────────────────────────────────────────────────┐
│  Hermes Agent (you / cron / Telegram)                           │
│  orchestrates via MCP → AgentOS :7777 · Drop :7788 · Bridge     │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
        1. DISCOVER  Product Scout + Parallel Web
           niches → candidates → unit economics score
                             ▼
        2. GATE      GO / TEST / NO-GO + kill criteria
           Linear issue per candidate (project dual-write)
                             ▼
        3. SUPPLY    Supplier Sourcer · QA Inspector
           landed cost, samples, CONDITIONAL/FAIL holds
                             ▼
        4. BUILD     Brand · Creative · Listing · Store · Catalog
           drafts only (Shopify live needs token)
                             ▼
        5. GROWTH    Media Buyer · Ads Creative Ops · Experiments
           campaign DRAFTS → HITL spend vault → optional live ads
                             ▼
        6. RUN OPS   Returns · Chargebacks · Fraud · Logistics · CX
           as orders appear (Shopify/tracking when connected)
                             ▼
        7. MEMORY    KIP/Anda brain + Hermes skills self-improve
           learnings dual-written; capsules exportable
```

### Frequent product finding (what you asked for)

| Mode | How |
|------|-----|
| **On demand** | `PYTHONPATH=. python -m scripts.autonomous_product_rank --niche "desk mobility" --processor ultra` |
| **Full draft lifecycle** | `python -m scripts.autonomous_lifecycle --niche "…" --processor ultra --top 3` |
| **Via Hermes MCP** | `run_product_rank` / `run_autonomous_lifecycle` on `ai-agency` or `drop` |
| **Scheduled** | Hermes cron → same command daily/hourly with rotating niches (see SWC-61) |

Outputs land in `tmp/runs/product_rank_*.{json,md}` and Linear issues on **AI Dropshipping Agency**.

HITL for ads (never unsupervised pay):

```text
attach_funding_source → request_spend_approval
  → human confirm_spend_approval(id, code, "I authorize…")
  → meta_launch / tiktok_launch (only with approval token)
```

---

## API keys & services matrix

### Required for “smart autonomous research” (minimum viable autonomy)

| Key / service | Env | Status now | Used for |
|---------------|-----|------------|----------|
| **Linear** | `LINEAR_API_KEY`, `LINEAR_TEAM_ID`, `LINEAR_TEAM_KEY=SWC`, `LINEAR_PROJECT_ID` | **LIVE** | Work log, dual-write issues |
| **Parallel Web** | `PARALLEL_API_KEY` | **SET** | Search / extract / deep task research |
| **xAI Grok** | `XAI_API_KEY` **or** SuperGrok OAuth device login | **Needed for agent reasoning** | All 30 Agno agents’ brains |
| **AgentOS** | local process `:7777` | **UP** | Agents / teams / workflows |
| **Drop gateway** | `:7788` | **UP** | Universal MCP + CoT×GoT + Linear tools |
| **Hermes bridge** | `:7790` | **UP** | Browser, skills, KIP from agents |
| **Anda nexus** | `:8091` `ANDA_NEXUS_URL` | preferred up | Shared KIP memory |

Without **xAI**, AgentOS loads but agent *runs* that call the model will fail or be empty. Fix: export a Grok API key or complete xAI OAuth on this host.

### Optional until you sell / advertise

| Key / service | Env | If missing |
|---------------|-----|------------|
| Shopify | `SHOPIFY_SHOP_NAME`, `SHOPIFY_ACCESS_TOKEN` | Store/catalog tools **stub** |
| Fal (UGC/images) | `FAL_KEY` | Creative media **stub** |
| Meta Ads | `META_ACCESS_TOKEN`, `META_AD_ACCOUNT_ID` | Drafts local; no remote ads |
| TikTok Ads | `TIKTOK_ACCESS_TOKEN`, `TIKTOK_ADVERTISER_ID` | Same |
| 17track | `SEVENTEENTRACK_TOKEN` | Tracking **stub** |
| ICP / ic-oss | `KIP_ICP_MODE=canister`, `IC_OSS_ENDPOINT`, … | Local capsules only |
| Postgres analytics | `AGENCY_ANALYTICS_DSN` | SQLite analytics OK |

### Local tokens (already generated on this box)

| Env | Role |
|-----|------|
| `DROP_MCP_TOKEN` | Auth for Drop MCP if not localhost-exempt |
| `HERMES_BRIDGE_TOKEN` | Optional bridge auth |
| `DROP_*` / `HERMES_BRIDGE_*` ports | Loopback services |

---

## What’s implemented vs still stubby

| Area | Implemented | Gaps |
|------|-------------|------|
| 30 agents + personas + ops tools | Yes | Need xAI to *think* |
| Product rank / lifecycle scripts | Yes | Needs Parallel + xAI |
| Linear dual-write → SWC project | **Yes (verified SWC-60/61)** | Kanban mirror best-effort |
| HITL spend vault | Yes (local codes) | No bank/crypto until you attach |
| Meta/TikTok | Draft + optional paused create | Live spend gated + keys |
| Shopify | Tool surface | No store token → stubs |
| Fal UGC | Tool surface | No `FAL_KEY` → stubs |
| KIP/Anda memory | Local + dual-write | On-chain optional |
| Agency Cockpit UI | Mock GenUI PWA/desktop | Not yet streaming live AgentOS events |
| Recurring discovery cron | Documented (SWC-61) | Not enabled until you pick cadence/niches |

---

## Recommended next steps (in order)

1. **Rotate Linear API key** (pasted in chat) and update `.env` + `connector.env`.
2. **Set xAI** so agents can run: `XAI_API_KEY=...` or OAuth login used by `tools/xai_model.py`.
3. **Smoke product rank**  
   `PYTHONPATH=. python -m scripts.autonomous_product_rank --niche "desk mobility" --processor ultra`
4. **Enable schedule** (Hermes cron daily) for 1–3 niches you care about → closes SWC-61.
5. When ready to sell: Shopify token → Catalog/Store agents go live.
6. When ready to advertise: Meta/TikTok + HITL vault confirm path only.

---

## Quick health commands

```bash
curl -s http://127.0.0.1:7777/health
curl -s http://127.0.0.1:7788/health
curl -s http://127.0.0.1:7790/health
cd /root/src/repos/ai-agency && source .venv/bin/activate
PYTHONPATH=. python -c "from tools.linear_tools import linear_status; print(linear_status())"
```

Linear project URL: https://linear.app/spectrumwebco/project/ai-dropshipping-agency-e61fc9b53cae
