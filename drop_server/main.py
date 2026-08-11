"""Drop hybrid gateway: MCP (Streamable HTTP) + ACP HTTP bridge + health.

Bind: 127.0.0.1:7788 (nginx terminates TLS for drop.autonogrammer.ai)

Endpoints:
  GET  /health
  GET  /           — service card
  *    /mcp        — MCP Streamable HTTP (Python MCP SDK / FastMCP)
  POST /acp/v1/session
  POST /acp/v1/session/{id}/prompt
  GET  /acp/v1/session/{id}
  GET  /acp/stdio-info — how to run stdio ACP
"""

from __future__ import annotations

import os
import secrets
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Mount, Route

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from drop_server.mcp_app import get_mcp
from drop_server.reasoning.cot_got import reason_auto, run_reasoning

# Load agency env helpers
try:
    from tools.envutil import env, load_dotenv_files

    load_dotenv_files()
except Exception:

    def env(name: str, default: str = "") -> str:  # type: ignore
        return (os.getenv(name) or default).strip()


DROP_TOKEN = env("DROP_MCP_TOKEN") or env("DROP_ACP_TOKEN")
# Generate ephemeral dev token if unset (printed once at startup)
_EPHEMERAL = False
if not DROP_TOKEN:
    DROP_TOKEN = secrets.token_urlsafe(24)
    _EPHEMERAL = True
    os.environ["DROP_MCP_TOKEN"] = DROP_TOKEN

HOST = env("DROP_HOST", "127.0.0.1")
PORT = int(env("DROP_PORT", "7788") or "7788")

_ACP_SESSIONS: Dict[str, Dict[str, Any]] = {}


