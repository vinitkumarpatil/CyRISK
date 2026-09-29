"""Executive + technical dashboard rollup (single call for the landing pages)."""
from __future__ import annotations
from fastapi import APIRouter, Depends

from ..database import get_db
from ..deps import get_current_user, current_org, get_result, get_frameworks
from ..engine import snapshots, fmt_inr
from ..engine.frameworks_data import enterprise_coverage
from ..engine.ml_model import get_model

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("")
def dashboard(db=Depends(get_db), user=Depends(get_current_user),
              org_id: int = Depends(current_org)):
    result = get_result(db, org_id)
    frameworks = get_frameworks(db, org_id)
    ent = result["enterprise"]
    model = get_model()
    coverage = enterprise_coverage(frameworks)

    return {
        "organization": result["org"],
        "generated_at": result["generated_at"],
        "enterprise": ent,
        "headline_inr": {
            "total_ale": fmt_inr(ent["total_ale_inr"]),
            "total_exposure": fmt_inr(ent["total_exposure_inr"]),
            "var95": fmt_inr(ent["var95_inr"]), "var99": fmt_inr(ent["var99_inr"]),
        },
        "top_contributors": result["contributors"][:8],
        "by_business_unit": result["by_business_unit"],
        "by_category": result["by_category"],
        "weakest_controls": result["controls"][:5],
        "top_assets": result["by_asset"][:8],
        "framework_coverage": [
            {"key": f["key"], "name": f["name"], "assessment_index": f["assessment_index"],
             "coverage_pct": f["coverage_pct"], "counts": f["counts"]} for f in frameworks],
        "framework_rollup": coverage,
        "ml_model": {"metrics": model.metrics, "importances": model.importances},
        "trend": snapshots.trend(db, org_id, limit=50),
        "role": user.role,
        "disclaimer": "All figures are modelled estimates on synthetic demo data.",
    }
