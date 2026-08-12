"""Pydantic I/O contracts for agency pipeline handoffs."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class Decision(str, Enum):
    GO = "GO"
    TEST = "TEST"
    NO_GO = "NO-GO"


class RiskLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class ComplianceVerdict(str, Enum):
    PASS = "PASS"
    REVISE = "REVISE"
    BLOCK = "BLOCK"


class EvidenceLink(BaseModel):
    url: str = Field(..., description="Source URL")
    note: str = Field("", description="Why this evidence matters")


class UnitEconomicsSnapshot(BaseModel):
    sell_price_usd: float
    cogs_usd: float
    shipping_usd: float
    target_cpa_usd: float = 18.0
    contribution_margin_usd: float | None = None
    contribution_margin_pct: float | None = None
    min_roas: float | None = None
    assumptions: str = ""


class ProductCandidate(BaseModel):
    name: str
    category: str
    avatar: str = ""
    decision: Decision
    composite_score: float = Field(..., ge=0, le=100)
    economics: UnitEconomicsSnapshot
    competition: RiskLevel = RiskLevel.medium
    shipping_risk: RiskLevel = RiskLevel.medium
    return_risk: RiskLevel = RiskLevel.medium
    differentiation_angle: str = ""
    why_now: str = ""
    risks: str = ""
    kill_criteria: str = ""
    next_experiment: str = ""
    evidence: list[EvidenceLink] = Field(default_factory=list)
    confidence_0_to_1: float = Field(0.5, ge=0, le=1)
    compliance_notes: str = ""


class ProductCandidateBatch(BaseModel):
    """Product Scout / Research Team primary output."""

    market_summary: str
    niche: str = ""
    candidates: list[ProductCandidate] = Field(default_factory=list)
    recommended_first_test: str | None = None
    open_questions: list[str] = Field(default_factory=list)


class SupplierScorecard(BaseModel):
    name: str
    score_0_to_100: float
    landed_cost_usd: float
    lead_time_days: int
    moq: int
    recommend: bool
    red_flags: list[str] = Field(default_factory=list)
    notes: str = ""
    evidence: list[EvidenceLink] = Field(default_factory=list)


class SupplierShortlist(BaseModel):
    product_name: str
    suppliers: list[SupplierScorecard] = Field(default_factory=list)
    recommended: str | None = None
    test_order_plan: str = ""
    backup_plan: str = ""


class PriceOfferPlan(BaseModel):
    product_name: str
    list_price_usd: float
    compare_at_usd: float | None = None
    bundle_options: list[str] = Field(default_factory=list)
    free_shipping_threshold_usd: float | None = None
    economics: UnitEconomicsSnapshot
    ab_tests: list[str] = Field(default_factory=list)
    rationale: str = ""


class BrandPositioning(BaseModel):
    brand_name_options: list[str] = Field(default_factory=list)
    avatar: str
    promise: str
    proof_pillars: list[str] = Field(default_factory=list)
    voice_do: list[str] = Field(default_factory=list)
    voice_dont: list[str] = Field(default_factory=list)
    competitive_frame: str = ""
    tagline_options: list[str] = Field(default_factory=list)


class CreativeConcept(BaseModel):
    rank: int
    name: str
    hook: str
    angle: str
    script_15s: str = ""
    script_30s: str = ""
    on_screen_text: list[str] = Field(default_factory=list)
    cta: str = ""
    formats: list[str] = Field(default_factory=list)
    compliance_notes: str = ""
    hypothesis: str = ""


class CreativeBriefBatch(BaseModel):
    product_name: str
    avatar: str
    concepts: list[CreativeConcept] = Field(default_factory=list)
    production_notes: str = ""


class ListingPackage(BaseModel):
    product_name: str
    title: str
    bullets: list[str] = Field(default_factory=list)
    description_html_outline: str = ""
    faq: list[str] = Field(default_factory=list)
    image_order: list[str] = Field(default_factory=list)
    seo_title: str = ""
    seo_description: str = ""
    price_usd: float
    compliance_notes: str = ""


class ComplianceReview(BaseModel):
    asset_type: str = Field(..., description="creative|pdp|email|landing|offer")
    asset_name: str = ""
    verdict: ComplianceVerdict
    issues: list[str] = Field(default_factory=list)
    required_rewrites: list[str] = Field(default_factory=list)
    allowed_claims: list[str] = Field(default_factory=list)
    blocked_claims: list[str] = Field(default_factory=list)
    policy_notes: str = ""


class CampaignPlan(BaseModel):
    product_name: str
    objective: str = "conversions"
    daily_budget_usd: float
    learning_budget_usd: float
    target_cpa_usd: float
    kill_roas: float
    scale_roas: float
    structure_notes: str = ""
    audiences: list[str] = Field(default_factory=list)
    creative_ids_or_names: list[str] = Field(default_factory=list)
    kill_criteria: str = ""
    autonomy_level: str = "L2"
    requires_human_approval: bool = True


class EmailFlowSpec(BaseModel):
    flow_name: str
    trigger: str
    emails: list[str] = Field(default_factory=list)
    goals: str = ""
    compliance_notes: str = ""
    cm_impact_notes: str = ""


class EmailLifecyclePlan(BaseModel):
    product_or_brand: str
    flows: list[EmailFlowSpec] = Field(default_factory=list)
    sms_rules: str = ""


class SupportMacroPack(BaseModel):
    topic: str
    macros: list[str] = Field(default_factory=list)
    escalation_rules: str = ""
    policy_summary: str = ""


class FulfillmentSLAPlan(BaseModel):
    product_name: str
    processing_hours_target: int = 48
    transit_guidance: str = ""
    tracking_sla: str = ""
    exception_playbook: list[str] = Field(default_factory=list)
    customer_eta_copy: str = ""


class InventoryPlan(BaseModel):
    product_name: str
    test_buy_units: int
    reorder_point_units: int | None = None
    safety_stock_units: int | None = None
    cash_at_risk_usd: float | None = None
    rationale: str = ""
    do_not_bulk_until: str = ""


class ScorecardKPI(BaseModel):
    name: str
    value: str
    trend: str = ""
    note: str = ""


class WeeklyScorecard(BaseModel):
    period: str
    kpis: list[ScorecardKPI] = Field(default_factory=list)
    wins: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)
    budget_recommendation: str = ""


class BudgetDecision(BaseModel):
    channel: str
    daily_cap_usd: float
    weekly_cap_usd: float
    rationale: str
    requires_human_approval: bool = True
    kill_switch: str = ""


class DirectorDecision(BaseModel):
    """Hermes Ops / Director Team orchestration output."""

    goal: str
    decision: str
    autonomy_level: str = "L2"
    recommended_workflow_or_team: str = ""
    margin_summary: str = ""
    risk_summary: str = ""
    confidence_0_to_1: float = Field(0.5, ge=0, le=1)
    next_actions: list[str] = Field(default_factory=list)
    requires_human_approval: list[str] = Field(default_factory=list)
    linear_issue_titles: list[str] = Field(default_factory=list)


class SEOContentPlan(BaseModel):
    product_or_category: str
    primary_keywords: list[str] = Field(default_factory=list)
    secondary_keywords: list[str] = Field(default_factory=list)
    page_types: list[str] = Field(default_factory=list)
    outline: str = ""
    internal_links: list[str] = Field(default_factory=list)


class StoreIAPlan(BaseModel):
    homepage_sections: list[str] = Field(default_factory=list)
    nav_items: list[str] = Field(default_factory=list)
    trust_stack: list[str] = Field(default_factory=list)
    policy_pages: list[str] = Field(default_factory=list)
    mobile_priorities: list[str] = Field(default_factory=list)
    checkout_friction_fixes: list[str] = Field(default_factory=list)


class InfluencerPlan(BaseModel):
    product_name: str
    creator_profile: str
    outreach_angles: list[str] = Field(default_factory=list)
    deliverables: list[str] = Field(default_factory=list)
    budget_per_asset_usd: float | None = None
    usage_rights: str = ""
    compliance_notes: str = ""


# ─── Ops expansion schemas (12 new agents) ───────────────────

class QAInspectionReport(BaseModel):
    sku: str
    sample_id: str = ""
    verdict: str = Field(..., description="PASS|CONDITIONAL|FAIL")
    defects: list[str] = Field(default_factory=list)
    measurements: str = ""
    photos_needed: list[str] = Field(default_factory=list)
    supplier_feedback: str = ""
    ship_hold: bool = False
    next_actions: list[str] = Field(default_factory=list)
    confidence_0_to_1: float = Field(0.6, ge=0, le=1)


class ReturnsOpsPlan(BaseModel):
    order_id: str = ""
    reason_codes: list[str] = Field(default_factory=list)
    disposition: str = Field(..., description="refund|exchange|deny|partial")
    restockable: bool = False
    reverse_label: bool = True
    customer_message: str = ""
    cost_estimate_usd: float = 0.0
    prevention_notes: str = ""
    next_actions: list[str] = Field(default_factory=list)


class ChargebackCasePlan(BaseModel):
    case_id: str = ""
    reason: str = ""
    amount_usd: float = 0.0
    win_probability_0_to_1: float = Field(0.5, ge=0, le=1)
    evidence_checklist: list[str] = Field(default_factory=list)
    representment_summary: str = ""
    prevention_actions: list[str] = Field(default_factory=list)
    recommend: str = Field(..., description="FIGHT|ACCEPT|PARTIAL")


class EscalationPlaybook(BaseModel):
    ticket_id: str = ""
    severity: RiskLevel = RiskLevel.medium
    customer_tier: str = "standard"
    root_cause: str = ""
    resolution_options: list[str] = Field(default_factory=list)
    recommended_resolution: str = ""
    brand_risk: RiskLevel = RiskLevel.medium
    follow_ups: list[str] = Field(default_factory=list)


class LogisticsExceptionPlan(BaseModel):
    tracking: str = ""
    exception_type: str = ""
    carrier: str = ""
    eta_revision: str = ""
    recovery_actions: list[str] = Field(default_factory=list)
    customer_comms: str = ""
    cost_impact_usd: float = 0.0
    escalate_to_supplier: bool = False


class CreativeOpsQueue(BaseModel):
    campaign: str = ""
    variants_ready: list[str] = Field(default_factory=list)
    variants_in_production: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    compliance_status: str = ""
    next_48h_ship_list: list[str] = Field(default_factory=list)
    ugc_requests: list[str] = Field(default_factory=list)


class CatalogOpsPlan(BaseModel):
    sku_actions: list[str] = Field(default_factory=list)
    price_fixes: list[str] = Field(default_factory=list)
    publish_queue: list[str] = Field(default_factory=list)
    archive_candidates: list[str] = Field(default_factory=list)
    merchandising_notes: str = ""
    risks: list[str] = Field(default_factory=list)


class FraudRiskAssessment(BaseModel):
    order_id: str = ""
    risk_score_0_to_100: float = Field(..., ge=0, le=100)
    signals: list[str] = Field(default_factory=list)
    action: str = Field(..., description="ALLOW|REVIEW|HOLD|CANCEL")
    customer_impact: str = ""
    evidence: list[str] = Field(default_factory=list)
    notes: str = ""


class PartnershipPipeline(BaseModel):
    opportunities: list[str] = Field(default_factory=list)
    tier: str = "affiliate"
    economics_notes: str = ""
    outreach_sequence: list[str] = Field(default_factory=list)
    contract_flags: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)


class TaxComplianceBrief(BaseModel):
    regions: list[str] = Field(default_factory=list)
    nexus_notes: str = ""
    collection_status: str = ""
    risks: list[str] = Field(default_factory=list)
    required_actions: list[str] = Field(default_factory=list)
    documentation: list[str] = Field(default_factory=list)
    verdict: str = Field(..., description="OK|ATTENTION|BLOCK_SHIP")


class CommunityOpsPlan(BaseModel):
    channels: list[str] = Field(default_factory=list)
    sentiment: str = ""
    ugc_opportunities: list[str] = Field(default_factory=list)
    crisis_flags: list[str] = Field(default_factory=list)
    response_queue: list[str] = Field(default_factory=list)
    content_to_amplify: list[str] = Field(default_factory=list)


class ExperimentBacklog(BaseModel):
    hypothesis: str
    primary_metric: str
    secondary_metrics: list[str] = Field(default_factory=list)
    variants: list[str] = Field(default_factory=list)
    sample_size_notes: str = ""
    duration_days: int = 14
    guardrails: list[str] = Field(default_factory=list)
    decision_rule: str = ""
    ranked_backlog: list[str] = Field(default_factory=list)
