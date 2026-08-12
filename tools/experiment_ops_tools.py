"""Experimentation / CRO design tools."""

from __future__ import annotations

from typing import Any


def experiment_design(
    hypothesis: str,
    primary_metric: str = "cvr",
    baseline_rate: float = 0.02,
    mde_rel: float = 0.15,
    variants: list[str] | None = None,
) -> dict[str, Any]:
    """Draft experiment design with rough sample guidance."""
    # very rough rule-of-thumb sample per variant
    p = max(0.001, baseline_rate)
    n_per = int((16 * p * (1 - p)) / max(1e-6, (p * mde_rel) ** 2))
    return {
        "ok": True,
        "hypothesis": hypothesis,
        "primary_metric": primary_metric,
        "baseline_rate": baseline_rate,
        "mde_rel": mde_rel,
        "variants": variants or ["control", "treatment"],
        "approx_n_per_variant": n_per,
        "duration_days_hint": 14,
        "note": "Heuristic sample size — validate with analyst for high stakes.",
    }


def experiment_ice_score(impact: float = 5, confidence: float = 5, ease: float = 5) -> dict[str, Any]:
    """ICE prioritization (1-10 each)."""
    for name, v in [("impact", impact), ("confidence", confidence), ("ease", ease)]:
        if not 1 <= float(v) <= 10:
            return {"ok": False, "error": f"{name} must be 1-10"}
    score = (float(impact) + float(confidence) + float(ease)) / 3.0
    return {"ok": True, "ice": round(score, 2), "impact": impact, "confidence": confidence, "ease": ease}


def experiment_decision_rule(
    primary_metric: str = "cvr",
    min_lift: float = 0.1,
    guardrail_refund_rate_max: float = 0.08,
    guardrail_min_roas: float = 1.5,
) -> dict[str, Any]:
    """Pre-register win/kill rules."""
    return {
        "ok": True,
        "win_if": f"{primary_metric} lift >= {min_lift:.0%} and guardrails hold",
        "kill_if": "flat/negative primary after planned sample OR guardrail breach",
        "guardrails": {
            "refund_rate_max": guardrail_refund_rate_max,
            "min_roas": guardrail_min_roas,
        },
        "no_peeking": True,
    }


def get_experiment_ops_tools() -> list:
    return [experiment_design, experiment_ice_score, experiment_decision_rule]
