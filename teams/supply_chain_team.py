"""Supply Chain Team — markdown in prompts/teams/supply_chain/."""

from agents.fulfillment_ops import fulfillment_ops
from agents.inventory_planner import inventory_planner
from agents.supplier_sourcer import supplier_sourcer

from teams._factory import build_team

supply_chain_team = build_team(
    key="supply_chain",
    name="Supply Chain Team",
    members=[supplier_sourcer, inventory_planner, fulfillment_ops],
    skill_names=("supplier-vetting", "fulfillment-playbook", "unit-economics"),
    fallback_instructions=["Coordinate suppliers, inventory, and fulfillment SLAs."],
)
