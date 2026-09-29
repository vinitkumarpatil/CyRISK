"""What-if scenario engine routes: apply mutations and recompute before/after."""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user, require_roles, current_org, get_state, options_for, get_result
from ..engine import scenarios

router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])


def _clean_mutation(m: schemas.Mutation) -> dict:
    return {k: v for k, v in m.model_dump().items() if v is not None}


@router.post("/simulate")
def simulate(body: schemas.ScenarioRequest, db=Depends(get_db),
             user=Depends(require_roles("ciso", "analyst")),
             org_id: int = Depends(current_org)):
    """Apply arbitrary mutations to a cloned state and return before/after/delta."""
    mutations = [_clean_mutation(m) for m in body.mutations]
    if not mutations:
        raise HTTPException(status_code=400, detail="Provide at least one mutation.")
    base = get_state(db, org_id)
    baseline = get_result(db, org_id)
    out = scenarios.simulate(base, mutations, label=body.name, baseline=baseline)
    if body.save:
        _save(db, org_id, body.name, body.description, mutations, out)
    return out


# __APPEND_SCENARIOS_ROUTER__


@router.post("/investment")
def investment_scenario(body: schemas.InvestmentScenarioRequest, db=Depends(get_db),
                        user=Depends(require_roles("ciso", "analyst")),
                        org_id: int = Depends(current_org)):
    """Simulate the combined effect of one or more investment options (by key)."""
    options = {o["key"]: o for o in options_for(db, org_id)}
    chosen = [options[k] for k in body.option_keys if k in options]
    if not chosen:
        raise HTTPException(status_code=400, detail="No valid investment option keys supplied.")
    mutations = []
    for o in chosen:
        mutations += scenarios.investment_to_mutations(o)
    base = get_state(db, org_id)
    baseline = get_result(db, org_id)
    cost = sum(o["cost"] for o in chosen)
    out = scenarios.simulate(base, mutations, cost_inr=cost, label=body.name, baseline=baseline)
    out["investments"] = [{"key": o["key"], "name": o["name"], "cost_inr": o["cost"]} for o in chosen]
    if body.save:
        _save(db, org_id, body.name, "Investment what-if", mutations, out)
    return out


def _save(db, org_id, name, description, mutations, result) -> None:
    db.add(models.Scenario(org_id=org_id, name=name, description=description,
                           spec={"mutations": mutations},
                           result={"before": result["before"], "after": result["after"],
                                   "delta": result["delta"]}))
    db.commit()


@router.get("")
def list_scenarios(db=Depends(get_db), user=Depends(get_current_user),
                   org_id: int = Depends(current_org)):
    rows = (db.query(models.Scenario).filter_by(org_id=org_id)
            .order_by(models.Scenario.created_at.desc()).limit(50).all())
    return {"scenarios": [{"id": s.id, "name": s.name, "description": s.description,
                           "spec": s.spec, "result": s.result,
                           "created_at": s.created_at.isoformat() if s.created_at else None}
                          for s in rows]}
