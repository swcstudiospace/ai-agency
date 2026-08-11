from agno.workflow import Step, Workflow

from teams.creative_team import creative_team
from teams.growth_ops_team import growth_ops_team
from teams.merchandising_team import merchandising_team

creative_production_ops_workflow = Workflow(
    name="Creative Production Ops",
    description="Creative brief → ads creative ops → growth launch readiness",
    steps=[
        Step(name="Creative Direction", team=creative_team),
        Step(name="Asset Factory", team=growth_ops_team),
        Step(name="Store Sync", team=merchandising_team),
    ],
)
