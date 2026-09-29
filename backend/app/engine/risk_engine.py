"""Risk engine orchestrator: turns enterprise state into explainable risk."""
from __future__ import annotations
from datetime import datetime, timezone

import numpy as np

from . import criticality as crit_mod
from . import controls as ctrl_mod
from . import financial as fin
from . import saturating
from .constants import (
    VULN_CATEGORY_CONTROLS, BASELINE_CONTROLS, ALE_REF_INR, RISK_SCORE_W_ALE,
    RISK_SCORE_W_CONTROL, RISK_SCORE_W_CRITVULN, CRITVULN_REF, VAR_SIMULATIONS,
    VAR_SEVERITY_SIGMA, VAR_SEED,
)
from .ml_model import get_model

ACTIVE_STATUSES = {"open", "remediating"}

THREAT_VULN_MATCH = {
    "ransomware": ["software", "patch", "config"],
    "phishing": ["identity", "web"],
    "web_attack": ["web"],
    "insider": ["identity", "config"],
    "ddos": ["network"],
    "supply_chain": ["software"],
    "apt": ["software", "network", "identity", "config"],
}


def control_effectiveness_map(state: dict) -> dict:
    incidents = state.get("incidents", [])
    out = {}
    for c in state.get("controls", []):
        detail = ctrl_mod.compute_effectiveness(c, incidents)
        out[c["key"]] = {"control": c, "effectiveness": detail["effectiveness"], "detail": detail}
    return out


def blended_control_eff(vuln: dict, ceff_map: dict):
    keys = list(dict.fromkeys(VULN_CATEGORY_CONTROLS.get(vuln.get("category", ""), []) + BASELINE_CONTROLS))
    vals, used = [], []
    for k in keys:
        if k in ceff_map:
            vals.append(ceff_map[k]["effectiveness"])
            used.append({"key": k, "effectiveness": ceff_map[k]["effectiveness"]})
    return (sum(vals) / len(vals) if vals else 0.0), used


def threat_relevance_for(vuln: dict, threats: list) -> float:
    best = 0.0
    for t in threats:
        match = 1.0 if vuln.get("category") in THREAT_VULN_MATCH.get(t.get("category", ""), []) else 0.4
        best = max(best, t.get("relevance", 0.0) * match)
    return best

# __APPEND__

def monte_carlo_var(findings: list, sims: int = VAR_SIMULATIONS,
                    sigma: float = VAR_SEVERITY_SIGMA, seed: int = VAR_SEED) -> dict:
    """Annual-loss distribution via Poisson(frequency) × lognormal(severity).
    Approximate portfolio VaR — documented as a modelled statistical estimate."""
    if not findings:
        return {"var95_inr": 0.0, "var99_inr": 0.0, "mean_inr": 0.0, "simulations": sims}
    rng = np.random.default_rng(seed)
    aros = np.array([max(0.0, f["aro"]) for f in findings])
    sles = np.array([max(0.0, f["sle_inr"]) for f in findings])
    counts = rng.poisson(aros, size=(sims, len(findings)))
    sev = rng.lognormal(mean=-0.5 * sigma ** 2, sigma=sigma, size=(sims, len(findings)))
    annual = (counts * sles * sev).sum(axis=1)
    return {
        "var95_inr": round(float(np.percentile(annual, 95)), 2),
        "var99_inr": round(float(np.percentile(annual, 99)), 2),
        "mean_inr": round(float(annual.mean()), 2),
        "p50_inr": round(float(np.percentile(annual, 50)), 2),
        "simulations": sims,
    }


def _asset_ml_features(asset, asset_vulns, avg_ctrl_eff, threat_pressure, incident_count) -> dict:
    active = [v for v in asset_vulns if v.get("status") in ACTIVE_STATUSES]
    return {
        "criticality": asset["_criticality"],
        "open_vulns": len(active),
        "critical_vulns": sum(1 for v in active if v.get("severity") == "Critical"),
        "max_cvss": max([v.get("cvss", 0.0) for v in active], default=0.0),
        "internet_facing": 1 if asset.get("internet_facing") else 0,
        "avg_control_eff": avg_ctrl_eff,
        "data_sensitivity": asset.get("data_sensitivity", 0),
        "exploit_present": 1 if any(v.get("exploit_available") for v in active) else 0,
        "threat_pressure": threat_pressure,
        "past_incidents": incident_count,
    }


