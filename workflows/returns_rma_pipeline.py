from agno.workflow import Step, Workflow

from teams.cx_operations_team import cx_operations_team
from teams.logistics_ops_team import logistics_ops_team
from teams.risk_finance_ops_team import risk_finance_ops_team

returns_rma_pipeline_workflow = Workflow(
    name="Returns RMA Pipeline",
    description="Returns intake → logistics reverse → CX resolution → analytics",
    steps=[
        Step(name="Returns Intake", team=cx_operations_team),
        Step(name="Reverse Logistics", team=logistics_ops_team),
        Step(name="Finance Impact", team=risk_finance_ops_team),
    ],
)
