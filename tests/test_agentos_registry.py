"""Unit tests — workflow registry + AgentOS counts (offline import)."""

import os

import pytest

# Keep AgentOS import offline/fast
os.environ.setdefault("XAI_API_KEY", "missing-ci-placeholder")
os.environ.setdefault("AGENCY_GROK_MODEL", "grok-4.5")
os.environ.setdefault("AGENCY_DISABLE_HERMES_BRIDGE", "1")
os.environ.setdefault("AGENCY_DISABLE_ANDA_BRAIN", "1")
os.environ.setdefault("AGENCY_DISABLE_ANDA_KNOWLEDGE", "1")
os.environ.setdefault("AGENCY_DISABLE_ANALYTICS", "1")
os.environ.setdefault("LINEAR_GITHUB_LINK", "0")


@pytest.fixture(scope="module")
def agent_os():
    from app.main import agent_os as aos

    return aos


def test_agentos_scale(agent_os):
    assert len(agent_os.agents) == 30
    assert len(agent_os.teams) == 12
    assert len(agent_os.workflows) >= 12


def test_key_workflows_registered(agent_os):
    names = {getattr(w, "name", str(w)) for w in agent_os.workflows}
    assert "Product Discovery & Locate" in names
    assert "Post-Locate Fulfillment Setup" in names
    assert "Full Product Lifecycle" in names


def test_key_agents_present(agent_os):
    names = {getattr(a, "name", str(a)) for a in agent_os.agents}
    for n in (
        "Hermes Ops",
        "Product Scout",
        "Supplier Sourcer",
        "Creative Director",
        "Ads Creative Ops",
        "Logistics Coordinator",
    ):
        assert n in names
