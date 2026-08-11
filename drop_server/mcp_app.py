"""Drop universal MCP server — FastMCP tools + CoT×GoT auto-reason."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure ai-agency root on path
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from mcp.server.fastmcp import FastMCP

from drop_server.reasoning.cot_got import get_graph, list_graphs, reason_auto, run_reasoning

mcp = FastMCP(
    name="drop-autonogrammer",
    instructions=(
        "Universal Dropshipping Agency MCP for Autonogrammer. "
        "Use reason_cot_got for complex goals (auto-triggers on lifecycle/spend/product tasks). "
        "Linear dual-write via linear_* tools. Agency lifecycle via agency_* tools. "
        "Never confirm spend codes; surface HITL to humans."
    ),
)


def _call_agency_tool(tool_obj, **kwargs):
    """Invoke agno Function-wrapped tools or plain callables."""
    if callable(tool_obj) and not hasattr(tool_obj, "entrypoint"):
        return tool_obj(**kwargs)
    fn = getattr(tool_obj, "entrypoint", None)
    if fn is None:
        raise TypeError(f"cannot invoke tool {tool_obj!r}")
    return fn(**kwargs)


def _maybe_auto_reason(goal: str, context: Optional[dict] = None) -> Optional[dict]:
    """Attach auto CoT×GoT when heuristics fire."""
    try:
        r = reason_auto(goal, context=context)
        if r.get("triggered"):
            return {
                "graph_id": r.get("id"),
                "triggers": r.get("triggers"),
                "recommendation": r.get("recommendation"),
                "confidence": r.get("confidence"),
                "summary": r.get("summary"),
            }
    except Exception as e:
        return {"auto_reason_error": str(e)}
    return None


# ─── Reasoning ───────────────────────────────────────────────


@mcp.tool()
def reason_cot_got(
    goal: str,
    mode: str = "hybrid",
    force_auto: bool = True,
    context_json: str = "",
) -> Dict[str, Any]:
    """Run Chain-of-Thought × Graph-of-Thought reasoning for a goal.

    mode: cot | got | hybrid (default hybrid).
    Use before high-stakes product, spend, or lifecycle decisions.
    """
    ctx = None
    if context_json.strip():
        try:
            ctx = json.loads(context_json)
        except json.JSONDecodeError:
            ctx = {"raw": context_json[:2000]}
    graph = run_reasoning(goal, mode=mode, auto_triggered=bool(force_auto), context=ctx)
    return graph


@mcp.tool()
def get_reasoning_graph(graph_id: str) -> Dict[str, Any]:
    """Fetch a previously built CoT×GoT graph by id."""
    return get_graph(graph_id)


@mcp.tool()
def list_reasoning_graphs(limit: int = 20) -> Dict[str, Any]:
    """List recent reasoning graphs."""
    return list_graphs(limit=limit)


# ─── Health / roster ─────────────────────────────────────────


@mcp.tool()
def drop_health() -> Dict[str, Any]:
    """Health of the Drop universal MCP/ACP gateway and key integrations."""
    out: Dict[str, Any] = {
        "ok": True,
        "service": "drop-autonogrammer",
        "mcp_path": "/mcp",
        "acp_path": "/acp",
        "protocols": ["mcp-streamable-http", "acp-stdio", "acp-http-bridge"],
    }
    try:
        from tools.linear_tools import linear_status

        out["linear"] = linear_status()
    except Exception as e:
        out["linear"] = {"ok": False, "error": str(e)}
    try:
        from tools.spend_vault import list_funding_sources, list_spend_approvals

        out["funding"] = list_funding_sources()
        out["pending_approvals"] = list_spend_approvals(status="pending")
    except Exception as e:
        out["spend"] = {"error": str(e)}
    try:
        import httpx

        r = httpx.get("http://127.0.0.1:7777/health", timeout=3.0)
        out["agentos"] = {"ok": r.status_code == 200, "body": r.json() if r.status_code == 200 else r.text[:200]}
    except Exception as e:
        out["agentos"] = {"ok": False, "error": str(e)}
    try:
        import httpx

        r = httpx.get("http://127.0.0.1:7790/health", timeout=3.0)
        out["hermes_bridge"] = r.json() if r.status_code == 200 else {"ok": False, "status": r.status_code}
    except Exception as e:
        out["hermes_bridge"] = {"ok": False, "error": str(e)}
    try:
        from kip_memory.nexus import find_concepts

        out["kip"] = {"ok": True, "concepts_sample": len(find_concepts(limit=20)), "protocol": "KIP local+ICP capsules"}
    except Exception as e:
        out["kip"] = {"ok": False, "error": str(e)}
    return out


@mcp.tool()
def drop_roster() -> Dict[str, Any]:
    """Agency agent/team/workflow ids for routing."""
    return {
            return {
        "counts": {"agents": 30, "teams": 12, "workflows": [
            "full-product-lifecycle",
            "marketing-launch",
            "supplier-onboarding",
            "post-purchase-ops",
            "weekly-performance-review",
        ],
        "agentos_mcp": "http://127.0.0.1:7777/mcp",
        "drop_mcp": "https://drop.autonogrammer.ai/mcp",
    }


# ─── Linear (first-class) ────────────────────────────────────


@mcp.tool()
def linear_status() -> Dict[str, Any]:
    """Check Linear API connectivity (SPE team)."""
    from tools.linear_tools import linear_status as _ls

    return _ls()


@mcp.tool()
def linear_create_issue(
    title: str,
    description: str = "",
    stage: str = "ops",
    priority: int = 3,
) -> Dict[str, Any]:
    """Create a Linear issue with Kanban dual-write. stage: research|supply|creative|growth|spend|ops|retention."""
    from tools.linear_tools import agency_track

    auto = _maybe_auto_reason(f"Create Linear work: {title}\n{description}", {"stage": stage})
    issue = agency_track(title=title, description=description, stage=stage, priority=priority)
    if auto:
        issue["reasoning"] = auto
    return issue


@mcp.tool()
def linear_update_issue(issue_id: str, state: str = "", comment: str = "") -> Dict[str, Any]:
    """Update Linear issue state (unstarted|started|completed|...) and/or comment."""
    from tools.linear_tools import update_linear_issue

    return update_linear_issue(issue_id, state=state, comment=comment)


@mcp.tool()
def linear_list_issues(limit: int = 10, state_key: str = "") -> Dict[str, Any]:
    """List recent Linear issues for the configured team."""
    from tools.linear_tools import list_linear_issues

    return list_linear_issues(limit=limit, state_key=state_key)


@mcp.tool()
def linear_comment(issue_id: str, body: str) -> Dict[str, Any]:
    """Comment on a Linear issue (UUID or SPE-N)."""
    from tools.linear_tools import comment_linear_issue

    return comment_linear_issue(issue_id, body)


# ─── Agency lifecycle bridges ────────────────────────────────


@mcp.tool()
def agency_run_lifecycle(
    niche: str,
    processor: str = "ultra",
    top: int = 3,
    timeout_s: float = 3600.0,
    render_ugc: bool = False,
) -> Dict[str, Any]:
    """Run autonomous dropshipping lifecycle (no payments). Auto-runs CoT×GoT first."""
    from tools.mcp_custom import run_autonomous_lifecycle

    reasoning = run_reasoning(
        goal=f"Autonomous dropshipping lifecycle for niche: {niche}",
        mode="hybrid",
        auto_triggered=True,
        context={"processor": processor, "top": top},
    )
    try:
        result = _call_agency_tool(
            run_autonomous_lifecycle,
            niche=niche,
            processor=processor,
            top=top,
            timeout_s=timeout_s,
            render_ugc=render_ugc,
        )
    except Exception as e:
        result = {"error": str(e)}
    return {
        "reasoning": {
            "graph_id": reasoning.get("id"),
            "recommendation": reasoning.get("recommendation"),
        },
        "lifecycle": result,
    }


@mcp.tool()
def agency_product_rank(niche: str, processor: str = "ultra", skip_team: bool = False) -> Dict[str, Any]:
    """Run product find+rank pipeline with auto CoT×GoT framing."""
    from tools.mcp_custom import run_product_rank

    reasoning = run_reasoning(
        goal=f"Find and rank dropshipping products for: {niche}",
        mode="hybrid",
        auto_triggered=True,
    )
    try:
        result = _call_agency_tool(
            run_product_rank,
            niche=niche,
            processor=processor,
            skip_team=skip_team,
        )
    except Exception as e:
        result = {"error": str(e)}
    return {"reasoning": {"graph_id": reasoning.get("id")}, "rank": result}


@mcp.tool()
def agency_integrations_status() -> Dict[str, Any]:
    """Linear/Shopify/Meta/TikTok/Fal/spend readiness."""
    from tools.mcp_custom import agency_integrations_status as _s

    return _call_agency_tool(_s)


@mcp.tool()
def spend_request_approval(
    amount_usd: float,
    channel: str,
    purpose: str,
    campaign_draft_id: str = "",
    daily_budget_usd: float = 0.0,
) -> Dict[str, Any]:
    """Request HITL ad spend approval. Auto CoT×GoT on spend goals. Does NOT confirm."""
    from tools.spend_vault import request_spend_approval

    reasoning = run_reasoning(
        goal=f"Approve ad spend ${amount_usd} on {channel}: {purpose}",
        mode="hybrid",
        auto_triggered=True,
        context={"amount_usd": amount_usd, "channel": channel},
    )
    res = request_spend_approval(
        amount_usd=amount_usd,
        channel=channel,
        purpose=purpose,
        campaign_draft_id=campaign_draft_id,
        daily_budget_usd=daily_budget_usd,
    )
    res["reasoning"] = {"graph_id": reasoning.get("id"), "recommendation": reasoning.get("recommendation")}
    res["note"] = "Human must confirm_spend_approval offline; agents must not self-confirm."
    return res


@mcp.tool()
def attach_funding_source(
    kind: str,
    label: str,
    last4: str = "",
    institution: str = "",
    chain: str = "",
    address: str = "",
    daily_cap_usd: float = 100.0,
) -> Dict[str, Any]:
    """Attach bank (institution+last4) or crypto (chain+address) funding metadata."""
    from tools.spend_vault import attach_funding_source as _a

    return _a(
        kind=kind,
        label=label,
        last4=last4,
        institution=institution,
        chain=chain,
        address=address,
        daily_cap_usd=daily_cap_usd,
    )


# ─── Proxy helpers into AgentOS HTTP ─────────────────────────


@mcp.tool()
def agentos_run_agent(agent_id: str, message: str, session_id: str = "") -> Dict[str, Any]:
    """Call AgentOS built-in run_agent via local MCP HTTP (if AgentOS up)."""
    import httpx

    auto = _maybe_auto_reason(message, {"agent_id": agent_id})
    # Prefer REST agent run if available
    payload = {"message": message}
    if session_id:
        payload["session_id"] = session_id
    try:
        with httpx.Client(timeout=600.0) as client:
            # Agno AgentOS typical route
            r = client.post(f"http://127.0.0.1:7777/agents/{agent_id}/runs", json={"message": message})
            if r.status_code >= 400:
                r = client.post(
                    "http://127.0.0.1:7777/agents/runs",
                    json={"agent_id": agent_id, "message": message},
                )
            data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {"text": r.text[:4000]}
            return {"status_code": r.status_code, "data": data, "reasoning": auto}
    except Exception as e:
        return {"error": str(e), "reasoning": auto, "hint": "Is AgentOS running on :7777?"}


@mcp.tool()
def bridge_browser_navigate(url: str) -> Dict[str, Any]:
    """Proxy: browse URL via Hermes reverse bridge (:7790)."""
    from tools.hermes_bridge_tools import hermes_browser_navigate

    return hermes_browser_navigate(url=url)


@mcp.tool()
def bridge_skill_search(query: str, limit: int = 15) -> Dict[str, Any]:
    """Proxy: search Hermes self-improving skills."""
    from tools.hermes_bridge_tools import hermes_skill_search

    return hermes_skill_search(query=query, limit=limit)


@mcp.tool()
def bridge_kip_remember(text: str, kind: str = "Insight", name: str = "") -> Dict[str, Any]:
    """Proxy: store fact in shared KIP graph (Anda/ICP-ready)."""
    from tools.hermes_bridge_tools import kip_remember

    return kip_remember(text=text, kind=kind, name=name)


@mcp.tool()
def bridge_kip_recall(query: str, limit: int = 15) -> Dict[str, Any]:
    """Proxy: recall from shared KIP graph."""
    from tools.hermes_bridge_tools import kip_recall

    return kip_recall(query=query, limit=limit)


def get_mcp() -> FastMCP:
    return mcp
