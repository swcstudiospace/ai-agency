"""Cloud / ICP object-store hooks for KIP capsules (ic-oss + S3-compatible).

Env:
  KIP_ICP_MODE=local|canister|s3|ic_oss
  IC_OSS_ENDPOINT=https://...
  KIP_ICP_CANISTER_ID=
  KIP_S3_BUCKET=
  KIP_S3_ENDPOINT=   # optional custom endpoint
  AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY for S3
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional


def push_capsule(path: Path, meta: Optional[dict] = None) -> Dict[str, Any]:
    mode = (os.getenv("KIP_ICP_MODE") or "local").strip().lower()
    path = Path(path)
    if not path.is_file():
        return {"ok": False, "error": f"missing {path}"}
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    payload = {
        "filename": path.name,
        "sha256": digest,
        "bytes": len(raw),
        "meta": meta or {},
        "ts": time.time(),
    }

    if mode == "local":
        receipt_dir = path.parent / "icp_receipts"
        receipt_dir.mkdir(parents=True, exist_ok=True)
        rp = receipt_dir / f"{digest[:16]}.json"
        payload.update({"mode": "local_icp_ready", "capsule": str(path)})
        rp.write_text(json.dumps(payload, indent=2))
        return {"ok": True, **payload, "receipt": str(rp)}

    if mode in {"canister", "ic_oss"}:
        endpoint = os.getenv("IC_OSS_ENDPOINT") or os.getenv("KIP_ICP_GATEWAY")
        if not endpoint:
            return {"ok": False, "error": "IC_OSS_ENDPOINT required", "sha256": digest}
        try:
            import httpx

            files = {"file": (path.name, raw, "application/json")}
            data = {
                "canister_id": os.getenv("KIP_ICP_CANISTER_ID") or "",
                "sha256": digest,
            }
            headers = {}
            tok = os.getenv("IC_OSS_TOKEN") or os.getenv("ANDA_NEXUS_API_KEY")
            if tok:
                headers["Authorization"] = f"Bearer {tok}"
            with httpx.Client(timeout=120.0) as client:
                r = client.post(endpoint.rstrip("/") + "/upload", data=data, files=files, headers=headers)
            return {
                "ok": r.status_code < 300,
                "status": r.status_code,
                "sha256": digest,
                "body": r.text[:1500],
                "mode": mode,
            }
        except Exception as e:
            return {"ok": False, "error": str(e), "sha256": digest, "mode": mode}

    if mode == "s3":
        bucket = os.getenv("KIP_S3_BUCKET")
        if not bucket:
            return {"ok": False, "error": "KIP_S3_BUCKET required"}
        try:
            import boto3

            kw = {}
            ep = os.getenv("KIP_S3_ENDPOINT")
            if ep:
                kw["endpoint_url"] = ep
            s3 = boto3.client("s3", **kw)
            key = f"kip-capsules/{path.name}"
            s3.put_object(Bucket=bucket, Key=key, Body=raw, ContentType="application/json")
            return {"ok": True, "mode": "s3", "bucket": bucket, "key": key, "sha256": digest}
        except Exception as e:
            return {"ok": False, "error": str(e), "mode": "s3", "sha256": digest}

    return {"ok": False, "error": f"unknown KIP_ICP_MODE={mode}"}
