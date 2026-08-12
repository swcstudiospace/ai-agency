"""Warp / Oz CLI bottom layer — Hermes → Agno → Warp execution stack.

Stack
-----
  Hermes Agent (top orchestrator)
       ↓ MCP
  Agno AgentOS (agents / teams / workflows)
       ↓ tools/warp_tools.py
  Warp Oz CLI  ``oz``  + Warp Agent CLI ``warp``  (bottom)

Agents should **prefer offloading** long shell / multi-step terminal work and
specialized coding agents to Warp Oz rather than inventing ad-hoc loops.

Auth
----
- ``WARP_API_KEY`` or ``oz login`` / ``warp --api-key``
- Never log secrets.

Env
---
- ``WARP_OZ_BIN`` — path to ``oz`` (default: PATH lookup)
- ``WARP_TUI_BIN`` — path to ``warp`` TUI agent CLI
- ``WARP_API_KEY`` — non-interactive auth
- ``WARP_DEFAULT_CWD`` — default workdir (repo root)
- ``WARP_AUTO_APPROVE`` — ``1`` to pass auto-approve where supported
- ``AGENCY_DISABLE_WARP`` — disable auto toolbelt attach
"""

from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

from tools.envutil import env

_ROOT = Path(__file__).resolve().parents[1]
_ARTIFACTS = _ROOT / "tmp" / "warp_runs"


def _which(name: str, env_key: str = "") -> str | None:
    if env_key:
        p = (env(env_key) or "").strip()
        if p and Path(p).exists():
            return p
    return shutil.which(name)


def _oz_bin() -> str | None:
    return _which("oz", "WARP_OZ_BIN") or _which("oz-stable") or _which("oz-preview")


def _warp_tui_bin() -> str | None:
    return _which("warp", "WARP_TUI_BIN")


def _default_cwd(cwd: str = "") -> str:
    c = (cwd or env("WARP_DEFAULT_CWD") or str(_ROOT)).strip()
    return c


def _run(
    argv: list[str],
    *,
    cwd: str = "",
    timeout_s: float = 600.0,
    env_extra: dict[str, str] | None = None,
) -> dict[str, Any]:
    run_env = os.environ.copy()
    if env("WARP_API_KEY"):
        run_env["WARP_API_KEY"] = env("WARP_API_KEY") or ""
    if env("WARP_OUTPUT_FORMAT"):
        run_env["WARP_OUTPUT_FORMAT"] = env("WARP_OUTPUT_FORMAT") or "pretty"
    if env_extra:
        run_env.update(env_extra)
    started = time.time()
    try:
        proc = subprocess.run(
            argv,
            cwd=_default_cwd(cwd) or None,
            capture_output=True,
            text=True,
            timeout=max(5.0, float(timeout_s)),
            env=run_env,
        )
        out = (proc.stdout or "") + (("\n" + proc.stderr) if proc.stderr else "")
        return {
            "ok": proc.returncode == 0,
            "exit_code": proc.returncode,
            "cmd": argv,
            "stdout": (proc.stdout or "")[-50000:],
            "stderr": (proc.stderr or "")[-20000:],
            "output": out[-50000:],
            "duration_s": round(time.time() - started, 2),
            "cwd": _default_cwd(cwd),
        }
    except subprocess.TimeoutExpired as e:
        return {
            "ok": False,
            "error": f"timeout after {timeout_s}s",
            "cmd": argv,
            "stdout": (e.stdout or "")[-20000:] if isinstance(e.stdout, str) else "",
            "duration_s": round(time.time() - started, 2),
        }
    except FileNotFoundError as e:
        return {"ok": False, "error": str(e), "cmd": argv}
    except Exception as e:
        return {"ok": False, "error": str(e), "cmd": argv}


def _save_artifact(kind: str, payload: dict[str, Any]) -> str:
    _ARTIFACTS.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    path = _ARTIFACTS / f"{kind}_{stamp}_{int(time.time()) % 10000}.json"
    # redact api keys in cmd display
    safe = json.loads(json.dumps(payload, default=str))
    if isinstance(safe.get("cmd"), list):
        safe["cmd"] = [
            ("***" if "wk-" in str(c) or str(c).startswith("sk-") else c) for c in safe["cmd"]
        ]
    path.write_text(json.dumps(safe, indent=2, default=str) + "\n", encoding="utf-8")
    return str(path)


