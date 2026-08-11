# Expected output — DirectorDecision

Produce a structured decision package:

1. **goal** — one sentence
2. **decision** — what we will do now
3. **autonomy_level** — usually L2
4. **recommended_workflow_or_team** — id or name
5. **margin_summary** — CM/ROAS/budget implications
6. **risk_summary** — top risks
7. **confidence_0_to_1**
8. **next_actions** — ordered, owner-tagged when possible
9. **requires_human_approval** — list
10. **linear_issue_titles** — ready to create

Also include a short executive paragraph a human can paste into Slack.

## Self-validation checklist (run before final answer)
- [ ] Required schema fields populated or explicitly marked N/A with reason
- [ ] Numbers labeled estimate vs source-backed
- [ ] At least one concrete next action with owner
- [ ] Risks and kill criteria present when recommending TEST/GO
- [ ] Compliance-sensitive language reviewed
- [ ] No secrets or fabricated citations
