"""Framework coverage assessment (NOT compliance certification).

Coverage status for each framework control is derived from the *computed*
effectiveness of the linked internal control. Language is deliberately an
assessment vocabulary — Covered / Partial / Potential Gap / Review Required —
never a claim of certified or audited compliance.
"""
from __future__ import annotations

# effectiveness band -> assessment status
def status_for(effectiveness: float | None) -> str:
    if effectiveness is None:
        return "Review Required"
    if effectiveness >= 0.75:
        return "Covered"
    if effectiveness >= 0.50:
        return "Partial"
    if effectiveness >= 0.30:
        return "Potential Gap"
    return "Review Required"


def _control_fields(c) -> tuple:
    """Return (control_ref, category, title, internal_control_key) from a catalog
    control that is either a 4-tuple (control_ref, category, title, internal_key)
    or a dict with those keys. Keeps the tuple catalog and the assessment engine
    in agreement without duplicating the control definitions."""
    if isinstance(c, dict):
        return (c.get("control_ref", ""), c.get("category", ""),
                c.get("title", ""), c.get("internal_control_key", ""))
    ref = c[0] if len(c) > 0 else ""
    cat = c[1] if len(c) > 1 else ""
    title = c[2] if len(c) > 2 else ""
    internal_key = c[3] if len(c) > 3 else ""
    return (ref, cat, title, internal_key)


def assess_frameworks(framework_defs: list, ceff_by_key: dict) -> list:
    """framework_defs: [{key,name,full_name,version, controls:[...]}] where each
    control is a 4-tuple (control_ref, category, title, internal_control_key) or a
    dict with those keys. ceff_by_key: {control_key: effectiveness}."""
    out = []
    for fw in framework_defs:
        controls = []
        effs = []
        counts = {"Covered": 0, "Partial": 0, "Potential Gap": 0, "Review Required": 0}
        for c in fw["controls"]:
            ref, cat, title, key = _control_fields(c)
            eff = ceff_by_key.get(key)
            status = status_for(eff)
            counts[status] += 1
            if eff is not None:
                effs.append(eff)
            controls.append({
                "control_ref": ref, "category": cat,
                "title": title, "internal_control_key": key,
                "effectiveness": round(eff, 4) if eff is not None else None,
                "status": status,
            })
        total = len(fw["controls"]) or 1
        avg_eff = sum(effs) / len(effs) if effs else 0.0
        addressed = counts["Covered"] + counts["Partial"]
        out.append({
            "key": fw["key"], "name": fw["name"],
            "full_name": fw.get("full_name", ""), "version": fw.get("version", ""),
            "control_count": len(fw["controls"]),
            "counts": counts,
            "coverage_pct": round(100.0 * addressed / total, 1),
            "assessment_index": round(100.0 * avg_eff, 1),
            "controls": controls,
            "disclaimer": "Internal assessment / mapping on synthetic demo data — "
                          "not a compliance certification or audit attestation.",
        })
    out.sort(key=lambda f: f["assessment_index"])
    return out


def enterprise_coverage(assessments: list) -> dict:
    """Roll up an org-wide coverage indicator across all frameworks (for dashboard)."""
    if not assessments:
        return {"assessment_index": 0.0, "frameworks": 0}
    idx = sum(a["assessment_index"] for a in assessments) / len(assessments)
    return {
        "assessment_index": round(idx, 1),
        "frameworks": len(assessments),
        "weakest": assessments[0]["name"] if assessments else "",
    }