def warp_status() -> dict[str, Any]:
    """Report Warp Oz + Warp TUI CLI availability and auth (no secrets)."""
    oz = _oz_bin()
    warp = _warp_tui_bin()
    who = None
    if oz:
        r = _run([oz, "whoami", "--output-format", "json"], timeout_s=30)
        who = {
            "ok": r.get("ok"),
            "exit_code": r.get("exit_code"),
            "output": (r.get("stdout") or r.get("output") or "")[:1500],
        }
    return {
        "ok": bool(oz or warp),
        "stack": "Hermes → Agno → Warp/Oz",
        "oz_bin": oz,
        "warp_tui_bin": warp,
        "warp_api_key_set": bool(env("WARP_API_KEY")),
        "whoami": who,
        "default_cwd": _default_cwd(),
        "hint": None
        if oz
        else "Install Oz CLI (https://docs.warp.dev/reference/cli/cli) or set WARP_OZ_BIN",
    }


def warp_offload_shell(
    command: str,
    *,
    cwd: str = "",
    timeout_s: float = 300.0,
    reason: str = "",
    agent_name: str = "",
) -> dict[str, Any]:
    """Offload a shell command through the Warp bottom layer (logged artifact).

    Prefer this over ad-hoc subprocess for multi-step ops so Hermes/Agno keep
    an audit trail under tmp/warp_runs/.
    """
    command = (command or "").strip()
    if not command:
        return {"ok": False, "error": "command required"}
    # Safety: block obvious secret-dumping patterns
    lowered = command.lower()
    for bad in ("cat .env", "printenv", "export ", "aws configure", "warp_api_key="):
        if bad in lowered and "example" not in lowered:
            # allow export PATH etc. but block export WARP_API_KEY dumps
            if bad == "export " and "api_key" not in lowered and "secret" not in lowered:
                continue
            if bad in ("cat .env",) or "api_key" in lowered or "secret" in lowered:
                return {
                    "ok": False,
                    "error": "blocked_sensitive_command",
                    "hint": "Do not dump secrets via warp_offload_shell",
                }

    argv = ["bash", "-lc", command]
    result = _run(argv, cwd=cwd, timeout_s=timeout_s)
    result["layer"] = "warp_offload_shell"
    result["reason"] = reason
    result["agent_name"] = agent_name
    result["artifact"] = _save_artifact("shell", result)
    result["note"] = "Shell offload via Warp bottom layer — prefer oz agent run for multi-step agent work"
    return result


def warp_agent_run(
    prompt: str,
    *,
    name: str = "",
    cwd: str = "",
    model: str = "",
    skill: str = "",
    mcp_json_path: str = "",
    share: str = "",
    timeout_s: float = 900.0,
    output_format: str = "pretty",
) -> dict[str, Any]:
    """Run a **local** Oz agent (``oz agent run``) — bottom-layer orchestration.

    Use for coding, shell multi-step, repo surgery that benefits from Warp agents.
    """
    oz = _oz_bin()
    if not oz:
        return {
            "ok": False,
            "error": "oz CLI not found",
            "hint": "Install Oz CLI or set WARP_OZ_BIN; fallback: warp_offload_shell",
        }
    prompt = (prompt or "").strip()
    if not prompt and not skill:
        return {"ok": False, "error": "prompt or skill required"}

    argv = [oz, "--output-format", output_format or "pretty", "agent", "run"]
    if env("WARP_API_KEY"):
        argv = [oz, "--api-key", env("WARP_API_KEY") or "", "--output-format", output_format or "pretty", "agent", "run"]
    if prompt:
        argv += ["--prompt", prompt]
    if skill:
        argv += ["--skill", skill]
    if name:
        argv += ["--name", name]
    cwd_use = _default_cwd(cwd)
    if cwd_use:
        argv += ["--cwd", cwd_use]
    if model:
        argv += ["--model", model]
    if mcp_json_path:
        argv += ["--mcp", mcp_json_path]
    elif (_ROOT / "configs" / "warp" / "agency-mcp.json").is_file():
        # default: connect Oz agent to local AgentOS MCP when present
        if (env("WARP_ATTACH_AGENCY_MCP") or "1").lower() not in {"0", "false", "no"}:
            argv += ["--mcp", str(_ROOT / "configs" / "warp" / "agency-mcp.json")]
    if share:
        argv += ["--share", share]

    result = _run(argv, cwd=cwd_use, timeout_s=timeout_s)
    result["layer"] = "oz_agent_run"
    result["prompt_preview"] = prompt[:300]
    result["artifact"] = _save_artifact("agent_run", result)
    return result


