"""Tests — Warp + CodeRabbit tool surface (offline)."""

from tools.coderabbit_tools import coderabbit_status, get_coderabbit_tools
from tools.toolbelts import TOOLBELTS, resolve_toolbelt
from tools.warp_tools import (
    WARP_OFFLOAD_INSTRUCTIONS,
    get_warp_tools,
    warp_offload_shell,
    warp_status,
)
from workflows._warp import with_warp_guidance


def test_warp_belt_registered():
    assert "warp" in TOOLBELTS
    names = {getattr(t, "__name__", str(t)) for t in TOOLBELTS["warp"]}
    for n in (
        "warp_status",
        "warp_agent_run",
        "warp_agent_run_cloud",
        "warp_offload_shell",
        "warp_orchestrate_agency_task",
    ):
        assert n in names


def test_coderabbit_belt_registered():
    assert "coderabbit" in TOOLBELTS
    names = {getattr(t, "__name__", str(t)) for t in TOOLBELTS["coderabbit"]}
    assert "coderabbit_review" in names
    assert "coderabbit_status" in names


def test_resolve_includes_warp_and_cr():
    tools = resolve_toolbelt(["warp", "coderabbit"])
    names = {getattr(t, "__name__", str(t)) for t in tools}
    assert "warp_status" in names
    assert "coderabbit_status" in names


def test_warp_status_shape():
    st = warp_status()
    assert "ok" in st
    assert st.get("stack", "").startswith("Hermes")
    assert "oz_bin" in st


def test_warp_offload_shell_echo():
    r = warp_offload_shell("echo warp-bottom-layer-ok", reason="unit-test")
    assert r.get("ok") is True
    assert "warp-bottom-layer-ok" in (r.get("stdout") or r.get("output") or "")
    assert r.get("artifact")


def test_warp_offload_blocks_env_dump():
    r = warp_offload_shell("cat .env", reason="should-block")
    assert r.get("ok") is False
    assert r.get("error") == "blocked_sensitive_command"


def test_warp_instructions_nonempty():
    assert "Warp" in WARP_OFFLOAD_INSTRUCTIONS
    assert "warp_agent_run" in WARP_OFFLOAD_INSTRUCTIONS


def test_workflow_warp_guidance():
    s = with_warp_guidance("Do research")
    assert "Warp" in s
    assert "Do research" in s


def test_get_tool_lists():
    assert len(get_warp_tools()) >= 6
    assert len(get_coderabbit_tools()) >= 2


def test_coderabbit_status_installed_or_hint():
    st = coderabbit_status()
    assert "ok" in st or "installed" in st
