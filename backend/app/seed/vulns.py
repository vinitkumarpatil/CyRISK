"""Synthetic vulnerabilities and historical incidents for the demo enterprise.

SYNTHETIC / DEMO data. CVE identifiers are real public advisories used only to
make the demo realistic; the findings themselves are fictional.
Incident root-cause text is authored so the effectiveness engine attributes
each event to the correct control (see INCIDENT_CONTROL_KEYWORDS).
"""

# asset, cve, title, cvss, severity, exploit, net_exposed, status, category, patch_available, age_days, remediation_cost, source
def _v(asset, cve, title, cvss, sev, exploit, net, status, cat, patch, age, cost, source):
    return {"asset": asset, "cve": cve, "title": title, "cvss": cvss, "severity": sev,
            "exploit": exploit, "net": net, "status": status, "category": cat,
            "patch": patch, "age": age, "cost": cost, "source": source}

VULNERABILITIES = [
    _v("vpn_gw", "CVE-2023-4966", "VPN session hijack (unauthenticated token leak)", 9.4, "Critical", True, True, "open", "network", True, 120, 800_000, "threat_intel"),
    _v("vpn_gw", "CVE-2024-21887", "VPN appliance command injection", 9.1, "Critical", True, True, "open", "network", True, 60, 600_000, "vuln_scanner"),
    _v("ib_web", "CVE-2024-1709", "Authentication bypass in portal component", 9.8, "Critical", True, True, "open", "web", True, 45, 500_000, "vuln_scanner"),
    _v("ib_web", "", "SQL injection in transaction search", 8.2, "High", False, True, "open", "web", False, 90, 350_000, "vuln_scanner"),
    _v("ib_web", "", "Missing security headers / session fixation", 5.3, "Medium", False, True, "remediating", "web", True, 200, 90_000, "cspm"),
    _v("web_dmz", "CVE-2021-41773", "Outdated Apache path traversal / RCE", 9.1, "Critical", True, True, "open", "software", True, 150, 250_000, "vuln_scanner"),
    _v("web_dmz", "", "Directory listing / information disclosure", 4.3, "Medium", False, True, "closed", "config", True, 300, 40_000, "cspm"),
    _v("upi_switch", "", "Middleware deserialization RCE", 9.0, "Critical", False, True, "open", "software", True, 75, 900_000, "vuln_scanner"),
    _v("upi_switch", "", "Weak TLS ciphers on payment endpoint", 5.9, "Medium", False, True, "open", "config", True, 180, 120_000, "cspm"),
    _v("upi_db", "", "Excessive DB privileges / no row-level control", 7.1, "High", False, False, "open", "identity", False, 220, 300_000, "iam"),
    _v("upi_db", "", "Unencrypted sensitive columns", 6.5, "Medium", False, False, "open", "config", True, 160, 260_000, "cspm"),
    _v("cbs_db", "CVE-2023-21893", "Oracle privilege escalation (unpatched)", 8.8, "High", True, False, "open", "patch", True, 130, 700_000, "vuln_scanner"),
    _v("cbs_db", "", "Shared DBA credentials, no PAM", 7.8, "High", False, False, "open", "identity", False, 250, 400_000, "iam"),
    _v("cbs_db", "", "Audit logging disabled on sensitive tables", 5.5, "Medium", False, False, "open", "config", True, 190, 150_000, "siem"),
    _v("cbs_app", "CVE-2020-0796", "Unpatched OS SMB remote code execution", 8.1, "High", True, False, "open", "patch", True, 110, 350_000, "vuln_scanner"),
    _v("cbs_app", "", "Legacy TLS / weak service configuration", 5.0, "Medium", False, False, "remediating", "config", True, 210, 100_000, "cspm"),
    _v("cust_db", "", "Unmasked PII accessible to broad role", 7.5, "High", False, False, "open", "identity", False, 240, 450_000, "iam"),
    _v("cust_db", "", "Backup snapshots unencrypted", 6.8, "Medium", False, False, "open", "config", True, 170, 280_000, "cspm"),
    _v("cust_db", "", "SQL injection reachable via CRM integration", 8.5, "High", False, False, "open", "web", False, 100, 320_000, "vuln_scanner"),
    _v("mobile_api", "", "Broken object level authorization (BOLA)", 8.2, "High", False, True, "open", "web", False, 85, 300_000, "vuln_scanner"),
    _v("mobile_api", "", "Hardcoded API secret in mobile build", 6.9, "Medium", False, True, "open", "config", True, 140, 120_000, "threat_intel"),
    _v("loan_app", "", "Outdated framework with XSS/RCE chain", 7.9, "High", False, True, "open", "web", True, 160, 220_000, "vuln_scanner"),
    _v("loan_app", "", "Verbose error leaks stack trace", 4.7, "Medium", False, True, "closed", "web", True, 260, 50_000, "cspm"),
    _v("credit_db", "", "Weak access controls on scoring data", 6.7, "Medium", False, False, "open", "identity", False, 230, 180_000, "iam"),
    _v("wealth_app", "", "Vulnerable JS dependency (supply chain)", 7.4, "High", False, True, "open", "software", True, 120, 160_000, "vuln_scanner"),
    _v("wealth_app", "", "Missing MFA on advisor logins", 6.5, "Medium", False, True, "open", "identity", False, 200, 140_000, "iam"),
    _v("dw_db", "", "Over-permissive analytics access to PII", 6.9, "Medium", False, False, "open", "identity", False, 210, 200_000, "iam"),
    _v("dw_db", "", "Unpatched ETL service", 7.0, "High", False, False, "open", "patch", True, 175, 190_000, "vuln_scanner"),
    _v("crm_app", "", "SaaS misconfig: public share links", 6.4, "Medium", False, True, "open", "config", True, 150, 90_000, "cspm"),
    _v("crm_app", "", "OAuth token over-scoped", 5.8, "Medium", False, True, "closed", "identity", True, 190, 80_000, "cspm"),
    _v("email_saas", "", "Legacy auth (IMAP) enabled — MFA bypass", 7.2, "High", False, True, "open", "identity", True, 220, 110_000, "cspm"),
    _v("email_saas", "", "No DMARC enforcement (phishing exposure)", 5.4, "Medium", False, True, "remediating", "config", True, 300, 60_000, "cspm"),
    _v("ad_dc", "CVE-2020-1472", "Unpatched domain controller (Zerologon-style)", 9.2, "Critical", True, False, "open", "patch", True, 95, 500_000, "vuln_scanner"),
    _v("ad_dc", "", "Kerberoasting exposure / weak service accounts", 8.0, "High", False, False, "open", "identity", False, 200, 380_000, "iam"),
    _v("ad_dc", "", "Excessive Domain Admin membership", 7.6, "High", False, False, "open", "identity", False, 260, 300_000, "iam"),
    _v("jump_host", "CVE-2019-0708", "Unpatched RDP remote code execution (BlueKeep-style)", 8.6, "High", True, False, "open", "patch", True, 130, 200_000, "vuln_scanner"),
    _v("jump_host", "", "No session recording / shared admin access", 7.3, "High", False, False, "open", "identity", False, 240, 250_000, "iam"),
    _v("backup_srv", "", "Backups not immutable / online only (ransomware risk)", 7.7, "High", False, False, "open", "config", True, 180, 400_000, "cspm"),
    _v("backup_srv", "", "Restore process untested", 5.6, "Medium", False, False, "open", "config", True, 220, 120_000, "siem"),
    _v("atm_switch", "", "Legacy operating system on ATM switch", 7.1, "High", False, False, "open", "patch", True, 300, 350_000, "vuln_scanner"),
    _v("dev_ci", "", "Exposed CI secrets / tokens in build logs", 7.9, "High", False, True, "open", "config", True, 110, 150_000, "cspm"),
    _v("dev_ci", "", "Dependency confusion risk in build pipeline", 6.6, "Medium", False, True, "open", "software", True, 160, 100_000, "threat_intel"),
    _v("endpoint_fleet", "", "Outdated EDR coverage on a subset of endpoints", 6.3, "Medium", False, False, "open", "software", True, 150, 130_000, "edr"),
    _v("endpoint_fleet", "", "Local administrator rights widespread", 6.8, "Medium", False, False, "open", "identity", False, 240, 160_000, "iam"),
    _v("hr_payroll", "", "Unpatched application server", 6.5, "Medium", False, False, "open", "patch", True, 200, 90_000, "vuln_scanner"),
]

