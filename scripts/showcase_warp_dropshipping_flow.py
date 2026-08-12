#!/usr/bin/env python3
"""Showcase: how Agno agents run Warp CLI inside the Autonomous Dropshipping Flow.

Demonstrates the stack:

  Hermes (top) → Agno agents (middle) → Warp Oz / offload (bottom)

Stages (HITL-safe — no spend, no auto-email send, no live publish):
  1. warp_status
  2. Agent toolbelt proves warp_* tools are attached
  3. warp_offload_shell — audited shell steps of the dropshipping pipeline
  4. oz agent run attempt (needs oz login / WARP_API_KEY for full agent)
  5. Artifact report under tmp/runs/warp_dropshipping_showcase_*

Usage:
  PYTHONPATH=. python -m scripts.showcase_warp_dropshipping_flow
  PYTHONPATH=. python -m scripts.showcase_warp_dropshipping_flow --try-oz-agent
  PYTHONPATH=. python -m scripts.showcase_warp_dropshipping_flow --skip-locate
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from tools.envutil import load_dotenv_files

load_dotenv_files()

from tools.warp_tools import (  # noqa: E402
    WARP_OFFLOAD_INSTRUCTIONS,
    warp_agent_run,
    warp_offload_shell,
    warp_orchestrate_agency_task,
    warp_status,
)


def utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def banner(title: str) -> None:
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Warp CLI × Autonomous Dropshipping showcase")
    ap.add_argument("--try-oz-agent", action="store_true", help="Attempt oz agent run (needs login)")
    ap.add_argument("--skip-locate", action="store_true", help="Skip Parallel locate (faster demo)")
    ap.add_argument("--product", default="Fold-Flat Adjustable Aluminum Laptop Stand")
    args = ap.parse_args(argv)

    stamp = utc()
    stages: list[dict[str, Any]] = []
    out_dir = ROOT / "tmp" / "runs"
    out_dir.mkdir(parents=True, exist_ok=True)

    banner("STACK: Hermes → Agno → Warp (Oz bottom layer)")
    print(
        """
  Hermes Agent          top orchestrator (MCP client)
         │
         ▼
  Agno AgentOS          30 agents · warp + hermes_bridge toolbelts
    e.g. Product Scout, Supplier Sourcer, Hermes Ops
         │  warp_offload_shell / warp_agent_run / warp_orchestrate_agency_task
         ▼
  Warp Oz CLI (`oz`)    multi-step agent + MCP to :7777/:7788/:7790
  warp_offload_shell    audited single commands → tmp/warp_runs/
