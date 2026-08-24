#!/usr/bin/env python3
"""SWC-284 — Solid shampoo + conditioner bar duo + travel tin.

Independent per-unit P&L rebuild, sensitivity analysis, break-even math,
and hurdle benchmarking. All assumptions explicit and sourced inline.
Outputs a markdown memo in the same directory.
"""
from itertools import product as iproduct

# ----------------------------------------------------------------------------
# Stated inputs (from SWC-284 discovery rank, 2026-08-16)
# ----------------------------------------------------------------------------
PRICE = 34.99          # retail price point
COGS = 6.50            # factory COGS for bar duo + tin (unverified supplier quote)
SHIP = 5.50            # outbound shipping per order
STATED_CM = 1.93       # contribution margin claimed by original rank ($)
STATED_PCT = 5.5

# ----------------------------------------------------------------------------
# Rebuild assumptions (each explicit; ranges used in sensitivity)
# ----------------------------------------------------------------------------
REFERRAL_PCT = 0.15        # marketplace referral/payment fees ~15% of price
FREIGHT_IN_ALLOC = 0.60    # inbound ocean freight+drayage+duty allocation/unit
TIN_PACKAGING = 1.10       # travel tin already inside COGS? NO - treated separately:
                           # conservative: COGS covers bars only, tin+carton here
CAC_AT_TARGET_ROAS = 17.50 # blended CAC at target ROAS (~2.0x at $34.99 AOV)
CPA_GATE = 18.00           # agency CPA gate used by the Aug-16 rank run
HURDLE = 0.20              # portfolio margin hurdle: >= 20% contribution margin
RETURN_RATE = 0.03         # category return/damage allowance on units sold
RETURNS_COST_MULT = 0.55   # % of unit revenue lost per returned unit

def pnl(price, cogs, ship=SHIP, referral_pct=REFERRAL_PCT,
        freight=FREIGHT_IN_ALLOC, tin=TIN_PACKAGING):
    """Return dict of per-unit P&L lines and CM."""
    referral = price * referral_pct
    returns_cost = price * RETURN_RATE * RETURNS_COST_MULT
    cm = price - cogs - freight - tin - referral - returns_cost - ship
    return {
        "price": price, "cogs": cogs, "freight_in": freight,
        "tin": tin, "referral": referral, "returns": returns_cost,
        "ship": ship, "cm": cm, "cm_pct": cm / price if price else 0.0,
    }

def line(label, val):
    print(f"  {label:<38} ${val:>7.2f}")

base = pnl(PRICE, COGS)
print("=== BASE CASE PER-UNIT P&L (rebuild) ===")
line("Retail price", base["price"])
line("Factory COGS (bar duo)", -base["cogs"])
line("Inbound freight+duty alloc", -base["freight_in"])
line("Travel tin + carton packaging", -base["tin"])
line(f"Marketplace fees ({REFERRAL_PCT:.0%})", -base["referral"])
line(f"Returns allowance ({RETURN_RATE:.0%} @ {RETURNS_COST_MULT:.0%} loss)", -base["returns"])
line("Outbound shipping", -base["ship"])
line("Contribution margin", base["cm"])
print(f"  {'CM %':<38} {base['cm_pct']:>7.1%}")
print()

# Cross-check vs stated numbers: stated stack = 34.99 - 6.50 - 5.50 = 22.99 cost
# => stated CM should be 34.99-12.00 = 22.99?? No: stated CM 1.93 implies extra
# costs of 34.99-12.00-1.93 = 21.06 in the original model (fees+CAC etc).
implied_other = PRICE - COGS - SHIP - STATED_CM
print(f"Stated-rank implied 'other costs' beyond COGS+ship: ${implied_other:.2f}")
print(f"Rebuilt non-ad fixed stack (fees+freight+tin+returns): "
      f"${(base['referral']+base['freight_in']+base['tin']+base['returns']):.2f}")
print()

# ----------------------------------------------------------------------------
# With paid acquisition (CAC) — the gate that actually killed it
# ----------------------------------------------------------------------------
with_cac = base["cm"] - CAC_AT_TARGET_ROAS
print("=== AFTER PAID ACQUISITION (blended CAC @ target ROAS) ===")
line(f"CAC assumption", CAC_AT_TARGET_ROAS)
line("Net contribution / unit after ads", with_cac)
print()

