from agno.workflow import Step, Workflow
from teams.agency_director import agency_director_team
from teams.growth_team import growth_team
from teams.retention_team import retention_team
from teams.supply_chain_team import supply_chain_team

weekly_performance_workflow = Workflow(
    name="Weekly Performance Review",
    description="Scorecard ads + CX + supply risk → leadership decisions",
    steps=[
        Step(name="Growth Scorecard", team=growth_team),
        Step(name="Retention and CX", team=retention_team),
        Step(name="Supply Risk", team=supply_chain_team),
        Step(name="Leadership Decisions", team=agency_director_team),
    ],
)
