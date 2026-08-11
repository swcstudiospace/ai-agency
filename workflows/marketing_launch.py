from agno.workflow import Step, Workflow

from teams.creative_team import creative_team
from teams.growth_team import growth_team
from teams.store_ops_team import store_ops_team

marketing_launch_workflow = Workflow(
    name="Marketing Launch",
    description="Creatives + compliance store check → budgeted campaign launch",
    steps=[
        Step(name="Prepare Creatives", team=creative_team),
        Step(name="Store Compliance Gate", team=store_ops_team),
        Step(name="Launch Campaign", team=growth_team),
    ],
)
