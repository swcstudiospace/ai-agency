"""Growth Ops Team — markdown in prompts/teams/growth_ops/."""

from agents.ads_creative_ops import ads_creative_ops
from agents.community_manager import community_manager
from agents.experimentation_lead import experimentation_lead
from agents.growth_media_buyer import growth_media_buyer

from teams._factory import build_team

growth_ops_team = build_team(
    key="growth_ops",
    name="Growth Ops Team",
    members=[growth_media_buyer, ads_creative_ops, experimentation_lead, community_manager],
    skill_names=(
        "ugc-hooks",
        "roas-guardrails",
        "claims-compliance",
        "linear-ops",
    ),
    fallback_instructions=["Run creative ops, experiments, community signal, and media buying under HITL spend."],
)
