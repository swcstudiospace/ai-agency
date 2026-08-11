"""Role-shaped toolbelts for agency agents."""

from __future__ import annotations

from typing import Any, Dict, List, Sequence

from tools.analytics_store import get_analytics_tools
from tools.anda_knowledge import get_anda_brain_tools, get_anda_filesystem_knowledge
from tools.catalog_ops_tools import get_catalog_ops_tools
from tools.chargeback_ops_tools import get_chargeback_ops_tools
from tools.community_ops_tools import get_community_ops_tools
from tools.creative_ops_tools import get_creative_ops_tools
from tools.cx_ops_tools import get_cx_ops_tools
from tools.economics_tools import get_economics_tools
from tools.experiment_ops_tools import get_experiment_ops_tools
from tools.fal_tools import get_fal_tools
from tools.fraud_ops_tools import get_fraud_ops_tools
from tools.hermes_bridge_tools import get_hermes_bridge_tools
from tools.linear_tools import get_linear_tools
from tools.logistics_ops_tools import get_logistics_ops_tools
from tools.logistics_tools import get_logistics_tools
from tools.meta_ads_tools import get_meta_tools
from tools.parallel_tools import (
    parallel_create_monitor,
    parallel_entity_search,
    parallel_extract,
    parallel_search,
    parallel_task,
    parallel_task_result,
)
from tools.partnership_ops_tools import get_partnership_ops_tools
from tools.promptwise_tools import get_promptwise_tools
from tools.qa_ops_tools import get_qa_ops_tools
from tools.returns_ops_tools import get_returns_ops_tools
from tools.shopify_tools import get_shopify_tools
from tools.spend_vault import get_spend_tools
from tools.supplier_tools import get_supplier_tools
from tools.tax_ops_tools import get_tax_ops_tools
from tools.tiktok_ads_tools import get_tiktok_tools


def _parallel_core() -> List[Any]:
    return [parallel_search, parallel_extract, parallel_task, parallel_task_result]


def _parallel_research() -> List[Any]:
    return _parallel_core() + [parallel_entity_search, parallel_create_monitor]


def _parallel_light() -> List[Any]:
    return [parallel_search, parallel_extract]


TOOLBELTS: Dict[str, List[Any]] = {
    "parallel_research": _parallel_research(),
    "parallel_core": _parallel_core(),
    "parallel_light": _parallel_light(),
    "economics": get_economics_tools(),
    "linear": get_linear_tools(),
    "supplier": get_supplier_tools(),
    "shopify": get_shopify_tools(),
    "fal": get_fal_tools(),
    "promptwise": get_promptwise_tools(),
    "meta_ads": get_meta_tools(),
    "tiktok_ads": get_tiktok_tools(),
    "logistics": get_logistics_tools(),
    "spend": get_spend_tools(),
    "ads_full": get_meta_tools() + get_tiktok_tools() + get_spend_tools(),
    "creative_prod": get_fal_tools() + get_promptwise_tools() + get_shopify_tools(),
    "hermes_bridge": get_hermes_bridge_tools(),
    "anda_brain": get_anda_brain_tools(),
    "analytics": get_analytics_tools(),
    # ── ops expansion belts ──
    "qa_ops": get_qa_ops_tools(),
    "returns_ops": get_returns_ops_tools(),
    "chargeback_ops": get_chargeback_ops_tools(),
    "cx_ops": get_cx_ops_tools(),
    "logistics_ops": get_logistics_ops_tools(),
    "creative_ops": get_creative_ops_tools() + get_promptwise_tools() + get_fal_tools(),
    "catalog_ops": get_catalog_ops_tools(),
    "fraud_ops": get_fraud_ops_tools(),
    "partnership_ops": get_partnership_ops_tools(),
    "tax_ops": get_tax_ops_tools(),
    "community_ops": get_community_ops_tools(),
    "experiment_ops": get_experiment_ops_tools(),
}


def resolve_toolbelt(names: Sequence[str] | None) -> List[Any]:
    """Compose tools from named belts; de-dupe by function identity/name."""
    if not names:
        return []
    seen: set[str] = set()
    out: List[Any] = []
    for name in names:
        belt = TOOLBELTS.get(name)
        if not belt:
            raise KeyError(f"Unknown toolbelt: {name}. Known: {sorted(TOOLBELTS)}")
        for fn in belt:
            key = getattr(fn, "__name__", None) or getattr(fn, "name", None) or id(fn)
            key_s = str(key)
            if key_s in seen:
                continue
            seen.add(key_s)
            out.append(fn)
    return out
