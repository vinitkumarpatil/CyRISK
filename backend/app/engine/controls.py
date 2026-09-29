"""Transparent control effectiveness scoring from demo telemetry."""
from __future__ import annotations
from .constants import (
    CONTROL_WEIGHTS, COMPLIANCE_SCORE, INCIDENT_PENALTY_PER_EVENT,
    INCIDENT_PENALTY_CAP, INCIDENT_CONTROL_KEYWORDS,
)
from . import clamp


def related_incident_count(control_key: str, incidents: list) -> int:
    n = 0
    for inc in incidents:
        text = f"{inc.get('root_cause', '')} {inc.get('category', '')} {inc.get('title', '')}".lower()
        for kw, ckey in INCIDENT_CONTROL_KEYWORDS.items():
            if ckey == control_key and kw in text:
                n += 1
                break
    return n


def compute_effectiveness(control: dict, incidents: list | None = None) -> dict:
    """Blend configuration strength, coverage, compliance, maturity and
    monitoring, then apply a penalty for related historical incidents."""
    incidents = incidents or []
    w = CONTROL_WEIGHTS
    compliance = COMPLIANCE_SCORE.get(control.get("compliance_status", "Partial"), 0.5)
    maturity_n = clamp(control.get("maturity", 0) / 5.0)
    monitoring = 1.0 if control.get("monitored") else 0.0

    components = {
        "config_strength": (clamp(control.get("config_strength", 0.0)), w["config_strength"]),
        "coverage": (clamp(control.get("coverage", 0.0)), w["coverage"]),
        "compliance": (compliance, w["compliance"]),
        "maturity": (maturity_n, w["maturity"]),
        "monitoring": (monitoring, w["monitoring"]),
    }
    base = sum(val * weight for (val, weight) in components.values())

    n_inc = related_incident_count(control.get("key", ""), incidents)
    penalty = min(INCIDENT_PENALTY_CAP, INCIDENT_PENALTY_PER_EVENT * n_inc)
    effectiveness = clamp(base * (1 - penalty), 0.02, 0.99)

    breakdown = [
        {"name": k, "value": round(v, 4), "weight": wt, "contribution": round(v * wt, 4)}
        for k, (v, wt) in components.items()
    ]
    return {
        "effectiveness": round(effectiveness, 4),
        "base": round(base, 4),
        "incident_penalty": round(penalty, 4),
        "related_incidents": n_inc,
        "breakdown": breakdown,
        "rating": _rating(effectiveness),
        "formula": "effectiveness = (Σ weight×factor) × (1 − incident_penalty)",
    }


def _rating(e: float) -> str:
    if e >= 0.75:
        return "Strong"
    if e >= 0.5:
        return "Moderate"
    if e >= 0.3:
        return "Weak"
    return "Critical Gap"
