from agno.workflow import Step, Workflow

from teams.creative_team import creative_team
from teams.growth_team import growth_team
from teams.research_team import research_team
from teams.retention_team import retention_team
from teams.store_ops_team import store_ops_team
from teams.supply_chain_team import supply_chain_team

full_product_lifecycle_workflow = Workflow(
    name="Full Product Lifecycle",
    description="Research → supply → creative/store → compliance-ready launch → retention setup",
    steps=[
        Step(name="Research Score Price", team=research_team),
        Step(name="Supply Chain Setup", team=supply_chain_team),
        Step(name="Brand Creative Listing", team=creative_team),
        Step(name="Store Build Compliance", team=store_ops_team),
        Step(name="Marketing Launch", team=growth_team),
        Step(name="Retention Setup", team=retention_team),
    ],
)
