---
name: product-scoring
description: "Score dropshipping product opportunities on margin, competition, risk, and differentiation."
metadata:
  category: agency
  agency: ai-dropshipping
---

# Product Scoring

## When to use
Before recommending any new SKU or scaling an existing one.

## Process
1. Gather evidence with Parallel Search (objective + 2–3 queries) and Extract on top PDPs/reviews.
2. Estimate: COGS, shipping, sell price, expected CPA, return rate.
3. Run `contribution_margin` tool (or equivalent math).
4. Score each dimension 1–5:

| Dimension | 1 (bad) | 5 (great) |
|-----------|---------|-----------|
| Contribution margin after ads | <10% or negative | ≥35% at target CPA |
| Competition intensity | Dominated by brands with huge creative volume | Clear angle / underserved avatar |
| Shipping risk | >25 days unreliable tracking | ≤12 days reliable |
| Return / defect risk | Wearables fit, complex electronics | Simple durable goods |
| Differentiation | Commodity clone | Bundle, brand story, unique proof |
| Seasonality | Extreme short window only | Evergreen or multi-peak |

5. **Composite**: weight CM 30%, competition 20%, shipping 15%, returns 15%, differentiation 15%, seasonality 5%.
6. Output: GO / TEST / NO-GO with evidence URLs and next experiment.

## Hard rules
- No GO if CM after target ads is negative.
- No GO on restricted categories without Compliance PASS.
- Always propose a smallest viable test (budget + creative count + kill criteria).