def _risk_score(total_ale, avg_ctrl_eff, critical_vulns):
    ale_comp = 100 * saturating(total_ale, ALE_REF_INR)
    ctrl_comp = 100 * (1 - avg_ctrl_eff)
    critv_comp = 100 * min(1.0, critical_vulns / CRITVULN_REF)
    score = (RISK_SCORE_W_ALE * ale_comp + RISK_SCORE_W_CONTROL * ctrl_comp
             + RISK_SCORE_W_CRITVULN * critv_comp)
    band = "Critical" if score >= 75 else "High" if score >= 50 else "Medium" if score >= 25 else "Low"
    return round(min(100.0, score), 2), band, {
        "ale_component": round(ale_comp, 2), "control_component": round(ctrl_comp, 2),
        "critical_vuln_component": round(critv_comp, 2),
        "weights": {"ale": RISK_SCORE_W_ALE, "control": RISK_SCORE_W_CONTROL, "critical_vulns": RISK_SCORE_W_CRITVULN},
    }

# __APPEND2__

def compute(state: dict, run_ml: bool = True, run_var: bool = True) -> dict:
    threats = state.get("threats", [])
    incidents = state.get("incidents", [])
    threat_pressure = max([t.get("relevance", 0.0) for t in threats], default=0.0)

    ceff_map = control_effectiveness_map(state)
    ctrl_effs = [c["effectiveness"] for c in ceff_map.values()]
    avg_ctrl_eff = round(sum(ctrl_effs) / len(ctrl_effs), 4) if ctrl_effs else 0.0

    crit_by_asset = {}
    for a in state["assets"]:
        cd = crit_mod.compute_criticality(a)
        a["_criticality"] = cd["score"]
        crit_by_asset[a["id"]] = cd

    vulns_by_asset = {}
    for v in state["vulns"]:
        vulns_by_asset.setdefault(v["asset_id"], []).append(v)
    incidents_by_asset = {}
    for i in incidents:
        if i.get("asset_id"):
            incidents_by_asset[i["asset_id"]] = incidents_by_asset.get(i["asset_id"], 0) + 1

    model = get_model() if run_ml else None
    ml_prob_by_asset = {}
    for a in state["assets"]:
        feats = _asset_ml_features(a, vulns_by_asset.get(a["id"], []), avg_ctrl_eff,
                                   threat_pressure, incidents_by_asset.get(a["id"], 0))
        a["_ml_features"] = feats
        ml_prob_by_asset[a["id"]] = model.predict_proba_one(feats) if model else 0.5

    asset_by_id = {a["id"]: a for a in state["assets"]}
    findings = []
    for v in state["vulns"]:
        if v.get("status") not in ACTIVE_STATUSES:
            continue
        a = asset_by_id.get(v["asset_id"])
        if a is None:
            continue
        ceff, used = blended_control_eff(v, ceff_map)
        trel = threat_relevance_for(v, threats)
        mlp = ml_prob_by_asset.get(a["id"], 0.5)
        f = fin.compute_finding(a, v, a["_criticality"], ceff, trel, mlp, state["assumptions"])
        f.update({
            "asset_id": a["id"], "asset_name": a["name"], "bu_name": a["bu_name"],
            "vuln_id": v["id"], "title": v["title"], "cve_id": v.get("cve_id", ""),
            "severity": v["severity"], "category": v["category"],
            "controls_considered": used, "ml_probability": mlp,
        })
        findings.append(f)
