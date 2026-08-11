"""Pydantic I/O contracts for agency pipeline handoffs."""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

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
    contribution_margin_usd: Optional[float] = None
    contribution_margin_pct: Optional[float] = None
    min_roas: Optional[float] = None
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
    evidence: List[EvidenceLink] = Field(default_factory=list)
    confidence_0_to_1: float = Field(0.5, ge=0, le=1)
    compliance_notes: str = ""


class ProductCandidateBatch(BaseModel):
    """Product Scout / Research Team primary output."""

    market_summary: str
    niche: str = ""
    candidates: List[ProductCandidate] = Field(default_factory=list)
    recommended_first_test: Optional[str] = None
    open_questions: List[str] = Field(default_factory=list)


class SupplierScorecard(BaseModel):
    name: str
    score_0_to_100: float
    landed_cost_usd: float
    lead_time_days: int
    moq: int
    recommend: bool
    red_flags: List[str] = Field(default_factory=list)
    notes: str = ""
    evidence: List[EvidenceLink] = Field(default_factory=list)


class SupplierShortlist(BaseModel):
    product_name: str
    suppliers: List[SupplierScorecard] = Field(default_factory=list)
    recommended: Optional[str] = None
    test_order_plan: str = ""
    backup_plan: str = ""


class PriceOfferPlan(BaseModel):
    product_name: str
    list_price_usd: float
    compare_at_usd: Optional[float] = None
    bundle_options: List[str] = Field(default_factory=list)
    free_shipping_threshold_usd: Optional[float] = None
    economics: UnitEconomicsSnapshot
    ab_tests: List[str] = Field(default_factory=list)
    rationale: str = ""


class BrandPositioning(BaseModel):
    brand_name_options: List[str] = Field(default_factory=list)
    avatar: str
    promise: str
    proof_pillars: List[str] = Field(default_factory=list)
    voice_do: List[str] = Field(default_factory=list)
    voice_dont: List[str] = Field(default_factory=list)
    competitive_frame: str = ""
    tagline_options: List[str] = Field(default_factory=list)


class CreativeConcept(BaseModel):
    rank: int
    name: str
    hook: str
    angle: str
    script_15s: str = ""
    script_30s: str = ""
    on_screen_text: List[str] = Field(default_factory=list)
    cta: str = ""
    formats: List[str] = Field(default_factory=list)
    compliance_notes: str = ""
    hypothesis: str = ""


class CreativeBriefBatch(BaseModel):
    product_name: str
    avatar: str
    concepts: List[CreativeConcept] = Field(default_factory=list)
    production_notes: str = ""


class ListingPackage(BaseModel):
    product_name: str
    title: str
    bullets: List[str] = Field(default_factory=list)
    description_html_outline: str = ""
    faq: List[str] = Field(default_factory=list)
    image_order: List[str] = Field(default_factory=list)
    seo_title: str = ""
    seo_description: str = ""
    price_usd: float
    compliance_notes: str = ""


class ComplianceReview(BaseModel):
    asset_type: str = Field(..., description="creative|pdp|email|landing|offer")
    asset_name: str = ""
    verdict: ComplianceVerdict
    issues: List[str] = Field(default_factory=list)
    required_rewrites: List[str] = Field(default_factory=list)
    allowed_claims: List[str] = Field(default_factory=list)
    blocked_claims: List[str] = Field(default_factory=list)
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
    audiences: List[str] = Field(default_factory=list)
    creative_ids_or_names: List[str] = Field(default_factory=list)
    kill_criteria: str = ""
    autonomy_level: str = "L2"
    requires_human_approval: bool = True


class EmailFlowSpec(BaseModel):
    flow_name: str
    trigger: str
    emails: List[str] = Field(default_factory=list)
    goals: str = ""
    compliance_notes: str = ""
    cm_impact_notes: str = ""


class EmailLifecyclePlan(BaseModel):
    product_or_brand: str
    flows: List[EmailFlowSpec] = Field(default_factory=list)
    sms_rules: str = ""


class SupportMacroPack(BaseModel):
    topic: str
    macros: List[str] = Field(default_factory=list)
    escalation_rules: str = ""
    policy_summary: str = ""


class FulfillmentSLAPlan(BaseModel):
    product_name: str
    processing_hours_target: int = 48
    transit_guidance: str = ""
    tracking_sla: str = ""
    exception_playbook: List[str] = Field(default_factory=list)
    customer_eta_copy: str = ""


class InventoryPlan(BaseModel):
    product_name: str
    test_buy_units: int
    reorder_point_units: Optional[int] = None
    safety_stock_units: Optional[int] = None
    cash_at_risk_usd: Optional[float] = None
    rationale: str = ""
    do_not_bulk_until: str = ""


class ScorecardKPI(BaseModel):
    name: str
    value: str
    trend: str = ""
    note: str = ""


class WeeklyScorecard(BaseModel):
    period: str
    kpis: List[ScorecardKPI] = Field(default_factory=list)
    wins: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    actions: List[str] = Field(default_factory=list)
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
    next_actions: List[str] = Field(default_factory=list)
    requires_human_approval: List[str] = Field(default_factory=list)
    linear_issue_titles: List[str] = Field(default_factory=list)


class SEOContentPlan(BaseModel):
    product_or_category: str
    primary_keywords: List[str] = Field(default_factory=list)
    secondary_keywords: List[str] = Field(default_factory=list)
    page_types: List[str] = Field(default_factory=list)
    outline: str = ""
    internal_links: List[str] = Field(default_factory=list)


