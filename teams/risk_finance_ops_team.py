"""Risk & Finance Ops Team — markdown in prompts/teams/risk_finance_ops/."""

from agents.analyst import analyst
from agents.compliance_officer import compliance_officer
from agents.finance_controller import finance_controller
from agents.risk_fraud_analyst import risk_fraud_analyst
from agents.tax_compliance import tax_compliance

from teams._factory import build_team

risk_finance_ops_team = build_team(
    key="risk_finance_ops",
    name="Risk & Finance Ops Team",
    members=[risk_fraud_analyst, tax_compliance, finance_controller, compliance_officer, analyst],
    skill_names=(
        "claims-compliance",
        "roas-guardrails",
        "unit-economics",
        "linear-ops",
    ),
    fallback_instructions=["Fraud, tax, compliance, and finance controls for safe scale."],
)
