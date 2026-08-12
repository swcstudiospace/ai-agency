"""CodeRabbit CLI tools — local + CI review integration for the agency."""

from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

from tools.envutil import env

_ROOT = Path(__file__).resolve().parents[1]
_ART = _ROOT / "tmp" / "coderabbit"


def _cr_bin() -> str | None:
    p = (env("CODERABBIT_BIN") or "").strip()
    if p and Path(p).exists():
        return p
    return shutil.which("coderabbit") or shutil.which("cr")


def _run(argv: list[str], timeout_s: float = 600.0, cwd: str = "") -> dict[str, Any]:
    run_env = os.environ.copy()
    if env("CODERABBIT_API_KEY"):
        run_env["CODERABBIT_API_KEY"] = env("CODERABBIT_API_KEY") or ""
    try:
        proc = subprocess.run(
            argv,
            cwd=cwd or str(_ROOT),
            capture_output=True,
            text=True,
            timeout=timeout_s,
            env=run_env,
        )
        return {
            "ok": proc.returncode == 0,
            "exit_code": proc.returncode,
            "cmd": [a if "key" not in a.lower() else "***" for a in argv],
            "stdout": (proc.stdout or "")[-80000:],
            "stderr": (proc.stderr or "")[-20000:],
            "output": ((proc.stdout or "") + "\n" + (proc.stderr or ""))[-80000:],
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "cmd": argv}


def coderabbit_status() -> dict[str, Any]:
    """CLI install + auth/doctor status (no secrets)."""
    cr = _cr_bin()
    if not cr:
        return {
            "ok": False,
            "installed": False,
            "hint": "curl -fsSL https://cli.coderabbit.ai/install.sh | sh",
        }
    doc = _run([cr, "doctor"], timeout_s=60)
    auth = _run([cr, "auth", "status", "--agent"], timeout_s=30)
    return {
        "ok": True,
        "installed": True,
        "bin": cr,
        "api_key_set": bool(env("CODERABBIT_API_KEY")),
        "doctor": doc,
        "auth": auth,
    }


def coderabbit_review(
    *,
    base: str = "main",
    agent_json: bool = True,
    uncommitted: bool = False,
    include_untracked: bool = False,
    committed_only: bool = False,
    light: bool = False,
    timeout_s: float = 900.0,
) -> dict[str, Any]:
    """Run CodeRabbit CLI review on the repo (HITL for applying fixes)."""
    cr = _cr_bin()
    if not cr:
        return {"ok": False, "error": "coderabbit CLI not found"}
    argv = [cr, "review"]
    if agent_json:
        argv.append("--agent")
    if light:
        argv.append("--light")
    if uncommitted:
        argv.append("--uncommitted")
    if include_untracked:
        argv.append("--include-untracked")
    if committed_only:
        argv.append("--committed")
    if base:
        argv += ["--base", base]
    if env("CODERABBIT_API_KEY"):
        argv += ["--api-key", env("CODERABBIT_API_KEY") or ""]

    result = _run(argv, timeout_s=timeout_s)
    _ART.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    path = _ART / f"review_{stamp}.txt"
    path.write_text(result.get("output") or result.get("stdout") or "", encoding="utf-8")
    result["artifact"] = str(path)
    result["hitl"] = True
    result["note"] = "Review only — agents must not auto-commit fixes without human approval"
    return result


def coderabbit_config_validate(path: str = "") -> dict[str, Any]:
    """Validate .coderabbit.yaml against official schema."""
    cr = _cr_bin()
    if not cr:
        return {"ok": False, "error": "coderabbit CLI not found"}
    argv = [cr, "config", "validate"]
    if path:
        argv.append(path)
    return _run(argv, timeout_s=60)


def get_coderabbit_tools() -> list:
    return [coderabbit_status, coderabbit_review, coderabbit_config_validate]
