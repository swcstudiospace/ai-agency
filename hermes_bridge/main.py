"""Hermes Bridge gateway — MCP for Agno reverse calls."""

from __future__ import annotations

import contextlib
import os
import secrets
import sys
from pathlib import Path

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from hermes_bridge.mcp_app import get_mcp

try:
    from tools.envutil import env, load_dotenv_files

    load_dotenv_files()
except Exception:

    def env(name: str, default: str = "") -> str:  # type: ignore
        return (os.getenv(name) or default).strip()


HOST = env("HERMES_BRIDGE_HOST", "127.0.0.1")
PORT = int(env("HERMES_BRIDGE_PORT", "7790") or "7790")
TOKEN = env("HERMES_BRIDGE_TOKEN") or env("DROP_MCP_TOKEN")
if not TOKEN:
    TOKEN = secrets.token_urlsafe(24)
    os.environ["HERMES_BRIDGE_TOKEN"] = TOKEN


class BearerAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in {"/health", "/"}:
            return await call_next(request)
        require = (env("HERMES_BRIDGE_REQUIRE_AUTH", "1") or "1").lower() in {"1", "true", "yes"}
        if not require:
            return await call_next(request)
        client = request.client.host if request.client else ""
        if (env("HERMES_BRIDGE_ALLOW_LOCALHOST", "1") or "1").lower() in {"1", "true", "yes"} and client in {
            "127.0.0.1",
            "::1",
        }:
            return await call_next(request)
        auth = request.headers.get("authorization") or ""
        token = auth.split(" ", 1)[1].strip() if auth.lower().startswith("bearer ") else ""
        token = token or request.headers.get("x-hermes-bridge-token") or ""
        if not token or not secrets.compare_digest(token, TOKEN):
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        return await call_next(request)


async def health(_: Request) -> JSONResponse:
    from hermes_bridge.mcp_app import hermes_bridge_health

    return JSONResponse(hermes_bridge_health())


async def root(_: Request) -> JSONResponse:
    return JSONResponse(
        {
            "name": "Hermes Reverse Bridge",
            "mcp": f"http://{HOST}:{PORT}/mcp",
            "purpose": "Agno agents → Hermes browser/skills/memory + KIP shared graph",
            "kip": "local Cognitive Nexus; EXPORT for ICP capsules",
        }
    )


def build_app() -> Starlette:
    mcp = get_mcp()
    mcp_app = mcp.streamable_http_app()

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette):
        async with mcp.session_manager.run():
            yield

    return Starlette(
        routes=[
            Route("/health", health, methods=["GET"]),
            Route("/", root, methods=["GET"]),
            Mount("/", app=mcp_app),
        ],
        middleware=[Middleware(BearerAuthMiddleware)],
        lifespan=lifespan,
    )


app = build_app()


def main() -> None:
    import uvicorn

    print(f"[hermes-bridge] http://{HOST}:{PORT}/mcp", flush=True)
    uvicorn.run("hermes_bridge.main:app", host=HOST, port=PORT, reload=False, log_level="info")


if __name__ == "__main__":
    main()
