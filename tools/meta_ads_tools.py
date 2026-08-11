"""Meta Marketing API tools — draft freely; LIVE requires HITL spend approval.

Uses Graph API when META_ACCESS_TOKEN + META_AD_ACCOUNT_ID are set.
"""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

from tools.envutil import env
from tools.spend_vault import verify_spend_token

GRAPH = env("META_GRAPH_VERSION", "v21.0")
BASE = f"https://graph.facebook.com/{GRAPH}"
_DRAFTS = Path(__file__).resolve().parents[1] / "tmp" / "ad_drafts"


def _token() -> str:
    return env("META_ACCESS_TOKEN") or env("FB_ACCESS_TOKEN")


def _account() -> str:
    act = env("META_AD_ACCOUNT_ID") or env("FB_AD_ACCOUNT_ID")
    if act and not act.startswith("act_"):
        act = f"act_{act}"
    return act


def meta_status() -> Dict[str, Any]:
    tok, act = _token(), _account()
    if not tok or not act:
        return {"ok": False, "mode": "stub", "reason": "META_ACCESS_TOKEN or META_AD_ACCOUNT_ID missing"}
    try:
        with httpx.Client(timeout=30.0) as client:
            r = client.get(f"{BASE}/{act}", params={"access_token": tok, "fields": "name,account_status,currency,timezone_name"})
            data = r.json()
        if "error" in data:
            return {"ok": False, "mode": "error", "error": data["error"]}
        return {"ok": True, "mode": "live", "account": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def meta_list_campaigns(limit: int = 10) -> Dict[str, Any]:
    tok, act = _token(), _account()
    if not tok or not act:
        return {"campaigns": [], "stub": True}
    with httpx.Client(timeout=45.0) as client:
        r = client.get(
            f"{BASE}/{act}/campaigns",
            params={
                "access_token": tok,
                "fields": "id,name,status,objective,daily_budget,lifetime_budget,updated_time",
                "limit": max(1, min(50, limit)),
            },
        )
        return r.json()


def meta_draft_campaign(
    name: str,
    objective: str = "OUTCOME_SALES",
    daily_budget_usd: float = 20.0,
    countries: Optional[List[str]] = None,
    pixel_id: str = "",
    landing_url: str = "",
    creative_message: str = "",
    video_url: str = "",
) -> Dict[str, Any]:
    """Create a local DRAFT campaign plan (and optional PAUSED remote objects if live)."""
    draft_id = f"meta_draft_{uuid.uuid4().hex[:10]}"
    countries = countries or ["US"]
    # Meta budgets often in cents
    daily_cents = int(round(float(daily_budget_usd) * 100))
    draft = {
        "id": draft_id,
        "platform": "meta",
        "status": "DRAFT",
        "name": name,
        "objective": objective,
        "daily_budget_usd": daily_budget_usd,
        "daily_budget_cents": daily_cents,
        "countries": countries,
        "pixel_id": pixel_id or env("META_PIXEL_ID"),
        "landing_url": landing_url,
        "creative_message": creative_message,
        "video_url": video_url,
        "created_at": time.time(),
        "remote": None,
    }
    tok, act = _token(), _account()
    if tok and act and env("META_AUTO_CREATE_PAUSED").lower() in {"1", "true", "yes"}:
        # Create PAUSED campaign only — still not spend until activated with approval
        try:
            with httpx.Client(timeout=60.0) as client:
                cr = client.post(
                    f"{BASE}/{act}/campaigns",
                    data={
                        "access_token": tok,
                        "name": name,
                        "objective": objective,
                        "status": "PAUSED",
                        "special_ad_categories": "[]",
                    },
                )
                draft["remote"] = cr.json()
        except Exception as e:
            draft["remote_error"] = str(e)
    _DRAFTS.mkdir(parents=True, exist_ok=True)
    path = _DRAFTS / f"{draft_id}.json"
    path.write_text(json.dumps(draft, indent=2))
    draft["path"] = str(path)
    return draft


def meta_launch_campaign(
    draft_id: str,
    approval_id: str,
    spend_token: str,
) -> Dict[str, Any]:
    """Activate a draft/paused campaign ONLY with confirmed HITL spend approval."""
    path = _DRAFTS / f"{draft_id}.json"
    if not path.is_file():
        # allow passing path
        path = Path(draft_id)
    if not path.is_file():
        return {"error": f"draft not found: {draft_id}"}
    draft = json.loads(path.read_text())
    amount = float(draft.get("daily_budget_usd") or 0)
    gate = verify_spend_token(approval_id, spend_token, amount_usd=amount, channel="meta")
    if not gate.get("ok"):
        return {"error": "spend approval failed", "gate": gate}

    tok, act = _token(), _account()
    if not tok or not act:
        draft["status"] = "APPROVED_STUB_LIVE"
        draft["approval_id"] = approval_id
        path.write_text(json.dumps(draft, indent=2))
        return {
            "ok": True,
            "stub": True,
            "message": "Spend approved but Meta credentials missing — draft marked APPROVED_STUB_LIVE",
            "draft": draft,
            "gate": gate,
        }

    remote = draft.get("remote") or {}
    campaign_id = (remote.get("id") if isinstance(remote, dict) else None) or draft.get("remote_campaign_id")
    if not campaign_id:
        # create paused then activate
        with httpx.Client(timeout=60.0) as client:
            cr = client.post(
                f"{BASE}/{act}/campaigns",
                data={
                    "access_token": tok,
                    "name": draft.get("name"),
                    "objective": draft.get("objective") or "OUTCOME_SALES",
                    "status": "PAUSED",
                    "special_ad_categories": "[]",
                },
            )
            created = cr.json()
            campaign_id = created.get("id")
            draft["remote"] = created
            if not campaign_id:
                return {"error": "failed to create campaign", "remote": created}

    # Set daily budget on campaign if supported; many setups budget at ad set level.
    with httpx.Client(timeout=60.0) as client:
        up = client.post(
            f"{BASE}/{campaign_id}",
            data={"access_token": tok, "status": "ACTIVE"},
        )
        result = up.json()
    draft["status"] = "LIVE" if "error" not in result else "ERROR"
    draft["launch_result"] = result
    draft["approval_id"] = approval_id
    path.write_text(json.dumps(draft, indent=2))

    try:
        from tools.linear_tools import agency_track

        agency_track(
            title=f"Meta LIVE {draft.get('name')} ${amount}/day",
            description=f"draft={draft_id}\napproval={approval_id}\nresult={json.dumps(result)[:1500]}",
            stage="growth",
            priority=2,
        )
    except Exception:
        pass

    return {"ok": "error" not in result, "campaign_id": campaign_id, "result": result, "draft": draft, "gate": gate}


def meta_pause_campaign(campaign_id: str) -> Dict[str, Any]:
    tok = _token()
    if not tok:
        return {"ok": True, "stub": True, "status": "PAUSED"}
    with httpx.Client(timeout=30.0) as client:
        r = client.post(f"{BASE}/{campaign_id}", data={"access_token": tok, "status": "PAUSED"})
        return r.json()


def meta_insights(object_id: str, date_preset: str = "last_7d") -> Dict[str, Any]:
    tok = _token()
    if not tok:
        return {"stub": True, "insights": []}
    with httpx.Client(timeout=45.0) as client:
        r = client.get(
            f"{BASE}/{object_id}/insights",
            params={
                "access_token": tok,
                "date_preset": date_preset,
                "fields": "impressions,clicks,spend,cpc,ctr,actions,purchase_roas,campaign_name",
            },
        )
        return r.json()


def get_meta_tools() -> list:
    return [
        meta_status,
        meta_list_campaigns,
        meta_draft_campaign,
        meta_launch_campaign,
        meta_pause_campaign,
        meta_insights,
    ]
