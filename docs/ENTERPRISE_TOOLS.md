# Enterprise SOTA tool map — AI Dropshipping Agency

This document maps the **full dropshipping lifecycle** to integrations, what we
implemented, and what remains credential-gated.

## Principle

| Layer | Autonomy |
|-------|----------|
| Research, scoring, briefs, drafts, Linear dual-write | **Autonomous (L2)** |
| Shopify draft products, Meta/TikTok **DRAFT/PAUSED** | **Autonomous (L2)** |
| Ad **LIVE** delivery | **HITL** via spend vault |
| Supplier payment / bulk PO / bank wire | **Human only** (not automated) |
| Confirm spend codes | **Human only** (agents blocked) |

## Lifecycle → tools

| Stage | Tools | Status |
|-------|-------|--------|
| Market / product discovery | `parallel_*`, Product Scout, `run_product_rank` | Live (Parallel key) |
| Unit economics | `contribution_margin`, `price_ladder` | Live |
| Work tracking | `linear_*`, `agency_track`, Hermes Kanban mirror | Live when Linear key present (auto from hermes-linear connector.env) |
| Supplier vetting | `score_supplier`, `compare_suppliers`, Parallel extract | Heuristic + research |
| Logistics / ETA | `estimate_shipping_profile`, `track_shipment`, SLA copy | Heuristic; 17track when token set |
| Brand / creative strategy | Creative agents + skills | Live (LLM) |
| UGC production | `generate_ugc_avatar_video` (Fal `argil/avatars/text-to-video`), `generate_product_image` | Live when `FAL_KEY` + `fal-client` |
| Store / PDP | `draft_product`, `list_products`, `list_orders`, draft orders | Live when Shopify token |
| Compliance | Compliance Officer + claims skill | Live (policy LLM) |
| Meta ads | `meta_draft_campaign`, `meta_launch_campaign` (HITL), insights | Draft always; live needs Meta token + spend token |
| TikTok ads | `tiktok_draft_campaign`, `tiktok_launch_campaign` (HITL) | Same pattern |
| Funding / HITL | `attach_funding_source`, `request_spend_approval`, `confirm_spend_approval` | Live local vault |
| End-to-end | `scripts.autonomous_lifecycle` / MCP `run_autonomous_lifecycle` | Live |

## Fal UGC path (recommended)

1. Creative Director produces hook + 15s script (compliance-safe).
2. `build_ugc_brief_and_render` or `generate_ugc_avatar_video`:
   - Endpoint default: `argil/avatars/text-to-video`
   - Inputs: avatar, text/script, voice
   - Output: MP4 URL
3. Optional stills via `fal-ai/flux/dev`.
4. Dual-write Linear `[Creative]` issue with asset URLs.
5. Attach URL on Meta/TikTok drafts.

Alternatives (not wired): Creatify, Arcads, HeyGen, VEED — same adapter pattern.

## Meta & TikTok

**Meta Graph Marketing API**

- Campaign → Ad set → Ad → Creative
- We create **drafts locally**; optional PAUSED remote create if `META_AUTO_CREATE_PAUSED=1`
- Activation only via `meta_launch_campaign(draft_id, approval_id, spend_token)`

**TikTok Business API**

- Same draft → HITL enable pattern (`operation_status` DISABLE→ENABLE)

## Linear dual-track (critical)

1. **Linear SPE team** — stakeholder-visible issues (`agency_track` prefixes by stage)
2. **Hermes Kanban `eng` board** — best-effort mirror via `hermes kanban create --idempotency-key linear:SPE-N`
3. Keys auto-loaded from `~/.config/hermes-linear/connector.env` + `config.yaml` state IDs
4. State keys: backlog / unstarted / started / completed / canceled

Verify: `python -c "from tools.linear_tools import linear_status; print(linear_status())"`

## HITL spend vault

```text
attach_funding_source(bank|crypto metadata)
        ↓
request_spend_approval(amount, channel, purpose, draft_ids)
        ↓  (returns approval_id + one-time code; Linear [Spend HITL] issue)
human: confirm_spend_approval(id, code, "I authorize…")
        ↓  (returns spend_token)
meta_launch_campaign / tiktok_launch_campaign(draft, approval_id, token)
```

Crypto stores **public address only**. Bank stores **institution + last4 only**.

## Autonomous runner

```bash
cd /root/src/repos/ai-agency && source .venv/bin/activate
PYTHONPATH=. python -m scripts.autonomous_lifecycle \
  --niche "desk mobility kits" --processor ultra --top 3
# optional: --render-ugc   # requires FAL_KEY
```

Artifacts: `tmp/runs/lifecycle_*.md` + `*_HITL_CODES.json` (chmod 600).

## Credential checklist

- [x] Parallel
- [x] Linear (connector.env)
- [ ] Shopify
- [ ] Fal
- [ ] Meta
- [ ] TikTok
- [ ] 17track (optional)
- [ ] Funding source attached in spend vault

## SOTA backlog (next)

1. Full Meta ad set + creative upload + pixel CAPI
2. TikTok Spark Ads / identity + video upload API
3. CJDropshipping / Zendrop / Spocket order APIs (still HITL pay)
4. AfterShip instead of/in addition to 17track
5. Klaviyo flows API for Email CRM
6. Stripe Connect for store payouts (not ad spend)
7. Start hermes-linear-connector on :8799 if Kanban ensure-issue HTTP desired
8. Eval harness for lifecycle JSON schema completeness
