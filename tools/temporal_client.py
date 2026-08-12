"""Temporal client stubs — wire a real client when TEMPORAL_ADDRESS is live."""

from __future__ import annotations

from typing import Any


def start_workflow(workflow_name: str, args: dict | None = None) -> str:
    print(f"[Temporal STUB] Would start workflow: {workflow_name} args={args}")
    return "temporal-stub-run-id"


def signal_workflow(workflow_id: str, signal_name: str, data: Any = None) -> None:
    print(f"[Temporal STUB] Would signal {workflow_id} → {signal_name} data={data}")
