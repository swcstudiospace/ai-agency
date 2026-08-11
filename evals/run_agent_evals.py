#!/usr/bin/env python3
"""Agent eval harness — schema presence, persona packs, skill scopes, smoke runs.

Usage:
  cd /root/src/repos/ai-agency && source .venv/bin/activate
  PYTHONPATH=. python -m evals.run_agent_evals
  PYTHONPATH=. python -m evals.run_agent_evals --live-scout   # optional LLM call
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agents.profiles import PROFILES
from agents.prompt_loader import list_personas, load_persona_sections
from tools.skills_loader import list_skill_names, skills_for
from tools.toolbelts import resolve_toolbelt


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--live-scout", action="store_true", help="Run a tiny Product Scout LLM call")
    args = ap.parse_args()

    fails: list[str] = []
    print("=== agency agent evals ===\n")

    # 1) Personas on disk for all profiles
    personas = set(list_personas())
    for p in PROFILES:
        if p.key not in personas:
            fails.append(f"missing persona pack: {p.key}")
            continue
        sec = load_persona_sections(p.key)
        for k in ("soul", "system", "output"):
            if len(sec.get(k) or "") < 200:
                fails.append(f"{p.key} {k} too short ({len(sec.get(k) or '')} chars)")
        print(f"  persona {p.key}: soul={len(sec['soul'])} system={len(sec['system'])} output={len(sec['output'])} examples={len(sec['examples'])}")

    # 2) Skills resolve
    known = set(list_skill_names())
    print(f"\n  skills available: {sorted(known)}")
    for p in PROFILES:
        missing = [s for s in p.skills if s not in known]
        if missing:
            fails.append(f"{p.key} unknown skills {missing}")
        else:
            sk = skills_for(*p.skills)
            if sk is None or len(sk.get_skill_names()) != len(set(p.skills)):
                fails.append(f"{p.key} skills_for mismatch {p.skills} -> {None if sk is None else sk.get_skill_names()}")
            else:
                print(f"  skills ok {p.key}: {list(sk.get_skill_names())}")

    # 3) Toolbelts resolve
    for p in PROFILES:
        try:
            tools = resolve_toolbelt(p.toolbelts)
            print(f"  tools {p.key}: {len(tools)} from {list(p.toolbelts)}")
        except Exception as e:
            fails.append(f"{p.key} toolbelt error: {e}")

    # 4) Import all agents + AgentOS
    try:
        from app.main import agent_os

        assert len(agent_os.agents) == 18
        assert len(agent_os.teams) == 7
        # spot-check product scout has skills scoped not global
        scout = next(a for a in agent_os.agents if a.name == "Product Scout")
        sn = set(scout.skills.get_skill_names()) if scout.skills else set()
        if "ugc-hooks" in sn:
            fails.append("Product Scout should not load ugc-hooks")
        if "product-scoring" not in sn:
            fails.append("Product Scout missing product-scoring")
        print(f"\n  AgentOS ok agents={len(agent_os.agents)} teams={len(agent_os.teams)} scout_skills={sorted(sn)}")
        # history flags
        hermes = next(a for a in agent_os.agents if a.name == "Hermes Ops")
        if not hermes.add_history_to_context:
            fails.append("Hermes Ops should have add_history_to_context")
        else:
            print("  Hermes Ops history enabled")
        if scout.output_schema is None:
            fails.append("Product Scout missing output_schema")
        else:
            print(f"  Product Scout output_schema={getattr(scout.output_schema, '__name__', scout.output_schema)}")
    except Exception as e:
        fails.append(f"AgentOS import failed: {e}")

    # 5) Optional live scout
    if args.live_scout:
        try:
            from agents.product_scout import product_scout

            r = product_scout.run(
                input=(
                    "Quick eval: propose 2 TEST-level desk mobility accessories for US dropshipping. "
                    "Use Parallel Search lightly. Keep response schema-complete but concise."
                )
            )
            content = getattr(r, "content", r)
            print("\n  live scout content type:", type(content))
            text = str(content)[:1500]
            print(text)
            Path(ROOT / "tmp" / "evals").mkdir(parents=True, exist_ok=True)
            (ROOT / "tmp" / "evals" / "live_scout_last.txt").write_text(text)
        except Exception as e:
            fails.append(f"live scout failed: {e}")

    print("\n=== summary ===")
    if fails:
        print(f"FAILED {len(fails)}")
        for f in fails:
            print(" -", f)
        return 1
    print("PASSED all structural evals")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
