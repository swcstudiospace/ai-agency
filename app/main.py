import os
import sys
from pathlib import Path

# ── ops 12
from agents.ads_creative_ops import ads_creative_ops

# ── original 18
from agents.analyst import analyst
from agents.brand_strategist import brand_strategist
from agents.catalog_ops import catalog_ops
from agents.chargeback_specialist import chargeback_specialist
from agents.community_manager import community_manager
from agents.compliance_officer import compliance_officer
from agents.creative_director import creative_director
from agents.customer_success import customer_success
from agents.cx_escalations import cx_escalations
from agents.email_crm import email_crm
from agents.experimentation_lead import experimentation_lead
from agents.finance_controller import finance_controller
from agents.fulfillment_ops import fulfillment_ops
from agents.growth_media_buyer import growth_media_buyer
from agents.hermes_ops import hermes_ops
from agents.influencer_manager import influencer_manager
from agents.inventory_planner import inventory_planner
from agents.listing_specialist import listing_specialist
from agents.logistics_coordinator import logistics_coordinator
from agents.partnerships_manager import partnerships_manager
from agents.pricing_strategist import pricing_strategist
from agents.product_scout import product_scout
from agents.qa_inspector import qa_inspector
from agents.returns_specialist import returns_specialist
from agents.risk_fraud_analyst import risk_fraud_analyst
from agents.seo_content import seo_content
from agents.store_builder import store_builder
from agents.supplier_sourcer import supplier_sourcer
from agents.tax_compliance import tax_compliance
from agno.db.sqlite import SqliteDb
from agno.os import AgentOS
from agno.os.config import MCPServerConfig
from dotenv import load_dotenv

# ── teams 7 + 5
from teams.agency_director import agency_director_team
from teams.creative_team import creative_team
from teams.cx_operations_team import cx_operations_team
from teams.growth_ops_team import growth_ops_team
from teams.growth_team import growth_team
from teams.logistics_ops_team import logistics_ops_team
from teams.merchandising_team import merchandising_team
from teams.research_team import research_team
from teams.retention_team import retention_team
from teams.risk_finance_ops_team import risk_finance_ops_team
from teams.store_ops_team import store_ops_team
from teams.supply_chain_team import supply_chain_team
from tools.mcp_custom import get_mcp_custom_tools

# ── workflows 5 + 5
from workflows.creative_production_ops import creative_production_ops_workflow
from workflows.experimentation_cycle import experimentation_cycle_workflow
from workflows.full_product_lifecycle import full_product_lifecycle_workflow
from workflows.incident_response_ops import incident_response_ops_workflow
from workflows.logistics_exception_handling import logistics_exception_handling_workflow
from workflows.marketing_launch import marketing_launch_workflow
from workflows.post_locate_fulfillment import post_locate_fulfillment_workflow
from workflows.post_purchase_ops import post_purchase_ops_workflow
from workflows.product_discovery_locate import product_discovery_locate_workflow
from workflows.returns_rma_pipeline import returns_rma_pipeline_workflow
from workflows.supplier_onboarding import supplier_onboarding_workflow
from workflows.weekly_performance import weekly_performance_workflow

load_dotenv()

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

Path("tmp").mkdir(parents=True, exist_ok=True)
db = SqliteDb(db_file="tmp/agency.db")

_mcp_hosts = [
    h.strip()
    for h in (os.getenv("AGENCY_MCP_ALLOWED_HOSTS") or "localhost,127.0.0.1").split(",")
    if h.strip()
]

mcp_config = MCPServerConfig(
    enable_builtin_tools=True,
    result_mode=os.getenv("AGENCY_MCP_RESULT_MODE", "trimmed"),
    tools=get_mcp_custom_tools(),
    allowed_hosts=_mcp_hosts,
)

agent_os = AgentOS(
    id="ai-dropshipping-agency",
    name="AI Dropshipping Agency",
    description=(
        "Enterprise AI Dropshipping Agency — 30 agents / 12 teams / 12 workflows. "
        "Stack: Hermes → Agno → Grok Build. SuperGrok + Parallel. CodeRabbit in CI."
    ),
    agents=[
        hermes_ops,
        product_scout,
        supplier_sourcer,
        pricing_strategist,
        brand_strategist,
        creative_director,
        listing_specialist,
        seo_content,
        store_builder,
        compliance_officer,
        growth_media_buyer,
        influencer_manager,
        email_crm,
        customer_success,
        fulfillment_ops,
        inventory_planner,
        analyst,
        finance_controller,
        # ops expansion
        qa_inspector,
        returns_specialist,
        chargeback_specialist,
        cx_escalations,
        logistics_coordinator,
        ads_creative_ops,
        catalog_ops,
        risk_fraud_analyst,
        partnerships_manager,
        tax_compliance,
        community_manager,
        experimentation_lead,
    ],
    teams=[
        agency_director_team,
        research_team,
        supply_chain_team,
        creative_team,
        store_ops_team,
        growth_team,
        retention_team,
        cx_operations_team,
        logistics_ops_team,
        growth_ops_team,
        risk_finance_ops_team,
        merchandising_team,
    ],
    workflows=[
        product_discovery_locate_workflow,
        post_locate_fulfillment_workflow,
        full_product_lifecycle_workflow,
        marketing_launch_workflow,
        supplier_onboarding_workflow,
        post_purchase_ops_workflow,
        weekly_performance_workflow,
        incident_response_ops_workflow,
        returns_rma_pipeline_workflow,
        creative_production_ops_workflow,
        experimentation_cycle_workflow,
        logistics_exception_handling_workflow,
    ],
    db=db,
    tracing=True,
    mcp_server=mcp_config,
)

app = agent_os.get_app()

if __name__ == "__main__":
    port = int(os.getenv("AGENCY_PORT", "7777"))
    agent_os.serve(app="app.main:app", reload=True, port=port)
