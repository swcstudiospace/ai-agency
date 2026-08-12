"""Seller outreach — draft sample/PO emails; optional Gmail compose via Hermes browser.

After product locate, humans usually:
  1) email/message the top supplier for sample + dropship terms
  2) or onboard a platform (CJ/Doba) that auto-fulfills

This module drafts HITL emails and can open Gmail compose in the bridge browser
for the operator to review/send (user logs into Gmail once in that profile).
"""

from __future__ import annotations

import json
import time
import uuid
import urllib.parse
from pathlib import Path
from typing import Any, Dict, List, Optional

from tools.envutil import env

_OUT_DIR = Path("tmp/outreach")


def draft_supplier_outreach_email(
    product_name: str,
    supplier_name: str,
    supplier_url: str = "",
    unit_cost_usd: float = 0.0,
    moq: float = 1,
    brand_name: str = "",
    dest_market: str = "US",
    sample_qty: int = 1,
    from_name: str = "",
    ask_dropship: bool = True,
) -> Dict[str, Any]:
    """Write a professional sample / dropship inquiry email (HITL — do not auto-send)."""
    brand = brand_name or env("SHOPIFY_SHOP_DISPLAY_NAME") or env("AGENCY_BRAND_NAME") or "AI Dropshipping Agency"
    sender = from_name or env("OUTREACH_FROM_NAME") or "Sourcing"
    domain = env("AGENCY_PRIMARY_DOMAIN") or env("SHOPIFY_PRIMARY_DOMAIN") or "ego.engineer"
    subject = f"Sample + dropship inquiry — {product_name}"[:180]

    body_lines = [
        f"Hi {supplier_name} team,",
        "",
        f"I'm {sender} with {brand} ({domain}). We're evaluating your listing for our store:",
        f"  Product: {product_name}",
    ]
    if supplier_url:
        body_lines.append(f"  Link: {supplier_url}")
    if unit_cost_usd:
        body_lines.append(f"  Reference unit cost we saw: ~USD {unit_cost_usd:.2f} (MOQ ~{moq})")
    body_lines += [
        "",
        "Could you please confirm:",
        f"1) Sample availability for {sample_qty} unit(s) to {dest_market}, sample cost + shipping, lead time.",
        "2) Bulk unit price at MOQ 1 / 10 / 50 / 100 (FOB or DDP to US if available).",
        "3) Whether you support dropshipping (we place orders → you ship to our customers with neutral packaging).",
        "4) Branding options (custom packaging / insert card) and any setup fees.",
        "5) Typical dispatch time after payment and which carriers you use for US parcels.",
        "6) Defective / RMA policy for retail customers.",
        "",
    ]
    if ask_dropship:
        body_lines.append(
            "If you have a CJ / Zendrop / Spocket / Doba style portal or private API for order push, "
            "please share onboarding steps."
        )
        body_lines.append("")
    body_lines += [
        "We're ready to place a paid sample this week if terms look good.",
        "",
        "Thanks,",
        f"{sender}",
        f"{brand}",
        domain,
    ]
    body = "\n".join(body_lines)

    _OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = f"{int(time.time())}_{uuid.uuid4().hex[:6]}"
    path = _OUT_DIR / f"email_{stamp}.json"
    payload = {
        "subject": subject,
        "body": body,
        "product_name": product_name,
        "supplier_name": supplier_name,
        "supplier_url": supplier_url,
        "hitl": True,
        "send_status": "draft_only",
        "note": "Human must review and send — agency never auto-sends supplier email",
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    md = _OUT_DIR / f"email_{stamp}.md"
    md.write_text(f"# {subject}\n\n**To:** {supplier_name}\n\n```\n{body}\n```\n", encoding="utf-8")

    return {
        "ok": True,
        "subject": subject,
        "body": body,
        "to_hint": supplier_name,
        "artifact_json": str(path),
        "artifact_md": str(md),
        "hitl": True,
        "gmail_compose_url": gmail_compose_url(to="", subject=subject, body=body),
    }


def gmail_compose_url(to: str = "", subject: str = "", body: str = "") -> str:
    """Build Gmail web compose deep link (operator still clicks Send)."""
    q = {
        "view": "cm",
        "fs": "1",
        "to": to or "",
        "su": subject or "",
        "body": body or "",
    }
    return "https://mail.google.com/mail/?" + urllib.parse.urlencode(q)


def open_gmail_compose(
    subject: str,
    body: str,
    to: str = "",
    screenshot: bool = True,
) -> Dict[str, Any]:
    """Open Gmail compose via Hermes reverse-bridge browser (HITL send).

    Operator must already be logged into Gmail in the bridge Playwright profile,
    or log in when the page opens.
    """
    url = gmail_compose_url(to=to, subject=subject, body=body)
    result: Dict[str, Any] = {
        "ok": False,
        "mode": "browser",
        "url": url,
        "hitl": True,
        "note": "Review in Gmail then click Send yourself — agency does not auto-send",
    }
    try:
        from tools import hermes_bridge_tools as hbt

        nav = hbt.hermes_browser_navigate(url=url)
        result["navigate"] = {
            "ok": not bool(nav.get("error")),
            "title": nav.get("title"),
            "final_url": nav.get("url") or nav.get("final_url"),
            "error": nav.get("error"),
        }
        if screenshot and hasattr(hbt, "hermes_browser_screenshot"):
            shot = hbt.hermes_browser_screenshot(url=url)
            result["screenshot"] = {
                "ok": not bool(shot.get("error")),
                "path": shot.get("path") or shot.get("file"),
                "error": shot.get("error"),
            }
        result["ok"] = bool(result["navigate"].get("ok"))
    except Exception as e:
        result["error"] = str(e)
        result["fallback"] = "Open gmail_compose_url manually in a logged-in browser"
    return result


def draft_and_open_outreach(
    product_name: str,
    supplier_name: str,
    supplier_url: str = "",
    unit_cost_usd: float = 0.0,
    moq: float = 1,
    open_browser: bool = True,
    to_email: str = "",
) -> Dict[str, Any]:
    """Draft email + optionally open Gmail compose for human send."""
    draft = draft_supplier_outreach_email(
        product_name=product_name,
        supplier_name=supplier_name,
        supplier_url=supplier_url,
        unit_cost_usd=unit_cost_usd,
        moq=moq,
    )
    out: Dict[str, Any] = {"draft": draft, "browser": None}
    if open_browser and (env("OUTREACH_BROWSER_ENABLED") or "1") not in {"0", "false", "no"}:
        out["browser"] = open_gmail_compose(
            subject=draft["subject"],
            body=draft["body"],
            to=to_email or env("OUTREACH_DEFAULT_TO") or "",
        )
    return out


def batch_outreach_from_locate(
    locate_json_path: str = "",
    top_n: int = 2,
    open_browser: bool = False,
) -> Dict[str, Any]:
    """Load latest product_locate_*.json and draft outreach for top suppliers."""
    path: Optional[Path] = Path(locate_json_path) if locate_json_path else None
    if not path or not path.is_file():
        runs = sorted(Path("tmp/runs").glob("product_locate_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        path = runs[0] if runs else None
    if not path or not path.is_file():
        return {"ok": False, "error": "no product_locate artifact"}

    data = json.loads(path.read_text(encoding="utf-8"))
    drafts = []
    for r in data.get("results") or []:
        product = r.get("product_name") or "product"
        for s in (r.get("suppliers") or [])[: max(1, top_n)]:
            d = draft_supplier_outreach_email(
                product_name=product,
                supplier_name=str(s.get("name") or "Supplier"),
                supplier_url=str(s.get("url") or ""),
                unit_cost_usd=float(s.get("unit_cost_usd_est") or 0),
                moq=float(s.get("moq") or 1),
            )
            if open_browser and len(drafts) == 0:
                d["browser"] = open_gmail_compose(d["subject"], d["body"])
            drafts.append(d)
    return {
        "ok": True,
        "source": str(path),
        "count": len(drafts),
        "drafts": drafts,
        "hitl": True,
    }


def get_outreach_tools() -> list:
    return [
        draft_supplier_outreach_email,
        gmail_compose_url,
        open_gmail_compose,
        draft_and_open_outreach,
        batch_outreach_from_locate,
    ]
