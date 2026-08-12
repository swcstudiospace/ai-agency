# Grok Build bottom layer + CodeRabbit

## Stack

```text
Hermes Agent          (top orchestrator — MCP client)
        │
        ▼
Agno AgentOS          (30 agents · 12 teams · 12 workflows)
  tools: grok_build_*  coderabbit_*
        │
        ▼
Grok Build CLI (`grok`)   (bottom — headless agent / shell offload · SuperGrok)
CodeRabbit CLI (`cr`)     (review gate in CI + agent tool)
```

**Warp/Oz was removed.** Bottom layer is Grok Build only.

## Agent access (automatic)

`agents/_factory.py` attaches toolbelts **`grok_build`** + **`coderabbit`** to **every** agent
(unless `AGENCY_DISABLE_GROK_BUILD=1` / `AGENCY_DISABLE_CODERABBIT=1`).

Injected instructions (`GROK_BUILD_OFFLOAD_INSTRUCTIONS`) tell agents to prefer:

| Tool | Use |
|------|-----|
| `grok_build_status` | CLI + SuperGrok auth probe |
| `grok_build_run` | Headless `grok -p` multi-step agent |
| `grok_build_offload_shell` | Audited single shell command → `tmp/grok_build_runs/` |
| `grok_build_orchestrate_agency_task` | High-level goal + agency agent profile |
| `grok_build_inspect` | Project instructions / skills discovery |
| `coderabbit_review` | Local AI code review |

Teams get Grok Build blurb + team-level `grok_build`/`coderabbit`/`linear` tools via `teams/_factory.py`.  
Workflows append guidance via `workflows/_grok_build.with_grok_build_guidance`.

## Customisations (full)

| Path | Purpose |
|------|---------|
| `AGENTS.md` | Project instructions Grok Build discovers |
| `configs/grok-build/agents/agency-bottom.md` | Default bottom executor persona |
| `configs/grok-build/agents/dropshipping-pipeline.md` | Rank/locate/post-locate specialist |
| `configs/grok-build/agents/agency-coder.md` | Repo coding specialist |
| `configs/grok-build/config.toml` | Model/permission defaults |
| `configs/grok-build/agency-mcp.json` | Optional MCP URLs (:7777/:7788/:7790) |
| `~/.grok/config.toml` | User SuperGrok defaults (`models.default = grok-build`) |

## Install / auth

```bash
curl -fsSL https://x.ai/cli/install.sh | bash
export PATH="$HOME/.grok/bin:$PATH"
# SuperGrok login (browser once) OR:
export XAI_API_KEY=xai-...
grok -p "hello" --always-approve --max-turns 1
```

## Env

```bash
GROK_BUILD_BIN=$HOME/.grok/bin/grok
GROK_BUILD_MODEL=grok-build
GROK_BUILD_DEFAULT_CWD=/root/src/repos/ai-agency
GROK_BUILD_ALWAYS_APPROVE=1
GROK_BUILD_MAX_TURNS=24
AGENCY_DISABLE_GROK_BUILD=0
CODERABBIT_API_KEY=           # Agentic API key for headless CI
```

## Showcase

```bash
PYTHONPATH=. python -m scripts.showcase_grok_build_dropshipping_flow --skip-locate
PYTHONPATH=. python -m scripts.showcase_grok_build_dropshipping_flow --try-grok-agent
```

Produces `tmp/runs/grok_build_dropshipping_showcase_*.{md,json}` and `tmp/grok_build_runs/`.

## CodeRabbit CI

Unchanged: inline job in `ci.yml` + standalone `ci-coderabbit.yml` + `.coderabbit.yaml`.
