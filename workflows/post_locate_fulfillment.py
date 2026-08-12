"""Post-locate: supplier outreach + shipping pipeline setup."""

from agno.workflow import Step, Workflow
from teams.store_ops_team import store_ops_team
from teams.supply_chain_team import supply_chain_team

post_locate_fulfillment_workflow = Workflow(
    name="Post-Locate Fulfillment Setup",
    description=(
        "After supplier locate: draft sample/dropship outreach emails (Gmail HITL), "
        "design shipping/order-routing pipeline, Shopify bootstrap + ego.engineer domain plan."
    ),
    steps=[
        Step(
            name="Seller Outreach Drafts",
            team=supply_chain_team,
            description=(
                "Use draft_supplier_outreach_email / batch_outreach_from_locate / "
                "scripts.autonomous_post_locate. Open Gmail compose via bridge for human send. "
                "Never auto-send or pay samples."
            ),
        ),
        Step(
            name="Shipping Pipeline + Store Bootstrap",
            team=store_ops_team,
            description=(
                "design_shipping_pipeline + setup_order_routing_playbook + "
                "shopify_bootstrap_checklist + shopify_domain_plan(ego.engineer). "
                "Prepare policies, rates, webhooks for Oxygen headless storefront."
            ),
        ),
    ],
)
