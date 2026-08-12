#!/usr/bin/env python3
"""Autonomous dropshipping lifecycle (everything except paying).

Stages:
  1. Research (Parallel ultra/pro) + unit economics
  2. Linear dual-write for top candidates
  3. Supplier shortlist heuristics + logistics profile
  4. Creative brief + optional Fal UGC stub/render
  5. Shopify draft package (draft only)
  6. Meta/TikTok campaign DRAFTS
  7. HITL spend approval request (human must confirm to go live)

Usage:
  PYTHONPATH=. python -m scripts.autonomous_lifecycle \\
    --niche "desk mobility kits" --processor ultra --top 3
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tools.economics_tools import contribution_margin
from tools.envutil import load_dotenv_files
from tools.fal_tools import build_ugc_brief_and_render, list_fal_avatars
from tools.linear_tools import agency_track, linear_status, update_linear_issue
from tools.logistics_tools import estimate_shipping_profile
from tools.meta_ads_tools import meta_draft_campaign, meta_status
from tools.parallel_tools import parallel_search, parallel_task
from tools.shopify_tools import draft_product, shopify_status
from tools.spend_vault import list_funding_sources, request_spend_approval
from tools.supplier_tools import score_supplier
from tools.tiktok_ads_tools import tiktok_draft_campaign, tiktok_status

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "tmp" / "runs"


def _utc() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def _cm(price: float, cogs: float, ship: float, cpa: float = 18.0) -> dict[str, Any]:
    try:
        return contribution_margin(price, cogs, ship, cpa)
    except Exception:
        cm = price - cogs - ship - cpa
        return {
            "sell_price": price,
            "cogs": cogs,
            "shipping": ship,
            "cpa": cpa,
            "contribution_margin_usd": round(cm, 2),
            "contribution_margin_pct": round(cm / price, 4) if price else 0,
        }


def stage_research(niche: str, processor: str, timeout: int) -> dict[str, Any]:
    search = parallel_search(
        objective=f"Winning dropshipping product opportunities in: {niche}",
        search_queries=[
            f"{niche} best sellers",
            f"{niche} market demand 2025 2026",
            f"{niche} product price competitors",
        ],
        max_results=10,
        mode="advanced",
    )
    schema = {
        "type": "json",
        "json_schema": {
            "type": "object",
            "properties": {
                "market_summary": {"type": "string"},
                "candidates": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "category": {"type": "string"},
                            "estimated_cogs_usd": {"type": "number"},
                            "suggested_price_usd": {"type": "number"},
                            "shipping_usd": {"type": "number"},
                            "competition": {"type": "string"},
                            "why_now": {"type": "string"},
                            "risks": {"type": "string"},
                            "differentiation": {"type": "string"},
                            "avatar": {"type": "string"},
                            "hook": {"type": "string"},
                            "evidence_urls": {"type": "array", "items": {"type": "string"}},
                            "confidence": {"type": "number"},
                        },
                        "required": ["name", "suggested_price_usd", "estimated_cogs_usd"],
                    },
                },
            },
            "required": ["candidates"],
        },
    }
    task = parallel_task(
        objective=(
            f"Deep product research for dropshipping niche: {niche}. "
            "Return 8-12 concrete product candidates with realistic US retail prices, "
            "estimated COGS from CN/EU, shipping, competition, differentiation, "
            "avatar, one ad hook, risks, evidence URLs. Prefer demo-friendly physical goods."
        ),
        processor=processor,
        output_schema=schema,
        wait=True,
        timeout_s=timeout,
    )
    return {"search": search, "task": task}


def _extract_candidates(task: dict[str, Any]) -> list[dict[str, Any]]:
    out = task.get("output") or task.get("result") or task
    if isinstance(out, str):
        try:
            out = json.loads(out)
        except Exception:
            return []
    if isinstance(out, dict):
        # nested content
        for k in ("candidates", "output", "result", "data"):
            if k in out and isinstance(out[k], dict) and "candidates" in out[k]:
                out = out[k]
                break
        cands = out.get("candidates")
        if isinstance(cands, list):
            return cands
        # parallel sometimes wraps
        basemodel = out.get("basis") or out
        if isinstance(basemodel, dict) and isinstance(basemodel.get("candidates"), list):
            return basemodel["candidates"]
    return []


def stage_score(candidates: list[dict[str, Any]], cpa: float) -> list[dict[str, Any]]:
    ranked = []
    for c in candidates:
        price = float(c.get("suggested_price_usd") or c.get("price") or 0)
        cogs = float(c.get("estimated_cogs_usd") or c.get("cogs") or 0)
        ship = float(c.get("shipping_usd") or 5.5)
        if price <= 0:
            continue
        e = _cm(price, cogs, ship, cpa)
        cm_pct = float(e.get("contribution_margin_pct") or 0)
        conf = float(c.get("confidence") or 0.5)
        # simple composite
        score = min(100.0, max(0.0, cm_pct * 100 * 0.55 + conf * 40 + 5))
        decision = "NO-GO"
        if cm_pct >= 0.25 and score >= 65:
            decision = "GO"
        elif cm_pct >= 0.15:
            decision = "TEST"
        ranked.append({**c, "economics": e, "composite_score": round(score, 1), "decision": decision})
    ranked.sort(key=lambda x: x["composite_score"], reverse=True)
    return ranked


def run(niche: str, processor: str, top_n: int, cpa: float, timeout: int, render_ugc: bool) -> dict[str, Any]:
    load_dotenv_files()
    started = time.time()
    report: dict[str, Any] = {
        "meta": {
            "niche": niche,
            "processor": processor,
            "started": _utc(),
            "linear": linear_status(),
            "shopify": shopify_status(),
            "meta_ads": meta_status(),
            "tiktok": tiktok_status(),
            "fal": list_fal_avatars(),
            "funding": list_funding_sources(),
        },
        "stages": {},
    }

    # Root Linear issue
    root_issue = agency_track(
        title=f"Lifecycle run: {niche}",
        description=f"Autonomous lifecycle (no payments).\nProcessor={processor}\nCPA target=${cpa}",
        stage="research",
        priority=2,
    )
    report["root_linear"] = root_issue

    print("[1/7] Research…")
    research = stage_research(niche, processor, timeout)
    report["stages"]["research"] = {
        "search_id": (research.get("search") or {}).get("search_id"),
        "task_id": (research.get("task") or {}).get("task_id") or (research.get("task") or {}).get("id"),
        "task_status": (research.get("task") or {}).get("status"),
    }
    cands = _extract_candidates(research.get("task") or {})
    ranked = stage_score(cands, cpa)
    report["ranked"] = ranked[: max(top_n * 2, top_n)]
    print(f"  candidates={len(ranked)}")

    selected = [c for c in ranked if c.get("decision") in {"GO", "TEST"}][:top_n]
    if not selected and ranked:
        selected = ranked[:top_n]
    report["selected"] = selected

    products_out = []
    for i, c in enumerate(selected, 1):
        name = c.get("name") or f"Candidate {i}"
        print(f"[2-6/7] Pipeline for: {name}")
        econ = c.get("economics") or {}
        desc = (
            f"## {name}\n\n"
            f"- decision: **{c.get('decision')}** score={c.get('composite_score')}\n"
            f"- price: {econ.get('sell_price')} COGS={econ.get('cogs')} ship={econ.get('shipping')} CPA={cpa}\n"
            f"- CM$: {econ.get('contribution_margin_usd')} CM%={econ.get('contribution_margin_pct')}\n"
            f"- why: {c.get('why_now')}\n"
            f"- risks: {c.get('risks')}\n"
            f"- differentiation: {c.get('differentiation')}\n"
            f"- evidence: {c.get('evidence_urls')}\n"
        )
        issue = agency_track(title=name, description=desc, stage="research", priority=3 if c.get("decision") == "GO" else 4)

        # logistics + supplier heuristic
        ship_prof = estimate_shipping_profile(weight_g=350)
        supplier = score_supplier(
            name=f"TBD supplier for {name}",
            lead_time_days=12,
            moq=1,
            unit_cost=float(econ.get("cogs") or 8),
            shipping_cost=float(econ.get("shipping") or ship_prof["estimated_ship_cost_usd"]),
            rating=4.2,
        )
        supply_issue = agency_track(
            title=f"Supply test plan — {name}",
            description=f"Supplier scorecard:\n```json\n{json.dumps(supplier, indent=2)}\n```\nShipping:\n```json\n{json.dumps(ship_prof, indent=2)}\n```",
            stage="supply",
            priority=3,
        )

        # creative + fal
        hook = c.get("hook") or f"I keep this at my desk now — {name}"
        script = (
            f"{hook}. Here's the 5-minute reset I actually do between meetings. "
            f"No complicated setup. Link in bio if you want the kit."
        )
        ugc = build_ugc_brief_and_render(
            product_name=name,
            hook=hook,
            script_15s=script,
            render=render_ugc,
        )
        creative_issue = agency_track(
            title=f"UGC pack — {name}",
            description=f"```json\n{json.dumps(ugc, indent=2)[:4000]}\n```",
            stage="creative",
            priority=3,
        )

        # shopify draft
        price = str(econ.get("sell_price") or c.get("suggested_price_usd") or "39.99")
        body = f"<p>{c.get('why_now') or name}</p><p>{c.get('differentiation') or ''}</p>"
        shop = draft_product(
            title=name,
            body_html=body,
            price=price,
            tags=["agency", "autonomous", niche[:40]],
            status="draft",
        )
        store_issue = agency_track(
            title=f"Shopify draft — {name}",
            description=f"```json\n{json.dumps(shop, indent=2)[:2500]}\n```",
            stage="ops",
            priority=4,
        )

        # ad drafts (not live)
        daily = 25.0
        meta_d = meta_draft_campaign(
            name=f"{name} — learning",
            daily_budget_usd=daily,
            landing_url="https://example.com/products/pending",
            creative_message=hook,
            video_url=((ugc.get("render") or {}).get("video_url") or ""),
        )
        tt_d = tiktok_draft_campaign(
            name=f"{name} — learning",
            daily_budget_usd=daily,
            ad_text=hook,
            video_url=((ugc.get("render") or {}).get("video_url") or ""),
        )
        growth_issue = agency_track(
            title=f"Ad drafts — {name}",
            description=(
                f"Meta draft: `{meta_d.get('id')}`\nTikTok draft: `{tt_d.get('id')}`\n"
                f"Daily budget planned: ${daily}\n**Not live — awaiting HITL spend approval.**"
            ),
            stage="growth",
            priority=2,
        )

        # HITL spend request (does not go live)
        spend = request_spend_approval(
            amount_usd=daily * 7,  # weekly learning envelope
            channel="meta+tiktok",
            purpose=f"7-day learning budget for {name}",
            campaign_draft_id=f"{meta_d.get('id')},{tt_d.get('id')}",
            daily_budget_usd=daily,
            max_total_usd=daily * 10,
            linear_issue=str((growth_issue or {}).get("identifier") or (growth_issue or {}).get("id") or ""),
        )

        products_out.append(
            {
                "product": name,
                "decision": c.get("decision"),
                "score": c.get("composite_score"),
                "economics": econ,
                "linear": {
                    "product": issue,
                    "supply": supply_issue,
                    "creative": creative_issue,
                    "store": store_issue,
                    "growth": growth_issue,
                },
                "supplier": supplier,
                "shipping": ship_prof,
                "ugc": ugc,
                "shopify": shop,
                "ads": {"meta": meta_d, "tiktok": tt_d},
                "spend_approval": {
                    k: v
                    for k, v in (spend or {}).items()
                    if k != "human_confirm_code"  # keep code only in secure log below
                },
                "spend_human_confirm_code": (spend or {}).get("human_confirm_code"),
            }
        )

    report["products"] = products_out
    report["meta"]["elapsed_s"] = round(time.time() - started, 1)
    report["meta"]["finished"] = _utc()
    report["human_next_steps"] = [
        "Review Linear SPE issues for each product stage",
        "Attach funding source if needed: attach_funding_source(kind='bank'| 'crypto', ...)",
        "Confirm spend with confirm_spend_approval(approval_id, confirm_code, human_ack='I authorize...')",
        "Then meta_launch_campaign / tiktok_launch_campaign with approval_id + spend_token",
        "Do NOT pay suppliers / place bulk POs without separate human approval",
    ]

    RUNS.mkdir(parents=True, exist_ok=True)
    stamp = _utc()
    json_path = RUNS / f"lifecycle_{stamp}.json"
    md_path = RUNS / f"lifecycle_{stamp}.md"
    # write JSON without confirm codes in main artifact? Keep them for operator in a sidecar
    public = json.loads(json.dumps(report))
    codes = []
    for p in public.get("products") or []:
        code = p.pop("spend_human_confirm_code", None)
        if code:
            codes.append({"product": p.get("product"), "approval_id": (p.get("spend_approval") or {}).get("approval_id"), "code": code})
    json_path.write_text(json.dumps(public, indent=2))
    codes_path = RUNS / f"lifecycle_{stamp}_HITL_CODES.json"
    codes_path.write_text(json.dumps(codes, indent=2))
    try:
        codes_path.chmod(0o600)
    except OSError:
        pass

    # markdown summary
    lines = [
        f"# Autonomous lifecycle — {niche}",
        "",
        f"- finished: {report['meta']['finished']}",
        f"- processor: {processor}",
        f"- root linear: {(root_issue or {}).get('identifier')} {(root_issue or {}).get('url')}",
        f"- linear mode: {(report['meta'].get('linear') or {}).get('mode')}",
        "",
        "## Selected products",
    ]
    for p in products_out:
        sa = p.get("spend_approval") or {}
        lines += [
            f"### {p.get('product')} — {p.get('decision')} (score {p.get('score')})",
            f"- CM: {((p.get('economics') or {}).get('contribution_margin_pct'))}",
            f"- Linear product: {(p.get('linear') or {}).get('product', {}).get('identifier')}",
            f"- Shopify: {(p.get('shopify') or {}).get('id')} stub={(p.get('shopify') or {}).get('stub')}",
            f"- Meta draft: {(p.get('ads') or {}).get('meta', {}).get('id')}",
            f"- TikTok draft: {(p.get('ads') or {}).get('tiktok', {}).get('id')}",
            f"- Spend approval: `{sa.get('approval_id')}` status={sa.get('status')} amount=${sa.get('amount_usd')}",
            f"- HITL code: see `{codes_path.name}` (mode 600)",
            "",
        ]
    lines += ["## Human next steps"] + [f"- {x}" for x in report["human_next_steps"]]
    md_path.write_text("\n".join(lines) + "\n")

    # comment root issue
    try:
        rid = (root_issue or {}).get("id") or (root_issue or {}).get("identifier")
        if rid:
            update_linear_issue(
                str(rid),
                state="started",
                comment=f"Lifecycle finished. Report: `{md_path}`\nProducts: {len(products_out)}",
            )
    except Exception:
        pass

    report["artifacts"] = {"json": str(json_path), "md": str(md_path), "hitl_codes": str(codes_path)}
    print(json.dumps({"ok": True, **report["artifacts"], "products": len(products_out)}, indent=2))
    return report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--niche", required=True)
    ap.add_argument("--processor", default="ultra", choices=["lite", "base", "core", "core2x", "pro", "ultra"])
    ap.add_argument("--top", type=int, default=3)
    ap.add_argument("--cpa", type=float, default=18.0)
    ap.add_argument("--timeout", type=int, default=3600)
    ap.add_argument("--render-ugc", action="store_true", help="Call Fal (needs FAL_KEY); default brief-only")
    args = ap.parse_args()
    run(args.niche, args.processor, args.top, args.cpa, args.timeout, args.render_ugc)


if __name__ == "__main__":
    main()