# asset, title, category, root_cause, financial_impact, downtime_hours, records_affected, days_ago
def _i(asset, title, cat, root_cause, fin, downtime, records, days_ago):
    return {"asset": asset, "title": title, "category": cat, "root_cause": root_cause,
            "fin": fin, "downtime": downtime, "records": records, "days_ago": days_ago}

INCIDENTS = [
    _i("ad_dc", "Phishing led to credential theft and remote access", "phishing",
       "Successful phishing email harvested employee credentials; MFA not enforced on VPN.", 12_000_000, 8, 0, 210),
    _i("backup_srv", "Ransomware outbreak on a branch server", "ransomware",
       "Unpatched server exploited; ransomware encrypted files and online backups were affected.", 45_000_000, 36, 0, 400),
    _i("cust_db", "Limited customer data exposure via web form", "web_attack",
       "SQL injection in a legacy web form allowed sensitive records to be exfiltrated.", 18_000_000, 4, 120_000, 300),
    _i("endpoint_fleet", "Malware outbreak across employee endpoints", "malware",
       "Malware spread via endpoints; lateral movement across a flat network segment.", 9_000_000, 12, 0, 150),
    _i("jump_host", "Privilege misuse by a departing contractor", "insider",
       "Shared admin credentials and standing privileged access were misused.", 6_500_000, 3, 0, 250),
    _i("ib_web", "DDoS disrupted internet banking", "ddos",
       "Volumetric DDoS overwhelmed the public web tier for several hours.", 4_000_000, 6, 0, 100),
    _i("upi_switch", "Attempted payment fraud blocked", "apt",
       "Unpatched middleware was probed; network segmentation gaps enabled lateral attempts.", 3_500_000, 2, 0, 180),
]

