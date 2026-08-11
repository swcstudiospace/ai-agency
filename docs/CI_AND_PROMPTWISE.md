# CI/CD + PromptWise UGC

## GitHub Actions

| Workflow | Path | When |
|----------|------|------|
| **CI umbrella** | `.github/workflows/ci.yml` | every push/PR |
| **Backend** | `.github/workflows/ci-backend.yml` | Python compile + import/roster smoke |
| **Cockpit** | `.github/workflows/ci-cockpit.yml` | `npm ci` + Vite PWA build; optional Tauri deb on `[tauri]` commit or manual dispatch |
| **Cockpit package** | `agency-cockpit/.github/workflows/package.yml` | legacy nested packaging job |

Backend CI is **offline** (no SuperGrok/Parallel secrets required). It validates structure so AgentOS does not silently rot.

### Manual Tauri Linux bundle
```bash
# commit message includes [tauri]  OR  Actions → CI Cockpit → Run workflow
git commit -m "build: desktop [tauri]"
```

---

## PromptWise integration (AI UGC)

**Product:** [PromptWise](https://www.promptwise.com) — creative studio with **UGC Factory**, Influencer Studio, Flows, Wise assistant. App: https://app.promptwise.com

### Reality check
- No stable public OpenAPI we could document today.
- FAQ mentions MCP interest; treat official API as **optional** when you get keys.
- **Primary path = browser automation** through Hermes reverse bridge (`:7790`) + structured briefs.
- **Fallback** = existing Fal UGC tools (`tools/fal_tools.py`).

### Agency tools (`tools/promptwise_tools.py`)
| Tool | Purpose |
|------|---------|
| `promptwise_status` | mode: `browser` \| `api` \| `brief_only` |
| `promptwise_build_ugc_brief` | structured brief + Wise prompt → `tmp/creatives/promptwise/` |
| `promptwise_open_workspace` | open app via Hermes browser |
| `promptwise_run_ugc_job` | brief → API if configured → else browser HITL playbook |

Attached to toolbelts: **`promptwise`**, **`creative_ops`**, **`creative_prod`**.  
Agents: **Creative Director**, **Ads Creative Ops**.

### Env
```bash
PROMPTWISE_APP_URL=https://app.promptwise.com
PROMPTWISE_UGC_PATH=                 # optional deep link path
PROMPTWISE_BROWSER_ENABLED=1
PROMPTWISE_API_KEY=                  # if PromptWise issues one
PROMPTWISE_API_BASE=                 # e.g. https://api.promptwise.com
HERMES_BRIDGE_URL=http://127.0.0.1:7790
```

### Operator setup (browser path)
1. Start `hermes-bridge` (`systemctl status hermes-bridge`).
2. Once, log into PromptWise in the bridge browser session (Playwright profile).
3. Agent: `promptwise_run_ugc_job(product_name=..., hook=..., script=...)`.
4. Human confirms generation (credits) → download asset → store under `tmp/creatives/promptwise/`.
5. Linear dual-write + ad draft HITL as usual.

### Recommended creative stack
```text
Product rank GO
  → Creative Director / Ads Creative Ops
      → promptwise_build_ugc_brief (always)
      → promptwise_run_ugc_job (browser or API)
      → fal generate_ugc_avatar_video (fallback / parallel variant)
  → HITL review before Meta/TikTok spend
```

### If PromptWise gives you MCP later
Register in Hermes `mcp_servers` and wrap the same brief → generate → asset path contract so agents do not care which transport won.