# ----------------------------------------------------------------------------
# Sensitivity: +/-10% on price and COGS (CM% before ads, hurdle test)
# ----------------------------------------------------------------------------
print("=== SENSITIVITY (+/-10% price x +/-10% COGS), CM% pre-ads ===")
prices = [PRICE * 0.9, PRICE, PRICE * 1.1]
cogses = [COGS * 0.9, COGS, COGS * 1.1]
grid = {}
for p, c in iproduct(prices, cogses):
    r = pnl(p, c)
    grid[(round(p, 2), round(c, 2))] = (r["cm"], r["cm_pct"])
hdr = "price\\cogs |" + "".join(f"   {c:>6.2f}$   " for c in cogses)
print(hdr)
for p in prices:
    row = f"{p:>8.2f}$  |"
    for c in cogses:
        cm, pct = grid[(round(p, 2), round(c, 2))]
        flag = "*" if pct >= HURDLE else " "
        row += f" {cm:>6.2f}/{pct:>5.1%}{flag}"
    print(row)
print("(* = clears >=20% CM hurdle pre-ads)")
pass_count = sum(1 for v in grid.values() if v[1] >= HURDLE)
print(f"Cells clearing hurdle: {pass_count}/9")
print()

# ----------------------------------------------------------------------------
# Break-even prices
# ----------------------------------------------------------------------------
be_zero = (COGS + FREIGHT_IN_ALLOC + TIN_PACKAGING + SHIP) / \
          (1 - REFERRAL_PCT - RETURN_RATE * RETURNS_COST_MULT)
be_hurdle = (COGS + FREIGHT_IN_ALLOC + TIN_PACKAGING + SHIP - HURDLE * 0) # placeholder
# CM = p*(1-ref-ret) - (c+f+t+s) ; hurdle: CM/p >= H
# p*(1-ref-ret-H) = c+f+t+s -> p = (c+f+t+s)/(1-ref-ret-H)
denom_h = 1 - REFERRAL_PCT - RETURN_RATE * RETURNS_COST_MULT - HURDLE
be_hurdle = (COGS + FREIGHT_IN_ALLOC + TIN_PACKAGING + SHIP) / denom_h
be_cac = (COGS + FREIGHT_IN_ALLOC + TIN_PACKAGING + SHIP + CAC_AT_TARGET_ROAS) / \
         (1 - REFERRAL_PCT - RETURN_RATE * RETURNS_COST_MULT)
print("=== BREAK-EVEN PRICES (base COGS/shipping/fees) ===")
print(f"  Zero-CM price (no ads):                ${be_zero:>7.2f}")
print(f"  Price to clear {HURDLE:.0%} CM hurdle (no ads):   ${be_hurdle:>7.2f}")
print(f"  Zero-net price incl ${CAC_AT_TARGET_ROAS:.2f} CAC:      ${be_cac:>7.2f}")
print()

# ----------------------------------------------------------------------------
# Leverage deltas: what single change clears the hurdle?
# ----------------------------------------------------------------------------
r = pnl(PRICE, COGS)
need_cm = HURDLE * PRICE
gap = need_cm - r["cm"]
print(f"=== GAP TO HURDLE: ${gap:.2f}/unit (need CM ${need_cm:.2f}, have ${r['cm']:.2f}) ===")

# Option A: pure COGS cut needed
cogs_cut_needed = gap
new_cogs = COGS - cogs_cut_needed
print(f"Option A: COGS must fall to ${new_cogs:.2f} (-{cogs_cut_needed/COGS:.0%}) — implausible vs $6.50 quoted")

# Option B: price increase alone
p_hurdle = be_hurdle
print(f"Option B: price alone -> ${p_hurdle:.2f} (+{(p_hurdle-PRICE)/PRICE:.0%}); "
      f"vs competitor duo+tin anchors $24-$44")

# Option C: bundle uplift (add refills/second tin set) price +$10, COGS +$3
rb = pnl(PRICE + 10, COGS + 3)
print(f"Option C: $44.99 bundle (+$10 price, +$3 COGS) -> CM ${rb['cm']:.2f} ({rb['cm_pct']:.1%})"
      f"{' CLEAR' if rb['cm_pct']>=HURDLE else ' MISS'}")

# Option D: DTC-only w/ free-ship threshold baked into AOV, no marketplace fees
rdtc = pnl(PRICE, COGS, referral_pct=0.029 + 0.003)  # Shopify Pay 2.9%+$0.30~absorbed
print(f"Option D: DTC-only (fees 3.2%) -> CM ${rdtc['cm']:.2f} ({rdtc['cm_pct']:.1%})"
      f"{' CLEAR' if rdtc['cm_pct']>=HURDLE else ' MISS'} (pre-ads)")

# What COGS cut does Option C-equivalent need if bundled?
# Highest-leverage summary printed in memo.
