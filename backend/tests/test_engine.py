"""Unit tests for the risk engine's core, deterministic maths.

These exercise the financial model, the frequency/control coupling, the 0/1
knapsack optimizer primitive, the framework-status bands and — importantly —
that framework assessment accepts the tuple-shaped catalog controls.
"""
import math

from app.engine import financial, optimizer, frameworks_data, saturating, fmt_inr


ASSET = {
    "business_value_inr": 50_000_000.0,
    "revenue_impact_per_day_inr": 2_000_000.0,
    "records_count": 100_000,
    "data_sensitivity": 4,
    "regulatory_importance": 4,
}

VULN = {
    "severity": "Critical", "cvss": 9.8, "category": "web",
    "internet_exposed": True, "exploit_available": True,
    "patch_available": False, "age_days": 120,
}


def test_sle_is_sum_of_components_and_ale_is_sle_times_aro():
    f = financial.compute_finding(ASSET, VULN, criticality=80.0, control_eff=0.5,
                                  threat_relevance=0.7, ml_prob=0.6,
                                  assumptions=financial.DEFAULT_ASSUMPTIONS)
    comps = f["impact"]["components"]
    assert abs(f["sle_inr"] - round(sum(comps.values()), 2)) < 0.01
    assert abs(f["ale_inr"] - round(f["sle_inr"] * f["aro"], 2)) < 0.01
    assert all(v >= 0 for v in comps.values())
    assert 0.0 <= f["likelihood"] < 1.0
    assert f["aro"] >= 0.0


def test_stronger_controls_reduce_frequency():
    weak = financial.frequency(VULN, control_eff=0.1, threat_relevance=0.5, ml_prob=0.5)
    strong = financial.frequency(VULN, control_eff=0.9, threat_relevance=0.5, ml_prob=0.5)
    assert strong["aro"] < weak["aro"]


def test_exposure_multipliers_increase_frequency():
    exposed = financial.frequency(VULN, 0.5, 0.5, 0.5)["exposure_multiplier"]
    calm = financial.frequency({**VULN, "internet_exposed": False,
                                "exploit_available": False, "patch_available": True},
                               0.5, 0.5, 0.5)["exposure_multiplier"]
    assert exposed > calm


def test_knapsack_is_optimal_and_within_budget():
    items = [{"cost_lakh": 2, "value": 3.0}, {"cost_lakh": 3, "value": 4.0},
             {"cost_lakh": 4, "value": 5.0}, {"cost_lakh": 5, "value": 6.0}]
    chosen = optimizer._knapsack(items, budget_lakh=5)
    assert set(chosen) == {0, 1}                       # cost 5, value 7 is optimal
    assert sum(items[i]["cost_lakh"] for i in chosen) <= 5


def test_knapsack_empty_budget_selects_nothing():
    items = [{"cost_lakh": 3, "value": 4.0}]
    assert optimizer._knapsack(items, budget_lakh=0) == []


def test_saturating_maps_reference_to_half_and_is_monotonic():
    assert abs(saturating(100.0, 100.0) - 0.5) < 1e-9
    assert saturating(50.0, 100.0) < saturating(200.0, 100.0)
    assert saturating(0.0, 100.0) == 0.0


def test_fmt_inr_indian_convention():
    assert fmt_inr(0) == "₹0"
    assert fmt_inr(2_50_00_000).endswith("Cr")     # crore
    assert fmt_inr(3_50_000).endswith("L")         # lakh
    assert fmt_inr(-1_00_00_000).startswith("-₹")


def test_status_bands():
    assert frameworks_data.status_for(0.9) == "Covered"
    assert frameworks_data.status_for(0.6) == "Partial"
    assert frameworks_data.status_for(0.35) == "Potential Gap"
    assert frameworks_data.status_for(0.1) == "Review Required"
    assert frameworks_data.status_for(None) == "Review Required"


def test_assess_frameworks_accepts_tuple_controls():
    """Catalog controls are 4-tuples (ref, category, title, internal_key)."""
    defs = [{
        "key": "demo", "name": "Demo FW", "full_name": "Demo", "version": "1",
        "controls": [
            ("D.1", "Access", "MFA everywhere", "mfa"),
            ("D.2", "Patch", "Patch management", "patch_management"),
        ],
    }]
    out = frameworks_data.assess_frameworks(defs, {"mfa": 0.8, "patch_management": 0.4})
    assert len(out) == 1
    fw = out[0]
    assert fw["control_count"] == 2
    statuses = {c["control_ref"]: c["status"] for c in fw["controls"]}
    assert statuses["D.1"] == "Covered"
    assert statuses["D.2"] == "Potential Gap"
    assert 0.0 <= fw["assessment_index"] <= 100.0
