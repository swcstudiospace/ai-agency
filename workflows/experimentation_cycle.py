from agno.workflow import Step, Workflow
from teams.growth_ops_team import growth_ops_team
from teams.merchandising_team import merchandising_team
from teams.risk_finance_ops_team import risk_finance_ops_team

experimentation_cycle_workflow = Workflow(
    name="Experimentation Cycle",
    description="Hypothesis backlog → growth ops run → analytics decision",
    steps=[
        Step(name="Design Experiments", team=growth_ops_team),
        Step(name="Merch/Store Variants", team=merchandising_team),
        Step(name="Score & Decide", team=risk_finance_ops_team),
    ],
)
