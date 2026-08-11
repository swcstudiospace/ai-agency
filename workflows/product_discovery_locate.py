"""Product discovery + supplier locate workflow (automated locate step)."""

from agno.workflow import Step, Workflow

from teams.research_team import research_team
from teams.supply_chain_team import supply_chain_team

product_discovery_locate_workflow = Workflow(
    name="Product Discovery & Locate",
    description=(
        "Rank dropshipping opportunities, then LOCATE real suppliers "
        "(Parallel search/task + supplier scorecards). HITL before samples/POs."
    ),
    steps=[
        Step(
            name="Discover Rank Products",
            team=research_team,
            description=(
                "Run niche discovery and score GO/TEST/NO-GO with unit economics. "
                "Prefer scripts.autonomous_product_rank for structured Parallel ultra/pro runs."
            ),
        ),
        Step(
            name="Locate Suppliers",
            team=supply_chain_team,
            description=(
                "For each GO/TEST SKU, call locate_suppliers_for_product / "
                "scripts.autonomous_product_locate. Build supplier shortlist, "
                "landed cost, MOQ, sample plan. Dual-write Linear. No PO payments."
            ),
        ),
    ],
)