class StoreIAPlan(BaseModel):
    homepage_sections: List[str] = Field(default_factory=list)
    nav_items: List[str] = Field(default_factory=list)
    trust_stack: List[str] = Field(default_factory=list)
    policy_pages: List[str] = Field(default_factory=list)
    mobile_priorities: List[str] = Field(default_factory=list)
    checkout_friction_fixes: List[str] = Field(default_factory=list)


class InfluencerPlan(BaseModel):
    product_name: str
    creator_profile: str
    outreach_angles: List[str] = Field(default_factory=list)
    deliverables: List[str] = Field(default_factory=list)
    budget_per_asset_usd: Optional[float] = None
    usage_rights: str = ""
    compliance_notes: str = ""


# ─── Ops expansion schemas (12 new agents) ───────────────────

class QAInspectionReport(BaseModel):
    sku: str
    sample_id: str = ""
    verdict: str = Field(..., description="PASS|CONDITIONAL|FAIL")
    defects: List[str] = Field(default_factory=list)
    measurements: str = ""
    photos_needed: List[str] = Field(default_factory=list)
    supplier_feedback: str = ""
    ship_hold: bool = False
    next_actions: List[str] = Field(default_factory=list)
    confidence_0_to_1: float = Field(0.6, ge=0, le=1)


class ReturnsOpsPlan(BaseModel):
    order_id: str = ""
    reason_codes: List[str] = Field(default_factory=list)
    disposition: str = Field(..., description="refund|exchange|deny|partial")
    restockable: bool = False
    reverse_label: bool = True
    customer_message: str = ""
    cost_estimate_usd: float = 0.0
    prevention_notes: str = ""
    next_actions: List[str] = Field(default_factory=list)


class ChargebackCasePlan(BaseModel):
    case_id: str = ""
    reason: str = ""
    amount_usd: float = 0.0
    win_probability_0_to_1: float = Field(0.5, ge=0, le=1)
    evidence_checklist: List[str] = Field(default_factory=list)
    representment_summary: str = ""
    prevention_actions: List[str] = Field(default_factory=list)
    recommend: str = Field(..., description="FIGHT|ACCEPT|PARTIAL")


class EscalationPlaybook(BaseModel):
    ticket_id: str = ""
    severity: RiskLevel = RiskLevel.medium
    customer_tier: str = "standard"
    root_cause: str = ""
    resolution_options: List[str] = Field(default_factory=list)
    recommended_resolution: str = ""
    brand_risk: RiskLevel = RiskLevel.medium
    follow_ups: List[str] = Field(default_factory=list)


class LogisticsExceptionPlan(BaseModel):
    tracking: str = ""
    exception_type: str = ""
    carrier: str = ""
    eta_revision: str = ""
    recovery_actions: List[str] = Field(default_factory=list)
    customer_comms: str = ""
    cost_impact_usd: float = 0.0
    escalate_to_supplier: bool = False


class CreativeOpsQueue(BaseModel):
    campaign: str = ""
    variants_ready: List[str] = Field(default_factory=list)
    variants_in_production: List[str] = Field(default_factory=list)
    blockers: List[str] = Field(default_factory=list)
    compliance_status: str = ""
    next_48h_ship_list: List[str] = Field(default_factory=list)
    ugc_requests: List[str] = Field(default_factory=list)


class CatalogOpsPlan(BaseModel):
    sku_actions: List[str] = Field(default_factory=list)
    price_fixes: List[str] = Field(default_factory=list)
    publish_queue: List[str] = Field(default_factory=list)
    archive_candidates: List[str] = Field(default_factory=list)
    merchandising_notes: str = ""
    risks: List[str] = Field(default_factory=list)


class FraudRiskAssessment(BaseModel):
    order_id: str = ""
    risk_score_0_to_100: float = Field(..., ge=0, le=100)
    signals: List[str] = Field(default_factory=list)
    action: str = Field(..., description="ALLOW|REVIEW|HOLD|CANCEL")
    customer_impact: str = ""
    evidence: List[str] = Field(default_factory=list)
    notes: str = ""


class PartnershipPipeline(BaseModel):
    opportunities: List[str] = Field(default_factory=list)
    tier: str = "affiliate"
    economics_notes: str = ""
    outreach_sequence: List[str] = Field(default_factory=list)
    contract_flags: List[str] = Field(default_factory=list)
    next_actions: List[str] = Field(default_factory=list)


class TaxComplianceBrief(BaseModel):
    regions: List[str] = Field(default_factory=list)
    nexus_notes: str = ""
    collection_status: str = ""
    risks: List[str] = Field(default_factory=list)
    required_actions: List[str] = Field(default_factory=list)
    documentation: List[str] = Field(default_factory=list)
    verdict: str = Field(..., description="OK|ATTENTION|BLOCK_SHIP")


class CommunityOpsPlan(BaseModel):
    channels: List[str] = Field(default_factory=list)
    sentiment: str = ""
    ugc_opportunities: List[str] = Field(default_factory=list)
    crisis_flags: List[str] = Field(default_factory=list)
    response_queue: List[str] = Field(default_factory=list)
    content_to_amplify: List[str] = Field(default_factory=list)


class ExperimentBacklog(BaseModel):
    hypothesis: str
    primary_metric: str
    secondary_metrics: List[str] = Field(default_factory=list)
    variants: List[str] = Field(default_factory=list)
    sample_size_notes: str = ""
    duration_days: int = 14
    guardrails: List[str] = Field(default_factory=list)
    decision_rule: str = ""
    ranked_backlog: List[str] = Field(default_factory=list)
