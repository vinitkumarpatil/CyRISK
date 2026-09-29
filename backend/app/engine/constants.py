"""Transparent, centrally-documented model constants.

Every number that shapes a risk score lives here so the methodology page and
the report can cite exact values. These are *modelled assumptions*, not
empirical ground truth, and are meant to be calibrated per organization.
"""

# --- Asset criticality factor weights (sum = 1.0) ----------------------------
CRITICALITY_WEIGHTS = {
    "data_sensitivity": 0.22,
    "operational_criticality": 0.22,
    "regulatory_importance": 0.18,
    "business_value": 0.16,
    "revenue_impact": 0.12,
    "dependency": 0.10,
}
# Saturating normalisation references (value that maps to ~0.5 on a 0-1 scale)
BUSINESS_VALUE_REF_INR = 100_000_000.0      # ₹10 crore
REVENUE_PER_DAY_REF_INR = 5_000_000.0       # ₹50 lakh / day
DEPENDENCY_REF = 8.0

# --- Control effectiveness weights (sum = 1.0 before penalties) --------------
CONTROL_WEIGHTS = {
    "config_strength": 0.35,
    "coverage": 0.30,
    "compliance": 0.15,
    "maturity": 0.10,
    "monitoring": 0.10,
}
COMPLIANCE_SCORE = {"Compliant": 1.0, "Partial": 0.5, "Non-Compliant": 0.1}
INCIDENT_PENALTY_PER_EVENT = 0.06
INCIDENT_PENALTY_CAP = 0.30

# --- Financial impact model --------------------------------------------------
SEVERITY_EF = {"Critical": 0.60, "High": 0.40, "Medium": 0.20, "Low": 0.08}
SEVERITY_DOWNTIME_DAYS = {"Critical": 5.0, "High": 3.0, "Medium": 1.0, "Low": 0.25}
SEVERITY_FACTOR = {"Critical": 1.0, "High": 0.75, "Medium": 0.45, "Low": 0.2}
EF_CAP = 0.95

# --- Likelihood / ARO model --------------------------------------------------
SEVERITY_BASE_RATE = {"Critical": 0.80, "High": 0.40, "Medium": 0.15, "Low": 0.05}
EXPOSURE_MULT_INTERNET = 1.8
EXPOSURE_MULT_EXPLOIT = 1.6
EXPOSURE_MULT_NO_PATCH = 1.3
CONTROL_FREQ_REDUCTION = 0.85   # controls remove up to 85% of event frequency
ML_BLEND_LOW, ML_BLEND_SPAN = 0.70, 0.60  # final = det * (0.70 + 0.60*ml_prob)

# --- Enterprise risk score (0-100) blend -------------------------------------
ALE_REF_INR = 250_000_000.0     # ₹25 crore ALE -> ~50 on the ALE component
RISK_SCORE_W_ALE = 0.75
RISK_SCORE_W_CONTROL = 0.15
RISK_SCORE_W_CRITVULN = 0.10
CRITVULN_REF = 10.0

# --- Value at Risk (Monte Carlo) ---------------------------------------------
VAR_SIMULATIONS = 5000
VAR_SEVERITY_SIGMA = 0.5        # lognormal sigma for per-year severity variation
VAR_SEED = 26105

# Which control keys mitigate which vulnerability categories (frequency side)
VULN_CATEGORY_CONTROLS = {
    "patch": ["patch_management", "vuln_management"],
    "software": ["patch_management", "vuln_management", "endpoint_protection"],
    "web": ["vuln_management", "logging_monitoring"],
    "network": ["network_segmentation", "logging_monitoring"],
    "config": ["vuln_management", "logging_monitoring"],
    "identity": ["mfa", "privileged_access", "access_review"],
}
# Fallback controls applied to every finding
BASELINE_CONTROLS = ["vuln_management", "logging_monitoring", "endpoint_protection"]

# Map incident root-cause keywords -> control key (for effectiveness penalty)
INCIDENT_CONTROL_KEYWORDS = {
    "mfa": "mfa", "credential": "mfa", "phishing": "mfa",
    "unpatched": "patch_management", "patch": "patch_management",
    "privile": "privileged_access", "admin": "privileged_access",
    "segment": "network_segmentation", "lateral": "network_segmentation",
    "backup": "backup", "ransom": "backup",
    "endpoint": "endpoint_protection", "malware": "endpoint_protection",
    "encrypt": "encryption", "exfil": "encryption",
}
