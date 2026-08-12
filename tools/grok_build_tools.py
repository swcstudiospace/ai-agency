"""Grok Build bottom layer — Hermes → Agno → Grok Build (SuperGrok).

Stack
-----
  Hermes Agent (top orchestrator)
       ↓ MCP
  Agno AgentOS (agents / teams / workflows)
       ↓ tools/grok_build_tools.py
  Grok Build CLI  ``grok``  (bottom — headless agent / shell offload)

Replaces the former Warp/Oz bottom layer. Uses the same SuperGrok subscription
already powering Agno models (``XAI_API_KEY`` / OAuth / Grok CLI auth).

Agents should **prefer offloading** multi-step shell, repo coding, and
specialized coding-agent work to Grok Build rather than inventing ad-hoc loops.

Auth
----
- Grok Build: SuperGrok login (``~/.grok/auth.json``) or ``XAI_API_KEY``
- Never log secrets.

Env
---
- ``GROK_BUILD_BIN`` — path to ``grok`` (default: PATH / ``~/.grok/bin/grok``)
- ``GROK_BUILD_MODEL`` — model id (default: ``grok-build`` or ``AGENCY_GROK_MODEL``)
- ``GROK_BUILD_DEFAULT_CWD`` — default workdir (repo root)
- ``GROK_BUILD_ALWAYS_APPROVE`` — ``1`` → ``--always-approve`` (default on for agents)
- ``GROK_BUILD_MAX_TURNS`` — default max turns for headless runs
- ``GROK_BUILD_PERMISSION_MODE`` — e.g. ``auto``, ``acceptEdits``, ``bypassPermissions``
- ``AGENCY_DISABLE_GROK_BUILD`` — disable auto toolbelt attach
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
_ARTIFACTS = _ROOT / "tmp" / "grok_build_runs"
_AGENTS_DIR = _ROOT / "configs" / "grok-build" / "agents"


def _which(name: str, env_key: str = "") -> str | None:
    if env_key:
        p = (env(env_key) or "").strip()
        if p and Path(p).exists():
            return p
    found = shutil.which(name)
    if found:
        return found
    home = Path.home() / ".grok" / "bin" / name
    if home.exists():
        return str(home)
    return None


def _grok_bin() -> str | None:
    return _which("grok", "GROK_BUILD_BIN")


def _default_cwd(cwd: str = "") -> str:
    return (cwd or env("GROK_BUILD_DEFAULT_CWD") or str(_ROOT)).strip()


def _default_model() -> str:
    """Model for headless runs. Empty → let Grok CLI use its configured default."""
    explicit = (env("GROK_BUILD_MODEL") or "").strip()
    if explicit:
        return explicit
    # Prefer not forcing a CLI-only id like "grok-build" when using XAI_API_KEY
    # (API key path exposes chat ids such as grok-4.5).
    return (env("AGENCY_GROK_MODEL") or env("XAI_MODEL") or "grok-4.5").strip()


def _always_approve() -> bool:
    v = (env("GROK_BUILD_ALWAYS_APPROVE") or "1").strip().lower()
    return v not in {"0", "false", "no", "off"}


def _max_turns(default: int = 24) -> int:
    try:
        return max(1, int((env("GROK_BUILD_MAX_TURNS") or str(default)).strip()))
    except ValueError:
        return default


def _run(
    argv: list[str],
    *,
    cwd: str = "",
    timeout_s: float = 600.0,
    env_extra: dict[str, str] | None = None,
) -> dict[str, Any]:
    run_env = os.environ.copy()
    # SuperGrok / xAI — prefer existing key; Grok Build also uses ~/.grok/auth.json
    try:
        from tools.xai_oauth_pkce import get_xai_token_or_fallback

        tok = get_xai_token_or_fallback()
        if tok and tok != "missing-xai-credentials" and not run_env.get("XAI_API_KEY"):
            run_env["XAI_API_KEY"] = tok
    except Exception:
        pass
    if env("XAI_API_KEY") and not run_env.get("XAI_API_KEY"):
        run_env["XAI_API_KEY"] = env("XAI_API_KEY") or ""
    # Prefer agency grok bin on PATH
    grok_home = str(Path.home() / ".grok" / "bin")
    run_env["PATH"] = grok_home + os.pathsep + run_env.get("PATH", "")
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
            "cmd": _redact_cmd(argv),
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
            "cmd": _redact_cmd(argv),
            "stdout": (e.stdout or "")[-20000:] if isinstance(e.stdout, str) else "",
            "duration_s": round(time.time() - started, 2),
        }
    except FileNotFoundError as e:
        return {"ok": False, "error": str(e), "cmd": _redact_cmd(argv)}
    except Exception as e:
        return {"ok": False, "error": str(e), "cmd": _redact_cmd(argv)}


def _redact_cmd(argv: list[str]) -> list[str]:
    out: list[str] = []
    skip_next = False
    for a in argv:
        if skip_next:
            out.append("***")
            skip_next = False
            continue
        if a in {"--api-key", "-k"} or a.startswith("xai-") or a.startswith("wk-"):
            if a in {"--api-key", "-k"}:
                out.append(a)
                skip_next = True
            else:
                out.append("***")
            continue
        out.append(a)
    return out


def _save_artifact(kind: str, payload: dict[str, Any]) -> str:
    _ARTIFACTS.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    path = _ARTIFACTS / f"{kind}_{stamp}_{int(time.time()) % 10000}.json"
    safe = json.loads(json.dumps(payload, default=str))
    path.write_text(json.dumps(safe, indent=2, default=str) + "\n", encoding="utf-8")
    return str(path)


def _auth_snapshot() -> dict[str, Any]:
    auth = Path.home() / ".grok" / "auth.json"
    return {
        "grok_auth_json": auth.is_file(),
        "xai_api_key_set": bool(env("XAI_API_KEY") or os.getenv("XAI_API_KEY")),
        "config_toml": (Path.home() / ".grok" / "config.toml").is_file(),
    }


def grok_build_status() -> dict[str, Any]:
    """Report Grok Build CLI availability + SuperGrok auth (no secrets)."""
    grok = _grok_bin()
    version = None
    if grok:
        r = _run([grok, "--version"], timeout_s=15)
        version = (r.get("stdout") or r.get("output") or "").strip()[:200]
    auth = _auth_snapshot()
    return {
        "ok": bool(grok),
        "stack": "Hermes → Agno → Grok Build",
        "grok_bin": grok,
        "version": version,
        "default_model": _default_model(),
        "default_cwd": _default_cwd(),
        "auth": auth,
        "agency_agents_dir": str(_AGENTS_DIR) if _AGENTS_DIR.is_dir() else None,
        "hint": None
        if grok
        else "Install: curl -fsSL https://x.ai/cli/install.sh | bash  (SuperGrok)",
    }


def grok_build_offload_shell(
    command: str,
    *,
    cwd: str = "",
    timeout_s: float = 300.0,
    reason: str = "",
    agent_name: str = "",
) -> dict[str, Any]:
    """Offload a shell command through the Grok Build bottom layer (audited).

    Prefer this over ad-hoc subprocess for multi-step ops so Hermes/Agno keep
    an audit trail under ``tmp/grok_build_runs/``.
    """
    command = (command or "").strip()
    if not command:
        return {"ok": False, "error": "command required"}
    lowered = command.lower()
    for bad in ("cat .env", "printenv", "aws configure"):
        if bad in lowered and "example" not in lowered:
            return {
                "ok": False,
                "error": "blocked_sensitive_command",
                "hint": "Do not dump secrets via grok_build_offload_shell",
            }
    if "api_key" in lowered and any(x in lowered for x in ("echo ", "cat ", "print")):
        return {"ok": False, "error": "blocked_sensitive_command"}

    argv = ["bash", "-lc", command]
    result = _run(argv, cwd=cwd, timeout_s=timeout_s)
    result["layer"] = "grok_build_offload_shell"
    result["reason"] = reason
    result["agent_name"] = agent_name
    result["artifact"] = _save_artifact("shell", result)
    result["note"] = (
        "Shell offload via Grok Build bottom layer — prefer grok_build_run for multi-step agent work"
    )
    return result


def grok_build_run(
    prompt: str,
    *,
    name: str = "",
    cwd: str = "",
    model: str = "",
    agent: str = "",
    agent_file: str = "",
    max_turns: int | None = None,
    always_approve: bool | None = None,
    permission_mode: str = "",
    output_format: str = "plain",
    system_prompt_override: str = "",
    rules: str = "",
    no_plan: bool = False,
    no_subagents: bool = False,
    timeout_s: float = 900.0,
    json_schema: str = "",
) -> dict[str, Any]:
    """Run **headless** Grok Build (``grok -p …``) — bottom-layer orchestration.

    Uses SuperGrok subscription (CLI auth and/or XAI_API_KEY).
    """
    grok = _grok_bin()
    if not grok:
        return {
            "ok": False,
            "error": "grok CLI not found",
            "hint": "curl -fsSL https://x.ai/cli/install.sh | bash",
        }
    prompt = (prompt or "").strip()
    if not prompt:
        return {"ok": False, "error": "prompt required"}

    cwd_use = _default_cwd(cwd)
    mid = (model or _default_model()).strip()
    turns = max_turns if max_turns is not None else _max_turns()
    approve = _always_approve() if always_approve is None else always_approve
    perm = (permission_mode or env("GROK_BUILD_PERMISSION_MODE") or "").strip()

    # Resolve custom agency agent profiles
    agent_path = (agent_file or "").strip()
    if not agent_path and agent:
        cand = _AGENTS_DIR / f"{agent}.md"
        if cand.is_file():
            agent_path = str(cand)
        else:
            # bare name — let grok resolve
            agent_path = ""

    argv: list[str] = [grok, "-p", prompt, "--cwd", cwd_use, "--output-format", output_format or "plain"]
    if mid:
        argv += ["-m", mid]
    if turns:
        argv += ["--max-turns", str(turns)]
    if approve:
        argv.append("--always-approve")
    if perm:
        argv += ["--permission-mode", perm]
    if agent_path:
        argv += ["--agent", agent_path]
    elif agent:
        argv += ["--agent", agent]
    if system_prompt_override:
        argv += ["--system-prompt-override", system_prompt_override]
    if rules:
        argv += ["--rules", rules]
    if no_plan:
        argv.append("--no-plan")
    if no_subagents:
        argv.append("--no-subagents")
    if json_schema:
        argv += ["--json-schema", json_schema]
    if name:
        # session title via rules annotation (no dedicated --name on all builds)
        argv += ["--rules", f"Session label: {name}. Agency HITL: no live spend, drafts only."]

    result = _run(argv, cwd=cwd_use, timeout_s=timeout_s)
    result["layer"] = "grok_build_run"
    result["prompt_preview"] = prompt[:300]
    result["model"] = mid
    result["agent"] = agent_path or agent or None
    result["artifact"] = _save_artifact("agent_run", result)
    return result


def grok_build_agent_stdio(
    *,
    model: str = "",
    always_approve: bool | None = None,
    agent_profile: str = "",
    timeout_s: float = 30.0,
) -> dict[str, Any]:
    """Probe ``grok agent`` headless/stdio availability (does not keep a long session)."""
    grok = _grok_bin()
    if not grok:
        return {"ok": False, "error": "grok CLI not found"}
    # Prefer a quick help probe — stdio is long-lived
    argv = [grok, "agent", "--help"]
    r = _run(argv, timeout_s=timeout_s)
    r["layer"] = "grok_build_agent_stdio_probe"
    r["note"] = "Use grok_build_run (-p headless) for scripted agency offload"
    r["artifact"] = _save_artifact("agent_probe", r)
    return r


def grok_build_inspect(cwd: str = "") -> dict[str, Any]:
    """Run ``grok inspect`` for project instructions / skills / MCP discovery."""
    grok = _grok_bin()
    if not grok:
        return {"ok": False, "error": "grok CLI not found"}
    r = _run([grok, "inspect"], cwd=cwd, timeout_s=60)
    r["layer"] = "grok_build_inspect"
    r["artifact"] = _save_artifact("inspect", r)
    return r


def grok_build_orchestrate_agency_task(
    goal: str,
    *,
    mode: str = "headless",
    name: str = "",
    agent: str = "agency-bottom",
    model: str = "",
    timeout_s: float = 900.0,
    max_turns: int | None = None,
) -> dict[str, Any]:
    """High-level offload: run Grok Build with agency HITL + dropshipping context.

    ``mode``: headless | shell
    """
    goal = (goal or "").strip()
    if not goal:
        return {"ok": False, "error": "goal required"}
    name = name or f"agency-{int(time.time())}"
    preamble = (
        "You are the Grok Build bottom-layer executor for the AI Dropshipping Agency. "
        "Stack: Hermes (top) → Agno AgentOS (middle) → you (bottom). "
        "Respect HITL: no live ad spend, no unsupervised supplier payments, Shopify drafts only. "
        "Never read or print .env secrets. Write useful artifacts under tmp/ when needed. "
        f"Repo: {_ROOT}. Goal:\n"
    )
    full = preamble + goal
    mode = (mode or "headless").lower()
    if mode == "shell":
        return grok_build_offload_shell(
            f"echo {shlex.quote('GROK_BUILD_SHELL_OFFLOAD: ' + goal[:500])}",
            reason=goal[:200],
            agent_name=name,
        )
    # Prefer custom agency agent profile when present
    agent_file = ""
    cand = _AGENTS_DIR / f"{agent}.md"
    if cand.is_file():
        agent_file = str(cand)
        agent = ""
    return grok_build_run(
        full,
        name=name,
        cwd=str(_ROOT),
        model=model,
        agent=agent,
        agent_file=agent_file,
        max_turns=max_turns,
        timeout_s=timeout_s,
    )


def get_grok_build_tools() -> list:
    return [
        grok_build_status,
        grok_build_offload_shell,
        grok_build_run,
        grok_build_orchestrate_agency_task,
        grok_build_inspect,
        grok_build_agent_stdio,
    ]


# ── instruction snippets for agents / teams / workflows ──────────────

GROK_BUILD_OFFLOAD_INSTRUCTIONS = """
## Grok Build bottom layer (mandatory preference)

Stack: **Hermes (top) → Agno agents/teams/workflows (middle) → Grok Build CLI (bottom)**.

Uses our **SuperGrok** subscription (same family as agent models). When work is multi-step shell,
repo coding, or benefits from a specialized coding agent:

1. Call ``grok_build_status`` once if unsure the CLI is available.
2. Prefer ``grok_build_run`` (headless ``grok -p``) or ``grok_build_orchestrate_agency_task`` for the job.
3. Use ``grok_build_offload_shell`` for discrete audited shell commands (pipeline scripts).
4. Custom agency agents live under ``configs/grok-build/agents/`` (pass via agent name).
5. Never dump secrets; never auto-confirm live spend via Grok Build.

Do **not** reinvent orchestration loops that Grok Build already handles.
Do **not** use Warp/Oz — that bottom layer was removed.
""".strip()
