"""Parallel Web Systems tools for Agno agents.

Prefers the official ``parallel`` SDK when installed; falls back to REST via httpx
using the same endpoints as the Hermes parallel-* skills.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import httpx

try:
    from parallel import Parallel
except ImportError:  # pragma: no cover
    Parallel = None  # type: ignore[misc, assignment]

API_BASE = os.environ.get("PARALLEL_API_BASE", "https://api.parallel.ai").rstrip("/")


def _load_api_key() -> str:
    key = (os.getenv("PARALLEL_API_KEY") or "").strip()
    if key:
        return key
    for path in (
        Path("/root/.config/parallel/api.env"),
        Path.home() / ".config" / "parallel" / "api.env",
        Path("/root/.hermes/.env"),
        Path.home() / ".hermes" / ".env",
    ):
        if not path.is_file():
            continue
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                if k.strip() == "PARALLEL_API_KEY":
                    val = v.strip().strip('"').strip("'")
                    if val:
                        os.environ["PARALLEL_API_KEY"] = val
                        return val
        except OSError:
            continue
    raise RuntimeError(
        "PARALLEL_API_KEY is required. Export it or put it in "
        "/root/.config/parallel/api.env (mode 600)."
    )


def _client():
    if Parallel is None:
        return None
    return Parallel(api_key=_load_api_key())


def _rest(method: str, path: str, body: dict | None = None, timeout: float = 120.0) -> dict[str, Any]:
    key = _load_api_key()
    url = path if path.startswith("http") else f"{API_BASE}{path}"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-api-key": key,
        "User-Agent": "ai-agency-parallel-tools/1.0",
    }
    with httpx.Client(timeout=timeout) as client:
        response = client.request(method.upper(), url, headers=headers, json=body)
        try:
            data = response.json() if response.content else {}
        except Exception:
            data = {"raw": response.text[:2000]}
        if response.status_code >= 400:
            raise RuntimeError(f"Parallel API HTTP {response.status_code} {method} {path}: {data}")
        return data if isinstance(data, dict) else {"data": data}


def parallel_search(
    objective: str,
    search_queries: list[str] | None = None,
    mode: str = "advanced",
    max_chars_total: int | None = None,
) -> dict[str, Any]:
    """Search the web with a natural-language objective.

    Modes (Parallel Search API): ``turbo``, ``basic``, ``advanced`` (and docs
    may also list ``fast``). There is no ``max_results`` — use
    ``max_chars_total`` to bound excerpt volume.
    """
    queries = search_queries or [objective[:80]]
    # Normalize legacy aliases agents might still pass
    mode_aliases = {"one-shot": "basic", "oneshot": "basic", "fast": "turbo"}
    mode = mode_aliases.get(mode, mode)
    if mode not in {"turbo", "basic", "advanced"}:
        mode = "advanced"

    client = _client()
    if client is not None:
        try:
            kwargs: dict[str, Any] = {
                "objective": objective,
                "search_queries": queries[:5],
                "mode": mode,
            }
            if max_chars_total is not None:
                kwargs["max_chars_total"] = max_chars_total
            result = client.search(**kwargs)
            return {
                "search_id": getattr(result, "search_id", None),
                "results": [
                    {
                        "url": r.url,
                        "title": r.title,
                        "publish_date": getattr(r, "publish_date", None),
                        "excerpts": r.excerpts if hasattr(r, "excerpts") else [],
                    }
                    for r in (result.results or [])
                ],
            }
        except Exception as e:
            # Prefer surfacing SDK errors; REST fallback still available
            sdk_error = str(e)
        else:
            sdk_error = None
    else:
        sdk_error = None

    body: dict[str, Any] = {
        "objective": objective,
        "search_queries": queries[:5],
        "mode": mode,
    }
    if max_chars_total is not None:
        body["max_chars_total"] = max_chars_total
    try:
        out = _rest("POST", "/v1/search", body=body, timeout=90)
    except Exception as e:
        return {"error": str(e), "sdk_error": sdk_error, "objective": objective}
    results = out.get("results") or []
    return {
        "search_id": out.get("search_id"),
        "results": [
            {
                "url": r.get("url"),
                "title": r.get("title"),
                "publish_date": r.get("publish_date"),
                "excerpts": r.get("excerpts") or [],
            }
            for r in (results if isinstance(results, list) else [])
        ],
        "usage": out.get("usage"),
        "warnings": out.get("warnings"),
        "sdk_error": sdk_error,
    }


def parallel_extract(urls: list[str], objective: str | None = None) -> dict[str, Any]:
    """Extract clean content from URLs."""
    client = _client()
    if client is not None:
        try:
            kwargs: dict[str, Any] = {"urls": urls}
            if objective:
                kwargs["objective"] = objective
            result = client.extract(**kwargs)
            return {"extractions": result}
        except Exception as e:
            return {"error": str(e), "urls": urls}

    body: dict[str, Any] = {"urls": urls}
    if objective:
        body["objective"] = objective
    try:
        return _rest("POST", "/v1/extract", body=body, timeout=120)
    except Exception as e:
        return {"error": str(e), "urls": urls}


def _task_spec(output_schema: Any | None = None) -> dict[str, Any] | None:
    if output_schema is None:
        return None
    return {"output_schema": output_schema}


def parallel_task(
    objective: str,
    processor: str = "pro",
    output_schema: Any | None = None,
    wait: bool = False,
    timeout_s: float = 3600.0,
) -> dict[str, Any]:
    """Start a Parallel Task run (deep research / structured enrichment).

    Processors: lite → base → core → pro → ultra.
    Set ``wait=True`` to block until the result is ready (needed for ultra deep research).
    """
    client = _client()
    task_spec = _task_spec(output_schema)
    run_id: str | None = None
    if client is not None:
        try:
            kwargs: dict[str, Any] = {"input": objective, "processor": processor}
            if task_spec:
                kwargs["task_spec"] = task_spec
            task_run = client.task_run.create(**kwargs)
            run_id = (
                getattr(task_run, "run_id", None)
                or getattr(task_run, "id", None)
                or getattr(task_run, "task_id", None)
            )
            out = {
                "task_id": run_id or str(task_run),
                "status": getattr(task_run, "status", "started"),
                "processor": processor,
            }
            if wait and run_id:
                result = client.task_run.result(run_id, api_timeout=int(min(timeout_s, 3600)))
                return _normalize_task_result(run_id, result, processor=processor)
            return out
        except Exception as e:
            if run_id and wait:
                # fall through to REST result poll
                pass
            elif not wait:
                return {"error": str(e), "objective": objective, "processor": processor}

    body: dict[str, Any] = {"input": objective, "processor": processor}
    if task_spec:
        body["task_spec"] = task_spec
    try:
        if run_id is None:
            created = _rest("POST", "/v1/tasks/runs", body=body, timeout=60)
            run_id = created.get("run_id") or created.get("id") or created.get("task_id")
            if not wait:
                return {
                    "task_id": run_id,
                    "status": created.get("status", "started"),
                    "processor": processor,
                    "raw": created,
                }
        if not run_id:
            return {"error": "no run_id", "objective": objective}
        # Long-poll result endpoint
        result = _rest(
            "GET",
            f"/v1/tasks/runs/{run_id}/result",
            body=None,
            timeout=min(timeout_s, 3600),
        )
        return _normalize_task_result(run_id, result, processor=processor)
    except Exception as e:
        return {"error": str(e), "objective": objective, "task_id": run_id, "processor": processor}


def _normalize_task_result(run_id: str, result: Any, *, processor: str) -> dict[str, Any]:
    """Normalize SDK object or REST dict task result."""
    if hasattr(result, "model_dump"):
        data = result.model_dump()
    elif hasattr(result, "dict"):
        data = result.dict()
    elif isinstance(result, dict):
        data = result
    else:
        data = {"output": str(result)}

    output = data.get("output") or data.get("result") or data.get("content")
    # SDK often nests output.content / output.basis
    if hasattr(result, "output"):
        out_obj = result.output
        if hasattr(out_obj, "content"):
            output = out_obj.content
        elif hasattr(out_obj, "model_dump"):
            output = out_obj.model_dump()
        else:
            output = out_obj
    basis = None
    if hasattr(result, "output") and hasattr(result.output, "basis"):
        basis = result.output.basis
    elif isinstance(data.get("output"), dict):
        basis = data["output"].get("basis")
        output = data["output"].get("content", output)

    return {
        "task_id": run_id,
        "status": data.get("status") or "completed",
        "processor": processor,
        "output": output,
        "basis": basis,
        "raw_keys": list(data.keys()) if isinstance(data, dict) else [],
    }


def parallel_task_result(run_id: str, timeout_s: float = 3600.0) -> dict[str, Any]:
    """Fetch a Task run result (waits up to timeout)."""
    client = _client()
    if client is not None:
        try:
            result = client.task_run.result(run_id, api_timeout=int(min(timeout_s, 3600)))
            return _normalize_task_result(run_id, result, processor="unknown")
        except Exception as e:
            err = str(e)
        else:
            err = None
    else:
        err = None
    try:
        result = _rest(
            "GET",
            f"/v1/tasks/runs/{run_id}/result",
            timeout=min(timeout_s, 3600),
        )
        return _normalize_task_result(run_id, result, processor="unknown")
    except Exception as e:
        return {"error": str(e), "sdk_error": err, "task_id": run_id}


def parallel_entity_search(
    objective: str,
    entity_type: str = "companies",
    match_limit: int = 50,
) -> dict[str, Any]:
    """Find entities (companies, people, products) matching an objective."""
    client = _client()
    if client is not None:
        try:
            result = client.findall.entity_search(
                entity_type=entity_type,
                objective=objective,
                match_limit=match_limit,
            )
            return {
                "entity_set_id": getattr(result, "entity_set_id", None),
                "entities": [
                    {
                        "name": e.name,
                        "url": getattr(e, "url", None),
                        "description": getattr(e, "description", None),
                    }
                    for e in (getattr(result, "entities", None) or [])
                ],
            }
        except Exception as e:
            return {"error": str(e), "objective": objective}

    body = {
        "entity_type": entity_type,
        "objective": objective,
        "match_limit": match_limit,
    }
    try:
        # Entity search path may vary by API version; try common routes.
        try:
            out = _rest("POST", "/v1beta/findall/entity_search", body=body, timeout=90)
        except Exception:
            out = _rest("POST", "/v1/findall/entity_search", body=body, timeout=90)
        entities = out.get("entities") or out.get("matches") or []
        return {
            "entity_set_id": out.get("entity_set_id"),
            "entities": entities if isinstance(entities, list) else [],
            "raw_keys": list(out.keys()),
        }
    except Exception as e:
        return {"error": str(e), "objective": objective}


def parallel_create_monitor(
    query: str,
    frequency: str = "1d",
    processor: str = "lite",
    webhook_url: str | None = None,
) -> dict[str, Any]:
    """Create a continuous monitor for competitor / category tracking."""
    client = _client()
    payload: dict[str, Any] = {
        "type": "event_stream",
        "frequency": frequency,
        "processor": processor,
        "settings": {"query": query},
    }
    if webhook_url:
        payload["webhook"] = {"url": webhook_url, "event_types": ["monitor.event.detected"]}

    if client is not None:
        try:
            result = client.monitors.create(**payload)
            return {
                "monitor_id": getattr(result, "monitor_id", None) or getattr(result, "id", None),
                "status": getattr(result, "status", "created"),
            }
        except Exception as e:
            return {"error": str(e), "query": query}

    try:
        out = _rest("POST", "/v1/monitors", body=payload, timeout=60)
        return {
            "monitor_id": out.get("monitor_id") or out.get("id"),
            "status": out.get("status", "created"),
            "raw": out,
        }
    except Exception as e:
        return {"error": str(e), "query": query}


def get_parallel_tools() -> list:
    return [
        parallel_search,
        parallel_extract,
        parallel_task,
        parallel_task_result,
        parallel_entity_search,
        parallel_create_monitor,
    ]
