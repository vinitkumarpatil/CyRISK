"""What-if scenario engine.

Applies a list of mutations to a *cloned* enterprise state and recomputes risk,
so every "before vs after" number is genuinely recalculated — never faked.
Also translates an InvestmentOption (action + params) into concrete mutations,
which is what the optimizer and recommendation engines build on.
"""
from __future__ import annotations

from .state import clone_state
from . import risk_engine

ACTIVE = {"open", "remediating"}


def _match_vuln(v: dict, filt: dict) -> bool:
    if not filt:
        return True
    if "category" in filt and v.get("category") != filt["category"]:
        return False
    if "severity" in filt and v.get("severity") != filt["severity"]:
        return False
    if "severity_in" in filt and v.get("severity") not in filt["severity_in"]:
        return False
    if "min_cvss" in filt and v.get("cvss", 0.0) < filt["min_cvss"]:
        return False
    if "internet_exposed" in filt and bool(v.get("internet_exposed")) != bool(filt["internet_exposed"]):
        return False
    if "exploit_available" in filt and bool(v.get("exploit_available")) != bool(filt["exploit_available"]):
        return False
    if "status_in" in filt and v.get("status") not in filt["status_in"]:
        return False
    if "asset_id" in filt and v.get("asset_id") != filt["asset_id"]:
        return False
    if "category_in" in filt and v.get("category") not in filt["category_in"]:
        return False
    return True


def _apply_set(v: dict, changes: dict) -> None:
    for k, val in changes.items():
        v[k] = val


# __APPEND_SCENARIOS__


def apply_mutations(state: dict, mutations: list) -> list:
    """Mutate `state` in place. Returns a human-readable list of applied effects."""
    log = []
    controls_by_key = {c["key"]: c for c in state.get("controls", [])}
    for m in mutations or []:
        op = m.get("op")
        if op in ("set_control", "improve_control", "degrade_control"):
            c = controls_by_key.get(m.get("control_key"))
            if c:
                for k, val in (m.get("fields") or {}).items():
                    c[k] = val
                log.append(f"{op}: {m.get('control_key')} -> {m.get('fields')}")
        elif op in ("patch_vulns", "reduce_exposure"):
            changes = dict(m.get("set") or {})
            if op == "reduce_exposure" and not changes:
                changes = {"internet_exposed": False}
            n = 0
            for v in state.get("vulns", []):
                if v.get("status") in ACTIVE and _match_vuln(v, m.get("filter") or {}):
                    _apply_set(v, changes)
                    n += 1
            log.append(f"{op}: {n} vulns matched -> {changes}")
        elif op == "add_vuln":
            v = dict(m.get("vuln") or {})
            v.setdefault("id", _next_vuln_id(state))
            v.setdefault("status", "open")
            v.setdefault("severity", "High")
            v.setdefault("category", "software")
            v.setdefault("cvss", 8.0)
            v.setdefault("patch_available", True)
            v.setdefault("exploit_available", False)
            v.setdefault("internet_exposed", False)
            v.setdefault("age_days", 1)
            state.setdefault("vulns", []).append(v)
            log.append(f"add_vuln: {v.get('title', 'new vulnerability')} on asset {v.get('asset_id')}")
        elif op == "change_assumption":
            key, val = m.get("key"), m.get("value")
            if key is not None:
                state.setdefault("assumptions", {})[key] = val
                log.append(f"change_assumption: {key} -> {val}")
        elif op == "delay_remediation":
            add = int(m.get("add_age_days", 90))
            n = 0
            for v in state.get("vulns", []):
                if v.get("status") in ACTIVE and _match_vuln(v, m.get("filter") or {}):
                    v["age_days"] = v.get("age_days", 0) + add
                    n += 1
            log.append(f"delay_remediation: +{add}d on {n} vulns")
    return log


def _next_vuln_id(state: dict) -> int:
    ids = [v.get("id", 0) for v in state.get("vulns", [])]
    return (max(ids) + 1) if ids else 1


def investment_to_mutations(option: dict) -> list:
    """Translate an InvestmentOption dict (key/action/control_key/params) into mutations."""
    action = option.get("action", "improve_control")
    params = option.get("params") or {}
    if action == "improve_control":
        return [{"op": "set_control", "control_key": option.get("control_key"),
                 "fields": params.get("target") or {}}]
    if action == "patch_vulns":
        return [{"op": "patch_vulns", "filter": params.get("filter") or {},
                 "set": params.get("set") or {"status": "closed"}}]
    if action == "reduce_exposure":
        return [{"op": "reduce_exposure", "filter": params.get("filter") or {},
                 "set": params.get("set") or {"internet_exposed": False}}]
    return []


def evaluate(state: dict, run_ml: bool = True, run_var: bool = True) -> dict:
    return risk_engine.compute(state, run_ml=run_ml, run_var=run_var)


def key_metrics(result: dict) -> dict:
    e = result["enterprise"]
    return {
        "risk_score": e["risk_score"], "risk_band": e["risk_band"],
        "total_ale_inr": e["total_ale_inr"], "total_exposure_inr": e["total_exposure_inr"],
        "var95_inr": e["var95_inr"], "var99_inr": e["var99_inr"],
        "avg_control_effectiveness": e["avg_control_effectiveness"],
        "open_vulns": e["open_vulns"], "critical_vulns": e["critical_vulns"],
    }


def rosi_percent(ale_reduction: float, cost: float) -> float | None:
    """Return on Security Investment = (annual ALE reduction − cost) / cost, as %."""
    if not cost:
        return None
    return round((ale_reduction - cost) / cost * 100.0, 1)


def simulate(base_state: dict, mutations: list, cost_inr: float = 0.0,
             label: str = "", baseline: dict | None = None,
             run_var: bool = True) -> dict:
    """Apply mutations to a clone of base_state and return before/after/delta."""
    before = baseline or evaluate(base_state, run_var=run_var)
    after_state = clone_state(base_state)
    applied = apply_mutations(after_state, mutations)
    after = evaluate(after_state, run_var=run_var)

    b, a = key_metrics(before), key_metrics(after)
    ale_reduction = round(b["total_ale_inr"] - a["total_ale_inr"], 2)
    delta = {
        "ale_reduction_inr": ale_reduction,
        "ale_reduction_pct": round(ale_reduction / b["total_ale_inr"] * 100, 2) if b["total_ale_inr"] else 0.0,
        "exposure_reduction_inr": round(b["total_exposure_inr"] - a["total_exposure_inr"], 2),
        "var95_reduction_inr": round(b["var95_inr"] - a["var95_inr"], 2),
        "risk_score_delta": round(a["risk_score"] - b["risk_score"], 2),
        "control_eff_delta": round(a["avg_control_effectiveness"] - b["avg_control_effectiveness"], 4),
    }
    return {
        "label": label, "cost_inr": cost_inr, "applied": applied,
        "before": b, "after": a, "delta": delta,
        "rosi_percent": rosi_percent(ale_reduction, cost_inr),
        "before_full": before, "after_full": after,
    }


def marginal_ale_reduction(base_state: dict, option: dict, baseline: dict) -> float:
    """ALE reduction from applying a single investment option (for optimizer scoring)."""
    after_state = clone_state(base_state)
    apply_mutations(after_state, investment_to_mutations(option))
    after = evaluate(after_state, run_var=False)
    return round(baseline["enterprise"]["total_ale_inr"] - after["enterprise"]["total_ale_inr"], 2)


