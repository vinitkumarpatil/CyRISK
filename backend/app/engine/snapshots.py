"""Persist a computed risk result as a point-in-time snapshot.

A snapshot stores the enterprise metrics plus the granular findings and ranked
contributions, so the platform can show trends over time (continuous / near
real-time risk view). Every number persisted is copied verbatim from the
computed engine result — nothing is re-derived or invented here.
"""
from __future__ import annotations

from .. import models


def create_snapshot(db, org_id: int, result: dict, frameworks: list | None = None,
                    label: str = "", trigger: str = "manual") -> models.RiskSnapshot:
    """Write a RiskSnapshot (+ findings + contributions) from `result`."""
    ent = result["enterprise"]
    snap = models.RiskSnapshot(
        org_id=org_id, label=label or trigger.title(), trigger=trigger,
        enterprise_risk_score=ent["risk_score"], total_ale_inr=ent["total_ale_inr"],
        total_exposure_inr=ent["total_exposure_inr"], var95_inr=ent["var95_inr"],
        var99_inr=ent["var99_inr"], likelihood_avg=ent["likelihood_avg"],
        open_vulns=ent["open_vulns"], critical_vulns=ent["critical_vulns"],
        avg_control_effectiveness=ent["avg_control_effectiveness"],
        top_contributors=result.get("contributors", [])[:12],
        by_business_unit=result.get("by_business_unit", []),
        by_category=result.get("by_category", []),
        control_effectiveness=[{"key": c["key"], "name": c["name"],
                                "effectiveness": c["effectiveness"], "rating": c["rating"]}
                               for c in result.get("controls", [])],
        framework_coverage=[{"key": f["key"], "name": f["name"],
                             "assessment_index": f["assessment_index"],
                             "coverage_pct": f["coverage_pct"]} for f in (frameworks or [])],
        metrics=ent,
    )
    db.add(snap)
    db.flush()

    for f in result.get("findings", []):
        db.add(models.RiskFinding(
            snapshot_id=snap.id, org_id=org_id, asset_id=f.get("asset_id"),
            vuln_id=f.get("vuln_id"), title=f.get("title", ""), category=f.get("category", ""),
            severity=f.get("severity", ""), likelihood=f.get("likelihood", 0.0),
            sle_inr=f.get("sle_inr", 0.0), aro=f.get("aro", 0.0), ale_inr=f.get("ale_inr", 0.0),
            breakdown={"impact": f.get("impact", {}), "frequency": f.get("frequency", {}),
                       "controls_considered": f.get("controls_considered", []),
                       "ml_probability": f.get("ml_probability"), "formula": f.get("formula", "")},
        ))

    for c in result.get("contributors", [])[:12]:
        db.add(models.RiskContribution(
            snapshot_id=snap.id, org_id=org_id, kind="finding", label=c["label"],
            ref_id=c.get("vuln_id"), ale_inr=c["ale_inr"], share=c.get("share", 0.0),
            likelihood_contrib=c.get("likelihood", 0.0),
            control_weakness=c.get("control_weakness", ""),
            recommended_action=c.get("recommended_action", ""),
            expected_reduction_inr=c.get("expected_reduction_inr", 0.0),
        ))

    db.commit()
    return snap


def snapshot_to_dict(s: models.RiskSnapshot) -> dict:
    return {
        "id": s.id, "created_at": s.created_at.isoformat() if s.created_at else None,
        "label": s.label, "trigger": s.trigger,
        "risk_score": s.enterprise_risk_score, "total_ale_inr": s.total_ale_inr,
        "total_exposure_inr": s.total_exposure_inr, "var95_inr": s.var95_inr,
        "var99_inr": s.var99_inr, "likelihood_avg": s.likelihood_avg,
        "open_vulns": s.open_vulns, "critical_vulns": s.critical_vulns,
        "avg_control_effectiveness": s.avg_control_effectiveness,
    }


def list_snapshots(db, org_id: int, limit: int = 50) -> list:
    rows = (db.query(models.RiskSnapshot).filter_by(org_id=org_id)
            .order_by(models.RiskSnapshot.created_at.asc()).limit(limit).all())
    return [snapshot_to_dict(s) for s in rows]


def trend(db, org_id: int, limit: int = 50) -> dict:
    """Return the time-ordered series used to draw the risk trend charts."""
    series = list_snapshots(db, org_id, limit)
    return {
        "points": series,
        "count": len(series),
        "latest": series[-1] if series else None,
        "note": "Trend of modelled risk over successive snapshots (synthetic demo data).",
    }
