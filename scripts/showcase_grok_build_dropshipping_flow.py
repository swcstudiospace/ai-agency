#!/usr/bin/env python3
"""Showcase: how Agno agents run Grok Build inside the Autonomous Dropshipping Flow.

Demonstrates the stack:

  Hermes (top) → Agno agents (middle) → Grok Build (bottom · SuperGrok)

Stages (HITL-safe — no spend, no auto-email send, no live publish):
  1. grok_build_status
  2. Agent toolbelt proves grok_build_* tools are attached
  3. grok_build_offload_shell — audited shell steps of the dropshipping pipeline
  4. grok_build_run headless agent (SuperGrok)
  5. Artifact report under tmp/runs/grok_build_dropshipping_showcase_*

Usage:
  PYTHONPATH=. python -m scripts.showcase_grok_build_dropshipping_flow
  PYTHONPATH=. python -m scripts.showcase_grok_build_dropshipping_flow --try-grok-agent
  PYTHONPATH=. python -m scripts.showcase_grok_build_dropshipping_flow --skip-locate
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from tools.envutil import load_dotenv_files

load_dotenv_files()

from tools.grok_build_tools import (  # noqa: E402
    GROK_BUILD_OFFLOAD_INSTRUCTIONS,
    grok_build_offload_shell,
    grok_build_run,
    grok_build_status,
)


def utc() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def banner(title: str) -> None:
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Grok Build × Autonomous Dropshipping showcase")
    ap.add_argument("--try-grok-agent", action="store_true", help="Run live headless grok -p")
    ap.add_argument("--skip-locate", action="store_true", help="Skip Parallel locate (faster demo)")
    ap.add_argument("--product", default="Fold-Flat Adjustable Aluminum Laptop Stand")
    args = ap.parse_args(argv)

    stamp = utc()
    stages: list[dict[str, Any]] = []
    out_dir = ROOT / "tmp" / "runs"
    out_dir.mkdir(parents=True, exist_ok=True)

    banner("STACK: Hermes → Agno → Grok Build (SuperGrok)")
    print(
        """
  Hermes Agent          top orchestrator (MCP client)
         │
         ▼
  Agno AgentOS          30 agents · grok_build + hermes_bridge toolbelts
    e.g. Product Scout, Supplier Sourcer, Hermes Ops
         │  grok_build_offload_shell / grok_build_run / grok_build_orchestrate_agency_task
         ▼
  Grok Build CLI (`grok`)   headless SuperGrok coding agent
  grok_build_offload_shell  audited single commands → tmp/grok_build_runs/