# __APPEND3__
    total_ale = round(sum(f["ale_inr"] for f in findings), 2)
    total_exposure = round(sum(f["sle_inr"] for f in findings), 2)
    active_vulns = [v for v in state["vulns"] if v.get("status") in ACTIVE_STATUSES]
    critical_vulns = sum(1 for v in active_vulns if v.get("severity") == "Critical")
    likelihood_avg = round(sum(f["likelihood"] for f in findings) / len(findings), 4) if findings else 0.0
    score, band, score_detail = _risk_score(total_ale, avg_ctrl_eff, critical_vulns)
    var = monte_carlo_var(findings) if run_var else {
        "var95_inr": 0.0, "var99_inr": 0.0, "mean_inr": 0.0, "p50_inr": 0.0, "simulations": 0}

    ranked = sorted(findings, key=lambda f: f["ale_inr"], reverse=True)
    contributors = []
    for f in ranked[:12]:
        weak = min(f["controls_considered"], key=lambda c: c["effectiveness"], default=None)
        contributors.append({
            "label": f"{f['title']} — {f['asset_name']}", "asset_id": f["asset_id"],
            "vuln_id": f["vuln_id"], "severity": f["severity"], "category": f["category"],
            "ale_inr": f["ale_inr"], "share": round(f["ale_inr"] / total_ale, 4) if total_ale else 0.0,
            "likelihood": f["likelihood"], "sle_inr": f["sle_inr"],
            "control_weakness": (weak["key"] if weak else ""),
            "recommended_action": _action_for(f["category"]),
            "expected_reduction_inr": f["ale_inr"],
        })

    def _agg(key_fn):
        acc = {}
        for f in findings:
            k = key_fn(f)
            d = acc.setdefault(k, {"ale_inr": 0.0, "exposure_inr": 0.0, "count": 0})
            d["ale_inr"] += f["ale_inr"]; d["exposure_inr"] += f["sle_inr"]; d["count"] += 1
        return acc

    by_asset = []
    aa = _agg(lambda f: f["asset_id"])
    for aid, d in aa.items():
        a = asset_by_id[aid]
        by_asset.append({"asset_id": aid, "name": a["name"], "bu_name": a["bu_name"],
                         "criticality": a["_criticality"], "tier": crit_by_asset[aid]["tier"],
                         "ale_inr": round(d["ale_inr"], 2), "exposure_inr": round(d["exposure_inr"], 2),
                         "vuln_count": d["count"]})
    by_asset.sort(key=lambda x: x["ale_inr"], reverse=True)

    by_bu = [{"business_unit": k, "ale_inr": round(v["ale_inr"], 2),
              "share": round(v["ale_inr"] / total_ale, 4) if total_ale else 0.0, "asset_count": v["count"]}
             for k, v in _agg(lambda f: f["bu_name"]).items()]
    by_bu.sort(key=lambda x: x["ale_inr"], reverse=True)
    by_cat = [{"category": k, "ale_inr": round(v["ale_inr"], 2),
               "share": round(v["ale_inr"] / total_ale, 4) if total_ale else 0.0}
              for k, v in _agg(lambda f: f["category"]).items()]
    by_cat.sort(key=lambda x: x["ale_inr"], reverse=True)

    controls_out = [{"key": k, "name": c["control"]["name"], "category": c["control"]["category"],
                     "effectiveness": c["effectiveness"], "rating": c["detail"]["rating"],
                     "detail": c["detail"], "inputs": c["control"]} for k, c in ceff_map.items()]
    controls_out.sort(key=lambda x: x["effectiveness"])

    return {
        "org": state["org"], "generated_at": datetime.now(timezone.utc).isoformat(),
        "enterprise": {
            "risk_score": score, "risk_band": band, "risk_score_breakdown": score_detail,
            "total_ale_inr": total_ale, "expected_annual_loss_inr": total_ale,
            "total_exposure_inr": total_exposure, "var95_inr": var["var95_inr"],
            "var99_inr": var["var99_inr"], "var_detail": var,
            "avg_control_effectiveness": avg_ctrl_eff, "likelihood_avg": likelihood_avg,
            "open_vulns": len(active_vulns), "critical_vulns": critical_vulns,
            "asset_count": len(state["assets"]), "control_count": len(state["controls"]),
        },
        "findings": findings, "contributors": contributors, "by_asset": by_asset,
        "by_business_unit": by_bu, "by_category": by_cat, "controls": controls_out,
        "criticality_by_asset": crit_by_asset,
    }


def _action_for(category: str) -> str:
    return {
        "patch": "Deploy vendor patch / hotfix", "software": "Patch and upgrade affected software",
        "web": "Remediate web vulnerability and add WAF monitoring",
        "network": "Apply network segmentation and firewall rules",
        "config": "Harden configuration to secure baseline",
        "identity": "Enforce MFA and privileged access controls",
    }.get(category, "Apply vulnerability management remediation")
