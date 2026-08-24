# SWC-283 Product Decision Record — NO-GO: Safety Razor Starter Kit (Bamboo Handle + Stand + Blades Tin) v1.0

**DECISION: NO-GO** · **Date:** 2026-08-24 · **Owner:** growth ops · **Deciding forum:** product council (record filed for ratification)
**Linked items:** Kanban epic t_65b49b4f (Linear SWC-283) · GitHub mirror [#146](https://github.com/swcstudiospace/ai-agency/issues/146) · Source: `ai-agency/tmp/runs/product_rank_20260816T200140Z.json` (grok-fallback rank run 2026-08-16) · Companion: SWC-284 NO-GO closeout (`docs/product-decisions/2026-08-24-swc-284-solid-shampoo-duo-tin/`) · Related: GH issues #149/#151 (later locate-stage work on this concept)

## 1. Decision summary

SWC-283 is rejected. The concept scored **54.3** in the 2026-08-16 rank-fallback run — below the batch leader (55.3, also NO-GO) — with post-ad contribution margin of **$2.77/unit (7.5% at $36.99)** against the portfolio hurdle of ≥20% (house convention SWC-135 §1). The ranker stamped `healthy=false` and `decision=NO-GO`. This record closes the loop: the $2.77 margin cannot absorb any of the three flagged risks — beginner-injury returns, mandatory education content, or blade-shipping compliance — individually, let alone together. The returns-rate sensitivity in §3 shows the go case failing even under optimistic assumptions.

## 2. Scorecard and provenance

| Field | Value |
|---|---|
| Composite score | **54.3** (batch leader 55.3 — also NO-GO) |
| Model confidence | 0.63 |
| Category | Plastic-free grooming tools · competition medium · year-round seasonality |
| Return risk (source) | medium · Shipping risk (source): low |
| Economics verdict (source) | `healthy=false`; source-recorded breakeven ROAS 2.06 vs suggested minimum 1.78 |

Provenance caveat: the rank run was a grok-fallback after the Parallel API returned HTTP 402 (insufficient credit); its metadata flags the web evidence as **UNVERIFIED**. That is adequate for a NO-GO — the error direction is conservative, since real costs are more likely to exceed estimates — but any revival must start from a verified Parallel re-rank.

## 3. Unit economics (per rank data + house fee formula 7.9%·P + $0.30)

| Line item | Per unit |
|---|---|
| Sell price | $36.99 |
| COGS (razor + stand + blades tin + how-to card) | −$7.50 |
| Outbound shipping | −$5.50 |
| Payment/platform fees (7.9% × $36.99 + $0.30) | −$3.22 |
| **Pre-ad contribution** | **$20.77 (56.1%)** |
| Planning CPA (portfolio default) | −$18.00 |
| **Post-ad contribution margin** | **$2.77 (7.5%)** — portfolio hurdle ≥20% |

Note: the $2.77 already carries the full $18 default CPA (source `variable_cost` $34.22 = price − margin, consistent with this build-up). It leaves essentially zero room for the three risks below, each of which lands inside that residue.

### Returns-rate sensitivity

Model (verified by `swc283_unit_economics.py` alongside this record): a returned kit is refunded in full and the kit itself is written off — opened blades have zero resale for hygiene reasons. Out-of-pocket loss per return ≈ **$23.88** (unsellable-kit COGS $7.50 + lost outbound ship $5.50 + non-refundable fees ~$0.88 + processing labor ~$4.00 + reverse freight ~$6.00). Expected post-ad CM per ordered unit = $2.77 − (return rate × $23.88).

| Return rate | Expected post-ad CM | Margin % | Max tolerable CAC (from $20.77 pre-ad pool) |
|---|---|---|---|
| 0% (hypothetical floor) | $2.77 | 7.5% | $20.77 |
| **5% (optimistic)** | **$1.57** | **4.3%** | $19.57 |
| 10% | $0.38 | 1.0% | $18.38 |
| 15% | **−$0.81** | **−2.2%** | $17.19 |

Read: even the optimistic 5% case leaves $1.57 (4.3%) — less than a quarter of the 20% hurdle. Expected margin goes negative beyond an **11.6%** return rate; at 15% the SKU loses money on every order *at the assumed $18 CPA, before any extra spend*. For calibration, technique-dependent consumer products routinely see double-digit early return rates, and the source itself rated return risk "medium."

### Why the go case fails under any assumption

To clear the ≥20% hurdle at $36.99 with the $18 planning CPA, COGS must be ≤ **$2.87 even at zero returns** — and ≤ **$0.48** when a realistic 10% returns allowance is included. Neither is remotely credible for a razor + stand + tin + card kit whose estimated COGS is already a lean $7.50. The binding constraints are price, CPA, and returns exposure — none of them movable by sourcing.

## 4. Top-3 ranked risks (why $2.77 cannot absorb them)

| # | Risk | Likelihood / impact | Quantified effect |
|---|---|---|---|
| R1 | **Beginner nicks drive returns and review damage.** The core pitch is converting cartridge users; classic safety razors demand technique (angle, near-zero pressure). First-blade cuts produce "product injured me" refunds, chargebacks, and 1-star reviews that permanently depress PDP conversion. The source rated return_risk medium *before* counting the injury-narrative multiplier. | Medium-high / high | Each return ≈ $23.88 out-of-pocket plus full revenue reversal; at 10–15% return rates (plausible for technique products) expected CM falls to $0.38 or −$0.81 (§3). Review damage pushes CAC upward on exactly the margin that cannot pay for it. |
| R2 | **Education content is mandatory, not optional.** Skipping it guarantees R1. Required: how-to card in box (already in BOM), PDP tutorial video, tutorial-led ad creative, onboarding email flow — est. $2,500–$5,000 upfront plus ongoing creator refresh. Tutorial creative also converts slower than demo creative, inflating CAC above the $18 baked into break-even. | High (certain) / high | Amortized over a 500-unit first batch, content alone adds $5–10/unit — 180–360% of the entire $2.77 margin. Even at 2,000 units it adds $1.25–2.50/unit, consuming 45–90% of what remains. Headroom at a 10% return rate is $0.38; there is no volume at which content pays for itself inside this price. |
| R3 | **Blade-shipping compliance overhead.** Carriers and countries restrict blade shipments; the ranker itself flagged "check blade mail restrictions." Compliance requires geo-exclusion engineering for denied lanes, 3PL handling SOPs with possible surcharges (~$0.50–1.50/order), customs declarations, and refund exposure on seized parcels — a permanent tax on every order, plus TAM loss from excluded markets. | Medium / medium | $0.50–1.50/order equals 18–54% of the $2.77 margin before a single return or content dollar; seized-parcel refunds land at full R1-style loss. Low drama, but guaranteed friction on 100% of orders. |

Interaction effect: the risks multiply rather than add. Mitigating R1 requires R2 spend; R2 spend raises CAC, squeezing the same $2.77 that R3 taxes on every order. There is no sequencing in which this margin survives all three.

## 5. Verdict

**NO-GO — confirmed.** SWC-283 fails on margin structure, not execution quality: a $2.77 (7.5%) post-ad margin cannot simultaneously fund beginner-technique returns, mandatory education content, and blade-compliance friction, and the returns sensitivity shows expected margin turning negative near a 12% return rate with zero incremental spend. Do not allocate sourcing or creative budget.

## 6. Revisit triggers (any ONE reopens evaluation on fresh data)

| # | Trigger | Threshold | Effect (house formula, 10%-returns drag) |
|---|---|---|---|
| T1 | Bundle/AOV lift (blade-refill subscription or gift-set attach) | AOV ≥ **$59** with blended COGS ≤ **$13.00** | CM ≈ $15.15 (**25.7%**) — clears the ≥20% hurdle |
| T2 | Onboarded-pilot returns proof | ≥100-unit pilot with angle-guide + QR tutorial + blade guard showing verified returns **≤5%** and rating **≥4.2★** | Removes R1 as blocker; CM at 5% returns = $1.57 — still requires T1 or T4 to clear hurdle |
| T3 | Compliant blade lanes secured | Signed carrier arrangement, incremental cost **≤$0.75/order**, denied-lane map published | Caps R3 at ≤27% of the $2.77 margin |
| T4 | Proven cheap acquisition | Tutorial-led funnel sustaining blended CAC **≤$10** over ≥14 days | Post-ad CM at 10% returns = $8.38 (**22.7%**) — clears hurdle |

Feasibility note: at $36.99 standalone with an $18 CPA, the ≥20% hurdle demands COGS ≤ $2.87 (zero returns) or ≤ $0.48 (10% returns) — impossible. The realistic revival paths are T1 (bundle/AOV) and/or T4 (proven sub-$10 CAC); T2 and T3 clear the operational blockers in parallel. Any revival must begin with a verified Parallel re-rank, not the unverified fallback data cited here.

---
*Filed to `ai-agency/docs/product-decisions/2026-08-24-swc-283-safety-razor-starter-kit/` (with `swc283_unit_economics.py` + `swc283_economics_output.md`) and attached to kanban task t_5953111c. Cross-reference: SWC-284 (shampoo + conditioner bar duo) NO-GO from the same 2026-08-16 fallback batch shares the root cause — an $18 default CPA pressing on thin-margin eco accessories.*
