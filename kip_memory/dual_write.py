"""Dual-write helpers: local SQLite Brain + remote Anda Cognitive Nexus (authoritative).

Remote UPSERTs use official KIP KML against anda_cognitive_nexus_server.
Unknown concept types are registered as $ConceptType on first use.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional, Sequence, Tuple

# Types known from Genesis + agency extensions
_CORE_TYPES = {
    "$ConceptType",
    "$PropositionType",
    "Domain",
    "Person",
    "Preference",
    "Event",
    "SleepTask",
    "Insight",
    "Commitment",
    "Product",
    "Capsule",
    "Supplier",
    "Campaign",
    "Skill",
}
_registered_remote: set[str] = set()


def _esc(s: str) -> str:
    return (s or "").replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ").strip()


def _attrs_literal(attrs: dict) -> str:
    """Serialize attributes as KIP object literal (JSON-compatible)."""
    clean = {}
    for k, v in (attrs or {}).items():
        if v is None:
            continue
        if isinstance(v, (str, int, float, bool)):
            clean[k] = v
        else:
            clean[k] = json.dumps(v, ensure_ascii=False)[:2000]
    # compact JSON works as object literal in KIP
    return json.dumps(clean, ensure_ascii=False)


def ensure_remote_type(type_name: str, description: str = "") -> Dict[str, Any]:
    """Register a $ConceptType on remote nexus if not core/already done."""
    from kip_memory.brain import remote_kip

    t = (type_name or "").strip()
    if not t or t in _CORE_TYPES or t in _registered_remote:
        return {"ok": True, "skipped": True, "type": t}
    if not (os.getenv("ANDA_NEXUS_URL") or os.getenv("KIP_NEXUS_URL")):
        return {"ok": False, "error": "no remote"}
    desc = description or f"Agency concept type {t}"
    cmd = f'''UPSERT {{
  CONCEPT ?t {{
    {{type: "$ConceptType", name: "{_esc(t)}"}}
    SET ATTRIBUTES {{ description: "{_esc(desc)}" }}
  }}
}}
WITH METADATA {{ source: "agency:schema", author: "$self", confidence: 1.0 }}'''
    r = remote_kip(cmd)
    if r.get("ok"):
        _registered_remote.add(t)
        _CORE_TYPES.add(t)
    return r


def ensure_remote_proposition(pred: str, description: str = "") -> Dict[str, Any]:
    """Register a $PropositionType on remote nexus."""
    from kip_memory.brain import remote_kip

    p = (pred or "").strip()
    if not p:
        return {"ok": False, "error": "empty pred"}
    key = f"prop:{p}"
    if key in _registered_remote:
        return {"ok": True, "skipped": True}
    if not (os.getenv("ANDA_NEXUS_URL") or os.getenv("KIP_NEXUS_URL")):
        return {"ok": False, "error": "no remote"}
    desc = description or f"Agency relation {p}"
    cmd = f'''UPSERT {{
  CONCEPT ?p {{
    {{type: "$PropositionType", name: "{_esc(p)}"}}
    SET ATTRIBUTES {{
      description: "{_esc(desc)}",
      subject_types: ["*"],
      object_types: ["*"]
    }}
  }}
}}
WITH METADATA {{ source: "agency:schema", author: "$self", confidence: 1.0 }}'''
    r = remote_kip(cmd)
    if r.get("ok"):
        _registered_remote.add(key)
    return r


def remote_upsert_concept(
    type_: str,
    name: str,
    attributes: Optional[dict] = None,
    metadata: Optional[dict] = None,
    propositions: Optional[Sequence[Tuple[str, str, str]]] = None,
) -> Dict[str, Any]:
    """UPSERT one concept (+ optional props) to remote Anda nexus.

    propositions: list of (predicate, object_type, object_name)
    """
    from kip_memory.brain import remote_kip

    if not (os.getenv("ANDA_NEXUS_URL") or os.getenv("KIP_NEXUS_URL")):
        return {"ok": False, "error": "ANDA_NEXUS_URL not set", "skipped": True}

    ensure_remote_type(type_)
    for pred, ot, _on in propositions or []:
        ensure_remote_type(ot)
        ensure_remote_proposition_type(pred)

    meta = {
        "source": "agency:dual_write",
        "author": "$self",
        "confidence": 0.9,
        **(metadata or {}),
    }
    conf = meta.get("confidence", 0.9)
    try:
        conf_f = float(conf)
    except Exception:
        conf_f = 0.9
    src = _esc(str(meta.get("source") or "agency:dual_write"))
    author = _esc(str(meta.get("author") or "$self"))

    attrs = dict(attributes or {})
    attrs_lit = _attrs_literal(attrs)

    obj_blocks = []
    prop_set = []
    for i, (pred, otype, oname) in enumerate(propositions or []):
        var = f"?o{i}"
        obj_blocks.append(
            f'''  CONCEPT {var} {{
    {{type: "{_esc(otype)}", name: "{_esc(oname)}"}}
    SET ATTRIBUTES {{ description: "{_esc(oname)}" }}
  }}'''
        )
        prop_set.append(f'("{_esc(pred)}", {var})')

    props_clause = ""
    if prop_set:
        props_clause = "\n    SET PROPOSITIONS { " + ", ".join(prop_set) + " }"

    blocks = "\n".join(obj_blocks)
    cmd = f'''UPSERT {{
{blocks}
  CONCEPT ?c {{
    {{type: "{_esc(type_)}", name: "{_esc(name)[:120]}"}}
    SET ATTRIBUTES {attrs_lit}{props_clause}
  }}
}}
WITH METADATA {{ source: "{src}", author: "{author}", confidence: {conf_f} }}'''

    r = remote_kip(cmd)
    r["kml_preview"] = cmd[:400]
    return r


def dual_upsert(
    type_: str,
    name: str,
    attributes: Optional[dict] = None,
    metadata: Optional[dict] = None,
    propositions: Optional[Sequence[Tuple[str, str, str]]] = None,
) -> Dict[str, Any]:
    """Write local SQLite + remote AndaDB. Remote is preferred SoT when available."""
    from kip_memory import nexus as local

    local_res = local.upsert_concept(
        type_,
        name,
        attributes=attributes,
        metadata=metadata,
        propositions=list(propositions) if propositions else None,
    )
    remote_res = remote_upsert_concept(
        type_, name, attributes=attributes, metadata=metadata, propositions=propositions
    )
    return {
        "ok": True,
        "local": local_res,
        "remote": remote_res,
        "remote_ok": bool(remote_res.get("ok")),
    }


def dual_remember(text: str, kind: str = "Insight", name: str = "", links: Optional[List[str]] = None) -> Dict[str, Any]:
    name = name or (text[:80].strip() if text else "memory")
    attrs = {"description": text, "kind": kind}
    props = []
    for link in links or []:
        if "/" in link:
            ot, on = link.split("/", 1)
            props.append(("related_to", ot.strip(), on.strip()))
    return dual_upsert(kind if kind else "Insight", name, attributes=attrs, propositions=props)


def ensure_remote_proposition_type(name: str, description: str = "") -> Dict[str, Any]:
    """Register a $PropositionType on remote nexus."""
    from kip_memory.brain import remote_kip

    n = (name or "").strip()
    if not n:
        return {"ok": False, "error": "empty"}
    if not (os.getenv("ANDA_NEXUS_URL") or os.getenv("KIP_NEXUS_URL")):
        return {"ok": False, "error": "no remote"}
    key = f"prop:{n}"
    if key in _registered_remote:
        return {"ok": True, "skipped": True, "type": n}
    desc = description or f"Agency proposition {n}"
    cmd = f'''UPSERT {{
  CONCEPT ?p {{
    {{type: "$PropositionType", name: "{_esc(n)}"}}
    SET ATTRIBUTES {{
      description: "{_esc(desc)}",
      subject_types: ["*"],
      object_types: ["*"]
    }}
  }}
}}
WITH METADATA {{ source: "agency:schema", author: "$self", confidence: 1.0 }}'''
    r = remote_kip(cmd)
    if r.get("ok"):
        _registered_remote.add(key)
    return r


def ensure_agency_schema_remote() -> Dict[str, Any]:
    """Register agency concept + proposition types on remote nexus."""
    types = [
        ("Product", "Sellable SKU, kit, or offer"),
        ("Supplier", "Product supplier or 3PL"),
        ("Campaign", "Paid or organic growth campaign"),
        ("Capsule", "Imported KIP knowledge capsule"),
        ("Skill", "Hermes/Anda agent skill"),
        ("Agent", "Software agent identity"),
    ]
    props = [
        ("derived_from", "Subject derived from object event/concept"),
        ("mentioned_in", "Subject mentioned in object"),
        ("related_to", "Generic association"),
        ("involved_in", "Person/agent involved in event"),
        ("consolidated_from", "Sleep consolidation link"),
        ("improves", "Skill improvement relation"),
        ("prefers", "Preference link"),
    ]
    out_t = []
    for t, d in types:
        out_t.append({"type": t, **ensure_remote_type(t, d)})
    out_p = []
    for p, d in props:
        out_p.append({"predicate": p, **ensure_remote_proposition_type(p, d)})
    return {"ok": True, "types": out_t, "propositions": out_p}
