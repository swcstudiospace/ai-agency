from agno.workflow import Step, Workflow
from teams.research_team import research_team
from teams.supply_chain_team import supply_chain_team

supplier_onboarding_workflow = Workflow(
    name="Supplier Onboarding",
    description="Shortlist suppliers → score landed cost → test-order plan → inventory policy",
    steps=[
        Step(name="Supplier Shortlist", team=research_team),
        Step(name="Vet and Plan Inventory", team=supply_chain_team),
    ],
)
