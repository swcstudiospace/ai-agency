"""ACP (Agent Client Protocol) agent for Drop — stdio + shared tool surface.

Editors (Zed/VS Code/JetBrains via Hermes ACP) and our HTTP bridge use this agent.
Complex prompts auto-trigger CoT×GoT before answering.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, List

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from acp import Agent, PromptResponse, run_agent
from acp.schema import InitializeResponse, NewSessionResponse

from drop_server.reasoning.cot_got import reason_auto, run_reasoning


def _prompt_text(prompt: Any) -> str:
    """Flatten ACP prompt content blocks to plain text."""
    if isinstance(prompt, str):
        return prompt
    parts: List[str] = []
    if isinstance(prompt, list):
        for block in prompt:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    parts.append(str(block.get("text") or ""))
                elif "text" in block:
                    parts.append(str(block.get("text") or ""))
            else:
                t = getattr(block, "text", None)
                if t:
                    parts.append(str(t))
                else:
                    parts.append(str(block))
    else:
        parts.append(str(prompt))
    return "\n".join(p for p in parts if p).strip()


class DropACPAgent(Agent):
    """Dropshipping agency ACP agent with CoT×GoT + Linear-aware guidance."""

    def __init__(self) -> None:
        super().__init__()
        self._sessions: dict[str, dict] = {}

    async def initialize(self, **kwargs: Any) -> InitializeResponse:
        try:
            return await super().initialize(**kwargs)
        except Exception:
            pv = kwargs.get("protocol_version") or kwargs.get("protocolVersion") or 1
            try:
                return InitializeResponse(protocol_version=pv, agent_capabilities={})
            except TypeError:
                return InitializeResponse(protocolVersion=pv)  # type: ignore[call-arg]

    async def new_session(self, cwd: str | None = None, mcp_servers: list | None = None, **kwargs: Any) -> NewSessionResponse:
        import uuid

        sid = f"drop_{uuid.uuid4().hex[:12]}"
        self._sessions[sid] = {"cwd": cwd, "history": []}
        try:
            return NewSessionResponse(session_id=sid)
        except TypeError:
            return NewSessionResponse(sessionId=sid)  # type: ignore[call-arg]

    async def prompt(self, session_id: str, prompt: Any = None, **kwargs: Any) -> PromptResponse:
        if prompt is None:
            prompt = kwargs.get("prompt")
        text = _prompt_text(prompt)
        self._sessions.setdefault(session_id, {"history": []})
        self._sessions[session_id].setdefault("history", []).append({"role": "user", "text": text})

        auto = reason_auto(text)
        chunks: List[str] = []
        if auto.get("triggered"):
            chunks.append(
                f"[CoT×GoT auto-triggered: {', '.join(auto.get('triggers') or [])}]\n"
                f"graph={auto.get('id')} confidence={auto.get('confidence')}\n"
                f"→ {auto.get('recommendation')}\n"
            )
        elif len(text) > 40:
            g = run_reasoning(text, mode="cot", auto_triggered=False)
            chunks.append(f"[CoT] {g.get('recommendation')}\n")

        reply = await asyncio.to_thread(self._route, text, auto if auto.get("triggered") else None)
        chunks.append(reply)
        full = "\n".join(chunks)
        self._sessions[session_id]["history"].append({"role": "assistant", "text": full})

        try:
            return PromptResponse(stop_reason="end_turn")
        except TypeError:
            return PromptResponse(stopReason="end_turn")  # type: ignore[call-arg]

    def _route(self, text: str, reasoning: dict | None) -> str:
        tl = text.lower()
        lines = ["## Drop ACP agent"]
        if reasoning:
            lines.append(f"_Reasoning graph:_ `{reasoning.get('id')}`")

        try:
            if any(k in tl for k in ("linear", "issue", "spe-", "ticket")):
                from tools.linear_tools import linear_status, list_linear_issues

                st = linear_status()
                issues = list_linear_issues(limit=5)
                lines.append(f"**Linear:** ok={st.get('ok')} mode={st.get('mode')} team={st.get('team_key')}")
                for it in (issues.get("issues") or [])[:5]:
                    lines.append(
                        f"- {it.get('identifier')}: {it.get('title')} [{(it.get('state') or {}).get('name')}]"
                    )
                return "\n".join(lines)

            if any(k in tl for k in ("health", "status", "integrations")):
                from drop_server.mcp_app import drop_health

                h = drop_health()
                lines.append("```json\n" + json.dumps(h, indent=2)[:3000] + "\n```")
                return "\n".join(lines)

            if any(k in tl for k in ("product", "niche", "rank", "lifecycle", "dropship")):
                lines.append(
                    "For autonomous product work use MCP tools:\n"
                    "- `agency_product_rank` / `agency_run_lifecycle`\n"
                    "- `linear_create_issue` for dual-write\n"
                    "- `spend_request_approval` then human confirm\n"
                    f"Goal received: {text[:500]}"
                )
                if reasoning:
                    lines.append(f"Recommendation: {reasoning.get('recommendation')}")
                return "\n".join(lines)
        except Exception as e:
            lines.append(f"Tool error: {e}")

        lines.append(
            "I'm the Drop ACP agent (MCP+ACP hybrid). "
            "Ask about Linear issues, integrations health, product ranking, or lifecycle. "
            "Full tool surface is on MCP at `/mcp`."
        )
        lines.append(f"You said: {text[:800]}")
        return "\n".join(lines)


def main() -> None:
    """stdio ACP entrypoint: python -m drop_server.acp_agent"""
    agent = DropACPAgent()
    run_agent(agent)


if __name__ == "__main__":
    main()
