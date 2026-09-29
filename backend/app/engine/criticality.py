"""Transparent asset criticality scoring."""
from __future__ import annotations
from .constants import (
    CRITICALITY_WEIGHTS, BUSINESS_VALUE_REF_INR, REVENUE_PER_DAY_REF_INR,
    DEPENDENCY_REF,
)
from . import saturating


def _tier(score: float) -> str:
    if score >= 80:
        return "Critical"
    if score >= 60:
        return "High"
    if score >= 40:
        return "Medium"
    return "Low"


def compute_criticality(asset: dict) -> dict:
    """Return criticality score (0-100) with a full factor breakdown.

    Each factor is normalised to 0-1, weighted, and summed. The breakdown is
    surfaced verbatim in the UI so a user can see *why* an asset is critical.
    """
    factors = []

    def add(name, raw, normalized):
        w = CRITICALITY_WEIGHTS[name]
        norm = max(0.0, min(1.0, normalized))
        contribution = round(100 * w * norm, 2)
        factors.append({
            "name": name,
            "raw": raw,
            "normalized": round(norm, 4),
            "weight": w,
            "contribution": contribution,
        })

    add("data_sensitivity", asset.get("data_sensitivity", 0), asset.get("data_sensitivity", 0) / 5.0)
    add("operational_criticality", asset.get("operational_criticality", 0), asset.get("operational_criticality", 0) / 5.0)
    add("regulatory_importance", asset.get("regulatory_importance", 0), asset.get("regulatory_importance", 0) / 5.0)
    add("business_value", asset.get("business_value_inr", 0.0), saturating(asset.get("business_value_inr", 0.0), BUSINESS_VALUE_REF_INR))
    add("revenue_impact", asset.get("revenue_impact_per_day_inr", 0.0), saturating(asset.get("revenue_impact_per_day_inr", 0.0), REVENUE_PER_DAY_REF_INR))
    add("dependency", asset.get("dep_count", 0), min(1.0, asset.get("dep_count", 0) / DEPENDENCY_REF))

    score = round(sum(f["contribution"] for f in factors), 2)
    return {
        "score": score,
        "tier": _tier(score),
        "factors": factors,
        "formula": "criticality = 100 × Σ (weight_i × normalised_factor_i)",
    }
