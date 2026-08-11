"""CoT × GoT reasoning engine for the Drop universal MCP/ACP server.

Chain-of-Thought (CoT): ordered linear decomposition.
Graph-of-Thought (GoT): branching nodes with merge/score aggregation.

`reason()` can be called explicitly or auto-triggered by the MCP middleware
when a goal looks multi-step / high-stakes.
"""

from __future__ import annotations

import json
import re
import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence


class NodeKind(str, Enum):
    root = "root"
    decompose = "decompose"
    research = "research"
    economics = "economics"
    risk = "risk"
    creative = "creative"
    supply = "supply"
    growth = "growth"
    compliance = "compliance"
    decision = "decision"
    merge = "merge"


@dataclass
class ThoughtNode:
    id: str
    kind: str
    title: str
    content: str
    parent_ids: List[str] = field(default_factory=list)
    score: float = 0.5
    status: str = "open"  # open|done|killed
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReasoningGraph:
    id: str
    goal: str
    mode: str  # cot | got | hybrid
    nodes: List[ThoughtNode] = field(default_factory=list)
    edges: List[Dict[str, str]] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    summary: str = ""
    recommendation: str = ""
    confidence: float = 0.5
    auto_triggered: bool = False
    triggers: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "goal": self.goal,
            "mode": self.mode,
            "nodes": [asdict(n) for n in self.nodes],
            "edges": self.edges,
            "created_at": self.created_at,
            "summary": self.summary,
            "recommendation": self.recommendation,
            "confidence": self.confidence,
            "auto_triggered": self.auto_triggered,
            "triggers": self.triggers,
        }


_STORE: Dict[str, ReasoningGraph] = {}


# Heuristics that suggest auto CoT×GoT
_AUTO_PATTERNS = [
    (r"\b(launch|scale|spend|budget|campaign)\b", "growth_stakes"),
    (r"\b(product|niche|rank|find|sourc|supplier)\b", "product_research"),
    (r"\b(roas|cpa|margin|unit.?econ|cogs)\b", "economics"),
    (r"\b(compliance|claim|policy|ban)\b", "compliance"),
    (r"\b(end.?to.?end|lifecycle|full.?funnel|autonomous)\b", "lifecycle"),
    (r"\b(compare|trade.?off|vs\.?|versus)\b", "branching"),
]


def should_auto_reason(goal: str, *, force: bool = False) -> tuple[bool, List[str]]:
    if force:
        return True, ["forced"]
    g = (goal or "").lower()
    hits = []
    for pat, name in _AUTO_PATTERNS:
        if re.search(pat, g, re.I):
            hits.append(name)
    # multi-clause / long goals
    if len(g) > 160 or g.count(" and ") + g.count(" then ") >= 2:
        hits.append("complexity")
    # question with multiple asks
    if g.count("?") >= 2:
        hits.append("multi_question")
    return (len(hits) >= 2 or "lifecycle" in hits or "branching" in hits), hits


def _node(kind: NodeKind | str, title: str, content: str, parents: Optional[List[str]] = None, score: float = 0.55) -> ThoughtNode:
    return ThoughtNode(
        id=f"n_{uuid.uuid4().hex[:8]}",
        kind=kind.value if isinstance(kind, NodeKind) else str(kind),
        title=title,
        content=content,
        parent_ids=list(parents or []),
        score=score,
        status="done",
    )


def build_cot_chain(goal: str) -> List[ThoughtNode]:
    """Linear CoT skeleton tailored to dropshipping agency work."""
    root = _node(NodeKind.root, "Goal", goal.strip(), score=1.0)
    steps = [
        (NodeKind.decompose, "Decompose", "Break the goal into research → economics → supply → creative → growth → decision."),
        (NodeKind.research, "Evidence first", "Gather market/product evidence (Parallel) before opinions."),
        (NodeKind.economics, "Unit economics", "Model price, COGS, shipping, target CPA, contribution margin."),
        (NodeKind.risk, "Risk & compliance", "Flag restricted claims, shipping/RMA, IP, and autonomy L2 gates."),
        (NodeKind.decision, "Decision", "Emit GO / TEST / NO-GO with kill criteria and next owner."),
    ]
    nodes = [root]
    prev = root.id
    for kind, title, content in steps:
        n = _node(kind, title, content, parents=[prev], score=0.6)
        nodes.append(n)
        prev = n.id
    return nodes


