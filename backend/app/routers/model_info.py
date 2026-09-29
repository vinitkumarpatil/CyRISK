"""ML model transparency route: metrics, feature importances, and model card."""
from __future__ import annotations
from fastapi import APIRouter, Depends

from ..deps import get_current_user
from ..engine.ml_model import get_model, FEATURES, SEED

router = APIRouter(prefix="/api/model", tags=["model"])

FEATURE_DEFS = {
    "criticality": "Modelled business criticality of the asset (0–100)",
    "open_vulns": "Count of open vulnerabilities on the asset",
    "critical_vulns": "Count of critical-severity vulnerabilities on the asset",
    "max_cvss": "Highest CVSS base score among the asset's findings (0–10)",
    "internet_facing": "Whether the asset is internet-facing (0/1)",
    "avg_control_eff": "Average effectiveness of relevant controls (0–1, protective)",
    "data_sensitivity": "Data sensitivity classification of the asset",
    "exploit_present": "Whether a public exploit exists for a finding (0/1)",
    "threat_pressure": "Modelled threat activity level for the category (0–1)",
    "past_incidents": "Count of prior incidents on the asset",
}


@router.get("")
def model_info(user=Depends(get_current_user)):
    """Return the incident-likelihood model card (genuine scikit-learn model)."""
    model = get_model()
    importances = sorted(
        ({"feature": f, "importance": imp,
          "description": FEATURE_DEFS.get(f, "")} for f, imp in model.importances.items()),
        key=lambda x: x["importance"], reverse=True)
    return {
        "algorithm": model.metrics.get("algorithm", "GradientBoostingClassifier"),
        "purpose": "Estimates the probability that a given (asset, vulnerability) leads to a "
                   "security incident within a year; this probability nudges the actuarial "
                   "frequency (ARO) used in the ALE calculation.",
        "metrics": model.metrics,
        "feature_importances": importances,
        "features": FEATURES,
        "training": {
            "seed": SEED,
            "data": "Synthetically generated, labelled training set (see engine/ml_model.py). "
                    "The model is real; the training data is synthetic for the demo.",
        },
        "hybrid_note": "Risk figures come from transparent actuarial formulas (SLE × ARO, "
                       "Monte-Carlo VaR); the ML model only adjusts likelihood. The model "
                       "never fabricates monetary values.",
        "disclaimer": "Trained on synthetic demo data — not a production threat model.",
    }
