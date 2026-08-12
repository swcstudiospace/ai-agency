"""Custom MCP tools exposed on AgentOS /mcp for Hermes control plane.

These complement the 8 built-in AgentOS MCP tools (run_agent/team/workflow, etc.).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from agno.tools import tool

_ROOT = Path(__file__).resolve().parents[1]
_RUNS = _ROOT / "tmp" / "runs"
_LOGS = _ROOT / "logs"


def _utc() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


@tool(
    name="agency_health",
    description=(
        "Check AI Dropshipping Agency runtime health: process paths, latest product-rank "
        "artifacts, and whether Parallel/xAI env looks configured (never returns secrets)."
    ),
)
def agency_health() -> dict[str, Any]:
    _RUNS.mkdir(parents=True, exist_ok=True)
    reports = sorted(_RUNS.glob("product_rank_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return {
        "ok": True,
        "ts": _utc(),
        "root": str(_ROOT),
        "parallel_key_set": bool((os.getenv("PARALLEL_API_KEY") or "").strip()),
        "xai_api_key_set": bool((os.getenv("XAI_API_KEY") or "").strip()),
        "latest_product_rank": str(reports[0].name) if reports else None,
        "product_rank_count": len(reports),
        "agentos_id": "ai-dropshipping-agency",
        "mcp_path": "/mcp",
    }


@tool(
    name="agency_roster",
    description=(
        "Return the fixed roster of agent_id / team_id / workflow_id values Hermes should "
        "pass to run_agent, run_team, and run_workflow. Prefer this for quick routing; "
        "use get_agentos_config for live discovery."
    ),
)
def agency_roster() -> dict[str, Any]:
    return {
        "os_id": "ai-dropshipping-agency",
        "agents": {
            "orchestrator": "hermes-ops",
            "research": ["product-scout", "supplier-sourcer", "pricing-strategist"],
            "creative": ["brand-strategist", "creative-director", "listing-specialist", "seo-content"],
            "store": ["store-builder", "compliance-officer"],
            "growth": ["growth-media-buyer", "influencer-manager"],
            "retention": ["email-crm", "customer-success"],
            "ops": ["fulfillment-ops", "inventory-planner"],
            "finance": ["analyst", "finance-controller"],
        },
        "teams": {
            "director": "agency-director-team",
            "research": "research-team",
            "supply_chain": "supply-chain-team",
            "creative": "creative-team",
            "store_ops": "store-ops-team",
            "growth": "growth-team",
            "retention": "retention-team",
        },
        "workflows": {
            "full_lifecycle": "full-product-lifecycle",
            "marketing_launch": "marketing-launch",
            "supplier_onboarding": "supplier-onboarding",
            "post_purchase": "post-purchase-ops",
            "weekly_review": "weekly-performance-review",
        },
        "routing_hints": {
            "new_product": "workflow:full-product-lifecycle OR team:research-team then creative-team",
            "product_find_rank": "custom tool run_product_rank (Parallel ultra) then team:research-team",
            "paid_launch": "workflow:marketing-launch",
            "supplier": "workflow:supplier-onboarding",
            "weekly": "workflow:weekly-performance-review",
        },
    }


@tool(
    name="list_product_rank_reports",
    description="List autonomous product-rank JSON/MD reports under tmp/runs (newest first).",
)
def list_product_rank_reports(limit: int = 10) -> dict[str, Any]:
    _RUNS.mkdir(parents=True, exist_ok=True)
    files = sorted(_RUNS.glob("product_rank_*.*"), key=lambda p: p.stat().st_mtime, reverse=True)
    out = []
    for p in files[: max(1, min(limit, 50))]:
        st = p.stat()
        out.append(
            {
                "name": p.name,
                "path": str(p),
                "bytes": st.st_size,
                "mtime": datetime.fromtimestamp(st.st_mtime, tz=UTC).isoformat(),
            }
        )
    return {"reports": out, "count": len(out)}


@tool(
    name="read_product_rank_report",
    description=(
        "Read a product-rank report. Pass filename (e.g. product_rank_….md) or 'latest'. "
        "format: 'md' | 'json' | 'summary'."
    ),
)
def read_product_rank_report(name: str = "latest", format: str = "summary") -> dict[str, Any]:
    _RUNS.mkdir(parents=True, exist_ok=True)
    fmt = (format or "summary").lower()
    if name in {"", "latest", "latest.md", "latest.json"}:
        suffix = ".json" if fmt == "json" else ".md"
        matches = sorted(_RUNS.glob(f"product_rank_*{suffix}"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not matches and fmt == "summary":
            matches = sorted(_RUNS.glob("product_rank_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not matches:
            return {"error": "no product_rank reports found", "dir": str(_RUNS)}
        path = matches[0]
    else:
        path = _RUNS / Path(name).name
        if not path.is_file():
            return {"error": f"not found: {path.name}", "dir": str(_RUNS)}

    text = path.read_text(encoding="utf-8", errors="replace")
    if fmt == "summary" and path.suffix == ".json":
        data = json.loads(text)
        ranked = data.get("ranked_candidates") or []
        top = []
        for c in ranked[:8]:
            econ = c.get("economics") or {}
            top.append(
                {
                    "decision": c.get("decision"),
                    "score": c.get("composite_score"),
                    "name": c.get("name"),
                    "price": c.get("suggested_price_usd"),
                    "cm_pct": econ.get("contribution_margin_pct"),
                }
            )
        return {
            "path": str(path),
            "meta": data.get("meta"),
            "market_summary": (data.get("market_summary") or "")[:1200],
            "top": top,
            "research_team_excerpt": (data.get("research_team_synthesis") or "")[:2500],
        }
    # Cap large dumps for LLM context
    max_chars = 24000 if fmt != "json" else 40000
    return {
        "path": str(path),
        "format": fmt,
        "content": text if len(text) <= max_chars else text[:max_chars] + "\n…[truncated]…",
        "truncated": len(text) > max_chars,
        "bytes": len(text),
    }


@tool(
    name="run_product_rank",
    description=(
        "Run the autonomous product find+rank pipeline (Parallel Search + Task deep research + "
        "unit-economics scoring + optional Research Team). processor: lite|base|core|pro|ultra. "
        "ultra is preferred for serious research and can take many minutes — Hermes MCP timeout "
        "for this server should be ≥ 3600s. Returns paths to JSON/MD reports."
    ),
)
def run_product_rank(
    niche: str,
    processor: str = "ultra",
    skip_team: bool = False,
    default_cpa: float = 18.0,
    timeout_s: float = 3600.0,
) -> dict[str, Any]:
    niche = (niche or "").strip()
    if not niche:
        return {"error": "niche is required"}
    proc = (processor or "ultra").lower().strip()
    if proc not in {"lite", "base", "core", "pro", "ultra"}:
        return {"error": f"invalid processor: {processor}"}

    _RUNS.mkdir(parents=True, exist_ok=True)
    _LOGS.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    log_path = _LOGS / f"product_rank_mcp_{stamp}.log"

    cmd = [
        sys.executable,
        "-u",
        "-m",
        "scripts.autonomous_product_rank",
        "--niche",
        niche,
        "--processor",
        proc,
        "--timeout",
        str(int(timeout_s)),
        "--default-cpa",
        str(default_cpa),
    ]
    if skip_team:
        cmd.append("--skip-team")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(_ROOT) + os.pathsep + env.get("PYTHONPATH", "")

    before = {p.name for p in _RUNS.glob("product_rank_*.json")}
    try:
        with log_path.open("w", encoding="utf-8") as logf:
            completed = subprocess.run(
                cmd,
                cwd=str(_ROOT),
                env=env,
                stdout=logf,
                stderr=subprocess.STDOUT,
                timeout=max(60.0, float(timeout_s) + 120.0),
                check=False,
            )
    except subprocess.TimeoutExpired:
        return {
            "error": "product rank timed out",
            "log": str(log_path),
            "hint": "Increase timeout_s / Hermes mcp timeout; check Parallel ultra run status",
        }
    except Exception as e:
        return {"error": str(e), "log": str(log_path)}

    after = sorted(
        [p for p in _RUNS.glob("product_rank_*.json") if p.name not in before],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    latest = after[0] if after else None
    if latest is None:
        # fallback to newest overall
        all_json = sorted(_RUNS.glob("product_rank_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        latest = all_json[0] if all_json else None

    md = latest.with_suffix(".md") if latest else None
    summary: dict[str, Any] = {
        "exit_code": completed.returncode,
        "log": str(log_path),
        "json_report": str(latest) if latest else None,
        "md_report": str(md) if md and md.is_file() else None,
        "niche": niche,
        "processor": proc,
    }
    if latest and latest.is_file():
        try:
            data = json.loads(latest.read_text(encoding="utf-8"))
            ranked = data.get("ranked_candidates") or []
            summary["meta"] = data.get("meta")
            summary["top3"] = [
                {
                    "decision": c.get("decision"),
                    "score": c.get("composite_score"),
                    "name": c.get("name"),
                    "price": c.get("suggested_price_usd"),
                }
                for c in ranked[:3]
            ]
        except Exception as e:
            summary["parse_warning"] = str(e)
    if completed.returncode != 0:
        # include tail of log
        try:
            tail = log_path.read_text(encoding="utf-8", errors="replace")[-3000:]
            summary["log_tail"] = tail
        except OSError:
            pass
    return summary


@tool(
    name="agency_integrations_status",
    description=(
        "Check Linear / Shopify / Meta / TikTok / Fal / spend-vault configuration "
        "(no secrets). Use before autonomous lifecycle or ad launch."
    ),
)
def agency_integrations_status() -> dict[str, Any]:
    from tools.fal_tools import list_fal_avatars
    from tools.linear_tools import linear_status
    from tools.meta_ads_tools import meta_status
    from tools.shopify_tools import shopify_status
    from tools.spend_vault import list_funding_sources, list_spend_approvals
    from tools.tiktok_ads_tools import tiktok_status

    return {
        "ts": _utc(),
        "linear": linear_status(),
        "shopify": shopify_status(),
        "meta": meta_status(),
        "tiktok": tiktok_status(),
        "fal": list_fal_avatars(),
        "funding_sources": list_funding_sources(),
        "pending_spend_approvals": list_spend_approvals(status="pending"),
    }


@tool(
    name="run_autonomous_lifecycle",
    description=(
        "Run end-to-end autonomous dropshipping lifecycle for a niche: Parallel research, "
        "score products, dual-write Linear issues, supplier+logistics notes, UGC briefs "
        "(optional Fal render), Shopify drafts, Meta/TikTok DRAFT campaigns, and HITL "
        "spend approval requests. Never pays or goes live without human confirm. "
        "processor=ultra recommended; can take many minutes."
    ),
)
def run_autonomous_lifecycle(
    niche: str,
    processor: str = "ultra",
    top: int = 3,
    default_cpa: float = 18.0,
    timeout_s: float = 3600.0,
    render_ugc: bool = False,
) -> dict[str, Any]:
    niche = (niche or "").strip()
    if not niche:
        return {"error": "niche is required"}
    proc = (processor or "ultra").lower().strip()
    _RUNS.mkdir(parents=True, exist_ok=True)
    _LOGS.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    log_path = _LOGS / f"lifecycle_mcp_{stamp}.log"
    cmd = [
        sys.executable,
        "-u",
        "-m",
        "scripts.autonomous_lifecycle",
        "--niche",
        niche,
        "--processor",
        proc,
        "--top",
        str(max(1, min(int(top), 8))),
        "--cpa",
        str(default_cpa),
        "--timeout",
        str(int(timeout_s)),
    ]
    if render_ugc:
        cmd.append("--render-ugc")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    before = {p.name for p in _RUNS.glob("lifecycle_*.json") if "_HITL" not in p.name}
    try:
        with log_path.open("w", encoding="utf-8") as logf:
            completed = subprocess.run(
                cmd,
                cwd=str(_ROOT),
                env=env,
                stdout=logf,
                stderr=subprocess.STDOUT,
                timeout=max(120.0, float(timeout_s) + 180.0),
                check=False,
            )
    except subprocess.TimeoutExpired:
        return {"error": "lifecycle timed out", "log": str(log_path)}
    except Exception as e:
        return {"error": str(e), "log": str(log_path)}

    after = sorted(
        [p for p in _RUNS.glob("lifecycle_*.json") if p.name not in before and "_HITL" not in p.name],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    latest = after[0] if after else None
    if latest is None:
        allj = sorted(
            [p for p in _RUNS.glob("lifecycle_*.json") if "_HITL" not in p.name],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        latest = allj[0] if allj else None
    md = latest.with_suffix(".md") if latest else None
    hitl = Path(str(latest).replace(".json", "_HITL_CODES.json")) if latest else None
    out: dict[str, Any] = {
        "exit_code": completed.returncode,
        "log": str(log_path),
        "json_report": str(latest) if latest else None,
        "md_report": str(md) if md and md.is_file() else None,
        "hitl_codes_path": str(hitl) if hitl and hitl.is_file() else None,
        "niche": niche,
        "processor": proc,
        "note": "HITL codes are mode-600 on disk; do not auto-confirm spend.",
    }
    if latest and latest.is_file():
        try:
            data = json.loads(latest.read_text(encoding="utf-8"))
            out["root_linear"] = data.get("root_linear")
            out["products"] = [
                {
                    "name": p.get("product"),
                    "decision": p.get("decision"),
                    "score": p.get("score"),
                    "spend_approval_id": (p.get("spend_approval") or {}).get("approval_id"),
                    "meta_draft": (p.get("ads") or {}).get("meta", {}).get("id"),
                    "tiktok_draft": (p.get("ads") or {}).get("tiktok", {}).get("id"),
                }
                for p in (data.get("products") or [])
            ]
            out["human_next_steps"] = data.get("human_next_steps")
        except Exception as e:
            out["parse_warning"] = str(e)
    if completed.returncode != 0:
        try:
            out["log_tail"] = log_path.read_text(encoding="utf-8", errors="replace")[-4000:]
        except OSError:
            pass
    return out


@tool(
    name="request_ad_spend_approval",
    description=(
        "Create a HITL spend approval for Meta/TikTok. Returns approval_id and a one-time "
        "human_confirm_code. Agents must NOT call confirm — surface code to the human operator."
    ),
)
def request_ad_spend_approval(
    amount_usd: float,
    channel: str,
    purpose: str,
    campaign_draft_id: str = "",
    daily_budget_usd: float = 0.0,
    funding_source_id: str = "",
) -> dict[str, Any]:
    from tools.spend_vault import request_spend_approval

    return request_spend_approval(
        amount_usd=float(amount_usd),
        channel=channel,
        purpose=purpose,
        campaign_draft_id=campaign_draft_id,
        daily_budget_usd=float(daily_budget_usd or 0),
        funding_source_id=funding_source_id or "",
    )


@tool(
    name="attach_agency_funding_source",
    description=(
        "Register a bank (institution+last4) or crypto (chain+address) funding source metadata "
        "for HITL ad spend. Never send private keys or full account numbers."
    ),
)
def attach_agency_funding_source(
    kind: str,
    label: str,
    last4: str = "",
    institution: str = "",
    chain: str = "",
    address: str = "",
    daily_cap_usd: float = 100.0,
) -> dict[str, Any]:
    from tools.spend_vault import attach_funding_source

    return attach_funding_source(
        kind=kind,
        label=label,
        last4=last4,
        institution=institution,
        chain=chain,
        address=address,
        daily_cap_usd=float(daily_cap_usd),
    )


def get_mcp_custom_tools() -> list[Any]:
    return [
        agency_health,
        agency_roster,
        agency_integrations_status,
        list_product_rank_reports,
        read_product_rank_report,
        run_product_rank,
        run_autonomous_lifecycle,
        request_ad_spend_approval,
        attach_agency_funding_source,
    ]
