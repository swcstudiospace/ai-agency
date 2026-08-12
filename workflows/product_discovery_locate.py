"""Product discovery + supplier locate workflow (automated locate step)."""

from agno.workflow import Step, Workflow
from teams.research_team import research_team
from teams.supply_chain_team import supply_chain_team

from workflows._warp import with_warp_guidance

product_discovery_locate_workflow = Workflow(
    name="Product Discovery & Locate",
    description=(
        "Rank dropshipping opportunities, LOCATE suppliers, then prepare "
        "outreach + shipping pipeline. Offload multi-step terminal work to Warp Oz CLI. "
        "HITL before samples/POs."
    ),
    steps=[
        Step(
            name="Discover Rank Products",
            team=research_team,
            description=with_warp_guidance(
                "Run niche discovery and score GO/TEST/NO-GO with unit economics. "
                "Prefer scripts.autonomous_product_rank for structured Parallel ultra/pro runs."
            ),
        ),
        Step(
            name="Locate Suppliers",
            team=supply_chain_team,
            description=with_warp_guidance(
                "For each GO/TEST SKU, call locate_suppliers_for_product / "
                "scripts.autonomous_product_locate. Build supplier shortlist. No PO payments."
            ),
        ),
        Step(
            name="Outreach + Shipping Plan",
            team=supply_chain_team,
            description=with_warp_guidance(
                "scripts.autonomous_post_locate: draft sample emails, shipping pipeline, "
                "Shopify bootstrap + ego.engineer domain plan."
            ),
        ),
    ],
)
