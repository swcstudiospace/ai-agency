export type AgentStatus = "idle" | "thinking" | "tooling" | "awaiting_hitl" | "done" | "error";

export type TeamId =
  | "director"
  | "research"
  | "supply"
  | "creative"
  | "store"
  | "growth"
  | "retention"
  | "cx_ops"
  | "logistics_ops"
  | "growth_ops"
  | "risk_finance"
  | "merch";

export interface AgentDef {
  id: string;
  name: string;
  role: string;
  team: TeamId;
  hue: number; // 0-360 for generative color
  tools: string[];
}

export const TEAMS: Record<
  TeamId,
  { name: string; blurb: string; accent: string }
> = {
  director: { name: "Director", blurb: "Hermes orchestration", accent: "#a78bfa" },
  research: { name: "Research", blurb: "Find & price winners", accent: "#38bdf8" },
  supply: { name: "Supply Chain", blurb: "Source & land cost", accent: "#34d399" },
  creative: { name: "Creative", blurb: "Brand & assets", accent: "#f472b6" },
  store: { name: "Store Ops", blurb: "PDP & compliance", accent: "#fb923c" },
  growth: { name: "Growth", blurb: "Paid + creators", accent: "#facc15" },
  retention: { name: "Retention", blurb: "Email & LTV", accent: "#c084fc" },
  cx_ops: { name: "CX Ops", blurb: "Returns & escalations", accent: "#fb7185" },
  logistics_ops: { name: "Logistics Ops", blurb: "Ship & QA gates", accent: "#2dd4bf" },
  growth_ops: { name: "Growth Ops", blurb: "Creative factory & CRO", accent: "#e879f9" },
  risk_finance: { name: "Risk & Finance", blurb: "Fraud, tax, P&L", accent: "#fbbf24" },
  merch: { name: "Merchandising", blurb: "Catalog & partners", accent: "#60a5fa" },
};

export const AGENTS: AgentDef[] = [
  { id: "hermes_ops", name: "Hermes Ops", role: "Agency Director", team: "director", hue: 265, tools: ["Linear", "Spend vault", "Bridge"] },
  { id: "product_scout", name: "Product Scout", role: "Opportunity scoring", team: "research", hue: 200, tools: ["Parallel", "Economics"] },
  { id: "supplier_sourcer", name: "Supplier Sourcer", role: "Vetting & landed cost", team: "supply", hue: 155, tools: ["Parallel", "Supplier"] },
  { id: "pricing_strategist", name: "Pricing Strategist", role: "Offers & AOV", team: "research", hue: 190, tools: ["Economics"] },
  { id: "brand_strategist", name: "Brand Strategist", role: "Positioning", team: "creative", hue: 320, tools: ["Parallel"] },
  { id: "creative_director", name: "Creative Director", role: "Campaign vision", team: "creative", hue: 330, tools: ["Fal", "UGC"] },
  { id: "listing_specialist", name: "Listing Specialist", role: "PDP conversion", team: "creative", hue: 310, tools: ["Shopify"] },
  { id: "seo_content", name: "SEO Content", role: "Organic content", team: "creative", hue: 300, tools: ["Parallel"] },
  { id: "store_builder", name: "Store Builder", role: "Store IA", team: "store", hue: 25, tools: ["Shopify"] },
  { id: "compliance_officer", name: "Compliance Officer", role: "Claims safety", team: "risk_finance", hue: 45, tools: ["Claims"] },
  { id: "growth_media_buyer", name: "Growth Media Buyer", role: "Paid social", team: "growth", hue: 50, tools: ["Meta", "TikTok", "HITL"] },
  { id: "influencer_manager", name: "Influencer Manager", role: "Creator ops", team: "growth", hue: 55, tools: ["Outreach"] },
  { id: "email_crm", name: "Email CRM", role: "Lifecycle", team: "retention", hue: 280, tools: ["Flows"] },
  { id: "customer_success", name: "Customer Success", role: "Support macros", team: "cx_ops", hue: 350, tools: ["Shopify", "Macros"] },
  { id: "fulfillment_ops", name: "Fulfillment Ops", role: "SLA reality", team: "logistics_ops", hue: 170, tools: ["Logistics"] },
  { id: "inventory_planner", name: "Inventory Planner", role: "Stock signals", team: "logistics_ops", hue: 165, tools: ["Analytics"] },
  { id: "analyst", name: "Analyst", role: "Scorecards", team: "risk_finance", hue: 40, tools: ["Analytics", "Ads"] },
  { id: "finance_controller", name: "Finance Controller", role: "Budgets & caps", team: "risk_finance", hue: 42, tools: ["Spend", "Economics"] },
  // ops 12
  { id: "qa_inspector", name: "QA Inspector", role: "Sample gates", team: "logistics_ops", hue: 160, tools: ["QA ops"] },
  { id: "returns_specialist", name: "Returns Specialist", role: "RMA & refunds", team: "cx_ops", hue: 355, tools: ["Returns", "Shopify"] },
  { id: "chargeback_specialist", name: "Chargeback Specialist", role: "Disputes", team: "cx_ops", hue: 0, tools: ["Chargeback"] },
  { id: "cx_escalations", name: "CX Escalations", role: "VIP / crisis", team: "cx_ops", hue: 348, tools: ["CX ops"] },
  { id: "logistics_coordinator", name: "Logistics Coordinator", role: "Exceptions", team: "logistics_ops", hue: 175, tools: ["Tracking"] },
  { id: "ads_creative_ops", name: "Ads Creative Ops", role: "Creative factory", team: "growth_ops", hue: 290, tools: ["Fal", "Meta draft"] },
  { id: "catalog_ops", name: "Catalog Ops", role: "SKU hygiene", team: "merch", hue: 210, tools: ["Catalog", "Shopify"] },
  { id: "risk_fraud_analyst", name: "Risk Fraud Analyst", role: "Order risk", team: "risk_finance", hue: 35, tools: ["Fraud ops"] },
  { id: "partnerships_manager", name: "Partnerships Manager", role: "Affiliate / B2B", team: "merch", hue: 215, tools: ["Partners"] },
  { id: "tax_compliance", name: "Tax Compliance", role: "Nexus / VAT gates", team: "risk_finance", hue: 48, tools: ["Tax ops"] },
  { id: "community_manager", name: "Community Manager", role: "Reputation & UGC", team: "growth_ops", hue: 295, tools: ["Community"] },
  { id: "experimentation_lead", name: "Experimentation Lead", role: "CRO tests", team: "growth_ops", hue: 285, tools: ["Experiments"] },
];

export const WORKFLOWS = [
  { id: "full_product_lifecycle", name: "Full Product Lifecycle", steps: 6 },
  { id: "marketing_launch", name: "Marketing Launch", steps: 3 },
  { id: "supplier_onboarding", name: "Supplier Onboarding", steps: 2 },
  { id: "post_purchase_ops", name: "Post Purchase Ops", steps: 2 },
  { id: "weekly_performance", name: "Weekly Performance", steps: 4 },
  { id: "incident_response_ops", name: "Incident Response Ops", steps: 3 },
  { id: "returns_rma_pipeline", name: "Returns RMA Pipeline", steps: 3 },
  { id: "creative_production_ops", name: "Creative Production Ops", steps: 3 },
  { id: "experimentation_cycle", name: "Experimentation Cycle", steps: 3 },
  { id: "logistics_exception_handling", name: "Logistics Exception Handling", steps: 3 },
];

export function agentColor(hue: number, a = 1) {
  return `hsla(${hue}, 85%, 62%, ${a})`;
}
