# Hermes Reverse Bridge + KIP shared memory

## Purpose

Give **Agno agency agents** access to Hermes-class capabilities:

| Capability | Tools |
|------------|--------|
| Browser | `hermes_browser_navigate/snapshot/screenshot/extract_links` |
| Self-improving skills | `hermes_skill_list/read/search/propose` |
| Hermes memory files | `hermes_memory_read/append` |
| Shared KIP graph (Anda/ldclabs) | `kip_remember/recall/execute/export_icp` |
| Desktop CUA handoff | `hermes_computer_use_request/list_jobs` |

## Architecture

```text
Agno agents  --HTTP MCP-->  hermes-bridge :7790
                               ├─ Playwright browser
                               ├─ ~/.hermes/skills (+ external)
                               ├─ ~/.hermes/memories
                               └─ kip_memory (local Cognitive Nexus)
                                      └─ EXPORT capsules → ICP-ready receipts
                                         (KIP_ICP_MODE=canister for on-chain)
```

Hermes top orchestrator still owns true `computer_use` sessions; agents queue jobs.

## KIP + ICP (ldclabs Anda)

Based on [KIP](https://github.com/ldclabs/KIP) + [Anda](https://github.com/ldclabs/anda) /
[Anda Cognitive Nexus](https://github.com/ldclabs/anda-db).

Local nexus implements KQL/KML subset. Capsules export to `kip_memory/data/capsules/`.

```bash
# local ICP-ready receipt (default)
KIP_ICP_MODE=local

# push to your ic-oss / canister gateway when ready:
# KIP_ICP_MODE=canister
# IC_OSS_ENDPOINT=https://your-gateway/upload
# KIP_ICP_CANISTER_ID=aaaaa-aa
```

This host already has Anda Bot at `/root/src/repos/anda-bot` and `~/.anda` —
optional future: start `anda daemon` and bridge `anda tool call` into KIP.

## Run

```bash
cp hermes_bridge/deploy/hermes-bridge.service /etc/systemd/system/
systemctl daemon-reload && systemctl enable --now hermes-bridge

# Chromium for browser tools:
/root/src/repos/ai-agency/.venv/bin/python -m playwright install chromium

curl -s http://127.0.0.1:7790/health | jq .
```

Hermes can also register the bridge as MCP (optional, for top agent):

```bash
hermes mcp add hermes-bridge --url http://127.0.0.1:7790/mcp
```

Agency agents call via `tools/hermes_bridge_tools.py` (auto toolbelt `hermes_bridge`).
