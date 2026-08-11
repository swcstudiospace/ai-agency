"""Anda Brain–style formation / recall / sleep on top of local KIP nexus.

Mirrors ldclabs Anda Brain HTTP semantics enough for Hermes+Agno:
  POST formation  → encode conversation/events into graph
  POST recall     → associative retrieval before answering
  POST maintenance→ NREM-like consolidate + light decay
  EXPORT          → capsules + ICP-ready receipts

When ANDA_NEXUS_URL is set, prefers remote anda_cognitive_nexus_server
(POST /kip) and falls back to local SQLite nexus.
"""

from __future__ import annotations

import json
import os
import re
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from kip_memory import nexus as local

_ROOT = Path(__file__).resolve().parents[1]
_SEED = Path(__file__).resolve().parent / "capsules_seed"
_STATE = Path(__file__).resolve().parent / "data" / "brain_state.json"


def _nexus_url() -> str:
    return (os.getenv("ANDA_NEXUS_URL") or os.getenv("KIP_NEXUS_URL") or "").rstrip("/")


def remote_kip(command: str = "", method: str = "execute_kip", **extra) -> Dict[str, Any]:
    """Call remote Cognitive Nexus HTTP JSON-RPC if configured."""
    base = _nexus_url()
    if not base:
        return {"ok": False, "error": "ANDA_NEXUS_URL not set"}
    import httpx

    params: Dict[str, Any] = dict(extra)
    if command:
        # anda_cognitive_nexus_server expects params with KIP payload
        params.setdefault("command", command)
        # some versions want the raw string as params directly
    body: Dict[str, Any] = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params if params else {"command": command},
    }
    # Official server: params is the KIP request object — try command field first
    if command and method == "execute_kip":
        body["params"] = {"command": command, **extra}

    headers = {"content-type": "application/json"}
    key = os.getenv("ANDA_NEXUS_API_KEY") or os.getenv("API_KEY")
    if key:
        headers["Authorization"] = f"Bearer {key}"
    try:
        with httpx.Client(timeout=60.0) as client:
            r = client.post(base.rstrip("/") + "/kip", json=body, headers=headers)
            try:
                data = r.json()
            except Exception:
                data = {"raw": r.text[:2000]}
            # Retry alternate param shapes
            if r.status_code >= 400 or (isinstance(data, dict) and data.get("error")):
                for alt in (
                    {"jsonrpc": "2.0", "id": 1, "method": method, "params": command},
                    {"jsonrpc": "2.0", "id": 1, "method": "kip", "params": {"command": command}},
                ):
                    r2 = client.post(base.rstrip("/") + "/kip", json=alt, headers=headers)
                    try:
                        d2 = r2.json()
                    except Exception:
                        continue
                    if r2.status_code < 400 and not (isinstance(d2, dict) and d2.get("error")):
                        return {"ok": True, "status": r2.status_code, "data": d2, "remote": True}
            ok = r.status_code < 400 and not (isinstance(data, dict) and data.get("error"))
            return {"ok": ok, "status": r.status_code, "data": data, "remote": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def execute(command: str) -> Dict[str, Any]:
    """Execute KIP command — remote preferred, local fallback."""
    if _nexus_url():
        r = remote_kip(command)
        if r.get("ok"):
            return r
        # fall through with note
        local_res = local.execute_kip(command)
        local_res["_remote_error"] = r.get("error") or r.get("data")
        return local_res
    return local.execute_kip(command)


def bootstrap_genesis() -> Dict[str, Any]:
    """Load Genesis + core capsules from kip_memory/capsules_seed (KIP repo)."""
    from kip_memory.dual_write import dual_upsert, ensure_agency_schema_remote

    schema = ensure_agency_schema_remote()
    loaded = []
    if not _SEED.is_dir():
        local.execute_kip("DESCRIBE PRIMER")
        return {"ok": True, "loaded": [], "note": "no seed dir; primer only", "schema": schema}
    for path in sorted(_SEED.glob("*.kip")):
        text = path.read_text(encoding="utf-8", errors="replace")
        name = path.stem
        dual_upsert(
            "Capsule",
            name,
            attributes={"source_file": path.name, "body_preview": text[:1500], "full_chars": len(text)},
            metadata={"source": f"capsule:{path.name}", "author": "genesis", "confidence": 1.0},
        )
        for m in re.finditer(r'type:\s*"([^"]+)"', text):
            dual_upsert(
                "$ConceptType" if m.group(1).startswith("$") else "Insight",
                f"TypeHint:{m.group(1)}" if not m.group(1).startswith("$") else m.group(1),
                attributes={"from_capsule": name, "hint_type": m.group(1)},
                metadata={"source": f"capsule:{path.name}", "author": "genesis", "confidence": 1.0},
            )
        # Prefer registering real concept types on remote
        from kip_memory.dual_write import ensure_remote_type

        for m in re.finditer(r'type:\s*"([^"]+)"', text):
            ensure_remote_type(m.group(1), f"From capsule {name}")
        loaded.append(path.name)
    primer = local.execute_kip("DESCRIBE PRIMER")
    remote_primer = remote_kip("DESCRIBE PRIMER") if _nexus_url() else None
    return {
        "ok": True,
        "loaded": loaded,
        "primer": primer,
        "remote_primer_ok": bool((remote_primer or {}).get("ok")),
        "schema": schema,
    }


def formation(
    messages: Any,
    *,
    counterparty: str = "",
    agent: str = "agency",
    space: str = "dropshipping",
    timestamp: Optional[str] = None,
) -> Dict[str, Any]:
    """Encode conversation → episodic Event + extracted Insights/Preferences.

    Dual-writes local SQLite + remote Anda Cognitive Nexus when ANDA_NEXUS_URL is set.
    `messages`: list[{role,content}] or plain string.
    """
    from kip_memory.dual_write import dual_upsert, ensure_agency_schema_remote

    ensure_agency_schema_remote()
    ts = timestamp or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    if isinstance(messages, str):
        text = messages.strip()
        turns = [{"role": "user", "content": text}]
    elif isinstance(messages, list):
        turns = messages
        parts = []
        for m in turns:
            if isinstance(m, dict):
                parts.append(f"{m.get('role', 'user')}: {m.get('content', '')}")
            else:
                parts.append(str(m))
        text = "\n".join(parts)
    else:
        text = str(messages)
        turns = [{"role": "user", "content": text}]

    event_name = f"Event {ts} {uuid.uuid4().hex[:6]}"
    meta_base = {"source": f"formation:{space}", "author": agent or "$self", "confidence": 0.85}
    ev = dual_upsert(
        "Event",
        event_name,
        attributes={
            "description": text[:4000],
            "counterparty": counterparty,
            "agent": agent,
            "space": space,
            "timestamp": ts,
            "turn_count": len(turns),
        },
        metadata=meta_base,
    )

    extracted: List[dict] = []
    remote_ok_flags: List[bool] = [bool(ev.get("remote_ok"))]

    for m in re.finditer(
        r"(?i)\b(?:prefer|likes?|love|want|need|always|never)\b[^.!?\n]{0,120}",
        text,
    ):
        snippet = m.group(0).strip()
        pref = dual_upsert(
            "Preference",
            snippet[:80],
            attributes={"description": snippet, "from_event": event_name},
            metadata={"source": f"formation:{space}", "author": agent, "confidence": 0.7},
            propositions=[("derived_from", "Event", event_name)],
        )
        remote_ok_flags.append(bool(pref.get("remote_ok")))
        extracted.append({"kind": "Preference", **(pref.get("local") or {}), "remote_ok": pref.get("remote_ok")})

    for m in re.finditer(
        r"(?i)\b(?:learned|insight|decision|concluded|because|kill if|go if|test if)\b[^.!?\n]{0,160}",
        text,
    ):
        snippet = m.group(0).strip()
        ins = dual_upsert(
            "Insight",
            snippet[:80],
            attributes={"description": snippet, "from_event": event_name},
            metadata={"source": f"formation:{space}", "author": agent, "confidence": 0.75},
            propositions=[("derived_from", "Event", event_name)],
        )
        remote_ok_flags.append(bool(ins.get("remote_ok")))
        extracted.append({"kind": "Insight", **(ins.get("local") or {}), "remote_ok": ins.get("remote_ok")})

    for m in re.finditer(r"\b([A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+){1,4})\b", text):
        name = m.group(1)
        if len(name) < 8 or name in {"Event", "Insight", "Preference"}:
            continue
        if any(w in name for w in ("The ", "This ", "When ", "From ")):
            continue
        if sum(1 for x in extracted if x.get("kind") == "Product") >= 3:
            break
        pr = dual_upsert(
            "Product",
            name[:80],
            attributes={"mentioned_in": event_name, "description": name},
            metadata={"source": f"formation:{space}", "author": agent, "confidence": 0.55},
            propositions=[("mentioned_in", "Event", event_name)],
        )
        remote_ok_flags.append(bool(pr.get("remote_ok")))
        extracted.append({"kind": "Product", **(pr.get("local") or {}), "remote_ok": pr.get("remote_ok")})

    if counterparty:
        dual_upsert(
            "Person",
            counterparty,
            attributes={"last_seen": ts, "description": counterparty},
            metadata={"source": f"formation:{space}", "author": agent, "confidence": 0.9},
            propositions=[("involved_in", "Event", event_name)],
        )

    _touch_state("formation", event_name)
    return {
        "ok": True,
        "event": ev.get("local") or ev,
        "event_remote_ok": ev.get("remote_ok"),
        "extracted": extracted[:20],
        "space": space,
        "engine": "dual_write",
        "remote_ok_ratio": (sum(1 for x in remote_ok_flags if x) / len(remote_ok_flags)) if remote_ok_flags else 0,
    }


def _remote_search_concepts(query: str, limit: int = 15) -> List[Dict[str, Any]]:
    if not _nexus_url() or not query:
        return []
    # escape quotes in query
    q = query.replace('"', " ").strip()[:120]
    cmd = f'SEARCH CONCEPT "{q}" LIMIT {max(1, min(50, limit))}'
    r = remote_kip(cmd)
    if not r.get("ok"):
        return []
    data = r.get("data") or {}
    result = data.get("result")
    out = []
    if isinstance(result, list):
        for node in result:
            if not isinstance(node, dict):
                continue
            out.append(
                {
                    "id": node.get("id"),
                    "type": node.get("type"),
                    "name": node.get("name"),
                    "attributes": node.get("attributes") or {},
                    "metadata": node.get("metadata") or {},
                    "source_engine": "remote_anda_db",
                }
            )
    return out


def recall(
    query: str,
    *,
    counterparty: str = "",
    limit: int = 15,
    include_related: bool = True,
) -> Dict[str, Any]:
    """Associative recall — merges local graph + remote Anda SEARCH CONCEPT."""
    q = (query or "").strip()
    concepts = local.find_concepts(query=q, limit=limit)
    if counterparty:
        concepts = concepts + local.find_concepts(query=counterparty, limit=5)
    # remote authoritative search
    remote_hits = _remote_search_concepts(q, limit=limit)
    if counterparty:
        remote_hits = remote_hits + _remote_search_concepts(counterparty, limit=5)

    related = []
    if include_related:
        related = local.find_related(q, limit=limit)
        if counterparty:
            related = related + local.find_related(counterparty, limit=10)

    seen = set()
    uniq = []
    for c in list(remote_hits) + list(concepts):
        key = c.get("id") or f"{c.get('type')}:{c.get('name')}"
        if key in seen:
            continue
        seen.add(key)
        uniq.append(c)

    lines = [f"# KIP Recall: {q}", ""]
    if remote_hits:
        lines.append(f"_Remote Anda DB hits: {len(remote_hits)}_")
        lines.append("")
    for c in uniq[:limit]:
        desc = (c.get("attributes") or {}).get("description") or ""
        conf = (c.get("metadata") or {}).get("confidence", "")
        eng = c.get("source_engine") or "local"
        lines.append(f"- [{c.get('type')}] **{c.get('name')}** conf={conf} ({eng})")
        if desc:
            lines.append(f"  {desc[:300]}")
    if related:
        lines.append("")
        lines.append("## Relations")
        for r in related[:limit]:
            s = r.get("subject") or {}
            o = r.get("object") or {}
            lines.append(f"- ({s.get('name')}) -[{r.get('predicate')}]-> ({o.get('name')})")

    _touch_state("recall", q)
    return {
        "ok": True,
        "query": q,
        "concepts": uniq[:limit],
        "related": related[:limit],
        "remote_hits": len(remote_hits),
        "context_markdown": "\n".join(lines),
        "engine": "dual_recall",
    }


def maintenance(*, max_events: int = 50) -> Dict[str, Any]:
    """NREM-lite sleep: mark events consolidated, reinforce repeated insights, decay stale.

    Dual-writes consolidated Insights to remote Anda nexus.
    """
    from kip_memory.dual_write import dual_upsert

    events = local.find_concepts(type_="Event", limit=max_events)
    consolidated = 0
    remote_ok = 0
    for ev in events:
        attrs = dict(ev.get("attributes") or {})
        if attrs.get("consolidated"):
            continue
        desc = attrs.get("description") or ""
        if len(desc) > 40:
            res = dual_upsert(
                "Insight",
                f"Consolidated: {ev['name'][:50]}",
                attributes={
                    "description": desc[:500],
                    "consolidated_from": ev["name"],
                    "sleep_cycle": True,
                },
                metadata={
                    "source": "sleep:nrem",
                    "author": "$system",
                    "confidence": 0.8,
                },
                propositions=[("consolidated_from", "Event", ev["name"])],
            )
            if res.get("remote_ok"):
                remote_ok += 1
        attrs["consolidated"] = True
        attrs["consolidated_at"] = time.time()
        dual_upsert("Event", ev["name"], attributes=attrs, metadata={"source": "sleep:nrem", "confidence": 0.85})
        consolidated += 1

    prefs = local.find_concepts(type_="Preference", limit=100)
    decayed = 0
    for p in prefs:
        meta = dict(p.get("metadata") or {})
        conf = float(meta.get("confidence") or 0.9)
        if conf > 0.4 and str(meta.get("source", "")).startswith("formation"):
            meta["confidence"] = round(max(0.4, conf - 0.01), 3)
            dual_upsert(
                "Preference",
                p["name"],
                attributes=p.get("attributes") or {},
                metadata=meta,
            )
            decayed += 1

    _touch_state("maintenance", f"consolidated={consolidated}")
    return {
        "ok": True,
        "phase": "nrem_lite",
        "events_consolidated": consolidated,
        "preferences_touched": decayed,
        "remote_insights": remote_ok,
        "engine": "dual_write",
    }


def learn_from_skill_proposal(
    skill_name: str,
    rationale: str,
    proposal_id: str = "",
    path: str = "",
) -> Dict[str, Any]:
    """Hermes self-improve → KIP: skill proposals become Insight + Commitment (dual-write)."""
    from kip_memory.dual_write import dual_upsert

    name = f"SkillImprove:{skill_name}:{proposal_id or uuid.uuid4().hex[:8]}"
    ins = dual_upsert(
        "Insight",
        name[:80],
        attributes={
            "description": rationale[:2000],
            "skill": skill_name,
            "proposal_id": proposal_id,
            "path": path,
            "status": "pending_review",
        },
        metadata={"source": "hermes:skill_propose", "author": "$self", "confidence": 0.9},
    )
    commit = dual_upsert(
        "Commitment",
        f"Review skill {skill_name}",
        attributes={
            "description": f"Curator should review proposal for {skill_name}",
            "skill": skill_name,
            "proposal_id": proposal_id,
            "due": "next_curator_pass",
        },
        metadata={"source": "hermes:skill_propose", "author": "$self", "confidence": 1.0},
        propositions=[("improves", "Insight", name[:80])],
    )
    return {
        "ok": True,
        "insight": ins.get("local") or ins,
        "commitment": commit.get("local") or commit,
        "remote_ok": bool(ins.get("remote_ok") and commit.get("remote_ok")),
    }


def learn_from_hermes_memory_entry(entry: str) -> Dict[str, Any]:
    """Mirror Hermes MEMORY.md line into KIP Insight (dual-write)."""
    from kip_memory.dual_write import dual_remember

    return {"ok": True, "stored": dual_remember(entry, kind="Insight", name=entry[:60])}


def _touch_state(op: str, detail: str) -> None:
    _STATE.parent.mkdir(parents=True, exist_ok=True)
    st = {}
    if _STATE.is_file():
        try:
            st = json.loads(_STATE.read_text())
        except Exception:
            st = {}
    st["last_op"] = op
    st["last_detail"] = detail[:500]
    st["last_ts"] = time.time()
    st["ops"] = int(st.get("ops") or 0) + 1
    _STATE.write_text(json.dumps(st, indent=2))


def status() -> Dict[str, Any]:
    primer = local.execute_kip("DESCRIBE PRIMER")
    st = {}
    if _STATE.is_file():
        try:
            st = json.loads(_STATE.read_text())
        except Exception:
            pass
    remote = None
    if _nexus_url():
        remote = remote_kip("DESCRIBE PRIMER")
    return {
        "ok": True,
        "local_primer": primer,
        "brain_state": st,
        "remote_url": _nexus_url() or None,
        "remote": remote,
        "seed_capsules": [p.name for p in _SEED.glob("*.kip")] if _SEED.is_dir() else [],
    }