def warp_agent_run_cloud(
    prompt: str,
    *,
    name: str = "",
    environment: str = "",
    model: str = "",
    skill: str = "",
    harness: str = "",
    timeout_s: float = 120.0,
    open_session: bool = False,
) -> dict[str, Any]:
    """Dispatch a **cloud** Oz agent (``oz agent run-cloud``).

    Returns quickly with run metadata when authenticated; requires WARP_API_KEY
    or ``oz login``.
    """
    oz = _oz_bin()
    if not oz:
        return {"ok": False, "error": "oz CLI not found"}
    prompt = (prompt or "").strip()
    if not prompt and not skill:
        return {"ok": False, "error": "prompt or skill required"}

    argv = [oz, "--output-format", "json", "agent", "run-cloud"]
    if env("WARP_API_KEY"):
        argv = [oz, "--api-key", env("WARP_API_KEY") or "", "--output-format", "json", "agent", "run-cloud"]
    if prompt:
        argv += ["--prompt", prompt]
    if skill:
        argv += ["--skill", skill]
    if name:
        argv += ["--name", name]
    if environment or env("WARP_ENVIRONMENT_ID"):
        argv += ["--environment", environment or env("WARP_ENVIRONMENT_ID") or ""]
    else:
        argv += ["--no-environment"]
    if model:
        argv += ["--model", model]
    if harness:
        argv += ["--harness", harness]
    if open_session:
        argv += ["--open"]

    result = _run(argv, timeout_s=timeout_s)
    result["layer"] = "oz_agent_run_cloud"
    result["artifact"] = _save_artifact("agent_run_cloud", result)
    return result


def warp_tui_agent(
    prompt: str = "",
    *,
    resume: str = "",
    auto_approve: bool = False,
    timeout_s: float = 120.0,
) -> dict[str, Any]:
    """Invoke Warp TUI Agent CLI (``warp``) for non-interactive agent turns.

    The local ``warp`` binary is conversation-oriented; prefer ``warp_agent_run``
    (Oz) for scripted multi-step work.
    """
    warp = _warp_tui_bin()
    if not warp:
        return {"ok": False, "error": "warp TUI CLI not found", "hint": "Install Warp Agent CLI"}
    argv = [warp]
    if env("WARP_API_KEY"):
        argv += ["--api-key", env("WARP_API_KEY") or ""]
    if resume:
        argv += ["--resume", resume]
    if auto_approve or (env("WARP_AUTO_APPROVE") or "").lower() in {"1", "true", "yes"}:
        argv += ["--auto-approve"]
    # Many warp TUI builds read prompt from stdin when non-tty
    result = _run(
        argv,
        timeout_s=timeout_s,
        env_extra={"WARP_AGENT_PROMPT": prompt} if prompt else None,
    )
    # If binary only accepts flags, try piping prompt
    if not result.get("ok") and prompt and "unexpected" in (result.get("stderr") or "").lower():
        try:
            proc = subprocess.run(
                argv,
                input=prompt,
                capture_output=True,
                text=True,
                timeout=timeout_s,
                cwd=_default_cwd(),
            )
            result = {
                "ok": proc.returncode == 0,
                "exit_code": proc.returncode,
                "stdout": (proc.stdout or "")[-50000:],
                "stderr": (proc.stderr or "")[-20000:],
                "cmd": argv + ["<stdin-prompt>"],
            }
        except Exception as e:
            result = {"ok": False, "error": str(e), "cmd": argv}
    result["layer"] = "warp_tui"
    result["artifact"] = _save_artifact("tui", result)
    return result


