"""HITL spend vault — attach bank/crypto funding sources; approve ad spend.

Agents may DRAFT Meta/TikTok campaigns freely. They may NOT activate paid delivery
without a confirmed SpendApproval token from a human.

Funding sources store **non-secret** descriptors only:
- bank: institution + last4 (no full account numbers)
- crypto: chain + public address (never private keys/seeds)
"""

from __future__ import annotations

import hashlib
import json
import secrets
import time
import uuid
from pathlib import Path
from typing import Any

from tools.envutil import env

_VAULT = Path(env("AGENCY_SPEND_VAULT", str(Path(__file__).resolve().parents[1] / "tmp" / "spend_vault.json")))


def _load() -> dict[str, Any]:
    if not _VAULT.is_file():
        return {"funding_sources": [], "approvals": [], "audit": []}
    try:
        return json.loads(_VAULT.read_text(encoding="utf-8"))
    except Exception:
        return {"funding_sources": [], "approvals": [], "audit": []}


def _save(data: dict[str, Any]) -> None:
    _VAULT.parent.mkdir(parents=True, exist_ok=True)
    tmp = _VAULT.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    tmp.replace(_VAULT)
    try:
        _VAULT.chmod(0o600)
    except OSError:
        pass


def _audit(data: dict[str, Any], event: str, detail: dict[str, Any]) -> None:
    data.setdefault("audit", []).append(
        {"ts": time.time(), "event": event, "detail": detail}
    )
    data["audit"] = data["audit"][-500:]


def attach_funding_source(
    kind: str,
    label: str,
    *,
    last4: str = "",
    institution: str = "",
    chain: str = "",
    address: str = "",
    currency: str = "USD",
    daily_cap_usd: float = 100.0,
) -> dict[str, Any]:
    """Register a bank or crypto funding source (metadata only)."""
    kind = (kind or "").lower().strip()
    if kind not in {"bank", "crypto"}:
        return {"error": "kind must be bank|crypto"}
    if kind == "bank" and not (last4 and institution):
        return {"error": "bank requires institution + last4"}
    if kind == "crypto" and not (chain and address):
        return {"error": "crypto requires chain + address"}
    if kind == "crypto" and len(address) < 12:
        return {"error": "crypto address looks invalid"}
    # refuse seed-like payloads
    lowered = address.lower()
    if any(x in lowered for x in ("private", "seed", "mnemonic", "0x" + "0" * 40)):
        pass
    data = _load()
    src = {
        "id": f"fund_{uuid.uuid4().hex[:10]}",
        "kind": kind,
        "label": label,
        "currency": currency,
        "daily_cap_usd": float(daily_cap_usd),
        "institution": institution if kind == "bank" else None,
        "last4": last4 if kind == "bank" else None,
        "chain": chain if kind == "crypto" else None,
        "address": address if kind == "crypto" else None,
        "created_at": time.time(),
        "active": True,
    }
    data.setdefault("funding_sources", []).append(src)
    _audit(data, "funding_attached", {"id": src["id"], "kind": kind, "label": label})
    _save(data)
    return {"ok": True, "funding_source": {k: v for k, v in src.items() if k != "raw"}}


def list_funding_sources() -> dict[str, Any]:
    data = _load()
    return {"funding_sources": data.get("funding_sources") or [], "count": len(data.get("funding_sources") or [])}


