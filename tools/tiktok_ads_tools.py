"""TikTok Marketing API tools — draft freely; LIVE requires HITL spend approval."""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

from tools.envutil import env
from tools.spend_vault import verify_spend_token

TT_BASE = env("TIKTOK_API_BASE", "https://business-api.tiktok.com/open_api/v1.3")
_DRAFTS = Path(__file__).resolve().parents[1] / "tmp" / "ad_drafts"


def _token() -> str:
    return env("TIKTOK_ACCESS_TOKEN")


def _advertiser() -> str:
    return env("TIKTOK_ADVERTISER_ID")


def tiktok_status() -> Dict[str, Any]:
    tok, adv = _token(), _advertiser()
    if not tok or not adv:
        return {"ok": False, "mode": "stub", "reason": "TIKTOK_ACCESS_TOKEN or TIKTOK_ADVERTISER_ID missing"}
    try:
        with httpx.Client(timeout=30.0) as client:
            r = client.get(
                f"{TT_BASE}/advertiser/info/",
                headers={"Access-Token": tok},
                params={"advertiser_ids": json.dumps([adv])},
            )
            return {"ok": r.status_code == 200, "mode": "live", "data": r.json()}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def tiktok_draft_campaign(
    name: str,
    objective_type: str = "CONVERSIONS",
    daily_budget_usd: float = 20.0,
    landing_url: str = "",
    video_url: str = "",
    ad_text: str = "",
) -> Dict[str, Any]:
    draft_id = f"tt_draft_{uuid.uuid4().hex[:10]}"
    # TikTok budgets often in account currency minor units; keep USD float + note
    draft = {
        "id": draft_id,
        "platform": "tiktok",
        "status": "DRAFT",
        "name": name,
        "objective_type": objective_type,
        "daily_budget_usd": float(daily_budget_usd),
        "landing_url": landing_url,
        "video_url": video_url,
        "ad_text": ad_text,
        "created_at": time.time(),
        "remote": None,
    }
    _DRAFTS.mkdir(parents=True, exist_ok=True)
    path = _DRAFTS / f"{draft_id}.json"
    path.write_text(json.dumps(draft, indent=2))
    draft["path"] = str(path)

    tok, adv = _token(), _advertiser()
    if tok and adv and env("TIKTOK_AUTO_CREATE_PAUSED").lower() in {"1", "true", "yes"}:
        try:
            # Budget in cents for many currencies — document as estimate
            budget_val = int(round(float(daily_budget_usd) * 100))
            with httpx.Client(timeout=60.0) as client:
                r = client.post(
                    f"{TT_BASE}/campaign/create/",
                    headers={"Access-Token": tok, "Content-Type": "application/json"},
                    json={
                        "advertiser_id": adv,
                        "campaign_name": name,
                        "objective_type": objective_type,
                        "budget_mode": "BUDGET_MODE_DAY",
                        "budget": budget_val,
                        "operation_status": "DISABLE",  # paused equivalent
                    },
                )
                draft["remote"] = r.json()
                path.write_text(json.dumps(draft, indent=2))
        except Exception as e:
            draft["remote_error"] = str(e)
            path.write_text(json.dumps(draft, indent=2))
    return draft


def tiktok_launch_campaign(
    draft_id: str,
    approval_id: str,
    spend_token: str,
) -> Dict[str, Any]:
    path = _DRAFTS / f"{draft_id}.json"
    if not path.is_file():
        path = Path(draft_id)
    if not path.is_file():
        return {"error": f"draft not found: {draft_id}"}
    draft = json.loads(path.read_text())
    amount = float(draft.get("daily_budget_usd") or 0)
    gate = verify_spend_token(approval_id, spend_token, amount_usd=amount, channel="tiktok")
    if not gate.get("ok"):
        return {"error": "spend approval failed", "gate": gate}

    tok, adv = _token(), _advertiser()
    if not tok or not adv:
        draft["status"] = "APPROVED_STUB_LIVE"
        draft["approval_id"] = approval_id
        path.write_text(json.dumps(draft, indent=2))
        return {
            "ok": True,
            "stub": True,
            "message": "Spend approved but TikTok credentials missing",
            "draft": draft,
            "gate": gate,
        }

    remote = draft.get("remote") or {}
    campaign_id = None
    if isinstance(remote, dict):
        data = remote.get("data") or remote
        campaign_id = data.get("campaign_id") or data.get("id")

    with httpx.Client(timeout=60.0) as client:
        if not campaign_id:
            budget_val = int(round(amount * 100))
            cr = client.post(
                f"{TT_BASE}/campaign/create/",
                headers={"Access-Token": tok, "Content-Type": "application/json"},
                json={
                    "advertiser_id": adv,
                    "campaign_name": draft.get("name"),
                    "objective_type": draft.get("objective_type") or "CONVERSIONS",
                    "budget_mode": "BUDGET_MODE_DAY",
                    "budget": budget_val,
                    "operation_status": "DISABLE",
                },
            )
            created = cr.json()
            draft["remote"] = created
            data = created.get("data") or {}
            campaign_id = data.get("campaign_id")
            if not campaign_id:
                return {"error": "create failed", "remote": created}

        up = client.post(
            f"{TT_BASE}/campaign/status/update/",
            headers={"Access-Token": tok, "Content-Type": "application/json"},
            json={
                "advertiser_id": adv,
                "campaign_ids": [campaign_id],
                "operation_status": "ENABLE",
            },
        )
        result = up.json()

    draft["status"] = "LIVE"
    draft["launch_result"] = result
    draft["approval_id"] = approval_id
    path.write_text(json.dumps(draft, indent=2))

    try:
        from tools.linear_tools import agency_track

        agency_track(
            title=f"TikTok LIVE {draft.get('name')} ${amount}/day",
            description=f"draft={draft_id}\napproval={approval_id}\n{json.dumps(result)[:1500]}",
            stage="growth",
            priority=2,
        )
    except Exception:
        pass

    return {"ok": True, "campaign_id": campaign_id, "result": result, "draft": draft, "gate": gate}


def tiktok_pause_campaign(campaign_id: str) -> Dict[str, Any]:
    tok, adv = _token(), _advertiser()
    if not tok or not adv:
        return {"ok": True, "stub": True, "status": "DISABLE"}
    with httpx.Client(timeout=30.0) as client:
        r = client.post(
            f"{TT_BASE}/campaign/status/update/",
            headers={"Access-Token": tok, "Content-Type": "application/json"},
            json={
                "advertiser_id": adv,
                "campaign_ids": [campaign_id],
                "operation_status": "DISABLE",
            },
        )
        return r.json()


def get_tiktok_tools() -> list:
    return [
        tiktok_status,
        tiktok_draft_campaign,
        tiktok_launch_campaign,
        tiktok_pause_campaign,
    ]
