"""Agno-facing client tools that call the Hermes reverse bridge over HTTP/JSON-RPC MCP.

These are registered on agency agents so specialists can use browser, skills, and KIP
without running inside the Hermes process.
"""

from __future__ import annotations

import json
import os
import uuid
from typing import Any, Dict, Optional

import httpx

BRIDGE = (os.getenv("HERMES_BRIDGE_URL") or "http://127.0.0.1:7790/mcp").rstrip("/")
# base without /mcp for health
BRIDGE_BASE = BRIDGE[: -4] if BRIDGE.endswith("/mcp") else BRIDGE


class _MCPSession:
    def __init__(self) -> None:
        self.session_id: Optional[str] = None
        self._client = httpx.Client(timeout=120.0)

    def close(self) -> None:
        self._client.close()

    def _headers(self) -> dict:
        h = {
            "content-type": "application/json",
            "accept": "application/json, text/event-stream",
        }
        if self.session_id:
            h["mcp-session-id"] = self.session_id
        tok = os.getenv("HERMES_BRIDGE_TOKEN") or os.getenv("DROP_MCP_TOKEN")
        if tok:
            h["Authorization"] = f"Bearer {tok}"
        return h

    def ensure(self) -> None:
        if self.session_id:
            return
        r = self._client.post(
            BRIDGE,
            headers=self._headers(),
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "agno-agency", "version": "1"},
                },
            },
        )
        r.raise_for_status()
        self.session_id = r.headers.get("mcp-session-id") or r.headers.get("Mcp-Session-Id")
        # notifications/initialized
        try:
            self._client.post(
                BRIDGE,
                headers=self._headers(),
                json={"jsonrpc": "2.0", "method": "notifications/initialized"},
            )
        except Exception:
            pass

    def call_tool(self, name: str, arguments: Optional[dict] = None) -> Dict[str, Any]:
        self.ensure()
        r = self._client.post(
            BRIDGE,
            headers=self._headers(),
            json={
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "method": "tools/call",
                "params": {"name": name, "arguments": arguments or {}},
            },
        )
        if r.status_code >= 400:
            return {"error": f"HTTP {r.status_code}", "body": r.text[:1000]}
        text = r.text
        payload = None
        for line in text.splitlines():
            if line.startswith("data: "):
                payload = json.loads(line[6:])
                break
        if payload is None:
            try:
                payload = r.json()
            except Exception:
                return {"error": "bad response", "raw": text[:1000]}
        if "error" in payload:
            return {"error": payload["error"]}
        result = (payload.get("result") or {})
        # MCP tool result content blocks
        content = result.get("content") or result.get("structuredContent") or result
        if isinstance(content, list):
            texts = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    texts.append(block.get("text") or "")
                else:
                    texts.append(json.dumps(block))
            joined = "\n".join(texts)
            try:
                return json.loads(joined)
            except Exception:
                return {"result": joined}
        if isinstance(content, dict) and "result" in content:
            return content["result"] if isinstance(content["result"], dict) else content
        return content if isinstance(content, dict) else {"result": content}


_SESSION = _MCPSession()


def _call(tool_name: str, **kwargs) -> Dict[str, Any]:
    try:
        return _SESSION.call_tool(tool_name, kwargs)
    except Exception as e:
        return {"error": str(e), "hint": "Is hermes-bridge running on :7790?"}


# Thin wrappers — names match bridge tools for agent clarity


def hermes_browser_navigate(url: str, wait_until: str = "domcontentloaded", timeout_ms: int = 30000) -> Dict[str, Any]:
    """Browse a URL via Hermes reverse bridge (Playwright)."""
    return _call("hermes_browser_navigate", url=url, wait_until=wait_until, timeout_ms=timeout_ms)


def hermes_browser_snapshot(url: str, selector: str = "body") -> Dict[str, Any]:
    """Snapshot page text/html via Hermes bridge."""
    return _call("hermes_browser_snapshot", url=url, selector=selector)