def build_got_branches(goal: str, root_id: str) -> List[ThoughtNode]:
    """Parallel GoT branches that later merge."""
    branches = [
        (NodeKind.research, "Branch: Demand", "Search demand signals, SERP, competitors, seasonality."),
        (NodeKind.economics, "Branch: Margin", "Stress CM at CPA bands; kill if CM% < ~15% at target CPA."),
        (NodeKind.supply, "Branch: Supply", "Supplier lead time, MOQ, sample plan, logistics DIM risk."),
        (NodeKind.creative, "Branch: Creative", "UGC hooks, Fal avatar path, compliance-safe angles."),
        (NodeKind.growth, "Branch: Acquisition", "Meta/TikTok draft structure, HITL spend caps, kill ROAS."),
        (NodeKind.compliance, "Branch: Policy", "PASS/REVISE/BLOCK on claims before any live ads."),
    ]
    nodes = []
    for kind, title, content in branches:
        nodes.append(_node(kind, title, content, parents=[root_id], score=0.58))
    # merge
    merge_parents = [n.id for n in nodes]
    merge = _node(
        NodeKind.merge,
        "Merge branches",
        "Aggregate branch scores; prefer TEST over GO when landed costs unproven; enforce HITL on spend.",
        parents=merge_parents,
        score=0.62,
    )
    nodes.append(merge)
    return nodes


def run_reasoning(
    goal: str,
    mode: str = "hybrid",
    *,
    auto_triggered: bool = False,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build a CoT, GoT, or hybrid graph and store it."""
    goal = (goal or "").strip()
    if not goal:
        return {"error": "goal is required"}
    mode = (mode or "hybrid").lower().strip()
    if mode not in {"cot", "got", "hybrid"}:
        mode = "hybrid"

    gid = f"got_{uuid.uuid4().hex[:10]}"
    g = ReasoningGraph(id=gid, goal=goal, mode=mode, auto_triggered=auto_triggered)

    if mode in {"cot", "hybrid"}:
        cot_nodes = build_cot_chain(goal)
        g.nodes.extend(cot_nodes)
        for i in range(1, len(cot_nodes)):
            g.edges.append({"from": cot_nodes[i - 1].id, "to": cot_nodes[i].id, "type": "cot"})
        root_id = cot_nodes[0].id
    else:
        root = _node(NodeKind.root, "Goal", goal, score=1.0)
        g.nodes.append(root)
        root_id = root.id

    if mode in {"got", "hybrid"}:
        got_nodes = build_got_branches(goal, root_id)
        g.nodes.extend(got_nodes)
        for n in got_nodes:
            for p in n.parent_ids:
                g.edges.append({"from": p, "to": n.id, "type": "got"})

    # lightweight scoring from keywords in goal
    conf = 0.55
    gl = goal.lower()
    if any(k in gl for k in ("test", "pilot", "learning")):
        conf = 0.6
        rec = "TEST path: small budget, samples first, HITL spend approval required before live ads."
    elif any(k in gl for k in ("scale", "aggressive", "max")):
        conf = 0.45
        rec = "Do not scale until CM proven and compliance PASS; request Finance cap + HITL."
    else:
        rec = "Hybrid path: research → economics gate → supply test → creative → draft ads → HITL spend."

    if context:
        g.nodes.append(
            _node(
                NodeKind.decision,
                "Context injected",
                json.dumps(context, default=str)[:2000],
                parents=[g.nodes[-1].id],
                score=0.5,
            )
        )

    g.summary = (
        f"Reasoning graph ({mode}) with {len(g.nodes)} nodes / {len(g.edges)} edges "
        f"for goal: {goal[:200]}"
    )
    g.recommendation = rec
    g.confidence = conf
    _STORE[gid] = g
    return g.to_dict()


def get_graph(graph_id: str) -> Dict[str, Any]:
    g = _STORE.get(graph_id)
    if not g:
        return {"error": f"graph not found: {graph_id}"}
    return g.to_dict()


def list_graphs(limit: int = 20) -> Dict[str, Any]:
    items = sorted(_STORE.values(), key=lambda x: x.created_at, reverse=True)[: max(1, min(100, limit))]
    return {
        "graphs": [
            {
                "id": g.id,
                "goal": g.goal[:160],
                "mode": g.mode,
                "nodes": len(g.nodes),
                "confidence": g.confidence,
                "auto_triggered": g.auto_triggered,
                "recommendation": g.recommendation,
            }
            for g in items
        ],
        "count": len(items),
    }


def reason_auto(goal: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Auto-trigger hybrid reasoning when heuristics fire; else return skipped."""
    should, hits = should_auto_reason(goal)
    if not should:
        return {"triggered": False, "triggers": hits, "reason": "goal did not meet auto-reason threshold"}
    graph = run_reasoning(goal, mode="hybrid", auto_triggered=True, context=context)
    graph["triggered"] = True
    graph["triggers"] = hits
    return graph
