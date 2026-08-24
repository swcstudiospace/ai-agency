# SWC-284 Unit Economics Validation — NO-GO Finalized
**SKU:** Solid shampoo + conditioner bar duo with travel tin · $34.99
**Verdict:** CONFIRMED — NO-GO upheld, but the recorded rationale is wrong and must be corrected.
**Date:** 2026-08-24 · Model: `swc284_unit_economics.py` (this directory)

## 1. Verdict summary

The NO-GO stands, but not for the reason on record. SWC-284 was logged at "$1.93/unit CM (5.5%)". That number conflates customer-acquisition cost with product margin. Rebuilt line-by-line, the SKU earns **$15.46/unit (44.2% CM) before advertising** — comfortably above the portfolio hurdle. It is killed entirely by paid-acquisition arithmetic:

| Gate | Value | Result |
|---|---|---|
| Pre-ad CM vs ≥20% hurdle | 44.2% | PASSES |
| Fully-loaded (CM − $17.50 CAC) | −$2.04/unit (−5.8% of price) | FAILS |
| Agency CPA gate (~$18) | CAC $17.50 > $15.46 contribution | FAILS |

Every paid order loses ~$2.04. Reconciliation of the original figure implies their model embedded a ~$15.2 CAC inside "contribution margin" ($34.99 − 12.00 − 5.25 fees − ~0.58 returns − 1.93 = $15.23 residual), which matches the ~$18-CPA gate era of the Aug-16 rank run. The decision was right; the label "5.5% margin product" mischaracterizes it for future reuse.

## 2. Complete per-unit cost stack (base case)

| Line | Assumption | $ | % of price |
|---|---|---|---|
| Retail price | stated | 34.99 | — |
| Factory COGS (bar duo) | stated, **unverified** — see §6 | −6.50 | 18.6% |
| Travel tin + carton | modeled separately (conservative; may overlap COGS) | −1.10 | 3.1% |
| Inbound freight + duty alloc | LCL ocean share on ~$7.60 FOB-class goods | −0.60 | 1.7% |
| Marketplace fees | 15% referral/payment blend (Amazon/Shopify app layer) | −5.25 | 15.0% |
| Returns allowance | 3% return rate × 55% revenue loss | −0.58 | 1.7% |
| Outbound shipping | stated | −5.50 | 15.7% |
| **Contribution margin (pre-ads)** | | **+$15.46** | **44.2%** |
| Blended CAC at target ROAS | ~2.0x ROAS at $34.99 AOV | −17.50 | 50.0% |
| **Net contribution after ads** | | **−$2.04** | **−5.8%** |

## 3. Sensitivity (±10% price × ±10% COGS), pre-ad CM%

| Price \ COGS | $5.85 | $6.50 | $7.15 |
|---|---|---|---|
| $31.49 | 41.9% | 39.8% | 37.8% |
| $34.99 | 46.1% | 44.2% | 42.3% |
| $38.49 | 49.4% | 47.8% | 46.1% |

All 9 cells clear the 20% hurdle pre-ads (worst case 37.8%). Price/COGS noise does **not** change the verdict — the kill factor is acquisition cost, and the conclusion is robust to input error on both levers tested.

## 4. Break-even prices (base stack)

- Zero-CM, no ads: **$16.44**
- Clears 20% CM hurdle, no ads: **$21.63**
- Zero-net including $17.50 CAC: **$37.43** — i.e., the current $34.99 price cannot pay for its own traffic at target ROAS; a +7% price move merely stops the bleeding.
- Fully-loaded 20% net hurdle incl. CAC: **~$49.25** — bundle territory.

Organic-mix view: at $34.99, the SKU needs **≥52% of unit volume from non-paid channels** (blended CAC ≤ $8.46) to clear the 20% hurdle, or ≥12% organic just to reach zero-net. A consumable with natural repeat could plausibly get there on LTV (≈2.5 lifetime orders ⇒ ~$38.65 LTV contribution vs $17.50 first-order CAC, ~2.2x), but that is a retention program, not a launch SKU.

## 5. Highest-leverage paths to viability

1. **Raise AOV via bundling (primary lever, +$5.34/unit swing).** Move duo+tin → $44.99 kit (duo + refill bar pair + tin/gift box; +$10 price, ~+$3 COGS): pre-ad CM rises to **$20.80 (46.2%)**, absorbing the full $17.50 CAC with **+$3.30 (7.4%) net** left over. This mirrors the niche-wide finding from the Aug-16 run: bathroom eco SKUs only work as $45–79 bundles, not $35 singles. Fully-loaded 20% requires ~$49.25 of price — reachable only via a $49.99 deluxe kit, and only if CAC stays pinned near $17.50 instead of scaling to half the higher AOV.
2. **Amortize CAC with retention instead of paying it per order (secondary lever).** DTC-first (Shopify, ~3.2% fees instead of 15%) lifts pre-ad CM to $19.59, making the SKU viable iff achievable CAC ≤ ~$19.59 — then email/SMS replenishment flows shift repeat volume to ~zero CAC. At ≥52% organic mix the current $34.99 SKU already clears the hurdle. Without a working retention engine, do not relaunch.

A COGS cut alone is not a path: reaching the hurdle would require COGS to go *negative* (−130%); even stripping the tin and cutting outbound to $4.30 yields only +$2.30/unit — knife-edge zero-net against CAC.

## 6. Data caveats

- **COGS $6.50 was never supplier-verified.** The Aug-16 Grok-fallback locate ran only on cotton rounds and the razor kit; no shampoo-duo supplier quote exists on file. Treat $6.50 as a placeholder until an RFQ lands. Sensitivity shows the verdict survives ±10%, and even ±50% COGS error leaves pre-ad CM >20%, so the NO-GO does not hinge on it.
- Competitor anchors ($24–44 for comparable duos+tins; Ethique/Viori/Kitsch band) are model-knowledge, not live citations: Parallel search returned HTTP 402 again today (account still unfunded). A funded re-pull should precede any relaunch attempt.
- Shipping $5.50 stated, taken as-is; a lighter letter-mail bars-only variant could test ~$4.30.

## Bottom line

**CONFIRMED NO-GO** for launch as specified at $34.99 under the paid-growth model: −$2.04 net per paid order, fully-loaded margin −5.8% vs the assumed ≥20% portfolio hurdle. Correct the Linear record from "5.5% CM product" to "44% pre-ad CM product that fails the CPA gate." Re-evaluate only as a $45+ bundle or inside a retention program with demonstrated ≥52% organic mix.
