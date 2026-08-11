"""Shared env loading for agency tools (never prints secrets)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Iterable, Optional

_EXTRA_ENV_FILES = (
    Path("/root/src/repos/ai-agency/.env"),
    Path("/root/.config/hermes-linear/connector.env"),
    Path("/root/.config/parallel/api.env"),
    Path.home() / ".hermes" / ".env",
)


def load_dotenv_files(paths: Iterable[Path] | None = None) -> None:
    for path in paths or _EXTRA_ENV_FILES:
        if not path.is_file():
            continue
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                k, v = k.strip(), v.strip().strip('"').strip("'")
                if k and v and k not in os.environ:
                    os.environ[k] = v
        except OSError:
            continue


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