class BearerAuthMiddleware(BaseHTTPMiddleware):
    """Optional bearer auth for non-health routes when DROP_MCP_REQUIRE_AUTH=1 (default)."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path in {"/health", "/", "/acp/stdio-info"} or path.startswith("/.well-known"):
            return await call_next(request)
        require = (env("DROP_MCP_REQUIRE_AUTH", "1") or "1").lower() in {"1", "true", "yes"}
        if not require:
            return await call_next(request)
        # Allow local loopback without token for hermes on same host if configured
        client = request.client.host if request.client else ""
        allow_local = (env("DROP_MCP_ALLOW_LOCALHOST", "1") or "1").lower() in {"1", "true", "yes"}
        if allow_local and client in {"127.0.0.1", "::1"}:
            return await call_next(request)
        auth = request.headers.get("authorization") or ""
        token = ""
        if auth.lower().startswith("bearer "):
            token = auth.split(" ", 1)[1].strip()
        token = token or request.headers.get("x-drop-token") or ""
        if not token or not secrets.compare_digest(token, DROP_TOKEN):
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        return await call_next(request)


async def health(_: Request) -> JSONResponse:
    body: Dict[str, Any] = {
        "ok": True,
        "service": "drop-autonogrammer",
        "protocols": {
            "mcp": "/mcp",
            "acp_http": "/acp/v1",
            "acp_stdio": "python -m drop_server.acp_agent",
        },
        "ts": time.time(),
    }
    try:
        from tools.linear_tools import linear_status

        body["linear"] = linear_status()
    except Exception as e:
        body["linear"] = {"ok": False, "error": str(e)}
    return JSONResponse(body)


async def root(_: Request) -> JSONResponse:
    return JSONResponse(
        {
            "name": "Drop Autonogrammer Universal Gateway",
            "url": "https://drop.autonogrammer.ai",
            "mcp": "https://drop.autonogrammer.ai/mcp",
            "acp": {
                "http": "https://drop.autonogrammer.ai/acp/v1",
                "stdio": "python -m drop_server.acp_agent",
            },
            "features": [
                "MCP Streamable HTTP (Python SDK FastMCP)",
                "ACP stdio agent + HTTP session bridge",
                "Linear dual-write tools",
                "Agency lifecycle / product rank bridges",
                "Autonomous CoT × GoT reasoning graphs",
                "HITL spend request (no self-confirm)",
            ],
            "auth": "Bearer DROP_MCP_TOKEN (localhost exempt by default)",
            "agentos": "http://127.0.0.1:7777/mcp",
        }
    )


async def acp_stdio_info(_: Request) -> JSONResponse:
    return JSONResponse(
        {
            "command": str(_ROOT / ".venv" / "bin" / "python"),
            "args": ["-m", "drop_server.acp_agent"],
            "cwd": str(_ROOT),
            "env": {"PYTHONPATH": str(_ROOT)},
            "zed_settings_snippet": {
                "agent_servers": {
                    "Drop Autonogrammer": {
                        "type": "custom",
                        "command": str(_ROOT / ".venv" / "bin" / "python"),
                        "args": ["-m", "drop_server.acp_agent"],
                        "env": {"PYTHONPATH": str(_ROOT)},
                    }
                }
            },
            "hermes": "hermes acp (uses Hermes agent); for this Drop agent use stdio command above",
        }
    )


async def acp_new_session(request: Request) -> JSONResponse:
    body = {}
    try:
        body = await request.json()
    except Exception:
        pass
    sid = f"drop_{uuid.uuid4().hex[:12]}"
    goal = (body or {}).get("goal") or (body or {}).get("prompt") or ""
    reasoning = None
    if goal:
        reasoning = reason_auto(str(goal))
    _ACP_SESSIONS[sid] = {
        "id": sid,
        "created_at": time.time(),
        "history": [],
        "meta": body,
        "last_reasoning": reasoning if reasoning and reasoning.get("triggered") else None,
    }
    return JSONResponse(
        {
            "session_id": sid,
            "reasoning": _ACP_SESSIONS[sid]["last_reasoning"],
            "protocol": "acp-http-bridge",
        }
    )


async def acp_prompt(request: Request) -> JSONResponse:
    sid = request.path_params["session_id"]
    sess = _ACP_SESSIONS.get(sid)
    if not sess:
        return JSONResponse({"error": "session not found"}, status_code=404)
    try:
        body = await request.json()
    except Exception:
        body = {}
    text = (body or {}).get("prompt") or (body or {}).get("text") or ""
    if isinstance(text, list):
        # content blocks
        text = " ".join(
            (b.get("text") if isinstance(b, dict) else str(b)) for b in text  # type: ignore
        )
    text = str(text).strip()
    sess["history"].append({"role": "user", "text": text, "ts": time.time()})

    # Auto CoT×GoT
    auto = reason_auto(text)
    from drop_server.acp_agent import DropACPAgent

    agent = DropACPAgent()
    agent._sessions[sid] = sess
    # reuse routing synchronously
    reply = agent._route(text, auto if auto.get("triggered") else None)
    if auto.get("triggered"):
        preface = (
            f"[CoT×GoT auto] triggers={auto.get('triggers')} graph={auto.get('id')}\n"
            f"{auto.get('recommendation')}\n\n"
        )
        reply = preface + reply
    sess["history"].append({"role": "assistant", "text": reply, "ts": time.time()})
    sess["last_reasoning"] = auto if auto.get("triggered") else sess.get("last_reasoning")
    return JSONResponse(
        {
            "session_id": sid,
            "reply": reply,
            "reasoning": auto if auto.get("triggered") else None,
            "stop_reason": "end_turn",
        }
    )


async def acp_get_session(request: Request) -> JSONResponse:
    sid = request.path_params["session_id"]
    sess = _ACP_SESSIONS.get(sid)
    if not sess:
        return JSONResponse({"error": "session not found"}, status_code=404)
    return JSONResponse(sess)


async def acp_reason(request: Request) -> JSONResponse:
    try:
        body = await request.json()
    except Exception:
        body = {}
    goal = (body or {}).get("goal") or ""
    mode = (body or {}).get("mode") or "hybrid"
    return JSONResponse(run_reasoning(goal, mode=mode, auto_triggered=bool((body or {}).get("auto", True))))


def build_app() -> Starlette:
    import contextlib

    mcp = get_mcp()
    mcp_app = mcp.streamable_http_app()  # creates session_manager

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette):
        # Required for Streamable HTTP MCP session task group
        async with mcp.session_manager.run():
            yield

    routes = [
        Route("/health", health, methods=["GET"]),
        Route("/", root, methods=["GET"]),
        Route("/acp/stdio-info", acp_stdio_info, methods=["GET"]),
        Route("/acp/v1/session", acp_new_session, methods=["POST"]),
        Route("/acp/v1/session/{session_id}/prompt", acp_prompt, methods=["POST"]),
        Route("/acp/v1/session/{session_id}", acp_get_session, methods=["GET"]),
        Route("/acp/v1/reason", acp_reason, methods=["POST"]),
        # FastMCP streamable_http_app already serves at /mcp — mount at root
        Mount("/", app=mcp_app),
    ]
    app = Starlette(
        routes=routes,
        middleware=[Middleware(BearerAuthMiddleware)],
        lifespan=lifespan,
    )
    return app


app = build_app()


def main() -> None:
    import uvicorn

    if _EPHEMERAL:
        print(f"[drop] EPHEMERAL DROP_MCP_TOKEN={DROP_TOKEN}", flush=True)
        print("[drop] Set DROP_MCP_TOKEN in .env for a stable token.", flush=True)
    print(f"[drop] MCP+ACP gateway on http://{HOST}:{PORT}", flush=True)
    print(f"[drop] MCP: http://{HOST}:{PORT}/mcp", flush=True)
    print(f"[drop] ACP HTTP: http://{HOST}:{PORT}/acp/v1", flush=True)
    uvicorn.run(
        "drop_server.main:app",
        host=HOST,
        port=PORT,
        reload=False,
        log_level="info",
        timeout_keep_alive=75,
    )


if __name__ == "__main__":
    main()
