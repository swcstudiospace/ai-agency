"""Local KIP Cognitive Nexus — Knowledge Interaction Protocol store.

Implements a practical subset of ldclabs/KIP for shared agent memory:
  KQL: FIND ... WHERE ... LIMIT
  KML: UPSERT { CONCEPT ... SET ATTRIBUTES / PROPOSITIONS }
  META: DESCRIBE PRIMER | SEARCH

Persistence: SQLite at tmp/kip/nexus.db
ICP path: EXPORT capsules to tmp/kip/capsules/ + optional ic-oss/canister hook
  (see kip_memory.icp_sync). Full on-chain canister deploy is config-gated.
"""

from __future__ import annotations

import json
import re
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_ROOT = Path(__file__).resolve().parents[1]
_DB = Path(__file__).resolve().parent / "data" / "nexus.db"
_CAPSULES = Path(__file__).resolve().parent / "data" / "capsules"


def _conn() -> sqlite3.Connection:
    _DB.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(_DB))
    c.row_factory = sqlite3.Row
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS concepts (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            name TEXT NOT NULL,
            attributes TEXT DEFAULT '{}',
            metadata TEXT DEFAULT '{}',
            version INTEGER DEFAULT 1,
            created_at REAL,
            updated_at REAL,
            UNIQUE(type, name)
        )
        """
    )
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS propositions (
            id TEXT PRIMARY KEY,
            subject_id TEXT NOT NULL,
            predicate TEXT NOT NULL,
            object_id TEXT NOT NULL,
            metadata TEXT DEFAULT '{}',
            version INTEGER DEFAULT 1,
            created_at REAL,
            updated_at REAL
        )
        """
    )
    c.execute("CREATE INDEX IF NOT EXISTS idx_prop_subj ON propositions(subject_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_prop_pred ON propositions(predicate)")
    c.commit()
    return c


def _now() -> float:
    return time.time()


def _ensure_self(c: sqlite3.Connection) -> None:
    row = c.execute("SELECT id FROM concepts WHERE type=? AND name=?", ("Agent", "$self")).fetchone()
    if row:
        return
    cid = f"c_{uuid.uuid4().hex[:12]}"
    ts = _now()
    c.execute(
        "INSERT INTO concepts(id,type,name,attributes,metadata,version,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?)",
        (
            cid,
            "Agent",
            "$self",
            json.dumps({"description": "AI Dropshipping Agency shared mind (Hermes+Agno)"}),
            json.dumps({"source": "genesis", "author": "system", "confidence": 1.0}),
            1,
            ts,
            ts,
        ),
    )
    c.commit()


def upsert_concept(
    type_: str,
    name: str,
    attributes: Optional[dict] = None,
    metadata: Optional[dict] = None,
    propositions: Optional[List[Tuple[str, str, str]]] = None,
) -> Dict[str, Any]:
    """propositions: list of (predicate, obj_type, obj_name)."""
    c = _conn()
    _ensure_self(c)
    ts = _now()
    meta = {"source": "agency", "author": "$self", "confidence": 0.9, **(metadata or {})}
    attrs = attributes or {}
    row = c.execute("SELECT * FROM concepts WHERE type=? AND name=?", (type_, name)).fetchone()
    if row:
        cid = row["id"]
        old_attrs = json.loads(row["attributes"] or "{}")
        old_attrs.update(attrs)
        c.execute(
            "UPDATE concepts SET attributes=?, metadata=?, version=version+1, updated_at=? WHERE id=?",
            (json.dumps(old_attrs), json.dumps(meta), ts, cid),
        )
    else:
        cid = f"c_{uuid.uuid4().hex[:12]}"
        c.execute(
            "INSERT INTO concepts(id,type,name,attributes,metadata,version,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?)",
            (cid, type_, name, json.dumps(attrs), json.dumps(meta), 1, ts, ts),
        )
    prop_ids = []
    for pred, otype, oname in propositions or []:
        o = c.execute("SELECT id FROM concepts WHERE type=? AND name=?", (otype, oname)).fetchone()
        if not o:
            oid = f"c_{uuid.uuid4().hex[:12]}"
            c.execute(
                "INSERT INTO concepts(id,type,name,attributes,metadata,version,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?)",
                (oid, otype, oname, "{}", json.dumps(meta), 1, ts, ts),
            )
        else:
            oid = o["id"]
        pid = f"p_{uuid.uuid4().hex[:12]}"
        c.execute(
            "INSERT INTO propositions(id,subject_id,predicate,object_id,metadata,version,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?)",
            (pid, cid, pred, oid, json.dumps(meta), 1, ts, ts),
        )
        prop_ids.append(pid)
    c.commit()
    c.close()
    return {"id": cid, "type": type_, "name": name, "propositions": prop_ids}


