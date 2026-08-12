"""Fal.ai generation tools — UGC avatar video + image creatives.

Primary UGC path: argil/avatars/text-to-video (script → talking avatar MP4).
Falls back to stub payloads when FAL_KEY is missing.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from tools.envutil import env

# Known fal endpoints for UGC-style generation
FAL_AVATAR_T2V = env("FAL_AVATAR_ENDPOINT", "argil/avatars/text-to-video")
FAL_DEFAULT_IMAGE = env("FAL_IMAGE_ENDPOINT", "fal-ai/flux/dev")


def _client():
    key = env("FAL_KEY") or env("FAL_API_KEY")
    if not key:
        return None
    try:
        import fal_client  # type: ignore
    except ImportError:
        try:
            import fal  # noqa: F401
        except ImportError:
            return None
        # older package shapes vary
        return {"mode": "http", "key": key}
    return {"mode": "fal_client", "mod": fal_client, "key": key}


def list_fal_avatars() -> dict[str, Any]:
    """Return configured / known avatar presets for UGC generation."""
    # Argil exposes named avatars in the playground; keep a practical default set.
    presets = [
        {"id": "Noemie car (UGC)", "style": "ugc", "notes": "Casual car/outdoor UGC energy"},
        {"id": "default_ugc_female", "style": "ugc", "notes": "Fallback label — override via FAL_AVATAR_ID"},
        {"id": "default_ugc_male", "style": "ugc", "notes": "Fallback label — override via FAL_AVATAR_ID"},
    ]
    return {
        "endpoint": FAL_AVATAR_T2V,
        "avatars": presets,
        "default_avatar": env("FAL_AVATAR_ID", presets[0]["id"]),
        "default_voice": env("FAL_VOICE_ID", "Rachel"),
        "fal_configured": bool(env("FAL_KEY") or env("FAL_API_KEY")),
    }


def generate_ugc_avatar_video(
    script: str,
    avatar: str | None = None,
    voice: str | None = None,
    aspect_ratio: str = "9:16",
    product_name: str = "",
    hook: str = "",
) -> dict[str, Any]:
    """Generate a UGC-style talking-avatar video from a script via Fal.

    Uses queue.submit/result when fal_client is installed; otherwise returns a
    structured stub the Creative pipeline can still track in Linear.
    """
    script = (script or "").strip()
    if not script:
        return {"error": "script is required"}
    avatar = avatar or env("FAL_AVATAR_ID") or "Noemie car (UGC)"
    voice = voice or env("FAL_VOICE_ID") or "Rachel"
    client = _client()
    payload = {
        "avatar": avatar,
        "text": script[:4000],
        "voice": voice,
    }
    # Some endpoints accept extra fields — harmless if ignored
    meta = {
        "product_name": product_name,
        "hook": hook,
        "aspect_ratio": aspect_ratio,
        "endpoint": FAL_AVATAR_T2V,
    }
    if client is None:
        stub_path = Path("tmp/creatives")
        stub_path.mkdir(parents=True, exist_ok=True)
        out = stub_path / f"ugc_stub_{int(time.time())}.json"
        data = {
            "stub": True,
            "reason": "FAL_KEY missing or fal package not installed",
            "request": payload,
            "meta": meta,
            "video_url": None,
            "next": "export FAL_KEY and pip install fal-client",
        }
        out.write_text(json.dumps(data, indent=2))
        return data

    try:
        if client.get("mode") == "fal_client":
            fal_client = client["mod"]
            # fal_client.subscribe blocks until done
            result = fal_client.subscribe(
                FAL_AVATAR_T2V,
                arguments=payload,
                with_logs=False,
            )
            video = None
            if isinstance(result, dict):
                video = (result.get("video") or {}).get("url") or result.get("video_url")
            return {
                "stub": False,
                "endpoint": FAL_AVATAR_T2V,
                "video_url": video,
                "raw": result if isinstance(result, dict) else str(result)[:2000],
                "meta": meta,
                "request": {"avatar": avatar, "voice": voice, "script_len": len(script)},
            }
        # HTTP fallback via queue API
        import httpx

        key = client["key"]
        headers = {"Authorization": f"Key {key}", "Content-Type": "application/json"}
        with httpx.Client(timeout=300.0) as http:
            sub = http.post(
                f"https://queue.fal.run/{FAL_AVATAR_T2V}",
                headers=headers,
                json=payload,
            )
            sub.raise_for_status()
            job = sub.json()
            status_url = job.get("status_url") or job.get("response_url")
            # poll
            for _ in range(60):
                time.sleep(3)
                st = http.get(job.get("status_url", status_url), headers=headers)
                body = st.json()
                if body.get("status") in {"COMPLETED", "completed"}:
                    resp_url = body.get("response_url") or job.get("response_url")
                    final = http.get(resp_url, headers=headers).json()
                    video = (final.get("video") or {}).get("url")
                    return {
                        "stub": False,
                        "endpoint": FAL_AVATAR_T2V,
                        "video_url": video,
                        "raw": final,
                        "meta": meta,
                    }
                if body.get("status") in {"FAILED", "failed"}:
                    return {"error": body, "meta": meta}
            return {"error": "timeout waiting for fal job", "job": job, "meta": meta}
    except Exception as e:
        return {"error": str(e), "meta": meta, "request": payload}


def generate_product_image(
    prompt: str,
    size: str = "square_hd",
) -> dict[str, Any]:
    """Generate a still creative via Fal image model (flux/dev by default)."""
    prompt = (prompt or "").strip()
    if not prompt:
        return {"error": "prompt required"}
    client = _client()
    if client is None:
        return {
            "stub": True,
            "prompt": prompt,
            "image_url": None,
            "reason": "FAL_KEY missing or fal-client not installed",
        }
    try:
        if client.get("mode") == "fal_client":
            fal_client = client["mod"]
            result = fal_client.subscribe(
                FAL_DEFAULT_IMAGE,
                arguments={"prompt": prompt, "image_size": size, "num_images": 1},
            )
            images = result.get("images") if isinstance(result, dict) else None
            url = images[0].get("url") if images else None
            return {"stub": False, "image_url": url, "raw": result, "endpoint": FAL_DEFAULT_IMAGE}
        return {"error": "http image path not implemented; install fal-client"}
    except Exception as e:
        return {"error": str(e), "prompt": prompt}


def build_ugc_brief_and_render(
    product_name: str,
    hook: str,
    script_15s: str,
    avatar: str | None = None,
    render: bool = True,
) -> dict[str, Any]:
    """Creative-pipeline helper: package brief + optional Fal render."""
    brief = {
        "product_name": product_name,
        "hook": hook,
        "script_15s": script_15s,
        "avatar": avatar or env("FAL_AVATAR_ID") or "Noemie car (UGC)",
        "format": "9:16",
        "platform": ["tiktok", "meta_reels"],
        "compliance": "No medical/disease/income claims. Lifestyle language only.",
    }
    out: dict[str, Any] = {"brief": brief}
    if render:
        out["render"] = generate_ugc_avatar_video(
            script=f"{hook}. {script_15s}",
            avatar=brief["avatar"],
            product_name=product_name,
            hook=hook,
        )
    return out


def get_fal_tools() -> list:
    return [
        list_fal_avatars,
        generate_ugc_avatar_video,
        generate_product_image,
        build_ugc_brief_and_render,
    ]
