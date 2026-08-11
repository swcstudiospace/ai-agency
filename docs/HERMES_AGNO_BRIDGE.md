# Hermes × Agno interconnectivity

## Topology (live)

```text
Hermes Agent (top orchestrator)
  native: browser, computer_use, skills, memory, terminal
  MCP clients:
    ai-agency      → :7777/mcp
    drop           → :7788/mcp
    hermes-bridge  → :7790/mcp   (also usable by Hermes itself)
    linear         → mcp.linear.app

Agno agents (18) ──HTTP MCP──► hermes-bridge :7790
                                 browser (Playwright)
                                 skills list/read/propose
                                 MEMORY.md append
                                 KIP Cognitive Nexus
                                 computer_use job queue → Hermes

Shared memory:
  KIP local nexus (kip_memory/) — Anda/ldclabs protocol subset
  EXPORT capsules + ICP receipts (KIP_ICP_MODE=local|canister)
  Hermes MEMORY.md dual-write on hermes_memory_append
  Linear SPE as operational work log
```

## Reverse bridge tools (every agent)

Toolbelt `hermes_bridge` auto-attached in `agents/_factory.py`.

- `hermes_browser_*` — live page fetch/snapshot/screenshot/links
- `hermes_skill_*` — self-improving skill corpus (115+ indexed)
- `hermes_memory_*` — Hermes MEMORY.md / USER.md
- `kip_*` — shared graph memory (remember/recall/execute/export_icp)
- `hermes_computer_use_request` — queue desktop CUA for Hermes

## Services

| Service | Port | systemd |
|---------|------|---------|
| AgentOS | 7777 | `python -m app.main` / start_agentos.sh |
| Drop MCP+ACP | 7788 | `drop-gateway` |
| Hermes bridge | 7790 | `hermes-bridge` |

## KIP + ICP (ldclabs Anda)

- Spec: https://github.com/ldclabs/KIP
- Runtime ref: Anda Cognitive Nexus / anda-bot (installed at `/root/src/repos/anda-bot`)
- Agency implementation: `kip_memory/nexus.py`
- On-chain: set `KIP_ICP_MODE=canister` + `IC_OSS_ENDPOINT` + `KIP_ICP_CANISTER_ID`

## Computer-use note

True Hermes `computer_use` stays in the Hermes process (desktop/session).
Agents request jobs; Hermes picks up via `hermes_computer_use_list_jobs` and
completes with `hermes_computer_use_complete`.
