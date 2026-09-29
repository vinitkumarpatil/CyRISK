"""Explainable financial cyber-risk model: SLE, ARO, ALE per finding.

All figures are MODELLED ESTIMATES derived from supplied assumptions — not
actual or booked losses. Every intermediate value is returned for inspection.
"""
from __future__ import annotations
import math
from .constants import (
    SEVERITY_EF, SEVERITY_DOWNTIME_DAYS, SEVERITY_FACTOR, EF_CAP,
    SEVERITY_BASE_RATE, EXPOSURE_MULT_INTERNET, EXPOSURE_MULT_EXPLOIT,
    EXPOSURE_MULT_NO_PATCH, CONTROL_FREQ_REDUCTION, ML_BLEND_LOW, ML_BLEND_SPAN,
)

DEFAULT_ASSUMPTIONS = {
    "breach_cost_per_record_inr": 1200.0,
    "recovery_base_inr": 1_500_000.0,
    "regulatory_penalty_base_inr": 20_000_000.0,
    "reputation_base_inr": 5_000_000.0,
    "recovery_asset_fraction": 0.05,
}


def impact_components(asset: dict, vuln: dict, criticality: float, assumptions: dict) -> dict:
    sev = vuln.get("severity", "Medium")
    sf = SEVERITY_FACTOR.get(sev, 0.45)
    ef = min(EF_CAP, SEVERITY_EF.get(sev, 0.2) * (0.8 + 0.06 * asset.get("data_sensitivity", 0)))

    asset_impact = asset.get("business_value_inr", 0.0) * ef
    downtime = asset.get("revenue_impact_per_day_inr", 0.0) * SEVERITY_DOWNTIME_DAYS.get(sev, 1.0)
    records = asset.get("records_count", 0)
    data_breach = records * assumptions["breach_cost_per_record_inr"] * (asset.get("data_sensitivity", 0) / 5.0) * sf
    recovery = assumptions["recovery_base_inr"] * sf + assumptions["recovery_asset_fraction"] * asset.get("business_value_inr", 0.0) * sf
    regulated = records > 0 or asset.get("regulatory_importance", 0) >= 3
    regulatory = assumptions["regulatory_penalty_base_inr"] * (asset.get("regulatory_importance", 0) / 5.0) * sf if regulated else 0.0
    reputation = assumptions["reputation_base_inr"] * (criticality / 100.0) * sf

    components = {
        "asset_business_impact": round(asset_impact, 2),
        "downtime_cost": round(downtime, 2),
        "data_breach_cost": round(data_breach, 2),
        "recovery_cost": round(recovery, 2),
        "regulatory_penalty": round(regulatory, 2),
        "reputation_cost": round(reputation, 2),
    }
    sle = round(sum(components.values()), 2)
    return {"components": components, "exposure_factor": round(ef, 4), "sle_inr": sle,
            "severity_factor": sf}


def frequency(vuln: dict, control_eff: float, threat_relevance: float, ml_prob: float) -> dict:
    sev = vuln.get("severity", "Medium")
    base = SEVERITY_BASE_RATE.get(sev, 0.15) * (0.5 + vuln.get("cvss", 5.0) / 20.0)
    exp_mult = 1.0
    if vuln.get("internet_exposed"):
        exp_mult *= EXPOSURE_MULT_INTERNET
    if vuln.get("exploit_available"):
        exp_mult *= EXPOSURE_MULT_EXPLOIT
    if not vuln.get("patch_available", True):
        exp_mult *= EXPOSURE_MULT_NO_PATCH
    age_mult = 1.0 + min(0.5, vuln.get("age_days", 0) / 730.0)
    threat_mult = 1.0 + max(0.0, min(1.0, threat_relevance))

    raw_lambda = base * exp_mult * age_mult * threat_mult
    after_controls = raw_lambda * (1 - CONTROL_FREQ_REDUCTION * control_eff)
    ml_mult = ML_BLEND_LOW + ML_BLEND_SPAN * ml_prob
    aro = max(0.0, after_controls * ml_mult)
    return {
        "base_rate": round(base, 4), "exposure_multiplier": round(exp_mult, 3),
        "age_multiplier": round(age_mult, 3), "threat_multiplier": round(threat_mult, 3),
        "raw_lambda": round(raw_lambda, 4), "control_effectiveness": round(control_eff, 4),
        "after_controls": round(after_controls, 4), "ml_probability": round(ml_prob, 4),
        "ml_multiplier": round(ml_mult, 3), "aro": round(aro, 4),
        "annualized_likelihood": round(1 - math.exp(-aro), 4),
    }


def compute_finding(asset, vuln, criticality, control_eff, threat_relevance, ml_prob, assumptions) -> dict:
    imp = impact_components(asset, vuln, criticality, assumptions)
    freq = frequency(vuln, control_eff, threat_relevance, ml_prob)
    ale = round(imp["sle_inr"] * freq["aro"], 2)
    return {
        "sle_inr": imp["sle_inr"], "aro": freq["aro"], "ale_inr": ale,
        "likelihood": freq["annualized_likelihood"], "exposure_factor": imp["exposure_factor"],
        "impact": imp, "frequency": freq,
        "formula": "SLE = Σ impact components ; ALE = SLE × ARO",
    }
