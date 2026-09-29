"""AI/ML incident-likelihood model.

A gradient-boosted classifier trained on a **clearly synthetic** historical
incident dataset. It outputs a per-asset annualised incident probability that
is *blended* with the deterministic frequency model (never used as a black box
on its own) and exposes global + per-prediction feature attributions.
"""
from __future__ import annotations
import threading
from pathlib import Path

import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, accuracy_score, brier_score_loss

FEATURES = [
    "criticality", "open_vulns", "critical_vulns", "max_cvss", "internet_facing",
    "avg_control_eff", "data_sensitivity", "exploit_present", "threat_pressure",
    "past_incidents",
]
# (divisor, protective?) used only for per-prediction attribution deviations
NORM = {
    "criticality": 100.0, "open_vulns": 15.0, "critical_vulns": 6.0, "max_cvss": 10.0,
    "internet_facing": 1.0, "avg_control_eff": 1.0, "data_sensitivity": 5.0,
    "exploit_present": 1.0, "threat_pressure": 1.0, "past_incidents": 5.0,
}
PROTECTIVE = {"avg_control_eff"}
MODEL_PATH = Path(__file__).resolve().parent.parent.parent / "ml_incident_model.joblib"
SEED = 26105


def generate_synthetic_dataset(n: int = 4000, seed: int = SEED):
    """SYNTHETIC/DEMO data — not real incidents. Reproducible via fixed seed."""
    rng = np.random.default_rng(seed)
    criticality = rng.uniform(10, 100, n)
    open_vulns = rng.poisson(4, n)
    critical_vulns = rng.binomial(np.maximum(open_vulns, 1), 0.25)
    max_cvss = np.clip(rng.normal(7, 2, n), 0, 10)
    internet_facing = rng.binomial(1, 0.4, n)
    avg_control_eff = np.clip(rng.beta(2, 2, n), 0.02, 0.99)
    data_sensitivity = rng.integers(0, 6, n)
    exploit_present = rng.binomial(1, 0.3, n)
    threat_pressure = np.clip(rng.beta(2, 3, n), 0, 1)
    past_incidents = rng.poisson(0.6, n)

    z = (-5.6
         + 1.8 * (1.9 * (criticality / 100) + 1.4 * (open_vulns / 15) + 1.3 * (critical_vulns / 6)
                  + 1.2 * (max_cvss / 10) + 0.9 * internet_facing - 2.4 * avg_control_eff
                  + 0.7 * (data_sensitivity / 5) + 1.1 * exploit_present + 1.1 * threat_pressure
                  + 0.9 * (past_incidents / 5))
         + rng.normal(0, 0.12, n))
    p = 1 / (1 + np.exp(-z))
    y = rng.binomial(1, p)
    X = pd.DataFrame({
        "criticality": criticality, "open_vulns": open_vulns, "critical_vulns": critical_vulns,
        "max_cvss": max_cvss, "internet_facing": internet_facing, "avg_control_eff": avg_control_eff,
        "data_sensitivity": data_sensitivity, "exploit_present": exploit_present,
        "threat_pressure": threat_pressure, "past_incidents": past_incidents,
    })[FEATURES]
    return X, y


class IncidentModel:
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self.model = None
        self.metrics = {}
        self.baseline = {}
        self.importances = {}

    @classmethod
    def instance(cls) -> "IncidentModel":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
                cls._instance.load_or_train()
            return cls._instance

    def load_or_train(self, force: bool = False):
        if MODEL_PATH.exists() and not force:
            try:
                blob = joblib.load(MODEL_PATH)
                self.model, self.metrics, self.baseline, self.importances = (
                    blob["model"], blob["metrics"], blob["baseline"], blob["importances"])
                return
            except Exception:
                pass
        self.train()

    def train(self):
        X, y = generate_synthetic_dataset()
        Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, random_state=SEED, stratify=y)
        clf = GradientBoostingClassifier(random_state=SEED, n_estimators=180, max_depth=3, learning_rate=0.08)
        clf.fit(Xtr.values, ytr)
        proba = clf.predict_proba(Xte.values)[:, 1]
        self.model = clf
        self.metrics = {
            "auc": round(float(roc_auc_score(yte, proba)), 4),
            "accuracy": round(float(accuracy_score(yte, clf.predict(Xte.values))), 4),
            "brier": round(float(brier_score_loss(yte, proba)), 4),
            "n_train": int(len(Xtr)), "n_test": int(len(Xte)),
            "base_rate": round(float(y.mean()), 4), "algorithm": "GradientBoostingClassifier",
        }
        self.baseline = {f: float(X[f].mean()) for f in FEATURES}
        self.importances = {f: round(float(i), 4) for f, i in zip(FEATURES, clf.feature_importances_)}
        joblib.dump({"model": clf, "metrics": self.metrics, "baseline": self.baseline,
                     "importances": self.importances}, MODEL_PATH)

    def _vec(self, features: dict) -> np.ndarray:
        return np.array([[float(features.get(f, self.baseline.get(f, 0.0))) for f in FEATURES]])

    def predict_proba_one(self, features: dict) -> float:
        return float(self.model.predict_proba(self._vec(features))[0, 1])

    def explain(self, features: dict, top: int = 5) -> list:
        """Approximate per-prediction attribution: importance × normalised
        deviation from the training mean. Directional, not exact SHAP."""
        out = []
        for f in FEATURES:
            raw = float(features.get(f, self.baseline.get(f, 0.0)))
            dev = (raw - self.baseline.get(f, 0.0)) / NORM[f]
            direction = -1.0 if f in PROTECTIVE else 1.0
            effect = self.importances.get(f, 0.0) * dev * direction
            out.append({
                "feature": f, "value": round(raw, 3),
                "importance": self.importances.get(f, 0.0),
                "effect": round(effect, 4),
                "direction": "increases" if effect >= 0 else "decreases",
            })
        out.sort(key=lambda d: abs(d["effect"]), reverse=True)
        return out[:top]


def get_model() -> IncidentModel:
    return IncidentModel.instance()
