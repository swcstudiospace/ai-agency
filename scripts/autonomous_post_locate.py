#!/usr/bin/env python3
"""Post-locate automation: seller outreach drafts + shipping pipeline plan.

After product_locate answers *where to buy*, this stage prepares:
  A) sample / dropship inquiry emails (Gmail compose HITL)
  B) fulfillment / shipping pipeline design for Shopify → supplier

Usage:
  PYTHONPATH=. python -m scripts.autonomous_post_locate
  PYTHONPATH=. python -m scripts.autonomous_post_locate --open-gmail
  PYTHONPATH=. python -m scripts.autonomous_post_locate --locate-json tmp/runs/product_locate_….json
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
from tools.seller_outreach_tools import draft_supplier_outreach_email, open_gmail_compose
from tools.shipping_pipeline_tools import design_shipping_pipeline, setup_order_routing_playbook
from tools.shopify_tools import shopify_bootstrap_checklist, shopify_domain_plan


def utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def latest_locate() -> Path | None:
    runs = sorted((ROOT / "tmp/runs").glob("product_locate_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return runs[0] if runs else None


def main(argv: List[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--locate-json", default="")
    ap.add_argument("--top-suppliers", type=int, default=2)
    ap.add_argument("--open-gmail", action="store_true", help="Open first email in Gmail via bridge browser")
    ap.add_argument("--no-linear", action="store_true")
    ap.add_argument("--mode", default="supplier_dropship", choices=["supplier_dropship", "platform_cj", "stock_3pl", "hybrid"])
    args = ap.parse_args(argv)

    stamp = utc()
    path = Path(args.locate_json) if args.locate_json else latest_locate()
    if not path or not path.is_file():
        print("No product_locate artifact — run scripts.autonomous_product_locate first")
        return 2

    data = json.loads(path.read_text(encoding="utf-8"))
    results = data.get("results") or []
    print(f"=== Post-locate ===\nsource={path.name} products={len(results)}")

    out_items = []
    first_email_opened = False

    for r in results:
        product = str(r.get("product_name") or "product")
        origin = "CN"
        top = r.get("top_supplier") or {}
        ship = design_shipping_pipeline(
            product_name=product,
            origin_country=origin,
            fulfillment_mode=args.mode,
        )
        emails = []
        for s in (r.get("suppliers") or [])[: max(1, args.top_suppliers)]:
            d = draft_supplier_outreach_email(
                product_name=product,
                supplier_name=str(s.get("name") or "Supplier"),
                supplier_url=str(s.get("url") or ""),
                unit_cost_usd=float(s.get("unit_cost_usd_est") or 0),
                moq=float(s.get("moq") or 1),
            )
            if args.open_gmail and not first_email_opened:
                d["browser"] = open_gmail_compose(d["subject"], d["body"])
                first_email_opened = True
                print(f"  Gmail compose opened for {s.get('name')}")
            emails.append(d)
            print(f"  outreach draft → {d.get('artifact_md')}")

        item = {
            "product_name": product,
            "top_supplier": top,
            "emails": [
                {
                    "subject": e.get("subject"),
                    "artifact_md": e.get("artifact_md"),
                    "gmail_compose_url": e.get("gmail_compose_url"),
                    "browser_ok": (e.get("browser") or {}).get("ok"),
                }
                for e in emails
            ],
            "shipping_pipeline": {
                "mode": ship.get("fulfillment_mode"),
                "artifact": ship.get("artifact"),
                "steps": ship.get("pipeline_steps"),
                "sla": ship.get("sla"),
            },
        }
        out_items.append(item)

    playbook = setup_order_routing_playbook(mode=args.mode)
    bootstrap = shopify_bootstrap_checklist()
    domain = shopify_domain_plan()

    payload = {
        "meta": {"stamp": stamp, "source": str(path), "mode": args.mode},
        "items": out_items,
        "order_routing_playbook": playbook,
        "shopify_bootstrap": bootstrap,
        "domain_plan": domain,
        "decision_guide": {
            "contact_seller": (
                "YES for Alibaba/factory and most direct manufacturers — "
                "send sample + dropship terms email (HITL send via Gmail)."
            ),
            "shipping_pipeline": (
                "YES always — configure Shopify shipping profiles, policies, "
                "orders/paid routing, and tracking before paid ads. "
                "Platform apps (CJ/Doba) reduce manual supplier contact."
            ),
            "recommended_sequence": [
                "1. Draft/send sample emails to top 1-2 suppliers (HITL)",
                "2. Install Shopify app scopes + draft product",
                "3. Set shipping profile + policies + ego.engineer DNS",
                "4. Paid sample → QA",
                "5. Connect fulfillment mode (email push or CJ app)",
                "6. Test order → then creatives/ads HITL",
            ],
        },
    }

    out_dir = ROOT / "tmp" / "runs"
    out_dir.mkdir(parents=True, exist_ok=True)
    jp = out_dir / f"post_locate_{stamp}.json"
    mp = out_dir / f"post_locate_{stamp}.md"
    jp.write_text(json.dumps(payload, indent=2, default=str) + "\n")

    lines = [
        f"# Post-locate — {stamp}",
        "",
        f"Source locate: `{path.name}`",
        f"Fulfillment mode: `{args.mode}`",
        f"Domain: `{domain.get('primary_domain')}`",
        "",
        "## Do we contact the seller or set up shipping?",
        "",
        "**Both.** Contact top sellers for samples/dropship terms, and set up the shipping/order pipeline so paid orders can route.",
        "",
        "### Recommended sequence",
    ]
    for s in payload["decision_guide"]["recommended_sequence"]:
        lines.append(f"- {s}")
    lines += ["", "## Products"]
    for it in out_items:
        lines.append(f"### {it['product_name']}")
        top = it.get("top_supplier") or {}
        if top:
            lines.append(f"- Top supplier: **{top.get('name')}** landed ${top.get('landed_cost_usd')}")
        for e in it.get("emails") or []:
            lines.append(f"- Email: {e.get('subject')} → `{e.get('artifact_md')}`")
        lines.append(f"- Shipping plan: `{it['shipping_pipeline'].get('artifact')}`")
        lines.append("")
    lines += [
        "## Shopify bootstrap",
        f"- Live: **{bootstrap.get('shopify_status', {}).get('ok')}** ({bootstrap.get('shopify_status', {}).get('mode')})",
        f"- Reason: {bootstrap.get('shopify_status', {}).get('reason')}",
        "",
        "## Order routing checklist",
    ]
    for c in playbook.get("checklist") or []:
        lines.append(f"- [ ] {c}")
    lines += ["", "## DNS (ego.engineer)"]
    for rec in domain.get("dns_records_typical") or []:
        lines.append(f"- `{rec.get('type')}` {rec.get('host')} → {rec.get('value')} — {rec.get('note')}")

    mp.write_text("\n".join(lines) + "\n")

    if not args.no_linear:
        try:
            body = mp.read_text()[:12000]
            issue = create_linear_issue(
                title=f"[Post-locate] Outreach + shipping — {stamp}"[:250],
                description=body,
                priority=2,
            )
            print(f"Linear {issue.get('identifier')} {issue.get('url')}")
            payload["linear"] = {
                "identifier": issue.get("identifier"),
                "url": issue.get("url"),
            }
            jp.write_text(json.dumps(payload, indent=2, default=str) + "\n")
        except Exception as e:
            print("Linear error", e)

    print("=== post-locate done ===")
    print(jp)
    print(mp)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
