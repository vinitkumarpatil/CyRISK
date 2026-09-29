"""Vulnerability findings with modelled risk annotations."""
from __future__ import annotations
from fastapi import APIRouter, Depends

from ..database import get_db
from ..deps import get_current_user, current_org, get_result, get_state

router = APIRouter(prefix="/api/vulnerabilities", tags=["vulnerabilities"])


@router.get("")
def list_vulns(db=Depends(get_db), user=Depends(get_current_user),
               org_id: int = Depends(current_org)):
    result = get_result(db, org_id)
    state = get_state(db, org_id)
    asset_name = {a["id"]: a["name"] for a in state["assets"]}
    finding_by_vuln = {f["vuln_id"]: f for f in result["findings"]}

    out = []
    for v in state["vulns"]:
        f = finding_by_vuln.get(v["id"])
        out.append({
            "id": v["id"], "cve_id": v.get("cve_id", ""), "title": v["title"],
            "asset_id": v["asset_id"], "asset_name": asset_name.get(v["asset_id"], "—"),
            "cvss": v["cvss"], "severity": v["severity"], "category": v["category"],
            "status": v["status"], "exploit_available": v["exploit_available"],
            "internet_exposed": v["internet_exposed"], "patch_available": v["patch_available"],
            "age_days": v["age_days"], "source": v.get("source", ""),
            "ale_inr": (f["ale_inr"] if f else 0.0),
            "likelihood": (f["likelihood"] if f else 0.0),
            "sle_inr": (f["sle_inr"] if f else 0.0),
        })
    out.sort(key=lambda x: (x["ale_inr"], x["cvss"]), reverse=True)

    sev = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    status_counts = {"open": 0, "remediating": 0, "closed": 0}
    for v in state["vulns"]:
        sev[v["severity"]] = sev.get(v["severity"], 0) + 1
        status_counts[v["status"]] = status_counts.get(v["status"], 0) + 1

    return {"count": len(out), "by_severity": sev, "by_status": status_counts,
            "vulnerabilities": out}
