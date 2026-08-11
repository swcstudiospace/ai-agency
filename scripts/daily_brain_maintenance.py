#!/usr/bin/env python3
"""Daily brain maintenance: sleep + capsule export (+ optional analytics heartbeat).

Intended for cron / systemd timer. Safe to run repeatedly.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

# load .env lightly
env_path = ROOT / ".env"
if env_path.is_file():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

os.environ.setdefault("ANDA_NEXUS_URL", "http://127.0.0.1:8091")
os.environ.setdefault("KIP_ICP_MODE", "local")


def main() -> int:
    from kip_memory.brain import maintenance, status
    from kip_memory.cloud import push_capsule
    from kip_memory.dual_write import ensure_agency_schema_remote
    from kip_memory.nexus import export_capsule
    from tools.analytics_store import record_metric

    report: dict = {"ts": time.time(), "ok": True}
    try:
        report["schema"] = ensure_agency_schema_remote()
    except Exception as e:
        report["schema_error"] = str(e)

    try:
        report["sleep"] = maintenance()
    except Exception as e:
        report["sleep_error"] = str(e)
        report["ok"] = False

    try:
        day = time.strftime("%Y%m%d", time.gmtime())
        cap = export_capsule(label=f"daily_{day}")
        report["export"] = cap
        if cap.get("ok") and cap.get("path"):
            report["cloud"] = push_capsule(Path(cap["path"]), meta={"job": "daily_brain_maintenance"})
    except Exception as e:
        report["export_error"] = str(e)
        report["ok"] = False

    try:
        report["status"] = {
            "remote_url": status().get("remote_url"),
            "brain_ops": (status().get("brain_state") or {}).get("ops"),
        }
    except Exception as e:
        report["status_error"] = str(e)

    try:
        record_metric("brain_maintenance", name="daily", value=1.0 if report["ok"] else 0.0, unit="run")
    except Exception:
        pass

    out_dir = ROOT / "tmp" / "brain_maintenance"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"run_{int(time.time())}.json"
    out.write_text(json.dumps(report, indent=2, default=str))
    print(json.dumps({"ok": report["ok"], "report": str(out)}, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
