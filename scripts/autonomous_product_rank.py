#!/usr/bin/env python3
"""Autonomous product find + rank test.

Pipeline:
  1. Parallel Search (advanced) — market scan
  2. Parallel Task **ultra** — deep structured product research
  3. Local unit-economics scoring
  4. Research Team (Agno) — synthesize ranking with agency skills
  5. Write report under tmp/

Usage:
  cd ~/src/repos/ai-agency && source .venv/bin/activate
  python -m scripts.autonomous_product_rank
  python -m scripts.autonomous_product_rank --niche "home fitness recovery"
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from tools.economics_tools import contribution_margin, price_ladder
from tools.parallel_tools import parallel_search, parallel_task
from tools.supplier_tools import score_supplier


PRODUCT_SCHEMA: Dict[str, Any] = {
    "type": "json",
    "json_schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "market_summary": {
                "type": "string",
                "description": "2-4 sentence market snapshot for dropshipping viability",
            },
            "candidates": {
                "type": "array",
                "description": "8-12 concrete product opportunities ranked best-first",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "name": {"type": "string"},
                        "category": {"type": "string"},
                        "avatar": {"type": "string"},
                        "estimated_cogs_usd": {"type": "number"},
                        "shipping_usd": {"type": "number"},
                        "suggested_price_usd": {"type": "number"},
                        "target_cpa_usd": {"type": "number"},
                        "competition_level": {
                            "type": "string",
                            "description": "low|medium|high",
                        },
                        "differentiation_angle": {"type": "string"},
                        "shipping_risk": {
                            "type": "string",
                            "description": "low|medium|high",
                        },
                        "return_risk": {
                            "type": "string",
                            "description": "low|medium|high",
                        },
                        "seasonality": {"type": "string"},
                        "why_now": {"type": "string"},
                        "risks": {"type": "string"},
                        "supplier_hints": {"type": "string"},
                        "evidence_urls": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "confidence_0_to_1": {"type": "number"},
                    },
                    "required": [
                        "name",
                        "category",
                        "estimated_cogs_usd",
                        "suggested_price_usd",
                        "competition_level",
                        "why_now",
                        "evidence_urls",
                    ],
                },
            },
        },
        "required": ["market_summary", "candidates"],
    },
}


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _risk_score(level: str) -> float:
    return {"low": 1.0, "medium": 0.55, "high": 0.15}.get((level or "medium").lower(), 0.55)


def _competition_score(level: str) -> float:
    return {"low": 1.0, "medium": 0.55, "high": 0.2}.get((level or "medium").lower(), 0.55)


def score_candidate(c: Dict[str, Any], default_cpa: float = 18.0) -> Dict[str, Any]:
    cogs = float(c.get("estimated_cogs_usd") or 0)
    ship = float(c.get("shipping_usd") or max(3.0, cogs * 0.35))
    price = float(c.get("suggested_price_usd") or 0)
    cpa = float(c.get("target_cpa_usd") or default_cpa)
    if price <= 0 and cogs > 0:
        ladder = price_ladder(cogs, ship, target_cm_pct=0.30, ad_cpa=cpa)
        price = float(ladder.get("suggested_price") or (cogs + ship) * 3)

    econ = contribution_margin(
        sell_price=price,
        cogs=cogs,
        shipping=ship,
        ad_spend_per_order=cpa,
        returns_pct=0.08 if (c.get("return_risk") or "").lower() == "high" else 0.05,
    )

    cm_pct = float(econ.get("contribution_margin_pct") or 0)
    # Composite aligned with product-scoring skill weights
    cm_n = max(0.0, min(1.0, cm_pct / 0.35))
    comp_n = _competition_score(str(c.get("competition_level") or "medium"))
    ship_n = _risk_score(str(c.get("shipping_risk") or "medium"))
    ret_n = _risk_score(str(c.get("return_risk") or "medium"))
    conf = float(c.get("confidence_0_to_1") or 0.5)
    diff = 0.7 if c.get("differentiation_angle") else 0.4
    composite = (
        0.30 * cm_n
        + 0.20 * comp_n
        + 0.15 * ship_n
        + 0.15 * ret_n
        + 0.15 * diff
        + 0.05 * conf
    ) * 100

    if cm_pct < 0 or not econ.get("healthy") and cm_pct < 0.15:
        decision = "NO-GO"
    elif composite >= 62 and cm_pct >= 0.22:
        decision = "GO"
    elif composite >= 48 and cm_pct >= 0.12:
        decision = "TEST"
    else:
        decision = "NO-GO"

    supplier = score_supplier(
        name=str(c.get("supplier_hints") or c.get("name") or "unknown")[:80],
        lead_time_days=18 if (c.get("shipping_risk") or "").lower() == "high" else 12,
        moq=1,
        unit_cost=cogs,
        shipping_cost=ship,
        rating=4.2,
        notes=str(c.get("supplier_hints") or ""),
    )

    return {
        **c,
        "estimated_cogs_usd": cogs,
        "shipping_usd": ship,
        "suggested_price_usd": round(price, 2),
        "target_cpa_usd": cpa,
        "economics": econ,
        "supplier_score": supplier,
        "composite_score": round(composite, 1),
        "decision": decision,
    }


def parse_task_output(output: Any) -> Dict[str, Any]:
    if output is None:
        return {}
    if isinstance(output, dict):
        # sometimes {type, value} or content wrapper
        if "candidates" in output:
            return output
        for key in ("value", "content", "json", "data"):
            if key in output:
                return parse_task_output(output[key])
        return output
    if isinstance(output, str):
        text = output.strip()
        # strip fences
        fence = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.S)
        if fence:
            text = fence.group(1)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # try find first object
            m = re.search(r"\{.*\}", text, re.S)
            if m:
                try:
                    return json.loads(m.group(0))
                except json.JSONDecodeError:
                    return {"market_summary": text[:2000], "candidates": [], "parse_error": True}
            return {"market_summary": text[:2000], "candidates": [], "parse_error": True}
    return {"market_summary": str(output)[:2000], "candidates": []}


def run_research_team(niche: str, ranked: List[Dict[str, Any]], market_summary: str) -> str:
    """Ask Research Team to finalize ranking using Parallel-backed agents."""
    try:
        from teams.research_team import research_team
    except Exception as e:
        return f"[Research Team unavailable: {e}]"

    top = ranked[:8]
    brief = {
        "niche": niche,
        "market_summary": market_summary,
        "pre_scored_candidates": [
            {
                "name": c.get("name"),
                "composite_score": c.get("composite_score"),
                "decision": c.get("decision"),
                "price": c.get("suggested_price_usd"),
                "cogs": c.get("estimated_cogs_usd"),
                "cm_pct": (c.get("economics") or {}).get("contribution_margin_pct"),
                "competition": c.get("competition_level"),
                "angle": c.get("differentiation_angle"),
                "evidence_urls": (c.get("evidence_urls") or [])[:5],
                "why_now": c.get("why_now"),
                "risks": c.get("risks"),
            }
            for c in top
        ],
    }
    prompt = f"""You are running the Research Team product-ranking gate for our dropshipping agency.

