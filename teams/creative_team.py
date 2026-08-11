"""Creative Team — markdown in prompts/teams/creative/."""

from agents.brand_strategist import brand_strategist
from agents.creative_director import creative_director
from agents.listing_specialist import listing_specialist
from agents.seo_content import seo_content
from teams._factory import build_team

creative_team = build_team(
    key="creative",
    name="Creative Team",
    members=[brand_strategist, creative_director, listing_specialist, seo_content],
    skill_names=("ugc-hooks", "creative-briefing", "listing-cro", "compliance-ads-claims"),
    fallback_instructions=["Coordinate brand, creatives, listings, and SEO."],
)
