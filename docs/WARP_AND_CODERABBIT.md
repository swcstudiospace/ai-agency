# Warp / Oz bottom layer + CodeRabbit

## Stack

```text
Hermes Agent          (top orchestrator — MCP client)
        │
        ▼
Agno AgentOS          (30 agents · 12 teams · 12 workflows)
  tools: warp_*  coderabbit_*
        │
        ▼
Warp Oz CLI (`oz`)    (bottom — agent run / run-cloud / shell offload)
Warp TUI (`warp`)     (optional conversation agent)
CodeRabbit CLI (`cr`) (review gate in CI + agent tool)
```

## Agent access (automatic)

`agents/_factory.py` attaches toolbelts **`warp`** + **`coderabbit`** to **every** agent
(unless `AGENCY_DISABLE_WARP=1` / `AGENCY_DISABLE_CODERABBIT=1`).

Injected instructions (`WARP_OFFLOAD_INSTRUCTIONS`) tell agents to prefer:

| Tool | Use |
|------|-----|
| `warp_status` | CLI + auth probe |
| `warp_agent_run` | Local Oz agent (`oz agent run`) |
| `warp_agent_run_cloud` | Remote Oz (`oz agent run-cloud`) |
| `warp_offload_shell` | Audited single shell command → `tmp/warp_runs/` |
| `warp_orchestrate_agency_task` | High-level goal with agency MCP attached |
| `coderabbit_review` | Local AI code review |

Teams get Warp blurb + team-level `warp`/`coderabbit`/`linear` tools via `teams/_factory.py`.  
Workflows append Warp guidance via `workflows/_warp.with_warp_guidance`.

## Install

```bash
# Oz CLI (orchestration)
# https://docs.warp.dev/reference/cli/cli
# Linux tarball → oz binary; or brew install --cask oz
export PATH="$HOME/.local/bin:$PATH"
oz login   # or: export WARP_API_KEY=wk-...

# Warp TUI agent (optional)
# already at ~/.local/bin/warp on this host

# CodeRabbit
curl -fsSL https://cli.coderabbit.ai/install.sh | sh
coderabbit auth login   # or CODERABBIT_API_KEY agentic key
```

## Config

| Path | Purpose |
|------|---------|
| `configs/warp/agency-mcp.json` | Oz MCP → AgentOS :7777, Drop :7788, bridge :7790 |
| `configs/warp/agency-agent.yaml` | Default Oz agent file prompt |
| `.coderabbit.yaml` | PR/CLI review profile |

## Env

```bash
WARP_API_KEY=
WARP_OZ_BIN=/root/.local/bin/oz
WARP_TUI_BIN=/root/.local/bin/warp
WARP_DEFAULT_CWD=/root/src/repos/ai-agency
WARP_ATTACH_AGENCY_MCP=1
WARP_ENVIRONMENT_ID=          # for run-cloud
CODERABBIT_API_KEY=           # Agentic API key for headless CI
AGENCY_DISABLE_WARP=0
AGENCY_DISABLE_CODERABBIT=0
```

## CI

- `.github/workflows/ci-coderabbit.yml` — install CLI, validate config, headless review when secret set  
- Umbrella `ci.yml` includes **coderabbit** in **All CI gates green**  
- GitHub App [CodeRabbit](https://github.com/apps/coderabbitai) recommended for PR Check `coderabbitai`

## Example agent offload

```python
from tools.warp_tools import warp_orchestrate_agency_task, warp_offload_shell

warp_offload_shell("python -m scripts.autonomous_product_locate --top 1", reason="locate GO")
warp_orchestrate_agency_task(
    "Refactor tools/shopify_tools.py drafts to include tags ego.engineer",
    mode="local",
)
```
