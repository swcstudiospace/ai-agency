"""Growth Team — markdown in prompts/teams/growth/."""

from agents.analyst import analyst
from agents.finance_controller import finance_controller
from agents.growth_media_buyer import growth_media_buyer
from agents.influencer_manager import influencer_manager
from teams._factory import build_team

growth_team = build_team(
    key="growth",
    name="Growth Team",
    members=[growth_media_buyer, influencer_manager, analyst, finance_controller],
    skill_names=("roas-guardrails", "paid-social-structure", "unit-economics", "linear-ops"),
    fallback_instructions=["Coordinate paid growth under ROAS and budget caps."],
)
