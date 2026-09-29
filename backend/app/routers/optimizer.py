"""Budget-constrained investment optimization route (real 0/1 knapsack)."""
from __future__ import annotations
from fastapi import APIRouter, Depends

from .. import schemas
from ..database import get_db
from ..deps import get_current_user, current_org, get_state, options_for
from ..engine import optimizer, fmt_inr

router = APIRouter(prefix="/api/optimizer", tags=["optimizer"])


@router.post("/run")
def run_optimizer(body: schemas.OptimizeRequest, db=Depends(get_db),
                  user=Depends(get_current_user), org_id: int = Depends(current_org)):
    """Maximize modelled ALE reduction within the budget; joint re-simulation of the winners."""
    base = get_state(db, org_id)
    options = options_for(db, org_id)
    out = optimizer.optimize(base, options, body.budget_inr)
    out["budget_display"] = fmt_inr(body.budget_inr)
    out["total_cost_display"] = fmt_inr(out["total_cost_inr"])
    out["joint_ale_reduction_display"] = fmt_inr(out["joint_ale_reduction_inr"])
    return out
