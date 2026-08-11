"""CX Operations Team — markdown in prompts/teams/cx_ops/."""

from agents.customer_success import customer_success
from agents.returns_specialist import returns_specialist
from agents.chargeback_specialist import chargeback_specialist
from agents.cx_escalations import cx_escalations
from teams._factory import build_team

cx_operations_team = build_team(
    key="cx_ops",
    name="CX Operations Team",
    members=[customer_success, returns_specialist, chargeback_specialist, cx_escalations],
    skill_names=(
        "linear-ops",
        "autonomy-levels",
        "roas-guardrails",
    ),
    fallback_instructions=["Coordinate CX: tickets, returns, chargebacks, escalations with CM awareness."],
)
