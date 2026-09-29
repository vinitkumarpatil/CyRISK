"""Investment options catalog for the demo enterprise (SYNTHETIC / DEMO).

Each option maps to a concrete, simulatable change in enterprise state:
  - improve_control : raise a control's inputs to `target`, recomputing effectiveness
  - patch_vulns     : apply `set` to vulnerabilities matching `filter`
  - reduce_exposure : apply `set` (typically internet_exposed=False) to matches

The what-if / optimizer engines read `action` + `params` to recompute risk, so
the modelled ₹ risk reduction is always derived — never hardcoded.
"""

# key, name, category, control_key, action, cost_inr, effort, params
def _o(key, name, category, control_key, action, cost, effort, params):
    return {"key": key, "name": name, "category": category, "control_key": control_key,
            "action": action, "cost": cost, "effort": effort, "params": params}

INVESTMENT_OPTIONS = [
    _o("mfa_rollout", "Enterprise MFA rollout (privileged + remote access)", "identity", "mfa",
       "improve_control", 3_500_000, "Medium",
       {"target": {"config_strength": 0.90, "coverage": 0.95, "compliance_status": "Compliant", "maturity": 4, "monitored": True}}),
    _o("pam_deploy", "Privileged Access Management (PAM) deployment", "identity", "privileged_access",
       "improve_control", 6_000_000, "High",
       {"target": {"config_strength": 0.85, "coverage": 0.85, "compliance_status": "Compliant", "maturity": 4, "monitored": True}}),
    _o("patch_program", "Patch & vulnerability remediation uplift", "vulnerability", "patch_management",
       "improve_control", 4_500_000, "Medium",
       {"target": {"config_strength": 0.85, "coverage": 0.90, "compliance_status": "Compliant", "maturity": 4, "monitored": True}}),
    _o("patch_critical_internet", "Emergency patch: internet-facing critical vulnerabilities", "vulnerability", "patch_management",
       "patch_vulns", 2_000_000, "Low",
       {"filter": {"internet_exposed": True, "min_cvss": 9.0}, "set": {"status": "closed"}}),
    _o("patch_high_backlog", "Remediate high-severity vulnerability backlog", "vulnerability", "patch_management",
       "patch_vulns", 3_500_000, "Medium",
       {"filter": {"severity_in": ["High", "Critical"], "min_cvss": 7.0}, "set": {"status": "remediating", "patch_available": True}}),
    _o("segmentation", "Network micro-segmentation of crown-jewel systems", "network", "network_segmentation",
       "improve_control", 7_500_000, "High",
       {"target": {"config_strength": 0.80, "coverage": 0.80, "compliance_status": "Compliant", "maturity": 4, "monitored": True}}),
    _o("edr_expansion", "EDR coverage expansion and tuning", "endpoint", "endpoint_protection",
       "improve_control", 3_000_000, "Medium",
       {"target": {"config_strength": 0.85, "coverage": 0.95, "compliance_status": "Compliant", "maturity": 4, "monitored": True}}),
    _o("backup_dr", "Immutable backup & disaster-recovery program", "resilience", "backup",
       "improve_control", 5_000_000, "Medium",
       {"target": {"config_strength": 0.90, "coverage": 0.90, "compliance_status": "Compliant", "maturity": 4, "monitored": True}}),
    _o("siem_expansion", "SIEM / log coverage expansion", "detection", "logging_monitoring",
       "improve_control", 3_200_000, "Medium",
       {"target": {"config_strength": 0.80, "coverage": 0.90, "compliance_status": "Compliant", "maturity": 4, "monitored": True}}),
    _o("waf", "Web Application Firewall + web hardening", "web", "vuln_management",
       "reduce_exposure", 2_500_000, "Low",
       {"filter": {"category": "web", "internet_exposed": True}, "set": {"internet_exposed": False}}),
    _o("encryption_program", "Data encryption & masking program", "data", "encryption",
       "improve_control", 4_000_000, "Medium",
       {"target": {"config_strength": 0.90, "coverage": 0.90, "compliance_status": "Compliant", "maturity": 4, "monitored": True}}),
    _o("vuln_mgmt_platform", "Vulnerability management platform + remediation SLA", "vulnerability", "vuln_management",
       "improve_control", 3_800_000, "Medium",
       {"target": {"config_strength": 0.85, "coverage": 0.90, "compliance_status": "Compliant", "maturity": 4, "monitored": True}}),
    _o("access_review_automation", "Automated access reviews (joiner-mover-leaver)", "identity", "access_review",
       "improve_control", 2_200_000, "Low",
       {"target": {"config_strength": 0.80, "coverage": 0.85, "compliance_status": "Compliant", "maturity": 3, "monitored": True}}),
]