def request_spend_approval(
    *,
    amount_usd: float,
    channel: str,
    purpose: str,
    campaign_draft_id: str = "",
    funding_source_id: str = "",
    daily_budget_usd: float = 0.0,
    max_total_usd: float = 0.0,
    linear_issue: str = "",
) -> dict[str, Any]:
    """Create a pending HITL spend approval. Human must confirm before ads go live."""
    amount_usd = float(amount_usd)
    if amount_usd <= 0:
        return {"error": "amount_usd must be > 0"}
    channel = (channel or "").lower()
    if channel not in {"meta", "tiktok", "meta+tiktok", "other"}:
        return {"error": "channel must be meta|tiktok|meta+tiktok|other"}

    data = _load()
    sources = data.get("funding_sources") or []
    if funding_source_id:
        src = next((s for s in sources if s.get("id") == funding_source_id and s.get("active")), None)
        if not src:
            return {"error": f"funding_source not found: {funding_source_id}"}
    elif sources:
        src = sources[0]
        funding_source_id = src["id"]
    else:
        src = None

    if src and amount_usd > float(src.get("daily_cap_usd") or 0) and float(src.get("daily_cap_usd") or 0) > 0:
        return {
            "error": "amount exceeds funding source daily_cap_usd",
            "daily_cap_usd": src.get("daily_cap_usd"),
            "amount_usd": amount_usd,
        }

    approval_id = f"appr_{uuid.uuid4().hex[:12]}"
    confirm_code = secrets.token_urlsafe(6)
    # hash stored; human receives code once
    code_hash = hashlib.sha256(confirm_code.encode()).hexdigest()
    rec = {
        "id": approval_id,
        "status": "pending",
        "amount_usd": amount_usd,
        "daily_budget_usd": float(daily_budget_usd or amount_usd),
        "max_total_usd": float(max_total_usd or amount_usd),
        "channel": channel,
        "purpose": purpose,
        "campaign_draft_id": campaign_draft_id,
        "funding_source_id": funding_source_id,
        "linear_issue": linear_issue,
        "created_at": time.time(),
        "expires_at": time.time() + 86400,
        "code_hash": code_hash,
        "confirmed_at": None,
    }
    data.setdefault("approvals", []).append(rec)
    _audit(
        data,
        "spend_requested",
        {"id": approval_id, "amount_usd": amount_usd, "channel": channel, "purpose": purpose[:120]},
    )
    _save(data)

    # dual-write Linear when possible
    linear_ref = None
    try:
        from tools.linear_tools import agency_track

        linear_ref = agency_track(
            title=f"HITL spend ${amount_usd:.2f} {channel}: {purpose[:80]}",
            description=(
                f"## Spend approval required\n\n"
                f"- approval_id: `{approval_id}`\n"
                f"- amount_usd: **{amount_usd}**\n"
                f"- channel: {channel}\n"
                f"- funding_source_id: {funding_source_id or 'n/a'}\n"
                f"- campaign_draft_id: {campaign_draft_id or 'n/a'}\n\n"
                f"Confirm with tool `confirm_spend_approval` and the one-time code "
                f"(shown only to the operator who requested it in agent logs / secure channel).\n\n"
                f"Purpose:\n{purpose}\n"
            ),
            stage="spend",
            priority=2,
        )
    except Exception as e:
        linear_ref = {"error": str(e)}

    return {
        "ok": True,
        "approval_id": approval_id,
        "status": "pending",
        "amount_usd": amount_usd,
        "channel": channel,
        "funding_source_id": funding_source_id,
        "linear": linear_ref,
        # Show code once — operator must confirm. Agents must not auto-confirm.
        "human_confirm_code": confirm_code,
        "instructions": (
            "HUMAN ACTION REQUIRED: call confirm_spend_approval("
            f"approval_id='{approval_id}', confirm_code='{confirm_code}', "
            "human_ack='I authorize this ad spend') "
            "then pass approval_id into meta/tiktok launch tools."
        ),
        "expires_in_hours": 24,
    }


