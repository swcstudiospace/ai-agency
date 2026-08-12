# AI Dropshipping Agency — Grok Build project instructions

This repository is controlled by **Hermes → Agno → Grok Build**.

## Bottom layer

Use Grok Build headless (`grok -p`) for multi-step shell and coding.
Agency wrappers: `tools/grok_build_tools.py` (`grok_build_run`, `grok_build_offload_shell`).

## HITL

- No live ad spend without human confirm codes
- No unsupervised supplier payments
- Shopify: draft by default
- Gmail outreach: compose only, human sends

## SuperGrok

Agents and Grok Build share SuperGrok auth (`XAI_API_KEY` and/or `~/.grok/auth.json`).
Default chat model for Agno: `grok-4.5`. Grok Build default model: `grok-build`.

## Key scripts

- Rank: `python -m scripts.autonomous_product_rank`
- Locate: `python -m scripts.autonomous_product_locate`
- Post-locate: `python -m scripts.autonomous_post_locate`
- Showcase: `python -m scripts.showcase_grok_build_dropshipping_flow`
- E2E: `python -m scripts.e2e_agency_run`

## Brand

Primary domain: **ego.engineer**. Storefront scaffold: `storefront-oxygen/`.
