# Drop Autonogrammer — Hybrid MCP + ACP Gateway

**Public URL (when DNS/TLS live):** `https://drop.autonogrammer.ai`  
**Local:** `http://127.0.0.1:7788`

## What it is

A **universal control-plane gateway** for the AI Dropshipping Agency:

| Protocol | Path / entry | SDK |
|----------|--------------|-----|
| **MCP** Streamable HTTP | `/mcp` | Python `mcp` FastMCP |
| **ACP** HTTP bridge | `/acp/v1/*` | Session + prompt API |
| **ACP** stdio | `python -m drop_server.acp_agent` | `agent-client-protocol` |
| Health / card | `/health`, `/` | Starlette |

### Built-in logic

- **CoT × GoT** (`drop_server/reasoning/cot_got.py`) — hybrid chain + branching graph  
  - Explicit: `reason_cot_got`  
  - **Auto-triggered** on product/lifecycle/spend/complexity goals  
- **Linear** first-class tools (dual-write SPE + Kanban)  
- **Agency bridges** — lifecycle, product rank, integrations, HITL spend request  
- **AgentOS** proxy helper  

Hermes already has catalog **Linear MCP** enabled separately; this gateway embeds Linear so **one URL** is enough for external agents.

## Quick start

```bash
cd /root/src/repos/ai-agency
source .venv/bin/activate
# DROP_MCP_TOKEN should be in .env
./scripts/start_drop_gateway.sh
# or: systemctl enable --now drop-gateway
```

```bash
curl -s http://127.0.0.1:7788/health | jq .
curl -s http://127.0.0.1:7788/ | jq .
```

### Hermes MCP client

```bash
hermes mcp add drop --url http://127.0.0.1:7788/mcp --connect-timeout 60
hermes config set mcp_servers.drop.timeout 3600
# optional remote:
# hermes mcp add drop-public --url https://drop.autonogrammer.ai/mcp
# hermes config set mcp_servers.drop-public.headers.Authorization "Bearer $DROP_MCP_TOKEN"
```

Restart Hermes TUI/gateway after add so `mcp_drop_*` tools appear.

### ACP stdio (Zed / editors)

```bash
python -m drop_server.acp_agent
# or see GET /acp/stdio-info for settings.json snippet
```

### ACP HTTP

```bash
curl -s -X POST http://127.0.0.1:7788/acp/v1/session \
  -H 'content-type: application/json' \
  -d '{"goal":"find products and plan launch with budget"}' | jq .

curl -s -X POST http://127.0.0.1:7788/acp/v1/session/SESSION/prompt \
  -H 'content-type: application/json' \
  -d '{"prompt":"linear status and open issues"}' | jq .
```

## DNS + TLS (public)

1. Point `drop.autonogrammer.ai` **A record → `187.77.130.10`** (this VPS).  
   Currently `drop.autonogrammer.ai` is NXDOMAIN; apex `autonogrammer.ai` points elsewhere (`2.57.91.91`).
2. Install nginx site:
   ```bash
   cp drop_server/deploy/nginx-drop.autonogrammer.ai.conf \
      /etc/nginx/sites-available/drop.autonogrammer.ai
   # Temporarily comment the TLS server block until cert exists
   ln -sf /etc/nginx/sites-available/drop.autonogrammer.ai /etc/nginx/sites-enabled/
   nginx -t && systemctl reload nginx
   certbot certonly --webroot -w /var/www/letsencrypt -d drop.autonogrammer.ai
   # Uncomment TLS block, reload nginx
   ```
3. systemd:
   ```bash
   cp drop_server/deploy/drop-gateway.service /etc/systemd/system/
   systemctl daemon-reload
   systemctl enable --now drop-gateway
   ```

## Auth

- `DROP_MCP_TOKEN` bearer (or `X-Drop-Token`)
- Localhost exempt by default (`DROP_MCP_ALLOW_LOCALHOST=1`)
- Set `DROP_MCP_REQUIRE_AUTH=0` only for trusted private nets

## MCP tool surface (selected)

| Tool | Purpose |
|------|---------|
| `reason_cot_got` | Explicit CoT×GoT graph |
| `drop_health` / `drop_roster` | Gateway + agency map |
| `linear_*` | status, create, update, list, comment |
| `agency_run_lifecycle` | Full autonomous pipeline |
| `agency_product_rank` | Parallel rank |
| `spend_request_approval` | HITL spend (no confirm) |
| `agentos_run_agent` | Proxy to :7777 |

## Layout

```text
drop_server/
  main.py              # Starlette hybrid app
  mcp_app.py           # FastMCP tools
  acp_agent.py         # ACP stdio agent
  reasoning/cot_got.py # CoT × GoT engine
  deploy/              # nginx + systemd
```
