"""Load Agno LocalSkills packs with optional per-agent scoping."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from agno.skills import LocalSkills, Skills

_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOTS = (
    _ROOT / "skills" / "agency",
    _ROOT / "skills" / "marketing",
    _ROOT / "skills" / "ops",
    _ROOT / "skills" / "agents",
)


def _iter_skill_dirs() -> List[Path]:
    found: List[Path] = []
    for root in SKILL_ROOTS:
        if not root.is_dir():
            continue
        for item in sorted(root.iterdir()):
            if item.is_dir() and (item / "SKILL.md").is_file():
                found.append(item)
    return found


def _skill_index() -> Dict[str, Path]:
    return {p.name: p for p in _iter_skill_dirs()}


@lru_cache(maxsize=1)
def get_agency_skills() -> Skills:
    """Full registry of all agency/marketing/ops/agent skills."""
    loaders: List[LocalSkills] = []
    for root in SKILL_ROOTS:
        if root.is_dir() and any((p / "SKILL.md").exists() for p in root.iterdir() if p.is_dir()):
            loaders.append(LocalSkills(str(root), validate=True))
    if not loaders:
        loaders.append(LocalSkills(str(_ROOT / "skills" / "agency"), validate=False))
    return Skills(loaders=loaders)


@lru_cache(maxsize=64)
def _skills_for_frozen(names: Tuple[str, ...]) -> Skills:
    if not names:
        return get_agency_skills()
    index = _skill_index()
    loaders: List[LocalSkills] = []
    missing: List[str] = []
    for name in names:
        path = index.get(name)
        if path is None:
            missing.append(name)
            continue
        loaders.append(LocalSkills(str(path), validate=True))
    if missing:
        known = ", ".join(sorted(index)) or "(none)"
        raise KeyError(f"Unknown skill(s): {missing}. Known: {known}")
    if not loaders:
        raise RuntimeError("skills_for produced empty loader set")
    return Skills(loaders=loaders)


def skills_for(*names: str) -> Optional[Skills]:
    """Return Skills scoped to the given skill folder names.

    Empty call → all skills (legacy). Prefer explicit scopes per agent.
    """
    try:
        if not names:
            return get_agency_skills()
        # stable cache key
        key = tuple(sorted({n.strip() for n in names if n and n.strip()}))
        return _skills_for_frozen(key)
    except Exception:
        return None


def list_skill_names() -> List[str]:
    return sorted(_skill_index())
