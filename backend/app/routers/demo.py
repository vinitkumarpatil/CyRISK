"""Demo controls: dataset load/status and near-real-time telemetry simulation.

`simulate-telemetry` genuinely mutates the underlying data (ages findings,
discovers/remediates a vulnerability, drifts a control, or weaponises an
exploit), then recomputes risk and writes a new snapshot — so the trend line
moves for real. Nothing here is faked; every metric is recomputed by the engine.
"""
from __future__ import annotations
import random
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status

from .. import models
from ..database import get_db
from ..deps import get_current_user, current_org, get_result, get_frameworks, invalidate
from ..engine import snapshots
from ..seed.loader import seed_demo

router = APIRouter(prefix="/api/demo", tags=["demo"])

ACTIVE = ("open", "remediating")


@router.get("/status")
def status_(db=Depends(get_db), user=Depends(get_current_user),
            org_id: int = Depends(current_org)):
    """Report the CALLER's organization + row counts (used for tenant identity
    and empty-state detection)."""
    org = db.query(models.Organization).get(org_id)
    if org is None:
        return {"loaded": False}
    q = lambda m: db.query(m).filter_by(org_id=org.id).count()  # noqa: E731
    counts = {"assets": q(models.Asset), "vulnerabilities": q(models.Vulnerability),
              "controls": q(models.Control), "incidents": q(models.Incident),
              "snapshots": q(models.RiskSnapshot)}
    return {
        "loaded": True, "org_id": org.id, "organization": org.name, "sector": org.sector,
        "is_demo": bool(org.is_demo), "empty": counts["assets"] == 0,
        "counts": counts,
    }


@router.post("/load")
def load(db=Depends(get_db), user=Depends(get_current_user),
         org_id: int = Depends(current_org)):
    """(Re)seed the fictional demo enterprise and take an initial snapshot.

    Restricted to the demo organization so a real tenant cannot trigger the
    demo dataset rebuild.
    """
    org = db.query(models.Organization).get(org_id)
    if org is None or not org.is_demo:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Demo data can only be loaded from the demo organization.")
    summary = seed_demo(db)
    invalidate()
    org_id = summary["org_id"]
    result = get_result(db, org_id)
    frameworks = get_frameworks(db, org_id)
    snapshots.create_snapshot(db, org_id, result, frameworks,
                              label="Demo baseline", trigger="demo-load")
    return {"status": "loaded", "summary": summary,
            "risk_score": result["enterprise"]["risk_score"],
            "total_ale_inr": result["enterprise"]["total_ale_inr"]}


# __APPEND_DEMO__

_NEW_VULNS = [
    ("CVE-2024-3400", "Command injection in edge appliance", "network", 9.8, "Critical", True),
    ("CVE-2023-46604", "ActiveMQ RCE via OpenWire", "software", 9.8, "Critical", True),
    ("CVE-2024-23897", "Jenkins arbitrary file read", "software", 8.6, "High", True),
    ("CVE-2023-34362", "MOVEit SQL injection", "web", 9.8, "Critical", True),
    ("", "Weak TLS cipher suite on public endpoint", "config", 5.9, "Medium", False),
    ("", "Excessive privileged accounts detected", "identity", 6.5, "Medium", False),
    ("CVE-2022-1388", "iControl REST auth bypass", "web", 9.8, "Critical", True),
    ("", "Unpatched OS package backlog", "patch", 7.5, "High", False),
]


def _simulate_events(db, org_id: int) -> list:
    """Mutate the DB to emulate a fresh telemetry cycle. Returns event labels."""
    rng = random.Random()
    now = datetime.utcnow()
    events: list[str] = []
    vulns = (db.query(models.Vulnerability)
             .filter(models.Vulnerability.org_id == org_id,
                     models.Vulnerability.status.in_(ACTIVE)).all())

    # Age every active finding (older = higher modelled frequency).
    for v in vulns:
        v.age_days = (v.age_days or 0) + rng.randint(2, 9)

    action = rng.choice(["discover", "discover", "remediate", "control_drift", "weaponize"])
    assets = db.query(models.Asset).filter_by(org_id=org_id).all()

    if action == "discover" and assets:
        pool = [a for a in assets if a.internet_facing] or assets
        a = rng.choice(pool)
        cve, title, cat, cvss, sev, exploit = rng.choice(_NEW_VULNS)
        db.add(models.Vulnerability(
            org_id=org_id, asset_id=a.id, cve_id=cve, title=title, cvss=cvss, severity=sev,
            exploit_available=exploit, internet_exposed=bool(a.internet_facing), status="open",
            category=cat, patch_available=rng.random() > 0.3, age_days=1,
            remediation_cost_inr=float(rng.choice([200000, 400000, 750000])),
            source="Nessus / OpenVAS (simulated)", discovered_at=now, is_demo=True))
        events.append(f"Discovered {sev} finding '{title}' on {a.name}")
    elif action == "remediate" and vulns:
        v = rng.choice(vulns)
        v.status = "closed" if rng.random() > 0.4 else "remediating"
        events.append(f"{v.title} moved to {v.status}")
    elif action == "control_drift":
        controls = db.query(models.Control).filter_by(org_id=org_id).all()
        if controls:
            c = rng.choice(controls)
            delta = rng.choice([-0.04, -0.02, 0.02, 0.04])
            c.config_strength = min(0.99, max(0.02, (c.config_strength or 0.5) + delta))
            c.coverage = min(0.99, max(0.02, (c.coverage or 0.5) + delta))
            events.append(f"Control '{c.name}' drifted by {delta:+.0%}")
    elif action == "weaponize":
        cands = [v for v in vulns if not v.exploit_available and v.severity in ("High", "Critical")]
        if cands:
            v = rng.choice(cands)
            v.exploit_available = True
            events.append(f"Public exploit now available for '{v.title}'")

    src = (db.query(models.TelemetrySource)
           .filter_by(org_id=org_id, source_type="vuln_scanner").first())
    if src:
        src.record_count = db.query(models.Vulnerability).filter_by(org_id=org_id).count()
        src.last_sync = now
        src.status = "connected"
    db.commit()
    return events or ["Telemetry refreshed; findings aged"]


@router.post("/simulate-telemetry")
def simulate_telemetry(db=Depends(get_db), user=Depends(get_current_user),
                       org_id: int = Depends(current_org)):
    events = _simulate_events(db, org_id)
    invalidate(org_id)
    result = get_result(db, org_id)
    frameworks = get_frameworks(db, org_id)
    snap = snapshots.create_snapshot(db, org_id, result, frameworks,
                                     label="Telemetry update", trigger="telemetry")
    ent = result["enterprise"]
    return {
        "status": "updated", "events": events, "snapshot_id": snap.id,
        "risk_score": ent["risk_score"], "risk_band": ent["risk_band"],
        "total_ale_inr": ent["total_ale_inr"], "var95_inr": ent["var95_inr"],
        "open_vulns": ent["open_vulns"], "critical_vulns": ent["critical_vulns"],
    }
