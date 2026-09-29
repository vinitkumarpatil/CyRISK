"""Mitigation recommendation routes (data-driven, re-simulated ALE reductions)."""
from __future__ import annotations
from fastapi import APIRouter, Depends

from ..database import get_db
from ..deps import get_current_user, current_org, get_recommendations
from ..engine import fmt_inr

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


@router.get("")
def list_recommendations(db=Depends(get_db), user=Depends(get_current_user),
                         org_id: int = Depends(current_org)):
    """Ranked mitigations; each ALE reduction is individually re-simulated, not assumed."""
    recs = get_recommendations(db, org_id)
    for r in recs:
        r["cost_display"] = fmt_inr(r["cost_inr"])
        r["expected_ale_reduction_display"] = fmt_inr(r["expected_ale_reduction_inr"])
    total = round(sum(r["expected_ale_reduction_inr"] for r in recs), 2)
    return {
        "count": len(recs),
        "recommendations": recs,
        "summary": {
            "total_marginal_ale_reduction_inr": total,
            "total_marginal_ale_reduction_display": fmt_inr(total),
            "note": "Marginal reductions are individually simulated; combined effects are "
                    "non-additive — use the optimizer for a joint, budget-bounded portfolio.",
        },
        "disclaimer": "Modelled estimates on synthetic demo data.",
    }
