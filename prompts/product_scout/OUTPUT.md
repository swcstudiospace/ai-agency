# Expected output — ProductCandidateBatch

JSON matching schema fields:
- market_summary
- niche
- candidates[] with name, category, avatar, decision, composite_score, economics, risks, kill_criteria, next_experiment, evidence[], confidence
- recommended_first_test
- open_questions

Rank candidates best-first. Include at least 5 when research supports it; fewer if niche is thin (explain).

## Self-validation checklist (run before final answer)
- [ ] Required schema fields populated or explicitly marked N/A with reason
- [ ] Numbers labeled estimate vs source-backed
- [ ] At least one concrete next action with owner
- [ ] Risks and kill criteria present when recommending TEST/GO
- [ ] Compliance-sensitive language reviewed
- [ ] No secrets or fabricated citations
