# SWC-284 Risk Register & Revisit Triggers — Solid Shampoo + Conditioner Bar Duo with Travel Tin (v1.0)

**Status:** NO-GO (preserved) · **Date:** 2026-08-24 · **Owner:** growth ops · **Companion docs:** unit-economics memo (task t_93d0340c) and tracker closeout (task t_c5e7eb8b)
**Purpose:** SWC-284 is rejected primarily on margin (CM $1.93/unit, 5.5% at $34.99 price, house convention SWC-135 §1). This register preserves the *non-financial* rejection reasons and defines the exact conditions under which the concept can be revived without re-litigating old ground. Baseline used throughout: Price $34.99, COGS $6.50, Ship $5.50, CPA $18, Fees 7.9%·P+$0.30 → CM $1.93 (5.5%) vs portfolio hurdle ≥20%.

## R1 — Scent/hair-type mismatch drives returns and review damage

| Field | Entry |
|---|---|
| Failure mode | Shopper buys a duo formulated/scented for the wrong hair type (dry/curly vs oily/fine) or dislikes the scent they couldn't smell pre-purchase; unfamiliar solid-format lather reads as "doesn't work." Result: refunds, replacements, and — worse — 1-star reviews that permanently depress PDP conversion even after copy fixes. |
| Rough likelihood | Medium-high. Haircare has the highest preference variance of our categories; e-commerce removes both the sniff test and stylist advice. Expect elevated early-return rates until positioning matures. |
| Mitigation IF revisited | (a) Scent-sampler add-on at checkout ($6–9 mini-trio credited toward full-size purchase); (b) 20-second hair-type quiz on PDP routing to the right variant; (c) unambiguous per-SKU labeling ("Hydrate — dry/curly," not "nourishing"); (d) first-bar satisfaction guarantee to convert return exposure into trial trust; (e) tag every return reason code as scent / texture / results so the next go/no-go runs on data, not anecdote. Gate: projected return rate ≤6% with mitigations live. |

## R2 — Regulatory/copy risk (disease, clinical, hair-loss claims)

| Field | Entry |
|---|---|
| Failure mode | PDP, ad, or UGC copy drifts into disease/drug territory — "repairs damaged hair," "stops hair loss," "treats scalp conditions," "clinical results." Consequences: FTC substantiation exposure, FDA cosmetic-vs-drug line-crossing (regrowth claims), Meta/TikTok health-claim ad rejections mid-campaign, Amazon listing suppression. One bad claim can kill the SKU's ads account-wide. |
| Rough likelihood | Low-medium as a managed process; high if unmanaged, because UGC creators improvise benefit language and "hair loss" phrasing creeps in naturally around shedding/thinning angles. |
| Mitigation IF revisited | Enforce a binding claims checklist banning disease, clinical, and hair-loss/regrowth claims on PDP and ads. Maintain an approved-claims whitelist (cleanses, softens, adds shine, reduces breakage from brushing — only where substantiated). Creator briefs carry the banned-phrases list verbatim; all creative passes a pre-spend claims QC gate (same pattern as SWC-282 QC spec §8); marketplace listings re-reviewed quarterly. |

## R3 — Heat softens bars in transit

| Field | Entry |
|---|---|
| Failure mode | Summer truck/porch temperatures (>35 °C) soften or partially melt bars; product arrives deformed, fused to the tin interior, or greasy-wrapped. Refund/replace costs land directly on an already-thin CM, and "arrived melted" photos are review poison. |
| Rough likelihood | Low-moderate annually but sharply seasonal — concentrated June–September, spiking on heat waves and slow ground lanes (5+ day transit through Sun Belt routes). |
| Mitigation IF revisited | (a) Reformulate with higher-melt-point butter/stearic blend targeting softening point ≥55 °C (verify by 60 °C/2 h oven test) — also becomes a marketable "summer-proof formula"; (b) insulated mailers with selective phase-change packs (~$0.60–1.00 incremental, applied only to hot-ZIP/date-flagged orders, never blanket); (c) seasonal shipping windows: hold cheap-ground fulfillment above defined temperature thresholds June–Sept, upgrade lane speed instead; (d) tin liner/vent design so any softening doesn't fuse product to metal. |

## Revisit triggers (any one opens a fresh go/no-go evaluation)

| # | Trigger | Quantified threshold | Effect at current stack (house formula) |
|---|---|---|---|
| T1 | Negotiated landed COGS | ≤ **$4.50/unit** (from $6.50) | CM rises $1.93 → **$3.93 (11.2%)** — necessary but not sufficient alone |
| T2 | Tin supplier quote | ≤ **$1.20/unit FOB @ 1k MOQ** (vs est. $2.40 inside current COGS) | CM +$1.20 → $3.13 (8.9%); stacks toward T1 |
| T3 | Bundle/AOV lift | Attach strategy lifts AOV ≥ **$59** with blended COGS ≤ **$18.74** (~32% of AOV) | Fees recompute to $4.96; fixed stack $28.46 → CM ≥ $11.80 (**≥20% hurdle cleared**) — e.g., duo+tin+accessory at ~$16.25 blended COGS yields CM ≈ $14.29 (24.2%) |
| T4 | Returns confidence | Sampler + quiz + labeling plan projecting return rate **≤6%** and PDP rating **≥4.2★** | Removes R1 as a blocker; converts review risk into trial data |
| T5 | Heat-proof formulation | Lab-confirmed softening point **≥55 °C** enabling uninsulated year-round ground shipping | Removes R3 as a blocker; kills the $0.60–1.00 seasonal insulation surcharge |

Note on feasibility: clearing the ≥20% hurdle at $34.99 price requires COGS ≤ $1.43/unit — not credible for a bar duo + tin. The realistic revival path is T3 (bundle/AOV), optionally combined with T1/T2 cost relief; T4 and T5 clear the non-financial blockers in parallel.

## Monitoring cadence

Re-scan supplier quotes for T1/T2 quarterly; watch AOV/attach-rate dashboards for T3 candidates among live SKUs; T4/T5 activate only when T1–T3 make the concept economically plausible again. When any trigger fires, open a new analysis card referencing this register — do not restart discovery from scratch.
