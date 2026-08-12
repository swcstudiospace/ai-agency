from agno.workflow import Step, Workflow
from teams.agency_director import agency_director_team
from teams.cx_operations_team import cx_operations_team
from teams.risk_finance_ops_team import risk_finance_ops_team

incident_response_ops_workflow = Workflow(
    name="Incident Response Ops",
    description="Fraud/risk → CX escalation → chargeback path for critical incidents",
    steps=[
        Step(name="Risk Triage", team=risk_finance_ops_team),
        Step(name="CX Containment", team=cx_operations_team),
        Step(name="Director Review", team=agency_director_team),
    ],
)
