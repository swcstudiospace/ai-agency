"""Creative production ops — variant matrices and queue boards."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def creative_ops_variant_matrix(
    product: str,
    hooks: Optional[List[str]] = None,
    angles: Optional[List[str]] = None,
    formats: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Build hook × angle × format variant matrix for ad testing."""
    hooks = hooks or [
        "pain_agitation",
        "demo_3s",
        "social_proof",
        "offer_stack",
        "before_after_lifestyle",
        "ugc_confession",
    ]
    angles = angles or ["desk_worker", "gift", "productivity", "relief_without_claims"]
    formats = formats or ["9x16_ugc", "1x1_static", "15s_edit"]
    variants = []
    for h in hooks[:6]:
        for a in angles[:2]:
            variants.append({"hook": h, "angle": a, "format": formats[0], "product": product})
    return {
        "ok": True,
        "product": product,
        "variant_count": len(variants),
        "variants": variants[:12],
        "compliance_note": "Avoid medical cure claims; lifestyle only unless Compliance PASS.",
    }


def creative_ops_queue_board(
    ready: Optional[List[str]] = None,
    in_production: Optional[List[str]] = None,
    blockers: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Summarize 48h creative ship list."""
    return {
        "ok": True,
        "variants_ready": list(ready or []),
        "variants_in_production": list(in_production or []),
        "blockers": list(blockers or []),
        "next_48h_ship_list": list(ready or [])[:8],
        "hitl": "Live ad publish/spend requires Growth + Finance HITL",
    }


def get_creative_ops_tools() -> list:
    return [creative_ops_variant_matrix, creative_ops_queue_board]
