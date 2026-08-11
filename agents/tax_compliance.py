"""tax_compliance agent — thin wiring; brain lives in prompts/tax_compliance/."""

from agents._factory import build_agent
from agents.profiles import profile_by_key

_p = profile_by_key("tax_compliance")

tax_compliance = build_agent(
    name=_p.name,
    role=_p.role,
    persona=_p.key,
    toolbelts=_p.toolbelts,
    skill_names=_p.skills,
    output_schema=_p.output_schema,
    temperature=_p.temperature,
    add_history_to_context=_p.add_history,
    num_history_runs=_p.num_history_runs,
    use_json_mode=_p.use_json_mode,
)
