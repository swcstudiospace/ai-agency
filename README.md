# AI Dropshipping Agency

End-to-end multi-agent dropshipping agency on **Agno AgentOS**, **Grok (xAI)**, and **Parallel Web Systems**.

## Hermes control plane (AgentOS MCP)

Hermes is the top orchestrator. AgentOS exposes MCP at **`http://127.0.0.1:7777/mcp`**.

```bash
# 1) Start Agency (REST + MCP)
./scripts/start_agentos.sh
# or: source .venv/bin/activate && PYTHONPATH=. python -m app.main

# 2) Register once in Hermes
printf 'n\nY\n' | hermes mcp add ai-agency --url 'http://127.0.0.1:7777/mcp' --connect-timeout 90
hermes config set mcp_servers.ai-agency.timeout 3600
hermes mcp test ai-agency

# 3) New Hermes session — tools appear as mcp_ai_agency_*
```

Skill: **`ai-dropshipping-agency-mcp`** (load when controlling the agency from Hermes).

MCP surface:

- Built-ins: `get_agentos_config`, `run_agent`, `run_team`, `run_workflow`, `continue_run`, `cancel_run`, `get_sessions`, `get_session_runs`
- Custom: `agency_health`, `agency_roster`, `run_product_rank`, `list_product_rank_reports`, `read_product_rank_report`

## Quick start

```bash
cd ~/src/repos/ai-agency
source .venv/bin/activate
pip install -r requirements.txt
cp -n .env.example .env
# PARALLEL_API_KEY required; XAI via Hermes OAuth or XAI_API_KEY
python -m tools.xai_oauth_pkce login   # optional if using SuperGrok device-code
./scripts/start_agentos.sh             # http://localhost:7777 + /mcp
```

## Agents (18)

| Agent | Owns |
|-------|------|
| Hermes Ops | Orchestration, priorities, Linear dual-write |
| Product Scout | Opportunity discovery & scoring |
| Supplier Sourcer | Vetting, landed cost, backups |
| Pricing Strategist | Price, bundles, AOV, CM |
| Brand Strategist | Positioning & voice |
| Creative Director | UGC concepts & briefs |
| Listing Specialist | Shopify PDPs |
| SEO Content | Organic / content hubs |
| Store Builder | Store IA & UX |
| Compliance Officer | Claims & ads policy gate |
| Growth Media Buyer | Paid social ROAS |
| Influencer Manager | Creator seeding & UGC rights |
| Email CRM | Lifecycle flows |
| Customer Success | Macros, returns, reputation |
| Fulfillment Ops | SLAs & tracking |
| Inventory Planner | Reorder & stock risk |
| Analyst | Scorecards & cost control |
| Finance Controller | Budgets, MER, runway |

## Teams (7)

Agency Director · Research · Supply Chain · Creative · Store Ops · Growth · Retention

## Workflows (5)

1. **Full Product Lifecycle** — research → supply → creative → store/compliance → launch → retention  
2. **Marketing Launch** — creatives → compliance gate → campaigns  
3. **Supplier Onboarding** — shortlist → vet → inventory policy  
4. **Post Purchase Ops** — fulfillment exceptions → CX/retention  
5. **Weekly Performance Review** — growth + CX + supply → leadership  

## Skills (14 Agno packs)

Loaded via `tools/skills_loader.py` (`LocalSkills`) into agents/teams:

- **agency/** product-scoring, unit-economics, supplier-vetting, roas-guardrails, autonomy-levels, linear-ops  
- **marketing/** ugc-hooks, creative-briefing, listing-cro, paid-social-structure, email-retention  
- **ops/** fulfillment-playbook, customer-support-macros, compliance-ads-claims  

Agents use progressive disclosure: `get_skill_instructions` / `get_skill_reference`.

## Tools

- `parallel_tools` — Search, Extract, Task, Entity, Monitor  
- `xai_oauth_pkce` / `xai_model` — SuperGrok device-code or API key  
- `economics_tools` — CM & price ladder  
- `supplier_tools` — supplier scoring  
- `shopify_tools` — draft products (stub without creds)  
- `linear_tools` — issues (stub without creds)  

## Agent architecture (SOTA stack)

Each of the 18 agents is thin Python wiring over:

1. **Persona markdown** — `prompts/<agent>/{SOUL,SYSTEM,OUTPUT,EXAMPLES}.md`
2. **Scoped skills** — only relevant packs from `skills/{agency,marketing,ops,agents}/`
3. **Role toolbelts** — `tools/toolbelts.py` (not everyone gets full Parallel)
4. **Pydantic output schemas** — `agents/schemas.py` for typed handoffs
5. **History + autonomy hooks** — conversational roles keep history; L2 tool guardrails

```bash
# Structural evals (no LLM required)
PYTHONPATH=. python -m evals.run_agent_evals
```

Factory: `agents/_factory.py` · Profiles: `agents/profiles.py` · Loader: `agents/prompt_loader.py`

## Enterprise tools & HITL ads

See **[docs/ENTERPRISE_TOOLS.md](docs/ENTERPRISE_TOOLS.md)** for the full lifecycle map (Parallel, Linear, Fal UGC, Shopify, Meta/TikTok, logistics, spend vault).

```bash
# End-to-end autonomous (no payments / no live ads)
PYTHONPATH=. python -m scripts.autonomous_lifecycle --niche "desk mobility" --processor ultra --top 3

# HITL spend after drafts exist
# 1) attach_funding_source / attach_agency_funding_source
# 2) request_spend_approval
# 3) human confirm_spend_approval(... "I authorize...")
# 4) meta_launch_campaign / tiktok_launch_campaign
```

## Drop universal MCP + ACP gateway

Hybrid control plane at **`drop.autonogrammer.ai`** (local `:7788`):

```bash
systemctl status drop-gateway
curl -s http://127.0.0.1:7788/health
# Hermes: mcp_servers.drop → http://127.0.0.1:7788/mcp
```

See `drop_server/README.md` for MCP tools, ACP stdio/HTTP, CoT×GoT, nginx/TLS.

## Hermes reverse bridge + KIP memory

Agno agents call Hermes-class tools via **`:7790`** (`hermes-bridge.service`):

- Browser (Playwright), skills self-improve proposals, MEMORY.md
- Shared **KIP** graph (`kip_memory/`) with ICP capsule export
- See `docs/HERMES_AGNO_BRIDGE.md` and `hermes_bridge/README.md`

## Scale (current)
**30 agents · 12 teams · 10 workflows** — see `docs/AGENCY_EXPANSION_30.md`.

## Agency Cockpit (UI mock)
React + Tauri v2 generative UI: `agency-cockpit/` — `npm run dev` → http://127.0.0.1:1420

## Keys & autonomy
See `docs/AUTONOMY_AND_KEYS.md` (Linear SWC · spectrumwebco).
