# Ops agents SOTA upgrade

The +12 ops agents now match the original 18-agent archetype:

## Per-agent package
1. **Persona** `prompts/<key>/{SOUL,SYSTEM,OUTPUT,EXAMPLES}.md` (~6.0–6.4KB each)
2. **Thin module** `agents/<key>.py` via `build_agent` + profile
3. **Pydantic schema** in `agents/schemas.py`
4. **Domain skill** `skills/ops/*-playbook`
5. **Agent playbook** `skills/agents/<key>-playbook`
6. **Dedicated toolbelt** with external-service ops tools
7. Shared belts: Parallel, Shopify/Linear/Fal/Meta/TikTok as relevant, Hermes bridge, Anda brain, analytics

## Ops tool modules
| Belt | Module | Examples |
|------|--------|----------|
| qa_ops | `tools/qa_ops_tools.py` | inspection checklist, CAPA draft |
| returns_ops | `tools/returns_ops_tools.py` | policy, cost, RMA draft |
| chargeback_ops | `tools/chargeback_ops_tools.py` | evidence pack, win score |
| cx_ops | `tools/cx_ops_tools.py` | severity, resolutions, reply |
| logistics_ops | `tools/logistics_ops_tools.py` | exception triage, recovery |
| creative_ops | `tools/creative_ops_tools.py` | variant matrix, queue |
| catalog_ops | `tools/catalog_ops_tools.py` | health, price audit |
| fraud_ops | `tools/fraud_ops_tools.py` | score, velocity |
| partnership_ops | `tools/partnership_ops_tools.py` | fit, revshare, outreach |
| tax_ops | `tools/tax_ops_tools.py` | nexus gate, doc pack |
| community_ops | `tools/community_ops_tools.py` | sentiment, UGC, crisis |
| experiment_ops | `tools/experiment_ops_tools.py` | design, ICE, decision rule |

Shopify/Meta/TikTok/Fal remain **draft-first / HITL** where money or live publish is involved.

## Verify
```bash
PYTHONPATH=. python -c "
from agents.qa_inspector import qa_inspector
from tools.skills_loader import skills_for
from agents.profiles import profile_by_key
p=profile_by_key('qa_inspector')
print(len(qa_inspector.tools), skills_for(*p.skills) is not None)
"
```
