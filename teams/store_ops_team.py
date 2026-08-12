"""Store Ops Team — markdown in prompts/teams/store_ops/."""

from agents.compliance_officer import compliance_officer
from agents.listing_specialist import listing_specialist
from agents.store_builder import store_builder

from teams._factory import build_team

store_ops_team = build_team(
    key="store_ops",
    name="Store Ops Team",
    members=[store_builder, listing_specialist, compliance_officer],
    skill_names=("listing-cro", "compliance-ads-claims"),
    fallback_instructions=["Coordinate store IA, PDPs, and compliance gate."],
)
