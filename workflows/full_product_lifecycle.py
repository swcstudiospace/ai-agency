from agno.workflow import Step, Workflow
from teams.creative_team import creative_team
from teams.growth_team import growth_team
from teams.research_team import research_team
from teams.retention_team import retention_team
from teams.store_ops_team import store_ops_team
from teams.supply_chain_team import supply_chain_team

from workflows._grok_build import with_grok_build_guidance

full_product_lifecycle_workflow = Workflow(
    name="Full Product Lifecycle",
    description=(
        "Research → supply → creative/store → compliance-ready launch → retention. "
        "Grok Build is the bottom execution layer for multi-step shell/coding (SuperGrok)."
    ),
    steps=[
        Step(
            name="Research Score Price",
            team=research_team,
            description=with_grok_build_guidance("Discover niches, rank SKUs, unit economics."),
        ),
        Step(
            name="Supply Chain Setup",
            team=supply_chain_team,
            description=with_grok_build_guidance(
                "Locate suppliers, outreach drafts, shipping pipeline."
            ),
        ),
        Step(
            name="Brand Creative Listing",
            team=creative_team,
            description=with_grok_build_guidance("Brand, PromptWise/Fal UGC, listing drafts."),
        ),
        Step(
            name="Store Build Compliance",
            team=store_ops_team,
            description=with_grok_build_guidance(
                "Shopify drafts, policies, headless storefront notes."
            ),
        ),
        Step(
            name="Marketing Launch",
            team=growth_team,
            description=with_grok_build_guidance("Ad drafts only; HITL spend vault before launch."),
        ),
        Step(
            name="Retention Setup",
            team=retention_team,
            description=with_grok_build_guidance("CRM/post-purchase macros and loops."),
        ),
    ],
)