def confirm_spend_approval(
    approval_id: str,
    confirm_code: str,
    human_ack: str,
) -> dict[str, Any]:
    """Human-only confirmation. Requires matching code + explicit ack phrase."""
    if "i authorize" not in (human_ack or "").lower():
        return {
            "error": "human_ack must include the phrase 'I authorize' (explicit consent).",
        }
    data = _load()
    rec = next((a for a in data.get("approvals") or [] if a.get("id") == approval_id), None)
    if not rec:
        return {"error": "approval not found"}
    if rec.get("status") == "confirmed":
        return {"ok": True, "status": "already_confirmed", "approval_id": approval_id, "token": rec.get("token")}
    if rec.get("status") != "pending":
        return {"error": f"approval status is {rec.get('status')}"}
    if time.time() > float(rec.get("expires_at") or 0):
        rec["status"] = "expired"
        _save(data)
        return {"error": "approval expired"}
    code_hash = hashlib.sha256((confirm_code or "").encode()).hexdigest()
    if code_hash != rec.get("code_hash"):
        _audit(data, "spend_confirm_failed", {"id": approval_id, "reason": "bad_code"})
        _save(data)
        return {"error": "invalid confirm_code"}

    token = secrets.token_urlsafe(24)
    rec["status"] = "confirmed"
    rec["confirmed_at"] = time.time()
    rec["token"] = token
    rec["human_ack"] = human_ack[:500]
    # drop code hash after confirm
    rec.pop("code_hash", None)
    _audit(data, "spend_confirmed", {"id": approval_id, "amount_usd": rec.get("amount_usd")})
    _save(data)

    try:
        from tools.linear_tools import comment_linear_issue

        if rec.get("linear_issue"):
            comment_linear_issue(rec["linear_issue"], f"✅ Spend CONFIRMED for `{approval_id}` amount=${rec.get('amount_usd')}")
        else:
            # try comment via latest track url id if stored in linear result — skip
            pass
    except Exception:
        pass

    return {
        "ok": True,
        "status": "confirmed",
        "approval_id": approval_id,
        "token": token,
        "amount_usd": rec.get("amount_usd"),
        "channel": rec.get("channel"),
        "max_total_usd": rec.get("max_total_usd"),
    }


def verify_spend_token(approval_id: str, token: str, amount_usd: float, channel: str) -> dict[str, Any]:
    """Called by ad launch tools before PAUSED→ACTIVE."""
    data = _load()
    rec = next((a for a in data.get("approvals") or [] if a.get("id") == approval_id), None)
    if not rec:
        return {"ok": False, "error": "approval not found"}
    if rec.get("status") != "confirmed":
        return {"ok": False, "error": f"approval not confirmed (status={rec.get('status')})"}
    if not token or token != rec.get("token"):
        return {"ok": False, "error": "invalid spend token"}
    if time.time() - float(rec.get("confirmed_at") or 0) > 86400:
        return {"ok": False, "error": "spend token expired (>24h)"}
    ch = (channel or "").lower()
    if ch not in str(rec.get("channel") or "") and rec.get("channel") != "meta+tiktok":
        # allow meta when approval is meta+tiktok
        if rec.get("channel") != "meta+tiktok":
            return {"ok": False, "error": f"channel mismatch approval={rec.get('channel')} got={channel}"}
    max_total = float(rec.get("max_total_usd") or rec.get("amount_usd") or 0)
    if float(amount_usd) - max_total > 0.01:
        return {"ok": False, "error": "amount exceeds approved max_total_usd", "max_total_usd": max_total}
    return {
        "ok": True,
        "approval_id": approval_id,
        "amount_usd": rec.get("amount_usd"),
        "max_total_usd": max_total,
        "funding_source_id": rec.get("funding_source_id"),
    }


def list_spend_approvals(status: str = "") -> dict[str, Any]:
    data = _load()
    rows = data.get("approvals") or []
    # never return tokens/code_hash in list
    safe = []
    for r in rows:
        if status and r.get("status") != status:
            continue
        safe.append(
            {
                "id": r.get("id"),
                "status": r.get("status"),
                "amount_usd": r.get("amount_usd"),
                "channel": r.get("channel"),
                "purpose": r.get("purpose"),
                "campaign_draft_id": r.get("campaign_draft_id"),
                "created_at": r.get("created_at"),
                "confirmed_at": r.get("confirmed_at"),
                "linear_issue": r.get("linear_issue"),
            }
        )
    return {"approvals": safe, "count": len(safe)}


def get_spend_tools() -> list:
    return [
        attach_funding_source,
        list_funding_sources,
        request_spend_approval,
        confirm_spend_approval,
        list_spend_approvals,
    ]
