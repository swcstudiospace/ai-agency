"""Logistics Ops Team — markdown in prompts/teams/logistics_ops/."""

from agents.fulfillment_ops import fulfillment_ops
from agents.logistics_coordinator import logistics_coordinator
from agents.inventory_planner import inventory_planner
from agents.qa_inspector import qa_inspector
from teams._factory import build_team

logistics_ops_team = build_team(
    key="logistics_ops",
    name="Logistics Ops Team",
    members=[fulfillment_ops, logistics_coordinator, inventory_planner, qa_inspector],
    skill_names=(
        "linear-ops",
        "supplier-vetting",
        "autonomy-levels",
    ),
    fallback_instructions=["Clear shipping exceptions, inventory, QA gates, and fulfillment SLAs."],
)
