"""Data-driven mitigation recommendations.

For each candidate investment we actually re-simulate the enterprise state and
measure the ₹ ALE reduction, the assets whose risk falls, and the ROSI. Nothing
is hardcoded — remove an investment or change the data and the recommendations,
their ordering and their financials all change.
"""
from __future__ import annotations

from .state import clone_state
from . import scenarios


def _priority(reduction: float, base_ale: float) -> str:
    if base_ale <= 0:
        return "Low"
    frac = reduction / base_ale
    if frac >= 0.15:
        return "Critical"
    if frac >= 0.07:
        return "High"
    if frac >= 0.02:
        return "Medium"
    return "Low"


def recommend(base_state: dict, options: list, top: int = 8, baseline: dict | None = None) -> list:
    baseline = baseline or scenarios.evaluate(base_state)
    base_ale = baseline["enterprise"]["total_ale_inr"]
    base_by_asset = {a["asset_id"]: a for a in baseline["by_asset"]}
    ctrl_by_key = {c["key"]: c for c in baseline["controls"]}

    recs = []
    for o in options:
        mutations = scenarios.investment_to_mutations(o)
        after_state = clone_state(base_state)
        scenarios.apply_mutations(after_state, mutations)
        after = scenarios.evaluate(after_state, run_var=False)
        after_by_asset = {a["asset_id"]: a["ale_inr"] for a in after["by_asset"]}

        reduction = round(base_ale - after["enterprise"]["total_ale_inr"], 2)
        if reduction <= 0:
            continue

        affected = []
        for aid, ba in base_by_asset.items():
            d = ba["ale_inr"] - after_by_asset.get(aid, 0.0)
            if d > 1.0:
                affected.append({"asset_id": aid, "name": ba["name"],
                                 "ale_reduction_inr": round(d, 2)})
        affected.sort(key=lambda x: x["ale_reduction_inr"], reverse=True)

        ctrl = ctrl_by_key.get(o.get("control_key", ""))
        recs.append({
            "key": o["key"], "title": o["name"], "control_key": o.get("control_key", ""),
            "category": o.get("category", ""), "action": o.get("action", ""),
            "cost_inr": o["cost"], "effort": o.get("effort", "Medium"),
            "priority": _priority(reduction, base_ale),
            "expected_ale_reduction_inr": reduction,
            "expected_risk_reduction": round(reduction / base_ale, 4) if base_ale else 0.0,
            "rosi_percent": scenarios.rosi_percent(reduction, o["cost"]),
            "affected_asset_ids": [a["asset_id"] for a in affected],
            "affected_assets": affected[:6],
            "rationale": {
                "why": _why(o, ctrl, affected),
                "current_control": ({"key": ctrl["key"], "name": ctrl["name"],
                                     "effectiveness": ctrl["effectiveness"], "rating": ctrl["rating"]}
                                    if ctrl else None),
                "assets_affected": len(affected),
                "formula": "ROSI = (annual ALE reduction − cost) / cost; "
                           "reduction is re-simulated, not assumed.",
                "disclaimer": "Modelled estimate on synthetic demo data.",
            },
        })

    recs.sort(key=lambda r: r["expected_ale_reduction_inr"], reverse=True)
    return recs[:top]


def _why(option: dict, ctrl: dict | None, affected: list) -> str:
    action = option.get("action")
    n = len(affected)
    if action == "improve_control" and ctrl:
        return (f"{ctrl['name']} is currently {ctrl['rating'].lower()} "
                f"(effectiveness {ctrl['effectiveness']:.2f}); strengthening it lowers "
                f"attack frequency across {n} asset(s).")
    if action == "patch_vulns":
        return f"Remediating the targeted vulnerabilities removes exposure on {n} asset(s)."
    if action == "reduce_exposure":
        return f"Reducing internet exposure cuts likelihood on {n} internet-facing asset(s)."
    return f"Reduces modelled annual loss across {n} asset(s)."
