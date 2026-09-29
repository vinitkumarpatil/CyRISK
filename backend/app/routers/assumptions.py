"""Editable financial assumptions — transparent inputs to the risk model.

Editing an assumption invalidates the compute cache so the next risk read
reflects the change (the model genuinely recomputes; nothing is hardcoded).
"""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user, require_roles, current_org, invalidate
from ..engine import fmt_inr

router = APIRouter(prefix="/api/assumptions", tags=["assumptions"])


def _serialize(a: models.FinancialAssumption) -> dict:
    return {
        "key": a.key, "label": a.label, "value": a.value, "unit": a.unit,
        "category": a.category, "description": a.description, "editable": bool(a.editable),
        "value_display": fmt_inr(a.value) if a.unit == "INR" else f"{a.value:g} {a.unit}",
    }


@router.get("")
def list_assumptions(db=Depends(get_db), user=Depends(get_current_user),
                     org_id: int = Depends(current_org)):
    rows = db.query(models.FinancialAssumption).filter_by(org_id=org_id).all()
    return {"count": len(rows), "assumptions": [_serialize(a) for a in rows],
            "note": "These transparent inputs drive the financial model. Editing one "
                    "recomputes all downstream risk figures."}


@router.put("")
def update_assumption(body: schemas.AssumptionUpdate, db=Depends(get_db),
                      user=Depends(require_roles("ciso", "analyst")),
                      org_id: int = Depends(current_org)):
    a = (db.query(models.FinancialAssumption)
         .filter_by(org_id=org_id, key=body.key).first())
    if a is None:
        raise HTTPException(status_code=404, detail="Assumption not found.")
    if not a.editable:
        raise HTTPException(status_code=400, detail="This assumption is not editable.")
    old = a.value
    a.value = body.value
    db.commit()
    invalidate(org_id)  # force recompute on next read
    return {"status": "updated", "key": a.key, "old_value": old, "new_value": a.value,
            "assumption": _serialize(a),
            "note": "Risk figures will recompute on the next request."}
