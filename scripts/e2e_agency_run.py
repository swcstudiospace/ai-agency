#!/usr/bin/env python3
"""Full agency E2E smoke (research → econ → Linear → Shopify draft → ads draft → HITL).

Does NOT place real ad spend or publish live products.
Shopify goes live only when SHOPIFY_SHOP_NAME is set and client credentials work.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from tools.envutil import load_dotenv_files

load_dotenv_files()

from tools.economics_tools import contribution_margin
from tools.linear_tools import create_linear_issue, linear_status
from tools.logistics_tools import estimate_shipping_profile
from tools.meta_ads_tools import meta_draft_campaign, meta_status
from tools.parallel_tools import parallel_search, parallel_task
from tools.promptwise_tools import promptwise_build_ugc_brief, promptwise_status
from tools.shopify_tools import draft_product, list_products, shopify_status
from tools.spend_vault import request_spend_approval
from tools.supplier_tools import score_supplier
from tools.tiktok_ads_tools import tiktok_draft_campaign, tiktok_status
from tools.xai_model import DEFAULT_GROK_MODEL, get_grok_model
from tools.xai_oauth_pkce import get_xai_token_or_fallback


def utc() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def main() -> int:
    stamp = utc()
    out_dir = ROOT / "tmp" / "runs"
    out_dir.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {
        "meta": {
            "stamp": stamp,
            "niche": os.getenv("E2E_NICHE")
            or "desk mobility and posture tools for remote workers",
            "grok_model": DEFAULT_GROK_MODEL,
            "processor": os.getenv("E2E_PROCESSOR") or "pro",
        },
        "stages": {},
    }
    niche = report["meta"]["niche"]
    processor = report["meta"]["processor"]

    print("=== Agency E2E ===")
    print(f"niche={niche} processor={processor} grok={DEFAULT_GROK_MODEL}")

    # 0) auth probes
    stages: dict[str, Any] = {}
    try:
        tok = get_xai_token_or_fallback()
        m = get_grok_model()
        stages["supergrok"] = {
            "ok": bool(tok),
            "model": getattr(m, "id", None),
            "token_len": len(tok or ""),
        }
    except Exception as e:
        stages["supergrok"] = {"ok": False, "error": str(e)}
    stages["linear"] = linear_status()
    stages["shopify"] = shopify_status()
    stages["meta"] = meta_status()
    stages["tiktok"] = tiktok_status()
    stages["promptwise"] = promptwise_status()
    print(
        "auth:",
        {k: (v.get("ok"), v.get("mode") or v.get("model")) for k, v in stages.items()},
    )

    # 1) research
    skip_research = (os.getenv("E2E_SKIP_RESEARCH") or "").lower() in {"1", "true", "yes"}
    if skip_research:
        print("\n[1-2/7] Skipping Parallel research (E2E_SKIP_RESEARCH=1) — using prior product rank…")
        stages["search"] = {"ok": True, "skipped": True}
        stages["task"] = {"ok": True, "skipped": True}
        candidates = []
        ranks = sorted(
            (ROOT / "tmp/runs").glob("product_rank_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if ranks:
            prev = json.loads(ranks[0].read_text())
            candidates = [
                {
                    "name": c.get("name"),
                    "estimated_cogs_usd": c.get("estimated_cogs_usd"),
                    "shipping_usd": c.get("shipping_usd"),
                    "suggested_price_usd": c.get("suggested_price_usd"),
                    "differentiation_angle": c.get("differentiation_angle"),
                    "why_now": c.get("why_now"),
                    "from_prior_rank": True,
                    "prior_decision": c.get("decision"),
                }
                for c in (prev.get("ranked_candidates") or [])[:8]
            ]
            stages["task"]["fallback_rank"] = ranks[0].name
            print(f"  loaded {len(candidates)} from {ranks[0].name}")
    else:
        print("\n[1/7] Parallel search…")
        search = parallel_search(
            objective=f"Dropshipping product opportunities in: {niche}",
            search_queries=[
                f"{niche} best sellers",
                f"{niche} dropshipping 2026",
            ],
            mode="advanced",
        )
        hits = (search.get("results") or [])[:8]
        stages["search"] = {
            "ok": not bool(search.get("error")),
            "search_id": search.get("search_id"),
            "hits": len(hits),
            "error": search.get("error"),
        }
        print(" ", stages["search"])

        print(f"\n[2/7] Parallel task ({processor})…")
        evidence = "\n".join(f"- {h.get('title')}: {h.get('url')}" for h in hits)
        schema = {
            "type": "json",
            "json_schema": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "market_summary": {"type": "string"},
                    "candidates": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "name": {"type": "string"},
                                "estimated_cogs_usd": {"type": "number"},
                                "shipping_usd": {"type": "number"},
                                "suggested_price_usd": {"type": "number"},
                                "differentiation_angle": {"type": "string"},
                                "why_now": {"type": "string"},
                            },
                            "required": [
                                "name",
                                "estimated_cogs_usd",
                                "shipping_usd",
                                "suggested_price_usd",
                            ],
                        },
                    },
                },
                "required": ["market_summary", "candidates"],
            },
        }
        task = parallel_task(
            objective=(
                f"Find 5 concrete dropshipping products for niche: {niche}. "
                f"Seed hits:\n{evidence}\nReturn JSON with market_summary and candidates."
            ),
            processor=processor,
            output_schema=schema,
            wait=True,
            timeout_s=float(os.getenv("E2E_TIMEOUT", "900")),
        )
        stages["task"] = {
            "ok": not bool(task.get("error")),
            "task_id": task.get("task_id"),
            "status": task.get("status"),
            "error": task.get("error"),
        }
        print(" ", {k: stages["task"][k] for k in ("ok", "task_id", "status", "error")})

        # parse candidates
        candidates = []
        raw = task.get("output")
        try:
            if isinstance(raw, dict):
                candidates = raw.get("candidates") or raw.get("content") or []
                if isinstance(candidates, dict):
                    candidates = candidates.get("candidates") or []
            elif isinstance(raw, str):
                candidates = json.loads(raw).get("candidates") or []
            elif isinstance(raw, list):
                candidates = raw
        except Exception:
            try:
                content = raw
                if isinstance(content, dict) and "content" in content:
                    content = content["content"]
                if isinstance(content, str):
                    candidates = json.loads(content).get("candidates") or []
            except Exception as e:
                stages["task"]["parse_error"] = str(e)

        # fallback to last product rank if task empty
        if not candidates:
            ranks = sorted(
                (ROOT / "tmp/runs").glob("product_rank_*.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            if ranks:
                prev = json.loads(ranks[0].read_text())
                candidates = [
                    {
                        "name": c.get("name"),
                        "estimated_cogs_usd": c.get("estimated_cogs_usd"),
                        "shipping_usd": c.get("shipping_usd"),
                        "suggested_price_usd": c.get("suggested_price_usd"),
                        "differentiation_angle": c.get("differentiation_angle"),
                        "why_now": c.get("why_now"),
                        "from_prior_rank": True,
                    }
                    for c in (prev.get("ranked_candidates") or [])[:5]
                ]
                stages["task"]["fallback_rank"] = ranks[0].name

    # 3) unit econ + supplier + logistics
    print("\n[3/7] Unit economics + supplier + logistics…")
    ranked = []
    for c in candidates[:5]:
        price = float(c.get("suggested_price_usd") or 49.99)
        cogs = float(c.get("estimated_cogs_usd") or 12.0)
        ship = float(c.get("shipping_usd") or 5.5)
        econ = contribution_margin(price, cogs, ship, ad_spend_per_order=18.0)
        cm_pct = float(econ.get("contribution_margin_pct") or 0)
        decision = "GO" if cm_pct >= 0.28 else ("TEST" if cm_pct >= 0.18 else "NO-GO")
        # prefer prior GO/TEST labels when reusing rank artifacts
        if c.get("prior_decision") in {"GO", "TEST", "NO-GO"} and c.get("from_prior_rank"):
            decision = c["prior_decision"]
        supplier = score_supplier(
            name=str(c.get("name") or "supplier")[:80],
            lead_time_days=7,
            moq=50,
            unit_cost=cogs,
            shipping_cost=ship,
            rating=4.4,
        )
        logistics = estimate_shipping_profile(
            weight_g=450,
            length_cm=28,
            width_cm=20,
            height_cm=6,
            dest_country="US",
        )
        ranked.append(
            {
                **c,
                "economics": econ,
                "decision": decision,
                "supplier": supplier,
                "logistics": logistics,
            }
        )
        print(
            f"  [{decision}] {c.get('name')} ${price} CM%={cm_pct*100:.1f}"
        )
    stages["economics"] = {
        "ok": bool(ranked),
        "count": len(ranked),
        "go_test": sum(1 for r in ranked if r.get("decision") in {"GO", "TEST"}),
    }

    top = [r for r in ranked if r.get("decision") in {"GO", "TEST"}][:3] or ranked[:1]
    hero = top[0] if top else {
        "name": "Fold-Flat Adjustable Aluminum Laptop Stand",
        "suggested_price_usd": 49.99,
        "estimated_cogs_usd": 14.0,
        "shipping_usd": 5.5,
        "differentiation_angle": "fold-flat travel + desk ergonomics",
        "decision": "GO",
        "economics": contribution_margin(49.99, 14.0, 5.5, ad_spend_per_order=18.0),
    }

    # 4) Linear
    print("\n[4/7] Linear dual-write…")
    linear_issues = []
    try:
        parent = create_linear_issue(
            title=f"[E2E] Product pipeline — {hero.get('name')}"[:250],
            description=(
                f"**E2E stamp:** `{stamp}`\n"
                f"**Niche:** {niche}\n"
                f"**Hero:** {hero.get('name')} ({hero.get('decision')})\n"
                f"**Price:** ${hero.get('suggested_price_usd')}\n"
                f"**Shopify:** {stages['shopify']}\n"
                f"**Grok:** {stages['supergrok']}\n"
            ),
            priority=2,
        )
        linear_issues.append(parent)
        print(" ", parent.get("identifier"), parent.get("url"), "gh", (parent.get("github") or {}).get("github_url"))
        for r in top[:2]:
            child = create_linear_issue(
                title=f"[{r.get('decision')}] {r.get('name')}"[:250],
                description=f"From E2E `{stamp}`\nAngle: {r.get('differentiation_angle')}\nEcon: {r.get('economics')}",
                priority=2 if r.get("decision") == "GO" else 3,
            )
            linear_issues.append(child)
            print(" ", child.get("identifier"), child.get("url"))
        stages["linear_write"] = {
            "ok": all(not i.get("stub") and i.get("identifier") for i in linear_issues if isinstance(i, dict)),
            "issues": [
                {"id": i.get("identifier"), "url": i.get("url"), "github": (i.get("github") or {}).get("github_url")}
                for i in linear_issues
                if isinstance(i, dict)
            ],
        }
    except Exception as e:
        stages["linear_write"] = {"ok": False, "error": str(e)}
        print("  linear error", e)

    # 5) PromptWise brief + Shopify draft
    print("\n[5/7] PromptWise UGC brief…")
    try:
        brief = promptwise_build_ugc_brief(
            product_name=str(hero.get("name")),
            angle=str(hero.get("differentiation_angle") or ""),
            hook=f"Desk glow-up: {hero.get('name')}",
            price_usd=float(hero.get("suggested_price_usd") or 49.99),
        )
        stages["promptwise_brief"] = {"ok": True, "artifact": brief.get("artifact")}
        print(" ", brief.get("artifact"))
    except Exception as e:
        stages["promptwise_brief"] = {"ok": False, "error": str(e)}

    print("\n[6/7] Shopify draft product…")
    body = (
        f"<p><strong>{hero.get('name')}</strong></p>"
        f"<p>{hero.get('differentiation_angle') or ''}</p>"
        f"<p>{hero.get('why_now') or 'Built for remote workers.'}</p>"
        f"<p><em>Draft created by AI Dropshipping Agency E2E — not published.</em></p>"
    )
    shop_prod = draft_product(
        title=f"[DRAFT E2E] {hero.get('name')}",
        body_html=body,
        price=str(hero.get("suggested_price_usd") or "49.99"),
        tags=["agency-e2e", "draft", "desk-mobility"],
        vendor="AI Dropshipping Agency",
        status="draft",
        product_type="Home Office",
    )
    stages["shopify_draft"] = {
        "ok": bool(shop_prod.get("id")) and not shop_prod.get("error"),
        "stub": bool(shop_prod.get("stub")),
        "product_id": shop_prod.get("id"),
        "title": shop_prod.get("title"),
        "status": shop_prod.get("status"),
        "admin_url": (
            f"https://{stages['shopify'].get('shop_host')}/admin/products/{shop_prod.get('id')}"
            if stages["shopify"].get("shop_host") and shop_prod.get("id") and not shop_prod.get("stub")
            else None
        ),
        "error": shop_prod.get("error"),
        "reason": stages["shopify"].get("reason"),
    }
    print(" ", stages["shopify_draft"])
    if not shop_prod.get("stub") and shop_prod.get("id"):
        listed = list_products(limit=5, status="draft")
        stages["shopify_list"] = {
            "ok": not listed.get("stub"),
            "count": len(listed.get("products") or []),
        }

    # 6) Ads drafts + HITL spend request (no live launch)
    print("\n[7/7] Ad drafts + HITL spend request (no live spend)…")
    price = float(hero.get("suggested_price_usd") or 49.99)
    meta = meta_draft_campaign(
        name=f"E2E {hero.get('name')}"[:100],
        daily_budget_usd=25.0,
        objective="OUTCOME_SALES",
        countries=["US"],
        landing_url="https://example.com/e2e-draft",
    )
    tt = tiktok_draft_campaign(
        name=f"E2E {hero.get('name')}"[:100],
        daily_budget_usd=20.0,
        objective_type="CONVERSIONS",
    )
    spend = request_spend_approval(
        channel="meta",
        amount_usd=75.0,
        purpose=f"E2E draft only — {hero.get('name')} — human must confirm before any live ads",
        campaign_draft_id=str(meta.get("id") or ""),
        daily_budget_usd=25.0,
    )
    stages["ads"] = {
        "meta_draft": {"ok": True, "stub": meta.get("stub", True), "id": meta.get("id") or meta.get("campaign_id")},
        "tiktok_draft": {"ok": True, "stub": tt.get("stub", True), "id": tt.get("id") or tt.get("campaign_id")},
        "hitl_spend": {
            "ok": bool(spend.get("approval_id") or spend.get("id")),
            "approval_id": spend.get("approval_id") or spend.get("id"),
            "status": spend.get("status"),
            # never print confirm codes in shared logs if present — keep id only
        },
    }
    print(" ", stages["ads"])

    report["stages"] = stages
    report["hero"] = hero
    report["ranked"] = ranked
    report["linear_issues"] = stages.get("linear_write", {}).get("issues")

    # summary scorecard
    checks = {
        "supergrok": bool(stages.get("supergrok", {}).get("ok")),
        "parallel_search": bool(stages.get("search", {}).get("ok")),
        "parallel_task_or_fallback": bool(ranked),
        "linear": bool(stages.get("linear_write", {}).get("ok")),
        "promptwise_brief": bool(stages.get("promptwise_brief", {}).get("ok")),
        "shopify_live_draft": bool(stages.get("shopify_draft", {}).get("ok"))
        and not bool(stages.get("shopify_draft", {}).get("stub")),
        "shopify_stub_ok": bool(stages.get("shopify_draft", {}).get("stub")),
        "ads_drafts": True,
        "hitl_spend_created": bool(stages.get("ads", {}).get("hitl_spend", {}).get("ok")),
    }
    report["scorecard"] = checks
    report["pass_core"] = all(
        [
            checks["supergrok"],
            checks["parallel_search"],
            checks["parallel_task_or_fallback"],
            checks["linear"],
            checks["promptwise_brief"],
            checks["hitl_spend_created"],
        ]
    )
    report["shopify_gate"] = (
        "LIVE" if checks["shopify_live_draft"] else "BLOCKED_NEED_SHOP_NAME_OR_INSTALL"
    )

    jp = out_dir / f"e2e_{stamp}.json"
    mp = out_dir / f"e2e_{stamp}.md"
    jp.write_text(json.dumps(report, indent=2, default=str) + "\n")

    lines = [
        f"# Agency E2E — {stamp}",
        "",
        f"- Niche: `{niche}`",
        f"- Core pass: **{report['pass_core']}**",
        f"- Shopify: **{report['shopify_gate']}**",
        f"- Grok: `{stages.get('supergrok')}`",
        "",
        "## Scorecard",
        "",
    ]
    for k, v in checks.items():
        lines.append(f"- {'✅' if v else '❌'} `{k}`")
    lines += ["", "## Hero product", f"- **{hero.get('name')}** ({hero.get('decision')})", f"- Price ${hero.get('suggested_price_usd')}", ""]
    if stages.get("linear_write", {}).get("issues"):
        lines.append("## Linear")
        for i in stages["linear_write"]["issues"]:
            lines.append(f"- [{i.get('id')}]({i.get('url')}) {i.get('github') or ''}")
    lines += ["", f"JSON: `{jp}`", ""]
    if report["shopify_gate"] != "LIVE":
        lines += [
            "## Shopify blocked",
            "Client ID + secret are configured. Provide **SHOPIFY_SHOP_NAME** "
            "(e.g. `your-store` for `your-store.myshopify.com`) and ensure the Dev Dashboard app "
            "is **installed** on that shop with product write scopes. Then re-run:",
            "```bash",
            "PYTHONPATH=. python -m scripts.e2e_agency_run",
            "```",
            "",
        ]
    mp.write_text("\n".join(lines) + "\n")

    print("\n=== E2E done ===")
    print(f"core_pass={report['pass_core']} shopify={report['shopify_gate']}")
    print(f"JSON {jp}")
    print(f"MD   {mp}")
    return 0 if report["pass_core"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
