"""PromptWise AI Creative Studio integration for agency UGC.

PromptWise (https://www.promptwise.com / https://app.promptwise.com) is a
multi-model creative workspace with **UGC Factory**, Influencer Studio, Flows,
and Wise assistant. Public REST docs are not broadly published, so we support:

1. **Browser path (primary)** — drive app.promptwise.com via Hermes reverse
   bridge browser tools (session cookies / logged-in profile on the host).
2. **Brief builder (always)** — structured UGC briefs agents pass into PromptWise
   or Fal as a fallback.
3. **Optional HTTP API** — if PromptWise issues you a key later:
   ``PROMPTWISE_API_KEY`` + ``PROMPTWISE_API_BASE``.

Env:
  PROMPTWISE_APP_URL          default https://app.promptwise.com
  PROMPTWISE_UGC_PATH         default / (or /ugc if your workspace uses it)
  PROMPTWISE_API_KEY          optional
  PROMPTWISE_API_BASE         optional API root
  HERMES_BRIDGE_URL           default http://127.0.0.1:7790
  PROMPTWISE_BROWSER_ENABLED  1/0 (default 1)
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import httpx

from tools.envutil import env


def _app_url() -> str:
    return (env("PROMPTWISE_APP_URL") or "https://app.promptwise.com").rstrip("/")


def _bridge_url() -> str:
    return (env("HERMES_BRIDGE_URL") or "http://127.0.0.1:7790").rstrip("/")


def _api_configured() -> bool:
    return bool(env("PROMPTWISE_API_KEY") and env("PROMPTWISE_API_BASE"))


def promptwise_status() -> dict[str, Any]:
    """Report integration mode and readiness (never prints secrets)."""
    api = _api_configured()
    browser = env("PROMPTWISE_BROWSER_ENABLED", "1").lower() not in {"0", "false", "no"}
    bridge_ok = False
    try:
        r = httpx.get(f"{_bridge_url()}/health", timeout=4.0)
        bridge_ok = r.status_code == 200
    except Exception:
        bridge_ok = False

    mode = "api" if api else ("browser" if browser else "brief_only")
    return {
        "ok": True,
        "mode": mode,
        "app_url": _app_url(),
        "api_configured": api,
        "browser_enabled": browser,
        "hermes_bridge_reachable": bridge_ok,
        "ugc_factory": "PromptWise UGC Factory (UI) + agency brief builder",
        "fallback": "tools.fal_tools when PromptWise unavailable",
        "next": (
            "Log into PromptWise once in a browser profile the Hermes bridge can use, "
            "or set PROMPTWISE_API_KEY + PROMPTWISE_API_BASE if you have API access."
        ),
    }


def promptwise_build_ugc_brief(
    product_name: str,
    angle: str = "",
    hook: str = "",
    script: str = "",
    avatar_style: str = "casual authentic UGC creator, phone selfie energy",
    platform: str = "tiktok",
    duration_s: int = 20,
    cta: str = "Shop now — link in bio",
    brand_voice: str = "friendly, specific, no medical claims",
    product_image_url: str = "",
    price_usd: float | None = None,
) -> dict[str, Any]:
    """Build a structured UGC brief for PromptWise UGC Factory / Wise / Flows."""
    product_name = (product_name or "Product").strip()
    angle = (angle or "problem → demo → result").strip()
    hook = (hook or f"Stop scrolling if you work at a desk — {product_name}").strip()
    if not script:
        script = (
            f"{hook}\n\n"
            f"I tried {product_name} for a week. {angle}.\n"
            f"Here's the 10-second demo…\n"
            f"{cta}"
        )
    brief = {
        "product_name": product_name,
        "platform": platform,
        "duration_s": max(8, min(60, int(duration_s))),
        "avatar_style": avatar_style,
        "hook": hook,
        "angle": angle,
        "script": script.strip(),
        "cta": cta,
        "brand_voice": brand_voice,
        "product_image_url": product_image_url or None,
        "price_usd": price_usd,
        "promptwise": {
            "workspace": "UGC Factory",
            "suggested_models": ["Kling 3.0", "Seedance 2.0", "Nanobanana Pro"],
            "app_url": _app_url(),
            "wise_prompt": (
                f"Create a {duration_s}s {platform} UGC ad for {product_name}. "
                f"Avatar: {avatar_style}. Hook: {hook}. Script:\n{script}\n"
                f"Voice: {brand_voice}. CTA: {cta}. No medical claims."
            ),
        },
        "compliance": {
            "avoid": ["disease claims", "guaranteed results", "competitor trademarks"],
            "disclosures": ["#ad or paid partnership if required", "AI-generated disclosure if platform requires"],
        },
    }
    out_dir = Path("tmp/creatives/promptwise")
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"brief_{int(time.time())}.json"
    path.write_text(json.dumps(brief, indent=2) + "\n", encoding="utf-8")
    brief["artifact"] = str(path)
    return brief


def _bridge_browser(tool: str, **kwargs: Any) -> dict[str, Any]:
    """Call Hermes bridge browser helpers (in-process wrappers)."""
    try:
        from tools import hermes_bridge_tools as hbt

        if tool == "navigate":
            return hbt.hermes_browser_navigate(url=str(kwargs.get("url") or _app_url()))
        if tool == "snapshot":
            url = str(kwargs.get("url") or _app_url())
            return hbt.hermes_browser_snapshot(url=url)
        if tool == "screenshot":
            url = str(kwargs.get("url") or _app_url())
            return hbt.hermes_browser_screenshot(url=url, full_page=bool(kwargs.get("full_page", False)))
    except Exception as e:
        return {"ok": False, "error": f"bridge tools unavailable: {e}", "tool": tool}

    return {
        "ok": False,
        "error": f"no bridge handler for {tool}",
        "hint": "Ensure hermes-bridge is running on :7790 and hermes_bridge tools are attached",
    }


def promptwise_open_workspace(
    path: str = "",
    take_snapshot: bool = True,
) -> dict[str, Any]:
    """Open PromptWise in the Hermes bridge browser (requires logged-in session)."""
    if env("PROMPTWISE_BROWSER_ENABLED", "1").lower() in {"0", "false", "no"}:
        return {"ok": False, "error": "PROMPTWISE_BROWSER_ENABLED=0"}

    base = _app_url()
    rel = (path or env("PROMPTWISE_UGC_PATH") or "").strip()
    url = f"{base}{rel if rel.startswith('/') else '/' + rel}" if rel else base

    nav = _bridge_browser("navigate", url=url)
    out: dict[str, Any] = {"ok": bool(nav.get("ok", True)), "url": url, "navigate": nav}
    if take_snapshot:
        snap = _bridge_browser("snapshot")
        out["snapshot"] = {
            "ok": bool(snap.get("ok", True)),
            "title": snap.get("title"),
            "text_preview": (snap.get("text") or snap.get("content") or "")[:1200],
        }
    out["operator_note"] = (
        "If you see a login page, complete PromptWise login once in the bridge browser "
        "profile, then re-run. Prefer UGC Factory → paste wise_prompt from brief."
    )
    return out


def promptwise_run_ugc_job(
    product_name: str,
    angle: str = "",
    hook: str = "",
    script: str = "",
    open_browser: bool = True,
    use_api_if_available: bool = True,
) -> dict[str, Any]:
    """End-to-end UGC job: brief → optional API → browser open for generation.

    Does **not** auto-spend credits without a human in the loop when only
    browser UI is available — returns a run card for Creative Ops / HITL.
    """
    brief = promptwise_build_ugc_brief(
        product_name=product_name,
        angle=angle,
        hook=hook,
        script=script,
    )
    result: dict[str, Any] = {
        "ok": True,
        "brief": brief,
        "status": "brief_ready",
        "hitl": True,
        "message": "UGC brief ready — generate in PromptWise UGC Factory (credits spend).",
    }

    if use_api_if_available and _api_configured():
        api = _promptwise_api_generate(brief)
        result["api"] = api
        if api.get("ok"):
            result["status"] = "api_submitted"
            result["hitl"] = False
            return result

    if open_browser:
        browser = promptwise_open_workspace(take_snapshot=True)
        result["browser"] = browser
        result["status"] = "browser_opened" if browser.get("ok") else "brief_only"
        result["playbook"] = [
            "1. Confirm logged into PromptWise",
            "2. Open UGC Factory (or Flows canvas)",
            "3. Paste brief['promptwise']['wise_prompt'] into Wise / prompt bar",
            "4. Attach product image if product_image_url set",
            "5. Generate → download MP4 → store under tmp/creatives/promptwise/",
            "6. Dual-write Linear issue with asset path + spend note",
        ]
    return result


def _promptwise_api_generate(brief: dict[str, Any]) -> dict[str, Any]:
    """Best-effort HTTP call when PROMPTWISE_API_* is configured (shape may vary)."""
    base = env("PROMPTWISE_API_BASE").rstrip("/")
    key = env("PROMPTWISE_API_KEY")
    if not base or not key:
        return {"ok": False, "error": "api not configured"}

    # Conservative generic payload — adjust when official OpenAPI is available
    payload = {
        "type": "ugc",
        "prompt": (brief.get("promptwise") or {}).get("wise_prompt"),
        "product": brief.get("product_name"),
        "duration_s": brief.get("duration_s"),
        "platform": brief.get("platform"),
        "metadata": {"source": "ai-agency", "artifact": brief.get("artifact")},
    }
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "X-API-Key": key,
    }
    endpoints = [
        f"{base}/v1/generations",
        f"{base}/v1/ugc",
        f"{base}/generate",
        f"{base}/api/generate",
    ]
    last_err: Any = None
    for url in endpoints:
        try:
            with httpx.Client(timeout=60.0) as client:
                r = client.post(url, headers=headers, json=payload)
            if r.status_code < 300:
                return {"ok": True, "endpoint": url, "response": r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text[:2000]}
            last_err = {"status": r.status_code, "body": r.text[:400], "endpoint": url}
        except Exception as e:
            last_err = {"error": str(e), "endpoint": url}
    return {
        "ok": False,
        "error": "no PromptWise API endpoint accepted the payload",
        "last": last_err,
        "hint": "Confirm PROMPTWISE_API_BASE path with PromptWise support, or use browser mode",
    }


def get_promptwise_tools() -> list[Any]:
    return [
        promptwise_status,
        promptwise_build_ugc_brief,
        promptwise_open_workspace,
        promptwise_run_ugc_job,
    ]
