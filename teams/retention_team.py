"""Retention Team — markdown in prompts/teams/retention/."""

from agents.customer_success import customer_success
from agents.email_crm import email_crm

from teams._factory import build_team

retention_team = build_team(
    key="retention",
    name="Retention Team",
    members=[email_crm, customer_success],
    skill_names=("email-retention", "customer-support-macros", "fulfillment-playbook"),
    fallback_instructions=["Coordinate lifecycle email and CX macros."],
)