"""
    )
    print("Injected agent instructions (excerpt):")
    print(GROK_BUILD_OFFLOAD_INSTRUCTIONS[:420].strip(), "…\n")

    banner("[1/6] grok_build_status — CLI + SuperGrok auth")
    status = grok_build_status()
    stages.append({"stage": "grok_build_status", "result": status, "ok": status.get("ok")})
    print(json.dumps({k: status.get(k) for k in ("ok", "grok_bin", "version", "default_model", "auth")}, indent=2))

    banner("[2/6] Agent toolbelts include Grok Build")
    try:
        from tools.toolbelts import TOOLBELTS, resolve_toolbelt

        for key in ("product_scout", "supplier_sourcer", "hermes_ops"):
            from agents.profiles import PROFILES

            prof = next(p for p in PROFILES if p.key == key)
            tools = resolve_toolbelt(list(prof.toolbelts) + ["grok_build"])
            names = sorted(n for n in {getattr(t, "__name__", str(t)) for t in tools} if n.startswith("grok_build_"))
            print(f"  {key}: {names}")
        gb_names = [getattr(t, "__name__", str(t)) for t in TOOLBELTS.get("grok_build", [])]
        print("  TOOLBELTS['grok_build'] =", gb_names)
        stages.append({"stage": "toolbelts", "grok_build_tools": gb_names, "ok": bool(gb_names)})
    except Exception as e:
        print("  toolbelt check error:", e)
        stages.append({"stage": "toolbelts", "ok": False, "error": str(e)})

    banner("[3/6] grok_build_offload_shell — economics sanity")
    r = grok_build_offload_shell(
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
    stages.append(
        {
            "stage": "offload_economics",
            "ok": r.get("ok"),
            "artifact": r.get("artifact"),
            "output": (r.get("output") or "")[-500:],
        }
    )
    print("ok =", r.get("ok"), "| duration =", r.get("duration_s"), "s")
    print((r.get("output") or "")[-400:])
    print("artifact:", r.get("artifact"))

    banner("[4/6] grok_build_offload_shell — post_locate")
    r2 = grok_build_offload_shell(
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

    if not args.skip_locate and os.getenv("PARALLEL_API_KEY"):
        banner("[5/6] grok_build_offload_shell — product locate")
        r3 = grok_build_offload_shell(
            "cd /root/src/repos/ai-agency && source .venv/bin/activate && "
            f'export PYTHONPATH=. PYTHONUNBUFFERED=1 && '
            f'python -u -m scripts.autonomous_product_locate --product "{args.product}" '
            f"--processor core --no-linear",
            reason="Supplier Sourcer: locate suppliers for GO SKU",
            agent_name="supplier_sourcer",
            timeout_s=600,
        )
        stages.append({"stage": "offload_locate", "ok": r3.get("ok"), "artifact": r3.get("artifact")})
        print("ok =", r3.get("ok"), "| duration =", r3.get("duration_s"), "s")
    else:
        print("\n[5/6] skipped locate")
        stages.append({"stage": "offload_locate", "skipped": True})

    banner("[6/6] grok_build_run — headless SuperGrok agent")
    prompt = (
        "You are the Grok Build bottom-layer executor for AI Dropshipping Agency. "
        "In /root/src/repos/ai-agency list the newest files under tmp/runs/ matching "
        "product_rank_*, product_locate_*, post_locate_*. "
        "Print a 5-line summary of the loop rank → locate → post_locate → HITL. "
        "Do NOT read .env. Finish with DONE."
    )
    if args.try_grok_agent or status.get("ok"):
        print("Invoking grok_build_run (headless) …")
        agent_file = str(ROOT / "configs" / "grok-build" / "agents" / "agency-bottom.md")
        gb = grok_build_run(
            prompt,
            name="agency-dropshipping-showcase",
            cwd=str(ROOT),
            agent_file=agent_file if Path(agent_file).is_file() else "",
            max_turns=6,
            timeout_s=180,
            output_format="plain",
        )
        stages.append(
            {
                "stage": "grok_build_run",
                "ok": gb.get("ok"),
                "exit_code": gb.get("exit_code"),
                "artifact": gb.get("artifact"),
                "output_tail": (gb.get("output") or "")[-1200:],
                "error": gb.get("error"),
            }
        )
        print("ok =", gb.get("ok"), "| exit =", gb.get("exit_code"), "| duration =", gb.get("duration_s"))
        print((gb.get("output") or gb.get("error") or "")[-900:])
    else:
        stages.append({"stage": "grok_build_run", "ok": False, "skipped": True})
        print("Grok CLI missing — install from https://x.ai/cli/install.sh")

    try:
        from workflows._grok_build import with_grok_build_guidance

        banner("Workflow guidance")
        print(with_grok_build_guidance("Locate suppliers for GO SKUs.")[:500])
    except Exception as e:
        print("workflow note:", e)

    payload = {
        "meta": {
            "stamp": stamp,
            "title": "Grok Build × Autonomous Dropshipping Flow showcase",
            "stack": "Hermes → Agno → Grok Build",
            "product": args.product,
        },
        "grok_build_status": status,
        "stages": stages,
        "how_agents_use_grok_build": {
            "automatic": "agents/_factory.py attaches grok_build + GROK_BUILD_OFFLOAD_INSTRUCTIONS",
            "workflows": "product_discovery_locate + full_product_lifecycle use with_grok_build_guidance()",
            "preferred_tools": [
                "grok_build_offload_shell — pipeline scripts",
                "grok_build_run — multi-step SuperGrok coding agent",
                "grok_build_orchestrate_agency_task — goal + agency agent profile",
            ],
            "artifacts": "tmp/grok_build_runs/*.json",
            "custom_agents": "configs/grok-build/agents/*.md",
        },
    }
    jp = out_dir / f"grok_build_dropshipping_showcase_{stamp}.json"
    mp = out_dir / f"grok_build_dropshipping_showcase_{stamp}.md"
    jp.write_text(json.dumps(payload, indent=2, default=str) + "\n")
    lines = [
        f"# Grok Build × Autonomous Dropshipping Flow — {stamp}",
        "",
        "```text",
        "Hermes → Agno (30 agents) → Grok Build (SuperGrok)",
        "```",
        "",
        f"- grok: `{status.get('grok_bin')}`",
        f"- version: `{status.get('version')}`",
        f"- model: `{status.get('default_model')}`",
        f"- auth: `{status.get('auth')}`",
        "",
        "## Stages",
        "",
    ]
    for s in stages:
        mark = "✅" if s.get("ok") else ("⏭️" if s.get("skipped") else "⚠️")
        lines.append(f"- {mark} **{s.get('stage')}** artifact=`{s.get('artifact', '—')}`")
    lines += ["", f"JSON: `{jp}`", ""]
    mp.write_text("\n".join(lines) + "\n")

    banner("SHOWCASE DONE")
    print(mp)
    print(jp)
    ok_n = sum(1 for s in stages if s.get("ok"))
    print(f"stages_ok={ok_n}/{len(stages)}")
    core_ok = any(s.get("stage") == "offload_economics" and s.get("ok") for s in stages)
    return 0 if core_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
