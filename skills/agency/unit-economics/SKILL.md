---
name: unit-economics
description: "Compute and gate decisions on contribution margin, ROAS, MER, and AOV economics."
metadata:
  category: agency
  agency: ai-dropshipping
---

# Unit Economics

## Core formulas
- **Landed COGS** = unit + inbound shipping + duties/packaging share
- **Variable cost** = landed + payment fees + outbound (if any) + expected returns + ad CPA + other variable
- **Contribution margin (CM)** = sell price − variable cost
- **CM%** = CM / sell price
- **ROAS** = revenue / ad spend
- **MER** = total revenue / total ad spend (blended)
- **AOV** = revenue / orders

## Default gates (override only with Finance approval)
- Test launch: projected CM% ≥ 20% at target CPA
- Scale: realized CM% ≥ 25% and ROAS ≥ account target for 3+ days
- Kill: ROAS below floor for learning window with ≥ significant spend

## Offer levers
Price, bundle, free-ship threshold, order bump, post-purchase upsell — model CM impact of each before shipping creative.

## Reporting
Always show CM$, CM%, CPA, ROAS, MER, AOV, return rate assumption, and sensitivity (±20% CPA).