Parallel Ultra deep research already produced candidate products. Your job:
1. Critically review the pre-scored list (do NOT invent fake SKUs).
2. Optionally use Parallel Search lightly to validate the TOP 3 only if needed.
3. Produce a FINAL ranked top 5 with: decision GO/TEST/NO-GO, one-line why, kill criteria, and next experiment.
4. Call out any compliance / shipping / margin red flags.
5. Be skeptical — prefer TEST over GO when data is thin.

PRE-SCORED DATA (JSON):
{json.dumps(brief, indent=2)}

Return markdown with:
## Final ranking
## Rejects / watchlist
## Recommended first test
"""
    try:
        resp = research_team.run(input=prompt)
        # RunOutput variants
        content = getattr(resp, "content", None) or getattr(resp, "messages", None)
        if content is None:
            return str(resp)
        return str(content)
    except Exception as e:
        return f"[Research Team run failed: {e}]\n{traceback.format_exc()}"


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Autonomous product find/rank with Parallel ultra")
    p.add_argument(
        "--niche",
        default="home fitness recovery and mobility tools for desk workers",
        help="Market niche to research",
    )
    p.add_argument("--processor", default="ultra", choices=["lite", "base", "core", "pro", "ultra"])
    p.add_argument("--timeout", type=float, default=3600.0, help="Ultra task wait timeout seconds")
    p.add_argument("--skip-team", action="store_true", help="Skip Agno Research Team synthesis")
    p.add_argument("--default-cpa", type=float, default=18.0)
    args = p.parse_args(argv)

    out_dir = ROOT / "tmp" / "runs"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_path = out_dir / f"product_rank_{stamp}.json"
    md_path = out_dir / f"product_rank_{stamp}.md"

    print(f"=== Autonomous product rank ===")
    print(f"niche: {args.niche}")
    print(f"processor: {args.processor}")
    print(f"started: {_utc()}")

    # 1) Parallel Search scan
    print("\n[1/4] Parallel Search (advanced)…")
    search = parallel_search(
        objective=(
            f"Find trending and profitable dropshipping product opportunities in: {args.niche}. "
            "Focus on 2025-2026 demand signals, competitor products, price points, and reviews."
        ),
        search_queries=[
            f"{args.niche} best selling products",
            f"{args.niche} dropshipping products 2026",
            f"{args.niche} market trends amazon tiktok",
        ],
        mode="advanced",
    )
    search_hits = (search.get("results") or [])[:12]
    print(f"  search_id={search.get('search_id')} hits={len(search_hits)}")
    if search.get("error"):
        print(f"  search error: {search['error']}")

    evidence_blob = "\n".join(
        f"- {h.get('title')}: {h.get('url')}\n  excerpts: {'; '.join((h.get('excerpts') or [])[:2])[:400]}"
        for h in search_hits
    )

    # 2) Parallel Task ultra deep research
    print(f"\n[2/4] Parallel Task ({args.processor}) deep research — this can take several minutes…")
    task_input = f"""You are a senior dropshipping product researcher.

