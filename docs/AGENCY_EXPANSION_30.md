# Agency expansion — 30 agents / 12 teams / 10 workflows

## Why
SOTA dropshipping ops needs dedicated owners for QA, returns, chargebacks,
escalations, logistics exceptions, creative ops, catalog, fraud, partnerships,
tax, community, and experimentation — not just research/creative/growth.

## Counts
| Layer | Before | After |
|-------|--------|-------|
| Agents | 18 | **30** (+12 ops) |
| Teams | 7 | **12** (+5) |
| Workflows | 5 | **10** (+5) |

## +12 Ops agents
1. QA Inspector  
2. Returns Specialist  
3. Chargeback Specialist  
4. CX Escalations  
5. Logistics Coordinator  
6. Ads Creative Ops  
7. Catalog Ops  
8. Risk Fraud Analyst  
9. Partnerships Manager  
10. Tax Compliance  
11. Community Manager  
12. Experimentation Lead  

Each has: profile, thin module, `prompts/<key>/{SOUL,SYSTEM,OUTPUT,EXAMPLES}.md`, Pydantic schema, toolbelts (bridge/brain/analytics as appropriate).

## +5 Teams
- CX Operations  
- Logistics Ops  
- Growth Ops  
- Risk & Finance Ops  
- Merchandising  

## +5 Workflows
- Incident Response Ops  
- Returns RMA Pipeline  
- Creative Production Ops  
- Experimentation Cycle  
- Logistics Exception Handling  

## Verify
```bash
PYTHONPATH=. python -c "import app.main as m; print(len(m.agent_os.agents), len(m.agent_os.teams), len(m.agent_os.workflows))"
# expect 30 12 10
curl -s http://127.0.0.1:7777/health
```
