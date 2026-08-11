"""Linear dual-write: GraphQL API + optional Hermes Linear connector + Kanban.

Critical path for agency autonomy: every product/supply/creative/spend milestone
creates or updates a Linear issue on team SWC / spectrumwebco (or LINEAR_TEAM_ID),
optionally attached to LINEAR_PROJECT_ID (AI Dropshipping Agency).
"""

from __future__ import annotations

import json
import os
import subprocess
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
import yaml

from tools.envutil import env, load_dotenv_files

LINEAR_API = "https://api.linear.app/graphql"
_CFG = Path("/root/.config/hermes-linear/config.yaml")
_DEFAULT_CONNECTOR = env("HERMES_LINEAR_URL", "http://127.0.0.1:8799")  # agency-local default


def _load_linear_cfg() -> Dict[str, Any]:
    load_dotenv_files()
    cfg: Dict[str, Any] = {}
    if _CFG.is_file():
        try:
            cfg = yaml.safe_load(_CFG.read_text(encoding="utf-8")) or {}
        except Exception:
            cfg = {}
    linear = cfg.get("linear") or {}
    return {
        "api_key": env("LINEAR_API_KEY") or env(str(linear.get("api_key_env") or "LINEAR_API_KEY")),
        "team_id": env("LINEAR_TEAM_ID") or str(linear.get("team_id") or ""),
        "team_key": env("LINEAR_TEAM_KEY") or str(linear.get("team_key") or "SWC"),
        "project_id": env("LINEAR_PROJECT_ID") or str(linear.get("project_id") or ""),
        "states": linear.get("states") or {},
        "board": ((cfg.get("hermes") or {}).get("board") or env("HERMES_KANBAN_BOARD", "eng")),
    }


def _headers() -> Optional[Dict[str, str]]:
    c = _load_linear_cfg()
    key = c["api_key"]
    if not key:
        return None
    return {"Authorization": key, "Content-Type": "application/json"}


def _gql(query: str, variables: Optional[dict] = None) -> Dict[str, Any]:
    headers = _headers()
    if not headers:
        return {"error": "LINEAR_API_KEY not set", "stub": True}
    with httpx.Client(timeout=45.0) as client:
        resp = client.post(
            LINEAR_API,
            headers=headers,
            json={"query": query, "variables": variables or {}},
        )
        data = resp.json()
    if "errors" in data:
        return {"error": data["errors"], "raw": data}
    return data.get("data") or data


def linear_status() -> Dict[str, Any]:
    c = _load_linear_cfg()
    if not c["api_key"]:
        return {"ok": False, "mode": "stub", "reason": "no LINEAR_API_KEY"}
    data = _gql("{ viewer { id name email } }")
    viewer = (data or {}).get("viewer") if isinstance(data, dict) else None
    return {
        "ok": bool(viewer),
        "mode": "live",
        "team_id": c["team_id"],
        "team_key": c["team_key"],
        "project_id": c.get("project_id") or None,
        "viewer": viewer,
        "states_configured": list((c.get("states") or {}).keys()),
    }


