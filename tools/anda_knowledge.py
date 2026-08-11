"""Agno knowledge: Anda/KIP docs + shared memory tools for all agents."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, List, Optional

_ROOT = Path(__file__).resolve().parents[1]
_ANDA_DOCS = _ROOT / "knowledge" / "anda"


@lru_cache(maxsize=1)
def get_anda_filesystem_knowledge():
    """FileSystemKnowledge over scraped/cloned LDC Labs Anda docs."""
    if os.getenv("AGENCY_DISABLE_ANDA_KNOWLEDGE", "").lower() in {"1", "true", "yes"}:
        return None
    if not _ANDA_DOCS.is_dir():
        return None
    try:
        from agno.knowledge.filesystem import FileSystemKnowledge

        return FileSystemKnowledge(
            base_dir=str(_ANDA_DOCS),
            max_results=int(os.getenv("ANDA_KNOWLEDGE_MAX_RESULTS", "40") or "40"),
            include_patterns=["**/*.md", "**/*.kip", "**/*.txt"],
        )
    except Exception:
        return None


def get_anda_brain_tools() -> List[Any]:
    """Direct tools (in-process) for Brain formation/recall/sleep — no HTTP hop."""

    def anda_brain_status() -> dict:
        """Status of local KIP brain + optional remote Cognitive Nexus."""
        from kip_memory.brain import status

        return status()

    def anda_brain_bootstrap() -> dict:
        """Load Genesis + core KIP capsules into the shared graph."""
        from kip_memory.brain import bootstrap_genesis

        return bootstrap_genesis()

    def anda_brain_formation(text: str, counterparty: str = "", agent: str = "agency") -> dict:
        """Encode conversation/text into KIP Event + extracted Preferences/Insights."""
        from kip_memory.brain import formation

        return formation(text, counterparty=counterparty, agent=agent)

    def anda_brain_recall(query: str, limit: int = 15, counterparty: str = "") -> dict:
        """Recall shared KIP memories before answering (returns context_markdown)."""
        from kip_memory.brain import recall

        return recall(query, limit=limit, counterparty=counterparty)

    def anda_brain_sleep() -> dict:
        """Run NREM-lite maintenance: consolidate events, light preference decay."""
        from kip_memory.brain import maintenance

        return maintenance()

    def anda_docs_search(query: str, limit: int = 10) -> dict:
        """Grep Anda/KIP documentation corpus under knowledge/anda."""
        q = (query or "").lower().strip()
        if not q or not _ANDA_DOCS.is_dir():
            return {"hits": [], "error": "empty query or missing knowledge/anda"}
        hits = []
        for p in _ANDA_DOCS.rglob("*"):
            if not p.is_file():
                continue
            if p.suffix.lower() not in {".md", ".kip", ".txt"}:
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            low = text.lower()
            if q not in low and q not in p.name.lower():
                continue
            idx = low.find(q)
            snip = text[max(0, idx - 80) : idx + 200].replace("\n", " ")
            hits.append({"path": str(p.relative_to(_ANDA_DOCS)), "snippet": snip})
            if len(hits) >= max(1, min(50, limit)):
                break
        return {"query": query, "hits": hits, "count": len(hits)}

    return [
        anda_brain_status,
        anda_brain_bootstrap,
        anda_brain_formation,
        anda_brain_recall,
        anda_brain_sleep,
        anda_docs_search,
    ]
