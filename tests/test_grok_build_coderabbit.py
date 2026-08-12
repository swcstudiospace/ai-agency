"""Tests — Grok Build + CodeRabbit tool surface."""

from tools.coderabbit_tools import coderabbit_status, get_coderabbit_tools
from tools.grok_build_tools import (
    GROK_BUILD_OFFLOAD_INSTRUCTIONS,
    get_grok_build_tools,
    grok_build_offload_shell,
    grok_build_status,
)
from tools.toolbelts import TOOLBELTS, resolve_toolbelt
from workflows._grok_build import with_grok_build_guidance


def test_grok_build_belt_registered():
    assert "grok_build" in TOOLBELTS
    assert "warp" not in TOOLBELTS
    names = {getattr(t, "__name__", str(t)) for t in TOOLBELTS["grok_build"]}
    for n in (
        "grok_build_status",
        "grok_build_run",
        "grok_build_offload_shell",
        "grok_build_orchestrate_agency_task",
    ):
        assert n in names


def test_coderabbit_belt_registered():
    assert "coderabbit" in TOOLBELTS
    names = {getattr(t, "__name__", str(t)) for t in TOOLBELTS["coderabbit"]}
    assert "coderabbit_review" in names


def test_resolve_includes_grok_build_and_cr():
    tools = resolve_toolbelt(["grok_build", "coderabbit"])
    names = {getattr(t, "__name__", str(t)) for t in tools}
    assert "grok_build_status" in names
    assert "coderabbit_status" in names


def test_grok_build_status_shape():
    st = grok_build_status()
    assert "ok" in st
    assert st.get("stack", "").startswith("Hermes")
    assert "grok_bin" in st


def test_grok_build_offload_shell_echo():
    r = grok_build_offload_shell("echo grok-build-bottom-ok", reason="unit-test")
    assert r.get("ok") is True
    assert "grok-build-bottom-ok" in (r.get("stdout") or r.get("output") or "")
    assert r.get("artifact")


def test_grok_build_offload_blocks_env_dump():
    r = grok_build_offload_shell("cat .env", reason="should-block")
    assert r.get("ok") is False
    assert r.get("error") == "blocked_sensitive_command"


def test_grok_build_instructions_nonempty():
    assert "Grok Build" in GROK_BUILD_OFFLOAD_INSTRUCTIONS
    assert "grok_build_run" in GROK_BUILD_OFFLOAD_INSTRUCTIONS
    assert "Warp" in GROK_BUILD_OFFLOAD_INSTRUCTIONS  # explicit removal notice


def test_workflow_grok_build_guidance():
    s = with_grok_build_guidance("Do research")
    assert "Grok Build" in s
    assert "Do research" in s


def test_get_tool_lists():
    assert len(get_grok_build_tools()) >= 5
    assert len(get_coderabbit_tools()) >= 2


def test_coderabbit_status_installed_or_hint():
    st = coderabbit_status()
    assert "ok" in st or "installed" in st


def test_agency_custom_agents_exist():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    for name in ("agency-bottom.md", "dropshipping-pipeline.md", "agency-coder.md"):
        assert (root / "configs" / "grok-build" / "agents" / name).is_file()
