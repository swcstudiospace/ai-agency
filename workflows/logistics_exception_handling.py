from agno.workflow import Step, Workflow
from teams.cx_operations_team import cx_operations_team
from teams.logistics_ops_team import logistics_ops_team
from teams.supply_chain_team import supply_chain_team

logistics_exception_handling_workflow = Workflow(
    name="Logistics Exception Handling",
    description="Shipping exception → recovery → customer comms",
    steps=[
        Step(name="Exception Diagnose", team=logistics_ops_team),
        Step(name="Customer Update", team=cx_operations_team),
        Step(name="Supplier Follow-up", team=supply_chain_team),
    ],
)
