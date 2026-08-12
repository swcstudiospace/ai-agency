"""Agency Director Team — markdown in prompts/teams/agency_director/."""

from agents.analyst import analyst
from agents.compliance_officer import compliance_officer
from agents.finance_controller import finance_controller
from agents.hermes_ops import hermes_ops

from teams._factory import build_team

agency_director_team = build_team(
    key="agency_director",
    name="Agency Director Team",
    members=[hermes_ops, analyst, finance_controller, compliance_officer],
    skill_names=(
        "autonomy-levels",
        "roas-guardrails",
        "unit-economics",
        "compliance-ads-claims",
        "linear-ops",
        "hermes-ops-playbook",
    ),
    fallback_instructions=["Coordinate leadership; enforce budget and compliance gates."],
)
