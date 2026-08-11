"""Shared env loading for agency tools (never prints secrets)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Iterable, Optional

# Project .env is authoritative for agency LINEAR_* / AGENCY_* so a stale shell
# export (e.g. another org's Linear key) cannot silently win.
_PROJECT_ENV = Path("/root/src/repos/ai-agency/.env")
_EXTRA_ENV_FILES = (
    Path("/root/.config/hermes-linear/connector.env"),
    Path("/root/.config/parallel/api.env"),
    Path.home() / ".hermes" / ".env",
)
_FORCE_FROM_PROJECT = (
    "LINEAR_API_KEY",
    "LINEAR_TEAM_ID",
    "LINEAR_TEAM_KEY",
    "LINEAR_PROJECT_ID",
    "LINEAR_PROJECT_NAME",
    "LINEAR_ORG",
    "LINEAR_GITHUB_REPO",
    "AGENCY_GROK_MODEL",
    "PARALLEL_API_KEY",
)


def _parse_env_file(path: Path) -> Dict[str, str]:
    out: Dict[str, str] = {}
    if not path.is_file():
        return out
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k and v:
                out[k] = v
    except OSError:
        return out
    return out


def load_dotenv_files(paths: Iterable[Path] | None = None) -> None:
    # 1) optional extras — fill gaps only
    for path in paths or _EXTRA_ENV_FILES:
        for k, v in _parse_env_file(path).items():
            if k not in os.environ:
                os.environ[k] = v
    # 2) project .env — fill gaps, then force critical agency keys
    proj = _parse_env_file(_PROJECT_ENV)
    for k, v in proj.items():
        if k not in os.environ:
            os.environ[k] = v
    for k in _FORCE_FROM_PROJECT:
        if k in proj and proj[k]:
            os.environ[k] = proj[k]


def env(name: str, default: str = "") -> str:
    load_dotenv_files()
    return (os.getenv(name) or default).strip()


def env_bool(name: str, default: bool = False) -> bool:
    v = env(name).lower()
    if not v:
        return default
    return v in {"1", "true", "yes", "on"}


def require_env(*names: str) -> Optional[str]:
    """Return first missing env name, else None."""
    load_dotenv_files()
    for n in names:
        if not (os.getenv(n) or "").strip():
            return n
    return None


def redact_dict(d: Dict) -> Dict:
    out = {}
    for k, v in d.items():
        lk = k.lower()
        if any(s in lk for s in ("key", "token", "secret", "password", "seed", "private")):
            out[k] = "***" if v else ""
        else:
            out[k] = v
    return out
