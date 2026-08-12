"""xAI SuperGrok OAuth — device-code login + token resolve for Agno models.

Despite the historical filename (xai_oauth_pkce), the live xAI Grok CLI flow is
OAuth 2.0 *device code* (RFC 8628), not browser PKCE. Token resolution order:

1. ``XAI_API_KEY`` env (console key — always wins)
2. Project token store (``~/.config/ai-agency/xai_oauth.json``)
3. Hermes auth store (``~/.hermes/auth.json`` provider ``xai-oauth``) if present

CLI::

    python -m tools.xai_oauth_pkce login
    python -m tools.xai_oauth_pkce status
    python -m tools.xai_oauth_pkce logout
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import webbrowser
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

DEFAULT_XAI_BASE_URL = "https://api.x.ai/v1"
XAI_OAUTH_ISSUER = "https://auth.x.ai"
XAI_OAUTH_DISCOVERY_URL = f"{XAI_OAUTH_ISSUER}/.well-known/openid-configuration"
XAI_OAUTH_CLIENT_ID = os.getenv(
    "XAI_OAUTH_CLIENT_ID", "b1a00492-073a-47ea-816f-4c329264a828"
)
XAI_OAUTH_SCOPE = "openid profile email offline_access grok-cli:access api:access"
XAI_OAUTH_DEVICE_CODE_URL = f"{XAI_OAUTH_ISSUER}/oauth2/device/code"

DEFAULT_TOKEN_PATH = Path(
    os.getenv("AI_AGENCY_XAI_TOKEN_PATH")
    or (Path.home() / ".config" / "ai-agency" / "xai_oauth.json")
)
HERMES_AUTH_PATH = Path(os.getenv("HERMES_HOME", Path.home() / ".hermes")) / "auth.json"


class XaiOAuthError(RuntimeError):
    def __init__(self, message: str, *, code: str = "xai_oauth_error", relogin_required: bool = False):
        super().__init__(message)
        self.code = code
        self.relogin_required = relogin_required


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _validate_xai_endpoint(url: str, *, field: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise XaiOAuthError(f"{field} must be https", code="xai_endpoint_invalid")
    host = (parsed.hostname or "").lower()
    if host != "x.ai" and not host.endswith(".x.ai"):
        raise XaiOAuthError(f"{field} host must be under x.ai", code="xai_endpoint_invalid")
    return url


def _token_path() -> Path:
    return Path(DEFAULT_TOKEN_PATH).expanduser()


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _save_tokens(state: dict[str, Any], path: Path | None = None) -> Path:
    target = path or _token_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    os.chmod(tmp, 0o600)
    tmp.replace(target)
    try:
        os.chmod(target, 0o600)
    except OSError:
        pass
    return target


def _jwt_exp(access_token: str) -> int | None:
    try:
        parts = access_token.split(".")
        if len(parts) < 2:
            return None
        import base64

        pad = "=" * (-len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(parts[1] + pad))
        exp = payload.get("exp")
        return int(exp) if exp is not None else None
    except Exception:
        return None


def _is_expiring(access_token: str, skew_seconds: int = 120) -> bool:
    exp = _jwt_exp(access_token)
    if exp is None:
        return False
    return time.time() >= (exp - max(0, skew_seconds))


def discover_oidc(timeout_seconds: float = 15.0) -> dict[str, str]:
    try:
        response = httpx.get(
            XAI_OAUTH_DISCOVERY_URL,
            headers={"Accept": "application/json"},
            timeout=timeout_seconds,
        )
    except Exception as exc:
        raise XaiOAuthError(f"xAI OIDC discovery failed: {exc}", code="xai_discovery_failed") from exc
    if response.status_code != 200:
        raise XaiOAuthError(
            f"xAI OIDC discovery returned status {response.status_code}",
            code="xai_discovery_failed",
        )
    payload = response.json()
    if not isinstance(payload, dict):
        raise XaiOAuthError("Invalid discovery payload", code="xai_discovery_incomplete")
    authorization_endpoint = str(payload.get("authorization_endpoint") or "").strip()
    token_endpoint = str(payload.get("token_endpoint") or "").strip()
    if not authorization_endpoint or not token_endpoint:
        raise XaiOAuthError("Discovery missing endpoints", code="xai_discovery_incomplete")
    _validate_xai_endpoint(authorization_endpoint, field="authorization_endpoint")
    _validate_xai_endpoint(token_endpoint, field="token_endpoint")
    return {
        "authorization_endpoint": authorization_endpoint,
        "token_endpoint": token_endpoint,
    }


def refresh_tokens(
    refresh_token: str,
    *,
    token_endpoint: str = "",
    timeout_seconds: float = 20.0,
) -> dict[str, Any]:
    if not refresh_token.strip():
        raise XaiOAuthError(
            "Missing refresh_token. Run: python -m tools.xai_oauth_pkce login",
            code="xai_auth_missing_refresh_token",
            relogin_required=True,
        )
    endpoint = token_endpoint.strip() or discover_oidc(timeout_seconds)["token_endpoint"]
    _validate_xai_endpoint(endpoint, field="token_endpoint")
    with httpx.Client(timeout=max(5.0, timeout_seconds), headers={"Accept": "application/json"}) as client:
        response = client.post(
            endpoint,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "refresh_token",
                "client_id": XAI_OAUTH_CLIENT_ID,
                "refresh_token": refresh_token,
            },
        )
    if response.status_code != 200:
        detail = response.text.strip()
        if response.status_code == 403:
            raise XaiOAuthError(
                "xAI token refresh HTTP 403 — account may lack SuperGrok Heavy / API entitlement. "
                "Set XAI_API_KEY instead of re-login loops."
                + (f" Response: {detail}" if detail else ""),
                code="xai_oauth_tier_denied",
                relogin_required=False,
            )
        raise XaiOAuthError(
            "xAI token refresh failed" + (f": {detail}" if detail else ""),
            code="xai_refresh_failed",
            relogin_required=response.status_code in {400, 401},
        )
    payload = response.json()
    access = str(payload.get("access_token") or "").strip()
    if not access:
        raise XaiOAuthError("Refresh missing access_token", code="xai_refresh_missing_access_token", relogin_required=True)
    return {
        "access_token": access,
        "refresh_token": str(payload.get("refresh_token") or refresh_token).strip(),
        "id_token": str(payload.get("id_token") or "").strip(),
        "expires_in": payload.get("expires_in"),
        "token_type": str(payload.get("token_type") or "Bearer").strip() or "Bearer",
        "last_refresh": _utc_now_iso(),
    }


def _request_device_code(client: httpx.Client) -> dict[str, Any]:
    response = client.post(
        XAI_OAUTH_DEVICE_CODE_URL,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        },
        data={"client_id": XAI_OAUTH_CLIENT_ID, "scope": XAI_OAUTH_SCOPE},
    )
    if response.status_code != 200:
        raise XaiOAuthError(
            f"Device-code request failed (HTTP {response.status_code}): {response.text.strip()}",
            code="device_code_request_failed",
        )
    payload = response.json()
    required = (
        "device_code",
        "user_code",
        "verification_uri",
        "verification_uri_complete",
        "expires_in",
        "interval",
    )
    missing = [k for k in required if k not in payload]
    if missing:
        raise XaiOAuthError(f"Device-code response missing: {', '.join(missing)}", code="device_code_invalid")
    return payload


def _poll_device_token(
    client: httpx.Client,
    *,
    token_endpoint: str,
    device_code: str,
    expires_in: int,
    poll_interval: int,
) -> dict[str, Any]:
    deadline = time.monotonic() + max(1, int(expires_in))
    interval = max(1, int(poll_interval))
    while time.monotonic() < deadline:
        response = client.post(
            token_endpoint,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            },
            data={
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                "client_id": XAI_OAUTH_CLIENT_ID,
                "device_code": device_code,
            },
        )
        if response.status_code == 200:
            payload = response.json()
            if not payload.get("access_token") or not payload.get("refresh_token"):
                raise XaiOAuthError(
                    "Device token response missing access/refresh token",
                    code="xai_device_token_invalid",
                )
            return payload
        try:
            error_payload = response.json()
        except Exception:
            raise XaiOAuthError(
                f"Device token poll failed (HTTP {response.status_code})",
                code="xai_device_token_failed",
            )
        err = str(error_payload.get("error") or "")
        if err == "authorization_pending":
            time.sleep(interval)
            continue
        if err == "slow_down":
            interval = min(interval + 1, 30)
            time.sleep(interval)
            continue
        description = error_payload.get("error_description") or err or response.text
        raise XaiOAuthError(f"Device token poll failed: {description}", code="xai_device_token_failed")
    raise XaiOAuthError("Timed out waiting for xAI device authorization", code="device_code_timeout")


def device_code_login(*, open_browser: bool = True, timeout_seconds: float = 20.0) -> dict[str, Any]:
    discovery = discover_oidc(timeout_seconds)
    token_endpoint = discovery["token_endpoint"]
    with httpx.Client(timeout=max(20.0, timeout_seconds), headers={"Accept": "application/json"}) as client:
        device_data = _request_device_code(client)
        verification_url = str(device_data.get("verification_uri_complete") or device_data["verification_uri"])
        user_code = str(device_data["user_code"])
        print()
        print("xAI SuperGrok device-code login")
        print(f"  1. Open: {verification_url}")
        print(f"  2. If prompted, enter code: {user_code}")
        if open_browser:
            try:
                if webbrowser.open(verification_url):
                    print("  (Opened browser)")
            except Exception:
                print("  (Could not open browser — use the URL above)")
        print(f"Waiting for approval (poll every {max(1, int(device_data['interval']))}s)...")
        payload = _poll_device_token(
            client,
            token_endpoint=token_endpoint,
            device_code=str(device_data["device_code"]),
            expires_in=int(device_data["expires_in"]),
            poll_interval=int(device_data["interval"]),
        )

    state = {
        "provider": "xai-oauth",
        "auth_mode": "oauth_device_code",
        "tokens": {
            "access_token": str(payload.get("access_token") or "").strip(),
            "refresh_token": str(payload.get("refresh_token") or "").strip(),
            "id_token": str(payload.get("id_token") or "").strip(),
            "expires_in": payload.get("expires_in"),
            "token_type": str(payload.get("token_type") or "Bearer").strip() or "Bearer",
        },
        "discovery": discovery,
        "last_refresh": _utc_now_iso(),
        "base_url": os.getenv("XAI_BASE_URL", DEFAULT_XAI_BASE_URL).rstrip("/"),
    }
    path = _save_tokens(state)
    print(f"Saved tokens → {path}")
    return state


def _tokens_from_project_store() -> dict[str, Any] | None:
    state = _load_json(_token_path())
    tokens = state.get("tokens") if isinstance(state.get("tokens"), dict) else {}
    access = str(tokens.get("access_token") or "").strip()
    refresh = str(tokens.get("refresh_token") or "").strip()
    if not access and not refresh:
        return None
    return state


def _tokens_from_hermes_store() -> dict[str, Any] | None:
    store = _load_json(HERMES_AUTH_PATH)
    # Hermes shapes vary: providers dict or nested auth entries
    providers = store.get("providers") if isinstance(store.get("providers"), dict) else {}
    state = providers.get("xai-oauth") if isinstance(providers.get("xai-oauth"), dict) else None
    if state is None:
        # Alternate: top-level keys used by some Hermes versions
        for key in ("xai-oauth", "xai_oauth"):
            if isinstance(store.get(key), dict):
                state = store[key]
                break
    if not isinstance(state, dict):
        return None
    tokens = state.get("tokens") if isinstance(state.get("tokens"), dict) else {}
    if not tokens.get("access_token") and not tokens.get("refresh_token"):
        return None
    return state


def _persist_refreshed(state: dict[str, Any], refreshed: dict[str, Any], *, project: bool) -> dict[str, Any]:
    tokens = dict(state.get("tokens") or {})
    tokens["access_token"] = refreshed["access_token"]
    tokens["refresh_token"] = refreshed["refresh_token"]
    if refreshed.get("id_token"):
        tokens["id_token"] = refreshed["id_token"]
    if refreshed.get("expires_in") is not None:
        tokens["expires_in"] = refreshed["expires_in"]
    if refreshed.get("token_type"):
        tokens["token_type"] = refreshed["token_type"]
    state = dict(state)
    state["tokens"] = tokens
    state["last_refresh"] = refreshed.get("last_refresh") or _utc_now_iso()
    if project:
        _save_tokens(state)
    return state


def get_xai_token_or_fallback(*, force_refresh: bool = False, skew_seconds: int = 120) -> str:
    """Return a usable Bearer token / API key for OpenAI-compatible xAI chat."""
    env_key = (os.getenv("XAI_API_KEY") or "").strip()
    if env_key:
        return env_key

    state = _tokens_from_project_store()
    source = "project"
    if state is None:
        state = _tokens_from_hermes_store()
        source = "hermes"
    if state is None:
        raise XaiOAuthError(
            "No xAI credentials. Set XAI_API_KEY or run: python -m tools.xai_oauth_pkce login",
            code="xai_auth_missing",
            relogin_required=True,
        )

    tokens = dict(state.get("tokens") or {})
    access = str(tokens.get("access_token") or "").strip()
    refresh = str(tokens.get("refresh_token") or "").strip()
    discovery = state.get("discovery") if isinstance(state.get("discovery"), dict) else {}
    token_endpoint = str(discovery.get("token_endpoint") or "").strip()

    needs_refresh = force_refresh or (not access) or _is_expiring(access, skew_seconds)
    if needs_refresh and refresh:
        refreshed = refresh_tokens(refresh, token_endpoint=token_endpoint)
        state = _persist_refreshed(state, refreshed, project=(source == "project"))
        access = refreshed["access_token"]
    if not access:
        raise XaiOAuthError(
            "xAI access_token unavailable after refresh. Re-login.",
            code="xai_auth_missing_access_token",
            relogin_required=True,
        )
    return access


def status() -> dict[str, Any]:
    env_set = bool((os.getenv("XAI_API_KEY") or "").strip())
    project = _tokens_from_project_store()
    hermes = _tokens_from_hermes_store()
    out: dict[str, Any] = {
        "xai_api_key_set": env_set,
        "project_token_path": str(_token_path()),
        "project_oauth_set": project is not None,
        "hermes_oauth_set": hermes is not None,
        "hermes_auth_path": str(HERMES_AUTH_PATH),
    }
    if project:
        access = str((project.get("tokens") or {}).get("access_token") or "")
        out["project_expiring"] = _is_expiring(access) if access else True
        out["project_last_refresh"] = project.get("last_refresh")
    return out


def logout() -> None:
    path = _token_path()
    if path.is_file():
        path.unlink()
        print(f"Removed {path}")
    else:
        print(f"No project token file at {path}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m tools.xai_oauth_pkce", description="xAI SuperGrok device-code OAuth")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_login = sub.add_parser("login", help="Device-code login (SuperGrok)")
    p_login.add_argument("--no-browser", action="store_true")
    p_login.add_argument("--timeout", type=float, default=20.0)

    sub.add_parser("status", help="Show credential status (no secrets)")
    sub.add_parser("logout", help="Delete project OAuth token file")
    p_token = sub.add_parser("token", help="Print resolved access token (sensitive)")
    p_token.add_argument("--force-refresh", action="store_true")

    args = parser.parse_args(argv)
    try:
        if args.cmd == "login":
            device_code_login(open_browser=not args.no_browser, timeout_seconds=args.timeout)
            print("Login successful.")
            return 0
        if args.cmd == "status":
            print(json.dumps(status(), indent=2))
            return 0
        if args.cmd == "logout":
            logout()
            return 0
        if args.cmd == "token":
            print(get_xai_token_or_fallback(force_refresh=args.force_refresh))
            return 0
    except XaiOAuthError as exc:
        print(f"ERROR [{exc.code}]: {exc}", file=sys.stderr)
        return 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