def find_concepts(query: str = "", type_: str = "", limit: int = 20) -> List[Dict[str, Any]]:
    c = _conn()
    _ensure_self(c)
    sql = "SELECT * FROM concepts WHERE 1=1"
    args: list = []
    if type_:
        sql += " AND type=?"
        args.append(type_)
    if query:
        sql += " AND (name LIKE ? OR attributes LIKE ?)"
        args.extend([f"%{query}%", f"%{query}%"])
    sql += " ORDER BY updated_at DESC LIMIT ?"
    args.append(max(1, min(100, limit)))
    rows = c.execute(sql, args).fetchall()
    out = []
    for r in rows:
        out.append(
            {
                "id": r["id"],
                "type": r["type"],
                "name": r["name"],
                "attributes": json.loads(r["attributes"] or "{}"),
                "metadata": json.loads(r["metadata"] or "{}"),
                "version": r["version"],
            }
        )
    c.close()
    return out


def find_related(name: str, limit: int = 30) -> List[Dict[str, Any]]:
    c = _conn()
    row = c.execute("SELECT id FROM concepts WHERE name=? LIMIT 1", (name,)).fetchone()
    if not row:
        # try contains
        row = c.execute("SELECT id FROM concepts WHERE name LIKE ? LIMIT 1", (f"%{name}%",)).fetchone()
    if not row:
        c.close()
        return []
    sid = row["id"]
    props = c.execute(
        """
        SELECT p.predicate, s.name as subject, s.type as stype, o.name as object, o.type as otype, p.metadata
        FROM propositions p
        JOIN concepts s ON s.id=p.subject_id
        JOIN concepts o ON o.id=p.object_id
        WHERE p.subject_id=? OR p.object_id=?
        LIMIT ?
        """,
        (sid, sid, limit),
    ).fetchall()
    out = [
        {
            "predicate": p["predicate"],
            "subject": {"type": p["stype"], "name": p["subject"]},
            "object": {"type": p["otype"], "name": p["object"]},
            "metadata": json.loads(p["metadata"] or "{}"),
        }
        for p in props
    ]
    c.close()
    return out


def execute_kip(command: str) -> Dict[str, Any]:
    """Execute a KIP command string (subset)."""
    cmd = (command or "").strip()
    if not cmd:
        return {"error": {"code": "KIP_EMPTY", "message": "empty command"}}

    upper = cmd.upper()
    try:
        if upper.startswith("DESCRIBE PRIMER") or upper.startswith("DESCRIBE $SELF"):
            self_c = find_concepts(type_="Agent", limit=5)
            types = {}
            for c in find_concepts(limit=50):
                types.setdefault(c["type"], 0)
                types[c["type"]] += 1
            return {
                "ok": True,
                "primer": {
                    "self": self_c,
                    "concept_type_counts": types,
                    "protocol": "KIP v1.0-RC subset (agency local nexus)",
                    "icp": "capsules exportable; canister sync optional",
                },
            }

        if upper.startswith("SEARCH"):
            # SEARCH "query"
            m = re.search(r'SEARCH\s+"([^"]+)"', cmd, re.I) or re.search(r"SEARCH\s+(\S+)", cmd, re.I)
            q = m.group(1) if m else ""
            return {"ok": True, "results": find_concepts(query=q, limit=20)}

        if upper.startswith("FIND"):
            # FIND concepts matching name fragment after WHERE name ~
            m = re.search(r'name\s*[:=]\s*"([^"]+)"', cmd, re.I)
            t = re.search(r'type\s*[:=]\s*"([^"]+)"', cmd, re.I)
            q = m.group(1) if m else ""
            ty = t.group(1) if t else ""
            # also FIND(?x) bare → list recent
            if "RELATED" in upper or "NEIGHBOR" in upper:
                name = q or re.search(r'["\']([^"\']+)["\']', cmd)
                nm = q if q else (name.group(1) if name else "")
                return {"ok": True, "results": find_related(nm)}
            return {"ok": True, "results": find_concepts(query=q, type_=ty, limit=20)}

        if upper.startswith("UPSERT"):
            # UPSERT CONCEPT type="X" name="Y" attrs={...} prop predicate -> type/name
            t = re.search(r'type\s*[:=]\s*"([^"]+)"', cmd, re.I)
            n = re.search(r'name\s*[:=]\s*"([^"]+)"', cmd, re.I)
            if not n:
                return {"error": {"code": "KIP_SYNTAX", "message": "UPSERT requires name=\"...\""}}
            type_ = t.group(1) if t else "Concept"
            name = n.group(1)
            # attributes JSON blob optional
            attrs = {}
            am = re.search(r"ATTRIBUTES\s+(\{.*\})", cmd, re.I | re.S)
            if am:
                try:
                    attrs = json.loads(am.group(1))
                except json.JSONDecodeError:
                    attrs = {"raw": am.group(1)[:500]}
            # description shortcut
            d = re.search(r'description\s*[:=]\s*"([^"]+)"', cmd, re.I)
            if d:
                attrs["description"] = d.group(1)
            props = []
            for pm in re.finditer(
                r'\(\s*"([^"]+)"\s*,\s*"([^"]+)"\s*/\s*"([^"]+)"\s*\)', cmd
            ):
                # ("prefers", "Preference"/"Dark Mode")
                props.append((pm.group(1), pm.group(2), pm.group(3)))
            for pm in re.finditer(r'PROP\s+"([^"]+)"\s+->\s+"([^"]+)"\s*/\s*"([^"]+)"', cmd, re.I):
                props.append((pm.group(1), pm.group(2), pm.group(3)))
            res = upsert_concept(type_, name, attributes=attrs, propositions=props)
            return {"ok": True, "upserted": res}

        if upper.startswith("EXPORT"):
            return export_capsule(label=re.search(r'label\s*[:=]\s*"([^"]+)"', cmd, re.I))

        return {
            "error": {
                "code": "KIP_UNSUPPORTED",
                "message": "Supported: DESCRIBE PRIMER, SEARCH, FIND, UPSERT CONCEPT, EXPORT",
                "got": cmd[:200],
            }
        }
    except Exception as e:
        return {"error": {"code": "KIP_INTERNAL", "message": str(e)}}