"""
    )
    print("Injected agent instructions (excerpt):")
    print(WARP_OFFLOAD_INSTRUCTIONS[:400].strip(), "…\n")

    # ── 1) status ──────────────────────────────────────────────
    banner("[1/6] warp_status — CLI + auth probe")
    status = warp_status()
    stages.append({"stage": "warp_status", "result": status})
    print(json.dumps({k: status.get(k) for k in status if k != "whoami"}, indent=2))
    who = status.get("whoami") or {}
    print("whoami.ok =", who.get("ok"), "| api_key_set =", status.get("warp_api_key_set"))
    if not who.get("ok") and not status.get("warp_api_key_set"):
        print(
            "NOTE: Oz not logged in — full `oz agent run` needs `oz login` or WARP_API_KEY.\n"
            "      Showcase continues with warp_offload_shell (always available) + dry agent path."
        )

    # ── 2) toolbelt proof ──────────────────────────────────────
    banner("[2/6] Agent toolbelts include Warp (Product Scout / Supplier Sourcer)")
    try:
        from agents.profiles import PROFILES
        from tools.toolbelts import resolve_toolbelt

        for key in ("product_scout", "supplier_sourcer", "hermes_ops"):
            prof = next(p for p in PROFILES if p.key == key)
            tools = resolve_toolbelt(list(prof.toolbelts) + ["warp"])
            # factory auto-adds warp; resolve profile belts + warp
            from agents._factory import build_agent  # may be heavy

            # lighter: check TOOLBELTS and factory pattern
            names = {getattr(t, "__name__", str(t)) for t in tools}
            has = sorted(n for n in names if n.startswith("warp_"))
            print(f"  {key}: warp tools visible when belt attached → {has or 'via factory auto-attach'}")
        from tools.toolbelts import TOOLBELTS

        warp_names = [getattr(t, "__name__", str(t)) for t in TOOLBELTS.get("warp", [])]
        print("  TOOLBELTS['warp'] =", warp_names)
        stages.append({"stage": "toolbelts", "warp_tools": warp_names, "ok": bool(warp_names)})
    except Exception as e:
        print("  toolbelt check error:", e)
        stages.append({"stage": "toolbelts", "ok": False, "error": str(e)})

    # ── 3) offload: unit econ check (fast) ─────────────────────
    banner("[3/6] warp_offload_shell — economics sanity (agent would call this)")
    r = warp_offload_shell(
        "cd /root/src/repos/ai-agency && source .venv/bin/activate && "
        "PYTHONPATH=. python - <<'PY'\n"
        "from tools.economics_tools import contribution_margin\n"
        "r = contribution_margin(49.99, 14.0, 5.5, ad_spend_per_order=18.0)\n"
        "print('CM%', round(r['contribution_margin_pct']*100,1), 'healthy', r['healthy'])\n"
        "print('decision', 'GO' if r['contribution_margin_pct']>=0.28 else 'TEST')\n"
        "PY",
        reason="Product Scout / Pricing: unit economics for GO laptop stand",
        agent_name="product_scout",
        timeout_s=60,
    )
    stages.append({"stage": "offload_economics", "ok": r.get("ok"), "artifact": r.get("artifact"), "output": (r.get("output") or "")[-500:]})
    print("ok =", r.get("ok"), "| duration =", r.get("duration_s"), "s")
    print((r.get("output") or r.get("stderr") or "")[-400:])
    print("artifact:", r.get("artifact"))

    # ── 4) offload: post_locate (uses prior locate if present) ─
    banner("[4/6] warp_offload_shell — post_locate (outreach + shipping plan)")
    r2 = warp_offload_shell(
        "cd /root/src/repos/ai-agency && source .venv/bin/activate && "
        "export PYTHONPATH=. PYTHONUNBUFFERED=1 && "
        "python -u -m scripts.autonomous_post_locate --top-suppliers 1 --no-linear",
        reason="Supplier Sourcer: post-locate after rank/locate",
        agent_name="supplier_sourcer",
        timeout_s=120,
    )
    stages.append(
        {
            "stage": "offload_post_locate",
            "ok": r2.get("ok"),
            "artifact": r2.get("artifact"),
            "output_tail": (r2.get("output") or "")[-800:],
        }
    )
    print("ok =", r2.get("ok"), "| duration =", r2.get("duration_s"), "s")
    print((r2.get("output") or "")[-600:])
    print("artifact:", r2.get("artifact"))

    # ── 5) optional locate via offload ─────────────────────────
    if not args.skip_locate:
        banner("[5/6] warp_offload_shell — product locate (may call Parallel)")
        # Only if we have PARALLEL key - otherwise skip quickly
        if os.getenv("PARALLEL_API_KEY"):
            r3 = warp_offload_shell(
                "cd /root/src/repos/ai-agency && source .venv/bin/activate && "
                f'export PYTHONPATH=. PYTHONUNBUFFERED=1 && '
                f'python -u -m scripts.autonomous_product_locate --product "{args.product}" '
                f"--processor core --no-linear",
                reason="Supplier Sourcer: locate suppliers for GO SKU",
                agent_name="supplier_sourcer",
                timeout_s=600,
            )
            stages.append(
                {
                    "stage": "offload_locate",
                    "ok": r3.get("ok"),
                    "artifact": r3.get("artifact"),
                    "output_tail": (r3.get("output") or "")[-800:],
                }
            )
            print("ok =", r3.get("ok"), "| duration =", r3.get("duration_s"), "s")
            print((r3.get("output") or "")[-500:])
        else:
            print("PARALLEL_API_KEY not set — skipping live locate")
            stages.append({"stage": "offload_locate", "ok": False, "skipped": True})
    else:
        print("\n[5/6] skipped locate (--skip-locate)")
        stages.append({"stage": "offload_locate", "skipped": True})

    # ── 6) Oz agent run (auth-dependent) ───────────────────────
    banner("[6/6] oz agent run — multi-step Warp agent (bottom orchestration)")
    oz_prompt = (
        "You are the bottom-layer Warp Oz agent for AI Dropshipping Agency. "
        "Task: In the repo /root/src/repos/ai-agency, list the latest files under "
        "tmp/runs/ matching product_rank_*, product_locate_*, post_locate_*. "
        "Print a 5-line summary of the autonomous dropshipping loop "
        "(rank → locate → post_locate → HITL). Do NOT read .env or secrets. "
        "Do NOT install packages. Finish with DONE."
    )
    if args.try_oz_agent or status.get("warp_api_key_set") or (who.get("ok")):
        print("Invoking warp_agent_run / oz agent run …")
        oz_r = warp_agent_run(
            oz_prompt,
            name="agency-dropshipping-showcase",
            cwd=str(ROOT),
            timeout_s=180,
            output_format="pretty",
        )
        stages.append(
            {
                "stage": "oz_agent_run",
                "ok": oz_r.get("ok"),
                "exit_code": oz_r.get("exit_code"),
                "artifact": oz_r.get("artifact"),
                "output_tail": (oz_r.get("output") or "")[-1200:],
                "error": oz_r.get("error"),
            }
        )
        print("ok =", oz_r.get("ok"), "| exit =", oz_r.get("exit_code"))
        print((oz_r.get("output") or oz_r.get("error") or "")[-800:])
    else:
        # Dry-run: show exact command agents would fire
        print("DRY-RUN (not logged in). Agents would call:")
        print(
            f'  oz agent run -p "{oz_prompt[:80]}…" '
            f"-C {ROOT} --mcp configs/warp/agency-mcp.json"
        )
        print("\nTo enable live Oz agents:")
        print("  oz login")
        print("  # or: export WARP_API_KEY=wk-…")
        print("  PYTHONPATH=. python -m scripts.showcase_warp_dropshipping_flow --try-oz-agent")
        # Still record orchestrate helper shape
        orch = {
            "tool": "warp_orchestrate_agency_task",
            "mode": "local",
            "goal": "Run post_locate for top GO SKU and summarize suppliers",
            "callable": True,
        }
        stages.append({"stage": "oz_agent_run", "ok": False, "dry_run": True, "orchestrate": orch})

    # ── workflow guidance ─────────────────────────────────────
    banner("Workflow guidance (agents see this on each step)")
    try:
        from workflows._warp import with_warp_guidance

        print(with_warp_guidance("Locate suppliers for GO SKUs.")[:500])
    except Exception as e:
        print("workflow note:", e)

    # ── report ────────────────────────────────────────────────
    payload = {
        "meta": {
            "stamp": stamp,
            "title": "Warp CLI × Autonomous Dropshipping Flow showcase",
            "stack": "Hermes → Agno → Warp/Oz",
            "product": args.product,
        },
        "warp_status": status,
        "stages": stages,
        "how_agents_use_warp": {
            "automatic": "agents/_factory.py attaches warp toolbelt + WARP_OFFLOAD_INSTRUCTIONS",
            "workflows": "product_discovery_locate + full_product_lifecycle use with_warp_guidance()",
            "preferred_tools": [
                "warp_offload_shell — single audited commands (pipeline scripts)",
                "warp_agent_run — multi-step Oz agent (coding/shell loops)",
                "warp_orchestrate_agency_task — goal + agency MCP",
            ],
            "artifacts": "tmp/warp_runs/*.json",
        },
        "next_operator_steps": [
            "oz login  # or set WARP_API_KEY",
            "Re-run with --try-oz-agent for full Oz multi-step agent",
            "Keep HITL: no spend, no auto-email send, Shopify drafts only",
        ],
    }
    jp = out_dir / f"warp_dropshipping_showcase_{stamp}.json"
    mp = out_dir / f"warp_dropshipping_showcase_{stamp}.md"
    jp.write_text(json.dumps(payload, indent=2, default=str) + "\n")

    lines = [
        f"# Warp CLI × Autonomous Dropshipping Flow — {stamp}",
        "",
        "## Stack",
        "",
        "```text",
        "Hermes → Agno (30 agents) → Warp Oz / warp_offload_shell",
        "```",
        "",
        f"- Oz bin: `{status.get('oz_bin')}`",
        f"- Warp TUI: `{status.get('warp_tui_bin')}`",
        f"- Auth: api_key_set={status.get('warp_api_key_set')} whoami_ok={(status.get('whoami') or {}).get('ok')}",
        "",
        "## Stages run",
        "",
    ]
    for s in stages:
        mark = "✅" if s.get("ok") else ("⏭️" if s.get("skipped") or s.get("dry_run") else "⚠️")
        lines.append(f"- {mark} **{s.get('stage')}** artifact=`{s.get('artifact', '—')}`")
    lines += [
        "",
        "## How agents call Warp in the dropshipping loop",
        "",
        "1. **Product Scout** ranks niches (Parallel) — may `warp_offload_shell` for scripts",
        "2. **Supplier Sourcer** `warp_offload_shell('python -m scripts.autonomous_product_locate …')`",
        "3. **Post-locate** `warp_offload_shell('python -m scripts.autonomous_post_locate …')`",
        "4. Multi-step coding/refactors → `warp_agent_run` / `warp_orchestrate_agency_task`",
        "5. Artifacts land in `tmp/warp_runs/` for Hermes audit",
        "",
        "## Report JSON",
        f"`{jp}`",
        "",
    ]
    mp.write_text("\n".join(lines) + "\n")

    banner("SHOWCASE DONE")
    print(mp)
    print(jp)
    ok_n = sum(1 for s in stages if s.get("ok"))
    print(f"stages_ok={ok_n}/{len(stages)}")
    # success if offload stages worked
    core_ok = any(s.get("stage") == "offload_economics" and s.get("ok") for s in stages)
    return 0 if core_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
