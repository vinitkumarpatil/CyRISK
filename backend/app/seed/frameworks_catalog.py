"""Security framework catalog and control mappings (SYNTHETIC / DEMO).

IMPORTANT: This is an internal *assessment / mapping* aid, NOT a certification
or attestation of compliance. Coverage status for each framework control is
COMPUTED at runtime from the effectiveness of the linked internal control
(see engine/frameworks_data.py) — it is never a claim of certified compliance.

Each control row: (control_ref, category, title, internal_control_key)
"""

# key, name, full_name, version, controls[]
FRAMEWORKS = [
    {
        "key": "iso27001", "name": "ISO/IEC 27001", "version": "2022",
        "full_name": "ISO/IEC 27001:2022 Information Security Management (Annex A)",
        "controls": [
            ("A.5.15", "Access Control", "Access control policy", "mfa"),
            ("A.5.17", "Access Control", "Authentication information", "mfa"),
            ("A.5.18", "Access Control", "Access rights (review & removal)", "access_review"),
            ("A.8.2", "Privileged Access", "Privileged access rights", "privileged_access"),
            ("A.8.8", "Vulnerability Mgmt", "Management of technical vulnerabilities", "vuln_management"),
            ("A.8.9", "Configuration", "Configuration & patch management", "patch_management"),
            ("A.8.24", "Cryptography", "Use of cryptography", "encryption"),
            ("A.8.13", "Resilience", "Information backup", "backup"),
            ("A.8.16", "Monitoring", "Monitoring activities", "logging_monitoring"),
            ("A.8.20", "Network Security", "Networks security", "network_segmentation"),
            ("A.8.7", "Malware", "Protection against malware", "endpoint_protection"),
        ],
    },
    {
        "key": "nist_csf", "name": "NIST CSF", "version": "2.0",
        "full_name": "NIST Cybersecurity Framework 2.0",
        "controls": [
            ("PR.AA-01", "Protect", "Identities & credentials managed", "mfa"),
            ("PR.AA-05", "Protect", "Access permissions (least privilege)", "privileged_access"),
            ("PR.AA-07", "Protect", "Access rights reviewed", "access_review"),
            ("PR.PS-02", "Protect", "Software maintenance (patching)", "patch_management"),
            ("ID.RA-01", "Identify", "Asset vulnerabilities identified", "vuln_management"),
            ("PR.DS-01", "Protect", "Data-at-rest protection", "encryption"),
            ("PR.IR-01", "Protect", "Networks & environments protected", "network_segmentation"),
            ("DE.CM-01", "Detect", "Networks & systems monitored", "logging_monitoring"),
            ("PR.PS-05", "Protect", "Malware defenses installed", "endpoint_protection"),
            ("RC.RP-01", "Recover", "Recovery plan & backups executed", "backup"),
        ],
    },
    {
        "key": "cis_v8", "name": "CIS Controls", "version": "8.0",
        "full_name": "CIS Critical Security Controls v8",
        "controls": [
            ("CIS 6", "Access Management", "Access control management (MFA)", "mfa"),
            ("CIS 5", "Account Management", "Account management & review", "access_review"),
            ("CIS 6.8", "Access Management", "Privileged access management", "privileged_access"),
            ("CIS 7", "Vulnerability Mgmt", "Continuous vulnerability management", "vuln_management"),
            ("CIS 4", "Configuration", "Secure configuration & patching", "patch_management"),
            ("CIS 3", "Data Protection", "Data protection (encryption)", "encryption"),
            ("CIS 10", "Malware", "Malware defenses", "endpoint_protection"),
            ("CIS 8", "Logging", "Audit log management", "logging_monitoring"),
            ("CIS 12", "Network", "Network infrastructure management", "network_segmentation"),
            ("CIS 11", "Resilience", "Data recovery", "backup"),
        ],
    },
    {
        "key": "rbi", "name": "RBI CSF", "version": "2016+",
        "full_name": "RBI Cyber Security Framework for Banks (Assessment)",
        "controls": [
            ("RBI-AC", "Access Control", "Multi-factor & user access control", "mfa"),
            ("RBI-PA", "Access Control", "Privileged / least-privilege access", "privileged_access"),
            ("RBI-AR", "Access Control", "Periodic access review", "access_review"),
            ("RBI-PM", "Patch Mgmt", "Patch & change management", "patch_management"),
            ("RBI-VA", "Vulnerability", "Vulnerability assessment", "vuln_management"),
            ("RBI-EN", "Data Security", "Data leak prevention & encryption", "encryption"),
            ("RBI-NW", "Network", "Network management & segmentation", "network_segmentation"),
            ("RBI-SOC", "Monitoring", "Security monitoring (SOC)", "logging_monitoring"),
            ("RBI-AM", "Malware", "Anti-malware measures", "endpoint_protection"),
            ("RBI-BR", "Resilience", "Backup, recovery & BCP", "backup"),
        ],
    },
    {
        "key": "sebi", "name": "SEBI CSCRF", "version": "2018+",
        "full_name": "SEBI Cyber Security & Cyber Resilience Framework (Assessment)",
        "controls": [
            ("SEBI-IA", "Access Control", "Identification & access (MFA)", "mfa"),
            ("SEBI-PA", "Access Control", "Privileged access management", "privileged_access"),
            ("SEBI-PM", "Patch Mgmt", "Patch management", "patch_management"),
            ("SEBI-VAPT", "Vulnerability", "VAPT / vulnerability management", "vuln_management"),
            ("SEBI-EN", "Data Security", "Encryption of sensitive data", "encryption"),
            ("SEBI-NW", "Network", "Network segmentation", "network_segmentation"),
            ("SEBI-SOC", "Monitoring", "Monitoring & detection (SOC)", "logging_monitoring"),
            ("SEBI-AM", "Malware", "Malware protection", "endpoint_protection"),
            ("SEBI-BR", "Resilience", "Data backup & recovery", "backup"),
        ],
    },
]
