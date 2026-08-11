#!/usr/bin/env python3
"""Autonomous product LOCATE pipeline.

After product rank picks GO/TEST SKUs, this finds *where to buy them*:
  1. Load latest product_rank_*.json (or run rank if --rank-first)
  2. For top GO/TEST products → Parallel supplier locate
  3. Score suppliers + logistics profile
  4. Linear dual-write + optional Shopify draft package notes
  5. Write tmp/runs/product_locate_*.{json,md}

Usage:
  PYTHONPATH=. python -m scripts.autonomous_product_locate
  PYTHONPATH=. python -m scripts.autonomous_product_locate --product "Fold-Flat Laptop Stand"
  PYTHONPATH=. python -m scripts.autonomous_product_locate --rank-first --niche "desk mobility"
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from tools.envutil import load_dotenv_files

load_dotenv_files()

from tools.linear_tools import create_linear_issue
from tools.logistics_tools import estimate_shipping_profile
from tools.supplier_tools import locate_suppliers_for_product


def utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def load_top_products(limit: int = 3) -> List[Dict[str, Any]]:
    ranks = sorted(
        (ROOT / "tmp/runs").glob("product_rank_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not ranks:
        return []
    data = json.loads(ranks[0].read_text())
    ranked = data.get("ranked_candidates") or []
    picks = [c for c in ranked if c.get("decision") in {"GO", "TEST"}][:limit]
    if not picks:
        picks = ranked[:limit]
    for p in picks:
        p["_source_rank"] = ranks[0].name
    return picks


def main(argv: List[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Locate suppliers for ranked products")
    ap.add_argument("--product", default="", help="Single product name (skips rank load)")
    ap.add_argument("--top", type=int, default=3)
    ap.add_argument("--processor", default="pro", choices=["lite", "base", "core", "pro", "ultra"])
    ap.add_argument("--dest", default="US")
    ap.add_argument("--rank-first", action="store_true")
    ap.add_argument("--niche", default="desk mobility and posture tools for remote workers")
    ap.add_argument("--no-linear", action="store_true")
    args = ap.parse_args(argv)

    stamp = utc()
    out_dir = ROOT / "tmp" / "runs"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=== Product LOCATE ===")
    products: List[Dict[str, Any]] = []
    if args.product:
        products = [{"name": args.product, "decision": "MANUAL", "suggested_price_usd": None}]
    else:
        if args.rank_first:
            print("[0] Running product rank first…")
            from scripts.autonomous_product_rank import main as rank_main

            rc = rank_main(["--niche", args.niche, "--processor", args.processor])
            print("  rank exit", rc)
        products = load_top_products(limit=args.top)
        if not products:
            print("No product_rank artifacts — pass --product or --rank-first")
            return 2

    print(f"locating {len(products)} products → dest={args.dest} processor={args.processor}")

    results = []
    for p in products:
        name = str(p.get("name") or "").strip()
        if not name:
            continue
        price = float(p.get("suggested_price_usd") or 49.99)
        target_cogs = max(5.0, price * 0.28)
        print(f"\n→ {name} (target COGS ~${target_cogs:.2f})")
        loc = locate_suppliers_for_product(
            product_name=name,
            target_unit_cost_usd=target_cogs,
            dest_market=args.dest,
            processor=args.processor,
            max_suppliers=5,
        )
        logistics = estimate_shipping_profile(dest_country=args.dest)
        loc["logistics_profile"] = logistics
        loc["product_decision"] = p.get("decision")
        loc["product_price_usd"] = price
        top = loc.get("top_supplier") or {}
        print(
            f"  ok={loc.get('ok')} suppliers={len(loc.get('suppliers') or [])} "
            f"top={top.get('name')} landed=${top.get('landed_cost_usd')}"
        )

        if not args.no_linear:
            try:
                body_lines = [
                    f"**Product:** {name}",
                    f"**Decision:** {p.get('decision')}",
                    f"**Retail:** ${price}",
                    f"**Locate task:** `{loc.get('task_id')}`",
                    "",
                    loc.get("summary") or "",
                    "",
                    "## Suppliers",
                ]
                for i, s in enumerate(loc.get("suppliers") or [], 1):
                    body_lines.append(
                        f"{i}. **{s.get('name')}** ({s.get('platform')}) — "
                        f"unit ${s.get('unit_cost_usd_est')} ship ${s.get('shipping_usd_est')} "
                        f"MOQ {s.get('moq')} score {s.get('scorecard', {}).get('score')} "
                        f"[link]({s.get('url')})"
                    )
                body_lines += [
                    "",
                    f"**Next:** {loc.get('recommended_next_step')}",
                    "",
                    "_HITL: do not pay samples/POs without human approval._",
                ]
                issue = create_linear_issue(
                    title=f"[Locate] {name}"[:250],
                    description="\n".join(body_lines),
                    priority=2 if p.get("decision") == "GO" else 3,
                )
                loc["linear"] = {
                    "identifier": issue.get("identifier"),
                    "url": issue.get("url"),
                    "github": (issue.get("github") or {}).get("github_url"),
                }
                print(f"  Linear {issue.get('identifier')} {issue.get('url')}")
            except Exception as e:
                loc["linear"] = {"error": str(e)}
                print("  Linear error", e)

        results.append(loc)

    payload = {
        "meta": {
            "stamp": stamp,
            "dest": args.dest,
            "processor": args.processor,
            "count": len(results),
        },
        "results": results,
    }
    jp = out_dir / f"product_locate_{stamp}.json"
    mp = out_dir / f"product_locate_{stamp}.md"
    jp.write_text(json.dumps(payload, indent=2, default=str) + "\n")

    lines = [
        f"# Product locate — {stamp}",
        "",
        f"- Dest market: `{args.dest}`",
        f"- Processor: `{args.processor}`",
        f"- Products: **{len(results)}**",
        "",
    ]
    for r in results:
        lines.append(f"## {r.get('product_name')} ({r.get('product_decision')})")
        lines.append(r.get("summary") or "_no summary_")
        lines.append("")
        top = r.get("top_supplier") or {}
        if top:
            lines.append(
                f"**Top supplier:** {top.get('name')} · {top.get('platform')} · "
                f"landed ${top.get('landed_cost_usd')} · "
                f"[url]({top.get('url')})"
            )
        lin = r.get("linear") or {}
        if lin.get("identifier"):
            lines.append(f"- Linear: [{lin.get('identifier')}]({lin.get('url')})")
        lines.append("")
        lines.append("| # | Supplier | Platform | Unit | Ship | MOQ | Score |")
        lines.append("|---|----------|----------|------|------|-----|-------|")
        for i, s in enumerate(r.get("suppliers") or [], 1):
            lines.append(
                f"| {i} | {s.get('name')} | {s.get('platform')} | "
                f"${s.get('unit_cost_usd_est')} | ${s.get('shipping_usd_est')} | "
                f"{s.get('moq')} | {s.get('scorecard', {}).get('score')} |"
            )
        lines.append("")
    mp.write_text("\n".join(lines) + "\n")

    print("\n=== locate done ===")
    print(jp)
    print(mp)
    return 0 if any(r.get("ok") for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
