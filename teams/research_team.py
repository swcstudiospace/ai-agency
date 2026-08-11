"""Research Team — markdown in prompts/teams/research/."""

from agents.pricing_strategist import pricing_strategist
from agents.product_scout import product_scout
from agents.supplier_sourcer import supplier_sourcer
from teams._factory import build_team

research_team = build_team(
    key="research",
    name="Research Team",
    members=[product_scout, supplier_sourcer, pricing_strategist],
    skill_names=(
        "product-scoring",
        "unit-economics",
        "supplier-vetting",
        "product-scout-playbook",
        "linear-ops",
    ),
    fallback_instructions=["Coordinate product research with CM and supplier rigor."],
)
