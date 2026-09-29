"""Control effectiveness routes with transparent factor breakdowns."""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException

from ..database import get_db
from ..deps import get_current_user, current_org, get_result

router = APIRouter(prefix="/api/controls", tags=["controls"])


@router.get("")
def list_controls(db=Depends(get_db), user=Depends(get_current_user),
                  org_id: int = Depends(current_org)):
    result = get_result(db, org_id)
    controls = result["controls"]
    avg = round(sum(c["effectiveness"] for c in controls) / len(controls), 4) if controls else 0.0
    return {"count": len(controls), "avg_effectiveness": avg, "controls": controls}


@router.get("/{key}")
def control_detail(key: str, db=Depends(get_db), user=Depends(get_current_user),
                   org_id: int = Depends(current_org)):
    result = get_result(db, org_id)
    c = next((c for c in result["controls"] if c["key"] == key), None)
    if c is None:
        raise HTTPException(status_code=404, detail="Control not found.")
    return c
