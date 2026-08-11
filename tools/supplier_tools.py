"""Supplier / marketplace research helpers + Parallel-backed product locate."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from tools.envutil import env


def score_supplier(
    name: str,
    lead_time_days: int,
    moq: int,
    unit_cost: float,
    shipping_cost: float,
    rating: float = 0.0,
    notes: str = "",
) -> Dict[str, Any]:
    """Heuristic supplier score 0-100 for agency ranking."""
    score = 50.0
    if lead_time_days <= 7:
        score += 15
    elif lead_time_days <= 14:
        score += 8
    elif lead_time_days > 25:
        score -= 15
    if moq <= 1:
        score += 10
    elif moq <= 10:
        score += 5
    elif moq > 50:
        score -= 10
    landed = unit_cost + shipping_cost
    if landed < 8:
        score += 10
    elif landed > 40:
        score -= 10
    if rating >= 4.5:
        score += 10
    elif rating and rating < 3.5:
        score -= 15
    score = max(0.0, min(100.0, score))
    return {
        "name": name,
        "score": round(score, 1),
        "landed_cost": round(landed, 2),
        "lead_time_days": lead_time_days,
        "moq": moq,
        "notes": notes,
        "recommend": score >= 65,
    }


def compare_suppliers(candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    ranked = sorted(candidates, key=lambda c: c.get("score", 0), reverse=True)
    return {"ranked": ranked, "top": ranked[0] if ranked else None}


def locate_suppliers_for_product(
    product_name: str,
    target_unit_cost_usd: float = 15.0,
    dest_market: str = "US",
    processor: str = "pro",
    max_suppliers: int = 5,
) -> Dict[str, Any]:
    """Find real supplier leads for a product via Parallel Search + Task.

    This is the **locate** step after product rank: where to buy, MOQ, sample
    cost, ship lanes, and red flags — without placing POs (HITL).
    """
    from tools.parallel_tools import parallel_search, parallel_task

    product_name = (product_name or "").strip()
    if not product_name:
        return {"ok": False, "error": "product_name required"}

    search = parallel_search(
        objective=(
            f"Find wholesale/dropship suppliers for: {product_name}. "
            f"Prefer Alibaba, 1688 agents, CJ Dropshipping, Spocket, Zendrop, "
            f"or verified manufacturers shipping to {dest_market}."
        ),
        search_queries=[
            f"{product_name} supplier alibaba",
            f"{product_name} dropshipping supplier MOQ",
            f"{product_name} wholesale manufacturer {dest_market}",
            f"{product_name} CJ dropshipping OR zendrop OR spocket",
        ],
        mode="advanced",
    )
    hits = (search.get("results") or [])[:12]
    evidence = "\n".join(
        f"- {h.get('title')}: {h.get('url')}\n  {(h.get('excerpts') or [''])[0][:280]}"
        for h in hits
    )

    schema = {
        "type": "json",
        "json_schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "summary": {"type": "string"},
                "suppliers": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "name": {"type": "string"},
                            "platform": {"type": "string"},
                            "url": {"type": "string"},
                            "unit_cost_usd_est": {"type": "number"},
                            "shipping_usd_est": {"type": "number"},
                            "moq": {"type": "number"},
                            "lead_time_days": {"type": "number"},
                            "sample_available": {"type": "boolean"},
                            "ships_to": {"type": "string"},
                            "rating_est": {"type": "number"},
                            "pros": {"type": "string"},
                            "cons": {"type": "string"},
                            "red_flags": {"type": "string"},
                        },
                        "required": ["name", "platform", "unit_cost_usd_est", "shipping_usd_est"],
                    },
                },
                "recommended_next_step": {"type": "string"},
            },
            "required": ["summary", "suppliers", "recommended_next_step"],
        },
    }

    task = parallel_task(
        objective=(
            f"You are a sourcing agent for a US/EU dropshipping brand.\n"
            f"PRODUCT: {product_name}\n"
            f"TARGET UNIT COGS: ~${target_unit_cost_usd}\n"
            f"DEST MARKET: {dest_market}\n\n"
            f"Using the evidence below, shortlist up to {max_suppliers} suppliers "
            f"with realistic cost/MOQ/lead-time estimates. Prefer platforms that "
            f"support samples and dropship. Flag counterfeit/IP risk.\n\n"
            f"EVIDENCE:\n{evidence}\n"
        ),
        processor=processor,
        output_schema=schema,
        wait=True,
        timeout_s=float(env("LOCATE_TIMEOUT", "900") or "900"),
    )

    suppliers_raw: List[Dict[str, Any]] = []
    summary = ""
    next_step = ""
    parse_error = None
    try:
        out = task.get("output")
        parsed = out
        if isinstance(out, str):
            parsed = json.loads(out)
        elif isinstance(out, dict) and "content" in out and isinstance(out["content"], str):
            parsed = json.loads(out["content"])
        if isinstance(parsed, dict):
            suppliers_raw = parsed.get("suppliers") or []
            summary = parsed.get("summary") or ""
            next_step = parsed.get("recommended_next_step") or ""
    except Exception as e:
        parse_error = str(e)

    scored = []
    for s in suppliers_raw[: max(1, max_suppliers)]:
        unit = float(s.get("unit_cost_usd_est") or target_unit_cost_usd)
        ship = float(s.get("shipping_usd_est") or 5.0)
        moq = int(s.get("moq") or 1)
        lead = int(s.get("lead_time_days") or 14)
        rating = float(s.get("rating_est") or 0)
        sc = score_supplier(
            name=str(s.get("name") or "unknown"),
            lead_time_days=lead,
            moq=moq,
            unit_cost=unit,
            shipping_cost=ship,
            rating=rating,
            notes=str(s.get("pros") or ""),
        )
        scored.append(
            {
                **s,
                "scorecard": sc,
                "landed_cost_usd": sc["landed_cost"],
                "recommend": sc["recommend"],
            }
        )
    scored.sort(key=lambda x: x.get("scorecard", {}).get("score", 0), reverse=True)

    return {
        "ok": not bool(task.get("error")),
        "product_name": product_name,
        "dest_market": dest_market,
        "target_unit_cost_usd": target_unit_cost_usd,
        "search_id": search.get("search_id"),
        "task_id": task.get("task_id"),
        "task_status": task.get("status"),
        "summary": summary,
        "recommended_next_step": next_step,
        "suppliers": scored,
        "top_supplier": scored[0] if scored else None,
        "evidence_hits": [{"title": h.get("title"), "url": h.get("url")} for h in hits[:8]],
        "error": task.get("error"),
        "parse_error": parse_error,
        "hitl": True,
        "note": "Locate only — do not place PO/sample payment without human approval",
    }


def locate_product_sources_batch(
    products: List[str],
    dest_market: str = "US",
    processor: str = "core",
) -> Dict[str, Any]:
    """Locate suppliers for multiple ranked products (sequential)."""
    results = []
    for name in products[:5]:
        results.append(
            locate_suppliers_for_product(
                product_name=name,
                dest_market=dest_market,
                processor=processor,
                max_suppliers=4,
            )
        )
    return {
        "ok": any(r.get("ok") for r in results),
        "count": len(results),
        "results": results,
    }


def get_supplier_tools() -> list:
    return [
        score_supplier,
        compare_suppliers,
        locate_suppliers_for_product,
        locate_product_sources_batch,
    ]
