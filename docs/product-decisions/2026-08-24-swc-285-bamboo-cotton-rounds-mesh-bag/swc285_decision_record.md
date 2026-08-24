# SWC-285 Decision Record — Reusable bamboo cotton rounds set with mesh wash bag (30–40 pads)

**Date:** 2026-08-24
**Decision:** NO-GO (maintained) — rationale corrected; locate question answered
**Retail:** $27.99 · **House CPA gate:** $18.00/order · **Hurdle:** ≥20% pre-ad CM
**Linear:** [SWC-285](https://linear.app/spectrumwebco/issue/SWC-285/locate-reusable-bamboo-cotton-rounds-set-with-mesh-wash-bag-30-40-pads) (state at record time: Todo)
**Board:** eng card t_7255df3b ([Locate], 3 child tasks, all complete)

## Why this record exists

SWC-285 was created by the 2026-08-16 discovery cron as a shell: the paired rank run stamped
**NO-GO (composite 55.3)** from an *estimated* cost stack (COGS $4.00 + ship $4.50 → CM −3.6%
after $18.00 CPA), and the same night's locate run returned **zero suppliers** for both products
(`product_locate_20260816T200411Z.md` — empty tables). The issue description inherited the shell's
"Decision: NO-GO" with no supplier evidence behind it.

On 2026-08-24 the board ran the full three-stage locate under t_7255df3b:
overseas manufacturer scan (10 verified Made-in-China suppliers), domestic/wholesale + retail-comp
survey, and a consolidated ranked shortlist with landed-cost math. This record reconciles the two.

## Corrected economics (house `contribution_margin` convention)

Landed COGS figures below are from the consolidated shortlist
(`swc285_supplier_shortlist_v1.md`): FOB tier anchors + duty (HTS 6307 ~7% est.) + sea freight/
clearance allocation ($0.45/set) + inspection amortization ($0.28/set), at 35 pads.
Customer shipping uses the house $5.50 small-parcel rate; fees 2.9% + $0.30; returns 5% of revenue.

| Scenario | Landed COGS/set | Pre-ad CM | Pre-ad CM % | After $18.00 CAC |
|---|---|---|---|---|
| Rank-stage guess (2026-08-16, no suppliers) | $8.50 est. all-in | — | **−3.6% after-CPA** (recorded) | −$2.02 |
| #1 Good Seller, 20-pad as-listed config | $2.54 | +$17.44 | **+62.3%** | −$0.56 |
| #1 Good Seller, 35-pad custom (mid estimate) | $3.57 | +$16.41 | **+58.6%** | −$1.59 |
| #2 Xiamen Ebei, 35-pad mid | $4.85 | +$15.13 | **+54.1%** | −$2.87 |

Corrections to the standing record:

1. The recorded "−3.6% margin" was an **after-CPA** number computed from placeholder COGS before
   any real supplier existed. With verified landed costs, pre-ad CM is strongly healthy
   (+54–62%, hurdle is ≥20%; COGS would have to exceed $14.38/set to fail).
2. Locate is no longer empty: 10 verified manufacturers/traders, ranked shortlist of 3
   (Good Seller $2.54–3.90 landed; Xiamen Ebei $4.85; Yangzhou Muhe conditional on quote basis,
   $1.10–7.29 swing). Import route decisively clears the $7–9 ceiling.
3. **NO-GO nonetheless holds**, and the binding constraint moves upstream of COGS: at $27.99
   single-set retail, every fully-paid order still loses money after acquisition cost
   (−$0.56 to −$2.87 across the shortlist at $18.00 CAC). Cheaper COGS cannot fix this — even the
   speculative $0.93-listing upside (~$1.60–2.00 landed) nets only ≈ +$0.25/order after CAC.

## Kill factor

Acquisition economics at single-set price point, not product cost. Same failure class as SWC-284,
different stated reason: SWC-284's recorded margin understated health; SWC-285's recorded margin
was a placeholder artifact of an empty locate. In both cases the product clears the pre-ad margin
hurdle comfortably once inputs are real, and dies at the CPA gate.

## What would change the verdict (revisit triggers)

- **Bundle/AOV path:** multi-set bundle or subscription that lifts revenue per order to ≥$45 while
  keeping blended COGS ≤32% → modeled net turns positive with headroom (mirrors SWC-284 T1/T3 math;
  a 2-set bundle at $45.99 with the #1 supplier nets ≈ +$6.5–8/order after CAC — worth a TEST if
  the agency ever wants this category).
- **Organic-mix path:** DTC+retention model needing ≈ ≤$14 CAC-equivalent (≈52%+ organic mix),
  per the SWC-284 retention analysis.
- **Category proof:** a competing $27.99-class single set demonstrating sustained paid ROAS ≥1.75
  in the niche would falsify the CAC assumption.

## Data-quality caveats

All supplier figures are public-listing anchors and desk estimates pending written RFQ quotes;
duty is an unverified HTS estimate; cert claims are profile-level tokens; Amazon review stats
unverified (bot wall). No RFQs, samples, POs, payments, or supplier contact occurred anywhere in
this pipeline (HITL gate respected). Raw evidence retained in board workspaces (`raw/` under
t_9b2b888f); artifacts attached to eng card t_7255df3b and its children t_53f2865b, t_9b2b888f,
t_79508af8.

## Companion files

- `swc285_one_page_summary_v1.md` — decision summary + human approval gate (what RFQ/samples/PO would cost if ever revived)
- `swc285_supplier_shortlist_v1.md` — full scored table, top-3 landed-cost math, upstream corrections
