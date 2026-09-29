"""Investment options catalogue + data-driven mitigation recommendations."""
from __future__ import annotations
from fastapi import APIRouter, Depends

from ..database import get_db
from ..deps import (get_current_user, current_org, get_state, get_result,
                    get_recommendations, options_for)
from ..engine import scenarios, fmt_inr

router = APIRouter(prefix="/api/investments", tags=["investments"])


@router.get("")
def list_options(db=Depends(get_db), user=Depends(get_current_user),
                 org_id: int = Depends(current_org)):
    """Each candidate investment with its individually-simulated ALE reduction."""
    base = get_state(db, org_id)
    baseline = get_result(db, org_id)
    out = []
    for o in options_for(db, org_id):
        marginal = scenarios.marginal_ale_reduction(base, o, baseline)
        out.append({
            "key": o["key"], "name": o["name"], "category": o["category"],
            "control_key": o["control_key"], "action": o["action"],
            "cost_inr": o["cost"], "cost_display": fmt_inr(o["cost"]), "effort": o["effort"],
            "marginal_ale_reduction_inr": marginal,
            "marginal_ale_reduction_display": fmt_inr(marginal),
            "rosi_percent": scenarios.rosi_percent(marginal, o["cost"]),
            "efficiency": round(marginal / o["cost"], 3) if o["cost"] else 0.0,
        })
    out.sort(key=lambda x: x["marginal_ale_reduction_inr"], reverse=True)
    return {"count": len(out), "options": out,
            "note": "Marginal reductions are individually re-simulated; combined effects are "
                    "non-additive and computed jointly by the optimizer."}


@router.get("/recommendations")
def recommendations(db=Depends(get_db), user=Depends(get_current_user),
                    org_id: int = Depends(current_org)):
    recs = get_recommendations(db, org_id)
    return {"count": len(recs), "recommendations": recs,
            "disclaimer": "Modelled estimates on synthetic demo data."}
