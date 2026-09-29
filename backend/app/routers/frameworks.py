"""Framework coverage assessment routes (mapping only — never certification)."""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException

from ..database import get_db
from ..deps import get_current_user, current_org, get_frameworks
from ..engine.frameworks_data import enterprise_coverage

router = APIRouter(prefix="/api/frameworks", tags=["frameworks"])


@router.get("")
def list_frameworks(db=Depends(get_db), user=Depends(get_current_user),
                    org_id: int = Depends(current_org)):
    frameworks = get_frameworks(db, org_id)
    return {
        "count": len(frameworks),
        "rollup": enterprise_coverage(frameworks),
        "frameworks": frameworks,
        "disclaimer": "Internal control-to-framework mapping on synthetic demo data. "
                      "This is an assessment aid, NOT a certification, audit, or attestation "
                      "of regulatory compliance.",
    }


@router.get("/{key}")
def framework_detail(key: str, db=Depends(get_db), user=Depends(get_current_user),
                     org_id: int = Depends(current_org)):
    frameworks = get_frameworks(db, org_id)
    fw = next((f for f in frameworks if f["key"] == key), None)
    if fw is None:
        raise HTTPException(status_code=404, detail="Framework not found.")
    return fw
