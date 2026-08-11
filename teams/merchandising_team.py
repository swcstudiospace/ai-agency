"""Merchandising Team — markdown in prompts/teams/merchandising/."""

from agents.catalog_ops import catalog_ops
from agents.listing_specialist import listing_specialist
from agents.partnerships_manager import partnerships_manager
from agents.pricing_strategist import pricing_strategist
from teams._factory import build_team

merchandising_team = build_team(
    key="merchandising",
    name="Merchandising Team",
    members=[catalog_ops, listing_specialist, partnerships_manager, pricing_strategist],
    skill_names=(
        "unit-economics",
        "linear-ops",
        "product-scoring",
    ),
    fallback_instructions=["Catalog hygiene, listings, pricing, and partnership distribution."],
)
