"""Hermes reverse bridge — expose Hermes capabilities to Agno agents.

Runs as MCP (Streamable HTTP) + REST on :7790.
Agents call these tools; bridge executes against:
  - Playwright browser (Hermes-class browsing)
  - Hermes skills tree (~/.hermes/skills + external)
  - Hermes MEMORY.md / USER.md
  - KIP shared memory (local nexus + ICP capsule export)
  - Job queue for heavy computer-use style tasks
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from mcp.server.fastmcp import FastMCP

HERMES_HOME = Path(os.getenv("HERMES_HOME") or Path.home() / ".hermes")
SKILLS_DIRS = [
    HERMES_HOME / "skills",
    Path("/root/agent-skills"),
    _ROOT / "skills",
]
MEMORY_DIR = HERMES_HOME / "memories"
JOBS_DIR = _ROOT / "tmp" / "bridge_jobs"
PROPOSALS = _ROOT / "skills" / "_proposals"

mcp = FastMCP(
    name="hermes-bridge",
    instructions=(
        "Reverse bridge: Agno agency agents use Hermes-class tools — browser, "
        "skills (self-improving), shared memory, and KIP/Anda-style graph memory. "
        "Prefer kip_remember/kip_recall for durable cross-agent facts. "
        "Use hermes_browser_* for live web inspection. "
        "Use hermes_skill_* to load and propose skill improvements."
    ),
)


def _token_ok(auth_header: str = "") -> bool:
    # tools themselves don't see headers; REST layer checks. MCP localhost open.
    return True


# ─── Browser (Playwright) ────────────────────────────────────


def _browser_run(fn):
    """Run sync Playwright off the asyncio loop (MCP handlers are async)."""
    import concurrent.futures

    def _inner():
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as e:
            return {"error": f"playwright not installed: {e}"}
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                try:
                    page = browser.new_page()
                    return fn(page)
                finally:
                    browser.close()
        except Exception as e:
            msg = str(e)
            if "Executable doesn't exist" in msg or "browserType.launch" in msg:
                return {
                    "error": "chromium not installed",
                    "fix": "Run: python -m playwright install chromium",
                    "detail": msg[:300],
                }
            return {"error": msg}

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(_inner).result(timeout=120)


@mcp.tool()
def hermes_browser_navigate(url: str, wait_until: str = "domcontentloaded", timeout_ms: int = 30000) -> Dict[str, Any]:
    """Navigate to URL and return title, final URL, and text excerpt (Hermes-class browser)."""

    def op(page):
        page.goto(url, wait_until=wait_until, timeout=timeout_ms)
        title = page.title()
        text = page.inner_text("body")[:8000]
        return {
            "ok": True,
            "url": page.url,
            "title": title,
            "text_excerpt": text,
            "length": len(text),
        }

    return _browser_run(op)


@mcp.tool()
def hermes_browser_snapshot(url: str, selector: str = "body", timeout_ms: int = 30000) -> Dict[str, Any]:
    """Load URL and return accessibility-ish text snapshot of selector."""

    def op(page):
        page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
        loc = page.locator(selector).first
        html = loc.inner_html()[:12000] if loc.count() else ""
        text = loc.inner_text()[:8000] if loc.count() else page.inner_text("body")[:8000]
        return {"ok": True, "url": page.url, "title": page.title(), "text": text, "html_excerpt": html[:4000]}

    return _browser_run(op)


@mcp.tool()
def hermes_browser_screenshot(url: str, path: str = "", full_page: bool = False) -> Dict[str, Any]:
    """Screenshot a URL to tmp/bridge_jobs/ (for agent evidence)."""
    JOBS_DIR.mkdir(parents=True, exist_ok=True)
    out = Path(path) if path else JOBS_DIR / f"shot_{uuid.uuid4().hex[:10]}.png"

    def op(page):
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        out.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(out), full_page=full_page)
        return {"ok": True, "path": str(out), "url": page.url, "title": page.title()}

    return _browser_run(op)


@mcp.tool()
def hermes_browser_extract_links(url: str, limit: int = 40) -> Dict[str, Any]:
    """Extract links from a page."""

    def op(page):
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        hrefs = page.eval_on_selector_all(
            "a[href]",
            "els => els.map(e => ({href: e.href, text: (e.innerText||'').trim().slice(0,120)}))",
        )
        return {"ok": True, "url": page.url, "links": (hrefs or [])[: max(1, min(200, limit))]}

    return _browser_run(op)


# ─── Skills (self-improving) ─────────────────────────────────


def _iter_skills() -> List[Dict[str, Any]]:
    found = []
    seen = set()
    for root in SKILLS_DIRS:
        if not root.is_dir():
            continue
        for skill_md in root.rglob("SKILL.md"):
            # skip huge node trees
            if "node_modules" in skill_md.parts:
                continue
            name = skill_md.parent.name
            key = str(skill_md.resolve())
            if key in seen:
                continue
            seen.add(key)
            try:
                text = skill_md.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            desc = ""
            m = re.search(r"^description:\s*[\"']?(.+?)[\"']?\s*$", text, re.M)
            if m:
                desc = m.group(1).strip()
            found.append(
                {
                    "name": name,
                    "path": str(skill_md),
                    "dir": str(skill_md.parent),
                    "description": desc[:300],
                    "bytes": len(text),
                    "source_root": str(root),
                }
            )
    return sorted(found, key=lambda x: x["name"])


@mcp.tool()
def hermes_skill_list(limit: int = 100, query: str = "") -> Dict[str, Any]:
    """List Hermes self-improving skills (local + external registries on disk)."""
    skills = _iter_skills()
    q = (query or "").lower().strip()
    if q:
        skills = [s for s in skills if q in s["name"].lower() or q in (s.get("description") or "").lower()]
    return {"count": len(skills), "skills": skills[: max(1, min(500, limit))], "roots": [str(r) for r in SKILLS_DIRS]}


@mcp.tool()
def hermes_skill_read(name: str, max_chars: int = 12000) -> Dict[str, Any]:
    """Read a skill SKILL.md by name (first match)."""
    name = (name or "").strip()
    for s in _iter_skills():
        if s["name"] == name or s["name"].replace("_", "-") == name:
            text = Path(s["path"]).read_text(encoding="utf-8", errors="replace")
            return {
                "ok": True,
                "name": s["name"],
                "path": s["path"],
                "content": text if len(text) <= max_chars else text[:max_chars] + "\n…[truncated]",
                "truncated": len(text) > max_chars,
            }
    return {"ok": False, "error": f"skill not found: {name}"}


@mcp.tool()
def hermes_skill_search(query: str, limit: int = 20) -> Dict[str, Any]:
    """Search skill names/descriptions/bodies for a query."""
    q = (query or "").lower().strip()
    if not q:
        return {"error": "query required"}
    hits = []
    for s in _iter_skills():
        try:
            body = Path(s["path"]).read_text(encoding="utf-8", errors="replace")[:50000].lower()
        except OSError:
            body = ""
        score = 0
        if q in s["name"].lower():
            score += 5
        if q in (s.get("description") or "").lower():
            score += 3
        if q in body:
            score += 1
        if score:
            hits.append({**s, "score": score})
    hits.sort(key=lambda x: -x["score"])
    return {"query": query, "hits": hits[: max(1, min(100, limit))]}


@mcp.tool()
def hermes_skill_propose(
    name: str,
    rationale: str,
    patch_markdown: str,
    skill_name: str = "",
) -> Dict[str, Any]:
    """Propose a skill improvement (self-improving loop). Writes to skills/_proposals/ for Hermes curator review.

    Does NOT auto-apply to production skills — Hermes/curator merges after review.
    """
    PROPOSALS.mkdir(parents=True, exist_ok=True)
    sid = f"prop_{uuid.uuid4().hex[:10]}"
    target = skill_name or name
    path = PROPOSALS / f"{sid}_{re.sub(r'[^a-zA-Z0-9_-]+','_', target)[:40]}.md"
    doc = (
        f"# Skill proposal `{sid}`\n\n"
        f"- target_skill: `{target}`\n"
        f"- created_at: {time.time()}\n"
        f"- status: pending_review\n\n"
        f"## Rationale\n\n{rationale}\n\n"
        f"## Proposed patch / content\n\n{patch_markdown}\n"
    )
    path.write_text(doc)
    # dual-write Linear if available
    linear = None
    try:
        from tools.linear_tools import agency_track

        linear = agency_track(
            title=f"Skill proposal: {target}",
            description=doc[:4000],
            stage="ops",
            priority=4,
        )
    except Exception as e:
        linear = {"error": str(e)}
    # Hermes self-improve → KIP shared mind
    kip = None
    try:
        from kip_memory.brain import learn_from_skill_proposal

        kip = learn_from_skill_proposal(
            skill_name=target,
            rationale=rationale,
            proposal_id=sid,
            path=str(path),
        )
    except Exception as e:
        kip = {"error": str(e)}
    return {"ok": True, "proposal_id": sid, "path": str(path), "linear": linear, "kip": kip}


@mcp.tool()
def hermes_skill_list_proposals(limit: int = 20) -> Dict[str, Any]:
    """List pending skill improvement proposals."""
    PROPOSALS.mkdir(parents=True, exist_ok=True)
    files = sorted(PROPOSALS.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    return {
        "proposals": [
            {"name": f.name, "path": str(f), "mtime": f.stat().st_mtime, "bytes": f.stat().st_size}
            for f in files[: max(1, min(100, limit))]
        ]
    }


# ─── Hermes memory files ─────────────────────────────────────


@mcp.tool()
def hermes_memory_read(which: str = "memory") -> Dict[str, Any]:
    """Read Hermes persistent memory (memory|user)."""
    which = (which or "memory").lower()
    path = MEMORY_DIR / ("USER.md" if which == "user" else "MEMORY.md")
    if not path.is_file():
        return {"ok": False, "error": f"missing {path}"}
    text = path.read_text(encoding="utf-8", errors="replace")
    return {"ok": True, "path": str(path), "content": text, "chars": len(text)}


@mcp.tool()
def hermes_memory_append(entry: str, which: str = "memory") -> Dict[str, Any]:
    """Append a durable memory entry (Hermes MEMORY.md style). Also mirrors into KIP."""
    entry = (entry or "").strip()
    if not entry:
        return {"error": "entry required"}
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    path = MEMORY_DIR / ("USER.md" if (which or "").lower() == "user" else "MEMORY.md")
    with path.open("a", encoding="utf-8") as f:
        f.write("\n§\n" + entry + "\n")
    kip = None
    try:
        from kip_memory.brain import learn_from_hermes_memory_entry

        kip = learn_from_hermes_memory_entry(entry)
    except Exception as e:
        try:
            from kip_memory.nexus import remember

            kip = remember(entry, kind="Insight", name=entry[:60])
        except Exception as e2:
            kip = {"error": str(e), "fallback_error": str(e2)}
    return {"ok": True, "path": str(path), "kip": kip}


@mcp.tool()
def kip_execute(command: str) -> Dict[str, Any]:
    """Execute a KIP command (FIND/UPSERT/SEARCH/DESCRIBE PRIMER/EXPORT)."""
    from kip_memory.brain import execute as brain_execute

    return brain_execute(command)


@mcp.tool()
def kip_remember(text: str, kind: str = "Insight", name: str = "", link: str = "") -> Dict[str, Any]:
    """Remember a fact in shared KIP graph (Anda/KIP; ICP exportable)."""
    from kip_memory.nexus import remember

    links = [link] if link else None
    return {"ok": True, "stored": remember(text, kind=kind, name=name, links=links)}


@mcp.tool()
def kip_recall(query: str, limit: int = 15) -> Dict[str, Any]:
    """Recall from shared KIP graph by query."""
    from kip_memory.brain import recall

    return recall(query, limit=limit)


@mcp.tool()
def anda_brain_formation(text: str, counterparty: str = "", agent: str = "agency") -> Dict[str, Any]:
    """Encode text/conversation into shared KIP graph (Anda Brain formation)."""
    from kip_memory.brain import formation

    return formation(text, counterparty=counterparty, agent=agent)


@mcp.tool()
def anda_brain_recall(query: str, limit: int = 15) -> Dict[str, Any]:
    """Recall from shared KIP brain before answering."""
    from kip_memory.brain import recall

    return recall(query, limit=limit)


@mcp.tool()
def anda_brain_sleep() -> Dict[str, Any]:
    """Run sleep/maintenance cycle on shared KIP graph."""
    from kip_memory.brain import maintenance

    return maintenance()


@mcp.tool()
def anda_brain_bootstrap() -> Dict[str, Any]:
    """Load Genesis capsules into the Cognitive Nexus."""
    from kip_memory.brain import bootstrap_genesis

    return bootstrap_genesis()


@mcp.tool()
def kip_export_icp(label: str = "agency") -> Dict[str, Any]:
    """Export knowledge capsule + ICP/cloud push (KIP_ICP_MODE)."""
    from kip_memory.cloud import push_capsule
    from kip_memory.nexus import export_capsule

    cap = export_capsule(label=label)
    if cap.get("ok") and cap.get("path"):
        cap["cloud"] = push_capsule(Path(cap["path"]), meta={"label": label})
    return cap


# ─── Computer-use job queue (Hermes session pickup) ──────────


@mcp.tool()
def hermes_computer_use_request(
    goal: str,
    app: str = "",
    notes: str = "",
    priority: int = 3,
) -> Dict[str, Any]:
    """Queue a computer-use / desktop task for Hermes top orchestrator to execute.

    Agno agents cannot drive the live Hermes CUA session in-process; this creates
    a job file + Linear issue. Hermes should poll hermes_computer_use_list_jobs.
    """
    JOBS_DIR.mkdir(parents=True, exist_ok=True)
    jid = f"cu_{uuid.uuid4().hex[:10]}"
    job = {
        "id": jid,
        "type": "computer_use",
        "status": "pending",
        "goal": goal,
        "app": app,
        "notes": notes,
        "priority": priority,
        "created_at": time.time(),
        "result": None,
    }
    path = JOBS_DIR / f"{jid}.json"
    path.write_text(json.dumps(job, indent=2))
    linear = None
    try:
        from tools.linear_tools import agency_track

        linear = agency_track(
            title=f"Computer-use job {jid}: {goal[:80]}",
            description=json.dumps(job, indent=2)[:4000],
            stage="ops",
            priority=priority,
        )
    except Exception as e:
        linear = {"error": str(e)}
    return {"ok": True, "job_id": jid, "path": str(path), "linear": linear}


@mcp.tool()
def hermes_computer_use_list_jobs(status: str = "pending", limit: int = 20) -> Dict[str, Any]:
    """List computer-use jobs for Hermes to pick up or agents to check."""
    JOBS_DIR.mkdir(parents=True, exist_ok=True)
    jobs = []
    for p in sorted(JOBS_DIR.glob("cu_*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            j = json.loads(p.read_text())
        except Exception:
            continue
        if status and j.get("status") != status and status != "all":
            continue
        jobs.append(j)
        if len(jobs) >= limit:
            break
    return {"jobs": jobs, "count": len(jobs)}


@mcp.tool()
def hermes_computer_use_complete(job_id: str, result: str, status: str = "done") -> Dict[str, Any]:
    """Mark a computer-use job complete (called by Hermes after CUA execution)."""
    path = JOBS_DIR / f"{job_id}.json"
    if not path.is_file():
        # try search
        matches = list(JOBS_DIR.glob(f"{job_id}*.json"))
        path = matches[0] if matches else path
    if not path.is_file():
        return {"error": f"job not found: {job_id}"}
    j = json.loads(path.read_text())
    j["status"] = status
    j["result"] = result
    j["completed_at"] = time.time()
    path.write_text(json.dumps(j, indent=2))
    return {"ok": True, "job": j}


@mcp.tool()
def hermes_bridge_health() -> Dict[str, Any]:
    """Health of reverse bridge + KIP + skills roots."""
    skills_n = len(_iter_skills())
    from kip_memory.nexus import find_concepts

    concepts = find_concepts(limit=5)
    return {
        "ok": True,
        "service": "hermes-bridge",
        "port": int(os.getenv("HERMES_BRIDGE_PORT", "7790")),
        "skills_indexed": skills_n,
        "memory_dir": str(MEMORY_DIR),
        "kip_concepts_sample": len(concepts),
        "jobs_dir": str(JOBS_DIR),
        "playwright": True,
    }


def get_mcp() -> FastMCP:
    return mcp
