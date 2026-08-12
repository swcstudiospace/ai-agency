#!/usr/bin/env python3
"""Fail CI if README drifts from the real repo (living documentation gate).

Checks:
  - Critical paths mentioned in README exist on disk
  - Scale numbers (agents/teams/workflows) match app.main
  - Required sections present
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text(encoding="utf-8")


def main() -> int:
    fails: list[str] = []

    required_sections = [
        r"## Quick start",
        r"## Control planes",
        r"## Product pipeline",
        r"## CI/CD",
        r"## Documentation",
        r"## Safety",
    ]
    for pat in required_sections:
        if not re.search(pat, README, re.I):
            fails.append(f"missing section matching {pat}")

    # Paths that README should keep honest
    must_exist = [
        "scripts/autonomous_product_rank.py",
        "scripts/autonomous_product_locate.py",
        "scripts/autonomous_post_locate.py",
        "scripts/e2e_agency_run.py",
        "docs-site/package.json",
        "storefront-oxygen/package.json",
        "agency-cockpit/package.json",
        "docs/POST_LOCATE_AND_FULFILLMENT.md",
        "docs/GROK_BUILD_AND_CODERABBIT.md",
        "tools/grok_build_tools.py",
        "tools/coderabbit_tools.py",
        ".coderabbit.yaml",
        "configs/grok-build/agents/agency-bottom.md",
        "scripts/showcase_grok_build_dropshipping_flow.py",
        "docs/PRODUCT_LOCATE.md",
        ".github/workflows/ci.yml",
        "tests/",
        "requirements.txt",
        "requirements-dev.txt",
    ]
    for rel in must_exist:
        p = ROOT / rel
        if not p.exists():
            fails.append(f"README references missing path: {rel}")
        # if README mentions the path, good; if not, still require existence for core paths
        if rel.endswith(".py") and rel.split("/")[-1].replace(".py", "") not in README.replace("_", ""):
            # softer: scripts should be mentioned by name
            name = Path(rel).stem
            if name.startswith("autonomous_") or name.startswith("e2e_"):
                if name not in README and name.replace("_", "-") not in README:
                    if f"scripts.{name}" not in README and name not in README:
                        fails.append(f"README should mention script {name}")

    # Scale numbers from source of truth
    try:
        import os

        os.environ.setdefault("XAI_API_KEY", "missing-ci-placeholder")
        os.environ.setdefault("AGENCY_DISABLE_HERMES_BRIDGE", "1")
        os.environ.setdefault("AGENCY_DISABLE_ANDA_BRAIN", "1")
        os.environ.setdefault("AGENCY_DISABLE_ANDA_KNOWLEDGE", "1")
        os.environ.setdefault("AGENCY_DISABLE_ANALYTICS", "1")
        os.environ.setdefault("LINEAR_GITHUB_LINK", "0")
        sys.path.insert(0, str(ROOT))
        from app.main import agent_os

        n_a, n_t, n_w = len(agent_os.agents), len(agent_os.teams), len(agent_os.workflows)
        for label, n in (("agents", n_a), ("teams", n_t), ("workflows", n_w)):
            # README should contain the number near the word
            if not re.search(rf"\b{n}\b[^\n]{{0,40}}{label}|\b{label}\b[^\n]{{0,40}}\b{n}\b", README, re.I):
                # also accept **30** agents style already counted separately
                if str(n) not in README:
                    fails.append(f"README missing scale number {n} for {label} (live={n_a}/{n_t}/{n_w})")
        # Hard: must claim correct counts somewhere
        if str(n_a) not in README:
            fails.append(f"README must include agent count {n_a}")
        if str(n_t) not in README:
            fails.append(f"README must include team count {n_t}")
        if str(n_w) not in README:
            fails.append(f"README must include workflow count {n_w}")
    except Exception as e:
        fails.append(f"could not import agent_os for scale check: {e}")

    # Living doc policy
    if "living" not in README.lower() and "update the README" not in README.lower():
        fails.append("README should state living-doc / keep-README-updated policy")

    # Domain + brand
    if "ego.engineer" not in README:
        fails.append("README should mention ego.engineer")

    print("README freshness check")
    if fails:
        print(f"FAILED {len(fails)}")
        for f in fails:
            print(" -", f)
        return 1
    print("PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