def export_capsule(label: Any = None) -> Dict[str, Any]:
    """Export full graph as KIP knowledge capsule (for ICP/ic-oss sync)."""
    _CAPSULES.mkdir(parents=True, exist_ok=True)
    concepts = find_concepts(limit=500)
    c = _conn()
    props = c.execute(
        """
        SELECT p.predicate, s.type as st, s.name as sn, o.type as ot, o.name as oname, p.metadata
        FROM propositions p
        JOIN concepts s ON s.id=p.subject_id
        JOIN concepts o ON o.id=p.object_id
        """
    ).fetchall()
    c.close()
    lab = "agency"
    if label and hasattr(label, "group"):
        lab = label.group(1)
    elif isinstance(label, str) and label:
        lab = label
    capsule = {
        "protocol": "KIP",
        "version": "1.0-RC-agency",
        "label": lab,
        "exported_at": _now(),
        "concepts": concepts,
        "propositions": [
            {
                "predicate": p["predicate"],
                "subject": {"type": p["st"], "name": p["sn"]},
                "object": {"type": p["ot"], "name": p["oname"]},
                "metadata": json.loads(p["metadata"] or "{}"),
            }
            for p in props
        ],
    }
    path = _CAPSULES / f"capsule_{lab}_{int(_now())}.json"
    path.write_text(json.dumps(capsule, indent=2))
    # ICP hook
    icp = try_icp_sync(path, capsule)
    return {"ok": True, "path": str(path), "concepts": len(concepts), "propositions": len(props), "icp": icp}


def try_icp_sync(path: Path, capsule: dict) -> Dict[str, Any]:
    """Optional ICP sync via configured canister / ic-oss.

    Env:
      KIP_ICP_MODE=local|canister|ic_oss
      KIP_ICP_CANISTER_ID=
      KIP_ICP_HOST=https://icp0.io
      IC_OSS_ENDPOINT=
    """
    import os

    mode = (os.getenv("KIP_ICP_MODE") or "local").strip().lower()
    if mode == "local":
        # store hash-chain style receipt locally (ICP-ready artifact)
        receipt_dir = _CAPSULES / "icp_receipts"
        receipt_dir.mkdir(parents=True, exist_ok=True)
        import hashlib

        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        receipt = {
            "mode": "local_icp_ready",
            "sha256": digest,
            "capsule": str(path),
            "note": "Set KIP_ICP_MODE=canister and KIP_ICP_CANISTER_ID to push on-chain via ic-oss/dfx.",
            "ts": _now(),
        }
        rp = receipt_dir / f"{digest[:16]}.json"
        rp.write_text(json.dumps(receipt, indent=2))
        return receipt

    if mode in {"canister", "ic_oss"}:
        # Best-effort HTTP to a configured gateway — no private keys in process.
        endpoint = os.getenv("IC_OSS_ENDPOINT") or os.getenv("KIP_ICP_GATEWAY")
        canister = os.getenv("KIP_ICP_CANISTER_ID")
        if not endpoint:
            return {"ok": False, "error": "IC_OSS_ENDPOINT or KIP_ICP_GATEWAY required for canister mode"}
        try:
            import httpx

            r = httpx.post(
                endpoint.rstrip("/") + "/upload",
                json={"canister_id": canister, "path": path.name, "capsule": capsule},
                timeout=60.0,
            )
            return {"ok": r.status_code < 300, "status": r.status_code, "body": r.text[:1000]}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    return {"ok": False, "error": f"unknown KIP_ICP_MODE={mode}"}


def remember(text: str, kind: str = "Insight", name: str = "", links: Optional[List[str]] = None) -> Dict[str, Any]:
    """Natural-language friendly remember → UPSERT."""
    name = name or text[:80].strip()
    attrs = {"description": text, "kind": kind}
    props = []
    for link in links or []:
        # link format Type/Name
        if "/" in link:
            ot, on = link.split("/", 1)
            props.append(("related_to", ot.strip(), on.strip()))
    return upsert_concept(kind if kind else "Insight", name, attributes=attrs, propositions=props)


def recall(query: str, limit: int = 15) -> Dict[str, Any]:
    concepts = find_concepts(query=query, limit=limit)
    related = find_related(query, limit=limit) if concepts else []
    return {"query": query, "concepts": concepts, "related": related}
