# SWC-284 Tracker Closeout — NO-GO Recorded

**Date:** 2026-08-24
**Product:** Solid shampoo + conditioner bar duo with travel tin ($34.99 · COGS $6.50 · ship $5.50)
**Decision:** **NO-GO — CONFIRMED** (recorded in tracker 2026-08-24)
**Tracker records:** Linear [SWC-284](https://linear.app/spectrumwebco/issue/SWC-284/no-go-solid-shampoo-conditioner-bar-duo-with-travel-tin) · GitHub mirror [#147](https://github.com/swcstudiospace/ai-agency/issues/147) · eng-board card `t_a6adefcb`

## Dated rationale

NO-GO stands, with corrected reasoning versus the original rank row:

1. **Original stated margin was mislabeled.** Rank run `product_rank_20260816T200140Z` recorded CM $1.93/unit (5.5%). Line-by-line rebuild (memo §1–2) shows that figure embedded ~$15.2 of blended CAC inside "contribution." True pre-ad CM is **$15.46/unit (44.2%)**, which clears the ≥20% portfolio hurdle in every ±10% price×COGS sensitivity cell.
2. **Kill factor is acquisition cost, not product margin.** At $17.50 blended CAC (target ROAS ~2.0x), every paid order nets **−$2.04**; break-even price incl. CAC is $37.43 > $34.99. The SKU cannot pay for its own traffic at the listed price.
3. **Verdict robustness:** holds across the full sensitivity grid and even ±50% COGS error (COGS remains supplier-unverified — no RFQ on file for this SKU).

## Artifacts

| Document | File | Source |
|---|---|---|
| Unit-economics memo (validated NO-GO rationale, cost stack, break-evens, viability levers) | `swc284_nogo_memo.md` | task t_93d0340c |
| Reproducible economics model | `swc284_unit_economics.py` | task t_93d0340c |
| Risk register v1.0 (3 risks + 5 quantified revisit triggers T1–T5) | `swc284_risk_register_v1.md` | task t_47f9d01d |

All three shipped as kanban attachments on tasks t_93d0340c / t_47f9d01d and are committed under `docs/product-decisions/2026-08-24-swc-284-solid-shampoo-duo-tin/` in `swcstudiospace/ai-agency`.

## Backlog learning (one line)

> Solid haircare duo fails paid-acquisition math at current price/CAC — pre-ad CM is healthy (44%), so revive only as a ≥$45 bundle (AOV lever T3) or via DTC+retention with ≥52% organic mix; do not relaunch as a $34.99 single.

(Condensed tracker one-liner: *Solid haircare duo fails margin after CAC at $34.99; revisit if bundle lifts AOV ≥$59 or COGS drops below trigger — see risk register T1–T5.*)

## Revisit protocol

Do not restart discovery from scratch. If any risk-register trigger fires (T1 COGS ≤$4.50, T2 tin ≤$1.20 FOB @1k, T3 bundle AOV ≥$59 w/ blended COGS ≤32%, T4 returns ≤6%/rating ≥4.2★, T5 softening ≥55 °C), open a fresh analysis card referencing the register.

## Closeout status

- Board children under SWC-284: t_93d0340c ✅ done · t_47f9d01d ✅ done · t_c5e7eb8b ✅ this task
- Linear SWC-284 moved to Canceled (house mapping for NO-GO; `require_dod_for_done` makes Done wrong for a rejected concept)