def create_linear_issue(
    title: str,
    description: str = "",
    team_id: Optional[str] = None,
    label: str = "agency",
    priority: int = 3,
    state_key: str = "unstarted",
    project_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Create Linear issue. Returns identifier/url/id (or stub)."""
    c = _load_linear_cfg()
    team = (team_id or c["team_id"] or "").strip()
    headers = _headers()
    if not headers or not team:
        stub_id = f"{c.get('team_key') or 'SWC'}-STUB-{uuid.uuid4().hex[:6].upper()}"
        print(f"[Linear STUB] {stub_id}: {title}")
        return {
            "identifier": stub_id,
            "id": stub_id,
            "url": "",
            "stub": True,
            "title": title,
        }

    state_id = (c.get("states") or {}).get(state_key)
    mutation = """
    mutation IssueCreate($input: IssueCreateInput!) {
      issueCreate(input: $input) {
        success
        issue { id identifier url title state { id name } project { id name } }
      }
    }
    """
    inp: Dict[str, Any] = {
        "teamId": team,
        "title": title[:250],
        "description": description or "",
        "priority": max(0, min(4, int(priority))),
    }
    if state_id:
        inp["stateId"] = state_id
    proj = (project_id or c.get("project_id") or "").strip()
    if proj:
        inp["projectId"] = proj

    data = _gql(mutation, {"input": inp})
    issue = (((data or {}).get("issueCreate") or {}).get("issue")) or {}
    if not issue:
        return {"error": data, "title": title}
    out = {
        "identifier": issue.get("identifier"),
        "id": issue.get("id"),
        "url": issue.get("url"),
        "title": issue.get("title"),
        "state": (issue.get("state") or {}).get("name"),
        "project": (issue.get("project") or {}).get("name"),
        "stub": False,
        "label": label,
    }
    print(f"[Linear] Created {out['identifier']}: {title}")
    # best-effort link to canonical GitHub repo (ai-agency), not agent_runtime
    try:
        gh = link_issue_to_github_repo(
            issue_id=str(out["id"]),
            identifier=str(out.get("identifier") or ""),
            title=title,
            description=description or "",
            linear_url=str(out.get("url") or ""),
        )
        out["github"] = gh
    except Exception as e:
        out["github"] = {"ok": False, "error": str(e)}
    # best-effort kanban mirror
    try:
        mirror = ensure_kanban_card(
            title=f"{out['identifier']} {title}"[:200],
            description=description,
            linear_issue_id=str(out["id"]),
            linear_identifier=str(out["identifier"]),
        )
        out["kanban"] = mirror
    except Exception as e:
        out["kanban"] = {"ok": False, "error": str(e)}
    return out


def link_issue_to_github_repo(
    *,
    issue_id: str,
    identifier: str = "",
    title: str = "",
    description: str = "",
    linear_url: str = "",
    repo: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a GitHub issue on LINEAR_GITHUB_REPO (default swcstudiospace/ai-agency)
    and attach it on the Linear issue. Avoids default Linear sync to agent_runtime.
    """
    import subprocess
    import urllib.error
    import urllib.request

    load_dotenv_files()
    repo = (repo or env("LINEAR_GITHUB_REPO") or "swcstudiospace/ai-agency").strip()
    if env("LINEAR_GITHUB_LINK", "1").lower() in {"0", "false", "no"}:
        return {"ok": False, "skipped": True, "reason": "LINEAR_GITHUB_LINK disabled"}

    try:
        tok = subprocess.check_output(["gh", "auth", "token"], text=True, timeout=15).strip()
    except Exception as e:
        return {"ok": False, "error": f"gh auth token failed: {e}"}

    body = (
        f"Synced from Linear [{identifier or issue_id}]({linear_url}).\n\n"
        f"{(description or '')[:2500]}\n\n"
        f"---\n_Canonical agency repo: `{repo}`._\n"
    )
    payload = json.dumps(
        {"title": f"{identifier + ': ' if identifier else ''}{title}"[:250], "body": body}
    ).encode()
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/issues",
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {tok}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
            "User-Agent": "ai-agency-linear-link",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            gi = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return {"ok": False, "error": f"github create {e.code}: {e.read().decode()[:200]}"}

    gh_url = gi.get("html_url") or ""
    gh_num = gi.get("number")
    if not gh_url:
        return {"ok": False, "error": "no github url", "raw": gi}

    # Drop any existing agent_runtime attachments first
    try:
        att = _gql(
            """query($id: String!) {
              issue(id: $id) { attachments { nodes { id url title } } }
            }""",
            {"id": issue_id},
        )
        for a in (((att or {}).get("issue") or {}).get("attachments") or {}).get("nodes") or []:
            if "agent_runtime" in (a.get("url") or ""):
                _gql(f'mutation {{ attachmentDelete(id: "{a["id"]}") {{ success }} }}')
    except Exception:
        pass

    link = _gql(
        """mutation($issueId: String!, $url: String!) {
          attachmentLinkGitHubIssue(issueId: $issueId, url: $url) {
            success
            attachment { id title url }
          }
        }""",
        {"issueId": issue_id, "url": gh_url},
    )
    success = bool(((link or {}).get("attachmentLinkGitHubIssue") or {}).get("success"))
    if not success:
        link = _gql(
            """mutation($issueId: String!, $url: String!, $title: String!) {
              attachmentLinkURL(issueId: $issueId, url: $url, title: $title) {
                success
                attachment { id title url }
              }
            }""",
            {
                "issueId": issue_id,
                "url": gh_url,
                "title": f"#{gh_num} {title}"[:100],
            },
        )
        success = bool(((link or {}).get("attachmentLinkURL") or {}).get("success"))

    return {
        "ok": success,
        "repo": repo,
        "github_url": gh_url,
        "github_number": gh_num,
        "link": link,
    }


def comment_linear_issue(issue_id: str, body: str) -> Dict[str, Any]:
    """issue_id may be UUID or identifier (SWC-123) — resolves if needed."""
    headers = _headers()
    if not headers:
        print(f"[Linear STUB] comment {issue_id}")
        return {"ok": True, "stub": True}
    resolved = resolve_issue_id(issue_id)
    if not resolved:
        return {"error": f"could not resolve issue {issue_id}"}
    mutation = """
    mutation CommentCreate($input: CommentCreateInput!) {
      commentCreate(input: $input) { success comment { id url } }
    }
    """
    data = _gql(mutation, {"input": {"issueId": resolved, "body": body}})
    return {"ok": True, "data": data, "issue_id": resolved}


def update_linear_issue(
    issue_id: str,
    state: str = "",
    comment: str = "",
    title: Optional[str] = None,
) -> Dict[str, Any]:
    """Update state by state_key (unstarted/started/completed/...) and/or comment."""
    headers = _headers()
    c = _load_linear_cfg()
    if not headers:
        print(f"[Linear STUB] Updated {issue_id} → {state}: {comment[:80]}")
        return {"ok": True, "stub": True, "issue_id": issue_id, "state": state}

    resolved = resolve_issue_id(issue_id)
    if not resolved:
        return {"error": f"could not resolve issue {issue_id}"}

    state_id = None
    if state:
        # allow key or raw name
        states = c.get("states") or {}
        state_id = states.get(state) or states.get(state.lower())
        if not state_id:
            # try match by fetching team states — fallback comment only
            pass

    results: Dict[str, Any] = {"issue_id": resolved}
    if state_id or title:
        mutation = """
        mutation IssueUpdate($id: String!, $input: IssueUpdateInput!) {
          issueUpdate(id: $id, input: $input) {
            success
            issue { id identifier url state { name } title }
          }
        }
        """
        inp: Dict[str, Any] = {}
        if state_id:
            inp["stateId"] = state_id
        if title:
            inp["title"] = title
        data = _gql(mutation, {"id": resolved, "input": inp})
        results["update"] = data
    if comment:
        results["comment"] = comment_linear_issue(resolved, f"**State:** {state or 'n/a'}\n\n{comment}")
    print(f"[Linear] Updated {issue_id} → {state}")
    return {"ok": True, **results}


def resolve_issue_id(issue_id_or_key: str) -> Optional[str]:
    s = (issue_id_or_key or "").strip()
    if not s:
        return None
    # UUID-ish
    if len(s) >= 32 and "-" in s and not s.upper().startswith("SPE"):
        return s
    # identifier SPE-123
    data = _gql(
        """
        query($q: String!) {
          issueSearch(query: $q, first: 5) {
            nodes { id identifier }
          }
        }
        """,
        {"q": s},
    )
    if isinstance(data, dict) and data.get("stub"):
        return s
    nodes = (((data or {}).get("issueSearch") or {}).get("nodes")) or []
    for n in nodes:
        if str(n.get("identifier", "")).upper() == s.upper() or n.get("id") == s:
            return n.get("id")
    # fallback filter
    data2 = _gql(
        """
        query($filter: IssueFilter) {
          issues(filter: $filter, first: 5) {
            nodes { id identifier }
          }
        }
        """,
        {"filter": {"number": {"eq": _number_from_identifier(s)}} } if _number_from_identifier(s) else {"filter": {}},
    )
    nodes2 = (((data2 or {}).get("issues") or {}).get("nodes")) or []
    for n in nodes2:
        if str(n.get("identifier", "")).upper() == s.upper():
            return n.get("id")
    return nodes[0]["id"] if nodes else (s if len(s) > 20 else None)


def _number_from_identifier(s: str) -> Optional[int]:
    if "-" not in s:
        return None
    tail = s.split("-")[-1]
    return int(tail) if tail.isdigit() else None


def list_linear_issues(limit: int = 10, state_key: str = "") -> Dict[str, Any]:
    c = _load_linear_cfg()
    team = c["team_id"]
    if not _headers() or not team:
        return {"issues": [], "stub": True}
    filt: Dict[str, Any] = {"team": {"id": {"eq": team}}}
    state_id = (c.get("states") or {}).get(state_key) if state_key else None
    if state_id:
        filt["state"] = {"id": {"eq": state_id}}
    data = _gql(
        """
        query($filter: IssueFilter, $first: Int) {
          issues(filter: $filter, first: $first, orderBy: updatedAt) {
            nodes { id identifier title url priority state { name type } updatedAt }
          }
        }
        """,
        {"filter": filt, "first": max(1, min(50, limit))},
    )
    nodes = (((data or {}).get("issues") or {}).get("nodes")) or []
    return {"issues": nodes, "count": len(nodes)}


def ensure_kanban_card(
    title: str,
    description: str = "",
    linear_issue_id: str = "",
    linear_identifier: str = "",
) -> Dict[str, Any]:
    """Mirror to Hermes kanban board when CLI available."""
    board = _load_linear_cfg()["board"] or "eng"
    key = f"linear:{linear_identifier or linear_issue_id or uuid.uuid4().hex[:8]}"
    body = description or ""
    if linear_identifier:
        body = f"<!-- hermes:linear={linear_identifier} -->\n{body}"
    cmd = [
        "hermes",
        "kanban",
        "--board",
        board,
        "create",
        title[:200],
        "--triage",
        "--idempotency-key",
        key,
        "--json",
    ]
    if body.strip():
        cmd.extend(["--body", body[:4000]])
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            env={**os.environ},
        )
    except FileNotFoundError:
        return {"ok": False, "error": "hermes CLI not found"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "kanban timeout"}
    out = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode != 0:
        return {"ok": False, "error": out[-800:], "code": proc.returncode}
    try:
        data = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        data = {"raw": proc.stdout}
    return {"ok": True, "result": data, "idempotency_key": key, "board": board}


def agency_track(
    title: str,
    description: str = "",
    stage: str = "research",
    priority: int = 3,
) -> Dict[str, Any]:
    """One-call dual-write for autonomous pipeline milestones."""
    prefix = {
        "research": "[Scout]",
        "supply": "[Supply]",
        "creative": "[Creative]",
        "compliance": "[Compliance]",
        "growth": "[Growth]",
        "spend": "[Spend HITL]",
        "ops": "[Ops]",
        "retention": "[Retention]",
    }.get(stage, "[Agency]")
    full_title = f"{prefix} {title}".strip()
    state_key = "started" if stage in {"growth", "supply", "creative"} else "unstarted"
    if stage == "compliance":
        state_key = "started"
    issue = create_linear_issue(
        title=full_title,
        description=description,
        priority=priority,
        state_key=state_key,
        label=stage,
    )
    return issue


def get_linear_tools() -> list:
    return [
        linear_status,
        create_linear_issue,
        update_linear_issue,
        comment_linear_issue,
        list_linear_issues,
        agency_track,
        ensure_kanban_card,
    ]
