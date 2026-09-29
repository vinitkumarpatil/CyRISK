"""Risk quantification routes: full result, findings, contributors, trends."""
from __future__ import annotations
from fastapi import APIRouter, Depends, Query

from ..database import get_db
from ..deps import get_current_user, current_org, get_result
from ..engine import snapshots

router = APIRouter(prefix="/api/risk", tags=["risk"])


@router.get("")
def full_risk(db=Depends(get_db), user=Depends(get_current_user),
              org_id: int = Depends(current_org)):
    """Complete computed risk result (enterprise + breakdowns + criticality)."""
    return get_result(db, org_id)


@router.get("/enterprise")
def enterprise(db=Depends(get_db), user=Depends(get_current_user),
               org_id: int = Depends(current_org)):
    return get_result(db, org_id)["enterprise"]


@router.get("/findings")
def findings(db=Depends(get_db), user=Depends(get_current_user),
             org_id: int = Depends(current_org),
             limit: int = Query(default=200, ge=1, le=1000)):
    """Granular per-(asset,vuln) findings with full SLE/ARO/ALE breakdown."""
    result = get_result(db, org_id)
    ranked = sorted(result["findings"], key=lambda f: f["ale_inr"], reverse=True)
    return {"count": len(ranked), "findings": ranked[:limit]}


@router.get("/contributors")
def contributors(db=Depends(get_db), user=Depends(get_current_user),
                 org_id: int = Depends(current_org)):
    result = get_result(db, org_id)
    return {"contributors": result["contributors"],
            "total_ale_inr": result["enterprise"]["total_ale_inr"]}


@router.get("/snapshots")
def snapshot_list(db=Depends(get_db), user=Depends(get_current_user),
                  org_id: int = Depends(current_org)):
    return {"snapshots": snapshots.list_snapshots(db, org_id, limit=100)}


@router.get("/trend")
def trend(db=Depends(get_db), user=Depends(get_current_user),
          org_id: int = Depends(current_org)):
    return snapshots.trend(db, org_id, limit=100)
