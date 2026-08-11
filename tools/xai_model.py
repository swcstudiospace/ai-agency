"""Grok / xAI model factory for Agno agents (SuperGrok OAuth or API key)."""

from __future__ import annotations

import logging
import os

from agno.models.openai import OpenAIChat

from tools.xai_oauth_pkce import XaiOAuthError, get_xai_token_or_fallback

logger = logging.getLogger(__name__)

# SuperGrok subscription chat models (verified against /v1/models on this tier).
# Multi-agent variants are NOT valid on /chat/completions.
DEFAULT_GROK_MODEL = (os.getenv("AGENCY_GROK_MODEL") or os.getenv("XAI_MODEL") or "grok-4.5").strip()


def get_grok_model(model_id: str | None = None, temperature: float = 0.3) -> OpenAIChat:
    """Build an OpenAI-compatible Grok model for SuperGrok / xAI.

    Token resolution (see ``xai_oauth_pkce``):
      1. ``XAI_API_KEY``
      2. Project OAuth store ``~/.config/ai-agency/xai_oauth.json``
      3. Hermes SuperGrok device-code tokens (``~/.hermes/auth.json`` / credential pool)

    Import-safe: missing credentials → placeholder key so AgentOS can boot;
    real runs need SuperGrok login: ``python -m tools.xai_oauth_pkce login``
    """
    mid = (model_id or DEFAULT_GROK_MODEL or "grok-4.5").strip()
    try:
        api_key = get_xai_token_or_fallback()
    except XaiOAuthError as exc:
        logger.warning("xAI credentials not ready (%s); using placeholder until login", exc.code)
        api_key = "missing-xai-credentials"
    base_url = (os.getenv("XAI_BASE_URL") or "https://api.x.ai/v1").rstrip("/")
    return OpenAIChat(
        id=mid,
        api_key=api_key,
        base_url=base_url,
        temperature=temperature,
    )