def hermes_browser_screenshot(url: str, full_page: bool = False) -> Dict[str, Any]:
    """Screenshot URL via Hermes bridge."""
    return _call("hermes_browser_screenshot", url=url, full_page=full_page)


def hermes_browser_extract_links(url: str, limit: int = 40) -> Dict[str, Any]:
    return _call("hermes_browser_extract_links", url=url, limit=limit)


def hermes_skill_list(limit: int = 50, query: str = "") -> Dict[str, Any]:
    """List Hermes self-improving skills available on disk."""
    return _call("hermes_skill_list", limit=limit, query=query)


def hermes_skill_read(name: str) -> Dict[str, Any]:
    """Read a Hermes skill playbook."""
    return _call("hermes_skill_read", name=name)


def hermes_skill_search(query: str, limit: int = 20) -> Dict[str, Any]:
    return _call("hermes_skill_search", query=query, limit=limit)


def hermes_skill_propose(name: str, rationale: str, patch_markdown: str, skill_name: str = "") -> Dict[str, Any]:
    """Propose a skill improvement for Hermes curator (self-improving loop)."""
    return _call(
        "hermes_skill_propose",
        name=name,
        rationale=rationale,
        patch_markdown=patch_markdown,
        skill_name=skill_name or name,
    )


def hermes_memory_read(which: str = "memory") -> Dict[str, Any]:
    return _call("hermes_memory_read", which=which)


def hermes_memory_append(entry: str, which: str = "memory") -> Dict[str, Any]:
    return _call("hermes_memory_append", entry=entry, which=which)


def kip_remember(text: str, kind: str = "Insight", name: str = "", link: str = "") -> Dict[str, Any]:
    """Store shared fact in KIP Cognitive Nexus (Anda/KIP; ICP-exportable)."""
    return _call("kip_remember", text=text, kind=kind, name=name, link=link)


def kip_recall(query: str, limit: int = 15) -> Dict[str, Any]:
    """Recall from shared KIP graph memory."""
    return _call("kip_recall", query=query, limit=limit)


def kip_execute(command: str) -> Dict[str, Any]:
    """Raw KIP command (FIND/UPSERT/DESCRIBE PRIMER/EXPORT)."""
    return _call("kip_execute", command=command)


def kip_export_icp(label: str = "agency") -> Dict[str, Any]:
    """Export KIP capsule + ICP receipt/sync."""
    return _call("kip_export_icp", label=label)


def hermes_computer_use_request(goal: str, app: str = "", notes: str = "") -> Dict[str, Any]:
    """Request Hermes top-orchestrator computer-use job (desktop CUA)."""
    return _call("hermes_computer_use_request", goal=goal, app=app, notes=notes)


def hermes_computer_use_list_jobs(status: str = "pending") -> Dict[str, Any]:
    return _call("hermes_computer_use_list_jobs", status=status)




def anda_brain_formation(text: str, counterparty: str = "", agent: str = "agency") -> Dict[str, Any]:
    """Encode conversation into KIP via bridge."""
    return _call("anda_brain_formation", text=text, counterparty=counterparty, agent=agent)


def anda_brain_recall(query: str, limit: int = 15) -> Dict[str, Any]:
    return _call("anda_brain_recall", query=query, limit=limit)


def anda_brain_sleep() -> Dict[str, Any]:
    return _call("anda_brain_sleep")


def anda_brain_bootstrap() -> Dict[str, Any]:
    return _call("anda_brain_bootstrap")

def get_hermes_bridge_tools() -> list:
    return [
        hermes_browser_navigate,
        hermes_browser_snapshot,
        hermes_browser_screenshot,
        hermes_browser_extract_links,
        hermes_skill_list,
        hermes_skill_read,
        hermes_skill_search,
        hermes_skill_propose,
        hermes_memory_read,
        hermes_memory_append,
        kip_remember,
        kip_recall,
        kip_execute,
        kip_export_icp,
        anda_brain_formation,
        anda_brain_recall,
        anda_brain_sleep,
        anda_brain_bootstrap,
        hermes_computer_use_request,
        hermes_computer_use_list_jobs,
    ]
