from agno.workflow import Step, Workflow
from teams.retention_team import retention_team
from teams.supply_chain_team import supply_chain_team

post_purchase_ops_workflow = Workflow(
    name="Post Purchase Ops",
    description="Fulfillment exceptions + support macros + retention saves",
    steps=[
        Step(name="Fulfillment Exceptions", team=supply_chain_team),
        Step(name="CX and Retention Saves", team=retention_team),
    ],
)