NICHE: {args.niche}

GOAL: Identify 8-12 concrete physical product opportunities suitable for Shopify dropshipping
(or light private-label), with realistic COGS/shipping/price bands for US/EU consumers.

Use current web evidence. Prefer products with:
- positive contribution margin potential after paid social CPA ~${args.default_cpa:.0f}
- manageable size/weight for cross-border shipping
- clear differentiation angle (bundle, problem-solution, demo-friendly UGC)
- not saturated medical-claim or restricted categories

Avoid: supplements with disease claims, weapons, adult, counterfeit IP, complex electronics with high RMA.

SEED SEARCH HITS (may be incomplete — verify and expand):
{evidence_blob}

Return structured JSON matching the schema. Rank candidates best-first. Include evidence_urls for each.
"""
    task = parallel_task(
        objective=task_input,
        processor=args.processor,
        output_schema=PRODUCT_SCHEMA,
        wait=True,
        timeout_s=args.timeout,
    )
    if task.get("error"):
        print(f"  TASK ERROR: {task['error']}")
        report_path.write_text(json.dumps({"error": task, "search": search}, indent=2, default=str))
        print(f"wrote {report_path}")
        return 2

    print(f"  task_id={task.get('task_id')} status={task.get('status')}")
    parsed = parse_task_output(task.get("output"))
    candidates = parsed.get("candidates") or []
    market_summary = parsed.get("market_summary") or ""
    print(f"  parsed candidates={len(candidates)} parse_error={parsed.get('parse_error')}")

    # 3) Local scoring
    print("\n[3/4] Unit-economics composite scoring…")
    ranked = [score_candidate(c, default_cpa=args.default_cpa) for c in candidates]
    ranked.sort(key=lambda x: (x.get("decision") != "NO-GO", x.get("composite_score", 0)), reverse=True)
    for i, c in enumerate(ranked[:10], 1):
        econ = c.get("economics") or {}
        print(
            f"  {i:2d}. [{c.get('decision'):5s}] {c.get('composite_score'):5.1f}  "
            f"{c.get('name')}  price=${c.get('suggested_price_usd')}  "
            f"CM%={float(econ.get('contribution_margin_pct') or 0)*100:.1f}%"
        )

    # 4) Research Team synthesis
    team_md = ""
    if not args.skip_team and ranked:
        print("\n[4/4] Research Team synthesis (Grok + skills)…")
        team_md = run_research_team(args.niche, ranked, market_summary)
        print("  team synthesis complete")
    else:
        print("\n[4/4] Skipping Research Team")

    payload = {
        "meta": {
            "niche": args.niche,
            "processor": args.processor,
            "started": stamp,
            "finished": _utc(),
            "default_cpa": args.default_cpa,
            "task_id": task.get("task_id"),
            "search_id": search.get("search_id"),
        },
        "market_summary": market_summary,
        "search_top": [
            {"title": h.get("title"), "url": h.get("url")} for h in search_hits[:8]
        ],
        "ranked_candidates": ranked,
        "research_team_synthesis": team_md,
        "task_basis_present": task.get("basis") is not None,
    }
    report_path.write_text(json.dumps(payload, indent=2, default=str) + "\n")

    # Markdown report
    lines = [
        f"# Product rank — {args.niche}",
        "",
        f"- Finished: `{payload['meta']['finished']}`",
        f"- Parallel Task: `{args.processor}` `{task.get('task_id')}`",
        f"- Parallel Search: `{search.get('search_id')}`",
        "",
        "## Market summary",
        market_summary or "_n/a_",
        "",
        "## Ranked candidates",
        "",
        "| # | Decision | Score | Product | Price | CM% | Competition |",
        "|---|----------|-------|---------|-------|-----|-------------|",
    ]
    for i, c in enumerate(ranked, 1):
        econ = c.get("economics") or {}
        cm = float(econ.get("contribution_margin_pct") or 0) * 100
        lines.append(
            f"| {i} | {c.get('decision')} | {c.get('composite_score')} | "
            f"{c.get('name')} | ${c.get('suggested_price_usd')} | {cm:.1f}% | "
            f"{c.get('competition_level')} |"
        )
    lines.extend(["", "## Top 5 detail", ""])
    for i, c in enumerate(ranked[:5], 1):
        lines.append(f"### {i}. {c.get('name')} — {c.get('decision')} ({c.get('composite_score')})")
        lines.append(f"- Category: {c.get('category')}")
        lines.append(f"- Angle: {c.get('differentiation_angle')}")
        lines.append(f"- Why now: {c.get('why_now')}")
        lines.append(f"- Risks: {c.get('risks')}")
        lines.append(
            f"- Economics: price=${c.get('suggested_price_usd')} cogs=${c.get('estimated_cogs_usd')} "
            f"ship=${c.get('shipping_usd')} cpa=${c.get('target_cpa_usd')} "
            f"CM={(c.get('economics') or {}).get('contribution_margin')}"
        )
        urls = c.get("evidence_urls") or []
        if urls:
            lines.append("- Evidence:")
            for u in urls[:5]:
                lines.append(f"  - {u}")
        lines.append("")
    if team_md:
        lines.extend(["## Research Team synthesis", "", team_md, ""])
    md_path.write_text("\n".join(lines) + "\n")

    print(f"\n=== done ===")
    print(f"JSON: {report_path}")
    print(f"MD:   {md_path}")
    go = [c for c in ranked if c.get("decision") == "GO"]
    test = [c for c in ranked if c.get("decision") == "TEST"]
    print(f"GO={len(go)} TEST={len(test)} NO-GO={len(ranked)-len(go)-len(test)}")

    # Linear dual-write top TEST/GO candidates → AI Dropshipping Agency project
    linear_issues = []
    try:
        from tools.envutil import load_dotenv_files
        from tools.linear_tools import create_linear_issue

        load_dotenv_files()
        top = [c for c in ranked if c.get("decision") in {"GO", "TEST"}][:5]
        if top:
            summary_lines = [
                f"**Niche:** {args.niche}",
                f"**Processor:** {args.processor}",
                f"**Report:** `{report_path}`",
                "",
                "## Top candidates",
            ]
            for i, c in enumerate(top, 1):
                econ = c.get("economics") or {}
                cm = float(econ.get("contribution_margin_pct") or 0) * 100
                summary_lines.append(
                    f"{i}. **{c.get('name')}** — {c.get('decision')} score={c.get('composite_score')} "
                    f"price=${c.get('suggested_price_usd')} CM%={cm:.1f}%"
                )
            parent = create_linear_issue(
                title=f"[Product Rank] {args.niche[:80]}",
                description="\n".join(summary_lines) + "\n\n" + (md_path.read_text()[:6000] if md_path.is_file() else ""),
                priority=2,
            )
            linear_issues.append(parent)
            print(f"Linear parent: {parent.get('identifier')} {parent.get('url')}")
            for c in top[:3]:
                econ = c.get("economics") or {}
                child = create_linear_issue(
                    title=f"[{c.get('decision')}] {c.get('name')}"[:250],
                    description=(
                        f"From product rank `{stamp}`\n\n"
                        f"- Score: {c.get('composite_score')}\n"
                        f"- Price: ${c.get('suggested_price_usd')} COGS ${c.get('estimated_cogs_usd')} ship ${c.get('shipping_usd')}\n"
                        f"- CM: {econ.get('contribution_margin')} ({float(econ.get('contribution_margin_pct') or 0)*100:.1f}%)\n"
                        f"- Angle: {c.get('differentiation_angle')}\n"
                        f"- Why now: {c.get('why_now')}\n"
                        f"- Risks: {c.get('risks')}\n"
                    ),
                    priority=3 if c.get("decision") == "TEST" else 2,
                )
                linear_issues.append(child)
                print(f"  Linear: {child.get('identifier')} {child.get('name') or c.get('name')}")
    except Exception as e:
        print(f"Linear dual-write skipped: {e}")
        linear_issues.append({"error": str(e)})

    # update JSON with linear refs
    try:
        payload["linear_issues"] = linear_issues
        payload["meta"]["grok_model"] = os.getenv("AGENCY_GROK_MODEL") or "grok-4.5"
        report_path.write_text(json.dumps(payload, indent=2, default=str) + "\n")
    except Exception:
        pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