def warp_run_list(limit: int = 10) -> dict[str, Any]:
    """List recent Oz cloud runs."""
    oz = _oz_bin()
    if not oz:
        return {"ok": False, "error": "oz CLI not found"}
    argv = [oz, "--output-format", "json", "run", "list", "--limit", str(max(1, min(50, limit)))]
    if env("WARP_API_KEY"):
        argv = [oz, "--api-key", env("WARP_API_KEY") or "", "--output-format", "json", "run", "list", "--limit", str(max(1, min(50, limit)))]
    return _run(argv, timeout_s=60)


def warp_run_get(run_id: str) -> dict[str, Any]:
    """Get details for an Oz run id."""
    oz = _oz_bin()
    if not oz:
        return {"ok": False, "error": "oz CLI not found"}
    run_id = (run_id or "").strip()
    if not run_id:
        return {"ok": False, "error": "run_id required"}
    argv = [oz, "--output-format", "json", "run", "get", run_id]
    if env("WARP_API_KEY"):
        argv = [oz, "--api-key", env("WARP_API_KEY") or "", "--output-format", "json", "run", "get", run_id]
    return _run(argv, timeout_s=60)


def warp_orchestrate_agency_task(
    goal: str,
    *,
    mode: str = "local",
    name: str = "",
    include_agency_mcp: bool = True,
    timeout_s: float = 900.0,
) -> dict[str, Any]:
    """High-level offload: run a Warp agent with agency context + optional MCP.

    ``mode``: local | cloud | shell
    """
    goal = (goal or "").strip()
    if not goal:
        return {"ok": False, "error": "goal required"}
    name = name or f"agency-{int(time.time())}"
    preamble = (
        "You are the Warp bottom-layer executor for the AI Dropshipping Agency. "
        "Hermes is top orchestrator; Agno owns agents/teams/workflows; you execute. "
        "Respect HITL: no live ad spend, no unsupervised supplier payments, Shopify drafts only. "
        f"Repo: {_ROOT}. Goal:\n"
    )
    full = preamble + goal
    mode = (mode or "local").lower()
    if mode == "cloud":
        return warp_agent_run_cloud(full, name=name, timeout_s=min(timeout_s, 180))
    if mode == "shell":
        # last resort: structured echo + user must expand
        return warp_offload_shell(
            f"echo {shlex.quote('WARP_SHELL_OFFLOAD: ' + goal[:500])}",
            reason=goal[:200],
        )
    mcp = str(_ROOT / "configs" / "warp" / "agency-mcp.json") if include_agency_mcp else ""
    return warp_agent_run(
        full,
        name=name,
        cwd=str(_ROOT),
        mcp_json_path=mcp if include_agency_mcp and Path(mcp).is_file() else "",
        timeout_s=timeout_s,
    )


def get_warp_tools() -> list:
    return [
        warp_status,
        warp_offload_shell,
        warp_agent_run,
        warp_agent_run_cloud,
        warp_tui_agent,
        warp_run_list,
        warp_run_get,
        warp_orchestrate_agency_task,
    ]


# ── instruction snippets for agents / teams / workflows ──────────────

WARP_OFFLOAD_INSTRUCTIONS = """
## Warp CLI bottom layer (mandatory preference)

Stack: **Hermes (top) → Agno agents/teams/workflows (middle) → Warp Oz CLI (bottom)**.

When work is multi-step shell, repo coding, or benefits from a specialized coding agent:
1. Call ``warp_status`` once if unsure CLIs are available.
2. Prefer ``warp_agent_run`` (local Oz) or ``warp_orchestrate_agency_task`` for the job.
3. Use ``warp_offload_shell`` for discrete audited shell commands.
4. Use ``warp_agent_run_cloud`` for long background remote runs (needs WARP_API_KEY).
5. Never dump secrets; never auto-confirm live spend via Warp.

Do **not** reinvent orchestration loops that Oz already handles.
""".strip()
