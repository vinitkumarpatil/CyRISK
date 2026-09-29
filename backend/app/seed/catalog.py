"""Static demo catalogs: controls, threats, telemetry sources, assumptions.

All data here is SYNTHETIC / DEMO data for a fictional organisation.
"""

# key, name, category, config_strength, coverage, compliance_status, maturity, monitored, description
CONTROLS = [
    ("mfa", "Multi-Factor Authentication", "preventive", 0.55, 0.60, "Partial", 2, False,
     "MFA on remote access and admin portals; not yet enforced on all privileged accounts."),
    ("endpoint_protection", "Endpoint Detection & Response (EDR)", "detective", 0.70, 0.75, "Compliant", 3, True,
     "EDR agents deployed across most endpoints and servers with central telemetry."),
    ("patch_management", "Patch & Vulnerability Remediation", "corrective", 0.45, 0.55, "Partial", 2, False,
     "Monthly patch cycle; critical patches frequently delayed beyond SLA."),
    ("network_segmentation", "Network Segmentation", "preventive", 0.50, 0.50, "Partial", 2, False,
     "Flat network in parts of the estate; limited micro-segmentation of crown-jewel systems."),
    ("privileged_access", "Privileged Access Management (PAM)", "preventive", 0.40, 0.45, "Non-Compliant", 1, False,
     "Shared admin credentials in use; no session recording or just-in-time access."),
    ("encryption", "Data Encryption (at rest & in transit)", "preventive", 0.75, 0.80, "Compliant", 3, True,
     "TLS enforced; database and disk encryption on most data stores."),
    ("backup", "Backup & Disaster Recovery", "corrective", 0.65, 0.70, "Partial", 3, True,
     "Daily backups; immutable/offline copies only for a subset of systems."),
    ("logging_monitoring", "Security Logging & Monitoring (SIEM)", "detective", 0.60, 0.65, "Partial", 3, True,
     "SIEM ingests core logs; coverage gaps on OT and some SaaS platforms."),
    ("vuln_management", "Vulnerability Management Program", "detective", 0.50, 0.60, "Partial", 2, True,
     "Authenticated scanning weekly; remediation tracking is inconsistent."),
    ("access_review", "Periodic Access Review", "administrative", 0.45, 0.50, "Partial", 2, False,
     "Quarterly reviews; joiner-mover-leaver process partially automated."),
]

# name, threat_actor, category, ttp, likelihood_weight, relevance, description
THREATS = [
    ("Ransomware campaign (financial sector)", "LockBit-style affiliate", "ransomware", "T1486 Data Encrypted for Impact",
     0.85, 0.80, "Active ransomware targeting Indian BFSI with double-extortion tactics."),
    ("Credential phishing / MFA fatigue", "Commodity phishing crews", "phishing", "T1566 Phishing",
     0.80, 0.78, "High-volume phishing against customer and employee credentials."),
    ("APT targeting payment systems", "State-aligned APT", "apt", "T1190 Exploit Public-Facing Application",
     0.65, 0.62, "Advanced actor interested in payment switch and SWIFT-adjacent systems."),
    ("Malicious / negligent insider", "Insider", "insider", "T1078 Valid Accounts",
     0.55, 0.50, "Privileged insiders with excessive standing access to core systems."),
    ("DDoS on public services", "Hacktivist / booter", "ddos", "T1498 Network Denial of Service",
     0.70, 0.60, "Volumetric attacks aimed at internet banking and payment gateways."),
    ("Software supply-chain compromise", "Supply-chain actor", "supply_chain", "T1195 Supply Chain Compromise",
     0.50, 0.45, "Compromise of third-party libraries and vendor software updates."),
    ("Web application attacks (OWASP)", "Opportunistic scanners", "web_attack", "T1190 Exploit Public-Facing Application",
     0.75, 0.72, "Injection, auth bypass and misconfig against internet-facing apps."),
]

# source_type, name, vendor, status, record_count, description
TELEMETRY = [
    ("vuln_scanner", "Vulnerability Scanner Feed", "Nessus / OpenVAS (simulated)", "simulated", 0,
     "Authenticated network + web vulnerability scan results."),
    ("siem", "SIEM Alert Stream", "Wazuh / ELK (simulated)", "simulated", 1820,
     "Correlated security alerts and detections from the SIEM."),
    ("iam", "Identity & Access Posture", "Keycloak / AD (simulated)", "simulated", 640,
     "Account inventory, MFA status and privileged role assignments."),
    ("edr", "Endpoint Detection & Response", "OpenEDR / Wazuh (simulated)", "simulated", 512,
     "Endpoint agent coverage, detections and quarantine events."),
    ("cspm", "Cloud Security Posture", "Prowler (simulated)", "simulated", 288,
     "Cloud misconfiguration and compliance findings."),
    ("asset_inventory", "CMDB Asset Inventory", "Internal CMDB (simulated)", "simulated", 0,
     "Authoritative inventory of business assets and ownership."),
    ("threat_intel", "Threat Intelligence Feed", "MISP (simulated)", "simulated", 156,
     "Curated threat actor, campaign and IOC intelligence for BFSI."),
]

# key, label, value, unit, category, description
ASSUMPTIONS = [
    ("breach_cost_per_record_inr", "Data breach cost per record", 1350.0, "INR/record", "impact",
     "Modelled per-record cost of a data breach (notification, remediation, fraud)."),
    ("recovery_base_inr", "Base incident recovery cost", 2_000_000.0, "INR", "impact",
     "Baseline incident response, forensics and recovery cost per major event."),
    ("regulatory_penalty_base_inr", "Regulatory penalty base (RBI/SEBI)", 30_000_000.0, "INR", "impact",
     "Modelled regulatory penalty exposure base for a reportable incident."),
    ("reputation_base_inr", "Reputation / business impact base", 8_000_000.0, "INR", "impact",
     "Modelled brand, churn and business-impact cost scaled by asset criticality."),
    ("recovery_asset_fraction", "Recovery cost as fraction of asset value", 0.05, "fraction", "impact",
     "Portion of asset value added to recovery cost for severe events."),
]
